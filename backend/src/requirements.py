"""
LLM-driven requirements extraction — Requirements Signal.

Reads a posting's full *description* (not its title) and extracts skills,
education, years of experience, work arrangement, language requirements, a
responsibilities summary, and a freeform catch-all, per the closed-set-plus-
catch-all taxonomy in design/market-health/job-classification.md —
Requirements Taxonomy.

Deliberately structured as its own module, own dedicated Gemini key, and own
daily budget, kept separate from classification.py's — see
backend/specs/market-health/api.md — Business Logic — Requirements extraction.
This is per-posting, not per-title: two postings sharing a title can have
completely different actual requirements, so there is no cache shortcut here
the way classification has.

Skill group selection is (role_category × track × specialization)-aware
(2026-08-11) — see job-classification.md — Skills. A posting's applicable
skill groups are no longer just its role_category's hands-on technical list:
track="management" postings (any role_category) also get the People
Leadership group, and Engineer postings whose specialization is pre-sales/
customer-facing (Solutions Engineer, Solutions Architect, etc.) get Pre-sales
& Solutions instead of being scored against a technical list that could never
match their real requirements.
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

# IC/hands-on lists, closed per Role Category — job-classification.md —
# Skills. Starts narrow, widens once real extraction data justifies it, same
# discipline as specializations. Engineer gained two groups 2026-08-11 (Data
# engineering / big data, Blockchain / Web3) after real other_requirements
# text showed named tools like Kafka/Spark/Airflow and blockchain/smart-
# contract stacks recurring often enough to promote.
IC_SKILLS_BY_ROLE_CATEGORY: dict[str, list[str]] = {
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
        "Data engineering / big data", "Blockchain / Web3",
    ],
}

# Applies whenever track == "management", any role_category — added
# 2026-08-11 after real data showed 216 Engineer + 26 PM + 7 Designer
# management-track postings scored against a hands-on-only list, structurally
# guaranteed to under-report (job-classification.md — Skills).
PEOPLE_LEADERSHIP_SKILLS: list[str] = [
    "Team building & hiring", "Coaching & career development",
    "Budget & resource planning", "Cross-functional / executive stakeholder management",
    "Organizational design", "Technical strategy & oversight", "Performance management",
]

# Applies to Engineer postings whose specialization is pre-sales/customer-
# facing, not hands-on coding — added 2026-08-11 after real data showed ~265
# such postings (Solutions Engineer/Architect/Customer Engineer/Support
# Engineer/Forward Deployed) with nothing in the technical list that could
# ever match their real requirement text.
PRESALES_SOLUTIONS_SKILLS: list[str] = [
    "Technical pre-sales & discovery", "RFP / technical proposal writing",
    "Executive & technical stakeholder relationship-building",
    "Co-solutioning & partner enablement", "Technical demoing & solution design",
    "Escalation & incident troubleshooting", "Customer-facing communication",
]

PRESALES_SPECIALIZATIONS = {
    "Solutions Engineer", "Solutions Architect", "Customer Engineer",
    "Support Engineer", "Forward Deployed Engineer", "Forward Deployed Software Engineer",
}

EDUCATION_LEVELS = ["not_mentioned", "bootcamp_or_equivalent", "bachelors", "masters", "phd"]
EDUCATION_REQUIRED_VALUES = {"required", "preferred", "not_mentioned"}
WORK_ARRANGEMENT_VALUES = {"onsite", "hybrid", "remote", "not_mentioned"}
SKILL_REQUIREMENT_LEVELS = {"must_have", "nice_to_have"}
LANGUAGE_REQUIREMENT_LEVELS = {"required", "preferred"}

# Batch size is materially smaller than classification's BATCH_SIZE=100 — each
# item now needs a full description as input and a richer structured output
# (skills + education + years of experience + work arrangement + language +
# a responsibilities summary + catch-all), not four short classification
# fields. Not spec'd exactly — tuned as real data comes in, same precedent as
# classification's BATCH_SIZE and denylist.
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

YEARS_EXPERIENCE_RE = re.compile(r"\b(\d{1,2})\s*\+?\s*years?\b", re.IGNORECASE)


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


def applicable_skill_groups(role_category: str, track: str | None, specialization: str | None) -> list[str]:
    """
    The union of skill_group values a posting should be checked against, per
    job-classification.md — Skills. More than one group can apply to the same
    posting — e.g. a Designer posting with track="management" is checked
    against both People Leadership and the Designer IC list, since a Design
    Manager posting sometimes states craft expectations alongside management
    ones. The IC/hands-on list for the posting's role_category always
    applies; People Leadership and Pre-sales & Solutions are additive on top
    of it, not a replacement for it.
    """
    groups = list(IC_SKILLS_BY_ROLE_CATEGORY.get(role_category, []))
    if track == "management":
        groups.extend(PEOPLE_LEADERSHIP_SKILLS)
    if role_category == "Engineer" and specialization in PRESALES_SPECIALIZATIONS:
        groups.extend(PRESALES_SOLUTIONS_SKILLS)
    return groups


def _system_instruction(valid_skills: list[str]) -> str:
    skills_list = ", ".join(f'"{s}"' for s in valid_skills)
    return f"""You extract structured requirements from job posting descriptions. For each \
