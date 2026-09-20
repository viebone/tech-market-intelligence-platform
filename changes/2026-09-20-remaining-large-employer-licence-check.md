---
id: remaining-large-employer-licence-check
date: 2026-09-20
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Licence check on the 4 remaining unchecked Large-employer platforms (no code change)

## Signal
User: "yes go ahead" — continuing the licence-check work after the Oracle Taleo finding, on the
4 platforms from pass 5 that hadn't been checked yet: Sainsbury's (Oracle Recruiting Cloud/HCM),
BT Group (SAP SuccessFactors), VodafoneThree (Attrax/Phenom), HSBC (Eightfold.ai).

## Outcome
See: `outcomes/job-data-source-flexibility.md` — same panel-research weight as every prior
licence-check pass.

## Change Type
`content-change` — documentation only. No code touched; no adapter built.

## What was found
See `research/2026-09-20-remaining-large-employer-licence-check.md` for full detail. Unlike
Oracle Taleo and Workday (whose career sections live entirely on the vendor's own domain, making
whose-terms-apply unambiguous), these 4 are white-labeled deployments — the visible domain and
every visible legal link belong to the employer, not the platform vendor. No cleanly-applicable
vendor Terms of Use was found directly for any of the 4 the way Oracle's and Workday's were.
`robots.txt` was checked directly for all 4 (real, unambiguous): Sainsbury's is fully open with
an explicit `Crawl-delay: 10`; HSBC explicitly allows `/careers` and related paths despite a
default-deny; BT doesn't disallow job listing paths; VodafoneThree explicitly disallows
`/jobs?*` — the one clear negative signal.

**Honest conclusion: genuinely unresolved for all 4** — no confirmed vendor prohibition (unlike
Oracle/Workday) and no confirmed permission either. A permissive `robots.txt` is a necessary
check under this project's Rule 13, never a substitute for a real licence record. None of the 4
are cleared to build against, but none are cleanly blocked either.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Data Source Documentation | `EMPLOYER_PANEL.md` | update — Sainsbury's/BT Group/VodafoneThree/HSBC rows updated with the honest unresolved status and their real robots.txt findings |
| Everything else | — | no-change — no code, no schema, no new tracked company |

## Execution Plan

- [x] Step 1: Attempted to find and directly fetch each vendor's own applicable Terms of Use (Eightfold, SAP, Vodafone/Three) — none resolved cleanly the way Oracle's/Workday's did
- [x] Step 2: Confirmed directly (live page fetch) that HSBC's careers page shows only HSBC's own legal links, with Eightfold branding explicitly hidden — established these are white-label deployments, a materially different shape than Taleo/Workday
- [x] Step 3: Fetched `robots.txt` directly for all 4 real career-site domains
- [x] Step 4: Reported the honest, mixed, unresolved conclusion rather than forcing a clean blocked/cleared call either way
- [x] Step 5: Updated `EMPLOYER_PANEL.md` with all 4 findings

## Decision Log
- 2026-09-20: Recognized these 4 as a materially different situation from Oracle Taleo/Workday
  (vendor-branded-domain cases) rather than applying the same blocked/cleared binary — an honest
  "still unresolved" is a real, distinct outcome, not an unfinished one.
