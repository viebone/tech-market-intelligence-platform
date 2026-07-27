source: bug
date: 2026-07-27

The daily ingestion cron (`job-sync` on Railway) ran for the first time on its real
schedule at 2026-07-27 06:00 UTC and crashed. Deploy logs:

- `UX designer` search: fetched 23, inserted 23 new — succeeded
- `user experience designer` search: fetched 9, inserted 5 new — succeeded
- `product designer` search: Adzuna returned `503 Service Temporarily Unavailable`
  — unhandled, propagated up through `ingest_search_term` → `run()`'s single
  try/except around the whole search-term loop, which logged the failure,
  recorded an `ingestion_runs` row with `status="failed"`, then re-raised.
  The re-raise crashed the container (Railway marked the deployment `CRASHED`;
  `restartPolicyType: NEVER` means no auto-retry — it just sits crashed until
  the next scheduled tick).

The two successful terms' postings were already committed before the crash, so
that data wasn't lost — but classification never ran this cycle, and the other
9 of 12 search terms were never attempted.

User's request, verbatim intent: fix `ingest.py`/`adzuna_client.py` so the pipeline
"handles all different scenarios" — specifically:
1. Handle empty responses from Adzuna gracefully (a term returning 0 results is
   normal, not an error)
2. Handle Adzuna errors (the 503 seen, and other HTTP error statuses generally)
   without crashing the whole run — one bad term should not take down the other 11
3. Respect Adzuna's rate limit (calls per minute) — user's understanding is Adzuna
   caps requests per minute; `adzuna_client.py` currently has no pacing/backoff at
   all between requests, unlike `classification.py`'s existing batch-pacing +
   rate-limit-retry logic for the Gemini API, which is the closest existing
   pattern in this codebase to model the fix on.

Related: `backend/specs/market-health/api.md`'s `IngestionRun.status` field already
documents `"partial"` = "completed but stopped early (e.g. hit an unresolvable rate
limit)" — but that graceful-degradation behavior currently only exists in
`classification.py` (`classify_postings`'s `stopped_early` handling). The fetch step
has no equivalent — this bug is the fetch step not living up to a resilience pattern
the spec already assumes exists product-wide.
