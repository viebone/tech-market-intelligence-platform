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

**Stakeholder direction (2026-09-06):** "each tab is an independent conversation. the chat
will allow the user to query in that tab." The answer and the follow-up conversation stay in
the task the question was asked from — the chat input is never a redirect.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Experience Spec | `design/market-health/experience.md` | update — each task is an independent conversation; the chat input queries the active task |
| Information Architecture | `design/information-architecture.md` | update — Task Panel items are conversations; the Working Space shows the active task's conversation |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — `useChat({ id: activeTaskId })`, per-task conversation, chips on every task |
| Frontend Implementation | `frontend/src/pages/MarketHealthPage.tsx`, `ConversationThread.tsx` | update |
| Backend | — | no-change |

## Execution Plan

- [x] Capture the signal.
- [x] Root-cause: `ChatInput` renders unconditionally; `ConversationThread` rendered the
      conversation only in the `HIRING_STATUS_TASK_ID` branch; default task moved away from it.
- [x] First attempt (commit `99bccce`, superseded): submitting switched `activeTaskId` to
      hiring-status. Rejected by the stakeholder — the conversation should stay in the tab it
      was asked from.
- [x] **Fix (2026-09-06): each task is its own conversation.** `useChat({ id: activeTaskId })`
      keys the message list / streamed data / loading state per task, so switching tasks
      switches the conversation. `ConversationThread` restructured so every task renders:
      its opening turn (welcome / chart+summary / story) → the suggested-question chips → that
      task's own conversation turns. The chat input queries the active task; it never
      redirects.
- [x] `SuggestedQuestions` chips render on every task (below the opening turn).
- [x] Update the experience + frontend specs.
- [x] Validate: `npm run build`, `tsc`.

## Decision Log

- 2026-09-06: First fix routed every question into the hiring-status conversation. Stakeholder
  corrected it: "each tab is an independent conversation. the chat will allow the user to
  query in that tab." So the model is per-task conversations, not one global thread.
- 2026-09-06: Implemented with `useChat({ id })` — the Vercel AI SDK keys `messages`,
  `streamData`, `isLoading`, and `error` by `[api, id]` via SWR, so one hook instance with a
  changing `id` gives fully isolated per-task histories. No manual conversation store needed.
- 2026-09-06: A stream in flight when the user switches tabs completes in its origin tab (its
  `mutate` closure is bound to the old key) — the answer lands where it was asked. Acceptable;
  documented as the intended behaviour, not an edge-case bug.
- 2026-09-06: The chat input stays visible on every task (`design/foundations.md` dual-mode
  interaction; IA's "fixed, always visible") — it now has somewhere to put the answer on
  every task.
