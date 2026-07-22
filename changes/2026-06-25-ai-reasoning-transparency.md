---
id: ai-reasoning-transparency
date: 2026-06-25
trigger-type: user-feedback
change-type: new-feature
outcome: ai-reasoning-transparency (to be created)
status: complete
---

# Change Request: AI Reasoning Transparency

## Signal
See: `research/2026-06-25-ai-reasoning-transparency.md`

## Outcome
To be created — see Step 1 of execution plan.

## Change Type
`new-feature` — product-wide principle: every AI response must be auditable.
This is not a one-off feature but a design principle to be encoded in foundations
and inherited by every experience spec.

## Design Direction
Full inspectability without overwhelming the user. Reference pattern: Claude AI / ChatGPT
thinking panels. "View thinking / Hide thinking" toggle, expandable/collapsible, pushes
content down. Shows: inputs, tools accessed, data sources, reasoning steps.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/ai-reasoning-transparency.md` | create |
| Design Foundations | `design/foundations.md` | create — encode transparency as a core UX principle |
| Information Architecture | `design/information-architecture.md` | create |
| Visual Design | `design/visual-design.md` | create — define thinking panel as standard component |
| Experience Spec | `design/market-health-overview/experience.md` | create (first feature to implement it) |
| Frontend Spec | `frontend/specs/market-health-overview/architecture.md` | create |
| Backend Spec | `backend/specs/market-health-overview/api.md` | create |
| Frontend Implementation | `frontend/src/` | update |
| Backend Implementation | `backend/src/` | update |

## Execution Plan

- ✅ Step 1: `/new-outcome` — `outcomes/ai-reasoning-transparency.md` created
- ✅ Step 2: `/new-design-foundations` — already exists and active; Principle 4 already encodes this
- ✅ Step 3: `/new-information-architecture` — Reasoning Panel added as universal inline primitive; Task types defined; taxonomy updated
- ✅ Step 4: `/new-visual-design` — Reasoning Panel toggle defined: tertiary link (text-xs gray-500), arrow ↓/↑, generation time on same line, positioned after subtitle before answer, expands inline pushing content down
- ✅ Step 5: `/new-experience` — `design/ai-reasoning-panel/experience.md` created, directive: high
- ✅ Step 6: `/new-backend-spec` — `backend/specs/ai-reasoning-panel/api.md` created; reasoning trace as first stream event in existing /api/chat; extends market-health contract
- ✅ Step 7: `/new-frontend-spec` — `frontend/specs/ai-reasoning-panel/architecture.md` created; ReasoningPanel component spec, trace state via refs+onFinish, extends existing AIMessage and MarketHealthPage
- ✅ Step 8: `/implement-backend` — `backend/src/models.py` extended with `SourceAccess`, `ReasoningStep`, `ReasoningTrace`; `backend/src/chat.py` rewritten with `_build_reasoning_trace()`, structured SSE events (`text/event-stream`), trace emitted as first stream event before tokens, `finish_message` with `generation_time_ms`
- ✅ Step 9: `/implement-frontend` — `ReasoningPanel.tsx` created; `AITurn.tsx` extended with `trace`/`generationTimeMs`/`isStreaming` props; `ConversationThread.tsx` replaces `chatProvenances` with `traces` map; `MarketHealthPage.tsx` switches to `streamProtocol: "data"`, captures trace events via refs+offset, commits in `onFinish`; backend stream format changed to Vercel AI SDK line format (`2:`, `0:`, `d:` prefixes)

## Decision Log
- 2026-06-25: Classified as product-wide design principle, not a feature spec. Outcome needed first
  to anchor it before it becomes a foundation rule. Applies to every AI response in the platform.
- 2026-06-25: Design direction confirmed — full inspectability, no overwhelm, reference: Claude AI /
  ChatGPT thinking panels. "View thinking / Hide thinking" toggle as standard component.
