---
id: cross-run-daily-budget-gap
date: 2026-08-05
trigger-type: internal
change-type: bug-fix, technical-refactor
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Cross-run daily LLM budget tracking + explicit "only new" guarantee

## Signal
See: `research/2026-08-05-cross-run-daily-budget-gap.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md`

Same outcome and pipeline as `changes/2026-07-27-adzuna-ingestion-resilience.md`,
`changes/2026-08-03-classification-transient-error-retry-gap.md`, and
`changes/2026-08-04-classification-llm-call-reduction.md` — market data must stay current
without the pipeline silently breaking itself against a known external constraint. This
change closes a gap in the most recent of those: the per-run budget cap doesn't actually
protect the real daily ceiling once more than one run happens in a day.

## Change Type
`bug-fix` — `backend/specs/market-health/api.md`'s Business Logic — Classification already
states the intent: `MAX_BATCHES_PER_RUN` exists "sized with headroom under the
20-requests/day ceiling." That statement is only true for a single run per day. Manual
"Run now" testing this week triggered multiple runs on the same day, each independently
getting its own fresh 12-batch allowance — meaning the *actual* behavior (up to 24 batches
attemptable across two same-day runs) already contradicts the spec's stated intent (stay
under 20/day). This is a real, found gap, not a hypothetical — narrowly avoided this week
by luck, not by design.
`technical-refactor` — no user-facing behavior change; every number involved becomes an
explicit, configurable constant rather than an implicit assumption.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | no-change — purely backend/ops, nothing user-facing changes |
| Backend Spec | `backend/specs/market-health/api.md` | update — (a) Business Logic — Classification — Per-run classification budget: redefine as a **cross-run daily** budget, not per-invocation, with configurable `DAILY_REQUEST_BUDGET`/`RETRY_HEADROOM` constants; (b) Data Models — IngestionRun: new `llm_requests_used` field (actual requests made, including retries — the real quantity that matters for quota, distinct from `llm_classified` which counts successfully-classified titles); (c) Data Models — RawPosting/Classification: make explicit, as a stated invariant, that "only new postings are ever stored/classified" is enforced at the database level (`raw_postings.id` PRIMARY KEY, `classifications.posting_id` UNIQUE), not just application logic — this part confirms and documents an already-true guarantee, no behavior change |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | no-change |
| Backend Implementation | `backend/src/classification.py`, `backend/src/db.py`, `backend/src/ingestion_runs.py`, `backend/src/ingest.py` | update |
| Frontend Implementation | `frontend/src/` | no-change |

## Execution Plan

- [x] Step 1: `/new-backend-spec` — updated `backend/specs/market-health/api.md`: added a
      new "Cross-run daily budget" Business Logic paragraph (redefines the budget as
      cross-run/daily, introduces `DAILY_REQUEST_BUDGET`/`RETRY_HEADROOM`, names
      `llm_requests_used` as the field it's computed from, documents UTC-calendar-day as a
      deliberately conservative boundary); added `llm_requests_used` to Data Models —
      IngestionRun; added the explicit DB-enforced "only new" invariant to both
      `raw_postings.id` and `classifications.posting_id` (citing the verification done
      2026-08-05); added a Tech Decisions entry for the two new named constants. Also fixed
      a side-effect: correctly updated the `raw_postings.id` field's stale reference to
      still-existing "legacy Adzuna rows" now that those rows were deleted earlier today
      (`changes/2026-08-05-adzuna-data-removal.md`).
- [x] Step 2: `/implement-backend` — implemented across 4 files, verified with `py_compile`,
      a runtime import check, a live functional test of the clamp arithmetic, and a live
      test of the new SQL query against the real database:
      - `classification.py`: added `DAILY_REQUEST_BUDGET=20`/`RETRY_HEADROOM=8` constants;
        `_complete_with_retry`/`classify_batch` now accept a mutable `request_counter` dict,
        incremented once per actual API attempt (success or failure, including retries);
        `classify_postings()` gained an `already_used_today` parameter and computes
        `effective_batch_cap = max(0, min(MAX_BATCHES_PER_RUN, DAILY_REQUEST_BUDGET -
        RETRY_HEADROOM - already_used_today))`, replacing the static per-run cap; returns
        the new `llm_requests_used` stat.
      - `db.py`: added `llm_requests_used INTEGER NOT NULL DEFAULT 0` to `ingestion_runs`,
        same idempotent migration pattern; applied live via `init_schema()`.
      - `ingestion_runs.py`: `record_run()` accepts and persists `llm_requests_used`; added
        `get_requests_used_today()` (sums `llm_requests_used` across today's UTC-calendar-day
        runs) — tested live, returns 0 as expected (no runs have used the new column yet).
      - `ingest.py`: calls `get_requests_used_today()` before classification and passes it
        in; threads `stats["llm_requests_used"]` into `record_run()`.
      - Functional verification of the actual fix: simulated `already_used_today` values
        0/5/11/12/15/20/25 all produced correct clamped results (12/7/1/0/0/0/0 respectively)
        — confirms a second same-day run now correctly sees a reduced-or-zero budget instead
        of a fresh 12-batch allowance, directly closing the gap this change targets.
      - "Only new" guarantee (Thing 2): confirmed already true, no code change made — see
        Step 1's spec documentation and the direct empirical verification done earlier
        (zero duplicate ids, zero double-classified postings, checked by id and by
        content-hash comparison of full raw_response and description text).

## Decision Log
- 2026-08-05: Tracked against `understand-market-health-before-searching`, same lineage as
  the three prior pipeline-reliability changes — same outcome, same pipeline, closing a gap
  in the most recent one rather than opening new scope.
- 2026-08-05: Deferred the full rich-sampling redesign (classification + salary + skills
  per posting, ~360/day ceiling) discussed earlier — real data showed steady-state new
  posting volume (~30-46/day) is far below what would justify that bigger change right now.
  Revisit if the tracked company list grows substantially or steady-state volume changes.
- 2026-08-05: Classified `bug-fix` (not purely `technical-refactor`) because the spec
  already stated an intent ("headroom under the 20-requests/day ceiling") that current
  behavior doesn't actually deliver once multiple runs happen per day — this is correcting
  a defect against an existing stated intent, not just refactoring for its own sake.
- 2026-08-05: `llm_requests_used` tracks actual requests (including retries), not
  `llm_classified` (successfully-classified titles) — a batch that needed 3 retries before
  succeeding consumes 3 requests against the real quota even though it only produces 1
  batch's worth of classifications; conflating the two would undercount real usage and
  reopen the exact gap this change fixes.
- 2026-08-05: UTC calendar day chosen as the "daily" boundary despite not being confirmed as
  Gemini's actual quota reset time — deliberately conservative (a safety margin, not a
  precision requirement), consistent with how this pipeline has always erred toward
  under-using the budget rather than assuming the most generous interpretation of an
  unconfirmed constraint.
- 2026-08-05: Confirmed via direct code review that "only store/classify new postings" is
  already true and enforced at the database level (not just application logic) — this part
  of the change request is documentation/confirmation only, explicitly not new code, to
  avoid inventing work that isn't needed.
