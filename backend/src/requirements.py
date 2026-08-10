"""
LLM-driven requirements extraction — Requirements Signal.

Reads a posting's full *description* (not its title) and extracts skills,
education level, language requirements, a responsibilities summary, and a
freeform catch-all, per the closed-set-plus-catch-all taxonomy in
design/market-health/job-classification.md — Requirements Taxonomy.

Deliberately structured as its own module, own dedicated Gemini key, and own
daily budget, kept separate from classification.py's — see
backend/specs/market-health/api.md — Business Logic — Requirements extraction.
This is per-posting, not per-title: two postings sharing a title can have
completely different actual requirements, so there is no cache shortcut here
the way classification has.
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import re
from datetime import datetime, timezone

from db import get_connection
from llm import providers

logger = logging.getLogger(__name__)

EXTRACTION_MODEL = "gemini-flash-latest"

# Closed per Role Category — design/market-health/job-classification.md — Skills.
# Starts narrow, widens once real extraction data justifies it, same discipline
# as sub-specializations.
SKILLS_BY_ROLE_CATEGORY: dict[str, list[str]] = {
    "Designer": [
        "Figma / design tooling", "Design systems", "UX research", "Prototyping",
        "Visual/UI design", "Accessibility", "Front-end coding (HTML/CSS/JS)",
        "Data & analytics literacy", "AI-assisted design tools",
    ],
    "Product Manager": [
        "Data analysis / SQL", "Experimentation (A/B testing)",
        "Roadmapping & prioritization", "Stakeholder management",
        "Technical/API fluency", "User research", "AI/ML product experience",
        "Business strategy (GTM, pricing)",
    ],
    "Engineer": [
        "Frontend frameworks", "Backend frameworks", "Cloud/infrastructure",
        "Databases", "System design", "ML/AI", "Mobile", "DevOps/SRE", "Security",
    ],
}

EDUCATION_LEVELS = ["not_mentioned", "bootcamp_or_equivalent", "bachelors", "masters", "phd"]
SKILL_REQUIREMENT_LEVELS = {"must_have", "nice_to_have"}
LANGUAGE_REQUIREMENT_LEVELS = {"required", "preferred"}

# Batch size is materially smaller than classification's BATCH_SIZE=100 — each
# item now needs a full description as input and a richer structured output
# (skills + education + language + a responsibilities summary + catch-all),
# not four short classification fields. Not spec'd exactly — tuned as real
# data comes in, same precedent as classification's BATCH_SIZE and denylist.
BATCH_SIZE = 15
MAX_DESCRIPTION_CHARS = 3000  # truncate very long descriptions before prompting
SECONDS_BETWEEN_BATCHES = 13
MAX_RETRIES = 5
RETRYABLE_ERROR_RETRY_DELAY = 60
MAX_BATCHES_PER_RUN = 12

# Own dedicated daily budget — see backend/specs/market-health/api.md —
# Business Logic — Requirements extraction. Kept separate from
# classification.py's DAILY_REQUEST_BUDGET/RETRY_HEADROOM so a heavy day for
# one can't silently starve the other.
REQUIREMENTS_DAILY_REQUEST_BUDGET = 20
REQUIREMENTS_RETRY_HEADROOM = 8

RETRYABLE_STATUS_CODES = {"429", "500", "502", "503", "504"}


def _is_retryable_error(exc: Exception) -> bool:
    """Same detection approach as classification.py's — see that module for
    why string-matching is used instead of a provider-specific exception type."""
    text = str(exc).lower()
    if any(code in text for code in RETRYABLE_STATUS_CODES):
        return True
    return any(
        keyword in text
        for keyword in ("resource_exhausted", "rate limit", "unavailable", "timeout", "connection")
    )


_TAG_RE = re.compile(r"<[^<]+?>")


def _extract_description(source: str, raw_response: dict) -> str:
    """
    Pull the description text out of a source's raw_response shape, clean it
    (unescape HTML entities, strip tags — pure token overhead for extraction
    purposes), and truncate. Field name differs per source, same as
    compensation extraction's per-source field selection.
    """
    if source == "greenhouse":
        raw = raw_response.get("content", "")
    elif source == "lever":
        raw = raw_response.get("descriptionPlain", "") or raw_response.get("descriptionBodyPlain", "")
    elif source == "ashby":
        raw = raw_response.get("descriptionPlain", "")
    else:
        raw = ""
    cleaned = _TAG_RE.sub(" ", html.unescape(raw or "")).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:MAX_DESCRIPTION_CHARS]


def _system_instruction(role_category: str) -> str:
    skills = SKILLS_BY_ROLE_CATEGORY[role_category]
    skills_list = ", ".join(f'"{s}"' for s in skills)
    return f"""You extract structured requirements from {role_category} job posting \
