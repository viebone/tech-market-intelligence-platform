"""
One-time sampling go-live bookkeeping — backend/specs/market-health/api.md — Data Models —
RawPosting (migration note 2026-10-23); changes/2026-10-10-requirements-extraction-sampling.md.

Inserts one posting_samples row with decision = 'kept_before_sampling' for every posting stored
before SAMPLING_GO_LIVE, so admin and queries can read the decision explicitly. The pipeline does
not depend on it: a pre-go-live posting with no row is already treated as kept_before_sampling.

Run by hand once after deploy. NEVER from ingest.py (Rule 15). Insert-only, scope fixed by a
constant cutoff (never "all rows"), ON CONFLICT DO NOTHING — a second run inserts nothing:
    python migrate_sampling_go_live.py
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from db import get_connection, init_schema  # noqa: E402
from sampling_settings import SAMPLING_GO_LIVE  # noqa: E402


def seed() -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO posting_samples
                (posting_id, decision, reason, group_role, group_specialization, group_month,
                 limit_at_decision, rate, hash_u, decided_at)
            SELECT rp.id, 'kept_before_sampling', 'before_sampling',
                   COALESCE(c.role_category, 'unclassified'), c.specialization,
                   date_trunc('month', rp.created_at)::date, NULL, 1.0, 0.0, now()
            FROM raw_postings rp
            LEFT JOIN classifications c ON c.posting_id = rp.id
            WHERE rp.created_at < %s
            ON CONFLICT (posting_id) DO NOTHING
            """,
            (SAMPLING_GO_LIVE,),
        )
        return cur.rowcount


if __name__ == "__main__":
    init_schema()
    print(f"Recorded {seed()} postings stored before {SAMPLING_GO_LIVE.isoformat()} as kept_before_sampling.")
