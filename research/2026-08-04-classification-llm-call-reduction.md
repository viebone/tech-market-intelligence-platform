source: internal
date: 2026-08-04

Follow-up to `research/2026-08-03-classification-transient-error-retry-gap.md` (which fixed
transient-error retries and has since been deployed and verified working — two `503`s were
successfully retried in production on 2026-08-04). Despite that fix, the 2026-08-04 scheduled
`job-sync` run still stopped early (`status: partial`), this time on a real `429
RESOURCE_EXHAUSTED`. Google's own error payload confirms the exact constraint for the first
time:

```
Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests,
limit: 20, model: gemini-2.5-flash
quotaId: 'GenerateRequestsPerDayPerProjectPerModel-FreeTier'
```

**20 requests per day, per project, per model.** Not a per-minute rate limit — the existing
code comments in `classification.py` (`SECONDS_BETWEEN_BATCHES = 13 # ... free tier's 5
req/min cap`) were based on an incorrect assumption about which limit actually binds. The
numbers line up exactly across the two most recent runs: the 2026-08-03 manual test consumed
15 requests before an unrelated 503 stopped it; the 2026-08-04 scheduled run got 5 more in
(batch 1 needed 3 attempts, batch 2 needed 2) before batch 3 hit the wall immediately —
15 + 5 = 20, exactly the documented daily cap.

At `BATCH_SIZE = 100` titles/batch and 20 requests/day, maximum daily classification
throughput is ~2,000 unique titles. But real multi-source ingestion runs are surfacing far
more than that: 4,663 unique titles on 2026-08-03, 3,121 on 2026-08-04. Unlike the retired
Adzuna search-term-based fetch, Greenhouse/Lever/Ashby return each company's entire job
board with no server-side tech-role filter — a large share of what's fetched is non-tech
(sales, legal, finance, HR, ops roles at companies like Stripe/Airbnb/Coinbase) and currently
burns a full LLM call just to land on `role_category: "other"`, which a cheap heuristic could
determine for free.

User's request, verbatim intent: "minimise at max as possible llm and api calls to make it
work with the free allowance... we need to limit the amount of jobs that we get, lets get
only new jobs, only those within the tech industry, etc." Concrete directions to explore:
1. Never spend an LLM call on a posting/title already resolved (already true today via the
   title cache and `get_all_unclassified()` — worth confirming/tightening, not rebuilding).
2. Pre-filter to plausible tech roles before any LLM call, so obviously non-tech titles reach
   `role_category: "other"` without spending a request.
3. Any other viable lever to cut daily call volume — backlog processing order was checked as
   part of this investigation: `raw_postings.get_all_unclassified()` has no `ORDER BY`, so
   which postings get priority when the backlog exceeds daily throughput is effectively
   undefined/arbitrary today, not FIFO. Worth fixing regardless of the pre-filter, since a
   20/day ceiling means order-of-processing now directly determines what actually gets
   classified promptly versus what waits indefinitely.

## Follow-up (same day): explicit sampling cap

User's further input: "should we limit the number of jobs we want to include. at the end we
just need a sample of data not everything. that could help as well." Reframes the goal from
"try to classify everything, eventually give up when quota runs out" to "deliberately bound
how much gets classified per run to a number the free tier can actually sustain, since Market
Health's trend charts need a representative read on the market, not an exhaustive census of
every posting." Today's `classify_postings` has no upper bound — it attempts every unclassified
title it's handed and only stops when the provider forces it to (`stopped_early`), which means
every run either silently succeeds under the cap or noisily fails against it; there's no
version of "succeeds on purpose, having deliberately done less."

