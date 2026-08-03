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

from sources.base import FetchedPosting, PacedFetcher

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

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
        return [
            FetchedPosting(
                source_ref=f"{company}/{job['id']}",
                company=company,
                title=job.get("title", ""),
                raw_response=job,
            )
            for job in jobs
        ]
