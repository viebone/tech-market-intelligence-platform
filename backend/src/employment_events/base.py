"""
Adapter abstraction for employment-event sources (layoffs, closures,
restructuring, bankruptcy, offshoring, expansion, hiring announcements).

Deliberately a separate protocol from sources.base.SourceAdapter, not a reuse
of it — the output shape is genuinely different (FetchedEmploymentEvent, not
FetchedPosting; no title/description to classify). See
backend/specs/market-health/api.md — Tech Decisions — EmploymentEventAdapter,
and changes/2026-09-11-employment-event-ingestion.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol


# Closed set — must match backend/specs/market-health/api.md — Data Models —
# EmploymentEvent — event_type, and design/market-health/experience.md's
# Chart Specification / User Flow 7d.
EVENT_TYPES = {
    "layoff", "closure", "restructuring", "bankruptcy", "offshoring",
    "expansion", "hiring_announcement",
}

# Human-readable registry names for provenance display (API responses, the
# Reasoning Panel's Sources section, chart-marker source_url labels) — one
# place to maintain these, shared by market_employment_events.py and
# market_query.py's query_employment_events_data.
SOURCE_DISPLAY_NAMES: dict[str, str] = {
    "eurofound_erm": "Eurofound European Restructuring Monitor",
    "us_warn": "US state WARN notices",
    "companies_house_insolvency": "UK Companies House (insolvency register)",
    "sec_edgar_8k": "SEC EDGAR (8-K Item 2.05 filings)",
}

# Derived, not independently input — see EmploymentEvent.direction in the
# backend spec: computed once from event_type, never a second signal that
# could disagree with it.
_CONTRACTION_TYPES = {"layoff", "closure", "restructuring", "bankruptcy", "offshoring"}
_EXPANSION_TYPES = {"expansion", "hiring_announcement"}


# Added 2026-09-11 — changes/2026-09-11-employment-risk-hide-placeholder-names.md.
# A source that carries no company name (UK Companies House's Streaming API,
# so far) gives us only a bare id — company_raw stores exactly that, never a
# fabricated "Company N" string. This is what keeps a bare id from ever being
# shown as if it were a real company. Matches both the corrected bare-id form
# ("12028607") and the two already-inserted legacy rows that predate this fix
# ("Company 12028607") — those rows are immutable and never rewritten
# (Data Models — EmploymentEvent), so the check has to catch both shapes.
_PLACEHOLDER_NAME_RE = re.compile(r"^(company\s+)?\d+$", re.IGNORECASE)


def is_real_company_name(company_raw: str) -> bool:
    """
    False for a bare id or an id dressed up as "Company {id}" — anything
    that isn't a real name a source actually reported. Used to keep such
    events out of any company-name-specific display (e.g. the Employment
    Risk story's "Companies with the most reported impact" ranking) while
    the events themselves still count toward direction/country/sector
    aggregates, which never reference company_raw.
    """
    return not _PLACEHOLDER_NAME_RE.match(company_raw.strip())


def direction_for(event_type: str) -> str:
    """'contraction' | 'expansion', derived from event_type. Raises on an
    event_type outside the closed set — a caller must validate before this
    point, same discipline as role_category validation elsewhere."""
    if event_type in _CONTRACTION_TYPES:
        return "contraction"
    if event_type in _EXPANSION_TYPES:
        return "expansion"
    raise ValueError(f"Unrecognised event_type: {event_type!r}")


@dataclass
class FetchedEmploymentEvent:
    """One employment event as returned by an adapter, before storage."""
    source_ref: str
    company_raw: str
    event_date: date
    event_type: str          # validated against EVENT_TYPES at insert time
    jobs_affected: int | None = None
    country: str | None = None
    region: str | None = None
    sector: str | None = None
    source_url: str | None = None
    # "reported" (registry compiled from public announcements/press) |
    # "confirmed" (a legal/statutory filing or an official register) — each
    # adapter sets its own fixed value, never inferred per-record.
    confidence: str = "reported"
    raw_response: dict = field(default_factory=dict)


class EmploymentEventAdapter(Protocol):
    """
    Protocol every employment-event source adapter implements. Each adapter
    lives in employment_events/{name}.py. To add a new source, create a class
    implementing this protocol — nothing else in the employment-events
    pipeline changes.
    """

    name: str  # "eurofound_erm" | "us_warn" | "companies_house_insolvency"

    def fetch(self) -> list[FetchedEmploymentEvent]:
        """
        Fetch this source's currently available records. Never raises for a
        single record's failure to parse — logged and skipped, the adapter
        continues (same per-record tolerance job-posting adapters give
        per-company). Only a whole-adapter-level failure propagates, for
        orchestration to catch without aborting the other employment-event
        adapters. See backend/specs/market-health/api.md — Business Logic —
        Employment event ingestion.
        """
        ...
