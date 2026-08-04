source: business
date: 2026-07-28

Adzuna is not free at the scale this platform needs. The product owner wants a job-data
ingestion strategy that is not locked to a single paid vendor:

"adzuna is not free, so we need to plan a way to access job data from different sources
while keeping standard data model, that we should build to answer our users main questions
and achieve their outcomes, so data model shoudl serve the outcomes; our system should be
able to feed tech job data from different sournces: by gettting direct information for
company job portals; getting jobs from free aggregated data, free to use; by completing
data from other researches, articles, etc... it has to be very flexible, super strong to
handle all situations, and maintain the data model."

Three source categories named:
1. Direct company job portals / career pages (per-company scraping or feeds — no shared schema across companies)
2. Free / free-to-use aggregated job data APIs or feeds (Adzuna's free tier, but also alternatives — different auth, pagination, rate limits, and field shapes per provider)
3. Supplementary enrichment from other research (articles, reports) — not raw postings, but signal that can inform market-health context

Explicit requirements:
- The internal data model must be driven by the outcomes the platform serves (what users need
  to know — demand, seniority, track, salary, trends), not dictated by any one source's schema.
- The ingestion architecture must be flexible enough to onboard a new source without redesigning
  the model, and resilient enough that one source's failure, rate limit, or schema quirk doesn't
  take down ingestion as a whole.

## Update — 2026-08-03

Adzuna is now confirmed fully unusable, not just costly at scale — no license to continue
using their API at all. This changes the shape of the fix: Adzuna is not "adapter #1 to
migrate," it's a source to drop entirely. Its resilience code (fault isolation, retry/backoff,
rate-limit pacing, all built in `changes/2026-07-27-adzuna-ingestion-resilience.md`) is still
worth reusing as a *template* for new adapters — the patterns are sound — but nothing about
Adzuna itself ships going forward.

Decided replacement sources, after discussing tradeoffs: **Greenhouse, Lever, and Ashby** — all
ATS (applicant tracking system) platforms that host job boards for many companies behind a
shared, public, unauthenticated JSON API per platform. This is the pragmatic middle ground
between "one bespoke scraper per company" (too slow, too fragile to site changes) and a single
paid aggregator (the Adzuna problem): one adapter per ATS platform serves every company that
uses it, driven by a curated list of company board tokens/slugs (same shape as `ingest.py`'s
existing `ROLE_SEARCH_TERMS` list — a one-time/periodically-reviewed list, not per-company code).
Known tradeoff: ATS-platform coverage skews toward startups/scaleups that adopted a modern ATS;
large enterprises running custom career sites or legacy ATS (Workday, Taleo) aren't reachable
this way — real, honest coverage, not universal, and the `source` field on each record is what
makes that visible rather than implied.

Related prior work in this codebase:
- `backend/specs/market-health/api.md` — current `RawPosting`/`Classification` data model is
  Adzuna-shaped today: `RawPosting.id` is literally "Adzuna's own job id", `raw_response` is
  "the full Adzuna API response object... stored verbatim." Single-source by construction.
- `changes/2026-07-27-adzuna-ingestion-resilience.md` — hardened fault isolation, retries, and
  pacing for Adzuna specifically (per-term isolation, backoff, rate-limit pacing). That
  resilience work was scoped to Adzuna's failure modes; it did not address vendor dependency or
  multi-source ingestion.
- `outcomes/ai-provider-flexibility.md` — an existing outcome with the same shape for AI
  providers: an explicit-at-call-site adapter abstraction so no single vendor is load-bearing,
  and adding a provider means writing one adapter, not touching business logic. The user's
  framing here ("different sources," "standard data model," "flexible... handle all
  situations") is structurally the same problem for job-data sourcing.
