---
id: frontend-organization
date: 2026-09-16
trigger-type: stakeholder-request
change-type: technical-refactor
outcome: codebase-stays-navigable-as-it-grows
status: complete
---

# Change Request: Reorganize `market-health`'s frontend into layout / stories / hiring-status, remove dead code

## Signal
See: `research/2026-09-16-frontend-organization.md`

## Outcome
See: `outcomes/codebase-stays-navigable-as-it-grows.md` (new — created for this change; no
existing outcome covered codebase organization).

## Change Type
`technical-refactor` — pure internal reorganization. No behavior change, no UI change, no new
capability. `features/mcp-access/` and `features/account/` need no change; they're already
properly isolated.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/codebase-stays-navigable-as-it-grows.md` | create (done) |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | no-change — nothing about the experience changes, only where its code lives |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — every moved component's Location path, plus removing `PromptBadge`/`PromptViewer` as confirmed dead (the spec currently documents them as real; the live app has neither) |
| Backend Spec | — | no-change |
| Frontend Implementation | `frontend/src/features/market-health/` | update — delete 11 dead files, move 19 live files into three new subfolders, update every import path that references a moved file |
| Backend Implementation | `backend/src/` | no-change |
| Plain-Language Overview | `OVERVIEW.md` | no-change — nothing about what the product *does* changes |

## Execution Plan

- [x] Step 1: Confirm a quality outcome exists — `outcomes/codebase-stays-navigable-as-it-grows.md` (done)
- [x] Step 2: Update `frontend/specs/market-health/architecture.md` — Location column for every moved component updated; `PromptBadge`/`PromptViewer` rows replaced with a removal note (done)
- [x] Step 3: Implement — 11 dead files deleted; `layout/`/`stories/`/`hiring-status/` created; 19 live files moved via `git mv` (history preserved); import paths fixed in the 3 files that needed it (`AITurn.tsx`, `ConversationThread.tsx`, `OutputPanel.tsx`) plus `pages/MarketHealthPage.tsx`; `tsc --noEmit` clean, `npm run build` clean (474 modules transformed, same as before — nothing lost; CSS bundle shrank 24.80kB → 19.95kB, confirming the dead files were contributing dead styles too) (done)

## Decision Log
- 2026-09-16: Triaged as `technical-refactor` (bucket C, no user-facing change). No existing outcome covered codebase organization — created `outcomes/codebase-stays-navigable-as-it-grows.md` (priority: medium, per the user's own choice) rather than silently reusing an unrelated one.
- 2026-09-16: Confirmed by tracing every import across the real app (not assumed) that 11 of `market-health/`'s 30 files are dead: `ConversationalArea`, `ExceptionBanner`, `FilterControls`, `ProvenancePanel`, `SearchImplication`, `TrendGrid`, `UXvsPMChart`, `TrendChart`, `MarketHealthSignal`, `PromptBadge`, `PromptViewer`. Three of these (`FilterControls`, `ProvenancePanel`, `ConversationalArea`) were already flagged dead in the spec's own 2026-08-11 review; the other 8 are new findings, including two (`PromptBadge`, `PromptViewer`) the frontend spec still documents as real, live components — a genuine spec-vs-code drift being corrected as part of this change, not left for a future one.
- 2026-09-16: Folder split agreed with the user: `layout/` (page chrome, present on every task), `stories/` (the data-story catalogue), `hiring-status/` (the one pinned-feature chart task, deliberately not filed under `stories/` since it isn't one per the IA's own Content Taxonomy).
