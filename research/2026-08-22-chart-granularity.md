---
source: user-feedback
date: 2026-08-22
---

Raw feedback (stakeholder, using the live deployed frontend):

> "on the initial tech hiring status there is no data because we have 5 years and 1
> year, can we have the breakdown to show month by month, week by week and day by
> day? I can imagine the chart may need horizontal scroll"

## Context grounded in the real implementation

`backend/src/market_openings.py`'s `get_openings()` always aggregates by month
(`date_trunc('month', rp.fetched_at)`) regardless of which `range` param is selected
(`"this_year" | "past_5_years" | "all_time"`) — `range` only filters *which* months
are included in the response, the bucket size (granularity) never changes.

Real live data collection only began 2026-08-03
(`changes/2026-07-16-adzuna-live-data-and-classification-taxonomy.md` et al.) — as of
today (2026-08-22) there are only ~3 weeks of real data. "This Year" (Jan–current)
shows 7 empty months and 1 partially-populated one; "Past 5 Years"/"All Time" are
even sparser. The chart currently has no way to view finer-than-month granularity,
so the only real data the platform has never renders as a meaningful shape — reads
as "no data" even though real data exists.

The stakeholder wants day/week/month as selectable **granularities** (bucket size),
independent of the existing **range** control (how far back the window goes), and
anticipates horizontal scroll may be needed for day-level granularity over a longer
window (e.g. daily buckets across "This Year" could mean 200+ x-axis points).

`design/market-health/experience.md`'s Chart Specification section currently defines
"Time Range" (This Year / Past 5 Years / All Time) as controlling both the window
*and* (implicitly, via "X axis ticks: Month names for This Year…") the fixed monthly
granularity — conflating two concepts that should be independent controls.
