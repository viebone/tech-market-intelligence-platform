"""
Eurofound European Restructuring Monitor (ERM) adapter.

Priority 1 source (backend/specs/market-health/api.md — Business Logic —
Employment event ingestion): EU + Norway, company-level, covers both
contraction and expansion, reports `sector` directly.

*** ACCESS MECHANISM NOT YET EMPIRICALLY CONFIRMED — see TODO below. ***
research/2026-09-11-employment-event-data-sources.md notes an explicit
"Request data access (.csv)" option on Eurofound's restructuring-monitor
site, but whether that resolves to a public, no-key bulk download or a
gated request requiring manual approval was not verified when this spec and
this adapter's structure were written. Per this pipeline's standing "confirm
empirically, don't assume" discipline (backend/specs/market-health/api.md —
Tech Decisions — Company-list curation), this file deliberately does NOT
fabricate a working call against a guessed endpoint. fetch() returns an
empty list and logs a clear, one-time-per-run notice explaining exactly
what's unverified, instead of silently pretending to succeed or raising an
alarming exception that would look like a real adapter failure.

TODO (first task for this adapter, per the backend spec):
  1. Visit Eurofound's European Restructuring Monitor site directly and
     determine the real mechanism behind "Request data access (.csv)" —
     public bulk download (has a stable URL, no key) vs. a gated
     manual-approval request.
  2a. If public/keyless: set ACCESS_CONFIRMED = True below, fill in
      REAL_ENDPOINT, and implement _fetch_csv() to download and parse it
      into FetchedEmploymentEvent rows using the field mapping already
      sketched in _map_record() below.
  2b. If gated/manual: this adapter cannot run on the automated cron
      schedule ingest_employment_events.py drives (Tech Decisions —
      Scheduling). Instead, build a standalone "run now, safe to re-run"
      script (same pattern as reprocess_taxonomy.py /
      reclassify_unknowns.py) that ingests a manually-downloaded CSV file
      from disk, and update DATA_SOURCES.md §3a to reflect that this
      source is manual-refresh, not scheduled.
  3. Once real records are seen, verify _RESTRUCTURING_TYPE_TO_EVENT_TYPE
     below against ERM's actual restructuring-type vocabulary — the
     mapping here is a best-effort guess from the research file's example
     categories, not yet checked against a real API/CSV response.
"""

from __future__ import annotations

import logging

from employment_events.base import EVENT_TYPES, FetchedEmploymentEvent

logger = logging.getLogger(__name__)

ACCESS_CONFIRMED = False  # flip to True once step 1/2a above is done

# UNVERIFIED — placeholder pending step 1 above.
REAL_ENDPOINT = "https://restructuringmonitor.eurofound.europa.eu/erm-database"  # noqa: E501 (unverified, see TODO)

# Best-effort mapping from ERM's restructuring-type vocabulary (per the
# research file's example categories: "Internal restructuring", "Closure",
# "Bankruptcy/liquidation", "Offshoring/Delocalisation", "Business
# expansion") to this platform's closed event_type set. NOT yet validated
# against a real fetched record — see TODO step 3.
_RESTRUCTURING_TYPE_TO_EVENT_TYPE = {
    "internal restructuring": "restructuring",
    "closure": "closure",
    "bankruptcy/liquidation": "bankruptcy",
    "bankruptcy": "bankruptcy",
    "liquidation": "bankruptcy",
    "offshoring/delocalisation": "offshoring",
    "offshoring": "offshoring",
    "delocalisation": "offshoring",
    "business expansion": "expansion",
    "expansion": "expansion",
}


def _map_record(record: dict) -> FetchedEmploymentEvent | None:
    """
    Maps one ERM record (research file's example shape: company, country,
    date, sector, restructuring type, employment_change) onto
    FetchedEmploymentEvent. Not yet exercised against a real record — the
    field names below follow the research file's illustrative shape and
    must be corrected against ERM's actual response/CSV column names once
    step 1/2a (module docstring) is done.
    """
    raw_type = (record.get("type") or "").strip().lower()
    event_type = _RESTRUCTURING_TYPE_TO_EVENT_TYPE.get(raw_type)
    if event_type is None:
        logger.warning(
            "eurofound_erm: unrecognised restructuring type %r — skipped, not guessed. "
            "Add it to _RESTRUCTURING_TYPE_TO_EVENT_TYPE once confirmed.", raw_type,
        )
        return None
    assert event_type in EVENT_TYPES

    record_id = record.get("id") or record.get("case_reference")
    company = record.get("company")
    event_date = record.get("date")
    if not (record_id and company and event_date):
        logger.warning("eurofound_erm: record missing id/company/date — skipped: %r", record)
        return None

    employment_change = record.get("employment_change")
    jobs_affected = abs(int(employment_change)) if employment_change is not None else None

    return FetchedEmploymentEvent(
        source_ref=str(record_id),
        company_raw=company,
        event_date=event_date,
        event_type=event_type,
        jobs_affected=jobs_affected,
        country=record.get("country"),
        sector=record.get("sector"),
        confidence="reported",  # ERM compiles from public announcements, not a legal filing
        raw_response=record,
    )


class EurofoundErmAdapter:
    name = "eurofound_erm"

    def fetch(self) -> list[FetchedEmploymentEvent]:
        if not ACCESS_CONFIRMED:
            logger.warning(
                "eurofound_erm: access mechanism not yet confirmed — returning no "
                "events this run. See employment_events/eurofound_erm.py module "
                "docstring TODO before enabling this adapter."
            )
            return []

        # Real fetch + CSV/JSON parsing goes here once ACCESS_CONFIRMED is
        # True (TODO step 2a). Intentionally unimplemented until then, rather
        # than a fabricated call against an unverified endpoint.
        raise NotImplementedError(
            "eurofound_erm: ACCESS_CONFIRMED is True but the real fetch is not "
            "implemented yet — finish TODO step 2a in this file."
        )
