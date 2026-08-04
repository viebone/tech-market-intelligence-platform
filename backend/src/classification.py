"""
LLM-driven posting classification.

Classifies each new raw_posting against the closed taxonomy defined in
design/market-health/job-classification.md (Role Category, Seniority, Track).
Uses LLMProvider.complete() — the provider abstraction has no native
schema-constrained output today (see backend/specs/market-health/api.md —
Tech Decisions), so the JSON response is parsed and validated here rather
than trusted as-is. A posting that doesn't validate is classified "other"
rather than forced into the nearest match.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone

from db import get_connection
from llm import providers

logger = logging.getLogger(__name__)

# Taxonomy version pinned to job-classification.md's `created` date — that
# spec has no separate version field, so its creation date is the version
# marker. Bump this if the taxonomy's closed sets are ever revised.
TAXONOMY_VERSION = "2026-07-16"
CLASSIFICATION_MODEL = "gemini-2.5-flash"

ROLE_CATEGORIES = {"Designer", "Product Manager", "Engineer"}
SENIORITY_LADDER = {
    "entry", "junior", "mid", "senior", "lead",
    "principal", "manager", "director", "vp", "exec",
}
TRACKS = {"ic", "management"}

# Batched, not one call per posting, to control LLM cost — and sized against
# real constraints found during ingestion: the Gemini free tier's binding
# limit is on *request count* (generate_content_free_tier_requests), not
# tokens. Confirmed 2026-08-04 via Google's own error payload: the limit is
# exactly 20 requests/day/project/model (quotaId:
# GenerateRequestsPerDayPerProjectPerModel-FreeTier) — a hard daily ceiling,
# not a per-minute rate. Since it's requests that are scarce, not tokens,
# fewer/larger batches directly buy more real progress per day than
# many/smaller ones. 100 titles/batch comfortably fits the adapter's 8192
# output-token budget (llm/gemini.py) once thinking is disabled (~50-60
# tokens per classified title).
BATCH_SIZE = 100

# Self-imposed good-citizenship pacing between batches, not a defense against
# a per-minute limit — the real constraint is the daily request count above,
# which pacing alone can't help with (see MAX_BATCHES_PER_RUN).
SECONDS_BETWEEN_BATCHES = 13
MAX_RETRIES = 5
RETRYABLE_ERROR_RETRY_DELAY = 60

# Deliberate per-run cap on how many LLM batches this run will attempt, sized
# with headroom under the 20-requests/day ceiling: 12 successful batches (12
# requests) leaves 8 requests of slack for this-run retries on transient
# errors (Retry policy, above) before ever risking a real 429. Reaching this
# cap is a clean, intentional stop — see backend/specs/market-health/api.md —
# Business Logic — Classification — Per-run classification budget — not a
# failure, and must not be conflated with `stopped_early` below.
MAX_BATCHES_PER_RUN = 12

# Denylist, not allowlist — deliberately. An allowlist (only send recognized
# tech keywords to the LLM) would silently starve the unusual-but-real tech
# titles design/market-health/job-classification.md's "Raw Title" section
# exists to catch (e.g. "Founding Engineer," "AI Product Manager"). This list
# only ever skips titles that are unambiguous regardless of phrasing.
# Curated, not exhaustive — tunable as real `other`-rate data comes in, same
# discipline as the source adapters' curated company lists.
DENYLIST_KEYWORDS = frozenset({
    "account executive", "account manager", "business development",
    "sales development", "sales manager", "sales director", "regional sales",
    "recruiter", "recruiting", "talent acquisition", "human resources",
    "payroll", "accountant", "accounting", "controller", "bookkeeper",
    "legal counsel", "attorney", "paralegal", "compliance officer",
    "marketing manager", "marketing coordinator", "content marketing",
    "communications manager", "public relations", "social media manager",
    "customer support", "customer success", "customer service",
    "warehouse", "logistics coordinator", "supply chain", "procurement",
    "office manager", "executive assistant", "administrative assistant",
    "facilities", "receptionist",
})
HEURISTIC_FILTER_MODEL = "heuristic-keyword-filter"

SYSTEM_INSTRUCTION = """You classify UK tech job postings into a closed taxonomy. \
For each posting, return exactly these fields:
- role_category: one of "Designer", "Product Manager", "Engineer", or "other" if the \
posting genuinely does not fit (e.g. a non-tech role that happens to share a title word).
- sub_specialization: a short specific title (e.g. "UX Designer", "Backend Engineer"), \
or null if role_category is "other".
- seniority: one of "entry", "junior", "mid", "senior", "lead", "principal", "manager", \
"director", "vp", "exec", or null if role_category is "other". UK "midweight" means "mid".
- track: "ic" (individual contributor) or "management", or null if role_category is "other" \
or genuinely unclear. "Lead" is ambiguous — infer from context whether it is a senior IC or \
a first-line management role.