posting, return exactly these fields:
- education_level: one of "not_mentioned", "bootcamp_or_equivalent", "bachelors", \
"masters", "phd" — the minimum level explicitly stated. "not_mentioned" if the posting \
never states one; never infer it from context.
- education_required: one of "required", "preferred", "not_mentioned" — whether \
education_level is a hard requirement or a stated preference.
- equivalent_experience_accepted: true or false — true only if the posting explicitly says \
equivalent professional experience is accepted in place of the stated education_level (e.g. \
"Bachelor's degree or equivalent professional experience").
- years_experience_min: an integer, or null — the minimum years of experience explicitly \
stated (e.g. "3+ years" -> 3, "5-8 years" -> 5). null if no minimum is stated.
- work_arrangement: one of "onsite", "hybrid", "remote", "not_mentioned" — based on explicit \
statements about remote/telecommuting/on-site work, or a stated location/time-zone \
requirement implying on-site or hybrid work. "not_mentioned" if genuinely not stated.
- skills: a list of {{"skill_group": ..., "raw_skill": ..., "requirement_level": "must_have" \
| "nice_to_have"}}. "skill_group" MUST be exactly one of: {skills_list}. "raw_skill" is the \
specific mention as it actually appears in the text (e.g. "React", "AWS", "Kubernetes", \
"RFP writing") — include it even if it's essentially the same as the skill_group name. \
Include a skill only if the posting genuinely mentions it (directly or via a clear synonym). \
Never invent or include a skill_group outside this exact list — mention anything else in \
other_requirements instead.
- languages: a list of {{"language": ..., "requirement_level": "required" | "preferred"}} \
for spoken/written language requirements only (not programming languages). Empty list if \
none mentioned.
- responsibilities_summary: a 2-4 sentence plain-language summary of the core day-to-day \
responsibilities described in the posting.
- other_requirements: a short freeform note for anything notable that doesn't fit the \
fields above — a certification, a security clearance, a portfolio requirement, a mentioned \
skill outside the fixed list above. Empty string if nothing notable. **Never** include a \
salary, compensation figure, or pay range here or anywhere else in your response, even if \
the posting states one — that data is handled by a separate system; ignore compensation \
text entirely.

