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
import time

import httpx

logger = logging.getLogger(__name__)

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/gb/search"
RESULTS_PER_PAGE = 50
MAX_PAGES = 60  # safety cap (3000 postings) so a runaway query can't paginate forever

# Adzuna's default quota (their Terms of Service): 25 hits/minute, 250/day, 1000/week,
# 2500/month. Pacing every request at this interval caps sustained throughput at
# 20/minute — safely under the per-minute limit no matter how many pages a term
# needs or how many terms run back-to-back — and stays well under the daily/weekly/
# monthly caps too at this pipeline's actual volume. See backend/specs/market-health/
# api.md — Business Logic — Ingestion — Adzuna rate limits.
MIN_REQUEST_INTERVAL_SECONDS = 3.0

MAX_RETRIES = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
BACKOFF_BASE_SECONDS = 2.0  # 2s, 4s, 8s

_last_request_at: float | None = None


class AdzunaFetchError(Exception):
    """
    A request to Adzuna failed and either wasn't retryable (a non-429 4xx) or was
    still failing after MAX_RETRIES. Callers should treat this as that one term's
    failure, not a reason to abort the whole ingestion run — see
    backend/specs/market-health/api.md — Business Logic — Ingestion — Fault
    isolation, per search term.
    """


def _pace() -> None:
    """
    Block until at least MIN_REQUEST_INTERVAL_SECONDS has passed since the last
    Adzuna request. Called from one place (`_get_with_retry`) so every request —
    each pagination page within a term, and the transition between terms — is
    naturally paced regardless of how the caller loops.
    """
    global _last_request_at
    if _last_request_at is not None:
        wait = MIN_REQUEST_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
    _last_request_at = time.monotonic()


def _get_with_retry(client: httpx.Client, url: str, params: dict) -> httpx.Response:
    """
    GET with pacing and retry-with-backoff on transient failures (HTTP 429/5xx,
    connection errors/timeouts). A non-429 4xx fails immediately — retrying a
    malformed request can't succeed and would just spend quota.
    """
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        _pace()
        try:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status not in RETRYABLE_STATUS_CODES:
                raise AdzunaFetchError(
                    f"Adzuna request failed (status {status}, not retryable): {exc}"
                ) from exc
            last_exc = exc
        except httpx.TransportError as exc:
            # Connection error / timeout — transient, treated the same as a 5xx.
            last_exc = exc

        if attempt < MAX_RETRIES:
            wait = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "Adzuna request failed (attempt %d/%d), retrying in %.0fs: %s",
                attempt, MAX_RETRIES, wait, last_exc,
            )
            time.sleep(wait)

    raise AdzunaFetchError(
        f"Adzuna request failed after {MAX_RETRIES} attempts: {last_exc}"
    ) from last_exc


def fetch_postings(what_phrase: str, max_days_old: int = 3) -> list[dict]:
    """
    Fetch all live postings matching `what_phrase` under category=it-jobs,
    within the last `max_days_old` days. Paginates until Adzuna returns fewer
    than a full page or MAX_PAGES is reached.

    Returns raw Adzuna posting dicts, each with an "id" field. An empty list is a
    normal, successful result — Adzuna having nothing new for a term is not an error.

    Raises AdzunaFetchError if a request is still failing after retrying transient
    failures — callers should treat that as this one term's failure, not a reason
    to crash the whole run.
    """
    app_id = os.environ["ADZUNA_APP_ID"]
    app_key = os.environ["ADZUNA_APP_KEY"]

    postings: list[dict] = []
    with httpx.Client(timeout=30.0) as client:
        for page in range(1, MAX_PAGES + 1):
            response = _get_with_retry(
                client,
                f"{ADZUNA_BASE_URL}/{page}",
                {
                    "app_id": app_id,
                    "app_key": app_key,
                    "what_phrase": what_phrase,
                    "category": "it-jobs",
                    "max_days_old": max_days_old,
                    "results_per_page": RESULTS_PER_PAGE,
                    "content-type": "application/json",
                },
            )
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
