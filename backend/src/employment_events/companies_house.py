"""
UK Companies House — insolvency adapter, via the **Streaming API**.

Revised 2026-09-11 (changes/2026-09-11-employment-events-no-company-matching.md):
the original design queried insolvency records for a curated candidate list of
companies drawn from the platform's own 35 tracked job-posting companies —
itself a form of company-matching the user's direction rules out. Replaced
with the Companies House Streaming API
(https://stream.companieshouse.gov.uk/insolvency-cases), confirmed live via
research the same day: a real-time feed of insolvency events across **all**
UK companies, no company targeting needed at all. Same free API key as the
REST API (Companies House Developer Hub — https://developer.company-information.service.gov.uk/),
different base URL/domain.

**Response shape confirmed live 2026-09-11** (a real authenticated call against
this exact endpoint, not a guess). Real example:
```json
{
  "resource_kind": "company-insolvency",
  "resource_uri": "/company/08439491/insolvency",
  "resource_id": "08439491",
  "data": {
    "cases": [{
      "dates": [{"date": "2025-06-26", "type": "wound-up-on"}],
      "number": "1",
      "practitioners": [...],
      "type": "creditors-voluntary-liquidation"
    }],
    "status": ["liquidation"]
  },
  "event": {"timepoint": 3654082, "published_at": "2026-09-11T13:54:01", "type": "changed"}
}
```
This corrected an initial guess in three places: the company identifier is
top-level `resource_id`, not nested under a `resource` key; the case list is
under `data.cases`, not `resource.case`; a case's date field is `date`, not
`made_up_date`.

**Known, permanent limitation: this stream carries no company name, only a
company number.** Every record's `company_raw` is `"Company {number}"` — a
real Companies House REST API call (`GET /company/{number}`) would resolve
the actual name, but that needs a **separate REST-type key**, not
interchangeable with the Streaming key this adapter uses (confirmed:
Companies House explicitly keeps REST and Streaming keys separate, chosen at
creation, not convertible after). Revisit if a REST key is ever added
alongside this one — out of scope for now, an honest gap, not a bug.

**Event type**: every record on the `insolvency-cases` stream is, by
construction, an insolvency event — this platform's `event_type` set has no
sub-classification finer than `"bankruptcy"` for that (see `EVENT_TYPES`,
`employment_events/base.py`), so every mapped record uses it directly; no
case-type lookup table is needed.

A long-running connection, not a simple request/response — this adapter
connects with a `timepoint` cursor (persisted in employment_event_cursors,
see employment_events_storage-adjacent Business Logic in the backend spec),
reads until the stream goes idle (caught up to "live"), then disconnects.
This is a scheduled batch job's version of tailing a stream, not a permanent
connection — ingest_employment_events.py runs this once a day.
"""

from __future__ import annotations

import base64
import json
import logging
import os

import httpx

from db import get_connection
from employment_events.base import EVENT_TYPES, FetchedEmploymentEvent

logger = logging.getLogger(__name__)

STREAM_URL = "https://stream.companieshouse.gov.uk/insolvency-cases"

# How long to wait for the next event before deciding the stream has caught
# up to "live" and it's time to disconnect. Generous enough that a brief gap
# between real events doesn't cut the read short.
IDLE_TIMEOUT_SECONDS = 15.0
# Hard cap so one run can never read forever even if events keep arriving —
# the next scheduled run picks up from the saved cursor.
MAX_EVENTS_PER_RUN = 2000


def _auth_header() -> dict[str, str]:
    api_key = os.environ["COMPANIES_HOUSE_API_KEY"]
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _get_cursor() -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT cursor FROM employment_event_cursors WHERE source = %s",
            ("companies_house_insolvency",),
        ).fetchone()
    return row[0] if row else None


