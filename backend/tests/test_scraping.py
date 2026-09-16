"""
Unit tests for scraping/base.py — no live database or network needed.
PoliteScraper is DB-agnostic by design (takes RobotsCacheStore/PageCacheStore
as parameters), so these tests use simple in-memory fakes instead of the
Postgres-backed stores in scraping_storage.py — mirrors test_mcp_access.py's
own "test the parts that don't need a live database" scope.

No pytest in this repo yet — run directly:

    cd backend/src && ./venv_linux/bin/python ../tests/test_scraping.py
    (or, on Windows, ./venv/Scripts/python ../tests/test_scraping.py)

Every `test_*` function is a plain assert, same convention as
test_mcp_access.py / test_curated_match.py.
"""

import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import httpx  # noqa: E402

from scraping.base import (  # noqa: E402
    FetchedMarketObservation,
    FetchedSkillAssociation,
    PageCacheEntry,
    PoliteScraper,
    RobotsCacheEntry,
    RobotsDisallowedError,
    ScraperConfigError,
)
import logging  # noqa: E402

import source_licences as licences_module  # noqa: E402
from source_licences import (  # noqa: E402
    LicenceNotRegisteredError,
    SourceLicence,
    get_licence,
    is_source_usable,
    overall_status,
)
from scraping_storage import (  # noqa: E402
    _association_unchanged,
    _due_from_last_run,
    _observation_unchanged,
    _warn_if_licence_unconfirmed,
)


# ---------------------------------------------------------------------------
# In-memory fakes — deliberately not the Postgres-backed stores in
# scraping_storage.py, so these tests never touch a database.
# ---------------------------------------------------------------------------

class FakeRobotsStore:
    def __init__(self):
        self._entries: dict[str, RobotsCacheEntry] = {}

    def get(self, host):
        return self._entries.get(host)

    def set(self, host, raw_body, http_status, fetched_at):
        self._entries[host] = RobotsCacheEntry(raw_body=raw_body, fetched_at=fetched_at, http_status=http_status)


class FakePageStore:
    def __init__(self):
        self._entries: dict[str, PageCacheEntry] = {}
        self.set_calls = 0

    def get(self, url):
        return self._entries.get(url)

    def set(self, url, source, raw_body, content_hash, etag, last_modified, fetched_at, http_status):
        self.set_calls += 1
        self._entries[url] = PageCacheEntry(
            raw_body=raw_body, content_hash=content_hash, etag=etag,
            last_modified=last_modified, fetched_at=fetched_at, http_status=http_status,
        )

    def touch(self, url, fetched_at):
        entry = self._entries[url]
        self._entries[url] = PageCacheEntry(
            raw_body=entry.raw_body, content_hash=entry.content_hash, etag=entry.etag,
            last_modified=entry.last_modified, fetched_at=fetched_at, http_status=entry.http_status,
        )


class FakeTransport(httpx.BaseTransport):
    """Routes every request to a canned response — robots.txt gets its own
    canned body, everything else gets `page_response`. Counts real network
    calls made, so the cache-prevents-network-call test can assert on it."""

    def __init__(self, robots_body: str | None, page_body: str = "<html>hi</html>"):
        self.robots_body = robots_body
        self.page_body = page_body
        self.calls: list[str] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(str(request.url))
        if request.url.path == "/robots.txt":
            if self.robots_body is None:
                return httpx.Response(404, request=request)
            return httpx.Response(200, text=self.robots_body, request=request)
        return httpx.Response(200, text=self.page_body, request=request)


def _scraper(monkeypatch_contact: str = "Test Org test@example.org", **kwargs) -> tuple[PoliteScraper, FakeRobotsStore, FakePageStore]:
    import os
    os.environ["SCRAPER_CONTACT"] = monkeypatch_contact
    robots_store, page_store = FakeRobotsStore(), FakePageStore()
    scraper = PoliteScraper(
        source_name="test_source", robots_store=robots_store, page_store=page_store,
        min_interval_seconds=0.0,  # no real pacing delay in tests
        **kwargs,
    )
    return scraper, robots_store, page_store


def test_refuses_to_construct_without_scraper_contact():
    import os
    os.environ.pop("SCRAPER_CONTACT", None)
    try:
        PoliteScraper(source_name="x", robots_store=FakeRobotsStore(), page_store=FakePageStore())
        raised = False
    except ScraperConfigError:
        raised = True
    assert raised, "PoliteScraper must refuse to construct with no SCRAPER_CONTACT set"


