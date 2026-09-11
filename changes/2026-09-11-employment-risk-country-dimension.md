---
id: employment-risk-country-dimension
date: 2026-09-11
trigger-type: stakeholder-request
change-type: bug-fix, ux-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Employment risk story — country dimension, not state

## Signal
See: `research/2026-09-11-employment-risk-country-dimension.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — no change, same story (Story 2,
`changes/2026-09-11-employment-events-independent-scope.md`) refined the same day it shipped.

## Change Type
`bug-fix` (the spec's own "Where it's happening" block conflates two different granularities —
US state codes and country codes — in one ranked list, which stops being a meaningful ranking
the moment a second country's data exists) + `ux-change` (the fix is a real content decision:
country as the dimension, state detail deliberately deferred).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Experience / Data Story spec | `design/market-health/data-stories.md` (Story 2) | update — "Where it's happening" becomes "By country", `COALESCE(region, country)` dropped in favour of `country` alone |
| Backend Spec | `backend/specs/market-health/api.md` | no-change — Story 2's contract lives in data-stories.md, not duplicated here |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | no-change — `EmploymentRiskStoryMessage` already consumes a generic ranked-list section; only its content key/heading change, not its shape |
| Backend Implementation | `backend/src/market_stories.py` | update — `build_employment_risk_overview()`'s region query |
| Frontend Implementation | `frontend/src/features/market-health/EmploymentRiskStoryMessage.tsx` | update — section id/key rename, heading |

## Execution Plan

- [x] Step 1: Update `design/market-health/data-stories.md` — Story 2's "Where it's happening"
      → "By country"
- [x] Step 2: `/implement-backend` — `market_stories.py`: group by `country` only
- [x] Step 3: `/implement-frontend` — `EmploymentRiskStoryMessage.tsx`: consume the renamed
      section
- [x] Step 4: Verify against real production data + a real `npm run build`

## Decision Log
- 2026-09-11: Classified `bug-fix` over pure `ux-change` — the original design (merging state
  and country into one list) was always going to break the moment a non-US source went live;
  today's single-country dataset just made it visible sooner. State-level detail is deferred,
  not dropped — `region` stays a stored column, just not surfaced in this block for now; a
  future story or drill-down can reintroduce it once there's a reason to compare states within
  one country rather than countries against each other.