descriptions. For each posting, return exactly these fields:
- education_level: one of "not_mentioned", "bootcamp_or_equivalent", "bachelors", \
"masters", "phd" — the minimum level explicitly stated. "not_mentioned" if the posting \
never states one; never infer it from context.
- skills: a list of {{"skill": ..., "requirement_level": "must_have" | "nice_to_have"}}. \
"skill" MUST be exactly one of: {skills_list}. Include a skill only if the posting \
genuinely mentions it (directly or via a clear synonym). Never invent or include a skill \
outside this exact list — mention anything else in other_requirements instead.
- languages: a list of {{"language": ..., "requirement_level": "required" | "preferred"}} \
for spoken/written language requirements only (not programming languages). Empty list if \
none mentioned.
- responsibilities_summary: a 2-4 sentence plain-language summary of the core day-to-day \
responsibilities described in the posting.
- other_requirements: a short freeform note for anything notable that doesn't fit the \
fields above — a certification, a security clearance, a portfolio requirement, a mentioned \
skill outside the fixed list above. Empty string if nothing notable.

Return strictly a JSON array, one object per input posting, each with an "id" field copied \
from the input plus the five fields above. No prose, no markdown fences."""


def _build_prompt(postings: list[dict]) -> str:
    lines = [
        f'{{"id": {json.dumps(p["id"])}, "description": {json.dumps(p["description"])}}}'
        for p in postings
    ]
    return "Extract requirements from these postings:\n[" + ",\n".join(lines) + "]"


def _parse_response(text: str) -> list[dict]:
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _validate(entry: dict, role_category: str) -> dict:
    """
    Coerce an entry to the closed sets. Anything invalid is dropped from its
    standard field and folded into other_requirements instead — never forced
    into the nearest match, never silently discarded. Mirrors
    classification.py's _validate discipline.
    """
    valid_skills = set(SKILLS_BY_ROLE_CATEGORY[role_category])
    overflow_notes: list[str] = []

    education_level = entry.get("education_level")
    if education_level not in EDUCATION_LEVELS:
        education_level = "not_mentioned"

    skills: list[dict] = []
    for s in entry.get("skills") or []:
        skill, level = s.get("skill"), s.get("requirement_level")
        if skill in valid_skills and level in SKILL_REQUIREMENT_LEVELS:
            skills.append({"skill": skill, "requirement_level": level})
        elif skill:
            overflow_notes.append(f"mentioned skill not in tracked list: {skill}")

    languages: list[dict] = []
    for entry_lang in entry.get("languages") or []:
        language, level = entry_lang.get("language"), entry_lang.get("requirement_level")
        if language and level in LANGUAGE_REQUIREMENT_LEVELS:
            languages.append({"language": language, "requirement_level": level})

    other_requirements = (entry.get("other_requirements") or "").strip()
    if overflow_notes:
        other_requirements = "; ".join(filter(None, [other_requirements, *overflow_notes]))

    return {
        "id": entry.get("id"),
        "education_level": education_level,
        "skills": skills,
        "languages": languages,
        "responsibilities_summary": (entry.get("responsibilities_summary") or "").strip() or None,
        "other_requirements": other_requirements or None,
    }


async def _complete_with_retry(prompt: str, system: str, request_counter: dict) -> str:
    provider = providers.gemini(EXTRACTION_MODEL, api_key=os.environ["GEMINI_API_KEY_REQUIREMENTS"])
    for attempt in range(1, MAX_RETRIES + 1):
        request_counter["requests"] += 1
        try:
            return await provider.complete(prompt=prompt, system=system)
        except Exception as exc:
            if not _is_retryable_error(exc) or attempt == MAX_RETRIES:
                raise
            logger.warning(
                "Requirements extraction: retryable error (attempt %d/%d), retrying in %ds: %s",
                attempt, MAX_RETRIES, RETRYABLE_ERROR_RETRY_DELAY, exc,
            )
            await asyncio.sleep(RETRYABLE_ERROR_RETRY_DELAY)
    raise RuntimeError("unreachable")


async def extract_batch(postings: list[dict], role_category: str, request_counter: dict) -> list[dict]:
    """postings: [{id, description}]. Returns one validated entry per input,
    in the same order — postings the model omits get an empty/default entry."""
    if not postings:
        return []
    response_text = await _complete_with_retry(
        _build_prompt(postings), _system_instruction(role_category), request_counter
    )
    parsed = {entry.get("id"): _validate(entry, role_category) for entry in _parse_response(response_text)}
    default = {
        "education_level": "not_mentioned", "skills": [], "languages": [],
        "responsibilities_summary": None, "other_requirements": None,
    }
    return [parsed.get(p["id"], {**default, "id": p["id"]}) for p in postings]


def insert_requirements(entries: list[dict]) -> None:
    """Writes posting_requirements + posting_skills + posting_languages for a
    batch of validated entries. PRIMARY KEY / UNIQUE constraints on all three
    tables enforce "extracted at most once per posting" at the database
    level, same discipline as classifications.posting_id."""
    if not entries:
        return
    extracted_at = datetime.now(timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO posting_requirements
                    (posting_id, education_level, responsibilities_summary,
                     other_requirements, model, extracted_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (posting_id) DO NOTHING
                """,
                [
                    (e["id"], e["education_level"], e["responsibilities_summary"],
                     e["other_requirements"], EXTRACTION_MODEL, extracted_at)
                    for e in entries
                ],
            )
            skill_rows = [
                (e["id"], s["skill"], s["requirement_level"])
                for e in entries for s in e["skills"]
            ]
            if skill_rows:
                cur.executemany(
                    """
                    INSERT INTO posting_skills (posting_id, skill, requirement_level)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (posting_id, skill) DO NOTHING
                    """,
                    skill_rows,
                )
            language_rows = [
                (e["id"], lang["language"], lang["requirement_level"])
                for e in entries for lang in e["languages"]
            ]
            if language_rows:
                cur.executemany(
                    """
                    INSERT INTO posting_languages (posting_id, language, requirement_level)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (posting_id, language) DO NOTHING
                    """,
                    language_rows,
                )


