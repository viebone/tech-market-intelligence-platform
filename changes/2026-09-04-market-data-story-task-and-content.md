---
id: market-data-story-task-and-content
date: 2026-09-04
trigger-type: stakeholder-request
change-type: ux-change, content-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Make the market data story a clear task

## Signal

See: `research/2026-09-04-market-data-story-task-and-content.md`

Related: `research/2026-09-04-market-data-stories.md` and
`changes/2026-09-03-chat-resilience-and-instant-answers.md`.

## Outcome

`outcomes/understand-market-health-before-searching.md` - the story supports a fast,
accessible market read before a professional commits to a search.

## Change Type

`ux-change`, `content-change`

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | update - add the story as a task above hiring status |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | update - task entry and concise visible briefing |
| Data Stories Spec | `design/market-health/data-stories.md` | update - visible content rules and summary shape |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update - task selection and story view |
| Backend Spec | `backend/specs/market-health/api.md` | no-change - existing live story contract is sufficient |
| Frontend Implementation | `frontend/src/` | update |
| Backend Implementation | `backend/src/` | no-change |
| Workspace Skill | `.claude/skills/end-user-content/SKILL.md` | create |

## Execution Plan

- [x] Capture stakeholder signal in `research/`.
- [x] Triage against `understand-market-health-before-searching`.
- [x] Confirm no existing end-user content skill.
- [x] Create the end-user content skill.
- [x] Update information architecture, experience, data-story, and frontend specs.
- [x] Move the story into the left Task Panel above hiring status.
- [x] Rewrite the visible story answer as a concise, non-technical market briefing.
- [x] Validate frontend build and diagnostics.

## Decision Log

- 2026-09-04: The story is a separate Query Task, not an inline suggested question. This
  matches the product's existing left-panel hierarchy model.
- 2026-09-04: The visible answer is intentionally smaller than the underlying data contract.
  Users get the business read first; technical detail remains inspectable through provenance.
- 2026-09-04: No backend change is needed. The existing deterministic endpoint already returns
  live values; this change affects task navigation and presentation content.
- 2026-09-04: Frontend build passed with `npm run build`; touched frontend files have no
  diagnostics and the product repository passes `git diff --check`.