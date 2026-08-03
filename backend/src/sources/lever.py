"""
Lever Postings API adapter.

Public, unauthenticated GET endpoint per company (site slug):
    https://api.lever.co/v0/postings/{site}?mode=json

Pagination (`skip`/`limit`) is documented but its default page size and any
maximum `limit` are not (confirmed against Lever's own API docs, 2026-08-03)
— an explicit PAGE_SIZE is passed on every request and the adapter paginates
defensively until a page returns fewer than PAGE_SIZE results, rather than
assuming one unpaginated call always returns everything. No documented rate
limit on this GET endpoint — Lever's only documented rate limit is on its
POST application-submission endpoint (2 req/sec), which this product never
calls. Paced conservatively regardless, see backend/specs/market-health/
api.md — Business Logic — Ingestion.
"""

from __future__ import annotations

import httpx

from sources.base import FetchedPosting, PacedFetcher

BASE_URL = "https://api.lever.co/v0/postings"
PAGE_SIZE = 100
MAX_PAGES = 20  # safety cap (2000 postings) so a runaway query can't paginate forever

# Curated, not exhaustive — every slug below was validated 2026-08-03 by
# confirming it resolves to a real, live Lever site (HTTP 200). Lever's
# market share has shrunk considerably as companies moved to newer ATS
# platforms, so this list is intentionally short — reviewed periodically,
# same discipline as Greenhouse's and Ashby's lists. See
# backend/specs/market-health/api.md — Tech Decisions — Company-list
# curation.
COMPANIES: list[str] = ["palantir", "plaid", "clari", "restream", "lever"]


class LeverAdapter:
    name = "lever"
    companies = COMPANIES

    def __init__(self) -> None:
        self._fetcher = PacedFetcher(source_name="lever")

    def fetch_company(self, company: str) -> list[FetchedPosting]:
        postings: list[dict] = []
        skip = 0
        with httpx.Client(timeout=30.0) as client:
            for _ in range(MAX_PAGES):
                response = self._fetcher.get(
                    client,
                    f"{BASE_URL}/{company}",
                    {"mode": "json", "skip": skip, "limit": PAGE_SIZE},
                )
                page = response.json()
                if not isinstance(page, list):
                    break
                postings.extend(page)
                if len(page) < PAGE_SIZE:
                    break
                skip += PAGE_SIZE

        return [
            FetchedPosting(
                source_ref=f"{company}/{p['id']}",
                company=company,
                title=p.get("text", ""),
                raw_response=p,
            )
            for p in postings
        ]
