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
# tokens, and it blocks hard after only a handful of requests in practice —
# well short of the documented "20/day" figure. Since it's requests that are
# scarce, not tokens, fewer/larger batches directly buy more real progress
# per usable window than many/smaller ones. 100 titles/batch comfortably
# fits the adapter's 8192 output-token budget (llm/gemini.py) once thinking
# is disabled (~50-60 tokens per classified title).
BATCH_SIZE = 100

# One request per 13s keeps a safety margin under the free tier's 5 req/min
# cap. Upgrading the API plan removes the need for this pacing entirely.
SECONDS_BETWEEN_BATCHES = 13
MAX_RETRIES = 5
RATE_LIMIT_RETRY_DELAY = 60

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


def _is_rate_limit_error(exc: Exception) -> bool:
    """
    Detect rate-limit errors generically from the exception's string form
    rather than importing a provider-specific exception type — LLMProvider
    doesn't define what its adapters raise, and different providers signal
    rate limits differently.
    """
    text = str(exc).lower()
    return "429" in text or "resource_exhausted" in text or "rate limit" in text


async def _complete_with_retry(prompt: str, system: str) -> str:
    # Dedicated key, separate from /api/chat's GEMINI_API_KEY — classification
    # and live chat must never compete for the same quota pool (see
    # backend/specs/market-health/api.md — Scheduled ingestion agent).
    provider = providers.gemini(CLASSIFICATION_MODEL, api_key=os.environ["GEMINI_API_KEY_CLASSIFICATION"])
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await provider.complete(prompt=prompt, system=system)
        except Exception as exc:
            if not _is_rate_limit_error(exc) or attempt == MAX_RETRIES:
                raise
            logger.warning(
                "Rate limited (attempt %d/%d), retrying in %ds: %s",
                attempt, MAX_RETRIES, RATE_LIMIT_RETRY_DELAY, exc,
            )
            await asyncio.sleep(RATE_LIMIT_RETRY_DELAY)
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
                        CLASSIFICATION_MODEL,
                        classified_at,
                    )
                    for c in classifications
                ],
            )


async def classify_postings(postings: list[dict]) -> dict:
    """
    Classify and store an arbitrary-length list of {id, title} postings.
    Returns stats for the IngestionRun record: {cache_hits, llm_classified,
    other_count, total_classified, stopped_early}.

    Two dedup layers run before any LLM call, since classification depends
    only on title (see _get_title_cache):
      1. Titles already classified in a prior run are reused from the DB —
         zero LLM calls.
      2. Among titles never seen before, duplicates within this batch are
         classified once (as a unique title, not once per posting) and the
         result is fanned out to every posting sharing that title.
    This matters a lot in practice — job titles repeat heavily across
    postings/companies/days — and it's the main lever available for staying
    under the LLM provider's request quota while building up the dataset.

    If the LLM provider becomes unavailable partway through (rate limit
    exhausted after all retries — routine on the free tier), stops gracefully
    and returns stopped_early=True rather than letting the exception crash
    the whole ingestion run. Everything classified before the stopping point
    is already persisted (per-batch insert, below), so nothing is lost.
    """
    empty_stats = {"cache_hits": 0, "llm_classified": 0, "other_count": 0, "total_classified": 0, "stopped_early": False}
    if not postings:
        return empty_stats

    # Grouped by title so a batch's result can be written for every posting
    # sharing that title as soon as it's known — not held in memory until
    # every batch finishes. A later batch failing (e.g. hitting the LLM
    # provider's rate limit, which happens routinely on the free tier) must
    # never discard already-paid-for classifications from earlier batches.
    postings_by_title: dict[str, list[dict]] = {}
    for p in postings:
        postings_by_title.setdefault(p["title"], []).append(p)

    unique_titles = list(postings_by_title.keys())
    cache = _get_title_cache(unique_titles)
    novel_titles = [t for t in unique_titles if t not in cache]

    logger.info(
        "classify_postings: %d postings, %d unique titles (%d cached, %d need classifying)",
        len(postings), len(unique_titles), len(unique_titles) - len(novel_titles), len(novel_titles),
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
    llm_classified = 0
    stopped_early = False

    num_batches = (len(novel_titles) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_num, i in enumerate(range(0, len(novel_titles), BATCH_SIZE), start=1):
        title_batch = novel_titles[i : i + BATCH_SIZE]
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
        logger.info("classified batch %d/%d (%d unique titles)", batch_num, num_batches, len(title_batch))
        if batch_num < num_batches:
            await asyncio.sleep(SECONDS_BETWEEN_BATCHES)

    return {
        "cache_hits": cache_hits,
        "llm_classified": llm_classified,
        "other_count": other_count,
        "total_classified": cache_hits + llm_classified,
        "stopped_early": stopped_early,
    }
