"""
Regression test for query_market_data's month-grouping baseline fix
(changes/2026-10-01-mcp-trend-baseline-gap.md).

Before this fix, query_market_data had NO baseline exclusion at all -- not even the
platform-wide-only version market_openings.py had before 2026-09-30. A month-grouped
call (used by the MCP get_job_demand tool, /api/chat's Stage 1, and curated_answers.py)
counted every company's entire first-crawl bulk load as that month's "demand," for
every company ever onboarded -- including the platform's own original launch day, not
just later panel-expansion batches.

This test inserts synthetic postings for a uniquely-named fake company into two past,
different months: one simulating that company's own first-crawl bulk load, one
simulating a genuinely new posting found afterward. It asserts (via before/after counts,
since real production data already populates these months):
  - group_by=["month"]: the bulk-load month's count is unchanged by the insert, the
    later month's count increases by exactly 1
  - group_by=["role_category"] (no "month"): BOTH inserted rows count immediately --
    confirming the fix is scoped to month-trend queries only, not stock breakdowns,
    where a bulk-loaded posting is still a real, currently-open role

Test rows are deleted in a `finally` block regardless of outcome.

Needs a DATABASE_URL (reads/writes live, then cleans up). Run:
    cd backend/src && ./venv_linux/bin/python ../tests/test_market_query_baseline.py
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


def _month_key(d):
    return d.strftime("%Y-%m")


def _count_for(rows, key, value):
    return next((r["count"] for r in rows if r.get(key) == value), 0)


def test_month_grouping_excludes_each_companys_own_baseline_day():
    if not _HAS_DB:
        print("  (skipped — no DATABASE_URL)")
        return

    import psycopg
    import market_query

    company = f"__test_mq_baseline_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    # Two calendar months apart and well in the past -- can't collide with the
    # live daily ingestion pipeline (which only ever inserts with fetched_at = now()).
    bulk_day = (now.replace(day=1) - timedelta(days=200))
    new_day = (now.replace(day=1) - timedelta(days=170))
    bulk_month = _month_key(bulk_day)
    new_month = _month_key(new_day)
    assert bulk_month != new_month, "test dates must land in different months"

    ids = [f"test:{company}/bulk1", f"test:{company}/bulk2", f"test:{company}/new1"]

    before_month = market_query.query_market_data(group_by=["month"])["rows"]
    before_role = market_query.query_market_data(group_by=["role_category"])["rows"]
    before_bulk = _count_for(before_month, "month", bulk_month)
    before_new = _count_for(before_month, "month", new_month)
    before_engineer = _count_for(before_role, "role_category", "Engineer")

    conn = psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=10)
    try:
        with conn.cursor() as cur:
            for pid, day in [(ids[0], bulk_day), (ids[1], bulk_day)]:
                cur.execute(
                    """
                    INSERT INTO raw_postings (id, source, source_ref, company, title, raw_response, fetched_at)
                    VALUES (%s, 'greenhouse', %s, %s, 'Test Engineer', '{}', %s)
                    """,
                    (pid, pid, company, day),
                )
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

        after_month = market_query.query_market_data(group_by=["month"])["rows"]
        after_role = market_query.query_market_data(group_by=["role_category"])["rows"]
        after_bulk = _count_for(after_month, "month", bulk_month)
        after_new = _count_for(after_month, "month", new_month)
        after_engineer = _count_for(after_role, "role_category", "Engineer")

        assert after_bulk == before_bulk, (
            f"month={bulk_month} (bulk-load month) should be unchanged by the insert "
            f"(both new rows are the company's own onboarding snapshot) — "
            f"was {before_bulk}, now {after_bulk}"
        )
        assert after_new == before_new + 1, (
            f"month={new_month} (post-onboarding month) should increase by exactly 1 "
            f"— was {before_new}, now {after_new}"
        )
        assert after_engineer == before_engineer + 3, (
            "role_category grouping (no 'month') must NOT exclude the bulk-load rows — "
            f"all 3 inserted postings should count immediately — "
            f"was {before_engineer}, now {after_engineer}"
        )
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM classifications WHERE posting_id = ANY(%s)", (ids,))
            cur.execute("DELETE FROM raw_postings WHERE id = ANY(%s)", (ids,))
        conn.commit()
        conn.close()


if __name__ == "__main__":
    test_month_grouping_excludes_each_companys_own_baseline_day()
    print("ok")
