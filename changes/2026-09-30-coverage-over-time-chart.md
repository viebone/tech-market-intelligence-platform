---
id: coverage-over-time-chart
date: 2026-09-30
trigger-type: user-feedback
change-type: new-feature
outcome: understand-market-health-before-searching
status: triaged
---

# Change Request: Coverage-over-time companion chart (tracked companies + tracked roles)

## Signal
See: `research/2026-09-30-coverage-over-time-chart.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — "They can see the trends clearly,
how the hiring market numbers evolve through time." Directly reinforces this: the openings trend
chart can only be read correctly if a viewer can tell coverage growth apart from demand growth,
which today requires reading a change request, not the product itself. No success-criteria
wording change needed — this makes an existing criterion actually hold up under a real scenario
(`changes/2026-09-30-job-openings-trend-per-company-baseline.md`) that already happened once.

## Change Type
`new-feature`

## Triage Notes

Small in scope but still a new capability: a new visual the product doesn't have today, not a
fix to an existing one. No new data — built entirely from `raw_postings.company` /
`raw_postings.fetched_at`, already captured by every ingestion run. Deliberately **separate**
from the Designer/Product Manager/Engineer openings chart, not merged into it — the whole point
is letting a viewer cross-reference two distinct charts, not further complicating the one that
already carries three role-category lines.

**Explicitly out of scope** (own future change request if ever warranted):
- Auto-annotating the openings chart with panel-expansion events (a marker/overlay approach) —
  a heavier UX change than a companion chart; revisit only if a companion chart proves
  insufficient.
- Per-source (Greenhouse/Lever/Ashby/Workable/Personio) breakdowns of coverage — start with one
  combined tracked-companies line and one tracked-roles line; split later only if requested.
- Retroactively backfilling coverage history from before this platform's own launch — there is
  none; `raw_postings.fetched_at` is the only coverage history that exists (same "no earlier
  data" constraint the openings chart itself already documents).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change — no new UX principle, existing data-legibility principle already governs this |
| Information Architecture | `design/information-architecture.md` | review only — expected no-change (lives on the existing Market Health page, no new nav/zone); confirm during `/new-experience` |
| Visual Design | `design/visual-design.md` | review only — expected no-change (a two-line time series over the same week/month buckets the openings chart already uses likely fits an existing chart form); `/new-visual-design` only if the experience spec finds no existing form fits |
| Experience Spec | `design/market-health/experience.md` (and/or `design/market-health/data-stories.md`, whichever the Designer judges the right home — a companion chart near the openings chart vs. a new catalogue Data Story) | update |
| Backend Spec | `backend/specs/market-health/api.md` | update — new read (own endpoint or a new data-story section) computing cumulative distinct-company-count and distinct-posting-count per week/month bucket from `raw_postings` |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update |
| Backend Implementation | `backend/src/` | update |
| Frontend Implementation | `frontend/src/` | update |
| Plain-Language Overview | `OVERVIEW.md` | update — a real user-visible addition to the Market Health page |
| MCP Access Review | `ACCESS.md` + `backend/specs/mcp-access/api.md` | update — runs automatically as part of `/new-backend-spec` (this product has an MCP layer); needs an explicit exposed/not-exposed decision for the new read, same as every other capability |
| Polite Scraping Review | — | not-applicable — no scraped source involved, reads only already-captured `raw_postings` |
| Data Surface Review | market-health data-story catalogue / admin dashboard / ad-hoc query layer | not-applicable — no new data category or table; this is a new aggregation/visualization of facts (`raw_postings.company`, `.fetched_at`) that already exist, not a new kind of fact |

## Execution Plan

- [ ] Step 1: `/new-experience` — update `design/market-health/experience.md` (or
      `data-stories.md`): define the question this chart answers, its placement relative to the
      openings chart, chart form, legend, and the data-legibility basics (title, subtitle/scope,
      units — "companies" and "roles" are different units on what should likely be a dual-axis or
      two-panel view, not one shared axis — Rule 10)
- [ ] Step 2: Confirm IA — no-change expected (existing Market Health page, no new zone)
- [ ] Step 3: Confirm Visual Design — no-change expected if an existing chart form fits;
      `/new-visual-design` only if not
- [ ] Step 4: `/new-backend-spec` — update `backend/specs/market-health/api.md` with the new
      read (cumulative distinct `company` count and distinct `raw_postings.id` count per bucket,
      same `week`/`month` bucketing as `_fetch_counts`). Runs `/mcp-access-review` automatically —
      record the exposed/not-exposed decision
- [ ] Step 5: `/new-frontend-spec` — update `frontend/specs/market-health/architecture.md`
- [ ] Step 6: `/implement-backend`
- [ ] Step 7: `/implement-frontend`
- [ ] Step 8: Update `OVERVIEW.md`

## Decision Log
- 2026-09-30: Classified `new-feature`, not `ux-change` — this is a chart that doesn't exist
  today, not a modification to the openings chart's existing behavior.
- 2026-09-30: Deliberately scoped as a **separate** chart, not an overlay/annotation on the
  existing openings chart, per the signal's own framing ("that is a separated chart for the
  opening question maybe"). Overlay/annotation is recorded as explicitly out of scope, revisit
  only if a separate chart proves insufficient.
- 2026-09-30: Data Surface Review judged not-applicable — no new table or new kind of fact, only
  a new read over already-captured `raw_postings` columns.
