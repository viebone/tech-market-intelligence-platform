from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class PostingPeriod:
    """A single data point in a time-series of job posting counts."""
    period: str   # "YYYY-MM"
    count: int


@dataclass
class MarketHealthSignal:
    verdict: str              # "Healthy" | "Cautious" | "Contracting"
    explanation: str          # one-sentence plain-language explanation
    trend_direction: str      # "improving" | "stable" | "worsening"
    as_of: date
    source: str


@dataclass
class SearchImplication:
    text: str
    signal_verdict: str       # matches the verdict this implication corresponds to


@dataclass
class DemandSignal:
    role_family: str          # e.g. "UX Design", "Product Management"
    seniority: str            # e.g. "Senior", "Mid"
    location: str
    posting_trend: list[PostingPeriod]
    trend_direction: str      # "rising" | "stable" | "declining"
    as_of: date
    source: str


@dataclass
class CompensationSignal:
    role_family: str
    seniority: str
    location: str
    salary_min: int           # annual, local currency
    salary_max: int
    salary_median: int
    trend_direction: str      # "rising" | "stable" | "declining"
    as_of: date
    source: str


@dataclass
class LayoffSignal:
    company: str
    sector: str
    event_date: date
    headcount_affected: Optional[int]   # None if unconfirmed
    source: str


@dataclass
class OpeningDataPoint:
    month: str            # "YYYY-MM"
    designer: int
    product_manager: int
    engineer: int


# ---------------------------------------------------------------------------
# Reasoning trace models
# ---------------------------------------------------------------------------

@dataclass
class SourceAccess:
    sequence: int
    source_type: str   # "data_source" | "tool"
    name: str
    purpose: str


@dataclass
class ReasoningStep:
    sequence: int
    content: str


@dataclass
class ReasoningTrace:
    input_context: str
    sources_and_tools: list[SourceAccess]
    reasoning_steps: list[ReasoningStep]
    is_complete: bool
