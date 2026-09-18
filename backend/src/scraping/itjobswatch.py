"""
IT Jobs Watch adapter — the first concrete adapter built on PoliteScraper
(scraping/base.py). Scrapes explicitly-permitted, CC-licensed aggregate UK
IT market statistics — see research/2026-09-16-itjobswatch-scraping-permission.md
(the permission grant) and research/2026-09-16-itjobswatch-data-model-analysis.md
(what the site publishes and the data model this maps into).

*** REVISED 2026-09-18 — REGEX EXTRACTION REPLACED BY LLM EXTRACTION ***
See changes/2026-09-18-itjobswatch-llm-extraction.md and
backend/specs/scraped-data-sources/api.md's "IT Jobs Watch adapter" Business
Logic subsection for the full account. The first real production run
(2026-09-16 — real PoliteScraper requests, robots.txt respected, 3 pages
fetched) confirmed the previous regex patterns were extracting wrong values,
not just unverified ones, once checked against the real cached HTML
(scrape_page_cache.raw_body):
  - The historical comparison table is 3 columns —
    "{label} {current} {same-period-2025} {same-period-2024}" — not the
    assumed "{number} {label}". This bled numbers from adjacent cells into
    vacancy_count/rank/rank_yoy_change.
  - The currency symbol wasn't decoding as "£", so every £-anchored salary
    regex matched nothing — all 5 percentiles landed NULL.
  - Skills render as "{rank} {job_count} ({pct}%) {name}", not the assumed
    "{name} ({pct}%)" — every skill_name came out garbled (e.g.
    "Roadmaps 2 162" instead of "Roadmaps").
Extraction now works by reducing the fetched page to plain text
(BeautifulSoup's get_text() — which also correctly decodes HTML entities,
resolving the mojibake issue as a side effect) and asking Gemini
(gemini-2.5-flash, via the existing llm/ provider abstraction) to return the
same structured shape this module always needed, as strict JSON — the same
"ask for JSON, strip fences, validate, unmatched means None" idiom this
codebase's classification.py already uses. An LLM reading real page text is
far less brittle to this kind of real-structure surprise than another round
of hand-written regexes would be.

Real page URL pattern, still true: `/jobs/uk/{title}.do` (lowercase, spaces
as %20) — confirmed 2026-09-16, see prior revision's account in
research/2026-09-16-itjobswatch-real-page-verification.md.

Still open:
  1. The specific CC licence variant is separately confirmed already
     (CC BY-NC-SA 4.0 — source_licences.py, unrelated to page extraction).
  2. How much historical depth beyond the current 3-period (current/2025/
     2024) comparison is reachable on this same page shape — not checked.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import httpx

from llm import providers
from scraping.base import (
    ExtractionCacheStore,
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
# trusted — confirmed 2026-09-16 for product-owner; ux-designer/product-manager
# not independently re-checked, but use the same confirmed URL template.
ROLE_SLUGS: list[str] = [
    "product-owner",
    "ux-designer",
    "product-manager",
]

# CONFIRMED 2026-09-16 against the live Product Owner page — real pattern,
# lowercase title with spaces as %20, .do extension. The %20 (not a literal
# space) matters — httpx will otherwise send an unencoded space.
_ROLE_URL_TEMPLATE = f"{BASE_URL}/jobs/uk/{{title_encoded}}.do"

# Named explicitly per Rule 9 / this codebase's own llm/providers.py
# convention — never hidden behind an env-driven default. Same model
# classification.py already uses for the same kind of job ("extract
# structured facts from messy real text"); reused rather than a new
# consumer, given the tiny added volume (backend/specs/scraped-data-sources/
# api.md — External Dependencies).
EXTRACTION_MODEL = "gemini-2.5-flash"


def _role_title_encoded(slug: str) -> str:
    return slug.replace("-", "%20")


# IT Jobs Watch's own rolling window, per the analysis's example ("355
# Product Owner vacancies over 6 months") — not confirmed to always be
# exactly six months for every role/page.
_ASSUMED_WINDOW_MONTHS = 6

_EXTRACTION_SYSTEM_INSTRUCTION = """You extract UK IT job-market statistics from the plain \
text of an IT Jobs Watch role page. The text contains a 3-period historical comparison table \
("current period", "same period last year", "same period two years ago") and a ranked list of \
co-occurring skills. Return exactly these fields, using ONLY the values for the current \
(first, most recent) period of each table row — never the prior-year comparison columns:
- rank: integer, this role's current demand rank (from the "Rank" row's first/current value), or null if not present.
- rank_yoy_change: integer (signed, e.g. +22 or -12), the current period's year-on-year rank change, or null.
- vacancy_count: integer, the current period's count of permanent jobs requiring this role, or null.
- vacancy_share: number, the current period's percentage share of all permanent jobs in the UK (e.g. 0.31 for "0.31%"), or null.
- salary_sample_size: integer, the current period's "Number of salaries quoted", or null.
- salary_p10: number, the current period's 10th Percentile salary in GBP (strip currency symbol and commas), or null.
- salary_p25: number, same for 25th Percentile, or null.
- salary_median: number, same for the Median annual salary (50th Percentile), or null.
- salary_p75: number, same for 75th Percentile, or null.
- salary_p90: number, same for 90th Percentile, or null.
- salary_yoy_change: number (signed percentage, e.g. 7.69 for "+7.69%"), the current period's median year-on-year salary change, or null.
- skills: an array of objects, one per co-occurring skill listed, each with:
  - rank: integer, the skill's stated rank in the list.
  - job_count: integer, the stated count of jobs mentioning this skill.
  - percentage: number, the stated percentage (e.g. 48.88 for "(48.88%)").
  - name: string, the skill's name only — never include the rank or job_count numbers in this field.

