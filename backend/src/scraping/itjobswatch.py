"""
IT Jobs Watch adapter — the first concrete adapter built on PoliteScraper
(scraping/base.py). Scrapes explicitly-permitted, CC-licensed aggregate UK
IT market statistics — see research/2026-09-16-itjobswatch-scraping-permission.md
(the permission grant) and research/2026-09-16-itjobswatch-data-model-analysis.md
(what the site publishes and the data model this maps into).

*** PAGE STRUCTURE PARTIALLY VERIFIED 2026-09-16 — READ BEFORE TRUSTING THIS
ADAPTER FURTHER ***
Confirmed via one real, polite fetch (WebFetch, a single request, not the
compliant PoliteScraper path — see research/2026-09-16-itjobswatch-real-page-verification.md
for the full account, including a process misstep during this same check):
  - The real URL pattern is `/jobs/uk/{title}.do` (lowercase, spaces as
    `%20`), NOT `/jobtitles/{slug}.aspx` — the original guess was wrong,
    exactly as this module's own earlier warning anticipated. Fixed below.
  - Real phrasing confirmed for the live Product Owner page, 2026-09-16:
    vacancy count ("352"), market share ("0.31% of all permanent jobs in
    the UK"), rank + YoY change ("Rank 478", "+12"), the stated window
    ("6 months to 16 Sep 2026" — confirms the 6-month assumption), salary
    percentiles labelled "10th Percentile:" etc., sample size as "Number
    of salaries quoted: 210", YoY salary change ("+7.69%"), and skills as
    "{Skill} ({pct}%)" — e.g. "Roadmaps (48.86%)" — parenthesized, not
    space-separated as originally guessed.
  - **Caveat that still applies**: this was confirmed through an LLM-
    summarized reading of the page (WebFetch), not a byte-for-byte raw
    HTML inspection — the regexes below are now built against real
    *wording*, but the exact surrounding HTML tags/classes are still
    inferred, not confirmed. Treat the patterns below as much better
    informed, not as guaranteed to match on the first real run.
Still open:
  1. The specific CC licence variant is separately confirmed already
     (CC BY-NC-SA 4.0 — source_licences.py, unrelated to this page check).
  2. How much historical depth beyond the current 6-month window is
     reachable — not checked in this pass.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import httpx

from scraping.base import (
    FetchedMarketObservation,
    FetchedSkillAssociation,
    PageCacheStore,
    PoliteScraper,
    RobotsCacheStore,
    RobotsDisallowedError,
    ScrapeFetchError,
    ScrapeResult,
)
from source_licences import get_licence

logger = logging.getLogger(__name__)

BASE_URL = "https://www.itjobswatch.co.uk"

# Curated seed list — hand-picked roles to track, same "hand-curated, not
# exhaustive" discipline sources/*.py's COMPANIES lists already follow
# (DATA_SOURCES.md §4). Each slug's URL must resolve (HTTP 200) before being
# trusted — not verified here, since no real request is made in this
# implementation pass.
ROLE_SLUGS: list[str] = [
    "product-owner",
    "ux-designer",
    "product-manager",
]

# CONFIRMED 2026-09-16 against the live Product Owner page — real pattern,
# lowercase title with spaces as %20, .do extension. The %20 (not a literal
# space) matters — httpx will otherwise send an unencoded space.
_ROLE_URL_TEMPLATE = f"{BASE_URL}/jobs/uk/{{title_encoded}}.do"


def _role_title_encoded(slug: str) -> str:
    return slug.replace("-", "%20")


# Regex patterns rebuilt 2026-09-16 against real confirmed phrasing (see
# module docstring) — still not a raw-HTML-verified match (WebFetch gives an
# LLM-summarized reading, not verbatim source), so still reasonably likely
# to need adjustment on the first real run, but built from real wording now,
# not invented from an unrelated example.
_ROLE_STAT_PATTERNS = {
    "vacancy_count": re.compile(r"([\d,]+)\s+permanent jobs", re.IGNORECASE),
    "vacancy_share": re.compile(r"([\d.]+)%\s+of all permanent jobs", re.IGNORECASE),
    "rank": re.compile(r"Rank\s+(\d+)", re.IGNORECASE),
    "rank_yoy_change": re.compile(r"([+\-]\d+)\s+year-on-year rank change", re.IGNORECASE),
    "salary_sample_size": re.compile(r"Number of salaries quoted:?\s*([\d,]+)", re.IGNORECASE),
    "salary_p10": re.compile(r"10th Percentile:?\s*£([\d,]+)", re.IGNORECASE),
    "salary_p25": re.compile(r"25th Percentile:?\s*£([\d,]+)", re.IGNORECASE),
    "salary_median": re.compile(r"Median:?\s*£([\d,]+)", re.IGNORECASE),
    "salary_p75": re.compile(r"75th Percentile:?\s*£([\d,]+)", re.IGNORECASE),
    "salary_p90": re.compile(r"90th Percentile:?\s*£([\d,]+)", re.IGNORECASE),
    "salary_yoy_change": re.compile(r"[Yy]ear-on-year median change:?\s*([+\-][\d.]+)%"),
}

# CONFIRMED 2026-09-16 — skills render as "{Skill} ({pct}%)", parenthesized,
# not space-separated as originally guessed.
_SKILL_LINE_PATTERN = re.compile(r"([A-Za-z][A-Za-z0-9 /\-]{1,40})\s*\(([\d.]+)%\)")

# IT Jobs Watch's own rolling window, per the analysis's example ("355
# Product Owner vacancies over 6 months") — not confirmed to always be
# exactly six months for every role/page.
_ASSUMED_WINDOW_MONTHS = 6


def _slug_to_role_name(slug: str) -> str:
    return slug.replace("-", " ").title()


def _to_int(raw: str | None) -> int | None:
    if raw is None:
        return None
    return int(raw.replace(",", ""))


def _to_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    return float(raw.replace(",", ""))


@dataclass
class _ParsedRolePage:
    """What `_parse_role_page` extracts from one role page's text. See the
    module docstring — every field here is a best-effort guess, not a
    verified extraction."""
    vacancy_count: int | None
    vacancy_share: float | None
    rank: int | None
    rank_yoy_change: int | None
    salary_sample_size: int | None
    salary_p10: float | None
    salary_p25: float | None
    salary_median: float | None
    salary_p75: float | None
    salary_p90: float | None
    salary_yoy_change: float | None
    skills: list[tuple[str, float]]  # (skill_name, percentage)


def _parse_role_page(html: str) -> _ParsedRolePage:
    """
    Patterns rebuilt 2026-09-16 against real confirmed phrasing from the
    live Product Owner page (see module docstring) — better-informed than
    the original pure guess, but still not verified against raw HTML byte
    structure (confirmed via an LLM-summarized WebFetch reading, not a
    direct markup inspection). Extracts plain text via BeautifulSoup (which
    also decodes HTML entities, e.g. "&pound;" -> "£") and runs the regexes
    above over it. A field that doesn't match returns None (never
    guessed/fabricated) — same "unmatched means NULL, not a made-up value"
    discipline every other adapter in this codebase follows (e.g.
    sources/base.py's normalize_country()).
    """
    from bs4 import BeautifulSoup

    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)

    def _match(field_name: str) -> str | None:
        m = _ROLE_STAT_PATTERNS[field_name].search(text)
        return m.group(1) if m else None

    # The parenthesized "{Skill} ({pct}%)" format (confirmed 2026-09-16) is
    # distinctive enough to scan the whole page for, without needing to
    # first locate a section heading — none of the other confirmed fields
    # (vacancy share, rank change, salary YoY) use parentheses around a
    # percentage, so collisions are unlikely. Still not raw-HTML-verified
    # (see module docstring) — the real skills-section heading text, if
    # any, wasn't confirmed.
    skills: list[tuple[str, float]] = []
    for m in _SKILL_LINE_PATTERN.finditer(text):
        name, pct = m.group(1).strip(), float(m.group(2))
        if name and 0 < pct <= 100:
            skills.append((name, pct))

    return _ParsedRolePage(
        vacancy_count=_to_int(_match("vacancy_count")),
        vacancy_share=_to_float(_match("vacancy_share")),
        rank=_to_int(_match("rank")),
        rank_yoy_change=_to_int(_match("rank_yoy_change")),
        salary_sample_size=_to_int(_match("salary_sample_size")),
        salary_p10=_to_float(_match("salary_p10")),
        salary_p25=_to_float(_match("salary_p25")),
        salary_median=_to_float(_match("salary_median")),
        salary_p75=_to_float(_match("salary_p75")),
        salary_p90=_to_float(_match("salary_p90")),
        salary_yoy_change=_to_float(_match("salary_yoy_change")),
        skills=skills,
    )


def _to_market_observation(
    role_slug: str, parsed: _ParsedRolePage, page_url: str,
    period_start: date, period_end: date, fetched_at: datetime, raw_html: str,
) -> FetchedMarketObservation:
    return FetchedMarketObservation(
        entity_type="role",
        entity_name=_slug_to_role_name(role_slug),
        employment_type="permanent",  # first cut — contract market deferred, see spec priority order
        location="UK",                # first cut — regional breakdown deferred, see spec priority order
        period_start=period_start,
        period_end=period_end,
        source_url=page_url,
        licence=get_licence("itjobswatch").licence,
        licence_confirmed=get_licence("itjobswatch").confirmed,
        fetched_at=fetched_at,
        rank=parsed.rank,
        rank_yoy_change=parsed.rank_yoy_change,
        vacancy_count=parsed.vacancy_count,
        vacancy_share=parsed.vacancy_share,
        salary_sample_size=parsed.salary_sample_size,
        salary_p10=parsed.salary_p10,
        salary_p25=parsed.salary_p25,
        salary_median=parsed.salary_median,
        salary_p75=parsed.salary_p75,
        salary_p90=parsed.salary_p90,
        salary_unit="GBP/year" if parsed.salary_median is not None else None,
        salary_yoy_change=parsed.salary_yoy_change,
        raw_response={"html_excerpt": raw_html[:2000]},
    )


def _to_skill_associations(
    role_slug: str, parsed: _ParsedRolePage, page_url: str,
    period_start: date, period_end: date, fetched_at: datetime,
) -> list[FetchedSkillAssociation]:
    role_name = _slug_to_role_name(role_slug)
    return [
        FetchedSkillAssociation(
            role_name=role_name,
            skill_name=skill_name,
            period_start=period_start,
            period_end=period_end,
            source_url=page_url,
            licence=get_licence("itjobswatch").licence,
            licence_confirmed=get_licence("itjobswatch").confirmed,
            fetched_at=fetched_at,
            percentage=percentage,
            raw_response={"role": role_name, "skill": skill_name, "percentage": percentage},
        )
        for skill_name, percentage in parsed.skills
    ]


class ItJobsWatchAdapter:
    name = "itjobswatch"

    def __init__(self, robots_store: RobotsCacheStore, page_store: PageCacheStore) -> None:
        # Constructing PoliteScraper here (not at import time) means a
        # missing SCRAPER_CONTACT fails when this adapter is actually used,
        # not merely imported — matches how every other adapter in this
        # codebase is only as strict as being instantiated.
        self._scraper = PoliteScraper(source_name=self.name, robots_store=robots_store, page_store=page_store)

    def fetch(self) -> ScrapeResult:
        result = ScrapeResult()
        fetched_at = datetime.now(timezone.utc)
        period_end = fetched_at.date()
        period_start = period_end - timedelta(days=30 * _ASSUMED_WINDOW_MONTHS)

        with httpx.Client(timeout=30.0) as client:
            for slug in ROLE_SLUGS:
                page_url = _ROLE_URL_TEMPLATE.format(title_encoded=_role_title_encoded(slug))
                try:
                    fetch_result = self._scraper.get(client, page_url)
                except RobotsDisallowedError as exc:
                    logger.warning("itjobswatch: skipping %s (robots.txt disallows it): %s", slug, exc)
                    continue
                except ScrapeFetchError as exc:
                    logger.warning("itjobswatch: skipping %s (fetch failed): %s", slug, exc)
                    continue

                try:
                    parsed = _parse_role_page(fetch_result.raw_body)
                except Exception:
                    logger.exception("itjobswatch: skipping %s (parse failed)", slug)
                    continue

                result.market_observations.append(
                    _to_market_observation(
                        slug, parsed, page_url, period_start, period_end,
                        fetched_at, fetch_result.raw_body,
                    )
                )
                result.skill_associations.extend(
                    _to_skill_associations(slug, parsed, page_url, period_start, period_end, fetched_at)
                )

        return result
