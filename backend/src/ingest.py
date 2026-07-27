"""
Daily ingestion + classification entry point for market-health.

Run manually or via an external scheduler (Railway cron in production — see
railway.json):
    python ingest.py

For each curated, industry-standard job title tracked per Role Category,
fetches new live Adzuna postings, dedupes by id, stores them in raw_postings.
Classification then runs once across everything newly ingested (not once per
search term) so the title-based dedup cache in classification.py sees the
widest possible pool before spending any LLM call. Every run — including a
failed one — is recorded in ingestion_runs, so its outcome is inspectable
after the fact instead of existing only as console output. See
backend/specs/market-health/api.md — Business Logic.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from adzuna_client import AdzunaFetchError, fetch_postings
from classification import classify_postings
from db import init_schema
from ingestion_runs import record_run
from raw_postings import get_all_unclassified, insert_new_postings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# category=it-jobs covers all three Role Categories (see
# design/market-health/job-classification.md), but it's a coarse, generic
# filter — Adzuna offers no finer-grained category underneath it. Precision
# comes entirely from these search terms, so each one is a specific,
# standard, high-frequency industry title rather than a bare category word
# like "designer" or "engineer" — those were confirmed to pull in a lot of
# irrelevant noise (e.g. "Cabling Infrastructure Designer"), which still
# costs a real classification call to reject as "other".
#
# This list is deliberately curated, not exhaustive, and is expected to be
# reviewed periodically — add a title once it recurs often enough in
# raw_postings to matter, retire one that's gone stale. This is the same
# review process job-classification.md already describes for Raw Title.
ROLE_SEARCH_TERMS: dict[str, list[str]] = {
    "Designer": [
        "UX designer",
        "user experience designer",
        "product designer",
        "UI designer",
    ],
    "Product Manager": [
        "product manager",
        "product owner",
        "technical product manager",
    ],
    "Engineer": [
        "software engineer",
        "software developer",
        "frontend engineer",
        "backend engineer",
        "devops engineer",
    ],
}

MAX_DAYS_OLD = 3  # rolling safety margin, not exactly 1 — tolerates a late/missed run


def ingest_search_term(term: str) -> dict:
    """
    Fetch and store new postings for one search term. Never raises — a term that
    fails after fetch_postings exhausts its own retries is recorded with its error
    rather than propagated, so one bad term can't abort the run. See
    backend/specs/market-health/api.md — Business Logic — Ingestion — Fault
    isolation, per search term.
    """
    try:
        postings = fetch_postings(term, max_days_old=MAX_DAYS_OLD)
    except AdzunaFetchError as exc:
        logger.error("ingest[%s]: failed, skipping this term: %s", term, exc)
        return {"term": term, "fetched": 0, "inserted": 0, "error": str(exc)}

    new_ids = insert_new_postings(term, postings)
    logger.info("ingest[%s]: fetched %d, inserted %d new", term, len(postings), len(new_ids))
    return {"term": term, "fetched": len(postings), "inserted": len(new_ids), "error": None}


async def run() -> None:
    init_schema()
    started_at = datetime.now(timezone.utc)
    terms_processed: list[dict] = []

    try:
        for terms in ROLE_SEARCH_TERMS.values():
            for term in terms:
                terms_processed.append(ingest_search_term(term))

        total_fetched = sum(t["fetched"] for t in terms_processed)
        total_inserted = sum(t["inserted"] for t in terms_processed)
        any_term_failed = any(t["error"] is not None for t in terms_processed)

        unclassified = get_all_unclassified()
        logger.info("classify: %d unclassified postings across all search terms", len(unclassified))
        stats = await classify_postings(unclassified)

    except Exception as exc:
        # Something outside per-term fault isolation went wrong (e.g. the database
        # itself is unreachable) — this run produced nothing usable.
        logger.exception("Ingestion run failed: %s", exc)
        record_run(
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            status="failed",
            terms_processed=terms_processed,
            error_message=str(exc),
        )
        raise

    status = "partial" if (any_term_failed or stats["stopped_early"]) else "success"
    record_run(
        started_at=started_at,
        completed_at=datetime.now(timezone.utc),
        status=status,
        terms_processed=terms_processed,
        total_fetched=total_fetched,
        total_inserted=total_inserted,
        total_classified=stats["total_classified"],
        cache_hits=stats["cache_hits"],
        llm_classified=stats["llm_classified"],
        other_count=stats["other_count"],
    )
    logger.info("ingestion run recorded: status=%s", status)


if __name__ == "__main__":
    asyncio.run(run())
