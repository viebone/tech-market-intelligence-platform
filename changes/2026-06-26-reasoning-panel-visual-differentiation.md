---
id: reasoning-panel-visual-differentiation
date: 2026-06-26
trigger-type: stakeholder-request
change-type: visual-change
outcome: ai-reasoning-transparency
status: complete
---

# Change Request: Reasoning Panel — Visual Differentiation of Panel Content

## Signal
See: `research/2026-06-26-reasoning-panel-visual-differentiation.md`

## Outcome
See: `outcomes/ai-reasoning-transparency.md`

## Change Type
`visual-change` — feature-scoped. The reasoning panel content text is currently the same
grey (`gray-300`) as the main AI answer content. The panel should read as clearly secondary —
metadata about the answer, not the answer itself. Making the panel text slightly more muted
achieves this without structural change.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/ai-reasoning-transparency.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | update — reasoning panel content text token |
| Experience Spec | `design/ai-reasoning-panel/experience.md` | no-change |
| Frontend Spec | `frontend/specs/ai-reasoning-panel/architecture.md` | update — section content class |
| Backend Spec | `backend/specs/ai-reasoning-panel/api.md` | no-change |
| Frontend Implementation | `frontend/src/components/ReasoningPanel.tsx` | update |
| Backend Implementation | `backend/src/` | no-change |

## Execution Plan

- ✅ Step 1: Update `design/visual-design.md` — documented `bg-gray-800 border-y border-gray-700 py-4 px-4` as the panel wrapper; added rationale for background lift vs answer content
- ✅ Step 2: Update `frontend/specs/ai-reasoning-panel/architecture.md` — updated panel wrapper class to include `bg-gray-800 px-4`
- ✅ Step 3: `/implement-frontend` — applied `bg-gray-800 border-y border-gray-700 py-4 px-4 my-2 space-y-4` to panel wrapper in `ReasoningPanel.tsx`

## Decision Log
- 2026-06-26: Classified as feature-scoped visual-change. The panel content text colour is
  a reasoning panel token defined in visual-design.md — not a product-wide system colour.
  No UX flow or structural change. Cascades only to frontend spec and implementation.
