"""
Storage layer for the employment_events table.

employment_events is immutable, same discipline as raw_postings: a
registry's published record is the only chance to capture it as reported: a
row is inserted once and never mutated after insert. See
backend/specs/market-health/api.md — Data Models — EmploymentEvent.

No company matching (added 2026-09-11, removed the same day —
changes/2026-09-11-employment-events-no-company-matching.md): employment
events carry only company_raw, never matched or compared against
raw_postings.company in any way.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from db import get_connection
from employment_events.base import FetchedEmploymentEvent, direction_for
from sources.base import normalize_country


def existing_ids(ids: list[str]) -> set[str]:
    """Return the subset of `ids` already present in employment_events."""
    if not ids:
        return set()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id FROM employment_events WHERE id = ANY(%s)", (ids,)
        ).fetchall()
    return {row[0] for row in rows}


def insert_new_events(source: str, events: list[FetchedEmploymentEvent]) -> list[str]:
    """
    Insert events not already stored, deduped by id = f"{source}:{source_ref}"
    (same shape as raw_postings.id). Returns the ids of the newly inserted
    events. direction (derived from event_type) is computed here, once, for
    every adapter — not inside each adapter — so there is one place to
    maintain that logic.
    """
    candidate_ids = [f"{source}:{e.source_ref}" for e in events]
    seen = existing_ids(candidate_ids)
    # Dedupe *within this batch* too, not just against the DB — added
    # 2026-09-11 while verifying the Companies House Streaming API adapter:
    # a change-stream can emit several update events for the same case in
    # one run (e.g. a practitioner's details changing), all mapping to the
    # same source_ref/id. ON CONFLICT DO NOTHING already kept the stored
    # data correct either way, but without this the "N new" count this
    # function returns (and every adapter logs) overstated real distinct
    # rows — first-occurrence wins, same tie-break existing_ids() implies.
    new: list[tuple[str, FetchedEmploymentEvent]] = []
    batch_seen: set[str] = set()
    for eid, e in zip(candidate_ids, events):
        if eid in seen or eid in batch_seen:
            continue
        batch_seen.add(eid)
        new.append((eid, e))
    if not new:
        return []

    ingested_at = datetime.now(timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO employment_events (
                    id, source, source_ref, source_url, company_raw,
                    sector, country, region, event_date, event_type, direction,
                    jobs_affected, confidence, source_type, raw_response, ingested_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                [
                    (
                        eid, source, e.source_ref, e.source_url, e.company_raw,
                        e.sector, normalize_country(e.country), e.region, e.event_date,
                        e.event_type, direction_for(e.event_type), e.jobs_affected,
                        e.confidence, "registry", json.dumps(e.raw_response), ingested_at,
                    )
                    for eid, e in new
                ],
            )

    return [eid for eid, _ in new]


# ---------------------------------------------------------------------------
# Read/aggregate functions — pipeline-visibility admin dashboard.
# See backend/specs/pipeline-visibility/api.md — GET /admin/employment-events,
# GET /admin/employment-events/{event_id}, and the Overview
# employment_events_summary block. Read-only; never joined to raw_postings or
# any other job-postings table (backend/EMPLOYMENT_EVENTS.md's core rule).
# ---------------------------------------------------------------------------

_SORT_COLUMNS = {"event_date", "company_raw", "source", "event_type", "jobs_affected", "ingested_at"}

_LIST_COLUMNS = (
    "id, source, company_raw, event_type, direction, event_date, "
    "jobs_affected, country, confidence"
)

_DETAIL_COLUMNS = (
    "id, source, source_ref, source_url, company_raw, sector, country, region, "
    "event_date, event_type, direction, jobs_affected, confidence, source_type, "
    "superseded_by, raw_response, ingested_at, created_at"
)


def list_events(
    source: str | None = None,
    event_type: str | None = None,
    direction: str | None = None,
    confidence: str | None = None,
    country: str | None = None,
    sort: str = "event_date",
    dir: str = "desc",
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """Filtered/sorted/paginated employment_events rows, for
    GET /admin/employment-events. Same closed-set validation discipline as
    raw_postings.list_postings()."""
    if sort not in _SORT_COLUMNS:
        sort = "event_date"
    order_dir = "ASC" if dir == "asc" else "DESC"

    conditions: list[str] = []
    params: list = []
    for column, value in (
        ("source", source), ("event_type", event_type),
        ("direction", direction), ("confidence", confidence), ("country", country),
    ):
        if value:
            conditions.append(f"{column} = %s")
            params.append(value)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    with get_connection() as conn:
        total = conn.execute(
            f"SELECT count(*) FROM employment_events {where_clause}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT {_LIST_COLUMNS} FROM employment_events
            {where_clause}
            ORDER BY {sort} {order_dir} NULLS LAST
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, (page - 1) * page_size],
        ).fetchall()
        columns = [c.strip() for c in _LIST_COLUMNS.split(",")]
        events = [dict(zip(columns, row)) for row in rows]

    return {"events": events, "total": total}


def get_event(event_id: str) -> dict | None:
    """Full stored record for one employment event, for
    GET /admin/employment-events/{event_id}. Returns None if not found."""
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT {_DETAIL_COLUMNS} FROM employment_events WHERE id = %s", (event_id,)
        ).fetchone()
        if row is None:
            return None
        columns = [c.strip() for c in _DETAIL_COLUMNS.split(",")]
        return dict(zip(columns, row))


def get_distinct_countries() -> list[str]:
    """Distinct non-null countries present in employment_events, for the
    Employment Events filter dropdown — same "build filter options from real
    stored values" pattern as classification.get_distinct_specializations()."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT country FROM employment_events WHERE country IS NOT NULL ORDER BY country"
        ).fetchall()
    return [r[0] for r in rows]


def get_summary() -> dict:
    """Overview's employment_events_summary block — total count, per-source
    breakdown (count, last ingested, cursor position when the source is
    streaming-style), and per-direction split. See backend/specs/
    pipeline-visibility/api.md — Business Logic — Employment events summary."""
    from employment_events.base import SOURCE_DISPLAY_NAMES

    with get_connection() as conn:
        total = conn.execute("SELECT count(*) FROM employment_events").fetchone()[0]

        source_rows = conn.execute(
            "SELECT source, count(*), max(ingested_at) FROM employment_events GROUP BY source"
        ).fetchall()
        cursors = dict(
            conn.execute("SELECT source, cursor FROM employment_event_cursors").fetchall()
        )
        by_source = [
            {
                "source": source,
                "display_name": SOURCE_DISPLAY_NAMES.get(source, source),
                "count": count,
                "last_ingested_at": last_ingested_at,
                "cursor": cursors.get(source),
            }
            for source, count, last_ingested_at in source_rows
        ]

        direction_counts = dict(
            conn.execute(
                "SELECT direction, count(*) FROM employment_events GROUP BY direction"
            ).fetchall()
        )
        by_direction = [
            {"direction": d, "count": direction_counts.get(d, 0)}
            for d in ("contraction", "expansion")
        ]

    return {"total": total, "by_source": by_source, "by_direction": by_direction}
