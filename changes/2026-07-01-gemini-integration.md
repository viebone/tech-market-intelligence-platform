---
id: gemini-integration
date: 2026-07-01
trigger-type: internal
change-type: api-change
outcome: ai-reasoning-transparency
status: complete
---

# Change Request: Switch LLM provider from Anthropic to Gemini

## Signal
See: `research/2026-07-01-gemini-integration.md`

## Outcome
See: `outcomes/ai-reasoning-transparency.md`

## Change Type
`api-change` — replacing the Anthropic SDK with the Google Gemini SDK as the LLM provider
for the `/api/chat` endpoint and the reasoning trace generation. No user-facing behaviour
changes; the stream contract from the frontend's perspective is unchanged.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Research | `research/2026-07-01-gemini-integration.md` | create |
| Outcome | `outcomes/ai-reasoning-transparency.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/ai-reasoning-panel/experience.md` | no-change |
| Frontend Spec | `frontend/specs/ai-reasoning-panel/architecture.md` | no-change |
| Backend Spec (market-health) | `backend/specs/market-health/api.md` | update — swap Anthropic SDK → Gemini SDK in external dependencies; update error codes (502 Anthropic → Gemini) |
| Backend Spec (ai-reasoning-panel) | `backend/specs/ai-reasoning-panel/api.md` | update — replace Anthropic extended thinking with Gemini's thinking equivalent |
| Backend Implementation | `backend/src/` | update |
| Frontend Implementation | `frontend/src/` | no-change |

## Execution Plan

- ✅ Step 1: `/new-backend-spec` — update `backend/specs/market-health/api.md`: swap external dependency from Anthropic Python SDK to Google Gemini SDK; update `/api/chat` error codes and streaming approach to match Gemini's API
- ✅ Step 2: `/new-backend-spec` — update `backend/specs/ai-reasoning-panel/api.md`: replace Anthropic extended thinking with Gemini's thinking/reasoning capability; keep the same ReasoningTrace contract emitted to the frontend
- ✅ Step 3: `/implement-backend` — implement the Gemini integration in `backend/src/`

## Decision Log
- 2026-07-01: Mapped to `ai-reasoning-transparency` — the chat capability and AI response transparency are the core of that outcome. The provider swap is an internal implementation detail; the user experience and stream contract are unchanged. Gemini was chosen by the product owner who has already obtained and configured the API key.
