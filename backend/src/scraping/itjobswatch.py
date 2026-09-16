"""
IT Jobs Watch adapter — the first concrete adapter built on PoliteScraper
(scraping/base.py). Scrapes explicitly-permitted, CC-licensed aggregate UK
IT market statistics — see research/2026-09-16-itjobswatch-scraping-permission.md
(the permission grant) and research/2026-09-16-itjobswatch-data-model-analysis.md
(what the site publishes and the data model this maps into).

*** REAL PAGE STRUCTURE NOT VERIFIED — READ BEFORE TRUSTING THIS ADAPTER ***
This implementation was written without fetching the live site — per
backend/specs/scraped-data-sources/api.md's explicit instruction not to
invent verified-sounding selectors as fact, and per this implementation
pass's own constraint against making real network calls to itjobswatch.co.uk.
Everything below `_parse_role_page` is a best-effort placeholder, shaped
around the concrete example numbers and phrasing in the data-model analysis
(e.g. "355 Product Owner vacancies", "median salary of £70,000", "ranked
#477") — not the real page's actual markup, which has never been inspected.
Before this adapter is trusted with real data:
  1. Fetch one real role page and compare its actual text/HTML against the
     patterns in `_ROLE_STAT_PATTERNS` below — expect most to need rewriting.
  2. Confirm the real URL structure (this guesses `{BASE_URL}/jobtitles/{slug}.aspx`
     from common IT-Jobs-Watch-style URL conventions — not verified).
  3. Confirm the real, specific CC licence variant and update its registered
     entry in `scraping/licences.py` (`SOURCE_LICENCES["itjobswatch"]`)
     and replace it before storing or republishing anything for real.
  4. Confirm how much historical depth (the source claims data back to
     2004) is actually reachable from a single rendered page vs. requiring
     separate historical-view URLs.
None of this is guessed *silently* — every placeholder below is named as one.
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
from scraping.licences import get_licence

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

# *** NOT VERIFIED *** — a guess at the URL pattern, common to this class of
# site but never confirmed against the real one.
_ROLE_URL_TEMPLATE = f"{BASE_URL}/jobtitles/{{slug}}.aspx"

# *** NOT VERIFIED *** — regex patterns guessing at how these figures might
# render as plain text once HTML tags are stripped, built from the analysis's
# own example phrasing ("355 Product Owner vacancies", "ranked #477", "10th
# percentile £46,250", etc.) — not from having seen the real page. Expect to
# rewrite these entirely once a real page is fetched and inspected.
_ROLE_STAT_PATTERNS = {
    "vacancy_count": re.compile(r"([\d,]+)\s+(?:permanent\s+)?vacanc(?:y|ies)", re.IGNORECASE),
    "vacancy_share": re.compile(r"([\d.]+)%\s+of all permanent (?:jobs|vacancies)", re.IGNORECASE),
    "rank": re.compile(r"rank(?:ed)?\s*#?\s*(\d+)", re.IGNORECASE),
    "rank_yoy_change": re.compile(r"([+\-]\d+)\s+positions?", re.IGNORECASE),
    "salary_sample_size": re.compile(r"([\d,]+)\s+vacanc(?:y|ies) quoting (?:a )?salary", re.IGNORECASE),
    "salary_p10": re.compile(r"10th percentile[^\d£]*£([\d,]+)", re.IGNORECASE),
    "salary_p25": re.compile(r"25th percentile[^\d£]*£([\d,]+)", re.IGNORECASE),
    "salary_median": re.compile(r"median salary[^\d£]*£([\d,]+)", re.IGNORECASE),
    "salary_p75": re.compile(r"75th percentile[^\d£]*£([\d,]+)", re.IGNORECASE),
    "salary_p90": re.compile(r"90th percentile[^\d£]*£([\d,]+)", re.IGNORECASE),
    "salary_yoy_change": re.compile(r"salary[^%\-+\d]*([+\-][\d.]+)%", re.IGNORECASE),
}

# *** NOT VERIFIED *** — a guess at how an associated-skill line might read
# as plain text, e.g. "Roadmaps 49.3%" — see the analysis's own Product
# Owner example list.
_SKILL_LINE_PATTERN = re.compile(r"([A-Za-z][A-Za-z0-9 /\-]{1,40})\s+([\d.]+)%")

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
    *** PLACEHOLDER — NOT VERIFIED AGAINST THE REAL SITE (see module
    docstring) ***. Extracts plain text via BeautifulSoup (which also
    decodes HTML entities, e.g. "&pound;" -> "£" — a naive tag-strip regex
    doesn't) and runs the regexes above over it — a reasonable first-guess
    strategy for a stats-table-style page, but the specific patterns are
    unverified. A field that doesn't match returns None (never
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

    # *** NOT VERIFIED *** — narrows skill-line matching to whatever follows
    # an "associated skills"-style label, to cut down on false positives
    # from unrelated "<words> N%" phrases elsewhere on the page (e.g. the
    # market-share sentence above). Still a guess: the real page's actual
    # skills-section marker is unknown.
    skills: list[tuple[str, float]] = []
    skills_section_match = re.search(r"associated skills[:\s]+(.*)$", text, re.IGNORECASE)
    skills_text = skills_section_match.group(1) if skills_section_match else ""
    for m in _SKILL_LINE_PATTERN.finditer(skills_text):
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
                page_url = _ROLE_URL_TEMPLATE.format(slug=slug)
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