Example: "Product Manager - Health Policy" is role_category "other" — nominally a Product \
Manager title, but a health-policy role, not a tech-market role this taxonomy tracks. Titles \
with a tech-unrelated qualifier like this should be "other" even if the base title matches.

Return strictly a JSON array, one object per input posting, each with an "id" field copied \
from the input plus the four fields above. No prose, no markdown fences."""


def _build_prompt(postings: list[dict]) -> str:
    lines = [f'{{"id": "{p["id"]}", "title": {json.dumps(p["title"])}}}' for p in postings]
    return "Classify these postings:\n[" + ",\n".join(lines) + "]"


def _parse_response(text: str) -> list[dict]:
    """Strip optional markdown code fences and parse the JSON array."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _get_title_cache(titles: list[str]) -> dict[str, dict]:
    """
    Look up existing classifications by exact raw_postings.title match.

    Classification depends only on title — _build_prompt sends nothing else —
    so identical titles always classify identically. Reusing a prior result
    for a title we've already paid to classify isn't just a cost saving, it's
    also a consistency improvement: it removes any run-to-run model variance
    for repeated titles instead of risking two different answers for the
    same exact title.
    """
    if not titles:
        return {}
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT ON (rp.title)
                rp.title, c.role_category, c.sub_specialization, c.seniority, c.track
            FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            WHERE rp.title = ANY(%s)
            ORDER BY rp.title, c.classified_at ASC
            """,
            (titles,),
        ).fetchall()
    return {
        row[0]: {
            "role_category": row[1],
            "sub_specialization": row[2],
            "seniority": row[3],
            "track": row[4],
        }
        for row in rows
    }


def _validate(entry: dict) -> dict:
    """Coerce an entry to the closed sets. Anything invalid becomes "other"."""
    role_category = entry.get("role_category")
    if role_category not in ROLE_CATEGORIES:
        return {
            "id": entry.get("id"),
            "role_category": "other",
            "sub_specialization": None,
            "seniority": None,
            "track": None,
        }

    seniority = entry.get("seniority")
    track = entry.get("track")
    return {
        "id": entry.get("id"),
        "role_category": role_category,
        "sub_specialization": entry.get("sub_specialization"),
        "seniority": seniority if seniority in SENIORITY_LADDER else None,
        "track": track if track in TRACKS else None,
    }


def _is_denylisted(title: str) -> bool:
    """
    True if `title` unambiguously names a non-tech role, per DENYLIST_KEYWORDS.
    Cost optimization only, not a taxonomy decision — a denylisted title
    resolves to the same `role_category: "other"` an LLM call would have
    produced anyway (design/market-health/job-classification.md —
    Classification Method).
    """
    text = title.lower()
    return any(keyword in text for keyword in DENYLIST_KEYWORDS)


# Mirrors the retryable-failure set already used for the Greenhouse/Lever/Ashby
# fetch adapters (sources/base.py — RETRYABLE_STATUS_CODES: 429/500/502/503/504) —
# a provider being transiently overloaded (e.g. a 503 "model currently experiencing
# high demand") is not the same failure as quota exhaustion, but both are equally
# worth retrying past before giving up on a batch (see backend/specs/market-health/
# api.md — Business Logic — Classification — Retry policy).
RETRYABLE_STATUS_CODES = {"429", "500", "502", "503", "504"}


def _is_retryable_error(exc: Exception) -> bool:
    """
    Detect retryable errors generically from the exception's string form
    rather than importing a provider-specific exception type — LLMProvider
    doesn't define what its adapters raise, and different providers signal
    failures differently. httpx status codes aren't available at this layer
    (the Gemini SDK raises its own exception types), so this matches on the
    exception's string form the same way the original rate-limit-only check
    did — just broadened to cover 5xx/transient-unavailability text too.
    """
    text = str(exc).lower()
    if any(code in text for code in RETRYABLE_STATUS_CODES):
        return True
    return any(
        keyword in text
        for keyword in ("resource_exhausted", "rate limit", "unavailable", "timeout", "connection")
    )


async def _complete_with_retry(prompt: str, system: str) -> str:
    # Dedicated key, separate from /api/chat's GEMINI_API_KEY — classification
    # and live chat must never compete for the same quota pool (see
    # backend/specs/market-health/api.md — Scheduled ingestion agent).
    provider = providers.gemini(CLASSIFICATION_MODEL, api_key=os.environ["GEMINI_API_KEY_CLASSIFICATION"])
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await provider.complete(prompt=prompt, system=system)
        except Exception as exc:
            if not _is_retryable_error(exc) or attempt == MAX_RETRIES:
                raise
            logger.warning(
                "Retryable error (attempt %d/%d), retrying in %ds: %s",
                attempt, MAX_RETRIES, RETRYABLE_ERROR_RETRY_DELAY, exc,
            )
            await asyncio.sleep(RETRYABLE_ERROR_RETRY_DELAY)
    raise RuntimeError("unreachable")  # loop always returns or raises


async def classify_batch(postings: list[dict]) -> list[dict]:
    """
    Classify a batch of up to BATCH_SIZE {id, title} postings.
    Returns one validated classification dict per input posting, in the same
    order requested — postings the model omits are classified "other".
    """
    if not postings:
        return []

    response_text = await _complete_with_retry(_build_prompt(postings), SYSTEM_INSTRUCTION)
    parsed = {entry.get("id"): _validate(entry) for entry in _parse_response(response_text)}

    return [
        parsed.get(p["id"], _validate({"id": p["id"]}))
        for p in postings
    ]


def insert_classifications(classifications: list[dict]) -> None:
    """
    Insert one classifications row per entry. `model` defaults to
    CLASSIFICATION_MODEL but honors a per-entry override (e.g.
    HEURISTIC_FILTER_MODEL for denylist-resolved rows) so provenance stays
    honest about which path actually produced a given classification — see
    backend/specs/market-health/api.md — Data Models — Classification.
    """
    if not classifications:
        return
    classified_at = datetime.now(timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO classifications
                    (posting_id, role_category, sub_specialization, seniority, track,
                     taxonomy_version, model, classified_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (posting_id) DO NOTHING
                """,
                [
                    (
                        c["id"],
                        c["role_category"],
                        c["sub_specialization"],
                        c["seniority"],
                        c["track"],
                        TAXONOMY_VERSION,
                        c.get("model", CLASSIFICATION_MODEL),
                        classified_at,
                    )
                    for c in classifications
                ],
            )


