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

import re

import httpx

from sources.base import FetchedPosting, PacedFetcher

BASE_URL = "https://api.lever.co/v0/postings"
PAGE_SIZE = 100
MAX_PAGES = 20  # safety cap (2000 postings) so a runaway query can't paginate forever

# Matches phrasing like "estimated salary range for this position is estimated
# to be $93,000 - $160,000/year" — confirmed fairly consistent across real
# Lever postings (2026-08-04). No LLM fallback for postings this doesn't
# match — see backend/specs/market-health/api.md — Business Logic —
# Compensation extraction for why (per-posting LLM cost, deliberately out of
# scope).
_SALARY_RANGE_RE = re.compile(r"\$\s?([\d,]{4,})\s*-\s*\$?\s?([\d,]{4,})")


def _extract_salary(additional_plain: str | None) -> tuple[int | None, int | None]:
    if not additional_plain:
        return None, None
    match = _SALARY_RANGE_RE.search(additional_plain)
    if not match:
        return None, None
    try:
        low = int(match.group(1).replace(",", ""))
        high = int(match.group(2).replace(",", ""))
    except ValueError:
        return None, None
    if low > high:
        low, high = high, low
    return low, high


def _extract_city(location: str | None) -> str | None:
    """Best-effort city from a "City, ST" free-text string. None if it
    doesn't split cleanly — never a guess."""
    if not location or "," not in location:
        return None
    city = location.split(",")[0].strip()
    return city or None

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

        results = []
        for p in postings:
            salary_min, salary_max = _extract_salary(p.get("additionalPlain"))
            results.append(FetchedPosting(
                source_ref=f"{company}/{p['id']}",
                company=company,
                title=p.get("text", ""),
                raw_response=p,
                country=(p.get("country") or "").upper() or None,
                city=_extract_city(p.get("categories", {}).get("location")),
                salary_min=salary_min,
                salary_max=salary_max,
                # Regex only matches a "$" pattern, and Lever postings in this
                # dataset are overwhelmingly US-based — USD is a reasonable
                # assumption for a match, not a guess at the number itself.
                salary_currency="USD" if salary_min is not None else None,
                salary_confidence="parsed" if salary_min is not None else None,
                salary_extraction_method="lever-regex" if salary_min is not None else None,
            ))
        return results
