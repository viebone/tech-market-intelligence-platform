"""
Storage layer for the raw_postings table.

raw_postings is immutable: a row is inserted once, at first sight, and never
updated — the exact source response is the only chance to ever capture a
given posting, since a company can edit or unpublish a posting at any time
with no way to recover its prior state.
See backend/specs/market-health/api.md — Data Models — RawPosting.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from db import get_connection
from industries import industry_for
from sources.base import FetchedPosting


def existing_ids(ids: list[str]) -> set[str]:
    """Return the subset of `ids` already present in raw_postings."""
    if not ids:
        return set()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id FROM raw_postings WHERE id = ANY(%s)", (ids,)
        ).fetchall()
    return {row[0] for row in rows}


def insert_new_postings(source: str, postings: list[FetchedPosting]) -> list[str]:
    """
    Insert postings not already stored, deduped by id = f"{source}:{source_ref}"
    (see backend/specs/market-health/api.md — Data Models — RawPosting — id).
    Returns the ids of the newly inserted postings.
    """
    candidate_ids = [f"{source}:{p.source_ref}" for p in postings]
    seen = existing_ids(candidate_ids)
    new = [(pid, p) for pid, p in zip(candidate_ids, postings) if pid not in seen]
    if not new:
        return []

    fetched_at = datetime.now(timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO raw_postings (
                    id, source, source_ref, company, title, raw_response, fetched_at,
                    country, city, salary_min, salary_max, salary_currency,
                    salary_confidence, salary_extraction_method, industry
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                [
                    (
                        pid, source, p.source_ref, p.company, p.title, json.dumps(p.raw_response), fetched_at,
                        p.country, p.city, p.salary_min, p.salary_max, p.salary_currency,
                        p.salary_confidence, p.salary_extraction_method, industry_for(p.company),
                    )
                    for pid, p in new
                ],
            )

    return [pid for pid, _ in new]


def get_all_unclassified() -> list[dict]:
    """
    Postings across every source that don't have a classification row yet,
    oldest-first by fetched_at.

    Deliberately not scoped to a single source or company: classification is
    run once across everything newly ingested (see ingest.py), not once per
    company, so the title-based dedup cache in classification.py sees the
    widest possible pool for catching duplicate titles before any LLM call —
    e.g. a "Product Designer" posting surfacing on both Greenhouse and Ashby.

    Oldest-first ordering added 2026-08-04: under a bounded daily
    classification budget (see backend/specs/market-health/api.md — Business
    Logic — Classification — Per-run classification budget), which postings
    actually get classified is no longer guaranteed to be "all of them," so
    processing order now matters — the longest-waiting backlog is prioritized
    over newly-arrived postings, rather than left arbitrary.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT rp.id, rp.title
            FROM raw_postings rp
            LEFT JOIN classifications c ON c.posting_id = rp.id
            WHERE c.posting_id IS NULL
            ORDER BY rp.fetched_at ASC
            """
        ).fetchall()
    return [{"id": row[0], "title": row[1]} for row in rows]


def get_all_needing_requirements() -> list[dict]:
    """
    Real (role_category not in "other"/"unknown") classified postings with no
    posting_requirements row yet, oldest-first by fetched_at — same fairness
    principle as get_all_unclassified(). Scoped to already-classified postings
    only: no point spending a requirements-extraction call on a posting
    already known to be irrelevant, or on one whose role_category (and
    therefore applicable skill_group list — see job-classification.md —
    Skills) isn't even known yet. "unknown" excluded 2026-08-11 for the same
    reason "other" always was. See backend/specs/market-health/api.md —
    Business Logic — Requirements extraction.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT rp.id, rp.source, rp.raw_response, c.role_category, c.track, c.specialization
            FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            LEFT JOIN posting_requirements pr ON pr.posting_id = rp.id
            WHERE c.role_category NOT IN ('other', 'unknown') AND pr.posting_id IS NULL
            ORDER BY rp.fetched_at ASC
            """
        ).fetchall()
    return [
        {
            "id": row[0], "source": row[1], "raw_response": row[2],
            "role_category": row[3], "track": row[4], "specialization": row[5],
        }
        for row in rows
    ]


def get_all_for_reclassification() -> list[dict]:
    """
    Every raw_postings row, oldest-first, regardless of whether it already
    has a classification — used only by the one-time 2026-08-11 taxonomy
    reprocessing pass (see backend/specs/market-health/api.md — Business
    Logic — Taxonomy reprocessing). Distinct from get_all_unclassified(),
    which only returns postings with no classification row at all and is
    what the ongoing daily pipeline still uses.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title FROM raw_postings ORDER BY fetched_at ASC"
        ).fetchall()
    return [{"id": row[0], "title": row[1]} for row in rows]


