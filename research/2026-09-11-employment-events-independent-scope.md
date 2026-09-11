source: stakeholder-request
date: 2026-09-11

See also: `research/2026-09-11-employment-event-data-sources.md` (original source evaluation,
same day) and `changes/2026-09-11-employment-event-ingestion.md` (the parent change this
refines — employment events shipped today, scoped to the 35 tracked job-posting companies).

Raw trigger, mid-conversation while planning how to source real data for the just-shipped
employment-events feature:

> "layoff data should be generic, not connected to the companies we are getting jobs from.
> this should be an independent data which add insights to the tech market intelligence, it
> helps with the strategy and understanding the market. so lets build a full list of sources,
> then lets start one by one. I would start by those that are easier to get the data
> automatically, if possible something global, that provides data from all countries, but if
> not possible is ok, lets start from what is easier, free, and open to scrap the data by
> code, making sure that data guets correctly contextualised"

This reverses a scoping decision already recorded in three specs shipped earlier today:
1. `design/market-health/experience.md` — the "Employment events strip" section reasons the
   chart strip should show *only* tracked-company events ("the same coherence rule that keeps
   the trend chart itself scoped to tracked-company job postings... one picture means the same
   companies' hiring and contraction, not an unrelated firehose of every reported event
   anywhere").
2. `backend/specs/market-health/api.md` — `GET /api/market-health/employment-events` filters
   `WHERE matched_company IS NOT NULL`, same coherence reasoning documented inline.
3. `frontend/specs/market-health/architecture.md` — built assuming that scoping.

The underlying `employment_events` data model and ingestion pipeline (adapters,
`matched_company` as a *nullable* field) were already built source-agnostic — this is a
**surface-level** scoping decision (what the chart/endpoint *shows*), not a data-model change.
