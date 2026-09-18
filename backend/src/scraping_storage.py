"""
Postgres-backed cache stores (RobotsCacheStore/PageCacheStore, scraping/base.py's
protocols) and insert functions for market_observations / skill_associations.

Both tables are immutable, same discipline as raw_postings/employment_events:
a scraped fact is inserted once and never mutated after insert. See
backend/specs/scraped-data-sources/api.md — Data Models — Part 2.

**Added 2026-09-18** (`changes/2026-09-18-admin-market-benchmark-visibility.md`):
read functions for the pipeline-visibility admin dashboard —
list_market_observations()/get_market_observation(),
list_skill_associations()/get_skill_association(), get_extraction_for_url(),
list_scrape_runs(). Still ingestion-only for any *consumer-facing* surface
(the spec's "What this doesn't decide" stands) — these reads are for the
operator-only admin dashboard, not a new public query surface.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from db import get_connection
from scraping.base import (
    ExtractionCacheEntry,
    FetchedMarketObservation,
    FetchedSkillAssociation,
    PageCacheEntry,
    RobotsCacheEntry,
)

# Comparable fields for value-level dedupe (Business Logic rule 9) — every
# market_observations column except id/period_start/period_end/fetched_at/
# raw_response, which are expected to differ run-to-run even when nothing
# about the market itself has changed.
_OBSERVATION_COMPARABLE_FIELDS = (
    "taxonomy_match", "rank", "rank_yoy_change", "vacancy_count", "vacancy_share",
    "live_jobs", "salary_sample_size", "salary_p10", "salary_p25", "salary_median",
    "salary_p75", "salary_p90", "salary_unit", "salary_yoy_change",
)
_ASSOCIATION_COMPARABLE_FIELDS = ("job_count", "percentage", "rank")


class PostgresRobotsCacheStore:
    def get(self, host: str) -> RobotsCacheEntry | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT raw_body, fetched_at, http_status FROM scrape_robots_cache WHERE host = %s",
                (host,),
            ).fetchone()
        if row is None:
            return None
        raw_body, fetched_at, http_status = row
        return RobotsCacheEntry(raw_body=raw_body, fetched_at=fetched_at, http_status=http_status)

    def set(self, host: str, raw_body: str | None, http_status: int, fetched_at: datetime) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO scrape_robots_cache (host, raw_body, fetched_at, http_status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (host) DO UPDATE SET
                    raw_body = EXCLUDED.raw_body,
                    fetched_at = EXCLUDED.fetched_at,
                    http_status = EXCLUDED.http_status
                """,
                (host, raw_body, fetched_at, http_status),
            )


class PostgresPageCacheStore:
    def get(self, url: str) -> PageCacheEntry | None:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT raw_body, content_hash, etag, last_modified, fetched_at, http_status
                FROM scrape_page_cache WHERE url = %s
                """,
                (url,),
            ).fetchone()
        if row is None:
            return None
        raw_body, content_hash, etag, last_modified, fetched_at, http_status = row
        return PageCacheEntry(
            raw_body=raw_body, content_hash=content_hash, etag=etag,
            last_modified=last_modified, fetched_at=fetched_at, http_status=http_status,
        )

    def set(
        self, url: str, source: str, raw_body: str, content_hash: str,
        etag: str | None, last_modified: str | None, fetched_at: datetime, http_status: int,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO scrape_page_cache
                    (url, source, raw_body, content_hash, etag, last_modified, fetched_at, http_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    raw_body = EXCLUDED.raw_body,
                    content_hash = EXCLUDED.content_hash,
                    etag = EXCLUDED.etag,
                    last_modified = EXCLUDED.last_modified,
                    fetched_at = EXCLUDED.fetched_at,
                    http_status = EXCLUDED.http_status
                """,
                (url, source, raw_body, content_hash, etag, last_modified, fetched_at, http_status),
            )

    def touch(self, url: str, fetched_at: datetime) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE scrape_page_cache SET fetched_at = %s WHERE url = %s",
                (fetched_at, url),
            )


