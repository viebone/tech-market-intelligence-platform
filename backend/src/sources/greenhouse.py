"""
Greenhouse Job Board API adapter.

Public, unauthenticated GET endpoint per company (board token):
    https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true

No pagination — one company's board returns every published job in a single
response. No documented rate limit for this endpoint (confirmed against
Greenhouse's own API docs, 2026-08-03) — paced conservatively regardless, see
backend/specs/market-health/api.md — Business Logic — Ingestion.
"""

from __future__ import annotations

import httpx

from sources.base import FetchedPosting, PacedFetcher, normalize_country

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


def _extract_location(job: dict) -> tuple[str | None, str | None]:
    """
    Best-effort city/country from offices[0].location ("City, State, Country")
    when present — absent for a large share of postings, in which case both
    are left None rather than parsing the separate, messier `location.name`
    field (which mixes remote-status and multiple cities in one string). See
    backend/specs/market-health/api.md — Business Logic — Location
    normalization.
    """
    offices = job.get("offices") or []
    if not offices:
        return None, None
    location = offices[0].get("location")
    if not location or "," not in location:
        return None, None
    parts = [p.strip() for p in location.split(",")]
    city = parts[0] or None
    country = normalize_country(parts[-1])
    return city, country

# Curated, not exhaustive — every token below was validated 2026-08-03 by
# confirming it resolves to a real, live Greenhouse job board (HTTP 200).
# Reviewed periodically, same discipline the retired ROLE_SEARCH_TERMS used:
# add a company once it's worth tracking, retire one whose board token stops
# resolving. See backend/specs/market-health/api.md — Tech Decisions —
# Company-list curation.
COMPANIES: list[str] = [
    "stripe", "airbnb", "pinterest", "asana", "reddit", "robinhood",
    "coinbase", "affirm", "webflow", "figma", "airtable", "cloudflare",
    "twilio", "discord", "gitlab",
]


class GreenhouseAdapter:
    name = "greenhouse"
    companies = COMPANIES

    def __init__(self) -> None:
        self._fetcher = PacedFetcher(source_name="greenhouse")

    def fetch_company(self, company: str) -> list[FetchedPosting]:
        with httpx.Client(timeout=30.0) as client:
            response = self._fetcher.get(
                client, f"{BASE_URL}/{company}/jobs", {"content": "true"}
            )
        jobs = response.json().get("jobs", [])
        results = []
        for job in jobs:
            city, country = _extract_location(job)
            results.append(FetchedPosting(
                source_ref=f"{company}/{job['id']}",
                company=company,
                title=job.get("title", ""),
                raw_response=job,
                country=country,
                city=city,
                # Salary intentionally left unextracted for Greenhouse — see
                # backend/specs/market-health/api.md — Business Logic —
                # Compensation extraction. Reliable extraction here would
                # need a per-posting LLM call, a deliberately excluded scope.
            ))
        return results
