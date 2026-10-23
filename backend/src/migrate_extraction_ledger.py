"""
One-time seed of requirements_extraction_ledger from today's posting_requirements rows — see
backend/specs/market-health/api.md — Business Logic — Repeat-work guardrails, and
changes/2026-10-10-requirements-re-extraction-loop.md (Step 4).

Without it, the circuit breaker would treat every posting extracted before the ledger existed as
"never paid for", and a second loop on those postings would go unnoticed. One `lane = 'seed'`
row per posting that has requirements and no ledger row yet.

Run by hand once at deploy. NEVER from ingest.py (Rule 15). Idempotent — it only inserts, only
for postings with no ledger row, so a second run inserts nothing:
    python migrate_extraction_ledger.py

History the 2026-09-21..10-10 loop deleted isn't recoverable and isn't reconstructed;
batch_jobs.posting_ids records submissions, not successes.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from db import get_connection, init_schema  # noqa: E402


def seed() -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO requirements_extraction_ledger (posting_id, lane, model, extracted_at)
            SELECT pr.posting_id, 'seed', pr.model, pr.extracted_at
            FROM posting_requirements pr
            WHERE NOT EXISTS (
                SELECT 1 FROM requirements_extraction_ledger l WHERE l.posting_id = pr.posting_id
            )
            """
        )
        return cur.rowcount


if __name__ == "__main__":
    init_schema()
    print(f"Seeded {seed()} ledger rows from existing posting_requirements.")
