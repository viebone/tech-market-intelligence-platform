---
id: chat-stream-protocol-fix
date: 2026-07-01
trigger-type: bug
change-type: bug-fix
outcome: ai-reasoning-transparency
status: complete
---

# Change Request: Fix chat stream protocol mismatch

## Signal
Chat input triggers no real AI response. Backend sends Vercel AI SDK data-stream format
(2:/0:/d: prefixes). Frontend ConversationalArea.tsx uses streamProtocol: "text", which
treats the entire response as plain text and renders raw protocol bytes as message content.

## Outcome
See: `outcomes/ai-reasoning-transparency.md`

## Change Type
`bug-fix` — code is wrong, spec is correct. The backend spec describes the data-stream wire
format; the frontend should use streamProtocol: "data" to parse it correctly.
No spec changes needed.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Experience Spec | `design/ai-reasoning-panel/experience.md` | no-change |
| Frontend Spec | `frontend/specs/ai-reasoning-panel/architecture.md` | no-change |
| Backend Spec | `backend/specs/market-health/api.md` | no-change |
| Frontend Implementation | `frontend/src/features/market-health/ConversationalArea.tsx` | update |
| Backend Implementation | `backend/src/` | no-change |

## Execution Plan

- ✅ Step 1: Fix `streamProtocol: "text"` → `streamProtocol: "data"` in `ConversationalArea.tsx`

## Decision Log
- 2026-07-01: Pre-existing bug — streamProtocol was wrong before the Gemini migration too.
  The backend has always used the Vercel AI SDK data-stream format. No spec is ambiguous;
  this is a straightforward frontend config error.
