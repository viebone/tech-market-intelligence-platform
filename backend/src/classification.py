"""
LLM-driven posting classification.

Classifies each new raw_posting against the closed taxonomy defined in
design/market-health/job-classification.md (Role Category, Specialization,
Level, Track, Classification Confidence). Uses LLMProvider.complete() — the
provider abstraction has no native schema-constrained output today (see
backend/specs/market-health/api.md — Tech Decisions), so the JSON response is
parsed and validated here rather than trusted as-is. A posting that doesn't
validate is classified "other" rather than forced into the nearest match.
"unknown" (2026-08-11) is a distinct, valid outcome from "other" — see
job-classification.md — Unknown vs. Other — not a validation failure.
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

# Taxonomy version pinned to job-classification.md's `updated` date — that
# spec has no separate version field, so its last-revision date is the version
# marker. Bumped 2026-08-11 for the Level/Track/Unknown/Confidence redesign
# (changes/2026-08-11-classification-taxonomy-redesign.md); bumped again
# 2026-09-21 for the specialization widening + Job Function addition
# (changes/2026-09-21-taxonomy-revision-specialization-and-job-function.md) —
# bump again if the taxonomy's closed sets are ever revised further.
TAXONOMY_VERSION = "2026-09-21"
CLASSIFICATION_MODEL = "gemini-2.5-flash"

ROLE_CATEGORIES = {"Designer", "Product Manager", "Engineer"}

# Canonical specialization values per Role Category (job-classification.md — Role Category,
# widened 2026-09-21 from real production data). This is the single source of truth: the
# SYSTEM_INSTRUCTION prompt below is built from this dict, and get_emerging_taxonomy_candidates()
# (pipeline-visibility) reads the exact same dict — a value can never drift between "what the
# LLM was told" and "what the detector considers already-canonical." NOT enforced as a closed
# set in _validate() (deliberately — see _validate's docstring and the module-level "starts
# narrow, widens with real data" precedent); this is guidance for the LLM and a reference for
# detection, never a rejection list.
SPECIALIZATIONS: dict[str, tuple[str, ...]] = {
    "Designer": (
        "UX Designer", "UX Researcher", "Product Designer", "UI Designer",
        "Content Designer", "UX Writer", "Design Systems", "Brand Designer",
        "Motion Designer", "Other Design",
    ),
    "Product Manager": (
        "Product Manager", "Product Owner", "Technical Product Manager",
        "Data Product Manager", "Growth Product Manager", "Platform Product Manager",
        "AI Product Manager", "Forward Deployed Product Manager", "Other Product",
    ),
    "Engineer": (
        "Frontend Engineer", "Backend Engineer", "Full-Stack Engineer", "Mobile Engineer",
        "Machine Learning Engineer", "AI Engineer", "Data Engineer", "Data Scientist",
        "DevOps/SRE Engineer", "Security Engineer", "Infrastructure Engineer",
        "Platform Engineer", "Network Engineer", "Research Engineer", "Solutions Engineer",
        "Solutions Architect", "Support Engineer", "Customer Engineer",
        "Forward Deployed Engineer", "Software Engineer",
        # Added 2026-09-21, same day, before the *_taxonomy_candidates detector's first real
        # run against production surfaced these with real volume >= 10 that the earlier
        # top-25-only manual pull had missed entirely — see changes/2026-09-21-emerging-role-
        # detection.md's "First real run" section.
        "Hardware Engineer", "Systems Engineer", "AI Deployment Engineer",
        "Analytics Engineer", "Database Engineer", "Integration Engineer", "QA Engineer",
        "Other Engineering",
    ),
}
# "unknown" (2026-08-11) is valid at every one of these four fields — distinct
# from role_category="other" (see module docstring). Not included in the sets
# below since it's handled as its own branch in _validate, same treatment at
# every field rather than folded into each closed set.
LEVEL_LADDER = {
    "entry", "junior", "mid", "senior", "lead",
    "principal", "director", "vp", "executive",
}  # replaces the old SENIORITY_LADDER, which wrongly included "manager" as a
   # level — see job-classification.md — Level, and the 160-posting
   # seniority="manager" collapse that motivated this revision.
TRACKS = {"ic", "management"}
CLASSIFICATION_CONFIDENCE_VALUES = {"low", "medium", "high"}

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

# Cross-run daily budget (added 2026-08-05, fixing a real gap: MAX_BATCHES_PER_RUN above
# used to reset per run invocation, so two "Run now" triggers on the same day could
# together attempt nearly double the real daily ceiling — narrowly avoided by luck during
# manual testing, not by design. See backend/specs/market-health/api.md — Business Logic —
# Classification — Cross-run daily budget. Named/configurable so raising the quota later
# (e.g. upgrading billing) is a one-line change.
DAILY_REQUEST_BUDGET = 20   # confirmed Gemini free-tier ceiling
RETRY_HEADROOM = 8          # reserved across ALL of today's runs combined, not per run

# Denylist, not allowlist — deliberately. An allowlist (only send recognized
# tech keywords to the LLM) would silently starve the unusual-but-real tech
# titles design/market-health/job-classification.md's "Raw Title" section
# exists to catch (e.g. "Founding Engineer," "AI Product Manager"). This list
# only ever skips titles that are unambiguous regardless of phrasing.
# Curated, not exhaustive — tunable as real `other`-rate data comes in, same
# discipline as the source adapters' curated company lists.
#
# Organized by Job Function (job-classification.md — Job Function,
# 2026-09-21) rather than a flat set — a denylisted title gets its
# job_function assigned directly from which cluster matched, at zero LLM
# cost, since the pre-filter already knows exactly why it flagged the title.
DENYLIST_JOB_FUNCTIONS: dict[str, tuple[str, ...]] = {
    "Sales & Business Development": (
        "account executive", "account manager", "business development",
        "sales development", "sales manager", "sales director", "regional sales",
    ),
    "People & Talent": (
        "recruiter", "recruiting", "talent acquisition", "human resources",
    ),
    "Finance & Accounting": (
        "payroll", "accountant", "accounting", "controller", "bookkeeper",
    ),
    "Legal & Compliance": (
        "legal counsel", "attorney", "paralegal", "compliance officer",
    ),
    "Marketing & Communications": (
        "marketing manager", "marketing coordinator", "content marketing",
        "communications manager", "public relations", "social media manager",
    ),
    "Customer Success & Support": (
        "customer support", "customer success", "customer service",
    ),
    "Operations & Business Ops": (
        "warehouse", "logistics coordinator", "supply chain", "procurement",
    ),
    "Executive & Administrative": (
        "office manager", "executive assistant", "administrative assistant",
        "facilities", "receptionist",
    ),
}
DENYLIST_KEYWORDS = frozenset(
    keyword for keywords in DENYLIST_JOB_FUNCTIONS.values() for keyword in keywords
)
HEURISTIC_FILTER_MODEL = "heuristic-keyword-filter"

# Closed set for the new Job Function field (job-classification.md — Job
# Function, 2026-09-21). Populated only when role_category == "other" — see
# _validate. "unknown" is handled the same way as every other field in this
# taxonomy: a real, distinct, honest outcome, not folded into "Other Non-Tech".
JOB_FUNCTIONS = {
    "Sales & Business Development", "Marketing & Communications",
    "Customer Success & Support", "People & Talent", "Legal & Compliance",
    "Finance & Accounting", "Operations & Business Ops", "IT & Technical Support",
    "Learning & Development", "Executive & Administrative", "Other Non-Tech",
}


def _denylisted_job_function(title: str) -> str:
    """
    Which Job Function cluster matched a denylisted title — computed from the
    same keyword check that already decided the title was denylisted, so this
    never costs an extra LLM call. Falls back to "Other Non-Tech" only if
    DENYLIST_KEYWORDS and DENYLIST_JOB_FUNCTIONS ever drift apart (they're
    derived from the same source above, so this should not happen in
    practice — kept as an honest fallback rather than an assumption).
    """
    text = title.lower()
    for job_function, keywords in DENYLIST_JOB_FUNCTIONS.items():
        if any(keyword in text for keyword in keywords):
            return job_function
    return "Other Non-Tech"

_SPECIALIZATION_PROMPT_BLOCK = "\n".join(
    f"  {category}: {', '.join(values)}" for category, values in SPECIALIZATIONS.items()
)

SYSTEM_INSTRUCTION = f"""You classify UK tech job postings into a closed taxonomy. \
For each posting, return exactly these fields:
- role_category: one of "Designer", "Product Manager", "Engineer", "other", or "unknown". \
Use "other" when you're confident the posting genuinely is not one of the three tracked \
occupations (e.g. a non-tech role that happens to share a title word). Use "unknown" when \
the title alone doesn't give you enough evidence to tell, even though it might plausibly be \
one of the three — these are different claims, do not use them interchangeably.
- specialization: a short specific title, "unknown" if role_category is a real tracked \
category but the title doesn't disambiguate which specialization within it, or null if \
role_category is "other" or "unknown". Prefer one of these canonical values when the title \
matches, so the same real occupation converges on one consistent name across postings — but \
you are not restricted to only these if a title clearly names something else real and specific:
{_SPECIALIZATION_PROMPT_BLOCK}
  ("Software Engineer" is the generic/unspecified Engineer default when no more specific match \
applies. "Content Designer" and "UX Writer" are two distinct, separate values — do not combine \
them even though they're closely related crafts. Converge spelling/phrasing variants onto the \
one canonical form above rather than inventing a near-duplicate: "Fullstack Engineer"/"Full \
Stack Software Engineer" → "Full-Stack Engineer"; "Backend Software Engineer" → "Backend \
Engineer"; "Frontend Software Engineer" → "Frontend Engineer"; "Solution Architect" \
(singular) → "Solutions Architect"; "QA/Test Engineer"/"Quality Engineer" → "QA Engineer"; \
"Product Management" → "Product Manager".)
- level: one of "entry", "junior", "mid", "senior", "lead", "principal", "director", "vp", \
"executive", "unknown" (title gives no real seniority signal), or null if role_category is \
"other" or "unknown". UK "midweight" means "mid". Never use an organizational-function word \
like "manager" here — that belongs in track, not level.
- track: "ic" (individual contributor), "management", "unknown" (title genuinely doesn't \
disclose which), or null if role_category is "other" or "unknown". "Lead" is ambiguous — \
infer from context whether it is a senior IC or a first-line management role; if you truly \
can't tell, use "unknown" rather than guessing. An "Engineering Manager"/"Design Manager"/ \
"Product Manager, X Team"-shaped title is track "management" with specialization set to the \
underlying technical/craft domain (your best real inference, e.g. "Software Engineer") — \
never put the organizational word itself into specialization.
- job_function: only when role_category is "other" — one of "Sales & Business Development", \
"Marketing & Communications", "Customer Success & Support", "People & Talent", "Legal & \
Compliance", "Finance & Accounting", "Operations & Business Ops", "IT & Technical Support", \
"Learning & Development", "Executive & Administrative", "Other Non-Tech" (genuinely doesn't \
fit any of the above), or "unknown" (confidently non-tech, but the title doesn't disclose \
which function). "Delivery Manager" / "Service Delivery Manager" / "Scrum Master" / "Agile \
Coach" are role_category "other", job_function "Operations & Business Ops" — real production \
data confirms these are not Product Manager, despite sounding tech-adjacent. Always null when \
role_category is "Designer", "Product Manager", \
"Engineer", or "unknown" — this field only ever describes what a real "other" posting actually \
is, never a fourth tracked category.
- classification_confidence: your own self-reported confidence in this classification — \
"low", "medium", or "high". This is your honest assessment, not a claim of measured accuracy.

Example: "Product Manager - Health Policy" is role_category "other", job_function "Other \
Non-Tech" — nominally a Product Manager title, but a health-policy role, not a tech-market \
role this taxonomy tracks. Titles with a tech-unrelated qualifier like this should be "other" \
even if the base title matches. Example: "Digital Lead" is role_category "unknown" — it might \
be Design, Product, or Engineering, but the title alone doesn't say which, so guessing would \
be worse than admitting the uncertainty.

Two consistency rules from real classified data, apply them exactly:
- "Technical Program Manager" is role_category "Product Manager", specialization "Technical \
Program Manager" — every time, regardless of any team/division qualifier after it. A generic \
"Program Manager" or "Project Manager" with no technical-product qualifier stays "other" \
(job_function "Operations & Business Ops" unless something more specific applies) — it is not \
tech-specific enough on its own.
- "Data Scientist" is role_category "Engineer", specialization "Data Scientist" — every time, \
regardless of any team/division qualifier after it (e.g. "Data Scientist, Core \
Infrastructure" is still Engineer/Data Scientist — the qualifier names the team, not a \
different occupation).

Return strictly a JSON array, one object per input posting, each with an "id" field copied \
from the input plus the six fields above. No prose, no markdown fences."""

# Description-assisted recovery pass (2026-09-06 —
# changes/2026-09-06-unknown-reclassification.md). Same closed sets and output shape as
# SYSTEM_INSTRUCTION; the only change is that the model now also has the job description and
# must use it to fill the gaps the title alone left (any of role_category / specialization /
# level / track / job_function that came back "unknown").
RECOVERY_SYSTEM_INSTRUCTION = SYSTEM_INSTRUCTION + """

You are re-examining a posting that a title-only pass could not fully classify — one or more \
of role_category, specialization, level, track, and job_function came back "unknown". You now \
also have the job description. Use it to fill those gaps: give the real role_category \
(Designer / Product Manager / Engineer), specialization, level, and track wherever the \
description makes them clear; use "other" for role_category (plus a real job_function, never \
left "unknown" if the description discloses it) if the description shows this is not one of \
the three tracked tech occupations; and keep a field "unknown" ONLY if the description still \
genuinely does not disclose it. Re-answer all six fields, not just the ones that were unknown \
before."""

# Provenance marker written to classifications.model for a row this pass produced — also the
# idempotency key (a re-run skips rows already carrying this value). Bump the suffix if the
# recovery model changes so the new model re-does the set.
RECOVERY_MODEL = "gemini-3.6-flash"
CLASSIFICATION_RECOVERY_MODEL = f"{RECOVERY_MODEL}+description"


def _build_prompt(postings: list[dict]) -> str:
    lines = [f'{{"id": "{p["id"]}", "title": {json.dumps(p["title"])}}}' for p in postings]
    return "Classify these postings:\n[" + ",\n".join(lines) + "]"


def build_unknown_recovery_prompt(posting: dict) -> str:
    """One {id, title, description} posting -> a single-posting classification prompt for the
    description-assisted recovery pass. See reclassify_unknowns.py."""
    return "Classify this posting:\n[" + json.dumps({
        "id": posting["id"],
        "title": posting["title"],
        "description": posting.get("description", ""),
    }) + "]"


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
                rp.title, c.role_category, c.specialization, c.level, c.track,
                c.classification_confidence
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
            "specialization": row[2],
            "level": row[3],
            "track": row[4],
            "classification_confidence": row[5],
        }
        for row in rows
    }


def _validate(entry: dict) -> dict:
    """
    Coerce an entry to the closed sets. `role_category: "unknown"` is a valid,
    distinct outcome from "other" (see module docstring) — only a genuinely
    invalid/unparseable value falls back to "other". `classification_confidence`
    defaults to "low" when missing or invalid, consistent with this codebase's
    bias toward under-claiming rather than assuming the most generous reading
    of an uncertain result. `job_function` (2026-09-21) is only ever non-null
    when role_category is "other" — see job-classification.md — Job Function;
    it is never populated for "unknown" (not even confident the posting is
    non-tech yet) or for a tracked category (would make it a de facto fourth
    Role Category, which it must never be).
    """
    role_category = entry.get("role_category")
    confidence = entry.get("classification_confidence")
    confidence = confidence if confidence in CLASSIFICATION_CONFIDENCE_VALUES else "low"

    if role_category == "unknown":
        return {
            "id": entry.get("id"),
            "role_category": "unknown",
            "specialization": None,
            "level": None,
            "track": None,
            "job_function": None,
            "classification_confidence": confidence,
        }

    if role_category not in ROLE_CATEGORIES:
        job_function = entry.get("job_function")
        job_function = job_function if (job_function in JOB_FUNCTIONS or job_function == "unknown") else "unknown"
        return {
            "id": entry.get("id"),
            "role_category": "other",
            "specialization": None,
            "level": None,
            "track": None,
            "job_function": job_function,
            "classification_confidence": confidence,
        }

    specialization = entry.get("specialization")
    level = entry.get("level")
    track = entry.get("track")
    return {
        "id": entry.get("id"),
        "role_category": role_category,
        "specialization": specialization if specialization == "unknown" else (specialization or None),
        "level": level if (level in LEVEL_LADDER or level == "unknown") else None,
        "track": track if (track in TRACKS or track == "unknown") else None,
        "job_function": None,
        "classification_confidence": confidence,
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


async def _complete_with_retry(prompt: str, system: str, request_counter: dict) -> str:
    """
    request_counter is a mutable {"requests": int}, incremented once per actual
    API call attempt — success or failure, including every retry — so the
    caller can track real request usage against the daily quota even when a
    batch ultimately fails after exhausting retries. A failed attempt still
    consumed a real request; `llm_classified` (successful titles) alone would
    undercount it. See backend/specs/market-health/api.md — Business Logic —
    Classification — Cross-run daily budget.
    """
    # Dedicated key, separate from /api/chat's GEMINI_API_KEY — classification
    # and live chat must never compete for the same quota pool (see
    # backend/specs/market-health/api.md — Scheduled ingestion agent).
    provider = providers.gemini(CLASSIFICATION_MODEL, api_key=os.environ["GEMINI_API_KEY_CLASSIFICATION"])
    for attempt in range(1, MAX_RETRIES + 1):
        request_counter["requests"] += 1
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


async def classify_batch(postings: list[dict], request_counter: dict) -> list[dict]:
    """
    Classify a batch of up to BATCH_SIZE {id, title} postings.
    Returns one validated classification dict per input posting, in the same
    order requested — postings the model omits are classified "other".
    `request_counter` — see _complete_with_retry.
    """
    if not postings:
        return []

    response_text = await _complete_with_retry(_build_prompt(postings), SYSTEM_INSTRUCTION, request_counter)
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
                    (posting_id, role_category, specialization, level, track,
                     classification_confidence, taxonomy_version, model, classified_at,
                     job_function)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (posting_id) DO NOTHING
                """,
                [
                    (
                        c["id"],
                        c["role_category"],
                        c["specialization"],
                        c["level"],
                        c["track"],
                        c.get("classification_confidence", "low"),
                        TAXONOMY_VERSION,
                        c.get("model", CLASSIFICATION_MODEL),
                        classified_at,
                        c.get("job_function"),
                    )
                    for c in classifications
                ],
            )


async def classify_postings(postings: list[dict], already_used_today: int = 0) -> dict:
    """
    Classify and store an arbitrary-length list of {id, title} postings.
    Returns stats for the IngestionRun record: {cache_hits,
    heuristic_filtered, llm_classified, other_count, total_classified,
    stopped_early, budget_reached, llm_requests_used}. `postings` is expected
    oldest-first (see raw_postings.get_all_unclassified) so that when demand
    exceeds this run's budget, the longest-waiting backlog is what actually
    gets classified.

    `already_used_today` — real LLM requests already made by other runs today
    (see ingestion_runs.get_requests_used_today), summed across all of today's
    runs, not just this one. This run's effective batch ceiling is
    `min(MAX_BATCHES_PER_RUN, DAILY_REQUEST_BUDGET - RETRY_HEADROOM -
    already_used_today)`, floored at 0 — fixes a real gap where multiple
    same-day runs each got their own fresh MAX_BATCHES_PER_RUN allowance,
    together exceeding the real daily quota. See backend/specs/market-health/
    api.md — Business Logic — Classification — Cross-run daily budget.

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
        "stopped_early": False, "budget_reached": False, "llm_requests_used": 0,
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

    # job_function computed per-title (not a shared dict) — the denylist already knows exactly
    # which functional cluster matched, at zero LLM cost (see _denylisted_job_function).
    denylisted_results = {
        t: {
            "role_category": "other", "specialization": None,
            "level": None, "track": None, "job_function": _denylisted_job_function(t),
            "classification_confidence": "high", "model": HEURISTIC_FILTER_MODEL,
        }
        for t in denylisted_titles
    }
    heuristic_rows = _rows_for(denylisted_titles, denylisted_results)
    insert_classifications(heuristic_rows)
    heuristic_filtered = len(heuristic_rows)
    other_count += _count_other(heuristic_rows)

    llm_classified = 0
    stopped_early = False
    budget_reached = False
    batches_attempted = 0
    request_counter = {"requests": 0}

    # Cross-run daily clamp — see backend/specs/market-health/api.md — Business
    # Logic — Classification — Cross-run daily budget. Floored at 0: if prior
    # runs today already used up the budget, this run attempts zero LLM
    # batches (cache hits and heuristic filtering above still happen for free).
    effective_batch_cap = max(0, min(
        MAX_BATCHES_PER_RUN,
        DAILY_REQUEST_BUDGET - RETRY_HEADROOM - already_used_today,
    ))

    num_batches = (len(llm_titles) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_num, i in enumerate(range(0, len(llm_titles), BATCH_SIZE), start=1):
        if batches_attempted >= effective_batch_cap:
            budget_reached = True
            logger.info(
                "classify_postings: reached today's effective batch cap (%d, already used "
                "%d/%d of the daily budget), %d/%d batches left for a future run",
                effective_batch_cap, already_used_today, DAILY_REQUEST_BUDGET,
                num_batches - batches_attempted, num_batches,
            )
            break
        title_batch = llm_titles[i : i + BATCH_SIZE]
        try:
            # classify_batch takes {id, title} pairs; here each unique title
            # stands in as its own id since we're classifying titles, not
            # individual postings.
            results = await classify_batch([{"id": t, "title": t} for t in title_batch], request_counter)
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
        if batch_num < num_batches and batches_attempted < effective_batch_cap:
            await asyncio.sleep(SECONDS_BETWEEN_BATCHES)

    return {
        "cache_hits": cache_hits,
        "heuristic_filtered": heuristic_filtered,
        "llm_classified": llm_classified,
        "other_count": other_count,
        "total_classified": cache_hits + heuristic_filtered + llm_classified,
        "stopped_early": stopped_early,
        "budget_reached": budget_reached,
        "llm_requests_used": request_counter["requests"],
    }


# ---------------------------------------------------------------------------
# One-time taxonomy reprocessing (2026-08-11) — see backend/specs/market-health/
# api.md — Business Logic — Taxonomy reprocessing. Not part of the ongoing
# daily pipeline; kept separate from classify_postings()/insert_classifications()
# above rather than folded in, since reprocessing's overwrite-on-purpose
# behavior is different in kind from normal operation's "classified at most
# once" invariant and should stay visibly distinct in code.
# ---------------------------------------------------------------------------

def _get_title_cache_for_version(titles: list[str], taxonomy_version: str) -> dict[str, dict]:
    """
    Same idea as _get_title_cache, but only counts a title as cached if it was
    already reprocessed onto `taxonomy_version` specifically — a title still
    sitting on a stale version must not be treated as cached just because it
    has *some* classification row, or reprocessing would never actually
    re-derive it. Lets a multi-day reprocessing run converge efficiently:
    titles already reprocessed by an earlier day's run of this same pass are
    skipped on subsequent days, while everything still stale is not.
    """
    if not titles:
        return {}
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT ON (rp.title)
                rp.title, c.role_category, c.specialization, c.level, c.track,
                c.classification_confidence
            FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            WHERE rp.title = ANY(%s) AND c.taxonomy_version = %s
            ORDER BY rp.title, c.classified_at ASC
            """,
            (titles, taxonomy_version),
        ).fetchall()
    return {
        row[0]: {
            "role_category": row[1], "specialization": row[2], "level": row[3],
            "track": row[4], "classification_confidence": row[5],
        }
        for row in rows
    }


