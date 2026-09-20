---
id: oracle-taleo-licence-check
date: 2026-09-20
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Oracle Taleo licence check (no code change)

## Signal
User: "ok go ahead with taleo research" — following up on the real, half-open Taleo REST-endpoint
lead surfaced in `changes/2026-09-20-large-employer-ats-research-pass5.md`.

## Outcome
See: `outcomes/job-data-source-flexibility.md` — same panel-research weight as every prior
verification/licence-check pass.

## Change Type
`content-change` — documentation only. No code touched; no adapter built.

## What was found
See `research/2026-09-20-oracle-taleo-licence-check.md` for full detail. Oracle's own **Web
Sites Terms of Use** (`oracle.com/legal/terms/`, fetched directly) explicitly prohibits "any
robot, spider, scraper or other automated means" without Oracle's express written permission,
scoped broadly to "the Oracle Web sites" — and `taleo.net` (the domain every Taleo career section
runs on, regardless of employer branding) is Oracle-owned, Oracle-operated infrastructure, an
arguably even clearer case of coverage than Workday's tenant-subdomain ambiguity was. Same shape
of finding as Indeed, Reed, and Workday: a technically-open, unauthenticated, confirmed-live
endpoint with an explicit written prohibition against exactly what an adapter would do.

**Decision: do not build a Taleo adapter without Oracle's express written permission.** This
affects all 3 currently-identified Taleo employers at once (Tesco, BAE Systems, Sky) — the
single biggest "one decision affects several employers" case in this panel so far.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Data Source Documentation | `EMPLOYER_PANEL.md` | update — Tesco/BAE Systems/Sky rows marked blocked-on-permission; "Next ATS adapters" table's Oracle Taleo row marked ❌ blocked, same treatment as Workday |
| Everything else | — | no-change — no code, no schema, no new tracked company |

## Execution Plan

- [x] Step 1: Checked the live Taleo career-section page itself for an Oracle-specific legal link (none found — only the employer's own cookie statement)
- [x] Step 2: Located and fetched Oracle's actual Web Sites Terms of Use directly (retried with a browser User-Agent after an initial 403 — real document, not a search summary)
- [x] Step 3: Quoted the scope definition and the robots/scraper prohibition verbatim, reasoned through whether `taleo.net` falls under "the Oracle Web sites" (concluded: yes, arguably more clearly than Workday's case)
- [x] Step 4: Applied the same "reachable ≠ permitted" decision already used for Indeed/Reed/Workday
- [x] Step 5: Updated `EMPLOYER_PANEL.md` — all 3 Taleo employer rows and the adapter backlog table

## Decision Log
- 2026-09-20: Extended the Workday precedent to Oracle Taleo — a live, non-404, technically
  reachable endpoint is not evidence of permission, regardless of how clean the API surface is.
  Blocking this closes out the single biggest remaining "quick win" the panel had left.