def test_refuses_to_construct_with_placeholder_contact():
    import os
    for placeholder in ("", "YourOrgName your-real-email@example.com", "set SCRAPER_CONTACT"):
        os.environ["SCRAPER_CONTACT"] = placeholder
        try:
            PoliteScraper(source_name="x", robots_store=FakeRobotsStore(), page_store=FakePageStore())
            raised = False
        except ScraperConfigError:
            raised = True
        assert raised, f"placeholder-looking contact {placeholder!r} should have been refused"


def test_accepts_a_real_looking_contact():
    scraper, _, _ = _scraper()
    assert "Test Org test@example.org" in scraper.user_agent


def test_robots_disallow_is_respected_and_skips_the_request():
    scraper, _, _ = _scraper()
    transport = FakeTransport(robots_body="User-agent: *\nDisallow: /private/")
    client = httpx.Client(transport=transport)

    raised = False
    try:
        scraper.get(client, "https://example.org/private/page.html")
    except RobotsDisallowedError:
        raised = True
    assert raised, "a robots.txt-disallowed path must raise RobotsDisallowedError, never be overridden"
    # The disallowed page itself was never actually requested — only robots.txt was.
    assert all(c.endswith("/robots.txt") for c in transport.calls)


def test_robots_allow_lets_the_request_through():
    scraper, _, _ = _scraper()
    transport = FakeTransport(robots_body="User-agent: *\nDisallow: /private/")
    client = httpx.Client(transport=transport)

    result = scraper.get(client, "https://example.org/public/page.html")
    assert result.raw_body == "<html>hi</html>"
    assert not result.from_cache


def test_missing_robots_txt_means_everything_allowed():
    scraper, _, _ = _scraper()
    transport = FakeTransport(robots_body=None)  # 404 on /robots.txt
    client = httpx.Client(transport=transport)

    result = scraper.get(client, "https://example.org/anything.html")
    assert result.raw_body == "<html>hi</html>"


def test_page_cache_prevents_a_second_network_call_within_the_freshness_window():
    scraper, _, page_store = _scraper(min_refetch_interval_hours=24.0)
    transport = FakeTransport(robots_body=None)
    client = httpx.Client(transport=transport)
    url = "https://example.org/page.html"

    first = scraper.get(client, url)
    assert not first.from_cache
    calls_after_first = len(transport.calls)

    second = scraper.get(client, url)
    assert second.from_cache
    assert second.raw_body == first.raw_body
    # No new network call at all for the page itself (rule 4) — only the
    # first call's robots.txt + page fetch should have happened.
    assert len(transport.calls) == calls_after_first, "a fresh cache hit must make zero network calls"


def test_page_cache_expires_after_the_freshness_window():
    scraper, _, page_store = _scraper(min_refetch_interval_hours=24.0)
    transport = FakeTransport(robots_body=None)
    client = httpx.Client(transport=transport)
    url = "https://example.org/page.html"

    scraper.get(client, url)
    # Simulate the cached entry being older than the freshness window.
    entry = page_store._entries[url]
    page_store._entries[url] = PageCacheEntry(
        raw_body=entry.raw_body, content_hash=entry.content_hash, etag=entry.etag,
        last_modified=entry.last_modified,
        fetched_at=datetime.now(timezone.utc) - timedelta(hours=25),
        http_status=entry.http_status,
    )
    calls_before = len(transport.calls)
    result = scraper.get(client, url)
    assert not result.from_cache
    assert len(transport.calls) > calls_before, "a stale cache entry must trigger a real request"


def test_fetched_market_observation_requires_attribution_fields():
    # Mandatory fields (no default) — omitting one is a TypeError, not a
    # silently-incomplete row. This is what makes "attribution can't be
    # omitted" real, not just documentation.
    raised = False
    try:
        FetchedMarketObservation(
            entity_type="role", entity_name="Product Owner", employment_type="permanent",
            location="UK", period_start=date(2026, 1, 1), period_end=date(2026, 6, 30),
            # source_url, licence, fetched_at deliberately omitted
        )
    except TypeError:
        raised = True
    assert raised, "FetchedMarketObservation must require source_url/licence/fetched_at"


def test_fetched_market_observation_constructs_with_attribution():
    obs = FetchedMarketObservation(
        entity_type="role", entity_name="Product Owner", employment_type="permanent",
        location="UK", period_start=date(2026, 1, 1), period_end=date(2026, 6, 30),
        source_url="https://www.itjobswatch.co.uk/jobtitles/product-owner.aspx",
        licence="CC BY-NC-SA 4.0",
        licence_confirmed=True,
        fetched_at=datetime.now(timezone.utc),
        vacancy_count=355,
    )
    assert obs.vacancy_count == 355
    assert obs.taxonomy_match is None  # reserved, unpopulated by default


