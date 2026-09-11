"""
Eurofound European Restructuring Monitor (ERM) adapter.

Priority 1 source (backend/specs/market-health/api.md — Business Logic —
Employment event ingestion): EU + Norway, company-level, covers both
contraction and expansion, reports `sector` directly.

**Access mechanism confirmed and live 2026-09-11**
(changes/2026-09-11-eurofound-erm-live.md,
research/2026-09-11-eurofound-erm-access-confirmed.md) — not by asking for a
manual browser step, but by reading Eurofound's own client-side JS
(restructuring-events/assets/js/scripts/search-page.js), which shows the
"Export data" button is just the search page's own URL with `search`
replaced by `factsheetscsv` in the path: a plain, keyless, unauthenticated
GET. Verified live: 200 OK, text/csv, 33,509 rows, freshest row dated
2026-09-08. No query params returns the entire dataset — no rate limit or
pagination observed.

Full-file refetch every run, not a trailing date window: unlike WARN
Firehose/SEC EDGAR (both genuinely rate/quota-constrained), this endpoint is
an unpaginated flat CSV. insert_new_events()'s existing id-based dedupe
(already proven correct for Companies House's change-stream case) makes a
full refetch safe and cheap — no cursor needed, and a late-corrected
historical row is naturally picked up on the next run.
"""

from __future__ import annotations

import csv
import io
import logging
from collections import Counter
from datetime import date

import httpx

from employment_events.base import EVENT_TYPES, FetchedEmploymentEvent

logger = logging.getLogger(__name__)

# Verified live 2026-09-11 — see module docstring. No query params = full dataset.
EXPORT_URL = "https://apps.eurofound.europa.eu/restructuring-events/factsheetscsv"

# Real ERM restructuring-type vocabulary (all 33,509 rows, checked directly —
# not assumed). 5 of 9 real values map cleanly onto this platform's closed
# event_type set, covering 94.9% of rows. The other 4
# (Merger/Acquisition, Relocation, Reshoring, Outsourcing — 5.1%) are
# deliberately NOT mapped: their direction is genuinely ambiguous or
# unconfirmed, so they're skipped (aggregated-logged, below) rather than
# guessed onto the closest-sounding value. See research/2026-09-11-eurofound-
# erm-access-confirmed.md for the full count table and the open question on
# Reshoring specifically. "Merger /Acquisition" (extra space) is a real typo
# variant seen once in the live data — matched via .lower() + a normalized
# key, not a second dict entry.
_RESTRUCTURING_TYPE_TO_EVENT_TYPE = {
    "business expansion": "expansion",
    "internal restructuring": "restructuring",
    "closure": "closure",
    "bankruptcy": "bankruptcy",
    "offshoring/delocalisation": "offshoring",
}


def _normalize_type_key(raw_type: str) -> str:
    """Collapses whitespace variance (e.g. the real "Merger /Acquisition"
    typo vs. "Merger/Acquisition") without attempting to guess a mapping for
    either — this only affects how skipped types are counted/logged."""
    return " ".join(raw_type.strip().lower().split())


def _map_record(row: dict) -> FetchedEmploymentEvent | None:
    """
    Maps one real ERM CSV row (columns: Id, Announcement date, Country,
    Company, Sector, Restructuring type, Employment Change) onto
    FetchedEmploymentEvent. Returns None for a row whose restructuring type
    isn't in the mapped set — caller aggregates and logs these, not this
    function (avoids one warning line per record for a ~1,700-row/run
    category).
    """
    raw_type = _normalize_type_key(row.get("Restructuring type") or "")
    event_type = _RESTRUCTURING_TYPE_TO_EVENT_TYPE.get(raw_type)
    if event_type is None:
        return None
    assert event_type in EVENT_TYPES

    record_id = (row.get("Id") or "").strip()
    company = (row.get("Company") or "").strip()
    event_date_raw = (row.get("Announcement date") or "").strip()
    if not (record_id and company and event_date_raw):
        logger.warning("eurofound_erm: row missing Id/Company/Announcement date — skipped: %r", row)
        return None

    event_date = date.fromisoformat(event_date_raw)

    # 252 real rows carry the literal string "None" here (not an empty
    # field) — found while verifying this adapter against the live export,
    # not assumed. Treated the same as genuinely absent, never coerced.
    employment_change = (row.get("Employment Change") or "").strip()
    jobs_affected = (
        abs(int(employment_change))
        if employment_change and employment_change.lower() != "none"
        else None
    )

    return FetchedEmploymentEvent(
        source_ref=record_id,
        company_raw=company,
        event_date=event_date,
        event_type=event_type,
        jobs_affected=jobs_affected,
        country=(row.get("Country") or "").strip() or None,
        sector=(row.get("Sector") or "").strip() or None,
        # No stable per-record factsheet URL found — ERM's search results
        # are rendered by a dynamic fetch this adapter doesn't need to
        # reverse-engineer further. Left None rather than guessed, same
        # "absent means absent" rule as every other nullable field here.
        source_url=None,
        confidence="reported",  # ERM compiles from public announcements, not a legal filing
        raw_response=row,
    )


class EurofoundErmAdapter:
    name = "eurofound_erm"

    def fetch(self) -> list[FetchedEmploymentEvent]:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(EXPORT_URL)
            response.raise_for_status()

        reader = csv.DictReader(io.StringIO(response.text))
        results: list[FetchedEmploymentEvent] = []
        skipped_by_type: Counter[str] = Counter()

        for row in reader:
            event = _map_record(row)
            if event is not None:
                results.append(event)
            else:
                raw_type = (row.get("Restructuring type") or "").strip()
                # A missing Id/Company/Announcement date is already logged
                # per-row inside _map_record(); only count here when the
                # type itself was the reason (a recognised type would never
                # reach this branch with an unmapped raw_type).
                if _normalize_type_key(raw_type) not in _RESTRUCTURING_TYPE_TO_EVENT_TYPE:
                    skipped_by_type[raw_type] += 1

        for raw_type, count in skipped_by_type.most_common():
            logger.info(
                "eurofound_erm: skipped %d row(s) with unmapped restructuring type %r "
                "(not guessed onto the existing event_type set)", count, raw_type,
            )

        assert all(e.event_type in EVENT_TYPES for e in results)
        return results
