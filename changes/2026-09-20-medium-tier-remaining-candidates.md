---
id: medium-tier-remaining-candidates
date: 2026-09-20
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Real research on the panel's 3 remaining Medium-tier candidates (no code change)

## Signal
User: "lets go to the medium/small for now" — moving off the exhausted Large-employer tier
(0 of 12 currently buildable) to the panel's last 3 unresolved Medium candidates: Sage, Softcat,
AJ Bell.

## Outcome
See: `outcomes/job-data-source-flexibility.md` — same panel-research weight as every prior
verification/licence-check pass.

## Change Type
`content-change` — documentation only. No code touched; no adapter built.

## What was found
See `research/2026-09-20-medium-tier-remaining-candidates.md` for full detail.

- **AJ Bell**: real platform correction — SmartRecruiters (`AJBell1`), not the previously-
  suspected Oracle Recruiting Cloud/HCM. Its public Postings API was tested directly and works
  cleanly (real 200, 19 jobs, same shape as Greenhouse). **Deliberately not built**: SAP's own
  API Policy (fetched directly, v.4.2026a) explicitly prohibits "scraping, harvesting, or
  systematic and/or large-scale data extraction or replication" — same shape of finding as
  Workday/Taleo, and it blocks the whole SmartRecruiters platform, not just AJ Bell.
- **Softcat**: found to be actively bot-challenged (AWS WAF `x-amzn-waf-action: challenge`), a
  materially stronger and more decisive finding than the prior "platform unidentified" note.
  Recommended as a strong "do not build" signal, not merely unresolved.
- **Sage**: re-checked with a working page fetch (real 200 this time) and found no ATS vendor
  markers of any kind — confirms rather than changes the existing "genuinely unidentified,
  needs a real browser network trace" finding.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Data Source Documentation | `EMPLOYER_PANEL.md` | update — Sage/Softcat/AJ Bell rows updated; "Next ATS adapters" table's SmartRecruiters row marked ❌ blocked, same treatment as Workday/Taleo |
| Everything else | — | no-change — no code, no schema, no new tracked company |

## Execution Plan

- [x] Step 1: Fetched AJ Bell's live careers page directly, found and resolved the real SmartRecruiters short-link, corrected the earlier wrong Oracle guess
- [x] Step 2: Tested SmartRecruiters' public Postings API directly with a real HTTP request (not assumed from documentation alone)
- [x] Step 3: Found and fetched the actual SAP API Policy PDF directly, quoted the relevant prohibition verbatim
- [x] Step 4: Inspected Softcat's real response headers, found the active WAF challenge
- [x] Step 5: Re-fetched Sage's careers page with a working request and searched exhaustively for platform markers — confirmed, not changed, the existing "unidentified" status
- [x] Step 6: Updated `EMPLOYER_PANEL.md` with all 3 findings

## Decision Log
- 2026-09-20: Applied the same "reachable ≠ permitted" standard to SmartRecruiters as
  Workday/Taleo — a clean, working, unauthenticated public API is still not evidence of
  permission once the parent company's own policy explicitly prohibits systematic extraction.
- 2026-09-20: Treated Softcat's active bot challenge as a stronger signal than a passive
  "platform unidentified" — an active technical control against automated access deserves the
  same respect as an explicit written prohibition, not treated as a puzzle to solve.
