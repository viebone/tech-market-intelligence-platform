---
id: chart-baseline-and-render-fixes
date: 2026-09-04
trigger-type: bug
change-type: bug-fix
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Chart shows unreal numbers — fix baseline definition and render bugs

## Signal

See: `research/2026-09-04-chart-baseline-and-render-fixes.md`

Related: `changes/2026-09-04-chart-summary-baseline.md` (introduced the
`ingestion_run_id`-keyed baseline this CR corrects), `changes/2026-08-22-chart-granularity.md`.

## Outcome

`outcomes/understand-market-health-before-searching.md` — success criterion "they can see the
trends clearly, how the hiring market numbers evolve through time" is currently violated: the
chart plots ~5% of the real data with numbers that do not match the dataset.

## Change Type

`bug-fix` — the chart violates what the spec promises. The `chart-summary-baseline` spec text
itself is also incorrect (baseline keyed on `ingestion_run_id`, which is NULL on 94% of rows),
so the affected spec layers are corrected first, then implementation.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change — success criteria already cover this |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | update — baseline described as the first collection day (not the first ingestion run); chart edge-case behaviour (flat line, sparse series, single bucket + caption); complete periods only (in-progress week/month not plotted) |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — chart rendering rules: month-period date formatting, zero-range Y-axis guard, X-label thinning, single-bucket caption, no re-adding a "today so far" point |
| Backend Spec | `backend/specs/market-health/api.md` | update — baseline defined by earliest `fetched_at::date`; drop the `ingestion_run_id` filter; restrict the query to the three plotted Role Categories; shape-match the range cutoff; in-progress bucket excluded from `data` |
| Frontend Implementation | `frontend/src/features/market-health/JobOpeningsChart.tsx` | update |
| Backend Implementation | `backend/src/market_openings.py` | update |

## Execution Plan

- [x] Step 1: `/new-experience` — updated `design/market-health/experience.md`: baseline = first
      collection day (by date, not ingestion run); trend window starts the next day; added
      Chart Specification rows for flat / single-bucket data and baseline exclusion; X-axis
      tick thinning for dense views; summary trend uses complete buckets only.
- [x] Step 2: `/new-backend-spec` — updated `backend/specs/market-health/api.md`: baseline is
      `min(fetched_at::date)`, postings on that date excluded; aggregation never references
      `ingestion_run_id`; query keeps only Designer / Product Manager / Engineer; range cutoff
      shape-matched to bucket key so boundary buckets aren't dropped; six months = current + 5.
- [x] Step 3: `/new-frontend-spec` — added a "Chart rendering rules" section to
      `frontend/specs/market-health/architecture.md`: month-period normalisation, zero-width
      y-domain guard, single-bucket dot, X-label thinning, per-year ticks on long ranges.
- [x] Step 4: `/implement-backend` — `backend/src/market_openings.py`: date baseline, category
      restriction, shape-matched cutoff, complete-bucket + post-baseline trend endpoints,
      baseline date threaded to the summary.
- [x] Step 5: `/implement-frontend` — `frontend/src/features/market-health/JobOpeningsChart.tsx`:
      `periodToDate` normalises month keys, zero-width y-domain guard, `niceTicks` dedupe +
      zero-range guard, single-bucket dots, X-label thinning, per-year ticks on long ranges.
- [x] Step 6: Validated — `get_openings` run against the production DB across the full
      range × granularity matrix (weekly Engineer ~134–182/wk, monthly correctly reports
      "not enough complete months"); endpoint verified through a live uvicorn stack; chart
      helper logic checked against real + degenerate data shapes; `npm run build` and
      `tsc` pass; `git diff --check` clean.
- [x] Step 7 (follow-up, user feedback "monthly view looks wrong"): the in-progress
      week/month is now dropped from `data` entirely, not just from the summary — a part-month
      beside a full month was drawing a false cliff. Backend: `_period_fully_elapsed` filter in
      `get_openings`. Frontend: single-bucket state shows labelled dots + an in-plot caption
      ("One complete month of data so far (August). The trend line needs at least two.").
      Experience + backend + frontend specs updated to "complete periods only". Re-validated
      against prod: weekly → 4 buckets (Aug 3–24), monthly → 1 bucket (August) + caption;
      `npm run build` passes.

## Decision Log

- 2026-09-04: Tracked against `understand-market-health-before-searching` — same outcome as the
  two prior chart CRs. No new outcome; success criteria already cover trustworthy trends.
- 2026-09-04: Classified `bug-fix`. The endpoint contract (params, response shape) does not
  change; internal aggregation logic does, and the backend + experience spec text describing
  the baseline is corrected because it is wrong, not merely out of date.
- 2026-09-04: Baseline moves from "earliest ingestion run with `total_inserted > 0`" to
  "earliest `fetched_at::date`". Production check: `ingestion_run_id` is NULL on 6,262 of 6,628
  rows (column added 2026-08-11, never backfilled), so the run-keyed approach silently dropped
  94% of postings. The real bulk seed (2026-08-03, 2,489 rows vs ~35/day after) is identifiable
  purely by date.
- 2026-09-04: The written summary's first-vs-last comparison uses only complete buckets
  (a week whose Sunday has passed; a month before the current one). With fewer than two
  complete post-baseline buckets the summary states the series is too short for a trend.
- 2026-09-04 (revised after user feedback): initially the in-progress bucket was still
  plotted (just not a summary endpoint). That still drew a false cliff on the chart — a
  4-day September next to a full August. Decision: the in-progress week/month is now removed
  from `data` entirely. The chart's last point is always a fully elapsed period. Monthly view
  is therefore a single labelled point (+ caption) until a second calendar month closes;
  that is honest and expected given ~1 month of post-baseline data.
- 2026-09-04: The `now.month - 5` six-month arithmetic was reviewed and kept — it yields six
  calendar months inclusive. Only the cutoff *string shape* was wrong for month granularity.
