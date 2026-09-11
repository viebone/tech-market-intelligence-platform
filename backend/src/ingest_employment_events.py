"""
Employment-events ingestion entry point.

Run manually or via an external scheduler (a separate Railway cron service
from job-posting ingestion — see the Scheduling note below):
    python ingest_employment_events.py

For each employment-event adapter (Eurofound ERM, US state WARN, UK
Companies House insolvency — see backend/src/employment_events/), fetches
that source's currently available records, dedupes by id, stores new rows
in employment_events. Run now, safe to re-run — same pattern as
reprocess_taxonomy.py / reclassify_unknowns.py.

Deliberately a **separate** entry point from ingest.py, not folded into it
(backend/specs/market-health/api.md — Tech Decisions — Scheduling):
different table, no shared back-pressure, and a source that turns out to
need a manual/gated access step (Eurofound ERM's access mechanism is
unconfirmed as of this writing — see employment_events/eurofound_erm.py)
can't share one automated daily trigger with sources that are fully
automatable without either blocking on the slowest one or silently
skipping it. As of this writing, EurofoundErmAdapter and UsWarnAdapter both
return an empty list (their real fetch mechanisms are not yet confirmed —
see each module's own TODO); only CompaniesHouseInsolvencyAdapter is fully
wired, and its own CANDIDATE_COMPANIES seed list is empty pending research
into which tracked companies have a real UK entity. Running this script
today is safe and idempotent — it will simply insert nothing until those
are filled in.

See backend/specs/market-health/api.md — Business Logic — Employment event
ingestion; changes/2026-09-11-employment-event-ingestion.md.
"""

from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from db import init_schema
from employment_events import ALL_EMPLOYMENT_EVENT_ADAPTERS
from employment_events_storage import insert_new_events

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_adapter(adapter) -> dict:
    """
    Fetch and store new events for one adapter. Never raises — an adapter
    that fails is recorded with its error rather than propagated, so one
    bad source can't abort the run (Business Logic — Employment event
    ingestion — per-adapter fault isolation, mirroring the job-posting
    pipeline's per-company/per-adapter isolation one level up, since these
    adapters have no per-company loop of their own).
    """
    try:
        events = adapter.fetch()
    except Exception as exc:
        logger.exception("ingest_employment_events[%s]: fetch failed: %s", adapter.name, exc)
        return {"source": adapter.name, "fetched": 0, "inserted": 0, "error": str(exc)}

    new_ids = insert_new_events(adapter.name, events)
    logger.info(
        "ingest_employment_events[%s]: fetched %d, inserted %d new",
        adapter.name, len(events), len(new_ids),
    )
    return {"source": adapter.name, "fetched": len(events), "inserted": len(new_ids), "error": None}


def run() -> None:
    init_schema()
    results = [ingest_adapter(adapter) for adapter in ALL_EMPLOYMENT_EVENT_ADAPTERS]

    total_fetched = sum(r["fetched"] for r in results)
    total_inserted = sum(r["inserted"] for r in results)
    any_failed = any(r["error"] is not None for r in results)

    logger.info(
        "ingest_employment_events: done — %d fetched, %d inserted, %s",
        total_fetched, total_inserted,
        "one or more adapters had an error (see log above)" if any_failed else "no errors",
    )


if __name__ == "__main__":
    run()
