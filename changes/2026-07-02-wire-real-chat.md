---
id: wire-real-chat
date: 2026-07-02
trigger-type: bug
change-type: bug-fix
outcome: ai-reasoning-transparency
status: complete
---

# Change Request: Wire ChatInput to real useChat — remove demo simulation intercept

## Signal
See: `research/2026-07-02-chat-demo-not-wired.md`

## Outcome
See: `outcomes/ai-reasoning-transparency.md`

## Change Type
`bug-fix` — code is wrong, spec is correct. The real useChat hook exists in
MarketHealthPage.tsx but handleSubmit/input/handleInputChange are never used.
The demo simulation onSubmit intercepts every submission. No spec changes needed.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Experience Spec | `design/ai-reasoning-panel/experience.md` | no-change |
| Frontend Spec | frontend specs | no-change |
| Backend Spec | backend specs | no-change |
| Frontend Implementation | `frontend/src/pages/MarketHealthPage.tsx` | update |
| Backend Implementation | `backend/src/` | no-change |

## Execution Plan

- ✅ Step 1: Remove demo simulation state and onSubmit from MarketHealthPage.tsx; wire ChatInput to useChat's handleSubmit, input, and handleInputChange

## Decision Log
- 2026-07-02: Demo simulation was a deliberate placeholder built before the real backend
  existed. Now that Gemini is integrated and the backend is live, the demo intercept
  must be removed. activeDemoSim becomes null; DEMO_TRACE and DEMO_CONTENT can be dropped.