Return strictly a JSON object with exactly these keys (rank, rank_yoy_change, vacancy_count, \
vacancy_share, salary_sample_size, salary_p10, salary_p25, salary_median, salary_p75, \
salary_p90, salary_yoy_change, skills). Use null for any field the text doesn't state — never \
guess or fabricate a value. No prose, no markdown fences."""

_NUMERIC_FIELDS = (
    "rank", "rank_yoy_change", "vacancy_count", "vacancy_share", "salary_sample_size",
    "salary_p10", "salary_p25", "salary_median", "salary_p75", "salary_p90", "salary_yoy_change",
)
_INT_FIELDS = {"rank", "rank_yoy_change", "vacancy_count", "salary_sample_size"}


def _build_extraction_prompt(text: str) -> str:
    return "Extract the statistics from this page text:\n" + json.dumps(text)


def _parse_extraction_response(text: str) -> dict:
    """Strip optional markdown code fences and parse the JSON object. Same
    idiom as classification.py's _parse_response — a malformed response
    yields {}, which _validate_extraction then turns into an all-None
    result rather than raising."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _coerce_number(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[^\d.\-+]", "", value)
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None
    return None


def _validate_extraction(entry: dict) -> dict:
    """
    Coerce a raw LLM JSON object to this adapter's expected shape. A field
    that's missing, null, or fails to coerce comes back None — never a
    guessed or fabricated value, same "unmatched means NULL" discipline the
    regex version followed (backend/specs/scraped-data-sources/api.md).
    """
    result: dict = {}
    for f in _NUMERIC_FIELDS:
        value = _coerce_number(entry.get(f))
        if value is not None and f in _INT_FIELDS:
            value = int(value)
        result[f] = value

    skills: list[dict] = []
    for raw_skill in entry.get("skills") or []:
        if not isinstance(raw_skill, dict):
            continue
        name = raw_skill.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        percentage = _coerce_number(raw_skill.get("percentage"))
        if percentage is None or not (0 < percentage <= 100):
            continue
        job_count = _coerce_number(raw_skill.get("job_count"))
        rank = _coerce_number(raw_skill.get("rank"))
        skills.append({
            "name": name.strip(),
            "percentage": percentage,
            "job_count": int(job_count) if job_count is not None else None,
            "rank": int(rank) if rank is not None else None,
        })
    result["skills"] = skills
    return result


def _slug_to_role_name(slug: str) -> str:
    return slug.replace("-", " ").title()


def _page_plain_text(html: str) -> str:
    """BeautifulSoup's get_text() also decodes HTML entities (e.g.
    "&pound;" -> "£"), resolving the currency-mojibake issue that broke the
    old regex extraction as a side effect of switching extraction methods."""
    from bs4 import BeautifulSoup

    text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text)


async def _extract_via_llm(text: str) -> dict:
    """
    One LLM call, following classification.py's prompt/parse idiom exactly
    (backend/specs/scraped-data-sources/api.md — Tech Decisions): ask for
    strict JSON, strip markdown fences, validate/coerce, never fabricate.
    No retry loop (unlike classification.py's _complete_with_retry) — at 3
    pages/week, a page that fails extraction this run is simply skipped
    (Business Logic rule 7) and picked up cleanly next week; the retry
    complexity there exists to protect a daily batch budget, which doesn't
    apply at this volume.
    """
    provider = providers.gemini(EXTRACTION_MODEL, api_key=os.environ.get("GEMINI_API_KEY_CLASSIFICATION"))
    response_text = await provider.complete(
        prompt=_build_extraction_prompt(text), system=_EXTRACTION_SYSTEM_INSTRUCTION,
    )
    return _validate_extraction(_parse_extraction_response(response_text))


@dataclass
class _ParsedRolePage:
    """What one role page's extraction resolves to — same shape whether it
    came from a fresh LLM call or a reused ExtractionCache entry."""
    rank: int | None
    rank_yoy_change: int | None
    vacancy_count: int | None
    vacancy_share: float | None
    salary_sample_size: int | None
    salary_p10: float | None
    salary_p25: float | None
    salary_median: float | None
    salary_p75: float | None
    salary_p90: float | None
    salary_yoy_change: float | None
    skills: list[dict]  # [{name, percentage, job_count, rank}]


def _to_parsed_role_page(extraction: dict) -> _ParsedRolePage:
    return _ParsedRolePage(**{f: extraction.get(f) for f in _NUMERIC_FIELDS}, skills=extraction.get("skills") or [])


def _extract_role_page(
    html: str, page_url: str, content_hash: str, extraction_store: ExtractionCacheStore,
) -> tuple[_ParsedRolePage, str]:
    """
    The content-hash-gated extraction step (Business Logic rule 11,
    ExtractionCache — backend/specs/scraped-data-sources/api.md). Returns
    the parsed page plus the model name that produced it (for
    extraction_model provenance), calling the LLM only on a cache miss or a
    changed hash.
    """
    cached = extraction_store.get(page_url)
    if cached is not None:
        entry, cached_hash = cached
        if cached_hash == content_hash:
            return _to_parsed_role_page(entry.extraction_json), entry.model

    text = _page_plain_text(html)
    extraction = asyncio.run(_extract_via_llm(text))
    extraction_store.set(
        page_url, content_hash, extraction, EXTRACTION_MODEL, datetime.now(timezone.utc),
    )
    return _to_parsed_role_page(extraction), EXTRACTION_MODEL


def _to_market_observation(
    role_slug: str, parsed: _ParsedRolePage, page_url: str,
    period_start: date, period_end: date, fetched_at: datetime, raw_html: str, extraction_model: str,
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
        extraction_model=extraction_model,
        raw_response={"html_excerpt": raw_html[:2000]},
    )


def _to_skill_associations(
    role_slug: str, parsed: _ParsedRolePage, page_url: str,
    period_start: date, period_end: date, fetched_at: datetime, extraction_model: str,
) -> list[FetchedSkillAssociation]:
    role_name = _slug_to_role_name(role_slug)
    return [
        FetchedSkillAssociation(
            role_name=role_name,
            skill_name=skill["name"],
            period_start=period_start,
            period_end=period_end,
            source_url=page_url,
            licence=get_licence("itjobswatch").licence,
            licence_confirmed=get_licence("itjobswatch").confirmed,
            fetched_at=fetched_at,
            percentage=skill["percentage"],
            job_count=skill["job_count"],
            rank=skill["rank"],
            extraction_model=extraction_model,
            raw_response={"role": role_name, **skill},
        )
        for skill in parsed.skills
    ]


class ItJobsWatchAdapter:
    name = "itjobswatch"

    def __init__(
        self,
        robots_store: RobotsCacheStore,
        page_store: PageCacheStore,
        extraction_store: ExtractionCacheStore,
    ) -> None:
        # Constructing PoliteScraper here (not at import time) means a
        # missing SCRAPER_CONTACT fails when this adapter is actually used,
        # not merely imported — matches how every other adapter in this
        # codebase is only as strict as being instantiated.
        self._scraper = PoliteScraper(source_name=self.name, robots_store=robots_store, page_store=page_store)
        self._extraction_store = extraction_store

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
                    parsed, extraction_model = _extract_role_page(
                        fetch_result.raw_body, page_url, fetch_result.content_hash, self._extraction_store,
                    )
                except Exception:
                    logger.exception("itjobswatch: skipping %s (extraction failed)", slug)
                    continue

                result.market_observations.append(
                    _to_market_observation(
                        slug, parsed, page_url, period_start, period_end,
                        fetched_at, fetch_result.raw_body, extraction_model,
                    )
                )
                result.skill_associations.extend(
                    _to_skill_associations(slug, parsed, page_url, period_start, period_end, fetched_at, extraction_model)
                )

        return result
