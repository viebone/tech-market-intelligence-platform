---
id: uk-employer-panel-v3
date: 2026-09-19
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Add Cuvva via the new Workable adapter; deeper Softcat/Sage research

## Signal
User: "ok lets continue" — continuing the employer panel work now that a Workable adapter
exists (`changes/2026-09-19-workable-adapter.md`), re-checking the 3 remaining unresolved
candidates (Softcat, Sage, Cuvva) against all four built adapters instead of three.

## Outcome
See: `outcomes/job-data-source-flexibility.md` — same content-curation weight as every prior
panel-verification pass.

## Change Type
`content-change` — one company added to an already-built adapter's `COMPANIES` list; no new
mechanism.

## What was done

**Cuvva — real hit, added.** Resolves on **Workable** (`cuvva`) — a real board, currently 0
open roles. Same "returns 0 is a legitimate state, not an error" convention this codebase
already documents for Greenhouse's `clari`/`restream`.

**Softcat and Sage — deeper research, still inconclusive, recorded honestly:**
- Softcat's real listings URL (`jobs.softcat.com/jobs/vacancy/find/results/`) doesn't match any
  built adapter or common ATS brand checked (Workday, SmartRecruiters, iCIMS, Eightfold,
  PhenomPeople, SuccessFactors) — likely custom/white-label, needs direct network-request
  inspection to identify for real, which isn't available through search/static page fetch.
- Sage Group's real careers search page blocks automated fetches (403); no conclusive ATS
  identification found via search either.

Neither is marked "rejected" — both remain `Unverified`, with the real dead-ends recorded so
the next attempt doesn't repeat the same searches.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Backend Implementation | `backend/src/sources/workable.py`, `backend/src/industries.py` | update |
| Data Source Documentation | `DATA_SOURCES.md` (55 → 56 companies), `EMPLOYER_PANEL.md` | update |
| Everything else | — | no-change, same reasoning as every prior panel-verification change |

## Execution Plan

- [x] Step 1: Re-tried `cuvva` against all four built adapters (previously only three existed) — real hit on Workable
- [x] Step 2: Verified via real adapter call (`WorkableAdapter().fetch_company("cuvva")` → 0 postings, correctly handled, no crash) before adding
- [x] Step 3: Added `cuvva` to `sources/workable.py`'s `COMPANIES`, tagged in `industries.py` (Insurtech/UK/Small-Growth)
- [x] Step 4: Deeper research on Softcat/Sage — real findings recorded in `EMPLOYER_PANEL.md`, not silently dropped
- [x] Step 5: Updated `DATA_SOURCES.md` (56 companies) and `EMPLOYER_PANEL.md` (21/36 added)
- [x] Step 6: Verified — `test_source_licences.py` (4/4) still passes; `industries.industry_for("cuvva")`/`region_for`/`size_band_for` all return correct real values

## Decision Log
- 2026-09-19: Added Cuvva despite it currently having 0 open roles — the company/board is real
  and correctly configured; an empty board today is a normal, expected state (companies don't
  always have open roles), not a reason to exclude a verified source.
- 2026-09-19: Did not force an ATS identification for Softcat or Sage — recorded the real
  dead-end (URL pattern found, no match; page blocks automated access) rather than guessing an
  ATS vendor from incomplete evidence.
