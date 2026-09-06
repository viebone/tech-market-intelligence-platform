source: bug
date: 2026-09-06

Testing the deployed build: on the local (and prod) app, typing a question into the
always-visible chat input and submitting does nothing visible — no user turn, no response,
no error.

Cause: `ChatInput` is rendered unconditionally in `MarketHealthPage`, but
`ConversationThread` only renders the `useChat` follow-up conversation inside the
`activeTaskId === "market-health"` (Tech market hiring status) branch. The welcome branch
("About this platform") and the story branches render only their own content. Since
`changes/2026-09-04-market-overview-default-task.md` and then
`changes/2026-09-04-about-this-platform-welcome.md` moved the default task away from
hiring-status, the app now loads with a chat input that visibly accepts a question and
silently drops the answer.

The suggested-question chips (`SuggestedQuestions`, added
`changes/2026-09-03-chat-resilience-and-instant-answers.md`) have the same problem — they
only render in the hiring-status branch, so they are invisible on first load.

Expected: the chat input is "the conversation". Asking a question from any task should show
the conversation. `design/market-health/experience.md` / `design/information-architecture.md`
describe the chat input as fixed and always available; a dead input contradicts that.
