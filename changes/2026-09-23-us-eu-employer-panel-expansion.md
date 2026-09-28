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
- [x] ✅ Step 5: Sample-check classification on non-English boards — **Done 2026-09-27** (`research/2026-09-27-us-eu-panel-batch-2.md`). German checked via the Personio adapter CR (13 titles, all sensible). French checked here (13 constructed titles, 1 LLM request, all sensible, `high` confidence) — unblocks Doctolib/Alan/Qonto/BlaBlaCar/Mirakl/Contentsquare/Swile/Ledger/Sorare/Back Market
- [x] Step 6: Verified batch 1 — all 26 tagged (no missing industry/region); real `fetch_company()` via the actual adapters returned real postings for `n26` (76), `pleo` (35), `spotify` (75); `test_source_licences.py` 4/4 pass (run directly — pytest is not installed in the venv); no new source, so no licence-registry change
- [x] ✅ Step 7: **Done 2026-09-27**, as part of the Personio adapter's production run — classification backlog 0, requirements backlog ~4,220 and draining normally, LLM budget raised $5→$10/month the same day (`changes/2026-09-27-llm-budget-raised-to-10.md`)
- [x] Step 8: Updated `DATA_SOURCES.md` (§4 count 56 → 82, 26 rows, §7 lever count), `EMPLOYER_PANEL.md`, and the product `CLAUDE.md` count; `OVERVIEW.md` checked — states no company count, no change needed
- [ ] Step 9: Complete only when every batch is added or explicitly deferred with a reason — Workable discovery is still deferred
- [x] ✅ Step 10: **Batch 2 — 35 companies** (14 Greenhouse, 4 Lever, 17 Ashby; 1,284 real live-verified postings) — see `research/2026-09-27-us-eu-panel-batch-2.md` for selection rationale. Added to `COMPANIES` lists, `industries.py` (industry + region), `employer_headcount.py` (`UNKNOWN_HEADCOUNT`, not yet researched), and `trusted_stats/crosswalks.py` (14 new industry-tag → SIC decisions, version bumped to `2026-09-27.1`). Every company live-fetched through its real adapter with zero errors (caught one real bug: TravelPerk's Ashby token is `perk`, not `travelperk`). `test_trusted_stats` (61), `test_employer_headcount` (14), `test_source_licences` (4) all pass. **75 companies remain held** (110 − 35), giants (SpaceX, Databricks, Anthropic, ...) still last and one at a time
- [x] ✅ Step 11: Updated `DATA_SOURCES.md` §4 count (85 → 120), `EMPLOYER_PANEL.md` (Batch 2 section added, held table down to 75), product `CLAUDE.md` count
- [x] ✅ Step 12: Committed (`d09d125`), pushed, and a real production run confirmed all 35 batch 2 companies live (ingestion_run 2026-09-27, 1,284 rows inserted exactly matching the live-fetched counts); the size-crosscheck block (a same-session, related CR) picked up batch 2's untagged companies as a real "Not placed in a size band" row the same run
- [x] ✅ Step 13: **Batch 3 — 14 companies** (9 Greenhouse, 1 Lever, 4 Ashby; 1,571 real live-verified postings) — see `research/2026-09-28-us-eu-panel-batch-3.md`. A "finish Europe" batch: every remaining non-giant EU/UK candidate, none from the US. Added to `COMPANIES` lists, `industries.py`, `employer_headcount.py` (`UNKNOWN_HEADCOUNT`), `trusted_stats/crosswalks.py` (5 new industry-tag → SIC decisions, version `2026-09-28.1`). Every company live-fetched through its real adapter with zero errors. `test_trusted_stats` (61), `test_employer_headcount` (14), `test_source_licences` (4), `test_statistics_crosscheck` (7) all pass. **61 companies remain held** (75 − 14): 3 (HelloFresh, Intercom, SumUp — Intercom/SumUp identity-unconfirmed/giant respectively), 13 giants, 45 US mid-size — all deferred to a dedicated US-focused batch 4
- [x] ✅ Step 14: Updated `DATA_SOURCES.md` §4 count (120 → 134), `EMPLOYER_PANEL.md` (Batch 3 section added, held table down to 61)
- [x] ✅ Step 15: Committed (`ccdba6d`), pushed, and a real production run confirmed all 14 batch 3 companies live (1,571 rows inserted, exactly matching the live-fetched counts; no errors on any of the 14; the same known pre-existing `lever/plaid` 404 is the run's only error)
- [x] ✅ Step 16: **Batch 4 — 27 companies** (21 Greenhouse, 1 Lever, 5 Ashby; 1,024 real live-verified postings) — see `research/2026-09-28-us-eu-panel-batch-4.md`. The smaller half of the 45 remaining US candidates (under 100 roles each); the 18 larger ones (100–280 roles) held for a dedicated batch 5, same "watch anything large individually" discipline as the giants. Added to `COMPANIES` lists, `industries.py`, `employer_headcount.py` (`UNKNOWN_HEADCOUNT`), `trusted_stats/crosswalks.py` (10 new industry-tag → SIC decisions incl. a genuinely new section, `I` — Accommodation and food service, for Sweetgreen; version `2026-09-28.2`). Every company live-fetched through its real adapter with zero errors. `test_trusted_stats` (61), `test_employer_headcount` (14), `test_source_licences` (4), `test_statistics_crosscheck` (7) all pass. **34 companies remain held** (61 − 27): 3 misc, 13 giants, 18 large-but-not-giant US companies for batch 5
- [x] ✅ Step 17: Updated `DATA_SOURCES.md` §4 count (134 → 161), `EMPLOYER_PANEL.md` (Batch 4 section added, held table down to 34)
- [x] ✅ Step 18: Committed (`44d3f43`), pushed, and a real production run confirmed all 27 batch 4 companies live (1,024 rows inserted, exactly matching the live-fetched counts; no errors beyond the known pre-existing `lever/plaid` 404)
- [x] ✅ Step 19: **Batch 5 — 9 companies** (all Greenhouse; 1,229 real live-verified postings) — see `research/2026-09-28-us-eu-panel-batch-5.md`. The smaller half of the 18 100–280-role US candidates held from batch 4 (under ~180 roles each); the 9 largest (200–280 roles) held for a dedicated batch 6. Classification backlog stood at 759 (not 0) when this batch was sized — today's daily LLM budget was already used by batches 3 and 4's own runs — a real signal, not a blocker, that kept this batch modest rather than the full 18. Added to `COMPANIES` lists, `industries.py`, `employer_headcount.py` (`UNKNOWN_HEADCOUNT`), `trusted_stats/crosswalks.py` (3 new industry-tag → SIC decisions, version `2026-09-28.3`). Every company live-fetched through its real adapter with zero errors. `test_trusted_stats` (61), `test_employer_headcount` (14), `test_source_licences` (4), `test_statistics_crosscheck` (7) all pass. **25 companies remain held** (34 − 9): 3 misc, 13 giants, 9 larger US companies (200–280 roles) for batch 6
- [x] ✅ Step 20: Updated `DATA_SOURCES.md` §4 count (161 → 170), `EMPLOYER_PANEL.md` (Batch 5 section added, held table down to 25, opening status line brought current for the first time since batch 1)
- [x] ✅ Step 21: Committed (`2994e85`), pushed, and a real production run confirmed all 9 batch 5 companies live (1,229 rows inserted, exactly matching the live-fetched counts; no errors beyond the known pre-existing `lever/plaid` 404)
- [x] ✅ Step 22: **Identity check, 2026-09-30** — resolved the two identity-unconfirmed candidates flagged since Step 1 (`research/2026-09-30-intercom-anysphere-identity-check.md`). **Intercom → Rejected**: the Greenhouse `intercom` token now hosts **Fin**, "now part of Salesforce" — Intercom's former AI Agent product, spun out and acquired; adding it as "Intercom" would have misattributed Salesforce hiring data. Removed from `EMPLOYER_PANEL.md`'s held table. **Anysphere/Cursor → Verified**: confirmed via explicit posting text ("the technical face of Anysphere... helping customers evaluate Cursor"), 128 real roles. Moved into the held table, ready for a future batch — **not added to `COMPANIES` in this pass**, deliberately: classification backlog (1,753) can't drain until tomorrow's daily LLM budget resets, so no new postings were added today. Held-table net count unchanged (25 → −1 Intercom +1 Anysphere = 25)

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
