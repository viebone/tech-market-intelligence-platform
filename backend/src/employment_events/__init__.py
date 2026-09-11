"""
Registry of every live employment-event adapter, mirroring
sources/__init__.py's ALL_SOURCE_ADAPTERS pattern (job postings). Every
adapter implementing EmploymentEventAdapter (base.py) and listed in
ALL_EMPLOYMENT_EVENT_ADAPTERS below is picked up automatically —
ingest_employment_events.py's run() loops over this list generically
(employment_events fault-isolated, one bad source never blocks another) and
never names a specific source. Nothing else in the pipeline (this module,
employment_events_storage.py, the API endpoint, the chat tool) branches on
which adapter produced a row — it only ever reads `source` for provenance,
same "one adapter, one internal model" principle as job postings
(DATA_SOURCES.md §1).

**Add a new source — a 4-step recipe, no other file needs to change:**
  1. Create `employment_events/{name}.py` implementing the
     `EmploymentEventAdapter` protocol (base.py) — a `name: str` and a
     `fetch(self) -> list[FetchedEmploymentEvent]` method. Confirm the
     source's real access mechanism empirically first (an actual
     authenticated call, not a guess from docs — see us_warn.py's own
     history: a guessed field-name mapping was wrong until verified
     against one real response).
  2. Add its display name to `SOURCE_DISPLAY_NAMES` in `base.py` (used by
     the chart, the chat tool's reasoning trace, and DATA_SOURCES.md).
  3. Import it and add one instance to `ALL_EMPLOYMENT_EVENT_ADAPTERS`
     below.
  4. Update `DATA_SOURCES.md` §3a/§7 (the standing source-documentation
     requirement — changes/2026-09-11-employment-event-ingestion.md).
That's the whole recipe — `ingest_employment_events.py`, the DB schema, the
API endpoint, and the chat tool all already handle "however many adapters
are registered," not a fixed count.
"""

from employment_events.base import EmploymentEventAdapter, FetchedEmploymentEvent
from employment_events.companies_house import CompaniesHouseInsolvencyAdapter
from employment_events.eurofound_erm import EurofoundErmAdapter
from employment_events.sec_edgar import SecEdgarAdapter
from employment_events.us_warn import UsWarnAdapter

# Priority order matches backend/specs/market-health/api.md — Business Logic
# — Employment event ingestion (implementation order, not a ranking of
# importance): Eurofound ERM -> US state WARN -> UK Companies House ->
# SEC EDGAR (added 2026-09-11, research/2026-09-11-employment-event-data-sources.md
# — "Expanded source catalog").
ALL_EMPLOYMENT_EVENT_ADAPTERS: list[EmploymentEventAdapter] = [
    EurofoundErmAdapter(),
    UsWarnAdapter(),
    CompaniesHouseInsolvencyAdapter(),
    SecEdgarAdapter(),
]

__all__ = ["ALL_EMPLOYMENT_EVENT_ADAPTERS", "EmploymentEventAdapter", "FetchedEmploymentEvent"]
