"""
Trusted external statistics — the standardised edge.

The adapter interface, the shared value types, and the polite fetcher every publisher's adapter
uses. DB-agnostic on purpose (same discipline as sources/base.py and scraping/base.py): the
orchestrator (`ingest_adapter`, below) takes a `storage` object, and tests pass an in-memory fake, so
none of the trusted-statistics tests need a live database.

Spec: backend/specs/trusted-statistics/api.md. Standard: backend/TRUSTED_STATISTICS.md.

An adapter does three things and nothing else — `discover` (which releases exist), `parse` (a PURE
function of the file's bytes), `validate` (is this release internally consistent). It never touches
storage or licences: the orchestrator owns cadence, download, hashing, the validation gate, licence
stamping, vintage-aware storage and run logging, so those rules cannot drift per publisher.
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

from scraping.base import _looks_like_placeholder  # one identification rule for every polite fetcher

logger = logging.getLogger(__name__)

USER_AGENT_TOKEN = "TechMarketIntelligencePlatform-Statistics"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024

VALUE_STATUSES = ("provisional", "final", "revised", "unknown")
SEASONAL = ("seasonally_adjusted", "not_adjusted", "unknown")


class StatisticsConfigError(Exception):
    """STATISTICS_CONTACT is unset or a placeholder — refuse to run (same stance as SCRAPER_CONTACT)."""


class StatisticsFetchError(Exception):
    """A request failed and was not retryable, or kept failing after retries."""


class LayoutError(Exception):
    """The file is not laid out the way the adapter expects. The release is REJECTED, never guessed at."""


# ── value types ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ReleaseRef:
    dataset_code: str
    release_date: date            # the publisher's own release date
    release_uri: str              # addressable release, e.g. .../current or .../previous/v128
    file_url: str
    file_name: str


@dataclass(frozen=True)
class SeriesDefinition:
    series_code: str
    dataset_code: str
    title: str
    measure: str
    unit: str
    unit_scale: int
    seasonal_adjustment: str
    period_type: str
    frequency: str
    dimensions: dict
    dimension_type: str
    definition_note: str
    coverage_note: str
    designation: str
    methodology_url: str
    source_page_url: str


@dataclass(frozen=True)
class FetchedStatistic:
    series_code: str
    period_start: date
    period_end: date
    period_label: str             # the publisher's own words, e.g. "Jun-Aug 2026"
    value: float                  # as published (thousands for ONS levels) — never derived
    value_status: str             # provisional | final | revised | unknown, from the file's own flag
    raw_cell: str                 # verbatim value + flag, for audit

    def __post_init__(self) -> None:
        if self.value_status not in VALUE_STATUSES:
            raise ValueError(f"value_status must be one of {VALUE_STATUSES}, got {self.value_status!r}")
        if self.period_end < self.period_start:
            raise ValueError("period_end before period_start")


@dataclass
class ParsedRelease:
    dataset_code: str
    series: list[SeriesDefinition]
    observations: list[FetchedStatistic]


class StatisticsAdapter(Protocol):
    source: str                                        # key in TRUSTED_PUBLISHERS and SOURCE_LICENCES

    def discover(self, fetcher: "PoliteFetcher") -> list[ReleaseRef]: ...
    def parse(self, ref: ReleaseRef, file_bytes: bytes) -> ParsedRelease: ...
    def validate(self, parsed: ParsedRelease) -> list[str]: ...
    # optional: validate_set(self, parsed: list[ParsedRelease]) -> list[str]  (cross-file checks)


# ── cadence (pure, unit-testable) ─────────────────────────────────────────────

def is_due_from_last_run(last_run_at: datetime | None, min_interval_hours: float, now: datetime) -> bool:
    if last_run_at is None:
        return True
    return (now - last_run_at) >= timedelta(hours=min_interval_hours)


# ── the polite fetcher ────────────────────────────────────────────────────────

class PoliteFetcher:
    """
    Identification, pacing, robots.txt, retries. Every request to a publisher goes through this.

    - `STATISTICS_CONTACT` must be a real contact — refuses to construct otherwise (this category has
      no scraping-style permission grant, but a public statistics publisher that states no access
      policy is owed honest identification all the same).
    - >= `min_interval_seconds` between any two requests (default 3 s).
    - robots.txt fetched once per host per run and honoured; a 404 (or an unreachable robots.txt) means
      "no restrictions stated" — RFC 9309; ONS publishes none.
    - retries only on transient statuses, with exponential backoff.
    """

    def __init__(
        self,
        source_name: str,
        min_interval_seconds: float = 3.0,
        max_retries: int = 3,
        backoff_base_seconds: float = 2.0,
        contact_env_var: str = "STATISTICS_CONTACT",
        client: httpx.Client | None = None,
    ) -> None:
        contact = os.environ.get(contact_env_var, "")
        # scraping.base's check recognises 'example.com' and its own 'set SCRAPER_CONTACT' marker; add this variable's.
        if _looks_like_placeholder(contact) or "set statistics_contact" in contact.lower():
            raise StatisticsConfigError(
                f"{contact_env_var} is unset or looks like a placeholder — refusing to run. Statistics "
                f"publishers get honest identification on every request: set {contact_env_var} to a real "
                f"'Your Org Name your-real-email@example.org' string."
            )
        self._source_name = source_name
        self._user_agent = f"{USER_AGENT_TOKEN}/1.0 (+{contact})"
        self._min_interval = min_interval_seconds
        self._max_retries = max_retries
        self._backoff_base = backoff_base_seconds
        self._client = client or httpx.Client(timeout=60.0, follow_redirects=True)
        self._last_request_at: float | None = None
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}

    @property
    def user_agent(self) -> str:
        return self._user_agent

    def _pace(self) -> None:
        if self._last_request_at is not None:
            wait = self._min_interval - (time.monotonic() - self._last_request_at)
            if wait > 0:
                time.sleep(wait)
        self._last_request_at = time.monotonic()

    def _check_robots(self, url: str) -> None:
        parsed = urlparse(url)
        host = parsed.netloc
        if host not in self._robots:
            self._pace()
            body = None
            try:
                r = self._client.get(f"{parsed.scheme}://{host}/robots.txt", headers={"User-Agent": self._user_agent})
                # Only a plain-text 200 counts as a robots file; a 404 — including an HTML "page not found"
                # served with 200 by some sites — states no restrictions.
                ctype = r.headers.get("content-type", "")
                if r.status_code == 200 and "html" not in ctype.lower():
                    body = r.text
            except httpx.TransportError as exc:
                logger.warning("%s: robots.txt fetch failed for %s (%s) — treating as no stated restrictions", self._source_name, host, exc)
            parser = urllib.robotparser.RobotFileParser()
            parser.parse(body.splitlines() if body else [])
            self._robots[host] = parser
        if not self._robots[host].can_fetch(USER_AGENT_TOKEN, url):
            raise StatisticsFetchError(f"robots.txt disallows {url} for {USER_AGENT_TOKEN}")

    def _get(self, url: str) -> httpx.Response:
        self._check_robots(url)
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            self._pace()
            try:
                r = self._client.get(url, headers={"User-Agent": self._user_agent})
            except httpx.TransportError as exc:
                last_exc = exc
            else:
                if r.status_code == 200:
                    return r
                if r.status_code not in RETRYABLE_STATUS_CODES:
                    raise StatisticsFetchError(f"{url} -> HTTP {r.status_code}")
                last_exc = StatisticsFetchError(f"{url} -> HTTP {r.status_code}")
            if attempt < self._max_retries:
                time.sleep(self._backoff_base * (2 ** attempt))
        raise StatisticsFetchError(f"{url} failed after {self._max_retries + 1} attempts: {last_exc}")

    def get_json(self, url: str) -> dict:
        r = self._get(url)
        try:
            return r.json()
        except ValueError as exc:
            raise StatisticsFetchError(f"{url} did not return JSON") from exc

    def get_bytes(self, url: str) -> bytes:
        r = self._get(url)
        if len(r.content) > MAX_DOWNLOAD_BYTES:
            raise StatisticsFetchError(f"{url} is {len(r.content)} bytes; refusing anything over {MAX_DOWNLOAD_BYTES}")
        return r.content


# ── the orchestrator ──────────────────────────────────────────────────────────

class StatisticsStorage(Protocol):
    """What the orchestrator needs from storage — statistics_storage.py implements it on Postgres; tests use a fake."""
    def get_last_run_at(self, source: str) -> datetime | None: ...
    def release_ingested(self, source: str, dataset_code: str, release_date: date) -> bool: ...
    def release_hash_seen(self, source: str, dataset_code: str, content_hash: str) -> bool: ...
    def store_release(self, *, source: str, ref: ReleaseRef, content_hash: str, parsed: ParsedRelease,
                      licence: dict, fetched_at: datetime) -> dict: ...
    def record_release_only(self, *, source: str, ref: ReleaseRef, content_hash: str | None,
                            status: str, summary: str, fetched_at: datetime) -> None: ...
    def record_run(self, *, source: str, ran_at: datetime, outcome: str, release_id: str | None, message: str) -> None: ...


@dataclass
class IngestResult:
    source: str
    outcome: str = "no_new_release"
    messages: list[str] = field(default_factory=list)
    stored: list[dict] = field(default_factory=list)


def ingest_adapter(adapter, storage: StatisticsStorage, fetcher_factory, *, now: datetime | None = None,
                   force: bool = False) -> IngestResult:
    """
    One publisher, one run. Enforces, in order, everything the spec's Business Logic §1 lists:
    cadence gate BEFORE any request; registry + licence checks; discover; new-only; download +
    hash; parse; validate (a failure rejects the whole release — nothing stored); cross-file checks;
    licence stamping; vintage-aware storage; run log. One publisher failing never raises out of here.

    `fetcher_factory` is called only after the cadence gate passes, so a run that is not due makes no
    network request and constructs nothing (and needs no STATISTICS_CONTACT).
    """
    from source_licences import get_licence
    from trusted_stats.registry import TRUSTED_PUBLISHERS

    now = now or datetime.now(timezone.utc)
    result = IngestResult(source=adapter.source)

    publisher = TRUSTED_PUBLISHERS.get(adapter.source)
    if publisher is None:
        raise KeyError(f"{adapter.source!r} has no TRUSTED_PUBLISHERS entry — register it (trust bar) before ingesting")
    licence = get_licence(adapter.source)            # raises LicenceNotRegisteredError — a hard error, by design

    if not force and not is_due_from_last_run(storage.get_last_run_at(adapter.source), publisher.min_check_interval_hours, now):
        result.outcome = "skipped_not_due"
        result.messages.append(f"{adapter.source}: checked within the last {publisher.min_check_interval_hours}h — skipped, no request made")
        logger.info(result.messages[-1])
        return result

    if licence.rejected:
        logger.warning("%s: licence marked rejected — collection continues (never gated), but do not surface this data", adapter.source)
    elif not licence.confirmed:
        logger.warning("%s: storing data under an UNCONFIRMED licence (%r) — do not surface, display or republish it until "
                       "SOURCE_LICENCES[%r].confirmed is True", adapter.source, licence.licence, adapter.source)
        result.messages.append("WARNING: licence not confirmed")

    licence_snapshot = {"licence": licence.licence, "licence_confirmed": licence.confirmed, "attribution_text": licence.attribution_text}

    # A missing/placeholder STATISTICS_CONTACT is a CONFIGURATION error, not a failed run: it propagates (the script
    # reports it) and records nothing — otherwise it would start the cadence clock and block a real run for 24h
    # after the operator fixes it (found by the first live run, 2026-09-25).
    fetcher = fetcher_factory()
    try:
        refs = adapter.discover(fetcher)
    except (StatisticsFetchError, LayoutError) as exc:
        result.outcome = "failed"
        result.messages.append(f"discover failed: {exc}")
        storage.record_run(source=adapter.source, ran_at=now, outcome="failed", release_id=None, message=result.messages[-1])
        logger.error("%s: %s", adapter.source, result.messages[-1])
        return result

    # Settle rule: a release is only ingested once it is `release_settle_days` old (PM, 2026-09-25 — "in case there are issues on
    # their side"). Enforced HERE, from the publisher's own release date, so it does not depend on when the scheduler fires.
    settle_cutoff = now.date() - timedelta(days=publisher.release_settle_days)
    settling = [r for r in refs if r.release_date > settle_cutoff]
    refs = [r for r in refs if r.release_date <= settle_cutoff]
    for r in settling:
        result.messages.append(f"{r.dataset_code} {r.release_date}: released too recently — waits {publisher.release_settle_days} day(s), "
                               f"eligible from {r.release_date + timedelta(days=publisher.release_settle_days)}")
        logger.info("%s: %s", adapter.source, result.messages[-1])

    pending: list[tuple[ReleaseRef, str, ParsedRelease]] = []
    outcomes: list[str] = []
    for ref in refs:
        if storage.release_ingested(adapter.source, ref.dataset_code, ref.release_date):
            outcomes.append("no_new_release")
            continue
        content_hash, parsed = None, None
        try:
            data = fetcher.get_bytes(ref.file_url)
            content_hash = hashlib.sha256(data).hexdigest()
            if storage.release_hash_seen(adapter.source, ref.dataset_code, content_hash):
                # The publisher re-stamped a byte-identical file: record the release, ingest nothing new.
                storage.record_release_only(source=adapter.source, ref=ref, content_hash=content_hash, status="ingested",
                                            summary="identical file (content hash) already ingested under an earlier release",
                                            fetched_at=now)
                outcomes.append("no_new_release")
                result.messages.append(f"{ref.dataset_code} {ref.release_date}: identical file already ingested — nothing new")
                continue
            parsed = adapter.parse(ref, data)
            failures = adapter.validate(parsed)
        except (StatisticsFetchError, LayoutError, ValueError) as exc:
            failures = [f"{type(exc).__name__}: {exc}"]
        if failures:
            summary = "; ".join(failures)
            storage.record_release_only(source=adapter.source, ref=ref, content_hash=content_hash,
                                            status="rejected_validation", summary=summary, fetched_at=now)
            outcomes.append("rejected_validation")
            result.messages.append(f"{ref.dataset_code} {ref.release_date}: REJECTED — {summary}")
            logger.error("%s: %s", adapter.source, result.messages[-1])
            continue
        pending.append((ref, content_hash, parsed))

    if pending and hasattr(adapter, "validate_set"):
        set_failures = adapter.validate_set([p for _, _, p in pending])
        if set_failures:
            summary = "; ".join(set_failures)
            for ref, content_hash, _ in pending:
                storage.record_release_only(source=adapter.source, ref=ref, content_hash=content_hash,
                                                status="rejected_validation", summary="cross-file check: " + summary, fetched_at=now)
            outcomes.append("rejected_validation")
            result.messages.append(f"cross-file check failed — {summary}")
            logger.error("%s: %s", adapter.source, result.messages[-1])
            pending = []

    release_id = None
    for ref, content_hash, parsed in pending:
        stored = storage.store_release(source=adapter.source, ref=ref, content_hash=content_hash, parsed=parsed,
                                       licence=licence_snapshot, fetched_at=now)
        result.stored.append(stored)
        release_id = stored["release_id"]
        outcomes.append("new_release_ingested")
        result.messages.append(f"{ref.dataset_code} {ref.release_date}: stored — {stored['observations_new']} new, "
                               f"{stored['observations_revised']} revised, {stored['observations_unchanged']} unchanged")

    if "new_release_ingested" in outcomes:
        result.outcome = "new_release_ingested"
    elif "rejected_validation" in outcomes:
        result.outcome = "rejected_validation"
    else:
        result.outcome = "no_new_release"
    storage.record_run(source=adapter.source, ran_at=now, outcome=result.outcome, release_id=release_id,
                       message="; ".join(result.messages) or result.outcome)
    return result