def test_fetched_skill_association_requires_attribution_fields():
    raised = False
    try:
        FetchedSkillAssociation(
            role_name="Product Owner", skill_name="Agile",
            period_start=date(2026, 1, 1), period_end=date(2026, 6, 30),
        )
    except TypeError:
        raised = True
    assert raised, "FetchedSkillAssociation must require source_url/licence/fetched_at"


def test_licence_registry_returns_a_registered_source():
    # Confirmed 2026-09-16 against itjobswatch.co.uk's own copyright page —
    # see source_licences.py's module comment for the exact quoted wording.
    lic = get_licence("itjobswatch")
    assert lic.source == "itjobswatch"
    assert lic.licence == "CC BY-NC-SA 4.0"
    assert lic.confirmed is True
    assert lic.attribution_text  # non-empty, real citation text, not just the licence name


def test_licence_registry_refuses_an_unregistered_source():
    raised = False
    try:
        get_licence("some-future-source-nobody-registered")
    except LicenceNotRegisteredError:
        raised = True
    assert raised, "an unregistered source must be a hard error, never a silent fallback"


def test_run_cadence_due_when_never_run():
    assert _due_from_last_run(None, min_interval_days=7, now=datetime.now(timezone.utc))


def test_run_cadence_not_due_within_the_window():
    now = datetime.now(timezone.utc)
    last_run_at = now - timedelta(days=3)
    assert not _due_from_last_run(last_run_at, min_interval_days=7, now=now)


def test_run_cadence_due_after_the_window():
    now = datetime.now(timezone.utc)
    last_run_at = now - timedelta(days=8)
    assert _due_from_last_run(last_run_at, min_interval_days=7, now=now)


def _sample_observation(**overrides) -> FetchedMarketObservation:
    defaults = dict(
        entity_type="role", entity_name="Product Owner", employment_type="permanent",
        location="UK", period_start=date(2026, 1, 1), period_end=date(2026, 6, 30),
        source_url="https://example.org/x", licence="test", licence_confirmed=True,
        fetched_at=datetime.now(timezone.utc),
        vacancy_count=355, vacancy_share=0.31, rank=477,
    )
    defaults.update(overrides)
    return FetchedMarketObservation(**defaults)


def test_observation_unchanged_detects_identical_values():
    obs = _sample_observation()
    previous = {f: getattr(obs, f) for f in (
        "taxonomy_match", "rank", "rank_yoy_change", "vacancy_count", "vacancy_share",
        "live_jobs", "salary_sample_size", "salary_p10", "salary_p25", "salary_median",
        "salary_p75", "salary_p90", "salary_unit", "salary_yoy_change",
    )}
    assert _observation_unchanged(obs, previous)


def test_observation_unchanged_detects_a_real_change():
    obs = _sample_observation(vacancy_count=355)
    previous = {f: getattr(obs, f) for f in (
        "taxonomy_match", "rank", "rank_yoy_change", "vacancy_count", "vacancy_share",
        "live_jobs", "salary_sample_size", "salary_p10", "salary_p25", "salary_median",
        "salary_p75", "salary_p90", "salary_unit", "salary_yoy_change",
    )}
    previous["vacancy_count"] = 360  # a real change since last time
    assert not _observation_unchanged(obs, previous)


def _sample_association(**overrides) -> FetchedSkillAssociation:
    defaults = dict(
        role_name="Product Owner", skill_name="Agile",
        period_start=date(2026, 1, 1), period_end=date(2026, 6, 30),
        source_url="https://example.org/x", licence="test", licence_confirmed=True,
        fetched_at=datetime.now(timezone.utc),
        job_count=163, percentage=45.9, rank=2,
    )
    defaults.update(overrides)
    return FetchedSkillAssociation(**defaults)


class _ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record):
        self.records.append(record)


def test_warns_loudly_when_storing_from_an_unconfirmed_licence_source():
    # A fake, deliberately unconfirmed source — never mutate the real
    # itjobswatch entry in a test.
    licences_module.SOURCE_LICENCES["_test_unconfirmed_source"] = SourceLicence(
        source="_test_unconfirmed_source", licence="Unclear", attribution_text="x",
        licence_url="https://example.org", confirmed=False, permits_commercial_use=False,
    )
    handler = _ListHandler()
    logger = logging.getLogger("scraping_storage")
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        _warn_if_licence_unconfirmed("_test_unconfirmed_source", 3, "market observation")
    finally:
        logger.removeHandler(handler)
        del licences_module.SOURCE_LICENCES["_test_unconfirmed_source"]

    assert len(handler.records) == 1
    assert handler.records[0].levelno == logging.WARNING
    assert "UNCONFIRMED" in handler.records[0].getMessage()


def _set_commercial_mode(value: str) -> None:
    import os
    os.environ["TMIP_COMMERCIAL_MODE"] = value


