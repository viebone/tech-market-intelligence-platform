---
id: uk-employer-panel-v1
date: 2026-09-18
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Add first 16 verified UK employer-panel companies

## Signal
See: `research/2026-09-18-uk-employer-panel-v1.md`, `research/2026-09-18-uk-employer-panel-plan.md`

## Outcome
See: `outcomes/job-data-source-flexibility.md` — content curation inside the already-delivered
adapter mechanism (Greenhouse/Lever/Ashby), same weight as every prior company addition to
`DATA_SOURCES.md` §4. No new outcome, no success-criteria change.

## Change Type
`content-change` — adding companies to already-built adapters' `COMPANIES` lists +
`industries.py`, exactly `DATA_SOURCES.md` §5's existing "add a company" recipe. No new
adapter, no schema change, no new data model.

## Triage Notes (Step 2)

Maps to `job-data-source-flexibility` — not a new area. This is the first worked slice of
`EMPLOYER_PANEL.md`'s 36-employer candidate list (itself proposed and evaluated in
`research/2026-09-18-uk-employer-panel-plan.md`), deliberately scoped to only the candidates
that need **zero new adapter work** — real, verified hits against the existing
Greenhouse/Lever/Ashby endpoints. The large enterprise employers (Tesco, Barclays, HSBC, etc.,
expected to need Workday/SuccessFactors) and public-sector/custom-page employers were
deliberately not attempted this pass, per the plan's own agreed sequencing.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | no-change |
| Design Foundations / IA / Visual Design | — | no-change |
| Experience Spec | none | no-change — data acquisition only |
| Backend Spec | `backend/specs/market-health/api.md` | no-change — company-list curation is already documented there as a Tech Decision, not a per-company spec change |
| Backend Implementation | `backend/src/sources/{greenhouse,lever,ashby}.py`, `backend/src/industries.py` | update |
| Plain-Language Overview | `OVERVIEW.md` | no-change — no user-visible capability changes, more of the same existing "job demand" data |
| MCP Access Review | `ACCESS.md` | no-change — no new capability, existing `get_job_demand`/etc. tools automatically cover any company in `COMPANIES` |
| Polite Scraping Review | `DATA_SOURCES.md` | update — §4 table gains 16 rows; §5 unaffected (recipe already covers this) |

## What was verified (real HTTP requests, not assumed)

16 companies, each confirmed by a real HTTP 200 against the adapter's actual public endpoint,
with real job content inspected (not just a status code):

| Company | ATS | Sector |
|---|---|---|
| monzo | Greenhouse | Fintech |
| deliveroo | Greenhouse (Ashby board deliberately excluded — see Decision Log) | Food Delivery/Marketplace |
| wise | Greenhouse | Fintech |
| autotrader | Greenhouse | Automotive Marketplace |
| cleo | Greenhouse | Fintech/AI |
| zopa | Lever | Fintech |
| trainline | Ashby | Travel/Tech |
| quantexa | Ashby | AI/Data |
| faculty | Ashby | AI |
| motorway | Ashby | Marketplace |
| marshmallow | Ashby | Insurtech |
| multiverse | Ashby | EdTech |
| attio | Ashby | SaaS/CRM |
| griffin | Ashby | Fintech (Banking-as-a-Service) |
| sylvera | Ashby | Climate/Data |
| beamery | Ashby | HR Tech |

Full verification detail (endpoint, real job count, methodology) recorded in
`EMPLOYER_PANEL.md`'s "Verification pass 1" section — not duplicated here.

## Execution Plan

- [x] Step 1: Signal captured — `research/2026-09-18-uk-employer-panel-v1.md`
- [x] Step 2: PM triage — mapped to `job-data-source-flexibility`, classified `content-change`
- [x] Step 3: Verified 16 candidates by real HTTP request against Greenhouse/Lever/Ashby's actual public endpoints (not assumed from the plan's claims) — recorded in `EMPLOYER_PANEL.md`
- [x] Step 4: Added the 16 verified companies to `sources/greenhouse.py` (5), `sources/lever.py` (1), `sources/ashby.py` (10) `COMPANIES` lists, and tagged each in `industries.py`
- [x] Step 5: Updated `DATA_SOURCES.md` §4 (35 → 51 tracked companies, 16 new rows) and its header note about the UK employer panel
- [x] Step 6: Updated `EMPLOYER_PANEL.md` — the 16 rows moved from `Unverified` to `Added`; the file's top-line status corrected
- [x] Step 7: Verified end-to-end: all 16 present in their adapter's `COMPANIES` + `industries.COMPANY_INDUSTRY`; real `fetch_company()` calls against `monzo` (Greenhouse), `attio` (Ashby), and `zopa` (Lever) each returned real parsed postings; `main.py`/`ingest.py` import cleanly; `test_source_licences.py` (4/4) still passes — no licence-coverage gap, since these are new companies on already-registered sources, not new sources

## Decision Log
- 2026-09-18: Deliberately added only Deliveroo's Greenhouse board, not its Ashby board — both
  are real, but the Ashby board is Deliveroo's separate operational/warehouse ("Hop" grocery
  site) hiring, which doesn't fit this platform's Designer/Product Manager/Engineer taxonomy
  the way its corporate/tech Greenhouse board does. Recorded as a deliberate scope decision in
  `EMPLOYER_PANEL.md`, not a missed source — can be added later if operational-role coverage
  is ever wanted.
- 2026-09-18: 8 candidates from this batch (Rightmove, Starling, incident.io, Ocado, Sage, AJ
  Bell, Softcat, Cuvva) did not resolve on a first-guess slug against any of the three
  platforms. Recorded honestly as `Unverified` (not `Rejected`) in `EMPLOYER_PANEL.md` — a
  wrong guess isn't evidence there's no accessible source; each needs real research (checking
  the company's own careers page) before another attempt.
- 2026-09-18: Deliberately did not attempt the 12 Large-enterprise candidates (Tesco, BT,
  Barclays, etc.) this pass — expected to need a new adapter (Workday/SuccessFactors, not yet
  built) or a custom/public-sector mechanism, per the panel's own agreed sequencing
  (`research/2026-09-18-uk-employer-panel-plan.md`).
