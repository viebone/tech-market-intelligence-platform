---
id: job-data-source-flexibility
source: business
priority: high
status: active
created: 2026-07-28
---

# Outcome: The platform can source job data from multiple providers, adapters, and enrichment channels without changing its internal data model

## Signal
See: `research/2026-07-28-multi-source-job-data-ingestion.md`

Adzuna is not free at the scale this platform needs. The business needs job-data ingestion
that is not load-bearing on a single paid vendor — able to draw from direct company job
portals, free/free-tier aggregated job APIs, and supplementary research/article enrichment,
all normalized into one internal model that serves what users actually need (demand,
seniority, track, salary, trends) — not whatever shape the last source happened to return.

## Context
Today's data model is Adzuna-shaped by construction: `RawPosting.id` is documented as
"Adzuna's own job id," and `raw_response` is "the full Adzuna API response object... stored
verbatim" (`backend/specs/market-health/api.md`). Every source this platform will ever add —
a company careers page, a different free aggregator, a research article with market
commentary — has a different schema, auth model, reliability profile, and update cadence.
Without a source-agnostic model and an explicit adapter boundary, every new source becomes a
bespoke rewrite of ingestion, storage, and classification, and the platform stays exposed to
any single vendor's pricing or availability.

This is the same shape as `outcomes/ai-provider-flexibility.md` solved for AI providers:
an explicit adapter per source, declared at the point of use, with no business logic that
assumes which source produced a given row. Losing one source degrades coverage; it must never
break ingestion, classification, or the trends `understand-market-health-before-searching`
depends on.

## Success looks like
- Adding a new job-data source (a new aggregator, a company portal, a research feed) means
  writing one adapter that maps into the existing model — no changes to classification,
  trend aggregation, or the API endpoints that read from it
- The internal data model (raw postings + classification) is defined by what the product's
  outcomes need to know, not by any one source's response shape
- Every stored posting/record is traceable to the specific source and adapter that produced
  it, so provenance and trust (`outcomes/ai-reasoning-transparency.md`) hold even when data
  is blended from multiple sources
- One source failing, rate-limiting, or being removed degrades coverage for that source only —
  ingestion as a whole keeps running on every other source, matching the fault-isolation
  precedent already set for Adzuna (`changes/2026-07-27-adzuna-ingestion-resilience.md`)
- Enrichment content (articles, reports) that isn't a structured job posting can still feed
  the platform's market-health narrative without being forced into the posting/classification
  shape it doesn't fit
- No feature or endpoint's business logic branches on which source a given record came from

## Out of scope
- Building every source connector immediately — this outcome is about the model and adapter
  boundary being source-agnostic, not about maximizing source count on day one
- Deduplicating the *same* job posting when it appears across multiple sources (cross-source
  entity resolution) — first pass treats each source's records independently; true dedupe is a
  future refinement once multiple sources are live
- Automatic source selection/routing by cost or quality — source configuration is explicit,
  same principle as `ai-provider-flexibility`'s "routing is always explicit, never magic"
- Paid/enterprise data licensing deals — this is about free and owned-channel sources
