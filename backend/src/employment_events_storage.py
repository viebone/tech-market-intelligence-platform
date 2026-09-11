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
