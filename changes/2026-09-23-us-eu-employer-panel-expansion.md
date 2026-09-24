---
id: us-eu-employer-panel-expansion
date: 2026-09-23
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: in-progress
---

# Change Request: Stratified US + EU employer panel on the four existing ATS adapters (Tier 1)

## Signal
See: `research/2026-09-23-us-eu-employer-panel-expansion.md`

## Outcome
See: `outcomes/job-data-source-flexibility.md` — content curation inside the already-delivered
adapter mechanism (Greenhouse / Lever / Ashby / Workable), same weight as
`changes/2026-09-18-uk-employer-panel-v1.md`. No new outcome, no success-criteria change.

## Change Type
`content-change` — adding verified companies to already-built adapters' `COMPANIES` lists +
`industries.py` (`COMPANY_INDUSTRY`, employer region, employer size band), exactly
`DATA_SOURCES.md` §5's "Add a company" recipe. No new adapter, no schema change, no new data
model, no new source.

## Triage Notes (Step 2)

Maps to `job-data-source-flexibility` (bucket A). The UK panel that previously fed this
recipe is exhausted (see signal), so this change first **builds the candidate list** —
a stratified US + EU panel by size band × sector × country — then works it one entry at a time
under `EMPLOYER_PANEL.md`'s existing Unverified → Checking → Verified → Added/Rejected process.

**Explicitly out of scope** (each its own future change request, with live terms verification
per Rule 13 before any code):
- New adapters: France Travail, Arbeitnow, Jobicy, USAJOBS, Personio, Recruitee, others.
- `source_type` / `retention` (derived-only) fields on job postings.
- Cross-source dedupe.
- Outreach to DWP for Find a Job access.
- Any source already blocked: Workday, Taleo, SmartRecruiters, Indeed, Reed, LinkedIn.

**Constraints that shape how this runs:**
- **LLM cap ($5/month) and classification backlog** (152 at last check): expansion is gradual —
  small batches, watching the backlog and the daily budget between batches, not one big drop.
- **Relevance:** the platform's taxonomy is Design / Product / Engineering with an `other`
  bucket; prefer employers with real tech/product hiring, but keep deliberate sector variety
  (the panel exists to correct the venture-backed-SaaS skew).
- **No false positives:** an HTTP 200 alone is never enough (the `sage49` near-miss) — every hit
  is content-inspected to confirm it is the intended company.
- **Non-English postings:** continental-EU boards may carry French/German/etc. postings; check
  classification copes on a sample before adding many such employers.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | no-change |
| Design Foundations / IA / Visual Design | — | no-change |
| Experience Spec | none | no-change — data acquisition only |
| Frontend Spec / Implementation | — | no-change |
| Backend Spec | `backend/specs/market-health/api.md` | no-change — company-list curation is already documented as a Tech Decision, not a per-company spec change |
| Backend Implementation | `backend/src/sources/{greenhouse,lever,ashby,workable}.py`, `backend/src/industries.py` | update |
| Plain-Language Overview | `OVERVIEW.md` | no-change — more of the same existing "job demand" data; no new capability. Re-check at close if headline coverage wording (e.g. tracked-company counts) appears there |
| MCP Access Review | `ACCESS.md` | no-change — existing tools cover any company in `COMPANIES` automatically |
| Polite Scraping Review | `DATA_SOURCES.md` | not-applicable for the review itself (no scraped source; all four are documented public APIs) — but `DATA_SOURCES.md` §4 (tracked-company table + counts) and §7 lever counts get updated by hand |
| Data Surface Review | — | not-applicable — more instances of an existing shape (rows in `raw_postings`), not a new data category |
| Panel documentation | `EMPLOYER_PANEL.md` | update — new US + EU candidate section, verification-pass log |

## Execution Plan

- [x] Step 1: Built the US + EU (+ extra UK) candidate list — 215 names by country and sector; recorded in `EMPLOYER_PANEL.md` ("US + EU expansion — verification pass 6") with results
- [x] Step 2: Probed Greenhouse / Lever (incl. EU host) / Ashby / Workable per candidate at 1 req/s per host, identified User-Agent, no bypassing. **Workable half of the probe is invalid** — 189 × HTTP 429 (the script did not back off on 429 — an oversight) plus 40 zero-job 200s; Workable discovery deferred to its own pass
- [x] Step 3: Content-inspected every hit. 136 verified; caught 4 false positives (Bird, Trade Republic, Remote, Greenhouse `lovable`), 14 zero-role boards, and 4 cross-platform duplicates (one platform each)
- [x] Step 4: **Batch 1 — 26 companies** (14 Greenhouse, 2 Lever, 10 Ashby; ~1,130 postings) added to the `COMPANIES` lists and `industries.py` (industry + HQ region). **Local edits only — not committed, not deployed**
- [ ] Step 5: Sample-check classification on non-English boards — not yet due (batch 1 is English-first; N26 has English titles for Italian/Spanish-market roles). Required before any mainly-French/German board (Doctolib, Alan, Qonto, ...) is released
- [x] Step 6: Verified batch 1 — all 26 tagged (no missing industry/region); real `fetch_company()` via the actual adapters returned real postings for `n26` (76), `pleo` (35), `spotify` (75); `test_source_licences.py` 4/4 pass (run directly — pytest is not installed in the venv); no new source, so no licence-registry change
- [ ] Step 7: After batch 1's first production ingest run, check the classification backlog and daily LLM budget before releasing batch 2 (needs a commit + deploy first)
- [x] Step 8: Updated `DATA_SOURCES.md` (§4 count 56 → 82, 26 rows, §7 lever count), `EMPLOYER_PANEL.md`, and the product `CLAUDE.md` count; `OVERVIEW.md` checked — states no company count, no change needed
- [ ] Step 9: Complete only when every batch is added or explicitly deferred with a reason — 110 verified companies (~16,100 postings) are held in `EMPLOYER_PANEL.md`, and Workable discovery is deferred

## Decision Log
- 2026-09-23: Scoped to Tier 1 only. New adapters and the `source_type`/`retention` fields
  were discussed in the same session and deliberately split into their own change requests —
  they carry Rule 13 licence work and a schema change that Tier 1 does not.
- 2026-09-23: Classified `content-change`, following `2026-09-18-uk-employer-panel-v1` and
  `2026-09-19-workable-adapter` precedent — adding companies to existing adapters is the
  documented §5 recipe, not a new capability.
- 2026-09-23: Batching is a hard requirement, not a preference — the $5/month LLM cap and the
  existing classification backlog mean a large one-shot addition would starve classification.
- 2026-09-23: Batch 1 chosen from mid-size boards (≤ ~91 roles each, ~1,130 postings total) with
  country/sector variety; the 15 boards with 300+ roles (SpaceX 2,570, Databricks 881, Anthropic
  629, ...) are held for last, one at a time, because they would dwarf the daily classification
  budget on their own.
- 2026-09-23: `employer_size_band` left untagged for the 26 — it is only populated from a cited
  headcount basis, never estimated; `employer_region` (HQ country) is tagged.
- 2026-09-23: For companies resolving on two platforms (Doctolib, Qonto, Wayve, Miro) only one is
  tracked — Ashby preferred (carries compensation) — to avoid double-counting the same jobs,
  same reasoning as the Deliveroo precedent.
- 2026-09-23: Incidental finding, not in scope here: several *existing* tracked boards contribute
  nothing — Plaid's Lever token 404s (every run since ~2026-09-06) and clari, restream, lever,
  mercury, deel, loom, vercel and cuvva return 0 roles. Worth its own small change request (they
  may have moved ATS).
