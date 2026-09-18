source: user-feedback
date: 2026-09-18

> "lets add this on the admin to track the market observations and the skills? we want to
> track this ingestions runs."

## Context
Follows directly from `changes/2026-09-18-itjobswatch-llm-extraction.md` — real
`market_observations`/`skill_associations` data now exists in production (3 observations, 90
skill associations, re-ingested through the new LLM-extraction path). The admin dashboard
(`pipeline-visibility`) has no view yet for this data, or for `scrape_ingestion_runs` (the
scraped-source run-cadence table) — an operator currently has no way to see any of it without
querying the database directly, the exact problem `outcomes/pipeline-processing-visibility.md`
already exists to solve for every other pipeline (postings, employment events, licensing).
