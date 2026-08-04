"""
Ashby Job Board API adapter.

Public, unauthenticated GET endpoint per company (job-board name):
    https://api.ashbyhq.com/posting-api/job-board/{jobBoardName}?includeCompensation=true

No pagination and no filtering support at all on this endpoint (confirmed
against Ashby's own API docs, 2026-08-03) — one call returns every published
job for a company. `includeCompensation=true` is passed so raw_response
captures the richest available response Ashby offers, consistent with never
projecting a source's response down. No documented rate limit; paced
conservatively regardless, see backend/specs/market-health/api.md —
Business Logic — Ingestion.
"""

from __future__ import annotations

import httpx

from sources.base import FetchedPosting, PacedFetcher, normalize_country

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"


def _extract_salary(raw: dict) -> tuple[int | None, int | None, str | None]:
    """
    Read directly from Ashby's own structured compensation summary — no
    inference. See backend/specs/market-health/api.md — Business Logic —
    Compensation extraction.
    """
    compensation = raw.get("compensation")
    if not compensation or not raw.get("shouldDisplayCompensationOnJobPostings", True):
        return None, None, None
    for component in compensation.get("summaryComponents") or []:
        if component.get("compensationType") == "Salary":
            min_v, max_v, currency = component.get("minValue"), component.get("maxValue"), component.get("currencyCode")
            if min_v is not None and max_v is not None:
                return min_v, max_v, currency
    return None, None, None

# Curated, not exhaustive — every name below was validated 2026-08-03 by
# confirming it resolves to a real, live Ashby job board (HTTP 200).
# Reviewed periodically, same discipline as Greenhouse's and Lever's lists.
# See backend/specs/market-health/api.md — Tech Decisions — Company-list
# curation.
COMPANIES: list[str] = [
    "ramp", "linear", "openai", "notion", "modal", "replit", "mercury",
    "deel", "loom", "vercel", "supabase", "perplexity", "elevenlabs",
    "ashby", "watershed",
]


class AshbyAdapter:
    name = "ashby"
    companies = COMPANIES

    def __init__(self) -> None:
        self._fetcher = PacedFetcher(source_name="ashby")

    def fetch_company(self, company: str) -> list[FetchedPosting]:
        with httpx.Client(timeout=30.0) as client:
            response = self._fetcher.get(
                client, f"{BASE_URL}/{company}", {"includeCompensation": "true"}
            )
        jobs = response.json().get("jobs", [])
        results = []
        for job in jobs:
            postal = (job.get("address") or {}).get("postalAddress") or {}
            salary_min, salary_max, currency = _extract_salary(job)
            results.append(FetchedPosting(
                source_ref=f"{company}/{job['id']}",
                company=company,
                title=job.get("title", ""),
                raw_response=job,
                country=normalize_country(postal.get("addressCountry")),
                city=postal.get("addressLocality") or None,
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=currency,
                salary_confidence="structured" if salary_min is not None else None,
                salary_extraction_method="ashby-structured" if salary_min is not None else None,
            ))
        return results
