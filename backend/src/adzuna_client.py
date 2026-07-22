"""
Adzuna Jobs API (UK) client — source of live postings for raw_postings.

Query shape (`what_phrase=<term>&category=it-jobs`) validated empirically in
research/2026-07-16-adzuna-live-data-and-classification-taxonomy.md: it-jobs is
the correct category filter for Designer, Product Manager, and Engineer postings
alike. See design/market-health/job-classification.md for why the earlier
creative-design-jobs guess for Designer postings was rejected.
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/gb/search"
RESULTS_PER_PAGE = 50
MAX_PAGES = 60  # safety cap (3000 postings) so a runaway query can't paginate forever


def fetch_postings(what_phrase: str, max_days_old: int = 3) -> list[dict]:
    """
    Fetch all live postings matching `what_phrase` under category=it-jobs,
    within the last `max_days_old` days. Paginates until Adzuna returns fewer
    than a full page or MAX_PAGES is reached.

    Returns raw Adzuna posting dicts, each with an "id" field.
    """
    app_id = os.environ["ADZUNA_APP_ID"]
    app_key = os.environ["ADZUNA_APP_KEY"]

    postings: list[dict] = []
    with httpx.Client(timeout=30.0) as client:
        for page in range(1, MAX_PAGES + 1):
            response = client.get(
                f"{ADZUNA_BASE_URL}/{page}",
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "what_phrase": what_phrase,
                    "category": "it-jobs",
                    "max_days_old": max_days_old,
                    "results_per_page": RESULTS_PER_PAGE,
                    "content-type": "application/json",
                },
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            postings.extend(results)
            if len(results) < RESULTS_PER_PAGE:
                break
        else:
            logger.warning(
                "fetch_postings(%r): hit MAX_PAGES=%d (%d postings) — more results may "
                "exist and were not fetched this run.",
                what_phrase, MAX_PAGES, len(postings),
            )

    return postings
