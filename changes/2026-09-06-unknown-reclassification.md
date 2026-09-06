---
id: unknown-reclassification
date: 2026-09-06
trigger-type: stakeholder-request
change-type: api-change, technical-refactor
outcome: understand-market-health-before-searching
status: triaged
---

# Change Request: Description-assisted recovery pass for classification `unknown` fields

> **Scope broadened 2026-09-06** (stakeholder: "all unknown ... make sure this time works"):
> from `role_category = 'unknown'` only (136) to **every posting with any `unknown`
> classification field** — `role_category` / `specialization` / `level` / `track` — which is
> **1,574 postings**. Model bumped from `gemini-2.5-flash` to `gemini-3.6-flash`. Also adds a
> requirements re-extraction for the **103** extracted postings that have zero skills.
>
> **Taxonomy investigation (the stakeholder suspected "the internal taxonomy failing"):**
> checked — it isn't. All 6,694 classifications are on one `taxonomy_version` (`2026-08-11`).
> The 3,253 `other` rows sampled correctly (BDR, Customer Success, TAM, Corporate Counsel,
> Sales — genuinely not Designer/PM/Engineer). The `unknown` fields are the **title-only
> method hitting its documented ceiling**: `level = 'unknown'` for 1,026 rows is titles like
> "Software Engineer" / "Data Scientist" with no seniority word — the description almost
> always discloses it. Separate observation: `other` is ~49% of the dataset, which
> `job-classification.md` says signals a **sourcing/targeting** problem (the ingestion query
> is too broad) — not classification, and out of scope here.

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

### Classification recovery (`reclassify_unknowns.py`)

- **Scope:** every posting where `role_category`, `specialization`, `level`, or `track` is
  `'unknown'` — 1,574 today. Title-only re-runs are pointless (same input → same `unknown`),
  so this pass sends the model **title + a job-description snippet** (per-source extraction
  from `raw_postings.raw_response`, the same `_extract_description` requirements uses) and
  asks it to re-answer all five fields.
- **Model:** `gemini-3.6-flash` (bumped from 2.5-flash — the stakeholder questioned 2.5's
  quality). Via the **Gemini Batch API** (`GeminiBatchAdapter` / `providers.batch`), on
  `GEMINI_API_KEY_CLASSIFICATION` — Batch pricing (~$0.05 for 1,574), off the interactive
  daily request quota.
- **A field the description still can't disclose stays `unknown`** — genuinely not stated,
  not a failure. `role_category` becomes `other` if the description shows it's not a tracked
  tech role. Nothing forced.
- Rows are `UPDATE`d in place (`classified_at` bumped, `model` = `gemini-3.6-flash+description`
  as provenance + idempotency key, `taxonomy_version` unchanged). `unknown`/`other` outcomes
  are written too, so a re-run only re-attempts rows still carrying a gap that this pass
  hasn't already stamped. Bumping the model suffix in `classification.CLASSIFICATION_RECOVERY_MODEL`
  forces a redo with a newer model.

### Requirements re-extraction (`reextract_skilless.py`)

- **Scope:** the 103 postings with a `posting_requirements` row but **zero `posting_skills`**
  — a reliable "the extractor missed" signal. `not_mentioned` education / work-arrangement
  and NULL years-of-experience are **not** targeted — those are usually correct.
- Delete the requirements/skills/languages rows for those ids, re-extract via the Gemini
  Batch API on `GEMINI_API_KEY_REQUIREMENTS`, `collect_batch_results` inserts fresh rows.

### Not in scope

- Wiring a description fallback into the daily pipeline (a follow-up if the ongoing `unknown`
  rate warrants it).
- The 4,024 postings with no requirements row at all — that is the in-progress
  `requirements-backlog-batch-catchup` cron, left alone here.
- The broad `other` rate / ingestion targeting — a separate sourcing question.

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

- [x] Step 1: `/new-backend-spec` — documented the description-assisted recovery pass in
      `backend/specs/market-health/api.md` (Business Logic — Classification) and the fallback
      in `design/market-health/job-classification.md` (the spec already anticipated it).
- [x] Step 2: `/implement-backend` — `classification.py` (`RECOVERY_SYSTEM_INSTRUCTION`,
      `build_unknown_recovery_prompt`, `RECOVERY_MODEL` + `CLASSIFICATION_RECOVERY_MODEL`
      marker); `reclassify_unknowns.py` (any-gap fetch, batch submit/poll/apply,
      before/after gap report); `reextract_skilless.py` (the 103 zero-skill postings).
      Reuses existing `_parse_response` / `_validate` / `update_classifications` /
      `prep_postings` / `build_batch_requests` / `collect_batch_results`.
- [x] Step 3: Diagnostic pass — confirmed it is not the taxonomy (see the box at the top);
      1,574 gap postings, 103 zero-skill postings.
- [ ] Step 4: Run both against production data; report the before/after.
- [ ] Step 5: Commit + push (manual scripts, no deploy needed; they ship with the repo).

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
