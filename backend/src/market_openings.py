"""
FastAPI router for job opening trend data.

Endpoint:
  GET /api/market-health/openings

Returns monthly job opening counts per role category (Designer, Product Manager,
Engineer) for three time ranges, plus a written summary of the trend.

Sourced from raw_postings + classifications — live-ingested, LLM-classified
postings from Greenhouse, Lever, and Ashby (Adzuna retired 2026-08-03, see
changes/2026-07-28-multi-source-job-data-ingestion.md) — not mock data. A
count is the number of distinct postings first observed by daily ingestion
in that month, not "total open positions" at any point in time: none of the
source platforms' APIs support a historical date-range query, so there is no
earlier data than when this pipeline started.
See backend/specs/market-health/api.md — Business Logic — Trend aggregation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException

from db import get_connection
from models import OpeningDataPoint

logger = logging.getLogger(__name__)

router = APIRouter()

TimeRange = Literal["this_year", "past_5_years", "all_time"]
VALID_RANGES: set[str] = {"this_year", "past_5_years", "all_time"}

_ROLE_CATEGORY_FIELDS = {
    "Designer": "designer",
    "Product Manager": "product_manager",
    "Engineer": "engineer",
}


def _fetch_monthly_counts() -> dict[str, dict[str, int]]:
    """
    Returns { "YYYY-MM": { "Designer": n, "Product Manager": n, "Engineer": n } }
    for every month that has at least one classified, non-"other" posting.
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT to_char(date_trunc('month', rp.fetched_at), 'YYYY-MM') AS month,
                   c.role_category,
                   count(*) AS n
            FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            WHERE c.role_category != 'other'
            GROUP BY month, c.role_category
            ORDER BY month
            """
        ).fetchall()

    by_month: dict[str, dict[str, int]] = {}
    for month, role_category, n in rows:
        by_month.setdefault(month, {})[role_category] = n
    return by_month


def _to_points(by_month: dict[str, dict[str, int]]) -> list[OpeningDataPoint]:
    points = []
    for month in sorted(by_month.keys()):
        counts = by_month[month]
        points.append(OpeningDataPoint(
            month=month,
            designer=counts.get("Designer", 0),
            product_manager=counts.get("Product Manager", 0),
            engineer=counts.get("Engineer", 0),
        ))
    return points


def _slice_range(points: list[OpeningDataPoint], range_key: str) -> list[OpeningDataPoint]:
    if range_key == "all_time":
        return points

    now = datetime.now(timezone.utc)
    if range_key == "this_year":
        cutoff = f"{now.year}-01"
    else:  # past_5_years
        cutoff = f"{now.year - 5}-01"

    return [p for p in points if p.month >= cutoff]


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


def _generate_summary(points: list[OpeningDataPoint]) -> str:
    if not points:
        return (
            "No live posting data is available yet for this range. Daily ingestion is "
            "still building up coverage — check back once postings have been collected."
        )

    first, last = points[0], points[-1]
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
        f"Over this period, {fragments[0]}, {fragments[1]}, and {fragments[2]}. "
        "Counts reflect postings first observed by live daily ingestion, not a backfilled "
        "historical series."
    )


@router.get("/api/market-health/openings")
def get_openings(range: str = "this_year") -> dict:
    """
    Returns monthly job opening counts for Designer, Product Manager, and
    Engineer categories, plus a written summary of the trend.

    Query params:
      range: "this_year" | "past_5_years" | "all_time"  (default: this_year)
    """
    if range not in VALID_RANGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid range '{range}'. Must be one of: {', '.join(sorted(VALID_RANGES))}.",
        )

    try:
        all_points = _to_points(_fetch_monthly_counts())
    except Exception as exc:
        logger.error("Could not fetch opening trends from the database: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Job openings data is temporarily unavailable.",
        )

    points = _slice_range(all_points, range)

    return {
        "range": range,
        "data": [
            {
                "month": p.month,
                "designer": p.designer,
                "product_manager": p.product_manager,
                "engineer": p.engineer,
            }
            for p in points
        ],
        "summary": _generate_summary(points),
        "as_of": datetime.now(timezone.utc).date().isoformat(),
        "source": "Company job boards hosted on Greenhouse, Lever, and Ashby — live postings, LLM-classified",
    }
