---
id: fold-reprocessing-into-ingest
date: 2026-09-21
trigger-type: user-feedback
change-type: technical-refactor
outcome: llm-spend-is-bounded-and-isolated
status: complete
---

# Change Request: Fold taxonomy backlog reprocessing into ingest.py's daily run

## Signal
See: `research/2026-09-21-fold-reprocessing-into-ingest.md`.

## Outcome
See: `outcomes/llm-spend-is-bounded-and-isolated.md` — this is a `technical-refactor`
(restructuring *where* reprocessing runs, no user-facing change, no new data) whose real risk
is exactly what that outcome exists to guard: a combined-step run silently spending past the
daily LLM request ceiling, the same shape of gap as the cross-run budget bug that outcome's own
signal already names, just within one run instead of across separate runs. No success criteria
change needed — this is enforcing the existing "cap enforced before each call, not reconciled
after" criterion in a new place, not adding a new one.

## Change Type
`technical-refactor` — no experience-spec/IA/visual-design impact. `backend/specs/market-health/
api.md`'s Business Logic section needs a note (structure changed: reprocessing now happens
inside the daily ingestion run, not only via the standalone script).

## What changes
`backend/src/ingest.py::run()` gains a step, right after `classify_postings()` and before the
requirements phase:
1. Check `raw_postings.get_all_for_reclassification()` — if empty (the overwhelming majority of
   days), do nothing further, at the cost of one fast query.
2. If non-empty, call `classification.reclassify_all()` with `already_used_today =
   get_requests_used_today() + stats["llm_requests_used"]` — carrying forward *this run's own*
   classification spend, not just prior runs' — before computing the daily budget still available.
3. Skipped entirely if `classify_postings()` itself already `stopped_early` this run (a real
   provider error, not a clean budget stop) — don't pile more retries onto a day that's already
   failing.
4. If anything was actually reclassified, delete now-stale `posting_requirements` rows
   (`raw_postings.get_requirements_reprocess_targets(TAXONOMY_VERSION)` +
   `requirements.delete_requirements_for_reprocess()`) *before* the requirements phase runs —
   letting the same run's requirements extraction pick them back up immediately, rather than
   waiting for tomorrow's run the way the two-separate-scripts version did.
5. Reprocessing stats are summed into the run's existing `total_classified`/`cache_hits`/
   `heuristic_filtered`/`llm_classified`/`other_count`/`llm_requests_used` fields — no new
   `IngestionRun` columns. `stopped_early`/`budget_reached` are OR'd across both steps.

`reprocess_taxonomy.py` is kept, unchanged — still useful for a deliberate, immediate, one-off
manual run (e.g. to check progress mid-day) without waiting for tomorrow's cron.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Backend Spec | `backend/specs/market-health/api.md` | update — Business Logic note: reprocessing now also runs inside the daily ingestion run |
| Backend Implementation | `backend/src/ingest.py` | update — new reprocessing step in `run()` |
| Everything else | — | no-change |

## Execution Plan

- [x] Step 1: Implemented the new step in `ingest.py`, carrying forward this-run's own spend correctly
- [x] Step 2: Verified the branching logic directly against real production data (not a full end-to-end run, which would trigger real external fetches unnecessarily) — confirmed today's already-exhausted budget (12/20 used, 8 headroom reserved) correctly makes the new step a true no-op (`llm_requests_used: 0`, `budget_reached: True`) rather than double-spending
- [x] Step 3: Updated `backend/specs/market-health/api.md` — Business Logic note
- [x] Step 4: Commit and push

## Decision Log
- 2026-09-21: Folded into `ingest.py` rather than giving `reprocess_taxonomy.py` its own
  permanent Railway cron — avoids adding a new service and structurally avoids the "empty runs
  clutter the Runs admin view" concern, since no new `ingestion_runs` row is added, only more
  detail on the row `ingest.py` already writes daily.
- 2026-09-21: `reprocess_taxonomy.py` kept as a manual escape hatch, not deleted — still useful
  for checking progress mid-day without waiting for the next cron tick.
