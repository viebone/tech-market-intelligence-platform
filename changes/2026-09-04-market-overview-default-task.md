---
id: market-overview-default-task
date: 2026-09-04
trigger-type: stakeholder-request
change-type: ux-change, technical-refactor
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Open on the market overview

## Signal

See: `research/2026-09-04-market-overview-default-task.md`

## Outcome

`outcomes/understand-market-health-before-searching.md` - give a professional a clear market
orientation quickly before they explore a narrower question.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Information Architecture | `design/information-architecture.md` | update - market overview is the default task |
| Experience Spec | `design/market-health/experience.md` | update - first-load behavior |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update - default task state |
| Backend Spec | `backend/specs/market-health/api.md` | no-change |
| Frontend Implementation | `frontend/src/` | update |
| Backend Implementation | `backend/src/` | no-change |

## Execution Plan

- [x] Capture signal and map it to the existing outcome.
- [x] Confirm the predefined story path uses no LLM call.
- [x] Update IA, experience, and frontend architecture specs.
- [x] Make the market overview the default selected task.
- [x] Validate frontend build and diagnostics.

## Decision Log

- 2026-09-04: The default task becomes `market-data-briefing`; users can still select
  `market-health` from the task panel.
- 2026-09-04: Clicking the predefined story calls `POST /api/market-health/stories/{story_id}`
  only. It runs database aggregates and does not invoke `/api/chat`, `LLMProvider`, or consume
  LLM tokens.
- 2026-09-04: Frontend `npm run build` passed and the touched page has no diagnostics.