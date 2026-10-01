---
id: coverage-over-time-chart
date: 2026-09-30
trigger-type: user-feedback
change-type: new-feature
outcome: understand-market-health-before-searching
status: in-progress
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

- [x] ✅ Step 1: `/new-experience` — updated `design/market-health/experience.md`. New
      **"Coverage Chart"** section (placed right after Written Summary Specification, before
      Interactions): two small stacked line charts (Companies tracked, Roles tracked — both
      cumulative), sharing the trend chart's own X axis/granularity/time-range controls so the
      two charts line up visually. Deliberately **no baseline exclusion** in this chart — the
      whole point is to surface the bulk-load jumps the trend chart above deliberately excludes.
      Fixed caption: "A step up here usually means more companies were added to tracking, not a
      change in hiring." Interactions and Edge Cases updated to match (switching range/
      granularity updates both charts; a no-change week renders as an honest flat line, not a
      no-data state)
- [x] ✅ Step 2: Confirmed IA — no-change. Same "Tech market hiring status" pinned task
      (`design/information-architecture.md` Task Panel entry, unchanged), no new zone or nav
      entry — the chart is new content inside an existing task's opening message, not a new
      destination
- [x] ✅ Step 3: Confirmed Visual Design — no-change. The Coverage Chart reuses the trend chart's
      own line-chart visual language (same type scale, same axis/tooltip treatment, same
      charting library per `design/visual-design.md`'s Charting library note) at smaller scale
      with no legend (one line per panel, panel title names it) — a compositional variant of the
      existing Line chart form, not a new chart type. No new tokens or catalogue entry needed
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
  a new read over already-captured `raw_postings`/`classifications` columns.
- 2026-10-01: **Refined per follow-up signal.** Panel 2 changed from "Roles tracked" (cumulative
  distinct `raw_postings`) to **"Job postings classified"** (cumulative distinct postings with a
  `classifications` row) — the user's stated goal is showing how much data the platform
  genuinely captures *and understands*, not just holds. This also makes the chart's purpose
  broader than the original spike-explainer framing alone: it's now also a plain, honest record
  of data growth and processing, which the spike-explainer use case still benefits from (a
  classification backlog lagging behind raw capture is itself a real, visible signal here, not
  hidden). `design/market-health/experience.md`'s Coverage Chart section updated accordingly —
  see Step 1 below.
