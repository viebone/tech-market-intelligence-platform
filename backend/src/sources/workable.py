"""
Workable Widget API adapter.

Public, unauthenticated GET endpoint per company (account subdomain):
    https://apply.workable.com/api/v1/widget/accounts/{account}

No API key, no login required (confirmed 2026-09-19, real request against
Starling Bank's real board). Returns every published job in one response,
same shape as Greenhouse — no documented pagination on this endpoint.
No documented rate limit for this GET endpoint either (Workable's own help
docs describe *using* the API, not access restrictions on it) — paced
conservatively regardless, same discipline as every other adapter here.

**Multi-location jobs are duplicated per location in the raw response** —
confirmed against real data: a single Starling "Android Engineer" role
posted in Manchester/Cardiff/Southampton/London appears as 4 separate array
entries sharing the same `shortcode`, unlike Greenhouse/Ashby (which nest
extra locations under one entry). Deduped here to one FetchedPosting per
distinct `shortcode` (first location kept) — same "one row per distinct
job, not per posted location" semantics Ashby's adapter already applies to
its own `secondaryLocations`, so a job open in 4 cities counts once toward
demand, not four times.
"""

from __future__ import annotations

import httpx

from sources.base import FetchedPosting, PacedFetcher, normalize_country

BASE_URL = "https://apply.workable.com/api/v1/widget/accounts"

# Curated, not exhaustive — every slug below was validated 2026-09-19 by
# confirming it resolves to a real, live Workable board (HTTP 200), same
# discipline as every other adapter's COMPANIES list. See EMPLOYER_PANEL.md
# — Starling was confirmed on Workable during UK employer panel research.
COMPANIES: list[str] = [
    "starling-bank",
]


class WorkableAdapter:
    name = "workable"
    companies = COMPANIES

    def __init__(self) -> None:
        self._fetcher = PacedFetcher(source_name="workable")

    def fetch_company(self, company: str) -> list[FetchedPosting]:
        with httpx.Client(timeout=30.0) as client:
            response = self._fetcher.get(client, f"{BASE_URL}/{company}")
        jobs = response.json().get("jobs", [])

        # Dedupe multi-location duplicates (see module docstring) — first
        # location seen for a given shortcode wins, never guessed/merged.
        seen_shortcodes: set[str] = set()
        results = []
        for job in jobs:
            shortcode = job.get("shortcode")
            if not shortcode or shortcode in seen_shortcodes:
                continue
            seen_shortcodes.add(shortcode)
            results.append(FetchedPosting(
                source_ref=f"{company}/{shortcode}",
                company=company,
                title=job.get("title", ""),
                raw_response=job,
                country=normalize_country(job.get("country")),
                city=job.get("city") or None,
                # Salary intentionally left unextracted for Workable — the
                # widget endpoint doesn't expose a structured compensation
                # field (confirmed against the real response shape,
                # 2026-09-19), same "no per-posting LLM call" scope
                # exclusion as Greenhouse.
            ))
        return results
