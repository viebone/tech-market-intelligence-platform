---
id: employer-panel-schema
date: 2026-09-19
trigger-type: user-feedback
change-type: api-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Add `employer_size_band`/`employer_region` to `raw_postings`

## Signal
See: `research/2026-09-19-employer-panel-schema.md` — chosen as the next step from a menu of
options, per the original UK employer panel plan's own recommendation.

## Outcome
See: `outcomes/job-data-source-flexibility.md` — a data-model addition supporting the same
panel-representativeness goal the employer panel work already serves under this outcome.

## Change Type
`api-change` — new columns on `raw_postings`, populated at ingestion time. No new table, no
new endpoint.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | no-change |
| Experience Spec / IA / Visual Design | — | no-change — nothing user-facing surfaces this yet (same status as `industry` itself, which exists but isn't charted anywhere either) |
| Backend Spec | `backend/specs/market-health/api.md` | update — Data Models (2 new `RawPosting` fields), Business Logic (new "Employer metadata tagging" subsection) |
| Backend Implementation | `backend/src/db.py`, `backend/src/industries.py`, `backend/src/raw_postings.py` | update |
| Plain-Language Overview | `OVERVIEW.md` | no-change — internal data-model detail, nothing a user sees change |
| MCP Access Review | `ACCESS.md` | no-change — no new capability; existing tools reading `raw_postings` will incidentally carry these two new fields once populated, not a new tool |
| Polite Scraping Review | — | no-change — doesn't touch a scraped source |

## What was built

Mirrors `industry`'s exact existing mechanism (added 2026-08-09): a static, curated Python
lookup keyed by `company`, consulted at insert time, `NULL` until a company is tagged, never
guessed.

- `db.py`: `ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS employer_size_band TEXT;` and
  `... employer_region TEXT;` — applied live against production during this change (confirmed
  via `information_schema.columns`, not assumed).
- `industries.py`: `COMPANY_REGION`/`COMPANY_SIZE_BAND` dicts + `region_for()`/`size_band_for()`
  functions, same shape as `COMPANY_INDUSTRY`/`industry_for()`.
- `raw_postings.py`: `insert_new_postings()` now also calls `size_band_for()`/`region_for()` at
  insert time, alongside the existing `industry_for()` call.

**Deliberately uneven population, for honesty, not oversight:**
- `employer_region`: populated for **all 54** tracked companies — HQ country/region is
  well-established public fact, safe to state confidently for every one.
- `employer_size_band`: populated **only** for the 19 UK employer-panel companies, using the
  exact size bucket already assigned to each one in
  `research/2026-09-18-uk-employer-panel-plan.md` (a user-supplied classification). The
  original 35 companies are left `NULL` — a real employee-count-based band needs actual
  research per company, the same discipline every ATS-token verification in `EMPLOYER_PANEL.md`
  already follows; a confident-sounding guess from general impression would undermine the exact
  credibility goal ("N continuously tracked employers, covering N industries and N regions")
  this feature exists to serve.

## Execution Plan

- [x] Step 1: Signal captured — `research/2026-09-19-employer-panel-schema.md`
- [x] Step 2: PM triage — mapped to `job-data-source-flexibility`, classified `api-change`
- [x] Step 3: Updated `backend/specs/market-health/api.md` — Data Models + Business Logic
- [x] Step 4: `/implement-backend` — `db.py` migration, `industries.py` lookups, `raw_postings.py` insert-time wiring
- [x] Step 5: Verified against real production: migration applied live (`init_schema()` against the real `DATABASE_URL`), both columns confirmed present via `information_schema.columns`; `region_for("monzo")` → `"UK"`, `size_band_for("monzo")` → `"Medium"`, `size_band_for("stripe")` → `None` (correctly untagged) — all as designed, not assumed
- [x] Step 6: Column/placeholder count in the `INSERT` statement re-verified by hand (17 columns, 17 placeholders, 17 tuple values) before trusting it — a silent off-by-one here would break tomorrow's real ingestion run
- [x] Step 7: Full test suite still passes (`test_source_licences.py` 4/4, `test_story_yoy.py` 3/3); `main.py`/`ingest.py`/`raw_postings.py` import cleanly
- [x] Step 8: Updated `EMPLOYER_PANEL.md`'s "Deferred" section to reflect this is done, with the real follow-up (original-35 size bands) named explicitly, not silently dropped

## Decision Log
- 2026-09-19: Deliberately did not attempt to estimate `employer_size_band` for the original 35
  companies from general impression (e.g. "Stripe feels large"). The entire point of this field
  is making a future panel-composition claim defensible — populating it with unverified guesses
  would work directly against that goal. Recorded as a named follow-up, not silently skipped.
- 2026-09-19: No rows have actually been backfilled with these values (this platform's own
  established "no backfill, populated going forward at ingestion time" pattern, same as
  `industry` in 2026-08-09) — existing rows keep both fields `NULL` since they were never
  re-fetched; only newly-inserted postings from tomorrow's ingestion run onward will carry
  real values.
