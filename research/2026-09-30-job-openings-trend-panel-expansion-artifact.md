source: user-feedback
date: 2026-09-30

Show me the current trend in tech job openings by role category — Designer, Product Manager,
and Engineer — month over... shows an ascendant trend in the last few days. but is it because
we are tracking more companies and jobs?

## Investigation (same session)

Confirmed: yes. `market_openings.py`'s `_fetch_counts()` (backend for
`GET /api/market-health/openings`) counts "distinct postings first observed by daily ingestion"
per week/month bucket. It excludes exactly one bulk load — the platform-wide baseline day
(`min(fetched_at::date)` across all of `raw_postings`, the very first day the pipeline ever ran).

It does **not** exclude a company's own first-crawl day when that company is onboarded later,
mid-stream. The `us-eu-employer-panel-expansion` change request (`changes/2026-09-23-us-eu-employer-panel-expansion.md`,
still `in-progress`) added companies in five batches this week:

| Date | Tracked companies | Postings added that run |
|---|---|---|
| 2026-09-24 (batch 1) | 56 → 82 | ~1,130 |
| 2026-09-27 (batch 2) | 82 → 120 | 1,284 |
| 2026-09-28 (batch 3) | 120 → 134 | 1,571 |
| 2026-09-28 (batch 4) | 134 → 161 | 1,024 |
| 2026-09-28 (batch 5) | 161 → 170 | 1,229 |

Each batch's first crawl of a newly added company pulled in every role that company currently
had open, all stamped with that crawl's `fetched_at` date — so they land in whatever bucket
contains 2026-09-24–2026-09-28 and read as a hiring spike, not a coverage change. ~6,200
postings entered the dataset this way in four days.

This directly undermines `outcomes/understand-market-health-before-searching.md`'s success
criterion "They can see the trends clearly, how the hiring market numbers evolve through time" —
the chart currently cannot distinguish "we started watching 114 more companies" from "companies
are hiring more."
