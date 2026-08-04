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
                    salary_confidence, salary_extraction_method
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                [
                    (
                        pid, source, p.source_ref, p.company, p.title, json.dumps(p.raw_response), fetched_at,
                        p.country, p.city, p.salary_min, p.salary_max, p.salary_currency,
                        p.salary_confidence, p.salary_extraction_method,
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
