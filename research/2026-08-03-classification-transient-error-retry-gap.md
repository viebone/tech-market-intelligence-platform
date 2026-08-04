source: bug
date: 2026-08-03

During a manual "Run now" test of the `job-sync` cron service on Railway (2026-08-03),
the ingestion run stopped early at classification batch 16/46 with:

```
INFO:classification:classify_postings: 5477 postings, 4663 unique titles (70 cached, 4593 need classifying)
... (batches 1-15 succeed) ...
INFO:httpx:HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent "HTTP/1.1 503 Service Unavailable"
ERROR:classification:classify batch 16/46 failed, stopping this run early (already-classified titles remain safely persisted): 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}
INFO:__main__:ingestion run recorded: status=partial
```

Diagnosis: `backend/src/classification.py`'s `_is_rate_limit_error()` only matches the
strings `"429"`, `"resource_exhausted"`, or `"rate limit"` in the exception text. A `503
UNAVAILABLE` ("model currently experiencing high demand") — a transient Gemini-side
overload, not a quota/rate-limit exhaustion — doesn't match any of those, so the existing
5-attempt/60s-backoff retry loop (`_complete_with_retry`) never triggered. The batch failed
on the very first attempt and the whole run stopped early (`status: "partial"`), even though
only 15 real requests had gone out (well under any real free-tier ceiling) and a retry would
plausibly have succeeded.

Notably, the source-fetch step for Greenhouse/Lever/Ashby (added in the 2026-07-28
multi-source-job-data-ingestion change) already treats "HTTP 429 and 5xx, plus connection
errors/timeouts" as retryable (`backend/specs/market-health/api.md` — Business Logic,
Ingestion). `classification.py`'s retry detection predates that pattern and is narrower —
it doesn't cover 5xx at all.
