---
id: large-employer-ats-research-pass5
date: 2026-09-20
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Real ATS research on the remaining 7 Large-employer panel candidates (no code change)

## Signal
User: "ok lets push the panel forwards" — continuing the Large-employer research
(`changes/2026-09-20-large-employer-ats-research.md` covered 5 of 12; this pass covers the
remaining 7: Sainsbury's, BT Group, VodafoneThree, Sky, BAE Systems, Rolls-Royce, Civil Service).

## Outcome
See: `outcomes/job-data-source-flexibility.md` — same panel-research weight as every prior
verification pass. This one produced no new tracked companies (0 added), but real findings
worth recording so a future pass doesn't repeat this research.

## Change Type
`content-change` — documentation only. No code touched; no company added to any `COMPANIES` list.

## What was found
See `research/2026-09-20-large-employer-pass5-findings.md` for full detail. Summary: real
platform identification for all 7 — Sainsbury's (Oracle Recruiting Cloud/HCM), BT Group (SAP
SuccessFactors), VodafoneThree (Attrax/Phenom), Sky (Oracle Taleo, at least one instance), BAE
Systems (Oracle Taleo), Rolls-Royce (Workday — already blocked, same decision as Barclays/
AstraZeneca applies, no new decision needed), Civil Service (still no official API, matches
existing expectation).

A real, half-open technical lead: Taleo's `careersection/rest/jobboard/searchjobs` endpoint is
live (confirmed via direct HTTP — 405 on GET, 400 on a guessed POST body, neither a 404) across
3 now-confirmed Taleo employers (Tesco, BAE Systems, Sky) — one adapter there could unlock all
three at once, matching this project's adapter-not-per-company-scraper philosophy. **Not built**:
Oracle's own Taleo terms of use weren't found (unlike Workday's explicit prohibition), so this is
recorded as reachable-but-unconfirmed, not cleared — same bar as Tesco's original finding.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Data Source Documentation | `EMPLOYER_PANEL.md` | update — 7 candidate-table rows updated with real findings, "Next ATS adapters" table gains Attrax and a firmer Oracle HCM/Recruiting Cloud entry (now 2 real sightings: Sainsbury's + suspected AJ Bell) |
| Everything else | — | no-change — no code, no schema, no new tracked company |

## Execution Plan

- [x] Step 1: Real research (WebSearch) on all 7 remaining Large-employer candidates
- [x] Step 2: Real content-inspection WebFetch (not just search summaries) confirmed 3 of the 7 platforms via actual CDN/URL evidence in the live page (Sainsbury's, BT Group, VodafoneThree)
- [x] Step 3: Verified BAE Systems' Taleo instance and its REST endpoint directly via real HTTP requests (200 / 405 / 400 — endpoint genuinely live, not guessed)
- [x] Step 4: Checked for Oracle Taleo's own terms of use before treating the REST lead as buildable — none found; recorded as unconfirmed, not cleared, same bar as every other source
- [x] Step 5: Recognized Rolls-Royce as another Workday tenant, requiring no new decision (already blocked, 2026-09-20)
- [x] Step 6: Updated `EMPLOYER_PANEL.md` with all 7 real findings

## Decision Log
- 2026-09-20: Applied the same "reachable ≠ permitted" standard to the new Taleo REST lead as
  Workday/Indeed/Reed — a live, non-404 endpoint is evidence worth recording, not evidence enough
  to build against.
- 2026-09-20: Rolls-Royce's Workday finding required no separate decision — it inherits the
  existing block from the Barclays/AstraZeneca research the same day.
