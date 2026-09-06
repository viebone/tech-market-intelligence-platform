---
id: requirements-backlog-batch-catchup
date: 2026-09-01
trigger-type: internal
change-type: new-feature, api-change
outcome: understand-market-health-before-searching
status: in-progress
---

# Change Request: Self-healing Batch catch-up for the requirements-extraction backlog

## Signal
See: `research/2026-09-01-requirements-backlog-batch-catchup.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md`

Its success criterion *"they can identify which roles and **skills** are in demand
vs. declining"* depends on requirements/skills extraction being reasonably
complete. A standing 1,651-posting extraction backlog (Engineer-heavy) directly
undermines it — skill-demand answers are computed from `posting_skills`, which
only exists for postings that have been through extraction.

Secondary outcomes touched:
- `pipeline-processing-visibility` — a batch job is a new pipeline activity an
  operator must be able to see and see fail.
- `ai-provider-flexibility` — the batch capability is a **new provider
  capability** and must obey that outcome's rules: named explicitly at the call
  site, one adapter per provider, swapping the batch provider is a one-line
  change, pipeline code never imports a provider SDK. "Tomorrow it can be
  switched to a different batch API" is a hard design requirement, not a
  nice-to-have (stakeholder, 2026-09-01).
- `llm-spend-is-bounded-and-isolated` — cost is bounded by this CR's own
  self-contained cap; it does **not** depend on that outcome's spend-ledger work
  (see Decision Log).

## Change Type
`new-feature` (Gemini Batch API capability, new `batch_jobs` table, new pipeline
phase) + `api-change` (new data model, new `ingest.py` business logic).

Not user-facing in the UI sense — no consumer screen changes. It changes what
data the existing `query_requirements_data` tool and market-health views can draw
on (more complete), and it adds operator-visible pipeline state.

## Design (agreed in principle — the spec nails the details)

### The mental model (keep it this simple)

> The daily run does as much interactive work as its **cost cap** allows.
> Whatever it couldn't get to is the **backlog**. The backlog is drained through
> the **cheaper batch lane**, one job at a time, also under a cost cap.

Nothing new conceptually — the daily cap (`MAX_BATCHES_PER_RUN`) already exists
for cost control. The only new idea: the work the cap defers goes to batch
instead of just waiting for tomorrow's cap to free up. Batch is ~50% of
interactive price, so draining via batch is the cost-minimising path; it also
sidesteps the interactive-endpoint congestion that created today's backlog.

### Provider-agnostic batch abstraction (hard requirement)

A new capability in the `llm/` layer, parallel to `LLMProvider`:

```
llm/base.py        BatchProvider protocol — submit(requests) -> job ref;
                   poll(job ref) -> state; fetch(job ref) -> results.
                   Provider- and model-named explicitly at the call site.
llm/gemini.py      GeminiBatchAdapter implements BatchProvider (Gemini Batch API).
llm/providers.py   providers.batch("gemini", model) factory — the ONE line that
                   changes to switch providers.
```

Pipeline code (`ingest.py`, the requirements module) imports **only** the
protocol — never `google.genai`, never a Batch-API-specific type. Swapping to
OpenAI Batch / Anthropic Message Batches later = one new adapter file + one
factory line, zero pipeline changes. This is `ai-provider-flexibility` applied
to a second capability.

### The `ingest.py` requirements phase becomes three steps

1. **Collect** — for the in-flight `batch_jobs` row, if any: ask the
   `BatchProvider` for state. Finished → fetch results, run them through the
   **same** parse/validate/insert path the interactive extractor uses, mark
   `collected`. Provider-failed → mark `failed`, record per-posting failures;
   those postings stay in the normal backlog.
2. **Interactive extraction** — unchanged. Its per-run cap is the cost cap.
3. **Maybe submit one batch** — if `backlog >= REQUIREMENTS_BATCH_MIN_BACKLOG`
   (a floor, so we never submit a trivially small batch) **and** no `batch_jobs`
   row is `submitted`/`running`:
   - take up to `MAX_BATCH_POSTINGS` oldest-first
   - estimate tokens → USD; **abort without submitting** if `> MAX_BATCH_USD`
   - **write the `batch_jobs` row, then submit** — never the other way round
     (Batch API is not idempotent; a crash after submit but before record must
     be reconcilable, not a silent double-charge)
   - at most one job per run

### `batch_jobs` table

