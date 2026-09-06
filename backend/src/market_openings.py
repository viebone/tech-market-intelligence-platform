"""
FastAPI router for job opening trend data.

Endpoint:
  GET /api/market-health/openings

Returns weekly or monthly job opening counts per role category (Designer, Product Manager,
Engineer) for four time ranges, plus a written summary of the trend.

Sourced from raw_postings + classifications — live-ingested, LLM-classified
postings from Greenhouse, Lever, and Ashby (Adzuna retired 2026-08-03, see
changes/2026-07-28-multi-source-job-data-ingestion.md) — not mock data. A
count is the number of distinct postings first observed by daily ingestion
in that bucket, not "total open positions" at any point in time: none of the
source platforms' APIs support a historical date-range query, so there is no
earlier data than when this pipeline started.

Postings first seen on the baseline date (the earliest fetched_at date) are
excluded — that first crawl is a one-time bulk load, not market activity — so
the first bucket returned starts the day after. See
backend/specs/market-health/api.md — Business Logic — Trend aggregation.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException

from db import get_connection
from models import OpeningDataPoint

logger = logging.getLogger(__name__)

router = APIRouter()

TimeRange = Literal["six_months", "this_year", "past_5_years", "all_time"]
Granularity = Literal["week", "month"]
VALID_RANGES: set[str] = {"six_months", "this_year", "past_5_years", "all_time"}
VALID_GRANULARITIES: set[str] = {"week", "month"}

_ROLE_CATEGORY_FIELDS = {
    "Designer": "designer",
    "Product Manager": "product_manager",
    "Engineer": "engineer",
}


PLOTTED_ROLE_CATEGORIES = ("Designer", "Product Manager", "Engineer")


def _fetch_counts(granularity: str) -> tuple[dict[str, dict[str, int]], date | None]:
    """
    One date bucket per classified posting in a plotted Role Category (Designer,
    Product Manager, Engineer). Weekly buckets start on Monday, matching
    PostgreSQL's date_trunc('week') behavior.

    Postings first observed on the baseline date — min(fetched_at::date), the
    earliest day the platform saw any posting — are excluded. That first crawl is
    a one-time bulk load of whatever the sources had open at the time, not market
    activity for that day, so counting it would read as a hiring surge. The
    baseline is identified purely by date; ingestion_run_id is never referenced
    (it is NULL on most historical rows). See backend/specs/market-health/api.md —
    Business Logic — Trend aggregation.
    """
    bucket = "week" if granularity == "week" else "month"
    period_format = "YYYY-MM-DD" if bucket == "week" else "YYYY-MM"
    with get_connection() as conn:
        baseline_row = conn.execute(
            "SELECT min(fetched_at::date) FROM raw_postings"
        ).fetchone()
        baseline_date: date | None = baseline_row[0] if baseline_row else None

        rows = conn.execute(
            f"""
            WITH baseline AS (
                SELECT min(fetched_at::date) AS day FROM raw_postings
            )
            SELECT to_char(date_trunc('{bucket}', rp.fetched_at), '{period_format}') AS period,
                   c.role_category,
                   count(DISTINCT rp.id) AS n
            FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            WHERE c.role_category IN ('Designer', 'Product Manager', 'Engineer')
              AND rp.fetched_at::date > (SELECT day FROM baseline)
            GROUP BY period, c.role_category
            ORDER BY period
            """
        ).fetchall()

    by_period: dict[str, dict[str, int]] = {}
    for period, role_category, n in rows:
        by_period.setdefault(period, {})[role_category] = n
    return by_period, baseline_date


def _to_points(by_period: dict[str, dict[str, int]]) -> list[OpeningDataPoint]:
    points = []
    for period in sorted(by_period.keys()):
        counts = by_period[period]
        points.append(OpeningDataPoint(
            period=period,
            designer=counts.get("Designer", 0),
            product_manager=counts.get("Product Manager", 0),
            engineer=counts.get("Engineer", 0),
        ))
    return points


def _slice_range(
    points: list[OpeningDataPoint], range_key: str, granularity: str
) -> list[OpeningDataPoint]:
    if range_key == "all_time":
        return points

    now = datetime.now(timezone.utc)
    if range_key == "six_months":
        # The current calendar month plus the five before it.
        month = now.month - 5
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
    elif range_key == "this_year":
        year, month = now.year, 1
    else:  # past_5_years
        year, month = now.year - 5, 1

    # Match the cutoff string's shape to the bucket key's shape ("YYYY-MM" for
    # month, "YYYY-MM-DD" for week) so a lexical compare can't drop the boundary
    # bucket — "2026-04" sorts before "2026-04-01".
    if granularity == "month":
        cutoff = f"{year:04d}-{month:02d}"
    else:
        cutoff = f"{year:04d}-{month:02d}-01"

    return [p for p in points if p.period >= cutoff]


def _pct_change(first: int, last: int) -> float:
    if first == 0:
        return 0.0 if last == 0 else 100.0
    return (last - first) / first * 100


def _direction_word(pct: float) -> str:
    if pct >= 5:
        return "up"
    if pct <= -5:
        return "down"
    return "flat"


def _range_label(range_key: str) -> str:
    return {
        "six_months": "the past 6 months",
        "this_year": "this year",
        "past_5_years": "the past 5 years",
        "all_time": "all available post-baseline data",
    }[range_key]


def _period_fully_elapsed(period: str, granularity: str, today: date) -> bool:
    """True once the whole week/month the bucket covers is in the past."""
    if granularity == "month":
        return (int(period[:4]), int(period[5:7])) < (today.year, today.month)
    return date.fromisoformat(period) + timedelta(days=6) < today


def _bucket_eligible_for_trend(
    period: str, granularity: str, today: date, baseline: date | None
) -> bool:
    """
    A bucket is an endpoint of the stated trend only if its whole period has
    elapsed (so a part-week/part-month is never compared to a full one) and it
    starts strictly after the baseline day (so the baseline-truncated first
    bucket, missing its opening day(s), is not an endpoint either).
    """
    if not _period_fully_elapsed(period, granularity, today):
        return False
    if baseline is None:
        return True
    if granularity == "month":
        return (int(period[:4]), int(period[5:7])) > (baseline.year, baseline.month)
    return date.fromisoformat(period) > baseline


def _generate_summary(
    points: list[OpeningDataPoint], range_key: str, granularity: str,
    baseline: date | None,
) -> str:
    view_label = "weekly" if granularity == "week" else "monthly"
    bucket_noun = "weeks" if granularity == "week" else "months"
    timeframe = _range_label(range_key)

    today = datetime.now(timezone.utc).date()
    complete = [
        p for p in points
        if _bucket_eligible_for_trend(p.period, granularity, today, baseline)
    ]
    if len(complete) < 2:
        return (
            f"The {view_label} view for {timeframe} does not have enough complete "
            f"{bucket_noun} after the collection baseline to show a trend yet. The first "
            "collection day is excluded, so this view reflects new jobs found afterward."
        )

    first, last = complete[0], complete[-1]
    categories = [
        ("Designer", first.designer, last.designer),
        ("Product Manager", first.product_manager, last.product_manager),
        ("Engineer", first.engineer, last.engineer),
    ]

    fragments = []
    for name, f, l in categories:
        pct = _pct_change(f, l)
        direction = _direction_word(pct)
        if direction == "flat":
            fragments.append(f"{name} openings have stayed roughly flat")
        else:
            fragments.append(f"{name} openings are {direction} {abs(pct):.0f}%")

    return (
        f"In the {view_label} view for {timeframe}, {fragments[0]}, {fragments[1]}, "
        f"and {fragments[2]}. Counts start after the initial collection baseline, "
        "so the first bulk load is not treated as a surge in hiring."
    )


@router.get("/api/market-health/openings")
def get_openings(range: str = "six_months", granularity: str = "week") -> dict:
    """
    Returns weekly or monthly job opening counts for Designer, Product Manager, and
    Engineer categories, plus a written summary of the trend.

    Query params:
    range: "six_months" | "this_year" | "past_5_years" | "all_time"  (default: six_months)
    granularity: "week" | "month" (default: week)
    """
    if range not in VALID_RANGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid range '{range}'. Must be one of: {', '.join(sorted(VALID_RANGES))}.",
        )
    if granularity not in VALID_GRANULARITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid granularity '{granularity}'. Must be one of: week, month.",
        )

    try:
        by_period, baseline_date = _fetch_counts(granularity)
        all_points = _to_points(by_period)
    except Exception as exc:
        logger.error("Could not fetch opening trends from the database: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Job openings data is temporarily unavailable.",
        )

    # Drop the in-progress trailing bucket. A part-month (or part-week) plotted
    # at full scale next to a complete one reads as a cliff — e.g. a 4-day
    # September next to a 31-day August looks like the market fell 80%. The chart
    # only ever shows periods that have fully elapsed.
    today = datetime.now(timezone.utc).date()
    points = [
        p for p in _slice_range(all_points, range, granularity)
        if _period_fully_elapsed(p.period, granularity, today)
    ]

    return {
        "range": range,
        "granularity": granularity,
        "data": [
            {
                "period": p.period,
                "designer": p.designer,
                "product_manager": p.product_manager,
                "engineer": p.engineer,
            }
            for p in points
        ],
        "summary": _generate_summary(points, range, granularity, baseline_date),
        "as_of": datetime.now(timezone.utc).date().isoformat(),
        "source": "Company job boards hosted on Greenhouse, Lever, and Ashby — live postings, LLM-classified",
    }
