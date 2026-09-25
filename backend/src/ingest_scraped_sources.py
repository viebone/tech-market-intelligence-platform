"""
Scraped market-benchmark sources ingestion entry point.

Run manually, or safe to invoke as often as you like via any external
scheduler — the once-a-week cadence is enforced HERE, in code, not left to
whoever/whatever calls this:
    python ingest_scraped_sources.py

For each registered scraped-source adapter (IT Jobs Watch, so far — see
scraping/), first checks scraping_storage.is_due() against
scrape_ingestion_runs — a source run less than MIN_RUN_INTERVAL_DAYS (7,
per source, scraping/__init__.py) ago is skipped for this invocation
entirely, no request made at all. For a source that *is* due: fetches its
currently reachable market-benchmark observations and skill associations,
stores new rows in market_observations / skill_associations — deduped by
id *and* by value (an observation identical to the last one stored for the
same entity is skipped even under a new id, since a shifting rolling window
alone shouldn't create a "new" row when nothing about the market changed —
"focus on new things, not old", Business Logic rule 9). Safe to re-run —
idempotent either way, same pattern as ingest.py / ingest_employment_events.py.

Deliberately a **separate** entry point, not folded into either of those:
different tables, a categorically different fetch mechanism (scraping vs.
API calls — robots.txt, page caching, pacing floor, mandatory contact
identification), and its own permission-conditioned pacing and cadence that
must never be pressured by another pipeline's schedule.

*** Extraction is LLM-based, not regex (revised 2026-09-18 — see
scraping/itjobswatch.py's module docstring and
changes/2026-09-18-itjobswatch-llm-extraction.md). Running this script makes
a real Gemini call per page that isn't already cached in scrape_extractions
by content hash — never a fabricated value for a field the model doesn't
return. ***

Requires SCRAPER_CONTACT to be set to a real contact (backend/.env.example)
— ItJobsWatchAdapter's construction raises ScraperConfigError immediately
if it isn't, per this feature's stricter-than-SEC_EDGAR_CONTACT identification
rule (backend/specs/scraped-data-sources/api.md — Tech Decisions).

See backend/specs/scraped-data-sources/api.md; changes/2026-09-16-polite-scraping-adapters.md.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from datetime import datetime, timezone

from db import init_schema
from scraping import (
    ALL_SCRAPED_SOURCE_ADAPTERS,
    DEFAULT_MIN_RUN_INTERVAL_DAYS,
    MIN_RUN_INTERVAL_DAYS,
    ScraperConfigError,
    is_commercial_mode,
    is_source_usable,
)
from scraping_storage import (
    PostgresExtractionCacheStore,
    PostgresPageCacheStore,
    PostgresRobotsCacheStore,
    insert_market_observations,
    insert_skill_associations,
    is_due,
    record_run,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _empty_result(source: str, error: str | None) -> dict:
    return {"source": source, "observations_fetched": 0, "observations_inserted": 0,
            "associations_fetched": 0, "associations_inserted": 0, "error": error,
            "skipped_not_due": False}


def ingest_adapter(adapter_cls, robots_store, page_store, extraction_store) -> dict:
    """
    Construct, fetch, and store one adapter's results. Never raises — an
    adapter that fails (including refusing to construct because
    SCRAPER_CONTACT is missing) is recorded with its error rather than
    propagated, so one bad source can't abort the run (fault isolation,
    same pattern as ingest_employment_events.ingest_adapter).

    **Ingestion always proceeds, full stop — never gated by anything in
    source_licences.py.** Revised 2026-09-16 per explicit direction: "make
    sure that ingestions always work... in any case the ingestions can work
    until we say the opposite." Collecting has value on its own, independent
    of whether the data can currently be *used* (see
    source_licences.py's own module note — two separate lifecycles). The
    only thing that happens here is a visible, non-blocking log line when a
    source has been explicitly `rejected=True` for use, so nobody is
    surprised later about what's sitting in the database that isn't cleared
    for use yet — see research/2026-09-16-commercial-mode-kill-switch.md.

    Enforces run cadence (Business Logic rule 8) before a single request is
    made — a source not yet due for its next run is skipped, not
    fetched-then-discarded. Even a failed run still records a run timestamp
    (below) so a broken adapter can't be retried in a tight loop either.
    """
    name = getattr(adapter_cls, "name", adapter_cls.__name__)

    if not is_source_usable(name):
        logger.info(
            "ingest_scraped_sources[%s]: this source is marked rejected=True for USE — "
            "collecting anyway (ingestion is never gated on this), but this data must be "
            "excluded wherever it's actually used until that's reversed.",
            name,
        )

    min_interval = MIN_RUN_INTERVAL_DAYS.get(name, DEFAULT_MIN_RUN_INTERVAL_DAYS)
    if not is_due(name, min_interval):
        logger.info(
            "ingest_scraped_sources[%s]: not due yet (runs at most every %d day(s)) — skipped",
            name, min_interval,
        )
        result = _empty_result(name, None)
        result["skipped_not_due"] = True
        return result

    now = datetime.now(timezone.utc)
    try:
        adapter = adapter_cls(robots_store=robots_store, page_store=page_store, extraction_store=extraction_store)
        result_data = adapter.fetch()
    except ScraperConfigError as exc:
        logger.error("ingest_scraped_sources[%s]: refused to run: %s", name, exc)
        record_run(name, now)
        return _empty_result(name, str(exc))
    except Exception as exc:
        logger.exception("ingest_scraped_sources[%s]: fetch failed: %s", name, exc)
        record_run(name, now)
        return _empty_result(name, str(exc))

    new_observation_ids = insert_market_observations(adapter.name, result_data.market_observations)
    new_association_ids = insert_skill_associations(adapter.name, result_data.skill_associations)
    record_run(adapter.name, now)
    logger.info(
        "ingest_scraped_sources[%s]: %d/%d new observations, %d/%d new skill associations",
        adapter.name, len(new_observation_ids), len(result_data.market_observations),
        len(new_association_ids), len(result_data.skill_associations),
    )
    return {
        "source": adapter.name,
        "observations_fetched": len(result_data.market_observations),
        "observations_inserted": len(new_observation_ids),
        "associations_fetched": len(result_data.skill_associations),
        "associations_inserted": len(new_association_ids),
        "error": None,
        "skipped_not_due": False,
    }


def run() -> bool:
    """Returns False if any adapter had an error (so a caller — ingest_periodic.py — can see it in the exit code)."""
    init_schema()
    if is_commercial_mode():
        logger.info(
            "ingest_scraped_sources: TMIP_COMMERCIAL_MODE is ON — this is informational only, "
            "a reminder to go review source_licences.py's SOURCE_LICENCES and set rejected=True "
            "on anything that shouldn't be used commercially. Ingestion collects every "
            "registered source regardless (collection is never gated on this or on `rejected`); "
            "any explicitly rejected source is logged per-adapter, below."
        )
    robots_store = PostgresRobotsCacheStore()
    page_store = PostgresPageCacheStore()
    extraction_store = PostgresExtractionCacheStore()
    results = [
        ingest_adapter(adapter_cls, robots_store, page_store, extraction_store)
        for adapter_cls in ALL_SCRAPED_SOURCE_ADAPTERS
    ]

    total_obs_fetched = sum(r["observations_fetched"] for r in results)
    total_obs_inserted = sum(r["observations_inserted"] for r in results)
    total_assoc_fetched = sum(r["associations_fetched"] for r in results)
    total_assoc_inserted = sum(r["associations_inserted"] for r in results)
    skipped_not_due = sum(1 for r in results if r["skipped_not_due"])
    any_failed = any(r["error"] is not None for r in results)

    logger.info(
        "ingest_scraped_sources: done — %d/%d observations, %d/%d skill associations, "
        "%d source(s) skipped (not due yet), %s",
        total_obs_inserted, total_obs_fetched, total_assoc_inserted, total_assoc_fetched,
        skipped_not_due,
        "one or more adapters had an error (see log above)" if any_failed else "no errors",
    )
    return not any_failed


if __name__ == "__main__":
    # Exit non-zero on an adapter error: this script used to exit 0 regardless, which would let the periodic runner
    # report a failed scrape as "ok" (changes/2026-09-25-periodic-source-ingestion-in-job-sync.md).
    sys.exit(0 if run() else 1)