`id`, `provider` (`"gemini"`), `model`, `provider_job_ref`, `purpose`
(`"requirements"` today — generic for future classification/reprocess use),
`state` (`submitted`/`running`/`collected`/`failed`), `item_count`,
`est_cost_usd`, `actual_cost_usd` (nullable), `submitted_at`, `completed_at`,
`error`.

### Shared extraction path — no duplication

`requirements.py` is refactored so prompt-build → `_parse` → `_validate` →
`insert_requirements` is one callable path used by **both** the interactive
extractor and the batch collector. The two lanes must produce identical
`posting_requirements` rows; the only legitimate difference is the `model`
provenance value. This refactor is a deliverable, not a side effect — see
Execution Plan Step 4.

### Not in scope for now

Classification backlog is 0, so `purpose` is `requirements` only. The table and
`BatchProvider` are designed so classification or a taxonomy-reprocess batch is
a later addition, not a redesign.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change (skills completeness already a criterion) |
| Outcome | `outcomes/pipeline-processing-visibility.md` | no-change (batch state fits its existing "see what ran / see failures" scope) |
| Outcome | `outcomes/ai-provider-flexibility.md` | no-change (the `BatchProvider` abstraction is this outcome working as intended) |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change (operator surface already outside the IA model) |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/pipeline-visibility/experience.md` | **update** — Overview + Ingestion Runs views surface batch-job state (in flight / last completed / failed); batch failures appear in the existing failure surfaces |
| Experience Spec | `design/market-health/experience.md` | review — expected no-change (requirements sourcing rule unchanged; only data coverage improves) |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | no-change |
| Frontend Spec | `frontend/specs/pipeline-visibility/` | n/a — server-rendered, no frontend spec (see `changes/2026-08-13-admin-pipeline-dashboard.md`) |
| Backend Spec | `backend/specs/market-health/api.md` | **update** — `BatchProvider` protocol (provider-agnostic); `batch_jobs` data model; the 3-step `ingest.py` requirements phase; threshold/cap constants; record-then-submit idempotency + reconciliation; cost-estimate + abort path; the shared interactive/batch extraction path |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | **update** — batch-job state on the Overview page + Ingestion Runs history (routes/fields); how a `failed` batch renders |
| Backend Implementation | `backend/src/` | **update** — `llm/base.py` (`BatchProvider` protocol); `llm/gemini.py` (`GeminiBatchAdapter`); `llm/providers.py` (`providers.batch(...)` factory); `db.py` migration (`batch_jobs`); `batch_jobs.py` module; **shared prompt/parse/validate/insert path** extracted from `requirements.py`; `ingest.py` phase wiring; `admin_templates/` for the batch-state display |
| Frontend Implementation | `frontend/src/` | no-change |

## Execution Plan

- [~] **Step 0 — carried over from `chat-free-tier-key-isolation`.**
  `job-sync` deploy `4bb35f10` (commit `f230302`, incl. the `ddb68b3` pin)
  succeeded 2026-09-02 12:36 UTC — pinned `gemini-3.6-flash` code is live.
  **Pending:** the first cron run after this (2026-09-03 06:00 UTC) should stamp
  new `posting_requirements` rows `model = gemini-3.6-flash`. Also in this CR's
  scope: fix the observability gap — a requirements-extraction crash must be
  distinguishable from "nothing to do" in the `ingestion_runs` row.
- [x] **Step 1 — `/new-experience`.** ✅ 2026-09-02. Revised
  `design/pipeline-visibility/experience.md` in place: new framing note (two
  extraction lanes, both pipeline-owned, dashboard just makes combined state
  legible); Overview gets a backlog count + batch-status line ("Batch running /
  Last batch / Batch failed / No batch needed"); Ingestion Runs rows + detail
  show per-run batch activity (collected / submitted / errored); batch state
  added to the status-indicator colour rules (neutral in-flight, emerald
  complete, red failed); 5 new edge cases incl. the interactive-crash
  observability gap; new eval metric "is the backlog draining or stuck? < 15s".
  No new operator controls — stays read-only. `directive: low` unchanged.
  **`design/market-health/experience.md` — no change (checked):** its
  requirements-answer honesty rule (User Flow 7b, line 285 — "reports
  proportions… states the sample size… never an absolute claim") already
  degrades gracefully on sparse data; more coverage via batch only improves the
  inputs, it doesn't change how answers are phrased or sourced.
- [x] **Step 2 — `/new-backend-spec`.** ✅ 2026-09-02. `backend/specs/market-health/api.md`:
  new Data Model **BatchJob** (`batch_jobs`) with a full state-machine table
  (incl. reconciliation rows for failed-submit and stuck-running) + orphan
  detection; new `ingestion_runs` fields `requirements_phase` (5 values, closes
  the crash-vs-idle gap), `batch_collected`, `batch_submitted_id`; new Business
  Logic section **Requirements extraction — Batch catch-up lane** (3-step phase,
  cost estimate, `MAX_BATCH_USD` abort, record-then-submit, budget independence,
  provenance, generality); Tech Decisions — **`BatchProvider` protocol** (its own
  Protocol, provider-neutral dataclasses, `providers.batch(...)` factory, grep
  acceptance check) + **shared extraction path** + batch-catch-up **constants**
  (`REQUIREMENTS_BATCH_MIN_BACKLOG` ~100, `MAX_BATCH_POSTINGS` ~500,
  `MAX_BATCH_USD` ~$1.00, dated price constants); `init_schema()` migration note;
  External Dependencies (batch API used only in `llm/gemini.py`);
  `backend/BATCH_PROCESSING.md` required.
  `backend/specs/pipeline-visibility/api.md`: `GET /admin/` gets a
  `requirements_backlog` block (count via `get_all_needing_requirements()` +
  current `batch_jobs` state + `expected_by`); `/admin/runs` + `/admin/runs/{id}`
  get per-run batch activity and the `requirements_phase` failure marker; Data
  Models + Business Logic note it reads `batch_jobs` (owned by market-health spec)
  and never writes it.
- [x] **Step 3 — `/new-frontend-spec`.** ✅ N/A confirmed. No consumer-facing
  frontend change (SSE contract, market-health views untouched). The admin
  dashboard is server-rendered Jinja in `backend/src/admin_templates/` — it has
  no `frontend/specs/` entry by design (`changes/2026-08-13-admin-pipeline-dashboard.md`).
  Template changes are covered by the pipeline-visibility backend spec + Step 4.
- [x] **Step 4 — `/implement-backend`.** ✅ 2026-09-02 (commit `01f9a23`):
  - `llm/base.py`: `BatchProvider` Protocol + `BatchRequest`/`BatchResult`/
    `BatchState` neutral types. `llm/gemini.py`: `GeminiBatchAdapter` (inlined
    requests, `JobState`→neutral-state map, `submit`/`poll`/`fetch`).
    `llm/providers.py`: `providers.batch(provider, model, api_key=)` +
    `_BATCH_ADAPTERS` registry.
  - `requirements.py`: shared `parse_and_validate()` path (each entry validated
    against its own posting's skill-groups) used by both `extract_batch()` and
    the batch collector; `insert_requirements(entries, model=…)`;
    `_prep_postings()`; batch constants + `estimate_batch_cost_usd()` +
    `build_batch_requests()` + `collect_batch_results()`.
  - `raw_postings.py`: `count_needing_requirements()`,
    `get_all_needing_requirements(limit=…)`, `get_postings_by_ids()`.
  - `batch_jobs.py`: new module — `create_job` (row-before-submit),
    `set_provider_ref`, `mark_running/collected/failed`, `get_active_job`,
    `get_latest_job`, `reconcile()` (failed-submit + stuck-running).
  - `db.py`: `batch_jobs` table + `ingestion_runs.requirements_phase` /
    `batch_collected` / `batch_submitted_id` (idempotent). Migrated on prod.
  - `ingest.py`: `run_requirements_phase()` — 3 steps (collect → interactive →
    maybe-submit), `_severest_phase()`, `_maybe_submit_batch()` (floor + in-flight
    guard + estimate + `MAX_BATCH_USD` abort + record-then-submit). `record_run`
    + `list_runs`/`get_run` carry the new fields.
  - Admin: `_requirements_backlog_status()` in `admin_main.py`; overview.html +
    runs.html + run_detail.html show backlog count, batch status, per-run batch
    activity, `requirements_phase` failure markers.
  - `backend/BATCH_PROCESSING.md` written.
  - **Clean-code check passed:** `grep` for `google`/`genai`/batch-API types
    outside `llm/gemini.py` → zero hits. All modules compile.
  - **e2e verified 2026-09-02 against production DB + real Gemini:** interactive
    lane unchanged after the shared-path refactor; a real 30-posting batch job
    submitted (row-before-submit, ref persisted), polled to `succeeded` in ~5
    min, fetched + parsed + validated + inserted **30/30, 0 failures**, all
    stamped `gemini-3.6-flash`, `batch_jobs` row → `collected`. In-flight guard,
    cost estimate ($0.23 for 500), `MAX_BATCH_USD` abort path, and the
    `google`/`genai`-outside-`llm/gemini.py` grep (zero hits) all checked.
    Admin templates render.
- [x] **Step 5 — `/implement-frontend`.** ✅ N/A. No consumer frontend. The
  admin dashboard is server-rendered Jinja (`admin_templates/`); its batch
  additions are in `overview.html` / `runs.html` / `run_detail.html`, covered by
  Step 4. Template render smoke-tested (overview backlog line + batch badge,
  runs list, run detail all render 200).
- [x] **Step 6 — Verify against production.** ✅ 2026-09-02, manual e2e (a real
  batch job driven by hand, mirroring `run_requirements_phase()` step 1):
  - submit 30 postings → `batch_jobs` row written **before** the provider call,
    `provider_job_ref` persisted after ✓
  - in-flight guard: a second `_maybe_submit_batch()` returned `None` while the
    job was active ✓
  - poll `submitted`→`running`→`succeeded` (~5 min); `fetch` → 13 inline
    responses, 0 errors ✓
  - `collect_batch_results` → **30/30 inserted**, rows identical shape to the
    interactive lane (`work_arrangement`/`education_level`/… populated),
    `model = gemini-3.6-flash`, `posting_requirements_failures` untouched (0 rows
    for the job's postings) ✓
  - cost-estimate abort: `MAX_BATCH_USD = $0.0001` → `_maybe_submit_batch()`
    logged the refusal and created no job ✓
  - admin dashboard (`/admin/`, `/admin/runs`, `/admin/runs/{id}`) render the
    backlog line + batch state ✓
  - **Not yet observed:** the fully autonomous cron cycle (run submits a batch →
    next day's run collects it). Deployed to `job-sync` (`01f9a23`); first
    real check is cron run 51 (2026-09-03 06:00 UTC) submitting a 500-job batch,
    run 52 collecting it.
- [ ] **Step 7 — Close.** Mark `complete` after cron runs 51–52 show the
  autonomous submit→collect cycle and the backlog visibly dropping (~1,597 → ~0
  over ~3–4 cycles), and the `chat-free-tier-key-isolation` Step 0 carry-over
  (a `job-sync` run stamping `gemini-3.6-flash`) is confirmed — run 50 was on
  the old alias code; run 51 is the first on `ddb68b3`+.

  **Status check 2026-09-06 (`batch_jobs` + `ingestion_runs` inspected directly):**
  - The autonomous cycle **is** working. Job 2 (09-03, 500) collected by run 52-ish;
    job 3 (09-04, 500) collected by run 53 (`batch_collected: 485`). `gemini-3.6-flash`
    is being stamped (carry-over confirmed).
  - Tracked-role backlog (Designer/PM/Engineer postings with no `posting_requirements`
    row — the metric this CR's "~1,597" referred to) is now **697**, down from ~1,597.
    On track, slightly slower than the 3–4-cycle estimate. (The raw "no requirements
    row" count is 4,024, but 3,327 of those are `other`/`unknown` and are out of scope
    by design — extraction only runs for tracked roles.)
  - **Transient stall:** run 54 (09-06) threw collecting job 4 (submitted 09-05) →
    `requirements_phase: batch_collect_failed`, job 4 still `submitted`. Because the
    in-flight guard (`get_active_job()`) then blocks `_maybe_submit_batch()`, run 54
    also submitted no new job. Job 4 was polled by hand 09-06 17:50 — it **succeeded
    provider-side**, `fetch()` returns all 267 result groups cleanly, so the collect
    path is healthy; run 54's failure looks transient (network blip / batch not ready
    at the ~24h mark). **Decision (stakeholder, 2026-09-06): wait for run 55
    (09-07 06:00 UTC) to self-heal** — it should collect job 4 and submit job 5. If
    run 55 also fails to collect/submit, that is a real bug → new CR. `reconcile()`
    fails job 4 to the failures table at +72h (09-08 06:07) if still stuck — the
    outcome to avoid.
  - **Design smell noted for a possible follow-up CR:** one transient collect error
    blocks batch submission for up to 72h (≈3 cycles), because submission is gated on
    "no active job" even when that job is already `succeeded` provider-side.

## Documentation & code-quality bar (explicit acceptance criteria)

The stakeholder called out "very well documented and cleanly coded" as a
requirement. This CR is not done unless:

- **A `backend/BATCH_PROCESSING.md`** exists — plain-language, same style as
  `backend/AI_INTERACTION_SETTINGS.md`: what the daily cap is, why the backlog
  exists, what batch is, why it's cheaper, the 3-step phase, the cost caps, and
  how to switch batch providers. Numbers live in code, not duplicated in the doc.
- **The spec** (`backend/specs/market-health/api.md`) documents the
  `BatchProvider` contract and the state machine as first-class, not a footnote.
- **The code** is organised so each piece has one job: `llm/` = provider
  mechanics only; `batch_jobs.py` = state/persistence only; the shared extraction
  path = prompt/parse/validate/insert only; `ingest.py` = orchestration only.
  No provider SDK import outside `llm/`. Every non-obvious constant carries a
  one-line "why this value" comment, matching the existing `classification.py` /
  `requirements.py` convention.
- **The `batch_jobs` state machine** has a diagram or table in the spec showing
  every transition and what triggers it, including the failure/reconciliation
  paths.

## Decision Log
- 2026-09-01: Tracked against `understand-market-health-before-searching` (an
  existing outcome — skills-demand completeness is one of its success criteria),
  not a new outcome. `pipeline-processing-visibility` is a secondary touched
  outcome (operator visibility of batch state). User confirmed the outcome
  choice when requesting this CR.
- 2026-09-01: Change type `new-feature` + `api-change`. It adds a capability that
  does not exist (Batch API integration, `batch_jobs` state machine, new pipeline
  phase) and a new data model — more than a `technical-refactor`.
- 2026-09-01: **Design: daily interactive stays primary; Batch is a
  threshold-triggered catch-up**, not a replacement. Chosen over (a) raising the
  interactive daily budget — forbidden until the spend-ledger CR and still
  subject to `gemini-flash*` congestion — and (b) a one-off throwaway backfill
  script — the automated trigger shares ~90% of the code and also handles every
  future accumulation.
- 2026-09-01: **Does NOT depend on the spend-ledger follow-on CR.** A one-time
  job of known size is bounded by a pre-submit token→USD estimate + `MAX_BATCH_USD`
  abort + the $5 prepay backstop. The full interactive spend-ledger is about
  bounding *ongoing* per-call spend and can land before or after this.
- 2026-09-01: **Blocked on `changes/2026-08-29-chat-free-tier-key-isolation.md`
  closing first** — this builds on that CR's `gemini-3.6-flash` pins and the
  `GEMINI_API_KEY_REQUIREMENTS` → prepaid-project swap. That CR's step 7 awaits
  the 2026-09-02 06:00 UTC cron. No implementation here until it's `complete`.
- 2026-09-01: Batch API **not idempotent** — recorded as a hard constraint:
  `batch_jobs` row is written before the provider submit call, and every run
  reconciles (a row stuck `submitted` with no provider job = failed submit,
  safe to retry; a provider job with no row = orphan, alert).
- 2026-09-01: **Provider-agnostic batch abstraction is a hard requirement**, not
  an implementation nicety (stakeholder: "tomorrow it can be switched to a
  different batch API"). New `BatchProvider` protocol in `llm/base.py`; pipeline
  code imports only the protocol; switching providers = one adapter + one factory
  line. This is `ai-provider-flexibility` extended to a second capability, so
  that outcome is a third touched outcome (no spec change needed there — the
  work *is* the outcome).
- 2026-09-01: **Honest cost framing.** At today's volume the whole 1,651 backlog
  is ~$1 interactive / ~$0.50 batch — the absolute saving is small. The value
  now is reliability (routes around the interactive `gemini-flash*` congestion)
  and throughput (clears in ~4 cycles vs a ~2-week interactive drip). The
  *structural* value — "daily cap + batch the overflow" as the way cost stays
  bounded as company coverage / reprocessing volume grows — is the real
  long-term reason, and matches the stakeholder's mental model.
- 2026-09-01: **Mental model deliberately kept minimal** — "daily does what its
  cap allows; the rest is backlog; backlog drains through the cheaper batch
  lane." A separate `> 100` trigger was discussed and simplified to a
  `MIN_BACKLOG` floor (only there to avoid submitting a trivially small batch).
