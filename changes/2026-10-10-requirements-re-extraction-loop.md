---
id: requirements-re-extraction-loop
date: 2026-10-10
trigger-type: bug
change-type: bug-fix, api-change
outcome: llm-spend-is-bounded-and-isolated
status: in-progress
---

# Change Request: Stop the daily requirements re-extraction loop, and guard against paid repeat work

## Signal
See: `research/2026-10-10-requirements-re-extraction-loop.md`

## Outcome
See: `outcomes/llm-spend-is-bounded-and-isolated.md`. Directly relevant success criterion: "A
bug, an infinite loop, a retry storm, or an unusually large ingestion event cannot produce spend
beyond the ceiling". This loop is that bug. The ceiling held only because of the daily request
budgets and the $1-per-batch cap, not because anything noticed the work was pointless.

## Change Type
- `bug-fix`: the daily taxonomy-reprocessing step treats every posting as stale and deletes
  every requirements row. Root cause is **spec and code both**. `backend/specs/market-health/api.md`
  — Taxonomy reprocessing says the daily check is "one fast, empty query on the vast majority of
  days", but names `get_all_for_reclassification()`, which its own 2026-08-11 bullet defines as
  returning *every* posting. Its requirements-delete rule ("classification already on the new
  version") becomes "everything" once a migration finishes. The spec gets fixed first.
- `api-change`: new guardrails, so repeat paid work is blocked and visible whatever the cause,
  not just this one cause.

## Scope

### 1. The fix
- **Stale means stale.** The daily reprocessing check selects only postings whose
  classification is on an older `taxonomy_version` than `TAXONOMY_VERSION`. On a steady-state
  day that is zero rows, and the step does nothing. `get_all_for_reclassification()` stays
  available only to the manual `reprocess_taxonomy.py` escape hatch, renamed or documented so it
  can't be mistaken for a stale query again.
- **Clear requirements only where the classification actually changed.** Reprocessing records
  which postings' `role_category` / `track` / `specialization` changed in this pass. Only those
  postings' requirements are cleared, because only they would get a different skill-group list.
  A posting whose classification came back identical keeps its requirements.
- **Rewriting an unchanged classification is not "classified".** `reclassify_all` stops counting
  cache-identical rewrites in `total_classified`. Ideally it doesn't rewrite them at all.

### 2. Guardrails (so this class of bug can't silently recur)
- **Repeat-work circuit breaker (both extraction lanes).** Before submitting a batch or running
  the interactive lane, count how many selected postings have *already been extracted before*.
  That needs a small append-only record of successful extractions which deletes never touch,
  because `posting_requirements` itself is what gets deleted. If repeats exceed a threshold
  (default: >10% of the selection, or >50 postings) and there is no explicitly recorded
  reprocess request for them, **do not spend**. Record
  `requirements_phase = repeat_work_blocked`, log a warning, and leave the postings alone.
- **Bulk-delete cap.** `delete_requirements_for_reprocess()` refuses, in the daily path, to delete
  more than a small cap per run (default 200). A larger reprocess must go through the manual
  script with an explicit flag and a change request, which is how taxonomy migrations are meant
  to work anyway. The refusal is recorded on the run, not swallowed.
- **Admin visibility** (`backend/specs/pipeline-visibility/api.md`): per run, show postings
  re-extracted (repeats), requirements rows deleted, and any blocked phase, with a plain warning
  state when the breaker fires. Also show the existing batch history as distinct postings
  ÷ slots, so "500 slots, 12 new" is visible at a glance.
- **Regression tests** (plain asserts, same style as `backend/tests/test_curated_match.py`):
  - a steady-state day (every classification current) selects nothing to reprocess, deletes
    nothing, and re-extracts nothing;
  - a reprocess where 3 of 100 classifications change clears exactly those 3;
  - the circuit breaker blocks a selection made of already-extracted postings;
  - the delete cap refuses an oversized daily delete.

### Explicitly out of scope
- The app-level dollar spend ledger (real `actual_cost_usd`, monthly ceiling enforced before
  each call). Still the right long-term backstop and still unplanned. This CR adds a cheap,
  cause-agnostic tripwire, not the ledger.
- Sampling (`changes/2026-10-10-requirements-extraction-sampling.md`, paused at Step 4). It
  resumes after this ships, with real cost data.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/llm-spend-is-bounded-and-isolated.md` | no-change (existing criterion covers it; logged as an instance below) |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/pipeline-visibility/experience.md` | update. The admin dashboard gains the repeat-work / deleted-rows / blocked-phase state. Operator-facing, but the admin surface has an experience spec, so it changes first. |
| Experience Spec | `design/market-health/*` | no-change. No end-user-visible change, beyond requirements data surviving more than one day. |
| Backend Spec | `backend/specs/market-health/api.md` | update. Fix the Taxonomy reprocessing section (stale query, changed-only clearing), and add the circuit breaker, delete cap and extraction record. |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | update. New per-run fields and batch distinct-vs-slots. |
| Frontend Spec | `frontend/specs/*` | no-change. The admin dashboard is server-rendered by the backend (`admin_templates`); confirm in Step 3. |
| Backend Implementation | `backend/src/` | update (`ingest.py`, `raw_postings.py`, `classification.py`, `requirements.py`, `batch_jobs.py`/`ingest._maybe_submit_batch`, `db.py`, `ingestion_runs.py`, admin dashboard, `backend/tests/`) |
| Frontend Implementation | `frontend/src/` | no-change |
| Plain-Language Overview | `OVERVIEW.md` | no-change (bug-fix plus an operator-only safeguard) |
| MCP Access Review | `ACCESS.md` | no-change. No new or changed user-facing capability. The admin run fields are operator telemetry and were never MCP-exposed. Confirmed explicitly, not assumed. |
| Polite Scraping Review | `DATA_SOURCES.md` | not-applicable |
| Data Surface Review | — | not-applicable. The extraction record is pipeline bookkeeping, not a new kind of market fact. |

## Execution Plan

- [x] ✅ Step 1: **Stop the bleeding first, with the owner's go-ahead.** Ship the minimal fix
      (stale-only selection plus changed-only clearing) before the next 06:00 UTC cron. Otherwise
      tomorrow's run deletes today's results again, including batch job 31's. The spec edit for
      this part is done in the same step and is small, but it comes first.
- [x] ✅ Step 2: Update `design/pipeline-visibility/experience.md` (admin states for repeat work,
      deletes, blocked phase).
- [x] ✅ Step 3: `/new-backend-spec`. Update `backend/specs/market-health/api.md` (circuit breaker,
      delete cap, extraction record) and `backend/specs/pipeline-visibility/api.md`. Confirm the
      admin dashboard is backend-rendered (no frontend spec).
- [x] ✅ Step 4: `/implement-backend`. Guardrails, admin fields, regression tests.
- [ ] Step 4b (added 2026-10-23): Deploy the guardrails (`job-sync`, `admin`; `api` restarts
      too on any push) with the owner's go-ahead. Run `migrate_extraction_ledger.py` once, then
      verify the next cron run:
      - the new `ingestion_runs` columns are filled;
      - `requirements_guard = ok`, with paid = new + repeats and repeats = 0;
      - the admin Overview shows the Paid work check line;
      - batch history shows distinct postings in slots.
- [x] ✅ Step 5: Verify in production over two runs (done 2026-10-13; see Decision Log):
      - 0 reprocess deletes on a steady-state day;
      - `posting_requirements` grows day over day (no more resets to ~500);
      - distinct postings per batch job = slots;
      - the backlog actually falls.
- [x] ✅ Step 6: Resume `changes/2026-10-10-requirements-extraction-sampling.md` Step 4 with the
      owner, re-deciding urgency and cap using real post-fix numbers.
- [x] ✅ Step 7 (framework, owner approved 2026-10-11): propose a framework-level rule so "a
      steady-state recurring run does no paid and no destructive work" is checked for every
      product, not only remembered in this one. See Decision Log.

## Decision Log
- 2026-10-10: Classified `bug-fix` with the spec also wrong (it names a whole-corpus helper as
  the daily stale check), plus `api-change` for the guardrails. The owner asked explicitly that
  "things like this don't happen again". A fix alone would only prevent this one path, so the
  guardrails are cause-agnostic: they detect paying twice for the same posting, whatever caused
  it.
- 2026-10-10: Anchored to `llm-spend-is-bounded-and-isolated` with no outcome change. Its
  "infinite loop … cannot produce spend beyond the ceiling" criterion already covers this.
- 2026-10-10: **Why nothing caught it.**
  - The daily request budgets and the $1-per-batch cap bounded the rate of spend, not the
    usefulness of it. They worked as designed while the money bought nothing.
  - Nothing compares "postings paid for" with "new postings gained". `batch_collected = 500`
    looked healthy every day.
  - `actual_cost_usd` is never filled in.
  - A one-time helper (`get_all_for_reclassification`) was reused in a recurring job without its
    semantics being re-read. Its name says "all", and its docstring says "one-time".
- 2026-10-10: Note for memory and docs: the monthly ceiling was raised to **$10** on 2026-09-27
  (`changes/2026-09-27-llm-budget-raised-to-10.md`), close to when this loop began repeating
  daily. Real headroom was spent on repeat work.
- 2026-10-10: Framework-level proposal for Step 7: a new Rule 15 in the workspace `CLAUDE.md`
  ("recurring jobs are idempotent: a steady-state run performs zero paid work and zero
  destructive work, proven by a test; one-time helpers are never reused in recurring jobs
  without re-review; every paid per-item pipeline has a repeat-work tripwire"), plus a matching
  check in `/change-request` and `/new-backend-spec`. Not done yet. It changes the framework,
  which the owner decides.
- 2026-10-11: ✅ Step 1 hotfix done (owner approved "fix + push to main").
  - **Spec:** `backend/specs/market-health/api.md` — Taxonomy reprocessing gains a "Corrected
    2026-10-10" block: stale means older version only; every selected posting is written;
    requirements are cleared only for changed postings; the whole-corpus helpers are removed.
  - **Code:**
    - `raw_postings.get_stale_for_reclassification()` replaces `get_all_for_reclassification()`;
      `get_requirements_reprocess_targets()` is deleted.
    - `classification.reclassify_all()` now writes cache hits. Before, they were counted but
      never written, which is the second bug that left 54 postings stuck on `2026-08-11`.
      The title cache now carries `job_function` and `model`, so a cache write doesn't blank
      them. It returns `changed_posting_ids` via the pure `changed_posting_ids()` helper.
    - `ingest.run_taxonomy_reprocessing_phase()` and `reprocess_taxonomy.py` delete
      requirements only for those ids.
  - **Tests:** `backend/tests/test_reprocessing_steady_state.py`, 6 passing. A steady-state day
    deletes nothing and makes no model call; only changed postings are cleared; level and
    confidence changes don't count; cache hits are written with their fields intact.
    `test_ingest_isolation.py` still 4/4.
  - **Dry run against production (read-only):** the next run selects 54 stale postings, all
    with titles already cached on the current version. So: 0 model calls, at most 54
    requirements cleared, then 0 on every day after.
- 2026-10-11: Deployed. `job-sync` deployment `596ad90b` is live on commit `f3db13c` (SUCCESS
  20:53 UTC). Too late for this morning's run 95 (06:03 UTC), which wiped requirements once
  more, down to 95 rows, and submitted batch job 32 (500 postings). Batch jobs 30 and 31 both
  `failed` provider-side; check why as part of Step 5. Tomorrow's run is the first on the
  fixed code. Expect: 54 stale postings rewritten from cache, 0 classification model calls,
  job 32 collected and *kept*.
- 2026-10-11: ✅ Step 7 done in the framework repo. Workspace `CLAUDE.md` gains **Rule 15**
  (recurring jobs: a stated steady state with no paid and no destructive work, proven by a
  test; no unreviewed one-time helpers in recurring paths; destructive steps scoped to what
  changed; a repeat-work tripwire on every paid per-item pipeline). `/new-backend-spec` gains
  a steady-state step (new Step 9) and two anti-patterns. `/change-request` gains a matching
  anti-pattern for changes that touch a recurring job without going through `/new-backend-spec`.
- 2026-10-11: ⚠ **The `api` service failed both of today's deploys (healthcheck)**, unrelated to
  this CR's code. `job-sync`, `web`, `employment-events` and `romantic-presence` deployed fine.
  - **Cause:** dependency drift. `pydantic` was unpinned (transitive via fastapi, google-genai
    and mcp). A fresh build took pydantic 2.14.1, which removed the private
    `_typing_extra.eval_type_backport` that `mcp==1.9.4`'s FastMCP imports, so `main.py` crashed
    at `app.mount("/mcp", ...)`. The last good `api` deploy (10-01) predates that release and
    stays live, so production `api` was not down. Any `api` deploy from today on would have
    failed regardless of what changed.
  - **Fix:** pin `pydantic==2.13.5` in `backend/requirements.txt`. Verified on a fresh install of
    the whole file: `pip check` is clean, the full `main` app imports, `test_mcp_access.py` 9/9
    and `test_reprocessing_steady_state.py` 6/6 pass.
  - Logged here, not as its own CR: it blocks this CR's deploy, is a one-line pin, and changes no
    behaviour. Same lesson as Rule 15 in spirit: an unpinned transitive dependency is a
    recurring job (every rebuild) with no steady-state guarantee.
- 2026-10-12: Step 5, run 1 of 2 (first run on the fixed code, `job-sync` 06:02–06:09 UTC). ✅
  Every expectation met:
  - **Reprocessing:** 54 stale postings, all 54 cache hits, 0 LLM calls, `changed_posting_ids: []`,
    so 0 requirements deleted. The stale set should now be empty on future runs.
  - **Batch job 32:** collected, 499 postings (1 skipped as an unknown/pruned id).
  - **Requirements kept:** `posting_requirements` = 652 rows / 652 postings. That is exactly
    95 (yesterday) + 499 (job 32) + 58 (12 interactive batches), so nothing was deleted.
  - **Batch job 33:** submitted with 500 distinct postings. 0 of them already have requirements,
    and none overlap job 32. 400 were in earlier jobs whose results the loop deleted (340 from
    job 29, 60 from 28), so this is legitimate rebuilding, not pointless repeat work.
  - Backlog: 7,567.
  - Run status `partial` only because 3 boards returned 404 (greenhouse amplitude/buzzfeed,
    lever plaid). Unrelated to this CR.
  - **Still open for Step 5:**
    - Run 2 tomorrow must show stale = 0 and requirements growing again.
    - Jobs 30 and 31 failed on our side with `submit did not complete`, on the same 500 posting
      ids. Check in Google AI Studio that no orphan provider batch was created or billed.
- 2026-10-13: ✅ Step 5, run 2 of 2. Step 5 complete.
  - **Reprocessing:** 0 stale postings. The phase returned early without logging anything (as
    intended), with no deletes and no model calls.
  - **Batch job 33:** collected, 499 postings.
  - **Requirements growing:** `posting_requirements` 652 → 1,198, exactly +499 (job 33) +47
    (12 interactive batches). 0 deleted.
  - **Batch job 34:** submitted with 500 distinct postings. 0 already extracted, and no overlap
    with jobs 32 or 33.
  - **Backlog falling:** 7,567 → 7,083. Classification handled 118 new titles in 2 calls (new
    postings, not reprocessing).
  - **Jobs 30 and 31 checked:** their `submit did not complete` is set by
    `batch_jobs.reconcile()` when a job has no `provider_job_ref` after 30 minutes. Google's own
    batch list for the requirements key shows no job created on 10-09 or 10-10, so there was no
    orphan provider batch and nothing was billed. The postings went back into the backlog. Why
    the submit didn't return on those two days is not yet known and isn't blocking. Step 4's
    admin "blocked/failed phase" visibility should make it visible next time.
  - Still to do: Steps 2–4 (the guardrails themselves) and Step 6.
- 2026-10-23: ✅ **Step 6 done in effect.** The sampling CR was resumed with the owner using real
  numbers from after the fix: cap 50, Designer unlimited, the backlog left to finish. Its
  scope was then widened to storage. See that CR's 2026-10-23 entries. The owner then asked
  for these guardrails before sampling is built, and sampling's backend build now depends on
  them.
- 2026-10-23: ✅ **Step 2 done.** `design/pipeline-visibility/experience.md` gains User Flow 15
  (Paid work check), chart specs for the Paid work check and for batch slots vs. distinct
  postings, two interactions, five edge cases and two metrics.
  - **States:** neutral when there are no repeats or removals. `amber-600` "Paused" /
    "Removal stopped" ("flag, not failure") when a safeguard fires. The existing `red-600` stays
    for real failures.
  - **No quiet stops:** a pause stays on the Overview until a later run reads normally. A run
    that didn't read always names why, so it can't look like a quiet day.
- 2026-10-23: ✅ **Step 3 done.**
  - **`backend/specs/market-health/api.md`:** a new Business Logic subsection, "Repeat-work
    guardrails". It adds:
    - an append-only `requirements_extraction_ledger`, written in the same transaction as each
      extraction and seeded once from current rows;
    - append-only `requirements_reprocess_requests`. A repeat is "explained" only if a request
      is newer than the posting's last ledger row;
    - a circuit breaker on the exact set each lane will pay for, checked before any spend:
      block if unexplained > 50 or > 10%, each lane independently, with thresholds as code
      constants rather than env vars;
    - a daily delete cap of 200, which raises before any SQL. Manual scripts need `allow_bulk`
      plus a `change_ref`;
    - paid / new / repeats / deleted per run, with `new + repeats = paid`;
    - de-duplicated batch selection plus `distinct_count`;
    - `batch_submit_incomplete` surfaced;
    - reprocessing `total_classified` counting changed rows only, with `reclassified_unchanged`
      separate.
    It also adds the IngestionRun fields `requirements_guard` and `guard_detail` (a guard firing
    does not make a run `partial`), and the two new tables.
  - **Steady state written in (Rule 15).** Proved by a new `test_requirements_guard.py` and an
    extended `test_reprocessing_steady_state.py`.
  - **`backend/specs/pipeline-visibility/api.md`:** Overview `paid_work_check` (read from run
    fields, never recomputed; `last_unresolved_guard` keeps a pause visible) and batch
    `distinct_count`, plus `/admin/runs` columns and run-detail `guard_detail` with links to
    unexplained postings.
  - **No frontend spec.** The admin is server-rendered (confirmed).
  - **MCP access review: no change, confirmed.** These are operator telemetry, covered by
    `ACCESS.md`'s existing "Pipeline processing visibility" row (not exposed, operator-only).
  - **Data surface review:** not applicable. The ledger and requests are pipeline bookkeeping,
    not a new kind of market fact.
  - **Polite scraping:** not applicable.
- 2026-10-23: ✅ **Step 4 done (built and tested locally; not committed or deployed).**
  - **New:**
    - `requirements_guard.py`: thresholds as constants (50 / 10% / delete cap 200), the pure
      `is_blocked`, `check_repeat_work` (injectable lookup), `RequirementsDeleteCapExceeded`,
      and `severest`.
    - `migrate_extraction_ledger.py`: a one-time idempotent seed, never run from `ingest.py`.
    - `backend/tests/test_requirements_guard.py`: 16 tests.
  - **Changed:**
    - `db.py`: two append-only tables, `batch_jobs.distinct_count`, and 7 `ingestion_runs`
      columns.
    - `requirements.py`: `insert_requirements` writes ledger rows for newly extracted postings
      in the same transaction (`lane`, `batch_job_id`). `delete_requirements_for_reprocess`
      enforces the cap before any SQL, requires `change_ref` for bulk deletes, records
      reprocess requests and returns the deleted count. `extract_requirements` takes
      `pre_spend_check` and reports paid/new/repeats. `collect_batch_results` passes
      `batch_job_id`.
    - `ingest.py`: reprocessing counts only changes and records a delete-cap block instead of
      raising. The interactive lane is guarded. `_maybe_submit_batch` de-duplicates, checks the
      breaker before `create_job` and returns `(job_id, info)`. Reconcile marks
      `batch_submit_incomplete`. Guard fields are folded into `record_run`.
    - `ingestion_runs.py`: new fields in `record_run` / `list_runs` / `get_run`, plus
      `get_paid_work_check()` with `last_unresolved_guard`.
    - `batch_jobs.py`: de-duplicates `posting_ids` and stores `distinct_count` (computed for
      legacy rows).
    - `raw_postings.attach_ingestion_run` also attaches ledger rows (NULL-only).
    - `reprocess_taxonomy.py` and `reextract_skilless.py`: `--change-ref` is required, and they
      call with `allow_bulk=True`.
    - Admin: Overview Paid work check line and batch "distinct in slots", runs-table
      Paid/New/Repeats/Removed column with badges, run-detail Paid work check card listing
      unexplained posting links, and a `.field-hint` CSS rule.
    - `DEPLOYMENT.md`: a deploy/seed/verify section.
    - `test_reprocessing_steady_state.py`: updated for the new delete signature, plus asserts
      that `total_classified` excludes unchanged rewrites.
  - **Verified:**
    - all 19 backend test files pass (`test_requirements_guard` 16/16,
      `test_reprocessing_steady_state` 6/6, all others unchanged and passing);
    - every changed module imports;
    - the three admin templates parse;
    - the Paid work check and run-detail fragments render correctly for healthy, leak, paused,
      delete-cap and incomplete-submit states (StrictUndefined).
  - **Not verified yet:** the new SQL against a real Postgres (DDL, the ledger lookup, the
    `last_unresolved_guard` query). It runs on the next deploy via `init_schema()`. This is
    Step 4b.
  - **Deviations from the spec:**
    - **Badge colour:** the admin's existing amber badge class is named `neutral` (it already
      means "flag, not failure"), so the spec's `amber-600` warning reuses it rather than adding
      a class.
    - **Interactive-lane paid count:** for that lane, `requirements_paid` counts postings in
      batches actually sent, including a batch whose call then failed, because a failed call
      may still be billed. For the batch lane, it is counted at successful submit.
