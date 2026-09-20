---
id: direct-employer-portal-check
date: 2026-09-20
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Does going directly to employer career portals open anything up? (no code change)

## Signal
User: "what about going directly to the companies career portals?" — questioning whether the
ATS-vendor licence research (Workday/Taleo/SmartRecruiters blocks) could be sidestepped by
targeting the employer's own domain instead.

## Outcome
See: `outcomes/job-data-source-flexibility.md` — same panel-research weight as every prior pass.

## Change Type
`content-change` — documentation only. No code touched.

## What was found
See `research/2026-09-20-direct-employer-portal-check.md` for full detail. Split into two real
buckets:

1. **7 vendor-hosted employers (Workday/Taleo/Eightfold)**: no separate "company portal" exists
   — confirmed directly that BAE Systems' own marketing careers page redirects into an
   Incapsula/Imperva bot-challenge rather than real content, a second independent wall unrelated
   to the already-found Taleo prohibition. Going to the employer's own site doesn't create a new
   option for any of the 7 — it's the same vendor domain already checked.
2. **BT, VodafoneThree, Sainsbury's**: their own domain already serves the real job content
   (already fetched in prior passes). Checked each employer's own general website terms
   specifically: BT and VodafoneThree have none at all (genuinely neutral); Sainsbury's has one
   but it's bot-protected and unreachable. Crucially, none of the 3 has a purpose-built public
   API the way Greenhouse/Lever/Ashby/Workable do — building against them would mean real HTML
   scraping against an undocumented page, the same weight as the already-identified "Custom
   careers-page adapter" deferred category, not a quick technical win.

Separate finding: Civil Service Jobs is itself actively bot-challenged, making its Open
Government Licence status moot in practice.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Data Source Documentation | `EMPLOYER_PANEL.md` | update — new section documenting this cross-cutting finding |
| Everything else | — | no-change — no code, no schema, no new tracked company |

## Execution Plan

- [x] Step 1: Confirmed directly that BAE Systems' own marketing site doesn't serve real content to automated requests (Incapsula challenge)
- [x] Step 2: Checked BT's and VodafoneThree's careers-site footers for a general website Terms of Use — found none for either
- [x] Step 3: Located and attempted to fetch Sainsbury's own Terms & Conditions — bot-protected, unreachable
- [x] Step 4: Confirmed Civil Service Jobs is itself bot-challenged via a direct fetch
- [x] Step 5: Updated `EMPLOYER_PANEL.md` with the full cross-cutting finding

## Decision Log
- 2026-09-20: Distinguished "no restriction found" (sufficient for Greenhouse/Lever/Ashby/
  Workable, each with a purpose-built public API) from "no restriction found, but also no
  purpose-built feed" (BT/VodafoneThree/Sainsbury's) — the latter doesn't carry the same weight
  and belongs in the Custom careers-page adapter deferred category instead.
