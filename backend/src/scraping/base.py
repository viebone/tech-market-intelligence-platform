"""
Polite-scraping mechanism — the sibling to sources/base.py (API adapters) and
employment_events/base.py (registry adapters), for sources with no public API
at all. See backend/specs/scraped-data-sources/api.md for the full design.

Deliberately DB-agnostic, same discipline sources/base.py already follows
(PacedFetcher takes an httpx.Client as a parameter rather than owning one) —
PoliteScraper takes cache stores as parameters (RobotsCacheStore,
PageCacheStore protocols) rather than importing db.py directly. The Postgres-
backed implementations live in scraping_storage.py; tests use simple
in-memory fakes instead, so none of the tests in backend/tests/test_scraping.py
need a live database.

**Deviation from the spec's exact wording, disclosed here**: the spec
(Data Models — Part 1) describes a single generic `FetchedScrapedFact`
dataclass with a `value: dict` field. This module instead defines two
concrete dataclasses, `FetchedMarketObservation` and `FetchedSkillAssociation`,
mirroring the two market-benchmark tables exactly — the same pattern
sources/base.py (FetchedPosting) and employment_events/base.py
(FetchedEmploymentEvent) already use: one concrete, typed shape per source
*category*, not a generic value bag. A generic `dict`-valued fact would have
pushed the "which fields exist, which are mandatory" question down into
string-keyed dict access at storage time, exactly what this codebase avoids
everywhere else. The *mandatory-attribution* discipline the spec actually
cares about (source_url/licence/fetched_at can't be omitted) is preserved
identically — it's just enforced on typed dataclasses instead of a dict.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
import urllib.robotparser
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Protocol
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# The token checked against a site's robots.txt rules (RobotFileParser
# matches on this, falling back to its own "*" wildcard rules when no rule
# names this token specifically) — kept short and stable; the full contact
# string travels in the User-Agent header instead (see _build_user_agent).
USER_AGENT_TOKEN = "TechMarketIntelligencePlatform-Scraper"


class ScraperConfigError(Exception):
    """
    Raised at PoliteScraper construction time when SCRAPER_CONTACT is
    missing or looks like a placeholder. Deliberately stricter than
    employment_events/sec_edgar.py's SEC_EDGAR_CONTACT (which falls back to
    a placeholder locally) — this adapter's right to run at all rests on a
    specific, named, conditional permission grant (Business Logic — polite
    scraping rule 5, Tech Decisions), not a general fair-access courtesy to
    an anonymous public API. See research/2026-09-16-itjobswatch-scraping-permission.md.
    """


class RobotsDisallowedError(Exception):
    """
    Raised when robots.txt disallows the requested URL for this scraper.
    Callers must treat this as "skip this page, log it, move on" — never a
    reason to override or ignore it (Business Logic — polite scraping rule
    2). Never caught-and-retried; disallowed is disallowed.
    """


class ScrapeFetchError(Exception):
    """
    A request failed and wasn't retryable, or was still failing after
    exhausting retries — the scraping-side counterpart to
    sources.base.SourceFetchError. One page failing should never abort an
    adapter's whole run (Business Logic — polite scraping rule 7); callers
    are expected to catch this per-page/per-entity, not let it propagate.
    """


def _looks_like_placeholder(contact: str) -> bool:
    """
    Heuristic check for an unset-in-spirit SCRAPER_CONTACT — an empty
    string, or a value that's obviously copy-pasted from documentation
    rather than a real contact (matches the same "example.com" / "set
    SCRAPER_CONTACT" markers backend/.env.example uses for this var).
    """
    if not contact or not contact.strip():
        return True
    lowered = contact.strip().lower()
    return "example.com" in lowered or "set scraper_contact" in lowered


def _build_user_agent(contact: str) -> str:
    return f"{USER_AGENT_TOKEN}/1.0 (+{contact})"


# ---------------------------------------------------------------------------
# Cache store protocols — Postgres-backed implementations in
# scraping_storage.py; tests use simple in-memory fakes (see
# backend/tests/test_scraping.py) so PoliteScraper itself never touches a
# database directly.
# ---------------------------------------------------------------------------

@dataclass
class RobotsCacheEntry:
    raw_body: str | None
    fetched_at: datetime
    http_status: int


class RobotsCacheStore(Protocol):
    def get(self, host: str) -> RobotsCacheEntry | None: ...
    def set(self, host: str, raw_body: str | None, http_status: int, fetched_at: datetime) -> None: ...


@dataclass
class PageCacheEntry:
    raw_body: str
    content_hash: str
    etag: str | None
    last_modified: str | None
    fetched_at: datetime
    http_status: int


class PageCacheStore(Protocol):
    def get(self, url: str) -> PageCacheEntry | None: ...

    def set(
        self, url: str, source: str, raw_body: str, content_hash: str,
        etag: str | None, last_modified: str | None, fetched_at: datetime, http_status: int,
    ) -> None: ...

    def touch(self, url: str, fetched_at: datetime) -> None:
        """A 304 response confirms the page is unchanged — update only
        fetched_at, never overwrite raw_body (Business Logic rule 4)."""
        ...


@dataclass
class PageFetchResult:
    raw_body: str
    from_cache: bool  # True if served from PageCacheStore with no network call at all


# ---------------------------------------------------------------------------
# PoliteScraper — the mechanical engine. Every rule from the spec's Business
# Logic — "Polite scraping — the mechanical rules" section is enforced here,
# in code, not left as a comment for each adapter to reimplement.
# ---------------------------------------------------------------------------

class PoliteScraper:
    def __init__(
        self,
        source_name: str,
        robots_store: RobotsCacheStore,
        page_store: PageCacheStore,
        min_interval_seconds: float = 3.0,       # Tech Decisions — higher floor than PacedFetcher's 1.0s
        min_refetch_interval_hours: float = 24.0,  # Tech Decisions — page cache freshness window
        robots_cache_ttl_hours: float = 24.0,
        max_retries: int = 3,
        backoff_base_seconds: float = 2.0,
        contact_env_var: str = "SCRAPER_CONTACT",
    ) -> None:
        contact = os.environ.get(contact_env_var, "")
        if _looks_like_placeholder(contact):
            raise ScraperConfigError(
                f"{contact_env_var} is unset or looks like a placeholder — refusing to run. "
                f"This adapter's permission to scrape {source_name!r} was granted on the "
                f"condition of real, honest identification (see "
                f"research/2026-09-16-itjobswatch-scraping-permission.md); running with no "
                f"real contact would itself violate that condition. Set {contact_env_var} to "
                f"a real 'Your Org Name your-real-email@example.org' string before running this."
            )
        self._source_name = source_name
        self._contact = contact
        self._user_agent = _build_user_agent(contact)
        self._robots_store = robots_store
        self._page_store = page_store
        self._min_interval = min_interval_seconds
        self._min_refetch_interval = timedelta(hours=min_refetch_interval_hours)
        self._robots_cache_ttl = timedelta(hours=robots_cache_ttl_hours)
        self._max_retries = max_retries
        self._backoff_base = backoff_base_seconds
        self._last_request_at: float | None = None
        self._robots_parsers: dict[str, urllib.robotparser.RobotFileParser] = {}

    @property
    def user_agent(self) -> str:
        return self._user_agent

    def _pace(self) -> None:
        if self._last_request_at is not None:
            wait = self._min_interval - (time.monotonic() - self._last_request_at)
            if wait > 0:
                time.sleep(wait)
        self._last_request_at = time.monotonic()

    def _robots_url(self, url: str) -> tuple[str, str]:
        parsed = urlparse(url)
        host = parsed.netloc
        robots_url = f"{parsed.scheme}://{host}/robots.txt"
        return host, robots_url

    def _ensure_robots_loaded(self, client: httpx.Client, host: str, robots_url: str) -> None:
        """
        Loads this host's robots.txt into an in-memory RobotFileParser,
        fetching (paced) and caching it if there's no cached copy or the
        cached copy is stale (Business Logic rule 1). A 404 on /robots.txt
        means "no restrictions stated" — treated as an empty ruleset, not
        an error (matches this codebase's "absence of a stated limit isn't
        a licence to skip checking" discipline elsewhere).
        """
        cached = self._robots_store.get(host)
        now = datetime.now(timezone.utc)
        if cached is not None and (now - cached.fetched_at) < self._robots_cache_ttl:
            raw_body = cached.raw_body
        else:
            self._pace()
            try:
                response = client.get(robots_url, headers={"User-Agent": self._user_agent})
                raw_body = response.text if response.status_code == 200 else None
                status = response.status_code
            except httpx.TransportError as exc:
                logger.warning(
                    "%s: robots.txt fetch failed for %s (%s) — treating as no stated "
                    "restrictions this run, will retry next run", self._source_name, host, exc,
                )
                raw_body, status = None, 0
            self._robots_store.set(host, raw_body, status, now)

        parser = urllib.robotparser.RobotFileParser()
        if raw_body:
            parser.parse(raw_body.splitlines())
        else:
            parser.parse([])  # no rules at all — everything allowed
        self._robots_parsers[host] = parser

    def _check_robots(self, client: httpx.Client, url: str) -> None:
        host, robots_url = self._robots_url(url)
        if host not in self._robots_parsers:
            self._ensure_robots_loaded(client, host, robots_url)
        parser = self._robots_parsers[host]
        if not parser.can_fetch(USER_AGENT_TOKEN, url):
            raise RobotsDisallowedError(f"robots.txt disallows fetching {url} for {USER_AGENT_TOKEN}")

    def get(self, client: httpx.Client, url: str) -> PageFetchResult:
        """
        The one entry point every adapter built on PoliteScraper should call
        for every page. Enforces, in order: robots.txt compliance (rule 1-2),
        cache-before-network (rule 4), pacing (rule 3), identification
        (rule 5 — enforced at construction, applied here via the User-Agent
        header on every request). Raises RobotsDisallowedError if disallowed
        — callers must catch this per-page (rule 7, fault isolation) and
        never retry it. Raises ScrapeFetchError on an unretryable or
        exhausted-retries network failure.
        """
        self._check_robots(client, url)

        cached = self._page_store.get(url)
        now = datetime.now(timezone.utc)
        if cached is not None and (now - cached.fetched_at) < self._min_refetch_interval:
            # Rule 4 — fresh enough, no network call at all, not even conditional.
            return PageFetchResult(raw_body=cached.raw_body, from_cache=True)

        headers = {"User-Agent": self._user_agent}
        if cached is not None:
            if cached.etag:
                headers["If-None-Match"] = cached.etag
            if cached.last_modified:
                headers["If-Modified-Since"] = cached.last_modified

        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            self._pace()
            try:
                response = client.get(url, headers=headers)
                if response.status_code == 304 and cached is not None:
                    self._page_store.touch(url, now)
                    return PageFetchResult(raw_body=cached.raw_body, from_cache=True)
                response.raise_for_status()
                raw_body = response.text
                content_hash = hashlib.sha256(raw_body.encode("utf-8")).hexdigest()
                self._page_store.set(
                    url, self._source_name, raw_body, content_hash,
                    response.headers.get("ETag"), response.headers.get("Last-Modified"),
                    now, response.status_code,
                )
                return PageFetchResult(raw_body=raw_body, from_cache=False)
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status not in RETRYABLE_STATUS_CODES:
                    raise ScrapeFetchError(
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

        raise ScrapeFetchError(
            f"{self._source_name} request failed after {self._max_retries} attempts: {last_exc}"
        ) from last_exc


# ---------------------------------------------------------------------------
# Output shapes — the market-benchmark category's two tables (Data Models —
# Part 2). Source-agnostic: a future second benchmark adapter reuses these
# same two dataclasses, with a different `source` value at storage time.
# ---------------------------------------------------------------------------

@dataclass
class FetchedMarketObservation:
    """One market_observations row, before storage. Mandatory fields (no
    default) first, per dataclass field-ordering rules — this is what makes
    "attribution can't be omitted" a real, enforced-by-construction rule
    rather than a comment: omitting source_url/licence/fetched_at raises
    TypeError immediately, the same way omitting entity_type would."""
    entity_type: str          # "role" | "skill" | "technology" | "capability"
    entity_name: str
    employment_type: str      # "permanent" | "contract"
    location: str
    period_start: date
    period_end: date
    source_url: str
    licence: str
    licence_confirmed: bool   # captured at scrape time — see source_licences.py's SourceLicence
    fetched_at: datetime
    rank: int | None = None
    rank_yoy_change: int | None = None
    vacancy_count: int | None = None
    vacancy_share: float | None = None
    live_jobs: int | None = None
    salary_sample_size: int | None = None
    salary_p10: float | None = None
    salary_p25: float | None = None
    salary_median: float | None = None
    salary_p75: float | None = None
    salary_p90: float | None = None
    salary_unit: str | None = None       # "GBP/year" | "GBP/day" — see spec, never inferred silently
    salary_yoy_change: float | None = None
    taxonomy_match: str | None = None    # reserved — reconciliation deferred, see spec
    raw_response: dict = field(default_factory=dict)


@dataclass
class FetchedSkillAssociation:
    """One skill_associations row, before storage. Same mandatory-fields-
    first shape as FetchedMarketObservation."""
    role_name: str
    skill_name: str
    period_start: date
    period_end: date
    source_url: str
    licence: str
    licence_confirmed: bool
    fetched_at: datetime
    job_count: int | None = None
    percentage: float | None = None
    rank: int | None = None
    role_taxonomy_match: str | None = None
    skill_taxonomy_match: str | None = None
    raw_response: dict = field(default_factory=dict)


@dataclass
class ScrapeResult:
    """What one adapter's fetch() returns — either list may be empty for an
    adapter that only produces one of the two shapes."""
    market_observations: list[FetchedMarketObservation] = field(default_factory=list)
    skill_associations: list[FetchedSkillAssociation] = field(default_factory=list)


class ScrapedSourceAdapter(Protocol):
    """
    Protocol every scraped market-benchmark adapter implements. Each adapter
    lives in scraping/{name}.py. To add a new source, create a class
    implementing this protocol and register it in
    scraping/__init__.py's ALL_SCRAPED_SOURCE_ADAPTERS — nothing else
    changes (ingest_scraped_sources.py, scraping_storage.py, and the schema
    are all source-agnostic).
    """

    name: str  # "itjobswatch"

    def fetch(self) -> ScrapeResult:
        """
        Fetch this source's currently available observations. Never raises
        for a single page/entity's failure to parse — logged and skipped
        (Business Logic rule 7); only a whole-adapter-level failure
        propagates, for orchestration to catch without aborting other
        registered adapters.
        """
        ...
