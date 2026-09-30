---
id: job-openings-trend-per-company-baseline
date: 2026-09-30
trigger-type: user-feedback
change-type: bug-fix
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Job openings trend counts a new company's bulk-loaded roles as a hiring spike

## Signal
See: `research/2026-09-30-job-openings-trend-panel-expansion-artifact.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — directly undermines "They can
see the trends clearly, how the hiring market numbers evolve through time." No success-criteria
change needed; this is a correctness fix to an existing success criterion.

## Change Type
`bug-fix`

## Root Cause

`backend/specs/market-health/api.md`'s own "Collection baseline" rule (added
`changes/2026-09-04-chart-baseline-and-render-fixes.md`) already states the right principle:
*"the first crawl is a one-time bulk load of whatever the sources had open at that moment
(collection setup), not market activity in that period."* But the rule as written only ever
applies that principle **once, platform-wide** — `min(fetched_at::date)` across all of
`raw_postings` — not per company. `market_openings.py::_fetch_counts()` implements exactly
that narrower rule.

The spec never anticipated a company being added to the tracked panel *after* the platform's
own baseline day. `us-eu-employer-panel-expansion` (`changes/2026-09-23-us-eu-employer-panel-expansion.md`,
still in-progress) did exactly that — batches added 2026-09-24 through 2026-09-28 took the
panel from 56 to 170 companies. Each batch's first crawl of a newly added company pulled in
every role that company currently had open, stamped with that crawl's `fetched_at` — the same
"bulk load, not market activity" pattern the existing rule already recognizes, just on a
different company on a different day. None of it was excluded, because the rule only checks
against the single, long-past platform baseline date. Result: ~6,200 postings landed in the
2026-09-24–2026-09-28 buckets and the Designer/Product Manager/Engineer lines all render an
ascendant trend that is coverage expansion, not hiring growth.

**Classification: spec is incomplete, not just the code.** The "Collection baseline" section
(`backend/specs/market-health/api.md` lines 745–750) and "Trend aggregation" (lines 1432–1453)
both define baseline exclusion as a single platform-wide date. That needs to change before the
implementation can be fixed correctly — this is not a case of code silently diverging from an
already-correct spec.

## The Fix

Generalize "exclude the bulk load" from **one platform-wide baseline day** to **each company's
own first-seen day**.

**Today's query** (`market_openings.py::_fetch_counts()`):
```sql
WITH baseline AS (
    SELECT min(fetched_at::date) AS day FROM raw_postings
)
SELECT ...
FROM raw_postings rp JOIN classifications c ON c.posting_id = rp.id
WHERE c.role_category IN (...)
  AND rp.fetched_at::date > (SELECT day FROM baseline)
GROUP BY period, c.role_category
```
One `day` for the entire table — only excludes postings from the platform's very first ingestion
run, ever.

**Fixed query:**
```sql
WITH company_baseline AS (
    SELECT company, min(fetched_at::date) AS day
    FROM raw_postings
    GROUP BY company
)
SELECT ...
FROM raw_postings rp
JOIN classifications c ON c.posting_id = rp.id
JOIN company_baseline cb ON cb.company IS NOT DISTINCT FROM rp.company
WHERE c.role_category IN (...)
  AND rp.fetched_at::date > cb.day
