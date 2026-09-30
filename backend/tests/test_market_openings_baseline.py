"""
Regression test for the per-company baseline fix
(changes/2026-09-30-job-openings-trend-per-company-baseline.md).

Before this fix, `_fetch_counts()` only excluded postings observed on the
platform's single, long-past baseline day. A company added to the tracked
panel later had its entire first-crawl snapshot counted as "new openings" in
whatever bucket its onboarding day fell into — a real bug: the
us-eu-employer-panel-expansion batches (2026-09-24 through 2026-09-28) turned
the week-of-2026-09-28 Designer/Product Manager/Engineer count from ~200
(consistent with every prior week) to ~1,960, purely from onboarding ~114
new companies, not real hiring growth.

This test inserts synthetic postings for a uniquely-named fake company —
never a real tracked company — into two past, already-fully-elapsed weeks:
one simulating that company's own first-crawl bulk load, one simulating a
genuinely new posting found afterward. It captures each bucket's real count
before inserting (the buckets already hold real production postings from
other companies, so the check is a before/after delta, not an absolute
value), then asserts the bulk-load week's count is unchanged by the insert
(proving those rows are excluded) and the later week's count increases by
exactly one (proving a real new posting still counts). Test rows are deleted
in a `finally` block regardless of outcome — nothing is left behind in the
shared database.

Needs a DATABASE_URL (reads/writes live, then cleans up). Run:
    cd backend/src && ./venv_linux/bin/python ../tests/test_market_openings_baseline.py
    (or ../venv/Scripts/python.exe on Windows)

Skips cleanly if no database is configured.
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

_SRC = Path(__file__).resolve().parent.parent / "src"
for _env in (_SRC.parent / ".env", _SRC / ".env"):
    if _env.exists():
        for line in _env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

_HAS_DB = bool(os.environ.get("DATABASE_URL"))


def _week_start(d):
    # Match PostgreSQL date_trunc('week', ...) — weeks start on Monday.
    return d - timedelta(days=d.weekday())


def test_new_company_onboarding_does_not_read_as_a_hiring_spike():
    if not _HAS_DB:
        print("  (skipped — no DATABASE_URL)")
        return

    import psycopg
    import market_openings

    company = f"__test_baseline_fix_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    # Both dates are well in the past and in different, already-elapsed weeks,
    # so they can't collide with the live daily ingestion pipeline (which only
    # ever inserts with fetched_at = now()) or with an in-progress bucket.
    bulk_day = now - timedelta(days=30)
    new_day = now - timedelta(days=16)
    bulk_period = _week_start(bulk_day.date()).isoformat()
    new_period = _week_start(new_day.date()).isoformat()
    assert bulk_period != new_period, "test dates must land in different week buckets"

    ids = [f"test:{company}/bulk1", f"test:{company}/bulk2", f"test:{company}/new1"]

    before_by_period, _ = market_openings._fetch_counts("week")
    before_bulk = before_by_period.get(bulk_period, {}).get("Engineer", 0)
    before_new = before_by_period.get(new_period, {}).get("Engineer", 0)

    conn = psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=10)
    try:
        with conn.cursor() as cur:
            # Two postings on the company's own first-crawl day (the "bulk load")...
            for pid, day in [(ids[0], bulk_day), (ids[1], bulk_day)]:
                cur.execute(
                    """
                    INSERT INTO raw_postings (id, source, source_ref, company, title, raw_response, fetched_at)
                    VALUES (%s, 'greenhouse', %s, %s, 'Test Engineer', '{}', %s)
                    """,
                    (pid, pid, company, day),
                )
            # ...and one genuinely new posting found on a later crawl.
            cur.execute(
                """
                INSERT INTO raw_postings (id, source, source_ref, company, title, raw_response, fetched_at)
                VALUES (%s, 'greenhouse', %s, %s, 'Test Engineer', '{}', %s)
                """,
                (ids[2], ids[2], company, new_day),
            )
            for pid in ids:
                cur.execute(
                    """
                    INSERT INTO classifications (posting_id, role_category, taxonomy_version, model)
                    VALUES (%s, 'Engineer', 'test', 'test-fixture')
                    """,
                    (pid,),
                )
        conn.commit()

        after_by_period, _ = market_openings._fetch_counts("week")
        after_bulk = after_by_period.get(bulk_period, {}).get("Engineer", 0)
        after_new = after_by_period.get(new_period, {}).get("Engineer", 0)

        assert after_bulk == before_bulk, (
            f"bulk-load week {bulk_period} count should be unchanged by the insert "
            f"(both new rows are the company's own onboarding snapshot and must be "
            f"excluded) — was {before_bulk}, now {after_bulk}"
        )
        assert after_new == before_new + 1, (
            f"post-onboarding week {new_period} count should increase by exactly 1 "
            f"(the one genuinely new posting) — was {before_new}, now {after_new}"
        )
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM classifications WHERE posting_id = ANY(%s)", (ids,))
            cur.execute("DELETE FROM raw_postings WHERE id = ANY(%s)", (ids,))
        conn.commit()
        conn.close()


if __name__ == "__main__":
    test_new_company_onboarding_does_not_read_as_a_hiring_spike()
    print("ok")