def count_postings() -> int:
    """Total raw_postings row count — admin Overview page (backend/specs/
    pipeline-visibility/api.md)."""
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM raw_postings").fetchone()[0]


def attach_ingestion_run(run_id: int, started_at: datetime) -> None:
    """
    Backfills ingestion_run_id for every raw_postings row inserted during the
    run that just finished, added 2026-08-16 for the pipeline-visibility
    admin dashboard (backend/specs/pipeline-visibility/api.md). Can't be set
    at insert_new_postings() time — the ingestion_runs row for the current
    run is only written at the *end* of ingest.py's run(), well after
    insert_new_postings() already ran during the fetch phase (see
    ingestion_runs.record_run()'s docstring). Scoped by
    `fetched_at >= started_at AND ingestion_run_id IS NULL`: safe because
    job-sync runs are sequential, never concurrent (Railway restart policy
    NEVER, one-shot cron per DEPLOYMENT.md) — no other run's postings could
    ever fall inside this window.
    """
    with get_connection() as conn:
        conn.execute(
            "UPDATE raw_postings SET ingestion_run_id = %s "
            "WHERE ingestion_run_id IS NULL AND fetched_at >= %s",
            (run_id, started_at),
        )


# Whitelisted sort columns for list_postings() — never interpolate a raw
# `sort` query param into ORDER BY directly. Same "validate against a closed
# set" discipline role_category/skill_group already use elsewhere in this
# product, applied here to protect against SQL injection via a column name.
POSTINGS_SORT_COLUMNS = {
    "fetched_at": "fetched_at",
    "company": "company",
    "role_category": "role_category",
    "level": "level",
    "classification_confidence": "classification_confidence",
    "taxonomy_version": "taxonomy_version",
}