def _group_into_batches(postings: list[dict]) -> list[tuple[str, list[dict]]]:
    """
    Chunk the oldest-first list into (role_category, batch) groups of up to
    BATCH_SIZE, starting a new batch whenever the category changes — keeps
    each LLM call single-category (so one closed skill list applies) while
    staying as close to true oldest-first order as that constraint allows.
    """
    batches: list[tuple[str, list[dict]]] = []
    current_category: str | None = None
    current: list[dict] = []
    for p in postings:
        if p["role_category"] != current_category or len(current) >= BATCH_SIZE:
            if current:
                batches.append((current_category, current))
            current_category = p["role_category"]
            current = []
        current.append(p)
    if current:
        batches.append((current_category, current))
    return batches


async def extract_requirements(postings: list[dict], already_used_today: int = 0) -> dict:
    """
    postings: what raw_postings.get_all_needing_requirements() returns
    ([{id, source, raw_response, role_category}], oldest-first).

    Returns stats for the IngestionRun record: {requirements_extracted,
    requirements_requests_used, requirements_budget_reached, stopped_early}.

    already_used_today — real requests already made by other runs today
    against THIS pipeline's own daily budget (separate from classification's
    — see backend/specs/market-health/api.md — Business Logic — Requirements
    extraction). Effective per-run cap is
    min(MAX_BATCHES_PER_RUN, REQUIREMENTS_DAILY_REQUEST_BUDGET -
    REQUIREMENTS_RETRY_HEADROOM - already_used_today), floored at 0.
    """
    empty_stats = {
        "requirements_extracted": 0, "requirements_requests_used": 0,
        "requirements_budget_reached": False, "stopped_early": False,
    }
    if not postings:
        return empty_stats

    effective_batch_cap = max(0, min(
        MAX_BATCHES_PER_RUN,
        REQUIREMENTS_DAILY_REQUEST_BUDGET - REQUIREMENTS_RETRY_HEADROOM - already_used_today,
    ))

    prepped = [
        {"id": p["id"], "role_category": p["role_category"],
         "description": _extract_description(p["source"], p["raw_response"])}
        for p in postings
    ]
    batches = _group_into_batches(prepped)

    request_counter = {"requests": 0}
    extracted = 0
    stopped_early = False
    budget_reached = False
    batches_attempted = 0
    num_batches = len(batches)

    for batch_num, (role_category, batch) in enumerate(batches, start=1):
        if batches_attempted >= effective_batch_cap:
            budget_reached = True
            logger.info(
                "extract_requirements: reached today's effective batch cap (%d, already used "
                "%d/%d of the daily budget), %d/%d batches left for a future run",
                effective_batch_cap, already_used_today, REQUIREMENTS_DAILY_REQUEST_BUDGET,
                num_batches - batches_attempted, num_batches,
            )
            break
        try:
            results = await extract_batch(
                [{"id": p["id"], "description": p["description"]} for p in batch],
                role_category, request_counter,
            )
        except Exception as exc:
            logger.error(
                "extract_requirements batch %d/%d (%s) failed, stopping this run early: %s",
                batch_num, num_batches, role_category, exc,
            )
            stopped_early = True
            break
        insert_requirements(results)
        extracted += len(results)
        batches_attempted += 1
        logger.info(
            "extract_requirements: batch %d/%d (%s, %d postings) done",
            batch_num, num_batches, role_category, len(batch),
        )
        if batch_num < num_batches and batches_attempted < effective_batch_cap:
            await asyncio.sleep(SECONDS_BETWEEN_BATCHES)

    return {
        "requirements_extracted": extracted,
        "requirements_requests_used": request_counter["requests"],
        "requirements_budget_reached": budget_reached,
        "stopped_early": stopped_early,
    }
