"""
Source adapter abstraction for job-posting ingestion.

Mirrors llm/base.py's LLMProvider pattern, applied to job-data sources
instead of AI providers: no business logic (ingestion orchestration,
classification, trend aggregation) needs to know or care which source
produced a given row. See backend/specs/market-health/api.md — Tech
Decisions — Source adapter abstraction.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@dataclass
class FetchedPosting:
    """One posting as returned by a source adapter, before storage."""
    source_ref: str    # unique within this source, e.g. "acme-corp/123456"
    company: str        # the board token / site / job-board name fetched
    title: str
    raw_response: dict  # the source's own job-object shape, verbatim
    # Added 2026-08-04 — all optional, populated per-adapter on a best-effort
    # basis (backend/specs/market-health/api.md — Business Logic — Location
    # normalization, Compensation extraction). None means "couldn't be
    # normalized," never a guess.
    country: str | None = None          # normalized ISO-2 code, e.g. "US"
    city: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    salary_confidence: str | None = None        # "structured" | "parsed" | None
    salary_extraction_method: str | None = None  # e.g. "ashby-structured", "lever-regex"


# Normalizes free-text country names (Ashby's addressCountry, Greenhouse's
# parsed office location) to the same ISO-2 codes Lever already provides
# natively — so `country` is comparable across all three sources instead of
# "US" vs "United States" vs "USA" fragmenting the same country into three
# group_by buckets. Curated from the country names actually observed in
# production data (2026-08-04), not exhaustive — an unmapped name resolves to
# None (excluded from location-specific answers) rather than being guessed at
# or passed through unnormalized.
COUNTRY_NAME_TO_ISO2 = {
    "united states": "US", "usa": "US", "us": "US",
    "united kingdom": "GB", "uk": "GB",
    "canada": "CA",
    "singapore": "SG",
    "japan": "JP",
    "india": "IN",
    "ireland": "IE",
    "germany": "DE",
    "mexico": "MX",
    "australia": "AU",
    "sweden": "SE",
    "spain": "ES",
    "france": "FR",
    "south korea": "KR",
    "poland": "PL",
    "netherlands": "NL",
    "united arab emirates": "AE",
    "denmark": "DK",
    "lithuania": "LT",
    "israel": "IL",
}


def normalize_country(raw: str | None) -> str | None:
    """
    Map a free-text country name to its ISO-2 code. Returns None for empty,
    already-2-letter (assumed already-ISO), or unrecognized input — an
    unnormalizable value is excluded from location answers, never guessed.
    """
    if not raw:
        return None
    cleaned = raw.strip()
    if len(cleaned) == 2:
        return cleaned.upper()
    return COUNTRY_NAME_TO_ISO2.get(cleaned.lower())


class SourceFetchError(Exception):
    """
    A request to a source's API failed and either wasn't retryable (a
    non-429 4xx) or was still failing after exhausting retries. Callers
    should treat this as that one company's failure, not a reason to abort
    the whole ingestion run or the rest of this adapter's company list — see
    backend/specs/market-health/api.md — Business Logic — Ingestion — Fault
    isolation, per company.
    """


class SourceAdapter(Protocol):
    """
    Protocol all job-data source adapters must implement. Each adapter lives
    in sources/{name}.py. To add a new source, create a class implementing
    this protocol — nothing else changes (ingest.py, raw_postings.py, and
    classification.py are all source-agnostic).
    """

    name: str              # "greenhouse" | "lever" | "ashby"
    companies: list[str]   # curated list of board tokens / sites / job-board names

    def fetch_company(self, company: str) -> list[FetchedPosting]:
        """
        Fetch one company's published postings. An empty list is a normal,
        successful result — a company having no open roles on a given day is
        expected, not exceptional. Raises SourceFetchError if the request is
        still failing after retrying transient failures.
        """
        ...


class PacedFetcher:
    """
    Shared GET-with-pacing-and-retry helper. None of Greenhouse, Lever, or
    Ashby documents a hard rate limit for their public GET job-board
    endpoints (confirmed against each platform's own docs, 2026-08-03) —
    pacing here is self-imposed good-API-citizenship, not compliance with a
    documented quota. One instance per adapter, holding that adapter's own
    pacing clock — one source's pacing must never throttle against another
    source's requests.
    """

    def __init__(
        self,
        source_name: str,
        min_interval_seconds: float = 1.0,
        max_retries: int = 3,
        backoff_base_seconds: float = 2.0,
    ) -> None:
        self._source_name = source_name
        self._min_interval = min_interval_seconds
        self._max_retries = max_retries
        self._backoff_base = backoff_base_seconds
        self._last_request_at: float | None = None

    def _pace(self) -> None:
        if self._last_request_at is not None:
            wait = self._min_interval - (time.monotonic() - self._last_request_at)
            if wait > 0:
                time.sleep(wait)
        self._last_request_at = time.monotonic()

    def get(self, client: httpx.Client, url: str, params: dict | None = None) -> httpx.Response:
        """
        GET with pacing and retry-with-backoff on transient failures (HTTP
        429/5xx, connection errors/timeouts). A non-429 4xx fails
        immediately — retrying a malformed request or an unknown company
        can't succeed.
        """
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            self._pace()
            try:
                response = client.get(url, params=params)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status not in RETRYABLE_STATUS_CODES:
                    raise SourceFetchError(
                        f"{self._source_name} request failed (status {status}, not retryable): {exc}"
                    ) from exc
                last_exc = exc
            except httpx.TransportError as exc:
                last_exc = exc

            if attempt < self._max_retries:
                wait = self._backoff_base * (2 ** (attempt - 1))
                logger.warning(
                    "%s request failed (attempt %d/%d), retrying in %.0fs: %s",
                    self._source_name, attempt, self._max_retries, wait, last_exc,
                )
                time.sleep(wait)

        raise SourceFetchError(
            f"{self._source_name} request failed after {self._max_retries} attempts: {last_exc}"
        ) from last_exc