def list_postings(
    role_category: str | None = None,
    level: str | None = None,
    track: str | None = None,
    specialization: str | None = None,
    classification_confidence: str | None = None,
    taxonomy_version: str | None = None,
    requirements_status: str | None = None,
    source: str | None = None,
    search: str | None = None,
    sort: str = "fetched_at",
    dir: str = "desc",
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Filterable/sortable/paginated postings list — backend/specs/
    pipeline-visibility/api.md GET /admin/postings. `requirements_status` is
    computed inline (extracted/not_eligible/failed/pending), never stored —
    see backend/specs/pipeline-visibility/api.md — Business Logic —
    Requirements Status derivation. A posting with no classification row yet
    (still waiting on the earlier classification phase) falls through to
    'pending' the same as a classified-but-not-yet-attempted one — both read
    as "nothing to show yet" from the operator's point of view.
    """
    sort_column = POSTINGS_SORT_COLUMNS.get(sort, "fetched_at")
    direction = "ASC" if dir == "asc" else "DESC"
    offset = (page - 1) * page_size

    where: list[str] = []
    params: list = []
    if role_category:
        where.append("role_category = %s"); params.append(role_category)
    if level:
        where.append("level = %s"); params.append(level)
    if track:
        where.append("track = %s"); params.append(track)
    if specialization:
        where.append("specialization = %s"); params.append(specialization)
    if classification_confidence:
        where.append("classification_confidence = %s"); params.append(classification_confidence)
    if taxonomy_version:
        where.append("taxonomy_version = %s"); params.append(taxonomy_version)
    if requirements_status:
        where.append("requirements_status = %s"); params.append(requirements_status)
    if source:
        where.append("source = %s"); params.append(source)
    if search:
        where.append("(title ILIKE %s OR company ILIKE %s)")
        like = f"%{search}%"
        params.extend([like, like])
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    postings_view = """
        WITH postings_view AS (
            SELECT
                rp.id, rp.source, rp.company, rp.title, rp.fetched_at,
                c.role_category, c.level, c.track, c.specialization,
                c.classification_confidence, c.taxonomy_version,
                CASE
                    WHEN pr.posting_id IS NOT NULL THEN 'extracted'
                    WHEN c.role_category IN ('other', 'unknown') THEN 'not_eligible'
                    WHEN prf.posting_id IS NOT NULL THEN 'failed'
                    ELSE 'pending'
                END AS requirements_status
            FROM raw_postings rp
            LEFT JOIN classifications c ON c.posting_id = rp.id
            LEFT JOIN posting_requirements pr ON pr.posting_id = rp.id
            LEFT JOIN posting_requirements_failures prf ON prf.posting_id = rp.id
        )
    """
    with get_connection() as conn:
        total = conn.execute(
            f"{postings_view} SELECT COUNT(*) FROM postings_view {where_sql}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            {postings_view}
            SELECT id, source, company, title, fetched_at, role_category, level, track,
                   specialization, classification_confidence, taxonomy_version, requirements_status
            FROM postings_view
            {where_sql}
            ORDER BY {sort_column} {direction} NULLS LAST
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, offset],
        ).fetchall()

    postings = [
        {
            "id": r[0], "source": r[1], "company": r[2], "title": r[3], "fetched_at": r[4],
            "role_category": r[5], "level": r[6], "track": r[7], "specialization": r[8],
            "classification_confidence": r[9], "taxonomy_version": r[10],
            "requirements_status": r[11],
        }
        for r in rows
    ]
    return {"postings": postings, "total": total, "page": page, "page_size": page_size}


def get_posting(posting_id: str) -> dict | None:
    """Full detail for one posting — backend/specs/pipeline-visibility/api.md
    GET /admin/postings/{posting_id}. None if no such posting."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT rp.id, rp.source, rp.company, rp.title, rp.fetched_at, rp.raw_response,
                   rp.country, rp.city, rp.salary_min, rp.salary_max, rp.salary_currency,
                   rp.salary_confidence, rp.ingestion_run_id,
                   c.role_category, c.specialization, c.level, c.track,
                   c.classification_confidence, c.taxonomy_version, c.model, c.classified_at,
                   pr.education_level, pr.education_required, pr.equivalent_experience_accepted,
                   pr.years_experience_min, pr.work_arrangement, pr.responsibilities_summary,
                   pr.other_requirements, pr.model, pr.extracted_at,
                   prf.error, prf.attempt_count, prf.last_attempted_at
            FROM raw_postings rp
            LEFT JOIN classifications c ON c.posting_id = rp.id
            LEFT JOIN posting_requirements pr ON pr.posting_id = rp.id
            LEFT JOIN posting_requirements_failures prf ON prf.posting_id = rp.id
            WHERE rp.id = %s
            """,
            (posting_id,),
        ).fetchone()
        if row is None:
            return None

        skill_rows = conn.execute(
            "SELECT raw_skill, skill_group, requirement_level FROM posting_skills WHERE posting_id = %s",
            (posting_id,),
        ).fetchall()
        language_rows = conn.execute(
            "SELECT language, requirement_level FROM posting_languages WHERE posting_id = %s",
            (posting_id,),
        ).fetchall()

        ingested_by_run = None
        if row[12] is not None:
            run_row = conn.execute(
                "SELECT id, started_at FROM ingestion_runs WHERE id = %s", (row[12],)
            ).fetchone()
            if run_row is not None:
                ingested_by_run = {"id": run_row[0], "started_at": run_row[1]}

    posting = {
        "id": row[0], "source": row[1], "company": row[2], "title": row[3], "fetched_at": row[4],
        "raw_response": row[5], "country": row[6], "city": row[7], "salary_min": row[8],
        "salary_max": row[9], "salary_currency": row[10], "salary_confidence": row[11],
    }

    classification = None
    if row[13] is not None:  # role_category
        classification = {
            "role_category": row[13], "specialization": row[14], "level": row[15],
            "track": row[16], "classification_confidence": row[17], "taxonomy_version": row[18],
            "model": row[19], "classified_at": row[20],
        }

    if row[21] is not None:  # education_level -> has a posting_requirements row
        requirements = {
            "status": "extracted", "education_level": row[21], "education_required": row[22],
            "equivalent_experience_accepted": row[23], "years_experience_min": row[24],
            "work_arrangement": row[25], "responsibilities_summary": row[26],
            "other_requirements": row[27], "model": row[28], "extracted_at": row[29],
        }
    elif row[30] is not None:  # error -> has a posting_requirements_failures row
        requirements = {
            "status": "failed", "error": row[30], "attempt_count": row[31],
            "last_attempted_at": row[32],
        }
    elif classification is not None and classification["role_category"] in ("other", "unknown"):
        requirements = {"status": "not_eligible"}
    else:
        requirements = {"status": "pending"}

    return {
        "posting": posting,
        "ingested_by_run": ingested_by_run,
        "classification": classification,
        "requirements": requirements,
        "skills": [
            {"raw_skill": r[0], "skill_group": r[1], "requirement_level": r[2]} for r in skill_rows
        ],
        "languages": [{"language": r[0], "requirement_level": r[1]} for r in language_rows],
    }


def get_requirements_reprocess_targets(taxonomy_version: str) -> list[str]:
    """
    Posting ids that already have a posting_requirements row AND whose
    classification has already been reprocessed onto `taxonomy_version` —
    the ordering dependency from Business Logic — Taxonomy reprocessing:
    a posting's requirements must never be reprocessed against a still-stale
    classification, since skill_group selection depends on
    role_category/track/specialization. One-time use only, same as
    get_all_for_reclassification().
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT pr.posting_id
            FROM posting_requirements pr
            JOIN classifications c ON c.posting_id = pr.posting_id
            WHERE c.taxonomy_version = %s
            """,
            (taxonomy_version,),
        ).fetchall()
    return [row[0] for row in rows]