def update_classifications(classifications: list[dict]) -> None:
    """
    UPDATE-in-place variant of insert_classifications(), for reprocessing
    only. classifications.posting_id is UNIQUE (Data Models — Classification)
    — the schema has no way to hold two taxonomy_versions for the same
    posting simultaneously, so reprocessing a posting means overwriting its
    existing row's taxonomy-bearing fields, not inserting a second one.
    Deliberately not merged into insert_classifications()'s ON CONFLICT
    clause: that function's DO NOTHING is a real safety net for the ongoing
    daily pipeline (posting_id's UNIQUE constraint is the DB-level guarantee
    a posting is classified "at most once" under normal operation), and this
    function's very different, overwrite-on-purpose behavior should stay
    visibly separate rather than silently share a function whose behavior
    quietly changed.
    """
    if not classifications:
        return
    classified_at = datetime.now(timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                UPDATE classifications
                SET role_category = %s, specialization = %s, level = %s, track = %s,
                    classification_confidence = %s, taxonomy_version = %s, model = %s,
                    classified_at = %s, job_function = %s
                WHERE posting_id = %s
                """,
                [
                    (
                        c["role_category"], c["specialization"], c["level"], c["track"],
                        c.get("classification_confidence", "low"), TAXONOMY_VERSION,
                        c.get("model", CLASSIFICATION_MODEL), classified_at,
                        c.get("job_function"), c["id"],
                    )
                    for c in classifications
                ],
            )


async def reclassify_all(postings: list[dict], already_used_today: int = 0) -> dict:
    """
    Reprocess an arbitrary-length list of {id, title} postings onto the
    current TAXONOMY_VERSION, regardless of whether they already have a
    classification. Mirrors classify_postings()'s structure closely
    (in-run title dedup, denylist pre-filter, batching, cross-run daily
    budget) with two deliberate differences: (1) the cross-run cache lookup
    is scoped to this taxonomy_version only (_get_title_cache_for_version),
    never reusing a stale-version result, and (2) writes go through
    update_classifications() (UPDATE), never insert_classifications()
    (INSERT ... ON CONFLICT DO NOTHING), since every posting already has a
    row. `postings` is expected oldest-first
    (raw_postings.get_all_for_reclassification()). Shares the same
    DAILY_REQUEST_BUDGET/GEMINI_API_KEY_CLASSIFICATION as ongoing daily
    classification — this is a larger-than-usual backlog on the same budget,
    not a separately budgeted concern the way requirements extraction is.
    Returns the same stats shape as classify_postings().
    """
    empty_stats = {
        "cache_hits": 0, "heuristic_filtered": 0, "llm_classified": 0,
        "other_count": 0, "total_classified": 0,
        "stopped_early": False, "budget_reached": False, "llm_requests_used": 0,
    }
    if not postings:
        return empty_stats

    postings_by_title: dict[str, list[dict]] = {}
    for p in postings:
        postings_by_title.setdefault(p["title"], []).append(p)

    unique_titles = list(postings_by_title.keys())
    cache = _get_title_cache_for_version(unique_titles, TAXONOMY_VERSION)
    novel_titles = [t for t in unique_titles if t not in cache]
    denylisted_titles = [t for t in novel_titles if _is_denylisted(t)]
    denylisted_set = set(denylisted_titles)
    llm_titles = [t for t in novel_titles if t not in denylisted_set]

    logger.info(
        "reclassify_all: %d postings, %d unique titles (%d already on %s, %d heuristic-filtered, "
        "%d need an LLM call)",
        len(postings), len(unique_titles), len(unique_titles) - len(novel_titles),
        TAXONOMY_VERSION, len(denylisted_titles), len(llm_titles),
    )

    def _rows_for(titles: list[str], result_by_title: dict[str, dict]) -> list[dict]:
        return [
            {"id": p["id"], **{k: v for k, v in result_by_title[title].items() if k != "id"}}
            for title in titles
            for p in postings_by_title[title]
        ]

    def _count_other(rows: list[dict]) -> int:
        return sum(1 for r in rows if r["role_category"] == "other")

    already_current_titles = [t for t in unique_titles if t in cache]
    cache_hits = sum(len(postings_by_title[t]) for t in already_current_titles)

    denylisted_results = {
        t: {
            "role_category": "other", "specialization": None,
            "level": None, "track": None, "job_function": _denylisted_job_function(t),
            "classification_confidence": "high", "model": HEURISTIC_FILTER_MODEL,
        }
        for t in denylisted_titles
    }
    heuristic_rows = _rows_for(denylisted_titles, denylisted_results)
    update_classifications(heuristic_rows)
    heuristic_filtered = len(heuristic_rows)
    other_count = _count_other(heuristic_rows)

    llm_classified = 0
    stopped_early = False
    budget_reached = False
    batches_attempted = 0
    request_counter = {"requests": 0}

    effective_batch_cap = max(0, min(
        MAX_BATCHES_PER_RUN,
        DAILY_REQUEST_BUDGET - RETRY_HEADROOM - already_used_today,
    ))

    num_batches = (len(llm_titles) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_num, i in enumerate(range(0, len(llm_titles), BATCH_SIZE), start=1):
        if batches_attempted >= effective_batch_cap:
            budget_reached = True
            logger.info(
                "reclassify_all: reached today's effective batch cap (%d, already used "
                "%d/%d of the daily budget), %d/%d batches left for a future run",
                effective_batch_cap, already_used_today, DAILY_REQUEST_BUDGET,
                num_batches - batches_attempted, num_batches,
            )
            break
        title_batch = llm_titles[i : i + BATCH_SIZE]
        try:
            results = await classify_batch([{"id": t, "title": t} for t in title_batch], request_counter)
        except Exception as exc:
            logger.error(
                "reclassify_all batch %d/%d failed, stopping this run early (already-reprocessed "
                "titles remain safely persisted): %s", batch_num, num_batches, exc,
            )
            stopped_early = True
            break
        fresh = dict(zip(title_batch, results))
        fresh_rows = _rows_for(title_batch, fresh)
        update_classifications(fresh_rows)
        llm_classified += len(fresh_rows)
        other_count += _count_other(fresh_rows)
        batches_attempted += 1
        logger.info("reclassified batch %d/%d (%d unique titles)", batch_num, num_batches, len(title_batch))
        if batch_num < num_batches and batches_attempted < effective_batch_cap:
            await asyncio.sleep(SECONDS_BETWEEN_BATCHES)

    return {
        "cache_hits": cache_hits,
        "heuristic_filtered": heuristic_filtered,
        "llm_classified": llm_classified,
        "other_count": other_count,
        "total_classified": cache_hits + heuristic_filtered + llm_classified,
        "stopped_early": stopped_early,
        "budget_reached": budget_reached,
        "llm_requests_used": request_counter["requests"],
    }


# ---------------------------------------------------------------------------
# Pipeline visibility admin dashboard (2026-08-16) — read-only aggregates.
# See backend/specs/pipeline-visibility/api.md — API Endpoints — GET /admin/.
# ---------------------------------------------------------------------------

DISTRIBUTION_DIMENSIONS = (
    "role_category", "level", "track", "specialization", "classification_confidence",
    "job_function",
)


def get_classification_distribution() -> dict[str, list[dict]]:
    """
    Value counts for every classification dimension the Overview page charts
    — one GROUP BY per dimension, each as its own small query rather than one
    big pivot, since the dimensions aren't mutually exclusive slices of the
    same rows. NULL values (role_category not yet classified) are excluded —
    that's a "not yet classified" state, not a classification value itself.
    """
    distribution: dict[str, list[dict]] = {}
    with get_connection() as conn:
        for dimension in DISTRIBUTION_DIMENSIONS:
            rows = conn.execute(
                f"""
                SELECT {dimension}, COUNT(*) FROM classifications
                WHERE {dimension} IS NOT NULL
                GROUP BY {dimension}
                ORDER BY COUNT(*) DESC
                """
            ).fetchall()
            distribution[dimension] = [{"value": r[0], "count": r[1]} for r in rows]
    return distribution


def get_taxonomy_version_breakdown() -> list[dict]:
    """
    Count of classified postings per taxonomy_version, flagging which one is
    TAXONOMY_VERSION (current) — makes an in-flight reprocessing backlog (like
    changes/2026-08-11-classification-taxonomy-redesign.md's) visibly drain
    instead of being a silent background fact. See backend/specs/
    pipeline-visibility/api.md — API Endpoints — GET /admin/.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT taxonomy_version, COUNT(*) FROM classifications GROUP BY taxonomy_version ORDER BY COUNT(*) DESC"
        ).fetchall()
    return [
        {"version": r[0], "count": r[1], "is_current": r[0] == TAXONOMY_VERSION}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Emerging taxonomy candidates (2026-09-21) — see outcomes/pipeline-processing-
# visibility.md ("Extended 2026-09-21") and changes/2026-09-21-emerging-role-
# detection.md. Detection/reporting only — this never coerces, discards, or
# renames anything; it surfaces real recurring off-canon values for a human
# (PM) to decide whether the next taxonomy revision should formalize them,
# same "reviewing raw title frequency is how this taxonomy gets revised over
# time" principle job-classification.md's own Raw Title section already
# names, just made a real, repeatable, on-demand query instead of an ad hoc
# one-off.
# ---------------------------------------------------------------------------

MIN_EMERGING_OCCURRENCES = 5  # curated, not derived — small enough to catch a real early
                              # signal, large enough that a single outlier posting doesn't
                              # trigger a false "emerging role." Tune as real monthly runs
                              # show whether this threshold is too noisy or too quiet.


def get_emerging_taxonomy_candidates(min_occurrences: int = MIN_EMERGING_OCCURRENCES) -> dict:
    """
    Real, on-demand signal for "what would the next taxonomy revision need to look at" —
    three independent signals, each grounded in production data, none of them mutated by
    running this:

    1. `off_canon_specializations` — specialization values already appearing under a tracked
       Role Category that aren't in SPECIALIZATIONS (the same canonical dict the LLM prompt
       is built from), grouped by category, ordered by real frequency. A value showing up
       here either recurs enough to be worth formalizing, or is genuine LLM phrasing noise —
       this function doesn't distinguish the two; a human does, same as every prior
       taxonomy revision in this project's history.
    2. `other_non_tech_titles` — real titles landing job_function = "Other Non-Tech" (the
       Job Function catch-all), grouped by raw title, ordered by frequency. A recurring
       cluster here is the same signal that justified promoting the pre-sales engineering
       cluster into real specializations on 2026-09-21 — just watched going forward instead
       of found once by hand.
    3. `unknown_rate` — role_category = "unknown" volume and share of total, a classification-
       quality signal distinct from both of the above (see job-classification.md — Unknown vs.
       Other): a rising rate means titles aren't giving the classifier enough to work with,
       not that new categories are needed.

    Both `off_canon_specializations` and `other_non_tech_titles` are capped to results with at
    least `min_occurrences` real postings — a single unusual title is not "emerging," it's
    noise; see MIN_EMERGING_OCCURRENCES.
    """
    with get_connection() as conn:
        off_canon_rows = conn.execute(
            """
            SELECT role_category, specialization, COUNT(*) AS n
            FROM classifications
            WHERE role_category = ANY(%s) AND specialization IS NOT NULL
                AND specialization != 'unknown'
            GROUP BY role_category, specialization
            HAVING COUNT(*) >= %s
            ORDER BY role_category, n DESC
            """,
            (list(ROLE_CATEGORIES), min_occurrences),
        ).fetchall()
        off_canon_specializations = [
            {"role_category": r[0], "specialization": r[1], "count": r[2]}
            for r in off_canon_rows
            if r[1] not in SPECIALIZATIONS.get(r[0], ())
        ]

        other_non_tech_rows = conn.execute(
            """
            SELECT rp.title, COUNT(*) AS n
            FROM classifications c
            JOIN raw_postings rp ON rp.id = c.posting_id
            WHERE c.job_function = 'Other Non-Tech'
            GROUP BY rp.title
            HAVING COUNT(*) >= %s
            ORDER BY n DESC
            """,
            (min_occurrences,),
        ).fetchall()
        other_non_tech_titles = [{"title": r[0], "count": r[1]} for r in other_non_tech_rows]

        unknown_row = conn.execute(
            "SELECT COUNT(*) FILTER (WHERE role_category = 'unknown'), COUNT(*) FROM classifications"
        ).fetchone()
        unknown_count, total_classified = unknown_row

    return {
        "off_canon_specializations": off_canon_specializations,
        "other_non_tech_titles": other_non_tech_titles,
        "unknown_rate": {
            "count": unknown_count,
            "total_classified": total_classified,
            "share": round(unknown_count / total_classified, 4) if total_classified else 0.0,
        },
        "min_occurrences": min_occurrences,
        "taxonomy_version": TAXONOMY_VERSION,
    }


def get_distinct_specializations() -> list[str]:
    """Distinct non-null specialization values in use today — backs the
    admin Postings filter dropdown (backend/specs/pipeline-visibility/api.md).
    Not the full closed taxonomy list (job-classification.md defines that);
    just what's actually present, so the dropdown never offers a value with
    zero matching postings."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT specialization FROM classifications WHERE specialization IS NOT NULL ORDER BY specialization"
        ).fetchall()
    return [r[0] for r in rows]
