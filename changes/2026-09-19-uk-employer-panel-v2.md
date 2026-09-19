---
id: uk-employer-panel-v2
date: 2026-09-19
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Add 3 more verified UK employer-panel companies (verification pass 2)

## Signal
User: "commit and push and lets continue" — continuing `EMPLOYER_PANEL.md`'s working process
against the 8 candidates verification pass 1 left as "not found on a first-guess slug."

## Outcome
See: `outcomes/job-data-source-flexibility.md` — same content-curation weight as
`changes/2026-09-18-uk-employer-panel-v1.md`.

## Change Type
`content-change` — same as v1: adding companies to already-built adapters' `COMPANIES` lists.

## What changed from pass 1 to pass 2

Pass 1 tried a plain lowercase-company-name guess against all three adapters. Pass 2 went back
and did real research (WebSearch for each company's actual careers page) before trying again —
catching that several "obvious" guesses were simply wrong slugs, not absent sources.

**3 more verified and added:**

| Employer | ATS | Real board token | Real jobs |
|---|---|---|---|
| Rightmove | Greenhouse | `rightmovecareers` (not `rightmove`) | 34 |
| Ocado (Group) | Greenhouse | `ocadogroup` (not `ocado`) | 50 |
| incident.io | Ashby | `incident` (not `incidentio`) | 29 |

**A real false positive, caught before shipping**: a Greenhouse board at `sage49` returned
HTTP 200 and looked plausible, but content inspection (job titles, all-US locations) showed
it's a different, unrelated company — not Sage Group plc. Not added. Recorded in
`EMPLOYER_PANEL.md` as the concrete example of why content inspection, not just a 200 status,
is required before trusting a match.

**3 more researched, still not added** (real findings recorded, not further guessing):
- Starling — confirmed on **Workable**, real board, no adapter built for it yet.
- AJ Bell — URL pattern suggests **Oracle Recruiting Cloud/HCM**, a 6th ATS not previously on
  this project's radar.
- Softcat — custom domain `jobs.softcat.com`, ATS behind it not identified from search alone.

**Still fully unresolved**: Sage Group's real ATS (the board found wasn't them), Cuvva (no hit
on any built adapter with the slugs tried).

## Specs Affected

Same as `changes/2026-09-18-uk-employer-panel-v1.md` — `backend/src/sources/{greenhouse,ashby}.py`,
`backend/src/industries.py`, `DATA_SOURCES.md` §4 (51 → 54), `EMPLOYER_PANEL.md`. No spec-chain
layers above implementation touched.

## Execution Plan

- [x] Step 1: Real research (not guessing) on the 8 pass-1 unknowns — found real board tokens for 3, real-but-unbuilt-adapter findings for 2, a real false positive for 1, nothing for 2
- [x] Step 2: Verified the 3 real hits by HTTP 200 + content inspection (job titles/company name literally present) before adding any
- [x] Step 3: Added `rightmovecareers`, `ocadogroup` to `sources/greenhouse.py`; `incident` to `sources/ashby.py`; tagged all 3 in `industries.py`
- [x] Step 4: Updated `DATA_SOURCES.md` §4 (51 → 54 rows) and `EMPLOYER_PANEL.md` (3 rows moved to Added, the false positive and 4 remaining unknowns recorded with real findings, not left as bare "Unverified")
- [x] Step 5: Verified end-to-end — real `fetch_company()` calls against all 3 new slugs returned real parsed postings; `test_source_licences.py` (4/4) still passes; `main.py`/`ingest.py` import cleanly

## Decision Log
- 2026-09-19: Did not add the `sage49` Greenhouse board despite a clean HTTP 200 — content
  inspection (all-US locations, unrelated job titles like "Network Cabling Project Manager")
  showed it's a different company entirely. A 200 status is necessary, never sufficient.
- 2026-09-19: Starling/AJ Bell/Softcat are recorded as real, specific findings (which ATS, or
  which URL pattern) rather than left as a bare "unverified" — the next person picking this up
  doesn't need to re-research from zero.