def test_usable_by_default_regardless_of_commercial_mode():
    # Revised 2026-09-16: usability is rejected-only now, never inferred
    # from commercial mode or permits_commercial_use.
    for mode in ("false", "true"):
        _set_commercial_mode(mode)
        assert is_source_usable("itjobswatch")  # confirmed, NC — but not rejected, so usable
    _set_commercial_mode("false")


def test_rejected_source_is_not_usable_regardless_of_commercial_mode():
    licences_module.SOURCE_LICENCES["_test_rejected"] = SourceLicence(
        source="_test_rejected", licence="Whatever", attribution_text="x",
        licence_url="https://example.org", confirmed=True, permits_commercial_use=True,
        rejected=True,
    )
    try:
        for mode in ("false", "true"):
            _set_commercial_mode(mode)
            assert not is_source_usable("_test_rejected")
    finally:
        _set_commercial_mode("false")
        del licences_module.SOURCE_LICENCES["_test_rejected"]


def test_commercial_mode_is_purely_informational():
    # Flipping the env var must not, by itself, change any source's
    # usability — only an explicit `rejected=True` does that now.
    licences_module.SOURCE_LICENCES["_test_permissive"] = SourceLicence(
        source="_test_permissive", licence="Whatever", attribution_text="x",
        licence_url="https://example.org", confirmed=False, permits_commercial_use=False,
    )
    try:
        _set_commercial_mode("false")
        before = is_source_usable("_test_permissive")
        _set_commercial_mode("true")
        after = is_source_usable("_test_permissive")
        assert before == after == True  # noqa: E712 — explicit for clarity
    finally:
        _set_commercial_mode("false")
        del licences_module.SOURCE_LICENCES["_test_permissive"]


def test_overall_status_pending_when_unconfirmed():
    licences_module.SOURCE_LICENCES["_test_status_pending"] = SourceLicence(
        source="_test_status_pending", licence="Unclear", attribution_text="x",
        licence_url="https://example.org", confirmed=False, permits_commercial_use=True,
    )
    try:
        assert overall_status("_test_status_pending") == "pending"
    finally:
        del licences_module.SOURCE_LICENCES["_test_status_pending"]


def test_overall_status_licensed_when_confirmed_and_not_rejected():
    _set_commercial_mode("false")
    assert overall_status("itjobswatch") == "licensed"


def test_overall_status_rejected_wins_even_if_confirmed():
    licences_module.SOURCE_LICENCES["_test_status_rejected"] = SourceLicence(
        source="_test_status_rejected", licence="Whatever", attribution_text="x",
        licence_url="https://example.org", confirmed=True, permits_commercial_use=True,
        rejected=True,
    )
    try:
        assert overall_status("_test_status_rejected") == "rejected"
    finally:
        del licences_module.SOURCE_LICENCES["_test_status_rejected"]


def test_overall_status_never_rejected_while_nobody_set_the_flag():
    # As of 2026-09-16: "we don't have any rejected just yet" — checked
    # against the real registry, not assumed. True regardless of commercial
    # mode, since rejection is now purely an explicit, manual decision.
    for mode in ("false", "true"):
        _set_commercial_mode(mode)
        for source in list(licences_module.SOURCE_LICENCES):
            assert overall_status(source) != "rejected"
    _set_commercial_mode("false")


def test_does_not_warn_for_a_confirmed_licence_source():
    handler = _ListHandler()
    logger = logging.getLogger("scraping_storage")
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        _warn_if_licence_unconfirmed("itjobswatch", 3, "market observation")  # confirmed, per licences.py
    finally:
        logger.removeHandler(handler)

    assert len(handler.records) == 0


def test_warns_loudly_when_storing_from_a_rejected_source():
    licences_module.SOURCE_LICENCES["_test_warn_rejected"] = SourceLicence(
        source="_test_warn_rejected", licence="Whatever", attribution_text="x",
        licence_url="https://example.org", confirmed=True, permits_commercial_use=True,
        rejected=True,
    )
    handler = _ListHandler()
    logger = logging.getLogger("scraping_storage")
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        _warn_if_licence_unconfirmed("_test_warn_rejected", 2, "market observation")
    finally:
        logger.removeHandler(handler)
        del licences_module.SOURCE_LICENCES["_test_warn_rejected"]

    assert len(handler.records) == 1
    assert "rejected=True" in handler.records[0].getMessage()


def test_association_unchanged_detects_identical_and_changed_values():
    a = _sample_association()
    previous_same = {"job_count": a.job_count, "percentage": a.percentage, "rank": a.rank}
    assert _association_unchanged(a, previous_same)

    previous_changed = {"job_count": a.job_count, "percentage": 10.0, "rank": a.rank}
    assert not _association_unchanged(a, previous_changed)


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"OK  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")
