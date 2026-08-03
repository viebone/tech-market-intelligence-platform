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

from sources.base import FetchedPosting, PacedFetcher

BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"

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
        return [
            FetchedPosting(
                source_ref=f"{company}/{job['id']}",
                company=company,
                title=job.get("title", ""),
                raw_response=job,
            )
            for job in jobs
        ]
