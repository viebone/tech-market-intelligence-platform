---
id: original-35-size-bands
date: 2026-09-19
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Populate `employer_size_band` for the original 35 companies via real research

## Signal
User: "ok continue" — following up on `changes/2026-09-19-employer-panel-schema.md`'s own
explicitly named follow-up: the original 35 tracked companies were left untagged for
`employer_size_band` rather than guessed, with a note that real research was still needed.

## Outcome
See: `outcomes/job-data-source-flexibility.md` — completes the data-model addition from
`changes/2026-09-19-employer-panel-schema.md` under the same outcome.

## Change Type
`content-change` — populating an existing static lookup (`industries.COMPANY_SIZE_BAND`) with
real data. No schema change (the columns already exist), no new mechanism.

## What was done

Real headcount research (WebSearch, cross-checking multiple sources — Revelio Labs
workforce-intelligence data, company-reported/SEC figures where available) for all 35 original
Greenhouse/Lever/Ashby companies, batched into ~10 search queries covering multiple companies
each. Full cited detail: `research/2026-09-19-original-35-size-bands.md`.

**Result: 33 of 35 companies tagged** with a real, cited `employer_size_band`
(Large/Medium/Small-Growth, matching the panel's own segmentation bands). **1 left
deliberately untagged**: `lever` (the ATS company itself, now a sub-brand of Employ Inc.
alongside Jobvite/JazzHR) — no real current headcount figure was found, so it stays `NULL`
rather than guessed.

Several companies had conflicting figures across sources (contractor-inclusion and
LinkedIn-graph-vs-payroll methodology differences) — the band applied is the one the weight of
evidence supports, and the conflicting range is noted in the research file rather than
silently resolved to false precision.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Backend Spec | `backend/specs/market-health/api.md` | update — corrected the `employer_size_band` field description and Business Logic note (previously said "not populated for most of the original 35," now accurate) |
| Backend Implementation | `backend/src/industries.py` | update — `COMPANY_SIZE_BAND` extended from 19 to 53 entries |
| Plain-Language Overview / IA / Visual Design / MCP / Polite Scraping | — | no-change, same reasoning as `changes/2026-09-19-employer-panel-schema.md` |

## Execution Plan

- [x] Step 1: Real headcount research for all 35 original companies (10 batched WebSearch queries) — see `research/2026-09-19-original-35-size-bands.md` for full citations
- [x] Step 2: Extended `industries.COMPANY_SIZE_BAND` — 33 new entries, `lever` left untagged
- [x] Step 3: Corrected `backend/specs/market-health/api.md` and `EMPLOYER_PANEL.md` to reflect the real, current coverage (53/54, not 19/54)
- [x] Step 4: Verified — `size_band_for()` spot-checked for `stripe`/`openai`/`deel` (Large), `restream`/`linear` (Small/Growth), `lever` (`None`, correctly untagged); `len(COMPANY_SIZE_BAND) == 53`; full test suite still passes; `main.py`/`ingest.py`/`raw_postings.py` import cleanly

## Decision Log
- 2026-09-19: Did not force a band onto `lever` (the company) despite the temptation to reach
  100% coverage — no real figure was found in research, and the whole point of this exercise
  was replacing guesses with real data, not replacing one gap with a fabricated non-gap.
- 2026-09-19: Recorded conflicting source figures honestly (e.g. Notion 1,920 vs. 4,162;
  ElevenLabs 400 vs. 880) rather than picking one silently — the research file states both
  ends of the range and which one the band decision leaned on.
