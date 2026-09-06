---
id: unknown-reclassification
date: 2026-09-06
trigger-type: stakeholder-request
change-type: api-change, technical-refactor
outcome: understand-market-health-before-searching
status: triaged
---

# Change Request: Description-assisted recovery pass for `role_category = 'unknown'`

## Signal

See: `research/2026-09-06-unknown-reclassification.md`

## Outcome

`outcomes/understand-market-health-before-searching.md` — "they can identify which roles and
skills are in demand vs. declining". 136 postings sitting in `unknown` are 136 real tech
postings missing from the Designer / Product Manager / Engineer trend counts. Recovering the
ones that are resolvable makes the demand read more complete.

## Change Type

- `api-change` — the classification method gains a **description-assisted fallback** for
  `unknown`, distinct from the title-only main path. `design/market-health/job-classification.md`
  (Unknown vs. Other) already anticipates this: "a high `unknown` rate ... might mean the
  title-only classification rule ... needs a fallback."
- `technical-refactor` — a one-time reprocessing operation (a manual script, same "run now,
  safe to re-run" pattern as `reprocess_taxonomy.py`), not new daily-pipeline behaviour.

## The design

- **Scope:** every posting currently `role_category = 'unknown'`. Title-only re-runs are
  pointless (same input → same `unknown`), so this pass sends the model **title + a snippet
  of the job description** (extracted from `raw_postings.raw_response` per source, the same
  way requirements extraction already does).
- **Mechanism:** the **Gemini Batch API** (`GeminiBatchAdapter` via `providers.batch`), on
  `GEMINI_API_KEY_CLASSIFICATION` (the classification prepaid project). A one-time job of
  ~136 short items — Batch API pricing, does not consume the interactive daily request quota.
- **A posting the description still can't disambiguate stays `unknown`** — genuinely
  ambiguous, not a failure. A posting that turns out not to be a tracked role becomes `other`.
- Resolved rows are `UPDATE`d in place (bump `classified_at`, `model` marks the
  description-assisted path, `taxonomy_version` stays current). `unknown`/`other` outcomes
  are also written so the pass is idempotent — a re-run only re-attempts rows still `unknown`
  *and* not yet touched by this pass.
- **Not in scope:** wiring a description fallback into the daily pipeline. If the ongoing
  `unknown` rate warrants it later, that is a follow-up.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change — no success criterion moves; the trends just get more complete |
| Outcome | `outcomes/llm-spend-is-bounded-and-isolated.md` | no-change — uses the existing classification prepaid key; a one-time ~136-item Batch job is well inside the framing, and Batch API pricing is cheaper than interactive. Note only. |
| Design — Classification | `design/market-health/job-classification.md` | update — Classification Method: the description-assisted `unknown`-recovery fallback |
| Backend Spec | `backend/specs/market-health/api.md` | update — Business Logic — Classification: the unknown-recovery Batch pass (inputs, key, idempotency, `unknown`-stays-`unknown`) |
| Backend Implementation | `backend/src/classification.py`, new `backend/src/reclassify_unknowns.py` | update / create |
| Frontend | — | no-change |

## Execution Plan

- [ ] Step 1: `/new-backend-spec` — document the description-assisted unknown-recovery pass in
      `backend/specs/market-health/api.md` and the fallback in
      `design/market-health/job-classification.md`.
- [ ] Step 2: `/implement-backend` —
      - `classification.py`: a `classify_with_description()` path (title + description snippet
        → validated classification), reusing `_parse_response` / `_validate` /
        `update_classifications`; a `build_unknown_recovery_requests()` helper.
      - `reclassify_unknowns.py`: fetch unknowns + descriptions → submit one Batch job →
        poll to completion → apply results → print a summary. Safe to re-run.
- [ ] Step 3: Run it against production data; report how many `unknown` resolved, to what.
- [ ] Step 4: Commit + push (no deploy needed — a manual script, not pipeline code; but it
      ships with the repo).

## Decision Log

- 2026-09-06: Title-only re-run rejected — deterministic on the same input, would reproduce
  every `unknown`. The description is the only added signal that can move the needle, and the
  classification spec already flagged a "fallback" as the expected fix for a high `unknown`
  rate.
- 2026-09-06: Gemini **Batch API**, not synchronous batched calls — stakeholder asked for
  "gemini batch"; it is the right tool for a bulk reprocess (cheaper, off the interactive
  quota) and the pattern generalises if the `unknown` backlog grows.
- 2026-09-06: Self-contained one-time script with a blocking poll loop, **not** wired through
  the shared `batch_jobs` table — that table and `ingest.py`'s "one active job" guard are
  scoped to the requirements lane; a second concurrent purpose there would collide. The
  script prints its job ref so an interrupted run can be checked manually.
- 2026-09-06: `unknown` after seeing the description is a valid, kept outcome — not forced
  into a category. Same principle as the title-only path.
