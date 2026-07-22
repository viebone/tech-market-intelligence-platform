"""
Storage layer for the raw_postings table.

raw_postings is immutable: a row is inserted once, at first sight, and never
updated — the exact Adzuna response is the only chance to ever capture a given
posting, since expired listings disappear from Adzuna's index permanently.
See backend/specs/market-health/api.md — Data Models — RawPosting.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from db import get_connection


def existing_ids(ids: list[str]) -> set[str]:
    """Return the subset of `ids` already present in raw_postings."""
    if not ids:
        return set()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id FROM raw_postings WHERE id = ANY(%s)", (ids,)
        ).fetchall()
    return {row[0] for row in rows}


def insert_new_postings(role_family_query: str, postings: list[dict]) -> list[str]:
    """
    Insert postings not already stored, deduped by Adzuna's own `id`.
    Returns the ids of the newly inserted postings.
    """
    seen = existing_ids([p["id"] for p in postings])
    new_postings = [p for p in postings if p["id"] not in seen]
    if not new_postings:
        return []

    fetched_at = datetime.now(timezone.utc)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO raw_postings (id, role_family_query, title, raw_response, fetched_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                [
                    (
                        p["id"],
                        role_family_query,
                        p.get("title", ""),
                        json.dumps(p),
                        fetched_at,
                    )
                    for p in new_postings
                ],
            )

    return [p["id"] for p in new_postings]


def get_all_unclassified() -> list[dict]:
    """
    Postings across every search term that don't have a classification row yet.

    Deliberately not scoped to a single role_family_query: classification is
    run once across everything newly ingested (see ingest.py), not once per
    search term, so the title-based dedup cache in classification.py sees the
    widest possible pool for catching duplicate titles before any LLM call —
    e.g. "UX designer" and "product designer" searches both surfacing a
    posting literally titled "Product Designer".
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT rp.id, rp.title
            FROM raw_postings rp
            LEFT JOIN classifications c ON c.posting_id = rp.id
            WHERE c.posting_id IS NULL
            """
        ).fetchall()
    return [{"id": row[0], "title": row[1]} for row in rows]
