---
id: large-employer-ats-research
date: 2026-09-20
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Real ATS research on the 12 Large-employer panel candidates (no code change)

## Signal
User: "ok go ahead" → "with 1" — picking option 1 from the "what's next in the panel" menu:
real ATS research on the 12 deliberately-deferred Large employers.

## Outcome
See: `outcomes/job-data-source-flexibility.md` — same panel-research weight as every prior
verification pass. This one produced no new tracked companies (0 added), but real findings
worth recording so the next pass doesn't repeat the same research.

## Change Type
`content-change` — documentation only. No code touched; no company added to any `COMPANIES`
list this pass.

## What was found

Real platform identification for 5 of 12 (see `EMPLOYER_PANEL.md`'s "Verification pass 4" for
full detail): Tesco → Oracle Taleo, Barclays → Workday, AstraZeneca → Workday, NatWest →
Cloudflare-blocked (platform unknown), HSBC → Eightfold.ai. The other 7 (Sainsbury's, BT Group,
VodafoneThree, Sky, BAE Systems, Rolls-Royce, Civil Service) weren't reached this pass.

**The real decision this pass produced**: Workday's public CXS job-search API is technically
excellent (confirmed real via 2 verification requests — Barclays 873 real jobs, AstraZeneca
confirmed too) but Workday's own Terms of Service explicitly prohibit scraping, automated data
extraction, and building applications that interact with their sites without prior written
consent (`research/2026-09-20-workday-licence-check.md`, exact clauses quoted). Same shape of
finding as the Indeed/Reed research (2026-09-19) — a technically-open endpoint with an explicit
written prohibition — and given the same treatment: **no adapter without explicit permission.**

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Data Source Documentation | `EMPLOYER_PANEL.md` | update — 5 rows updated with real findings, "Next ATS adapters" table updated (Workday marked blocked, Taleo/Eightfold added as newly-found unbuilt candidates) |
| Everything else | — | no-change — no code, no schema, no new tracked company |

## Execution Plan

- [x] Step 1: Real research (WebSearch + direct fetches) on 5 of 12 Large-employer candidates
- [x] Step 2: Verified Workday's technical claim with 2 real POST requests (Barclays, AstraZeneca) before deciding anything
- [x] Step 3: Checked Workday's own Terms of Service directly (not just search-summarized) — found explicit prohibitions, quoted verbatim in `research/2026-09-20-workday-licence-check.md`
- [x] Step 4: Presented the finding to the user with a clear recommendation (don't build without permission) — user confirmed: "lets skip workday for now"
- [x] Step 5: Updated `EMPLOYER_PANEL.md` with all 5 real findings and the Workday decision, so the next pass doesn't repeat this research

## Decision Log
- 2026-09-20: Applied the same standard to Workday as Indeed/Reed (2026-09-19) — a technically
  reachable, unauthenticated endpoint is not the same as permission. Explicit written
  prohibition found → don't build, regardless of technical quality.
- 2026-09-20: Recorded Tesco (Taleo) and HSBC (Eightfold.ai) as newly-discovered platforms with
  neither a confirmed public API nor a terms check yet — real, incremental findings, not fully
  resolved, and not silently dropped.