def _save_cursor(cursor: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO employment_event_cursors (source, cursor, updated_at)
            VALUES (%s, %s, now())
            ON CONFLICT (source) DO UPDATE SET cursor = EXCLUDED.cursor, updated_at = now()
            """,
            ("companies_house_insolvency", cursor),
        )


def _map_event(event: dict) -> tuple[FetchedEmploymentEvent | None, str | None]:
    """
    Returns (mapped event or None, timepoint of this event or None). Field
    names below confirmed against a real streamed event (module docstring).
    Still fails loudly, not silently, on a shape that doesn't match — a
    future stream schema change should surface as a skipped-and-logged
    record, never a guess.
    """
    event_meta = event.get("event") or {}
    timepoint_raw = event_meta.get("timepoint")
    timepoint = str(timepoint_raw) if timepoint_raw is not None else None

    company_number = event.get("resource_id")
    cases = (event.get("data") or {}).get("cases") or []

    if not company_number or not cases:
        logger.warning(
            "companies_house_insolvency: streamed event missing resource_id "
            "or data.cases — skipped, not guessed. Raw event: %r", event,
        )
        return None, timepoint

    # A record can carry multiple cases (renewed/updated proceedings); the
    # most recent one — first in the list, matching the REST API's own
    # ordering — is what this event represents.
    case = cases[0]
    dates = case.get("dates") or []
    event_date = dates[0].get("date") if dates else None
    if not event_date:
        logger.warning(
            "companies_house_insolvency: streamed event with no usable case "
            "date for company_number %s — skipped.", company_number,
        )
        return None, timepoint

    event_type = "bankruptcy"  # every record on this stream is, by construction
    assert event_type in EVENT_TYPES

    return FetchedEmploymentEvent(
        source_ref=f"{company_number}:{case.get('number', case.get('type', 'case'))}",
        # No company name in this stream — a real, permanent limitation
        # (module docstring). company_raw is the bare id exactly as the
        # source gave it, never dressed up as a fabricated "Company N"
        # string — that would misrepresent what the source actually
        # reported (revised 2026-09-11 —
        # changes/2026-09-11-employment-risk-hide-placeholder-names.md).
        # is_real_company_name() (base.py) is what keeps a bare id from
        # ever being displayed as if it were a company name.
        company_raw=company_number,
        event_date=event_date,
        event_type=event_type,
        jobs_affected=None,  # this endpoint never sizes headcount impact
        country="GB",
        source_url=f"https://find-and-update.company-information.gov.uk/company/{company_number}",
        confidence="confirmed",  # the official UK company register
        raw_response=event,
    ), timepoint


class CompaniesHouseInsolvencyAdapter:
    name = "companies_house_insolvency"

    def fetch(self) -> list[FetchedEmploymentEvent]:
        api_key = os.environ.get("COMPANIES_HOUSE_API_KEY")
        if not api_key:
            logger.info(
                "companies_house_insolvency: COMPANIES_HOUSE_API_KEY is not "
                "set — skipping. Sign up free at "
                "https://developer.company-information.service.gov.uk/."
            )
            return []

        cursor = _get_cursor()
        params = {"timepoint": cursor} if cursor else {}
        results: list[FetchedEmploymentEvent] = []
        last_timepoint: str | None = cursor
        read_timeout = httpx.Timeout(30.0, read=IDLE_TIMEOUT_SECONDS)

        try:
            with httpx.Client(timeout=read_timeout, headers=_auth_header()) as client:
                with client.stream("GET", STREAM_URL, params=params) as response:
                    response.raise_for_status()
                    count = 0
                    for line in response.iter_lines():
                        if not line or not line.strip():
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning(
                                "companies_house_insolvency: non-JSON stream line, "
                                "skipped: %r", line[:200],
                            )
                            continue

                        mapped, timepoint = _map_event(event)
                        if timepoint:
                            last_timepoint = timepoint
                        if mapped is not None:
                            results.append(mapped)

                        count += 1
                        if count >= MAX_EVENTS_PER_RUN:
                            logger.info(
                                "companies_house_insolvency: hit MAX_EVENTS_PER_RUN "
                                "(%d) — stopping early, next run resumes from cursor.",
                                MAX_EVENTS_PER_RUN,
                            )
                            break
        except httpx.ReadTimeout:
            # Expected, not an error: the stream caught up to "live" and went
            # idle — this is how a batch job knows to stop tailing.
            logger.info("companies_house_insolvency: stream idle, caught up for this run.")
        except httpx.HTTPStatusError as exc:
            logger.error("companies_house_insolvency: stream request failed: %s", exc)
            return results  # keep whatever was read before the failure

        if last_timepoint and last_timepoint != cursor:
            _save_cursor(last_timepoint)

        return results
