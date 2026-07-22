---
id: ai-provider-abstraction
date: 2026-07-01
trigger-type: internal
change-type: technical-refactor
outcome: ai-provider-flexibility
status: complete
---

# Change Request: AI provider abstraction layer

## Signal
See: `research/2026-07-01-multi-ai-provider.md`

## Outcome
See: `outcomes/ai-provider-flexibility.md`

## Change Type
`technical-refactor` — introduce a provider abstraction layer so that:
- each feature's AI provider is explicit at the call site
- a single feature can use more than one provider
- adding or swapping a provider touches only one adapter file, not business logic

No user-facing behaviour changes. The frontend stream contract is unchanged.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/ai-provider-flexibility.md` | create |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Specs | all | no-change |
| Frontend Specs | all | no-change |
| Backend Spec (market-health) | `backend/specs/market-health/api.md` | update — document provider abstraction in Tech Decisions |
| Backend Spec (ai-reasoning-panel) | `backend/specs/ai-reasoning-panel/api.md` | update — same |
| Backend Implementation | `backend/src/` | update |
| Frontend Implementation | `frontend/src/` | no-change |

## Execution Plan

- ✅ Step 1: `/new-backend-spec` — update `backend/specs/market-health/api.md` and `backend/specs/ai-reasoning-panel/api.md`: document the provider adapter contract and call-site provider declaration pattern in Tech Decisions
- ✅ Step 2: `/implement-backend` — implement the provider abstraction layer in `backend/src/`

## Decision Log
- 2026-07-01: Mapped to `ai-provider-flexibility` (new quality outcome created in same session). Change type is `technical-refactor` — no experience spec or frontend changes because the stream contract and API surface are unchanged. Automatic/magic provider routing is explicitly out of scope per the outcome; provider choice is always a deliberate call-site declaration.
