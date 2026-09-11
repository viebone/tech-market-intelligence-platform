---
id: employment-risk-12-month-window
date: 2026-09-11
trigger-type: stakeholder-request
change-type: ux-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Employment risk story — 90 days → 12 months

## Signal
See: `research/2026-09-11-employment-risk-12-month-window.md`

## Outcome
No change — same story (Story 2), refined the same day it shipped.

## Change Type
`ux-change` — widens the story's time window, a deliberate design decision, not a defect fix
(the 90-day window worked exactly as specified; the real UK data simply fell outside it).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Data Story spec | `design/market-health/data-stories.md` (Story 2) | update — 90 days → 12 months |
| Backend Implementation | `backend/src/market_stories.py` | update — `_EMPLOYMENT_RISK_WINDOW` |

## Execution Plan

- [x] Step 1: Update `design/market-health/data-stories.md`
- [x] Step 2: `/implement-backend` — update the constant, verify against real production data
      (the 2 real UK events + 25 US events must all appear correctly)

## Decision Log
- 2026-09-11: Real UK Companies House data surfaced the reason this decision needed making —
  a case's own date (when insolvency actually began) can be much older than when the Streaming
  API happens to push a live update about it, so "recent stream activity" and "recent market
  activity" aren't the same thing. 12 months is a better fit for that reality than 90 days —
  still bounded (not literally all-time), but wide enough that a live-tailed update on an
  older case isn't silently dropped.
