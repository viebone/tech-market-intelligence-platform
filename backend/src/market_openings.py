"""
FastAPI router for job opening trend data.

Endpoint:
  GET /api/market-health/openings

Returns monthly job opening counts per role category (Designer, Product Manager,
Engineer) for three time ranges, plus a pre-computed written summary.
"""

from __future__ import annotations

import dataclasses
from typing import Literal

from fastapi import APIRouter, HTTPException

from mock_data import OPENING_SUMMARIES, OPENING_TRENDS

router = APIRouter()

TimeRange = Literal["this_year", "past_5_years", "all_time"]
VALID_RANGES: set[str] = {"this_year", "past_5_years", "all_time"}


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

    data = [dataclasses.asdict(pt) for pt in OPENING_TRENDS[range]]
    summary = OPENING_SUMMARIES[range]

    return {
        "range": range,
        "data": data,
        "summary": summary,
        "as_of": "2026-06-01",
        "source": "Aggregated from job board postings (LinkedIn, UX Jobs Board, Remote OK)",
    }