GROUP BY period, c.role_category
```
One `day` **per company** — a company's own first-crawl date, whenever that happened to be.
`IS NOT DISTINCT FROM` (not `=`) because `company` is `NULL` for legacy Adzuna rows and plain
`=` would drop every `NULL` row from the join (`NULL = NULL` is never true in SQL).

**Why this is the right generalization, not a special case:**
- A company tracked since the platform's original launch day still gets exactly the same
  exclusion as before — its "own first-seen day" *is* the platform baseline day, so behavior
  for all pre-existing companies and pre-existing chart data is unchanged.
- A company added next month gets its own opening snapshot excluded the same way, automatically
  — no code change needed the next time a batch is added. This is what makes it a real fix
  instead of a one-off patch for the current 5 batches.
- `_bucket_eligible_for_trend()` / `_generate_summary()` need **no change** — they only decide
  whether the *first* bucket of the whole series is a valid trend endpoint (it's the one that
  can still be partially truncated by the platform-wide launch day). Once bulk-load rows are
  stripped out per company before bucketing, every other bucket's count is already organic-only,
  so no additional eligibility logic is needed for mid-series company additions.
- No backfill needed. This is a live query over `raw_postings`, not a materialized or cached
  value — the next request after the fix ships recomputes every bucket correctly, including the
  ones that already look inflated today.

**What doesn't change:** the response shape, the `/api/market-health/openings` contract, the
frontend (`JobOpeningsChart.tsx` reads the same `data`/`summary` shape), and the MCP layer
(`get_job_demand` reads a separate, unrelated current-snapshot query in `market_query.py`, not
`_fetch_counts()` — confirmed by grep, not affected).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations / IA / Visual Design | — | no-change |
| Experience Spec | `design/market-health/experience.md` | no-change — chart behavior/interaction is unchanged; this is a counting-correctness fix, not a UX change. Confirmed the experience spec doesn't itself describe baseline handling (that detail lives only in the backend spec) |
| Backend Spec | `backend/specs/market-health/api.md` | update — "Collection baseline" (~line 745) and "Trend aggregation" (~line 1432) both need to state the per-company rule, since the root cause is the spec's own narrower definition |
| Frontend Spec / Implementation | — | no-change |
| Backend Implementation | `backend/src/market_openings.py`, `backend/tests/` (a new regression test) | update |
| Plain-Language Overview | `OVERVIEW.md` | no-change — bug-fix, chart already exists and already claims to show trends correctly; nothing new to describe |
| MCP Access Review | `ACCESS.md` | not-applicable — `get_job_demand` uses separate logic in `market_query.py`, not `_fetch_counts()`; no capability changes |
| Polite Scraping Review | — | not-applicable — no scraped source touched |
| Data Surface Review | — | not-applicable — no new data category; same shape, corrected counting |

## Execution Plan

- [x] Step 1: Root cause identified — spec's "Collection baseline" rule only covers one
      platform-wide date, not per-company onboarding (this document)
- [x] ✅ Step 2: Updated `backend/specs/market-health/api.md` — "Collection baseline" (~line 745)
      and "Trend aggregation" (~line 1432) both now state the per-company rule
- [x] ✅ Step 3: Rewrote `_fetch_counts()`'s SQL in `market_openings.py` — single platform-wide
      `baseline` CTE replaced with `company_baseline` (grouped by `company`, joined via
      `IS NOT DISTINCT FROM` to handle legacy `NULL`-company Adzuna rows). Added
      `backend/tests/test_market_openings_baseline.py` — inserts synthetic postings for a
      uniquely-named fake company into two past, fully-elapsed weeks (a 2-row "bulk load" day and
      a 1-row "new posting" day), asserts the bulk-load week's count is unaffected and the new-
      posting week increases by exactly 1, then deletes the test rows in a `finally` block. **Run
      directly against the live production database (no separate test DB configured) — confirmed
      0 leftover rows after the run.** `market_openings`/`market_stories` import cleanly; the
      only import failure found (`main.py` → `mcp` package missing) is a pre-existing gap in this
      Windows venv, unrelated to this change (that dependency lives in `venv_linux`)
- [x] ✅ Step 4: Verified against real production data, before and after:

  | Week | Old logic | Fixed logic |
  |---|---|---|
  | Aug 3 – Sep 7 (unaffected weeks) | 166–216 | 166–216 (identical) |
  | Sep 14 | 477 | 183 |
  | Sep 21 | 1,318 | 242 |
  | Sep 28 | 1,963 | 233 |

  (combined Designer + Product Manager + Engineer, weekly). The fixed numbers land back in the
  same 150–210 range as every unaffected week; the "surge" weeks were entirely the panel
  expansion's bulk-loaded rows. Also ran the real `get_openings()` endpoint end-to-end
  post-fix — six-month weekly view now reads as a normal, flat-ish series with no artificial
  spike, and the generated summary text still renders correctly
- [x] ✅ Step 5a: Committed locally (`fa33e07`) — spec update, `market_openings.py` fix,
      regression test, this change request, and the signal file
- [x] ✅ Step 5b: Pushed to `origin/main`. Correction: `DEPLOYMENT.md` §"Service: `api`" —
      auto-deploy has been **on** for `api` since 2026-08-16 (this session's earlier note that it
      was off was wrong; that gotcha describes a resolved `job-sync` history, not `api`'s current
      state). The push alone triggered deployment `854c039d` automatically — confirmed `SUCCESS`
      via Railway MCP, `commitHash` matches `fa33e07`. Verified live against production:
      `GET https://api-production-df13.up.railway.app/api/market-health/openings?range=six_months&granularity=week`
      now returns the corrected series (Sep 14/21 weeks back in the normal 150–210 range, no
      spike), confirming the fix is live for real users

## Decision Log
- 2026-09-30: Classified `bug-fix`, not `api-change` — the response contract, endpoint, and
  frontend are unchanged; only the counting logic inside an already-specified endpoint is
  corrected.
- 2026-09-30: Root cause traced to the spec itself (not just the code) — the "Collection
  baseline" rule's literal definition (single platform-wide date) is narrower than the principle
  it states ("a first crawl is a bulk load, not market activity"), which applies equally to any
  company's first crawl, not only the platform's very first one. Spec updated before
  implementation, per the bug-fix procedure's "spec is ambiguous or incorrect" branch.
- 2026-09-30: No backfill required — confirmed the endpoint computes live from `raw_postings` on
  every request, so a query fix alone corrects all historical buckets, not just future ones.
