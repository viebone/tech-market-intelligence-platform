source: bug
date: 2026-09-04

The Tech hiring demand chart shows numbers that do not look real. Review found the cause and
several related rendering bugs.

## Root cause — the chart plots ~5% of the data

`backend/src/market_openings.py` `_fetch_counts()` filters `rp.ingestion_run_id IS NOT NULL`.
Production data (queried 2026-09-04):

- `raw_postings` total: 6,628
- `ingestion_run_id IS NULL`: 6,262 (94%) — the column was added 2026-08-11 and never
  backfilled for existing rows
- non-`"other"` classifications: 3,414
- rows that survive the chart's filters: ~180

So every plotted number is a small fraction of reality. Engineer shows ~140/week when the
real weekly inflow is ~150/week and the 2026-08-03 seed was ~2,200.

## The baseline exclusion does not do what the chart-summary-baseline CR intended

Intent: exclude the initial bulk collection so it does not read as a hiring surge.
Real seed in the data: 2026-08-03 = 2,489 postings in one day, vs 20–66/day afterwards.
That seed row set has `ingestion_run_id IS NULL`, so the `!= baseline_run_id` check never
touches it. The baseline must be defined by date (earliest `fetched_at::date`), not by
`ingestion_run_id`.

## Frontend rendering bugs (independent of the data issue)

1. Monthly view renders "Invalid Date": `JobOpeningsChart.tsx` does
   `new Date("2026-08T00:00:00")` for month periods — `NaN` in JS. Axis labels and tooltip
   date break.
2. Flat / single-point data → blank chart: when all in-view values are equal,
   `yMax - yMin === 0` → `toY` divides by zero → `NaN` path. `niceTicks` also returns no
   ticks; a 1-period range emits a lone `M` with no line segment.
3. Weekly + 6 Months → ~26 overlapping X labels. `xLabels()` emits one label per point for
   short ranges. The granularity spec called for a horizontal-scroll plot area
   (~24px/bucket) — not implemented.
4. Long range + weekly → no X labels. Labels only appear where `period.endsWith("-01")`;
   weekly Monday dates almost never do.

## Smaller issues

5. Month-granularity range cutoff: the string `"YYYY-MM-01"` compared lexically against
   `"YYYY-MM"` period keys drops the boundary month (`"2026-04" < "2026-04-01"`). (The
   `now.month - 5` arithmetic itself is fine — it yields six calendar months inclusive.)
6. Query filters `!= 'other'` but keeps `'unknown'` (135 rows) — counted in aggregates but
   not plotted as a series, so summary math will not match the lines.
7. The written summary compares the first bucket to the last bucket unconditionally. The last
   bucket is almost always the current in-progress week/month, so a 4-day-old September is
   compared against a full August and the summary reports a fake "down 77%".

## Proposed fix

- Drop the `ingestion_run_id` filter from the trend query entirely.
- Define baseline by date: earliest `fetched_at::date` in `raw_postings`; exclude that one
  calendar day from trend counts and name the covered window as starting the next day.
- Fix `formatPeriod`/`formatPeriodShort` for month periods, guard the zero-range
  `toY`/`niceTicks`, thin X labels, restrict the query to the three plotted categories,
  correct the six-month cutoff.

Related: `changes/2026-09-04-chart-summary-baseline.md`, `changes/2026-08-22-chart-granularity.md`.