async def classify_postings(postings: list[dict]) -> dict:
    """
    Classify and store an arbitrary-length list of {id, title} postings.
    Returns stats for the IngestionRun record: {cache_hits,
    heuristic_filtered, llm_classified, other_count, total_classified,
    stopped_early, budget_reached}. `postings` is expected oldest-first (see
    raw_postings.get_all_unclassified) so that when demand exceeds this run's
    budget, the longest-waiting backlog is what actually gets classified.

    Three layers run before any LLM call, since classification depends only
    on title (see _get_title_cache):
      1. Titles already classified in a prior run are reused from the DB —
         zero LLM calls.
      2. Among titles never seen before, ones matching DENYLIST_KEYWORDS are
         resolved straight to "other" by the heuristic pre-filter — zero LLM
         calls (see _is_denylisted).
      3. Among the remaining novel titles, duplicates within this run are
         classified once and the result is fanned out to every posting
         sharing that title.
    Job titles repeat heavily across postings/companies/days, and a large
    share of any given board is unambiguously non-tech — together these are
    the main levers for staying under the LLM provider's daily request quota
    (backend/specs/market-health/api.md — Business Logic — Classification).

    This run attempts at most MAX_BATCHES_PER_RUN LLM batches — a deliberate
    budget, not "classify everything." Reaching that budget with zero errors
    sets budget_reached=True; this is a clean, intentional stop, distinct
    from stopped_early=True, which means a batch failed after exhausting
    retries on a genuine error (routine on the free tier if the budget's
    headroom is ever exceeded). Everything classified before either stopping
    point is already persisted (per-batch insert, below), so nothing is lost.
    """
    empty_stats = {
        "cache_hits": 0, "heuristic_filtered": 0, "llm_classified": 0,
        "other_count": 0, "total_classified": 0,
        "stopped_early": False, "budget_reached": False,
    }
    if not postings:
        return empty_stats

    # Grouped by title so a batch's result can be written for every posting
    # sharing that title as soon as it's known — not held in memory until
    # every batch finishes. A later batch failing (e.g. hitting the LLM
    # provider's rate limit, which happens routinely on the free tier) must
    # never discard already-paid-for classifications from earlier batches.
    # dict preserves insertion order, so unique_titles below stays
    # oldest-first, matching the order `postings` arrived in.
    postings_by_title: dict[str, list[dict]] = {}
    for p in postings:
        postings_by_title.setdefault(p["title"], []).append(p)

    unique_titles = list(postings_by_title.keys())
    cache = _get_title_cache(unique_titles)
    novel_titles = [t for t in unique_titles if t not in cache]
    denylisted_titles = [t for t in novel_titles if _is_denylisted(t)]
    denylisted_set = set(denylisted_titles)
    llm_titles = [t for t in novel_titles if t not in denylisted_set]

    logger.info(
        "classify_postings: %d postings, %d unique titles (%d cached, %d heuristic-filtered, "
        "%d need an LLM call)",
        len(postings), len(unique_titles), len(unique_titles) - len(novel_titles),
        len(denylisted_titles), len(llm_titles),
    )

    def _rows_for(titles: list[str], result_by_title: dict[str, dict]) -> list[dict]:
        return [
            {"id": p["id"], **{k: v for k, v in result_by_title[title].items() if k != "id"}}
            for title in titles
            for p in postings_by_title[title]
        ]

    def _count_other(rows: list[dict]) -> int:
        return sum(1 for r in rows if r["role_category"] == "other")

    cached_titles = [t for t in unique_titles if t in cache]
    cached_rows = _rows_for(cached_titles, cache)
    insert_classifications(cached_rows)
    cache_hits = len(cached_rows)
    other_count = _count_other(cached_rows)

    denylisted_result = {
        "role_category": "other", "sub_specialization": None,
        "seniority": None, "track": None, "model": HEURISTIC_FILTER_MODEL,
    }
    heuristic_rows = _rows_for(denylisted_titles, {t: denylisted_result for t in denylisted_titles})
    insert_classifications(heuristic_rows)
    heuristic_filtered = len(heuristic_rows)
    other_count += _count_other(heuristic_rows)

    llm_classified = 0
    stopped_early = False
    budget_reached = False
    batches_attempted = 0

    num_batches = (len(llm_titles) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_num, i in enumerate(range(0, len(llm_titles), BATCH_SIZE), start=1):
        if batches_attempted >= MAX_BATCHES_PER_RUN:
            budget_reached = True
            logger.info(
                "classify_postings: reached MAX_BATCHES_PER_RUN (%d), %d/%d batches left for "
                "a future run", MAX_BATCHES_PER_RUN, num_batches - batches_attempted, num_batches,
            )
            break
        title_batch = llm_titles[i : i + BATCH_SIZE]
        try:
            # classify_batch takes {id, title} pairs; here each unique title
            # stands in as its own id since we're classifying titles, not
            # individual postings.
            results = await classify_batch([{"id": t, "title": t} for t in title_batch])
        except Exception as exc:
            logger.error(
                "classify batch %d/%d failed, stopping this run early (already-classified "
                "titles remain safely persisted): %s", batch_num, num_batches, exc,
            )
            stopped_early = True
            break
        fresh = dict(zip(title_batch, results))
        fresh_rows = _rows_for(title_batch, fresh)
        insert_classifications(fresh_rows)
        llm_classified += len(fresh_rows)
        other_count += _count_other(fresh_rows)
        batches_attempted += 1
        logger.info("classified batch %d/%d (%d unique titles)", batch_num, num_batches, len(title_batch))
        if batch_num < num_batches and batches_attempted < MAX_BATCHES_PER_RUN:
            await asyncio.sleep(SECONDS_BETWEEN_BATCHES)

    return {
        "cache_hits": cache_hits,
        "heuristic_filtered": heuristic_filtered,
        "llm_classified": llm_classified,
        "other_count": other_count,
        "total_classified": cache_hits + heuristic_filtered + llm_classified,
        "stopped_early": stopped_early,
        "budget_reached": budget_reached,
    }
