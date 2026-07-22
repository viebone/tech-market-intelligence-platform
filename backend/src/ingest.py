"""
Daily ingestion + classification entry point for market-health.

Run manually or via an external scheduler (cron, etc.):
    python ingest.py

For each curated, industry-standard job title tracked per Role Category,
fetches new live Adzuna postings, dedupes by id, stores them in raw_postings.
Classification then runs once across everything newly ingested (not once per
search term) so the title-based dedup cache in classification.py sees the
widest possible pool before spending any LLM call. See
backend/specs/market-health/api.md — Business Logic.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from adzuna_client import fetch_postings
from classification import classify_postings
from db import init_schema
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


def ingest_search_term(term: str) -> None:
    postings = fetch_postings(term, max_days_old=MAX_DAYS_OLD)
    new_ids = insert_new_postings(term, postings)
    logger.info("ingest[%s]: fetched %d, inserted %d new", term, len(postings), len(new_ids))


async def run() -> None:
    init_schema()

    for terms in ROLE_SEARCH_TERMS.values():
        for term in terms:
            ingest_search_term(term)

    unclassified = get_all_unclassified()
    logger.info("classify: %d unclassified postings across all search terms", len(unclassified))
    await classify_postings(unclassified)


if __name__ == "__main__":
    asyncio.run(run())
