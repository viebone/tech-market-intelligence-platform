"""
US WARN (Worker Adjustment and Retraining Notification Act) notices, via
WARN Firehose (warnfirehose.com) — a single aggregated API covering all 50
states, all in one integration.

Replaces this adapter's original per-state scraping design (each state
publishing its own idiosyncratic format — some XLSX, some PDF-only, no
unified federal source). Real finding from live research
(research/2026-09-11-employment-event-data-sources.md — "Expanded source
catalog", 2026-09-11): per-state scraping was the honest-but-hard path;
WARN Firehose solves the same problem in one call.

Confirmed via a real authenticated call to the live API, 2026-09-11
(`GET https://warnfirehose.com/api/records?limit=3`) — this is the actual
response shape, not a guess:
  Base URL:  https://warnfirehose.com/api/
  Endpoint:  GET /api/records
  Auth:      header "X-API-Key: {WARN_FIREHOSE_API_KEY}"
  Params:    state, company, city, date_from, date_to (YYYY-MM-DD),
             limit (default 100, max 5000), offset
  Free tier: 25 calls/day, WARN dataset only — signup at
             https://www.warnfirehose.com/account (email-verified, no
             credit card)
  Envelope:  {"records": [...], "total": int, "total_employees": int,
             "latest_notice": "YYYY-MM-DD", "states_count": int}
  Record shape (real example):
    {
      "id": "TN-2026-f990fc74",
      "company_name": "Kilgore Flares",
      "city": "Knoxville", "county": "Hardeman", "state": "TN",
      "employees_affected": 127,
      "notice_date": "2026-09-02", "effective_date": "2026-10-31",
      "layoff_type": null,             # or e.g. "Layoff" — sparsely populated
      "source_url": "https://www.tn.gov/...",
      "source_agency": "Tennessee Department of Labor and Workforce Development",
      "naics_code": null, "industry": null,   # sparsely populated
      "latitude": 35.07, "longitude": -89.15,
      "ticker": null, "cik": null, "sic_code": null,   # populated for some public companies
      "scraped_at": "2026-09-11T05:15:47Z", "source_granularity": "notice"
    }
"""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta

import httpx

from employment_events.base import EVENT_TYPES, FetchedEmploymentEvent

logger = logging.getLogger(__name__)

BASE_URL = "https://warnfirehose.com/api"
MAX_RESULTS_PER_PAGE = 5000  # the API's documented max
MAX_PAGES_PER_RUN = 3        # generous headroom under the 25 calls/day free-tier cap

# WARN notices carry no restructuring-type vocabulary the way Eurofound ERM
# does. `layoff_type` is real but sparsely populated (often null) — a
# WARN filing is, by definition, either a mass layoff or a plant closing;
# default to "layoff" when the source doesn't say which, per the "never
# guess a specific value, but a safe closed-set default is fine" pattern
# already used elsewhere (e.g. RawPosting.role_category's "other" escape
# hatch).
_LAYOFF_TYPE_TO_EVENT_TYPE = {
    "layoff": "layoff",
    "mass layoff": "layoff",
    "closure": "closure",
    "plant closing": "closure",
    "plant closure": "closure",
    "facility closure": "closure",
}


def _map_record(record: dict) -> FetchedEmploymentEvent | None:
    record_id = record.get("id")
    company = record.get("company_name")
    state = record.get("state")
    notice_date = record.get("notice_date")

    if not (company and state and notice_date):
        logger.warning(
            "us_warn: record missing company_name/state/notice_date — skipped, "
            "not guessed: %r", record,
        )
        return None

    raw_type = (record.get("layoff_type") or "layoff").strip().lower()
    event_type = _LAYOFF_TYPE_TO_EVENT_TYPE.get(raw_type, "layoff")
    assert event_type in EVENT_TYPES

    employees = record.get("employees_affected")
    jobs_affected = int(employees) if employees is not None else None

    if not record_id:
        # Real records carry a native id (e.g. "TN-2026-f990fc74"); this is
        # a fallback for the rare case one is missing, so the same notice
        # still produces the same source_ref across runs.
        record_id = f"{state}:{company}:{notice_date}"

    return FetchedEmploymentEvent(
        source_ref=str(record_id),
        company_raw=company,
        event_date=notice_date,
        event_type=event_type,
        jobs_affected=jobs_affected,
        country="US",
        region=state,
        sector=record.get("industry"),  # sparsely populated — None is honest, not a gap
        source_url=record.get("source_url"),
        confidence="confirmed",  # a WARN notice is a statutory filing
        raw_response=record,
    )


class UsWarnAdapter:
    name = "us_warn"

    def fetch(self) -> list[FetchedEmploymentEvent]:
        api_key = os.environ.get("WARN_FIREHOSE_API_KEY")
        if not api_key:
            logger.info(
                "us_warn: WARN_FIREHOSE_API_KEY is not set — skipping. Sign up "
                "free at https://www.warnfirehose.com/account."
            )
            return []

        # Real lag observed empirically 2026-09-11: an unfiltered live call's
        # `latest_notice` was 2026-09-02 while the actual date was 2026-09-11
        # — a ~9-day gap between a state filing a notice and it appearing in
        # this feed, wider than "updated daily" (about the scraper's own
        # cadence, not how current each state's own data is) suggested. A
        # 4-day window silently missed everything on the first real run. 30
        # days is a generous, empirically-informed margin; insert_new_events()'s
        # id-based dedupe (employment_events_storage.py) makes the overlap
        # free (ON CONFLICT DO NOTHING), so widening costs nothing but one
        # slightly larger response.
        date_to = date.today()
        date_from = date_to - timedelta(days=30)

        results: list[FetchedEmploymentEvent] = []
        offset = 0
        with httpx.Client(timeout=30.0, headers={"X-API-Key": api_key}) as client:
            for _ in range(MAX_PAGES_PER_RUN):
                response = client.get(
                    f"{BASE_URL}/records",
                    params={
                        "date_from": date_from.isoformat(),
                        "date_to": date_to.isoformat(),
                        "limit": MAX_RESULTS_PER_PAGE,
                        "offset": offset,
                    },
                )
                response.raise_for_status()
                records = response.json().get("records", [])
                if not records:
                    break

                for record in records:
                    event = _map_record(record)
                    if event is not None:
                        results.append(event)

                if len(records) < MAX_RESULTS_PER_PAGE:
                    break  # last page
                offset += MAX_RESULTS_PER_PAGE

        return results
