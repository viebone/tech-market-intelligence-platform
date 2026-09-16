"""
Postgres-backed cache stores (RobotsCacheStore/PageCacheStore, scraping/base.py's
protocols) and insert functions for market_observations / skill_associations.

Both tables are immutable, same discipline as raw_postings/employment_events:
a scraped fact is inserted once and never mutated after insert. See
backend/specs/scraped-data-sources/api.md — Data Models — Part 2.

No query/read functions here beyond existing-id dedupe checks — this feature
is ingestion-only, deliberately (the spec's "What this doesn't decide").
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from db import get_connection
from scraping.base import (
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


def _warn_if_licence_unconfirmed(source: str, row_count: int, kind: str) -> None:
    """
    "Always flag if the CC licence isn't confirmed — never block on it, but
    always highlight the warning" (research/2026-09-16-scraping-good-practices-refinement.md).
    A WARNING-level log (not INFO — this must be visible in operational
    logs even if nobody's specifically looking, unlike the routine
    unchanged-skip note above) every time data from an unconfirmed-licence
    source is actually stored. This is the ingestion-time half of the
    warning; the `licence_confirmed` column on the row itself is what lets
    every future consumer (a chat reasoning trace, an MCP tool's response
    envelope, an admin view) repeat this same warning without a second
    lookup — see scraping/licences.py's SourceLicence and Rule 13's
    provenance-propagation requirement.
    """
    import logging
    from scraping.licences import get_licence

    licence = get_licence(source)
    if not licence.confirmed:
        logging.getLogger(__name__).warning(
            "scraping_storage[%s]: storing %d new %s row(s) under an UNCONFIRMED licence "
            "(%r) — do not surface, display, or republish this data anywhere until "
            "scraping/licences.py's SOURCE_LICENCES[%r].confirmed is actually True.",
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
                    source_url, licence, licence_confirmed, fetched_at, raw_response
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                        o.licence_confirmed, o.fetched_at, json.dumps(o.raw_response),
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
                    source_url, licence, licence_confirmed, fetched_at, raw_response
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                [
                    (
                        aid, source, a.role_name, a.role_taxonomy_match, a.skill_name,
                        a.skill_taxonomy_match, a.period_start, a.period_end, a.job_count,
                        a.percentage, a.rank, a.source_url, a.licence, a.licence_confirmed,
                        a.fetched_at, json.dumps(a.raw_response),
                    )
                    for aid, a in new
                ],
            )

    return [aid for aid, _ in new]