Return strictly a JSON array, one object per input posting, each with an "id" field copied \
from the input plus the eight fields above. No prose, no markdown fences."""


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


def _validate(entry: dict, valid_skills: list[str]) -> dict:
    """
    Coerce an entry to the closed sets. Anything invalid is dropped from its
    standard field and folded into other_requirements instead — never forced
    into the nearest match, never silently discarded. Mirrors
    classification.py's _validate discipline. `valid_skills` is the specific
    posting's applicable skill_group union (applicable_skill_groups()), not a
    fixed per-role_category list — see module docstring.
    """
    valid_skills_set = set(valid_skills)
    overflow_notes: list[str] = []

    education_level = entry.get("education_level")
    if education_level not in EDUCATION_LEVELS:
        education_level = "not_mentioned"

    education_required = entry.get("education_required")
    if education_required not in EDUCATION_REQUIRED_VALUES:
        education_required = "not_mentioned"

    equivalent_experience_accepted = bool(entry.get("equivalent_experience_accepted"))

    years_experience_min = entry.get("years_experience_min")
    if not isinstance(years_experience_min, int) or isinstance(years_experience_min, bool):
        years_experience_min = None

    work_arrangement = entry.get("work_arrangement")
    if work_arrangement not in WORK_ARRANGEMENT_VALUES:
        work_arrangement = "not_mentioned"

    skills: list[dict] = []
    for s in entry.get("skills") or []:
        skill_group, raw_skill, level = s.get("skill_group"), s.get("raw_skill"), s.get("requirement_level")
        if skill_group in valid_skills_set and level in SKILL_REQUIREMENT_LEVELS and raw_skill:
            skills.append({"skill_group": skill_group, "raw_skill": raw_skill, "requirement_level": level})
        elif skill_group or raw_skill:
            overflow_notes.append(f"mentioned skill not in tracked list: {raw_skill or skill_group}")

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
        "education_required": education_required,
        "equivalent_experience_accepted": equivalent_experience_accepted,
        "years_experience_min": years_experience_min,
        "work_arrangement": work_arrangement,
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


async def extract_batch(postings: list[dict], valid_skills: list[str], request_counter: dict) -> list[dict]:
    """postings: [{id, description}]. Returns one validated entry per input,
    in the same order — postings the model omits get an empty/default entry.
    `valid_skills` — see applicable_skill_groups(); every posting in one
    batch shares the same applicable list (see _group_into_batches)."""
    if not postings:
        return []
    response_text = await _complete_with_retry(
        _build_prompt(postings), _system_instruction(valid_skills), request_counter
    )
    parsed = {entry.get("id"): _validate(entry, valid_skills) for entry in _parse_response(response_text)}
    default = {
        "education_level": "not_mentioned", "education_required": "not_mentioned",
        "equivalent_experience_accepted": False, "years_experience_min": None,
        "work_arrangement": "not_mentioned", "skills": [], "languages": [],
        "responsibilities_summary": None, "other_requirements": None,
    }
    return [parsed.get(p["id"], {**default, "id": p["id"]}) for p in postings]


def insert_requirements(entries: list[dict]) -> None:
    """Writes posting_requirements + posting_skills + posting_languages for a
    batch of validated entries. PRIMARY KEY / UNIQUE constraints on all three
    tables enforce "extracted at most once per posting" at the database
    level, same discipline as classifications.posting_id. posting_skills'
    UNIQUE constraint moved to (posting_id, raw_skill) 2026-08-11 — see
    backend/specs/market-health/api.md — Data Models — PostingSkill."""
    if not entries:
        return
    extracted_at = datetime.now(timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO posting_requirements
                    (posting_id, education_level, education_required,
                     equivalent_experience_accepted, years_experience_min, work_arrangement,
                     responsibilities_summary, other_requirements, model, extracted_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (posting_id) DO NOTHING
                """,
                [
                    (
                        e["id"], e["education_level"], e["education_required"],
                        e["equivalent_experience_accepted"], e["years_experience_min"],
                        e["work_arrangement"], e["responsibilities_summary"],
                        e["other_requirements"], EXTRACTION_MODEL, extracted_at,
                    )
                    for e in entries
                ],
            )
            skill_rows = [
                (e["id"], s["raw_skill"], s["skill_group"], s["requirement_level"])
                for e in entries for s in e["skills"]
            ]
            if skill_rows:
                cur.executemany(
                    """
                    INSERT INTO posting_skills (posting_id, raw_skill, skill_group, requirement_level)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (posting_id, raw_skill) DO NOTHING
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


def delete_requirements_for_reprocess(posting_ids: list[str]) -> None:
    """
    Deletes existing posting_requirements/posting_skills/posting_languages
    rows for the given posting ids, so they become indistinguishable from
    "never extracted" to get_all_needing_requirements() and are picked back
    up by the normal backlog on the next run. One-time use only, by the
    2026-08-11 taxonomy reprocessing pass — see backend/specs/market-health/
    api.md — Business Logic — Taxonomy reprocessing. Callers must only pass
    ids whose classification row has already been reprocessed onto the
    current taxonomy_version (raw_postings.get_requirements_reprocess_targets)
    — deleting a posting's requirements before its classification is
    reprocessed would let it be re-extracted against stale
    role_category/track/specialization, reintroducing the exact bug this
    revision fixes.
    """
    if not posting_ids:
        return
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM posting_skills WHERE posting_id = ANY(%s)", (posting_ids,))
            cur.execute("DELETE FROM posting_languages WHERE posting_id = ANY(%s)", (posting_ids,))
            cur.execute("DELETE FROM posting_requirements WHERE posting_id = ANY(%s)", (posting_ids,))


def _group_into_batches(postings: list[dict]) -> list[tuple[list[str], list[dict]]]:
    """
    Chunk the oldest-first list into (valid_skills, batch) groups of up to
    BATCH_SIZE, starting a new batch whenever the applicable skill_group list
    changes — keeps each LLM call scoped to one consistent closed set while
    staying as close to true oldest-first order as that constraint allows.
    Grouping key changed 2026-08-11 from role_category alone to the full
    applicable-skill-group union (role_category × track × specialization),
    since two postings sharing a role_category can now need different lists.
    `postings` must each carry role_category/track/specialization.
    """
    batches: list[tuple[list[str], list[dict]]] = []
    current_key: tuple[str, ...] | None = None
    current_valid_skills: list[str] = []
    current: list[dict] = []
    for p in postings:
        key = tuple(applicable_skill_groups(p["role_category"], p.get("track"), p.get("specialization")))
        if key != current_key or len(current) >= BATCH_SIZE:
            if current:
                batches.append((current_valid_skills, current))
            current_key = key
            current_valid_skills = list(key)
            current = []
        current.append(p)
    if current:
        batches.append((current_valid_skills, current))
    return batches


async def extract_requirements(postings: list[dict], already_used_today: int = 0) -> dict:
    """
    postings: what raw_postings.get_all_needing_requirements() returns
    ([{id, source, raw_response, role_category, track, specialization}],
    oldest-first).

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
        {
            "id": p["id"], "role_category": p["role_category"],
            "track": p.get("track"), "specialization": p.get("specialization"),
            "description": _extract_description(p["source"], p["raw_response"]),
        }
        for p in postings
    ]
    batches = _group_into_batches(prepped)

    request_counter = {"requests": 0}
    extracted = 0
    stopped_early = False
    budget_reached = False
    batches_attempted = 0
    num_batches = len(batches)

    for batch_num, (valid_skills, batch) in enumerate(batches, start=1):
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
                valid_skills, request_counter,
            )
        except Exception as exc:
            logger.error(
                "extract_requirements batch %d/%d failed, stopping this run early: %s",
                batch_num, num_batches, exc,
            )
            stopped_early = True
            break
        insert_requirements(results)
        extracted += len(results)
        batches_attempted += 1
        logger.info(
            "extract_requirements: batch %d/%d (%d postings) done",
            batch_num, num_batches, len(batch),
        )
        if batch_num < num_batches and batches_attempted < effective_batch_cap:
            await asyncio.sleep(SECONDS_BETWEEN_BATCHES)

    return {
        "requirements_extracted": extracted,
        "requirements_requests_used": request_counter["requests"],
        "requirements_budget_reached": budget_reached,
        "stopped_early": stopped_early,
    }
