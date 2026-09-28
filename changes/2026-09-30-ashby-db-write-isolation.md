---
id: ashby-db-write-isolation
date: 2026-09-30
trigger-type: internal
change-type: bug-fix
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Fix — a DB-write failure during ingestion could abort an entire adapter's remaining companies

## Signal
See: `research/2026-09-30-ashby-db-write-isolation.md`. Originally flagged
2026-09-27 (`changes/2026-09-26-personio-adapter.md` Decision Log) as a real production incident,
deliberately not fixed at the time — logged for its own change request instead.

## Outcome
See: `outcomes/job-data-source-flexibility.md` — the multi-adapter ingestion mechanism this
outcome established explicitly promises per-company fault isolation
(`backend/specs/market-health/api.md` — Business Logic — Ingestion — Fault isolation). This fix
makes that promise true for the storage step, not only the fetch step.

## Change Type
`bug-fix` — root cause: **the spec itself was narrower than the code's own documented contract**,
which is what let the gap exist. `ingest.py::ingest_company()`'s docstring promises "Never
raises" for the whole per-company operation; the backend spec's "Fault isolation, per company"
bullet only ever named "a single company's board fetch failing", never the storage step. The code
matched the spec's literal (narrow) wording, not its own docstring's (correct, broader) intent —
so both the spec and the code needed fixing, not code alone.

## What was wrong, concretely
`ingest_company()` wrapped only `adapter.fetch_company(company)` in a try/except
(`SourceFetchError`). The `insert_new_postings(...)` call right after it was unguarded. A real
production incident, 2026-09-27: a transient Postgres connection timeout inside
`insert_new_postings()` (via `existing_ids()`) for the Ashby company `thought-machine` propagated
straight out of `ingest_company()`, was caught only by `run()`'s **adapter-level** try/except, and
silently skipped every remaining company in Ashby's `COMPANIES` list for the rest of that run
(`zego`, the last company in the list, never got its same-day refresh — it already had rows from
an earlier day, so nothing was lost, but a *different* run on a *different* day could have missed
a company's only chance to see a posting before it's edited or unpublished, per `raw_postings`'
own "captured once, at first sight" contract).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | no-change |
| Backend Spec | `backend/specs/market-health/api.md` — "Fault isolation, per company, and per adapter" | **update** — broadened from "board fetch failing" to the whole per-company operation (fetch AND store), closing the ambiguity that let this gap exist |
| Backend Implementation | `backend/src/ingest.py::ingest_company()` | update — the DB write now has its own try/except, same shape as the fetch side |
| Plain-Language Overview | `OVERVIEW.md` | no-change — an internal reliability fix, no user-visible behaviour change (the platform already looked correct; this closes a rare failure window, not a feature) |
| MCP Access Review | — | not-applicable — no capability added or changed |
| Polite Scraping Review | — | not-applicable — no scraped source touched |
| Data Surface Review | — | not-applicable — no new data category |

## Execution Plan

- [x] Step 1: Read the spec's fault-isolation section and confirm the spec itself was narrower than `ingest_company()`'s own docstring — root cause is a spec/code mismatch, not code alone
- [x] Step 2: Updated `backend/specs/market-health/api.md`'s fault-isolation bullet to cover storage explicitly
- [x] Step 3: Fixed `ingest.py::ingest_company()` — wrapped `insert_new_postings(...)` in its own try/except, returning the same per-company error-dict shape as the fetch side; confirmed safe to catch broadly (both `existing_ids()` and the insert open their own connection via `with get_connection()`, so a failure here can't leave a partial write)
- [x] Step 4: New tests (`backend/tests/test_ingest_isolation.py`, 4 tests, offline — no real DB or network) — confirms the fetch-failure path is unchanged, the DB-write-failure path now returns an error dict instead of raising, and — reproducing the actual production symptom directly — a DB failure on the first of three companies (`synthesia`, `thought-machine`, `zego`, real order from `sources/ashby.py` at the time of the incident) no longer prevents the other two from being attempted. 4/4 pass
- [x] Step 5: Verify no regression in the module this touches — `ingest.py` imports cleanly; the fix is additive (one new try/except), no existing behaviour changed for the success path or the fetch-failure path (both covered by tests)

## Decision Log
- 2026-09-30: Chose a broad `except Exception` for the insert step, same as the fetch side already
  does (`SourceFetchError` is itself a wrapper the adapter raises for a range of underlying
  failures). Confirmed safe specifically because `insert_new_postings()`'s two DB calls
  (`existing_ids()`, the insert itself) each open their own connection via `with get_connection()`
  — a failure at either point can't leave a partial, uncommitted write needing a rollback.
- 2026-09-30: Treated as `bug-fix`, not `technical-refactor` — the behaviour was genuinely wrong
  (a documented "never raises" contract that could raise), not merely restructured. Updated the
  spec first (it was ambiguous/narrower than intended), then the implementation, per the
  `bug-fix` sequence's own "spec is ambiguous or incorrect → update the spec first" branch.
- 2026-09-30: Not fixed here (out of scope, unrelated): the incidental finding from
  `changes/2026-09-23-us-eu-employer-panel-expansion.md` that several existing tracked boards
  return 0 roles (`clari`, `restream`, `lever`, `mercury`, `deel`, `loom`, `vercel`, `cuvva`) and
  `plaid`'s Lever token 404s on every run — still open, still worth its own change request.
