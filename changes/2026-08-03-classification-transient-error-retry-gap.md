---
id: classification-transient-error-retry-gap
date: 2026-08-03
trigger-type: bug
change-type: bug-fix, technical-refactor
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Classification should retry transient provider errors, not just rate limits

## Signal
See: `research/2026-08-03-classification-transient-error-retry-gap.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md`

This outcome depends on market data staying current and continuous ("they can see the
trends clearly, how the hiring market numbers evolve through time"). A daily/manual
ingestion run that stops early on a momentary provider blip — rather than retrying past
it — breaks that continuity for no real reason. Same outcome and same reasoning as
`changes/2026-07-27-adzuna-ingestion-resilience.md`, which fixed the identical class of
problem on the fetch side of this same pipeline.

## Change Type
`bug-fix` — `classification.py`'s `_is_rate_limit_error()` only matches `"429"`,
`"resource_exhausted"`, or `"rate limit"` in the exception text. A `503 UNAVAILABLE`
("model currently experiencing high demand") is a transient provider overload, not a
quota/rate-limit exhaustion, so it doesn't match — the existing 5-attempt/60s-backoff
retry loop never triggers, and the run stops early after a single transient failure.
`backend/specs/market-health/api.md` already documents the fetch step (Greenhouse/Lever/
Ashby) treating "HTTP 429 and 5xx, plus connection errors/timeouts" as retryable —
classification's detection predates that pattern and is narrower.
`technical-refactor` — no user-facing behavior changes; purely ops-facing pipeline
hardening, same framing as the 2026-07-27 precedent.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | no-change — purely backend/ops resilience, nothing user-facing changes |
| Backend Spec | `backend/specs/market-health/api.md` | update — broaden the documented retryable-error policy for classification (Business Logic — Ingestion / Classification) to explicitly include HTTP 5xx / transient provider unavailability, matching the pattern already established for the source-fetch step; adjust the `IngestionRun.status = "partial"` cause description accordingly |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | no-change |
| Backend Implementation | `backend/src/classification.py` | update |
| Frontend Implementation | `frontend/src/` | no-change |

## Execution Plan

- [x] Step 1: `/new-backend-spec` — updated `backend/specs/market-health/api.md`: added a
      new "Retry policy — transient provider errors, not just rate limits" paragraph under
      Business Logic — Classification, documenting that classification batches retry on
      HTTP 429 **and** 5xx/transient unavailability/connection errors/timeouts, mirroring
      the fetch step's already-documented policy. Updated both `IngestionRun.status =
      "partial"` cause descriptions (Data Models table and Scheduled ingestion agent
      section) to say "an unresolvable rate limit or other transient provider error."
- [x] Step 2: `/implement-backend` — updated `backend/src/classification.py`: renamed
      `_is_rate_limit_error()` to `_is_retryable_error()` and broadened it to also match
      `RETRYABLE_STATUS_CODES = {"429", "500", "502", "503", "504"}` plus
      `"unavailable"`/`"timeout"`/`"connection"` text, on top of the existing
      `"resource_exhausted"`/`"rate limit"` matches — mirroring `sources/base.py`'s
      `RETRYABLE_STATUS_CODES` used for the Greenhouse/Lever/Ashby fetch adapters.
      Renamed `RATE_LIMIT_RETRY_DELAY` → `RETRYABLE_ERROR_RETRY_DELAY` and updated the
      retry log message accordingly, since the delay is no longer rate-limit-specific.
      Verified with `py_compile`. Not re-tested live against a real Gemini 503 (would
      require forcing that condition); confirmed by code review against the exact
      failure captured in the 2026-08-03 test-run logs, same verification approach used
      for the 2026-07-27 Adzuna precedent.

## Decision Log
- 2026-08-03: Tracked against `understand-market-health-before-searching`, matching the
  2026-07-27 Adzuna ingestion resilience change — same outcome, same reasoning (pipeline
  continuity), same pipeline, just the classification step instead of the fetch step.
- 2026-08-03: Classified `bug-fix` + `technical-refactor`, not `api-change` — no endpoint
  contract or data model changes, only internal fault-handling. No experience-spec cascade
  needed since nothing user-facing is affected.
- 2026-08-03: Spec update precedes implementation (not skipped) because the spec currently
  describes classification's stop-early behavior narrowly ("an unresolvable rate limit")
  when the actual intent, per the fetch step's already-documented pattern, is broader —
  formalizing the broadened policy avoids the spec and code drifting apart again.
