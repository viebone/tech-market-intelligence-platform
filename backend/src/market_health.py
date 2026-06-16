"""
FastAPI router for Market Health endpoints.

Endpoints:
  GET /api/market-health/summary
  GET /api/market-health/trends
  GET /api/alerts/exceptions
"""

from __future__ import annotations

import dataclasses
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from mock_data import (
    AS_OF,
    COMPENSATION_SIGNALS,
    DEMAND_SIGNALS,
    LAYOFF_SIGNALS,
    MARKET_HEALTH_SIGNALS,
    SEARCH_IMPLICATIONS,
    slice_posting_trend,
)
from models import (
    CompensationSignal,
    DemandSignal,
    LayoffSignal,
    MarketHealthSignal,
    PostingPeriod,
    SearchImplication,
)

router = APIRouter()

VALID_PERIODS = {"3m", "6m", "12m"}


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _serialise(obj: object) -> object:
    """Recursively convert dataclasses and dates to JSON-safe types."""
    if isinstance(obj, date):
        return obj.isoformat()
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _serialise(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, list):
        return [_serialise(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serialise(v) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------------------
# Filtering helpers
# ---------------------------------------------------------------------------

def _normalise(value: str) -> str:
    return value.strip().lower()


def _filter_demand(
    role: str, seniority: str, location: str
) -> list[DemandSignal]:
    r, s, loc = _normalise(role), _normalise(seniority), _normalise(location)
    return [
        d for d in DEMAND_SIGNALS
        if (r == "all" or _normalise(d.role_family) == r)
        and (s == "all" or _normalise(d.seniority) == s)
        and (loc == "all" or _normalise(d.location) == loc)
    ]


def _filter_compensation(
    role: str, seniority: str, location: str
) -> list[CompensationSignal]:
    r, s, loc = _normalise(role), _normalise(seniority), _normalise(location)
    return [
        c for c in COMPENSATION_SIGNALS
        if (r == "all" or _normalise(c.role_family) == r)
        and (s == "all" or _normalise(c.seniority) == s)
        and (loc == "all" or _normalise(c.location) == loc)
    ]


def _resolve_signal(
    role: str, seniority: str, location: str
) -> tuple[Optional[MarketHealthSignal], SearchImplication | None]:
    """
    Look up the most-specific matching MarketHealthSignal and its implication.

    Lookup order (most specific → most general):
      1. (role, seniority, location) exact match
      2. ("all", "all", "all") aggregate
    If no matching signal, return (None, None).
    """
    r, s, loc = _normalise(role), _normalise(seniority), _normalise(location)

    signal: Optional[MarketHealthSignal] = MARKET_HEALTH_SIGNALS.get(
        (r, s, loc)
    )

    # Fall back to aggregate only when all three params are "all"
    if signal is None and (r == "all" and s == "all" and loc == "all"):
        signal = MARKET_HEALTH_SIGNALS.get(("all", "all", "all"))

    if signal is None:
        return None, None

    implication = SEARCH_IMPLICATIONS.get(signal.verdict)
    return signal, implication


# ---------------------------------------------------------------------------
# GET /api/market-health/summary
# ---------------------------------------------------------------------------

@router.get("/api/market-health/summary")
def get_summary(
    role: str = Query(default="all"),
    seniority: str = Query(default="all"),
    location: str = Query(default="all"),
) -> JSONResponse:
    """
    Returns the current MarketHealthSignal and SearchImplication for the
    given filters. Returns verdict: null when no data matches.
    """
    signal, implication = _resolve_signal(role, seniority, location)

    if signal is None:
        return JSONResponse(content={"signal": None, "implication": None})

    return JSONResponse(
        content={
            "signal": {
                "verdict": signal.verdict,
                "explanation": signal.explanation,
                "trendDirection": signal.trend_direction,
                "asOf": signal.as_of.isoformat(),
                "source": signal.source,
            },
            "implication": {"text": implication.text} if implication else None,
        }
    )


# ---------------------------------------------------------------------------
# GET /api/market-health/trends
# ---------------------------------------------------------------------------

@router.get("/api/market-health/trends")
def get_trends(
    role: str = Query(default="all"),
    seniority: str = Query(default="all"),
    location: str = Query(default="all"),
    period: str = Query(default="6m"),
) -> JSONResponse:
    """
    Returns time-series Demand, Compensation, and Layoff Signals.
    The posting_trend arrays are sliced to the requested period.
    """
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period '{period}'. Must be one of: {', '.join(sorted(VALID_PERIODS))}.",
        )

    demand_signals = _filter_demand(role, seniority, location)
    comp_signals = _filter_compensation(role, seniority, location)

    demand_series = []
    for d in demand_signals:
        sliced = slice_posting_trend(d.posting_trend, period)
        demand_series.append({
            "id": f"{d.role_family}_{d.seniority}_{d.location}".lower().replace(" ", "_"),
            "title": f"{d.role_family} · {d.seniority} · {d.location}",
            "data": [{"period": p.period, "value": p.count} for p in sliced],
            "direction": d.trend_direction,
            "asOf": d.as_of.isoformat(),
            "source": d.source,
        })

    comp_series = []
    for c in comp_signals:
        comp_series.append({
            "id": f"comp_{c.role_family}_{c.seniority}_{c.location}".lower().replace(" ", "_"),
            "title": f"{c.role_family} · {c.seniority} · {c.location}",
            "data": [{"period": c.as_of.isoformat(), "value": c.salary_median}],
            "direction": c.trend_direction,
            "asOf": c.as_of.isoformat(),
            "source": c.source,
        })

    layoffs = [
        {
            "id": str(i),
            "company": l.company,
            "sector": l.sector,
            "date": l.event_date.isoformat(),
            "affectedCount": l.headcount_affected,
            "notes": None,
        }
        for i, l in enumerate(LAYOFF_SIGNALS)
    ]

    return JSONResponse(
        content={
            "demand": demand_series,
            "compensation": comp_series,
            "layoffs": layoffs,
            "layoffsAsOf": AS_OF.isoformat(),
            "layoffsSource": "Layoffs.fyi",
        }
    )


# ---------------------------------------------------------------------------
# GET /api/alerts/exceptions
# ---------------------------------------------------------------------------

@router.get("/api/alerts/exceptions")
def get_exceptions() -> JSONResponse:
    """Returns unresolved Exceptions for the current user. Empty in v1."""
    return JSONResponse(content={"exceptions": []})
