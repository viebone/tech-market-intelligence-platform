---
id: batch-collect-fk-violation
date: 2026-09-09
trigger-type: bug
change-type: bug-fix
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Batch requirements collect aborts on a single stray posting id

## Signal

See: `research/2026-09-09-batch-collect-fk-violation.md`. Stakeholder: "the batches are
failing, why?" — the requirements batch catch-up lane's collect step had failed on every
cron run since 2026-09-06 (runs 54–56), leaving the lane stalled.

This is the "if run 55 also fails to collect/submit, that is a real bug → new CR" branch
anticipated in `changes/2026-09-01-requirements-backlog-batch-catchup.md` Step 7.

## Outcome

`outcomes/understand-market-health-before-searching.md` — the batch lane is how the
skills/requirements backlog drains, which backs "identify which roles and skills are in
demand". A stalled lane means the Requirements Signal stops improving. No success criterion
changes.

## Change Type

`bug-fix` — the spec is correct (`backend/specs/market-health/api.md` — Business Logic —
Requirements extraction: "Per-response errors and dropped postings get a
`posting_requirements_failures` row … never silently lost"). The code doesn't match it: a
malformed/stale id in the model's output isn't dropped, it FK-violates the whole insert.
Code-only fix, no spec change.

## Root Cause

`collect_batch_results` (`backend/src/requirements.py`) feeds every entry from
`parse_and_validate()` straight into `insert_requirements()`. `parse_and_validate()` keeps an
entry for any `id` the model echoes back — including one not in the job's real posting set
(the model occasionally invents/garbles an id; a days-old batch can also name a since-pruned
posting). `insert_requirements()` runs one `executemany` INSERT; a single row whose
`posting_id` has no `raw_postings` FK aborts the entire transaction → the collect throws
`ForeignKeyViolation`, nothing saves, the job stays `submitted`, and it repeats every run
until `reconcile()` force-fails it at +72h and dumps all 500 postings to the failures table.

## Fix

`collect_batch_results` filters `entries` to ids present in `vs_by_id` (which is built from
`postings` = the ids that still exist in `raw_postings`) before `insert_requirements`. A
skipped id needs no failure row — it was never a real posting, or it's already gone from the
backlog. One `logger.info` line for visibility.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Backend Spec | `backend/specs/market-health/api.md` | no-change — the spec already says dropped postings must not abort the batch |
| Backend Impl | `backend/src/requirements.py` — `collect_batch_results` | update |

## Execution Plan

- [x] Step 1: Diagnose from production (Railway `job-sync` logs, run 56) — `ForeignKeyViolation`
      in `insert_requirements` via `collect_batch_results`.
- [x] Step 2: `/implement-backend` — filter `entries` to live posting ids in
      `collect_batch_results` before the insert.
- [x] Step 3: Recover by hand — collected job 4 (499 rows) and job 5 (500 rows) with the
      fixed code; both marked `collected`; `insert_requirements` auto-cleared their 999
      `posting_requirements_failures` rows. Tracked-role backlog 652 → 152; failures 474 → 1.
- [x] Step 4: Commit + push (rebuilds `job-sync`'s image). Verify the next cron run (58,
      2026-09-10 06:00 UTC) collects job 6-or-later cleanly.
- [x] Step 5: Update `changes/2026-09-01-requirements-backlog-batch-catchup.md` Step 7 with
      the diagnosis and this CR reference.

## Decision Log

- 2026-09-09: `bug-fix`, code-only. The spec's "dropped postings → failure row, never abort"
  rule is right; the code's all-or-nothing `executemany` insert violated it whenever the
  model output carried one bad id. Filtering to the known-live id set is the minimal fix and
  matches how the interactive lane already scopes its work.
- 2026-09-09: Recovered job 4's results by hand rather than letting its 500 postings churn
  back through the backlog — Gemini still had the (already-paid-for) batch output, and the
  fixed collector ingested 499/500 in one call.
- 2026-09-09: The `reconcile()` 72h timeout did its job as a backstop (no infinite stall),
  but 3 wasted cron cycles + a 500-row failure dump is a poor outcome for one bad id. The
  real fix is not aborting on it. Not touching `BATCH_STUCK_AFTER_HOURS` here.
