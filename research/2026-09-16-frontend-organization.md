---
source: stakeholder-request
date: 2026-09-16
---

"I would like to keep things well organised, starting from the front-end, I would like to keep
the stories well organised and separated from the main structure of the page or from the new
mcp functionality and from the login functionality. what would you recommend?"

Follow-up, after a proposed structure and a dead-code audit were presented: "great lets go with
your recommendation" — approving all of the following:

1. Delete 11 confirmed-dead files from `frontend/src/features/market-health/` (traced by import,
   not guessed — nothing reachable from the real app imports them): `ConversationalArea.tsx`,
   `ExceptionBanner.tsx`, `FilterControls.tsx`, `ProvenancePanel.tsx`, `SearchImplication.tsx`,
   `TrendGrid.tsx`, `UXvsPMChart.tsx`, `TrendChart.tsx`, `MarketHealthSignal.tsx`,
   `PromptBadge.tsx`, `PromptViewer.tsx`.
2. Split the remaining 19 live files into three subfolders by role:
   - `features/market-health/layout/` — the page chrome present on every task: `TopBar`,
     `TaskPanel`, `ConversationThread`, `OutputPanel`, `ChatInput`, `AITurn`, `UserTurn`,
     `SuggestedQuestions`.
   - `features/market-health/stories/` — the data-story catalogue, deterministic/no-model
     content: `WelcomeMessage`, `DataStoryMessage`, `StoryBlock`, `RankedBarList`,
     `StoryFigure`, `Meter`, `YearOnYearBars`, `EmploymentRiskStoryMessage`, `WorldRiskMap`.
   - `features/market-health/hiring-status/` — the one pinned-feature task, not a story:
     `JobOpeningsChart`, `MarketBriefingMessage`.

Context: this followed directly from a broader conversation about the user feeling they were
"losing control of everything that is happening" as the product grew (specifically triggered by
today's bring-your-own-AI-agent feature launch and its production debugging). That conversation
already produced `OVERVIEW.md` (a plain-language capability map) and a new framework-wide rule
requiring it to be kept current. This request is the same underlying concern — staying able to
navigate and understand the product as it grows — applied to the frontend codebase's own
organization specifically. `features/mcp-access/` and `features/account/` were checked and are
already properly isolated; the gap was entirely inside the pre-existing, never-reorganized
`features/market-health/` folder.
