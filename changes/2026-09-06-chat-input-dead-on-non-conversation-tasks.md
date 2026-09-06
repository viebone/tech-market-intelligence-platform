---
id: chat-input-dead-on-non-conversation-tasks
date: 2026-09-06
trigger-type: bug
change-type: bug-fix
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Asking a question does nothing unless you're on the hiring-status task

## Signal

See: `research/2026-09-06-chat-input-dead-on-non-conversation-tasks.md`

## Outcome

`outcomes/understand-market-health-before-searching.md` — the conversation is how a
professional explores demand/skills/salary beyond the chart. A chat input that silently
drops answers fails that outright.

## Change Type

`bug-fix` — the code is wrong, the spec is not. `design/market-health/experience.md` (opening
prompt / User Flow) and `design/information-architecture.md` (ChatInput "fixed, always
visible") both treat the conversation as always available. The regression came in with the
default-task moves (`changes/2026-09-04-market-overview-default-task.md`,
`changes/2026-09-04-about-this-platform-welcome.md`) — `ConversationThread` only renders the
`useChat` messages inside the `market-health` (hiring-status) branch, and the default task is
no longer that branch.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Experience Spec | `design/market-health/experience.md` | update — one line: submitting a question from any task opens the hiring-status conversation |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — same, plus the SuggestedQuestions placement note |
| Frontend Implementation | `frontend/src/pages/MarketHealthPage.tsx`, `ConversationThread.tsx` | update |
| Backend | — | no-change |

## Execution Plan

- [x] Capture the signal.
- [x] Root-cause: `ChatInput` renders unconditionally; `ConversationThread` renders the
      conversation only in the `HIRING_STATUS_TASK_ID` branch; default task moved away from it.
- [x] Fix: submitting a chat message (typed) or tapping a suggested-question chip switches
      `activeTaskId` to `market-health` before sending, so the conversation is visible.
- [x] Show the `SuggestedQuestions` chips on the welcome too (below its own content), so the
      instant-answer path is reachable from the default landing view.
- [x] Update the experience + frontend specs.
- [x] Validate: `npm run build`, `tsc`, manual first-load flow.

## Decision Log

- 2026-09-06: The fix is "submitting routes you into the conversation", not "hide the chat
  input on other tasks" — the input being always available is the intended design
  (`design/foundations.md` dual-mode interaction; IA's "fixed, always visible"). The
  conversation is part of the hiring-status task; asking a question means you're now in it.
- 2026-09-06: Chips also added under the welcome's "what you can ask" area so the fast
  instant-answer path is visible on the default first-load view, not only after switching to
  hiring-status.