class PostgresExtractionCacheStore:
    """
    Added 2026-09-18 (changes/2026-09-18-itjobswatch-llm-extraction.md) — the
    LLM-extraction-dedupe counterpart to PostgresPageCacheStore. A caller
    (an adapter's fetch()) checks get(url), compares the returned
    content_hash against the page it just fetched/read from PageCacheStore,
    and only calls the LLM (then set()) on a miss or a changed hash.
    """
    def get(self, url: str) -> tuple[ExtractionCacheEntry, str] | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT content_hash, extraction_json, model, extracted_at FROM scrape_extractions WHERE url = %s",
                (url,),
            ).fetchone()
        if row is None:
            return None
        content_hash, extraction_json, model, extracted_at = row
        return (
            ExtractionCacheEntry(extraction_json=extraction_json, model=model, extracted_at=extracted_at),
            content_hash,
        )

    def set(self, url: str, content_hash: str, extraction_json: dict, model: str, extracted_at: datetime) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO scrape_extractions (url, content_hash, extraction_json, model, extracted_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    content_hash = EXCLUDED.content_hash,
                    extraction_json = EXCLUDED.extraction_json,
                    model = EXCLUDED.model,
                    extracted_at = EXCLUDED.extracted_at
                """,
                (url, content_hash, json.dumps(extraction_json), model, extracted_at),
            )


def _warn_if_licence_unconfirmed(source: str, row_count: int, kind: str) -> None:
    """
    "Always flag if the CC licence isn't confirmed — never block on it, but
    always highlight the warning" (research/2026-09-16-scraping-good-practices-refinement.md),
    extended 2026-09-16 to also flag an explicitly `rejected` source — same
    "collect regardless, but never let it go unnoticed" principle. A
    WARNING-level log (not INFO — this must be visible in operational logs
    even if nobody's specifically looking) every time data from an
    unconfirmed *or* rejected source is actually stored. This is the
    ingestion-time half of the warning; the `licence_confirmed` column on
    the row itself is what lets every future consumer (a chat reasoning
    trace, an MCP tool's response envelope, an admin view) repeat this same
    warning without a second lookup — see source_licences.py's
    SourceLicence and Rule 13's provenance-propagation requirement.
    """
    import logging
    from source_licences import get_licence

    licence = get_licence(source)
    logger = logging.getLogger(__name__)
    if licence.rejected:
        logger.warning(
            "scraping_storage[%s]: storing %d new %s row(s) from a source marked "
            "rejected=True for USE — collection is never gated on this, but this data must "
            "not be surfaced, displayed, or republished anywhere until that's reversed.",
            source, row_count, kind,
        )
    elif not licence.confirmed:
        logger.warning(
            "scraping_storage[%s]: storing %d new %s row(s) under an UNCONFIRMED licence "
            "(%r) — do not surface, display, or republish this data anywhere until "
            "source_licences.py's SOURCE_LICENCES[%r].confirmed is actually True.",
            source, row_count, kind, licence.licence, source,
        )


def _existing_ids(table: str, ids: list[str]) -> set[str]:
    if not ids:
        return set()
    with get_connection() as conn:
        rows = conn.execute(f"SELECT id FROM {table} WHERE id = ANY(%s)", (ids,)).fetchall()
    return {row[0] for row in rows}


# ---------------------------------------------------------------------------
# Run cadence (Business Logic rule 8) — checked by ingest_scraped_sources.py
# before an adapter's fetch() is even called.
# ---------------------------------------------------------------------------

def get_last_run_at(source: str) -> datetime | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT last_run_at FROM scrape_ingestion_runs WHERE source = %s", (source,)
        ).fetchone()
    return row[0] if row else None


def record_run(source: str, at: datetime) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO scrape_ingestion_runs (source, last_run_at)
            VALUES (%s, %s)
            ON CONFLICT (source) DO UPDATE SET last_run_at = EXCLUDED.last_run_at
            """,
            (source, at),
        )


def _due_from_last_run(last_run_at: datetime | None, min_interval_days: int, now: datetime) -> bool:
    """Pure comparison, no DB — split out from is_due() so this logic is
    unit-testable without a live database (see backend/tests/test_scraping.py)."""
    if last_run_at is None:
        return True
    return (now - last_run_at) >= timedelta(days=min_interval_days)


def is_due(source: str, min_interval_days: int, now: datetime | None = None) -> bool:
    """
    True if `source` has never run, or its last run was >= min_interval_days
    ago. Called before fetch() — a source not yet due is skipped for this
    invocation entirely, regardless of how often the script itself runs.
    """
    now = now or datetime.now(timezone.utc)
    return _due_from_last_run(get_last_run_at(source), min_interval_days, now)


# ---------------------------------------------------------------------------
# Value-level dedupe (Business Logic rule 9) — "focus on new things, not
# old" made real: id-level dedupe alone isn't enough since a shifting
# rolling window changes the id every run even when nothing about the
# market itself changed.
# ---------------------------------------------------------------------------

def _latest_observation_values(
    source: str, entity_type: str, entity_name: str, employment_type: str, location: str,
) -> dict | None:
    columns = ", ".join(_OBSERVATION_COMPARABLE_FIELDS)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {columns} FROM market_observations
            WHERE source = %s AND entity_type = %s AND entity_name = %s
              AND employment_type = %s AND location = %s
            ORDER BY period_end DESC LIMIT 1
            """,
            (source, entity_type, entity_name, employment_type, location),
        ).fetchone()
    if row is None:
        return None
    return dict(zip(_OBSERVATION_COMPARABLE_FIELDS, row))


def _observation_unchanged(o: FetchedMarketObservation, previous: dict) -> bool:
    return all(getattr(o, field) == previous[field] for field in _OBSERVATION_COMPARABLE_FIELDS)


def _latest_association_values(source: str, role_name: str, skill_name: str) -> dict | None:
    columns = ", ".join(_ASSOCIATION_COMPARABLE_FIELDS)
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT {columns} FROM skill_associations
            WHERE source = %s AND role_name = %s AND skill_name = %s
            ORDER BY period_end DESC LIMIT 1
            """,
            (source, role_name, skill_name),
        ).fetchone()
    if row is None:
        return None
    return dict(zip(_ASSOCIATION_COMPARABLE_FIELDS, row))


def _association_unchanged(a: FetchedSkillAssociation, previous: dict) -> bool:
    return all(getattr(a, field) == previous[field] for field in _ASSOCIATION_COMPARABLE_FIELDS)


def insert_market_observations(source: str, observations: list[FetchedMarketObservation]) -> list[str]:
    """
    Insert observations not already stored, deduped by id =
    f"{source}:{entity_type}:{entity_name}:{employment_type}:{location}:{period_start}"
    (Data Models — Part 2), **and** by value — an observation identical to
    the most recently stored one for the same entity key is skipped even
    though its id differs (a shifting rolling window alone shouldn't create
    a new row when nothing about the market changed — Business Logic rule
    9). Returns the ids of the newly inserted rows.
    """
    candidate_ids = [
        f"{source}:{o.entity_type}:{o.entity_name}:{o.employment_type}:{o.location}:{o.period_start.isoformat()}"
        for o in observations
    ]
    seen = _existing_ids("market_observations", candidate_ids)
    new: list[tuple[str, FetchedMarketObservation]] = []
    batch_seen: set[str] = set()
    skipped_unchanged = 0
    for oid, o in zip(candidate_ids, observations):
        if oid in seen or oid in batch_seen:
            continue
        previous = _latest_observation_values(source, o.entity_type, o.entity_name, o.employment_type, o.location)
        if previous is not None and _observation_unchanged(o, previous):
            skipped_unchanged += 1
            continue
        batch_seen.add(oid)
        new.append((oid, o))
    if skipped_unchanged:
        import logging
        logging.getLogger(__name__).info(
            "scraping_storage[%s]: %d observation(s) unchanged since last run, not stored",
            source, skipped_unchanged,
        )
    if not new:
        return []

    _warn_if_licence_unconfirmed(source, len(new), "market observation")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO market_observations (
                    id, source, entity_type, entity_name, taxonomy_match, employment_type,
                    location, period_start, period_end, rank, rank_yoy_change, vacancy_count,
                    vacancy_share, live_jobs, salary_sample_size, salary_p10, salary_p25,
                    salary_median, salary_p75, salary_p90, salary_unit, salary_yoy_change,
                    source_url, licence, licence_confirmed, fetched_at, extraction_model, raw_response
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO NOTHING
                """,
                [
                    (
                        oid, source, o.entity_type, o.entity_name, o.taxonomy_match, o.employment_type,
                        o.location, o.period_start, o.period_end, o.rank, o.rank_yoy_change,
                        o.vacancy_count, o.vacancy_share, o.live_jobs, o.salary_sample_size,
                        o.salary_p10, o.salary_p25, o.salary_median, o.salary_p75, o.salary_p90,
                        o.salary_unit, o.salary_yoy_change, o.source_url, o.licence,
                        o.licence_confirmed, o.fetched_at, o.extraction_model, json.dumps(o.raw_response),
                    )
                    for oid, o in new
                ],
            )

    return [oid for oid, _ in new]


def insert_skill_associations(source: str, associations: list[FetchedSkillAssociation]) -> list[str]:
    """
    Insert associations not already stored, deduped by id =
    f"{source}:{role_name}:{skill_name}:{period_start}" (Data Models — Part 2),
    **and** by value — same "skip an unchanged observation" rule as
    insert_market_observations (Business Logic rule 9). Returns the ids of
    the newly inserted rows.
    """
    candidate_ids = [
        f"{source}:{a.role_name}:{a.skill_name}:{a.period_start.isoformat()}"
        for a in associations
    ]
    seen = _existing_ids("skill_associations", candidate_ids)
    new: list[tuple[str, FetchedSkillAssociation]] = []
    batch_seen: set[str] = set()
    skipped_unchanged = 0
    for aid, a in zip(candidate_ids, associations):
        if aid in seen or aid in batch_seen:
            continue
        previous = _latest_association_values(source, a.role_name, a.skill_name)
        if previous is not None and _association_unchanged(a, previous):
            skipped_unchanged += 1
            continue
        batch_seen.add(aid)
        new.append((aid, a))
    if skipped_unchanged:
        import logging
        logging.getLogger(__name__).info(
            "scraping_storage[%s]: %d skill association(s) unchanged since last run, not stored",
            source, skipped_unchanged,
        )
    if not new:
        return []

    _warn_if_licence_unconfirmed(source, len(new), "skill association")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO skill_associations (
                    id, source, role_name, role_taxonomy_match, skill_name, skill_taxonomy_match,
                    period_start, period_end, job_count, percentage, rank,
                    source_url, licence, licence_confirmed, fetched_at, extraction_model, raw_response
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                [
                    (
                        aid, source, a.role_name, a.role_taxonomy_match, a.skill_name,
                        a.skill_taxonomy_match, a.period_start, a.period_end, a.job_count,
                        a.percentage, a.rank, a.source_url, a.licence, a.licence_confirmed,
                        a.fetched_at, a.extraction_model, json.dumps(a.raw_response),
                    )
                    for aid, a in new
                ],
            )

    return [aid for aid, _ in new]


# ---------------------------------------------------------------------------
# Admin read functions — added 2026-09-18
# (changes/2026-09-18-admin-market-benchmark-visibility.md), for the
# pipeline-visibility admin dashboard. Same closed-set-validated WHERE/ORDER
# BY discipline as employment_events_storage.list_events() — see
# backend/specs/pipeline-visibility/api.md for the routes these serve.
# ---------------------------------------------------------------------------

_OBSERVATION_SORT_COLUMNS = {"period_end", "entity_name", "rank", "vacancy_count"}

_OBSERVATION_LIST_COLUMNS = (
    "id, source, entity_type, entity_name, employment_type, location, period_end, "
    "rank, vacancy_count, vacancy_share, salary_median, licence_confirmed, extraction_model"
)

_OBSERVATION_DETAIL_COLUMNS = (
    "id, source, entity_type, entity_name, taxonomy_match, employment_type, location, "
    "period_start, period_end, rank, rank_yoy_change, vacancy_count, vacancy_share, "
    "live_jobs, salary_sample_size, salary_p10, salary_p25, salary_median, salary_p75, "
    "salary_p90, salary_unit, salary_yoy_change, source_url, licence, licence_confirmed, "
    "fetched_at, extraction_model, raw_response, created_at"
)


def list_market_observations(
    source: str | None = None,
    entity_type: str | None = None,
    entity_name: str | None = None,
    employment_type: str | None = None,
    sort: str = "period_end",
    dir: str = "desc",
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """Filtered/sorted/paginated market_observations rows, for GET
    /admin/market-observations. See backend/specs/pipeline-visibility/api.md."""
    if sort not in _OBSERVATION_SORT_COLUMNS:
        sort = "period_end"
    order_dir = "ASC" if dir == "asc" else "DESC"

    conditions: list[str] = []
    params: list = []
    for column, value in (
        ("source", source), ("entity_type", entity_type),
        ("entity_name", entity_name), ("employment_type", employment_type),
    ):
        if value:
            conditions.append(f"{column} = %s")
            params.append(value)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    with get_connection() as conn:
        total = conn.execute(
            f"SELECT count(*) FROM market_observations {where_clause}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT {_OBSERVATION_LIST_COLUMNS} FROM market_observations
            {where_clause}
            ORDER BY {sort} {order_dir} NULLS LAST
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, (page - 1) * page_size],
        ).fetchall()
        columns = [c.strip() for c in _OBSERVATION_LIST_COLUMNS.split(",")]
        observations = [dict(zip(columns, row)) for row in rows]

    return {"observations": observations, "total": total}


def get_market_observation(observation_id: str) -> dict | None:
    """Full stored record for one market observation, for GET
    /admin/market-observations/{observation_id}. None if not found."""
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {_OBSERVATION_DETAIL_COLUMNS} FROM market_observations WHERE id = %s",
            (observation_id,),
        ).fetchone()
        if row is None:
            return None
        columns = [c.strip() for c in _OBSERVATION_DETAIL_COLUMNS.split(",")]
        return dict(zip(columns, row))


def get_distinct_observation_sources() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT source FROM market_observations ORDER BY source").fetchall()
    return [r[0] for r in rows]


def get_distinct_observation_entity_names() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT entity_name FROM market_observations ORDER BY entity_name"
        ).fetchall()
    return [r[0] for r in rows]


_ASSOCIATION_SORT_COLUMNS = {"rank", "percentage", "job_count"}

_ASSOCIATION_LIST_COLUMNS = (
    "id, source, role_name, skill_name, job_count, percentage, rank, "
    "licence_confirmed, extraction_model"
)

_ASSOCIATION_DETAIL_COLUMNS = (
    "id, source, role_name, role_taxonomy_match, skill_name, skill_taxonomy_match, "
    "period_start, period_end, job_count, percentage, rank, source_url, licence, "
    "licence_confirmed, fetched_at, extraction_model, raw_response, created_at"
)


def list_skill_associations(
    source: str | None = None,
    role_name: str | None = None,
    sort: str = "rank",
    dir: str = "asc",
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """Filtered/sorted/paginated skill_associations rows, for GET
    /admin/skill-associations. See backend/specs/pipeline-visibility/api.md."""
    if sort not in _ASSOCIATION_SORT_COLUMNS:
        sort = "rank"
    order_dir = "ASC" if dir == "asc" else "DESC"

    conditions: list[str] = []
    params: list = []
    for column, value in (("source", source), ("role_name", role_name)):
        if value:
            conditions.append(f"{column} = %s")
            params.append(value)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    with get_connection() as conn:
        total = conn.execute(
            f"SELECT count(*) FROM skill_associations {where_clause}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT {_ASSOCIATION_LIST_COLUMNS} FROM skill_associations
            {where_clause}
            ORDER BY {sort} {order_dir} NULLS LAST
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, (page - 1) * page_size],
        ).fetchall()
        columns = [c.strip() for c in _ASSOCIATION_LIST_COLUMNS.split(",")]
        associations = [dict(zip(columns, row)) for row in rows]

    return {"associations": associations, "total": total}


def get_skill_association(association_id: str) -> dict | None:
    """Full stored record for one skill association, for GET
    /admin/skill-associations/{association_id}. None if not found."""
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {_ASSOCIATION_DETAIL_COLUMNS} FROM skill_associations WHERE id = %s",
            (association_id,),
        ).fetchone()
        if row is None:
            return None
        columns = [c.strip() for c in _ASSOCIATION_DETAIL_COLUMNS.split(",")]
        return dict(zip(columns, row))


def get_distinct_association_sources() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT source FROM skill_associations ORDER BY source").fetchall()
    return [r[0] for r in rows]


def get_distinct_association_roles() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT role_name FROM skill_associations ORDER BY role_name").fetchall()
    return [r[0] for r in rows]


def get_extraction_for_url(url: str) -> dict | None:
    """The scrape_extractions row for one page url, for the Market
    Observations detail view's extraction-provenance line
    (backend/specs/pipeline-visibility/api.md — Business Logic). None if
    this observation predates the LLM-extraction rebuild, or its
    ExtractionCache row was since superseded — rendered as "Extraction
    provenance unavailable", never fabricated."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT content_hash, model, extracted_at FROM scrape_extractions WHERE url = %s",
            (url,),
        ).fetchone()
    if row is None:
        return None
    return {"content_hash": row[0], "model": row[1], "extracted_at": row[2]}


def list_scrape_runs() -> list[dict]:
    """
    One row per *registered* scraped-source adapter (backend/specs/
    pipeline-visibility/api.md — GET /admin/scrape-runs) — deliberately every
    adapter in scraping.ALL_SCRAPED_SOURCE_ADAPTERS, not only ones with a
    scrape_ingestion_runs row yet, since a never-run source is exactly the
    state this view exists to surface. Reuses _due_from_last_run()'s existing
    pure comparison logic so this view can never disagree with what
    ingest_scraped_sources.py itself would decide.
    """
    from scraping import ALL_SCRAPED_SOURCE_ADAPTERS, DEFAULT_MIN_RUN_INTERVAL_DAYS, MIN_RUN_INTERVAL_DAYS

    now = datetime.now(timezone.utc)
    with get_connection() as conn:
        rows = conn.execute("SELECT source, last_run_at FROM scrape_ingestion_runs").fetchall()
    last_run_by_source = {r[0]: r[1] for r in rows}

    runs = []
    for adapter_cls in ALL_SCRAPED_SOURCE_ADAPTERS:
        source = getattr(adapter_cls, "name", adapter_cls.__name__)
        min_interval = MIN_RUN_INTERVAL_DAYS.get(source, DEFAULT_MIN_RUN_INTERVAL_DAYS)
        last_run_at = last_run_by_source.get(source)
        next_due_at = last_run_at + timedelta(days=min_interval) if last_run_at is not None else None
        runs.append({
            "source": source,
            "last_run_at": last_run_at,
            "min_run_interval_days": min_interval,
            "next_due_at": next_due_at,
            "is_due": _due_from_last_run(last_run_at, min_interval, now),
        })
    return runs
