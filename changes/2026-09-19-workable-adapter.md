---
id: workable-adapter
date: 2026-09-19
trigger-type: user-feedback
change-type: new-feature
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Build a Workable source adapter

## Signal
User: "lets go" — picking up the next thread from the menu offered after the size-band research
(`changes/2026-09-19-original-35-size-bands.md`): a new ATS adapter to unlock Starling, which
`changes/2026-09-19-uk-employer-panel-v2.md` had already confirmed real on Workable.

## Outcome
See: `outcomes/job-data-source-flexibility.md` — a new adapter mechanism, same weight as the
original Greenhouse/Lever/Ashby adapters this outcome was written to cover.

## Change Type
`new-feature` — a genuinely new ATS mechanism (4th adapter), not a company-list edit. Follows
the exact recipe `DATA_SOURCES.md` §5 already names: *"Add a new ATS... new class in
`backend/src/sources/`, register in `ALL_SOURCE_ADAPTERS`."* No experience spec needed — same
"data acquisition only, no user-facing decision" precedent every prior source adapter (including
the original three) was speced under, directly against `DATA_SOURCES.md`'s own conventions
rather than a fresh experience/IA/visual-design chain.

## What was built

**Real endpoint research first** (not assumed): confirmed Workable's public widget API —
`GET https://apply.workable.com/api/v1/widget/accounts/{account}` — no API key, no login,
returns every published job in one call, same shape as Greenhouse. Verified against Starling
Bank's real board (`starling-bank`) — 55 real, distinct jobs.

**A real data-shape quirk found and handled, not assumed away**: Workable duplicates a
multi-location job into one array entry per location — a single "Android Engineer" role posted
in Manchester/Cardiff/Southampton/London appeared as 4 separate entries sharing the same
`shortcode`. Deduped to one row per distinct `shortcode` (first location kept) — the same "one
row per distinct job, not per posted location" semantics Ashby's adapter already applies to its
own `secondaryLocations`. Verified: 55 jobs fetched, 55 unique `source_ref`s after dedup — no
loss, no duplication.

**Licence checked before building** (same discipline as every other source): Workable's own
help docs describe the intended use as letting a company (or a third party building on its
behalf) build a careers page from this endpoint — no restriction on third-party read access
found, same honest "no formal licence, no restriction found, not manufactured" finding as
Greenhouse/Ashby's own registry entries.

**Files**: `backend/src/sources/workable.py` (new adapter), `sources/__init__.py`
(registration), `source_licences.py` (new registry entry), `industries.py` (Starling tagged:
Fintech / UK / Medium), `admin_main.py` (filter dropdown), `backend/specs/market-health/api.md`
(Data Models `source` closed set, illustrative Protocol snippet), `DATA_SOURCES.md` (§3 new
adapter row, §4 tracked-companies count), `EMPLOYER_PANEL.md` (Starling → Added; "Next ATS
adapters" backlog updated).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | no-change |
| Experience Spec | none (deliberate, per every prior adapter's own precedent) | no-change |
| Backend Spec | `backend/specs/market-health/api.md` | update — `source` closed set, Protocol snippet |
| Backend Implementation | `backend/src/sources/workable.py` (new), `sources/__init__.py`, `source_licences.py`, `industries.py`, `admin_main.py` | update |
| Plain-Language Overview | `OVERVIEW.md` | no-change — more of the same existing "job demand" capability, no new user-visible concept |
| MCP Access Review | `ACCESS.md` | no-change — existing tools (`get_job_demand` etc.) automatically cover any source in `raw_postings`, no new capability |
| Polite Scraping Review | — | no-change — a public API adapter, not a scraped source (no HTML parsing, no robots.txt) |

## Execution Plan

- [x] Step 1: Real endpoint research — confirmed the public widget API, no key/login required
- [x] Step 2: Real licence check — Workable's own docs, no restriction found, recorded honestly
- [x] Step 3: Built `sources/workable.py` — fetch, dedupe multi-location duplicates, normalize country
- [x] Step 4: Registered in `ALL_SOURCE_ADAPTERS`, `source_licences.py`, `industries.py` (Starling tagged), `admin_main.py`'s filter list
- [x] Step 5: Updated `backend/specs/market-health/api.md`, `DATA_SOURCES.md`, `EMPLOYER_PANEL.md`
- [x] Step 6: Verified end-to-end against real production: `WorkableAdapter().fetch_company("starling-bank")` → 55 real postings, 55 unique `source_ref`s (dedup confirmed correct, no loss); `test_source_licences.py` (4/4) still passes with the new adapter registered; `main.py`/`ingest.py` import cleanly

## Decision Log
- 2026-09-19: Deduped Workable's per-location job duplicates to one row per job, not one row
  per location — matches this platform's existing convention (Ashby's `secondaryLocations`) of
  counting a job once toward demand regardless of how many places it's posted, not inflating
  the count by location.
- 2026-09-19: Started with exactly one company (`starling-bank`) rather than researching more
  Workable-hosted employers preemptively — the adapter itself is the deliverable; expanding its
  `COMPANIES` list is the same lightweight, separately-gated operation as any other adapter's
  company-list growth (`DATA_SOURCES.md` §5), not bundled in here.
