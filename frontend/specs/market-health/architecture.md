---
id: market-health
experience: market-health
directive: low
status: draft
created: 2026-06-13
updated: 2026-06-15
---

# Market Health — Frontend Architecture Spec

## Experience this implements
See: `design/market-health/experience.md`

---

## Layout

Three persistent zones, all CSS-driven — no JavaScript scroll management.

```
┌─────────────────────────────────────────┐  ← fixed, z-index top
│  TopBar                                 │
├─────────────────────────────────────────┤
│                                         │
│  ConversationThread  (scrollable)       │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ MarketBriefingMessage           │    │  ← auto-generated on load
│  │  MarketHealthSignal             │    │
│  │  SearchImplication              │    │
│  │  FilterControls                 │    │
│  │  TrendGrid                      │    │
│  │  [view prompt]                  │    │
│  └─────────────────────────────────┘    │
│                                         │
│  UserMessage …                          │
│  AIMessage …                            │
│                                         │
├─────────────────────────────────────────┤  ← fixed, z-index top
│  ChatInput (full width)                 │
└─────────────────────────────────────────┘
```

---

## Component Breakdown

| Component | Responsibility | Location |
|---|---|---|
| `MarketHealthPage` | Top-level page. Owns filter state. Coordinates data fetching. Composes all zones. | `frontend/src/pages/MarketHealthPage.tsx` |
| `TopBar` | Fixed header. Product title only. No navigation in v1. | `frontend/src/features/market-health/TopBar.tsx` |
| `ConversationThread` | Scrollable message list between TopBar and ChatInput. Renders the briefing message, user messages, and AI follow-up messages. Auto-scrolls to bottom on new messages. | `frontend/src/features/market-health/ConversationThread.tsx` |
| `MarketBriefingMessage` | The first message in the thread. Rendered from REST API data (not streamed). Contains the full market briefing: signal, implication, filters, trend grid. Carries a `PromptBadge`. | `frontend/src/features/market-health/MarketBriefingMessage.tsx` |
| `PromptBadge` | Small affordance shown on every AI-sourced message. On click, opens `PromptViewer`. Receives the prompt text as a prop. | `frontend/src/features/market-health/PromptBadge.tsx` |
| `PromptViewer` | Read-only overlay showing the prompt behind an AI message. No editing. Dismissible. | `frontend/src/features/market-health/PromptViewer.tsx` |
| `ChatInput` | Fixed, full-width input bar pinned to the bottom of the viewport. Handles text input and submit. Emits message upward. | `frontend/src/features/market-health/ChatInput.tsx` |
| `MarketHealthSignal` | Displays the current verdict, one-sentence explanation, and Data Freshness label. Used inside `MarketBriefingMessage`. | `frontend/src/features/market-health/MarketHealthSignal.tsx` |
| `SearchImplication` | Plain-language statement beneath the signal. Used inside `MarketBriefingMessage`. | `frontend/src/features/market-health/SearchImplication.tsx` |
| `FilterControls` | Role family, seniority, location, and time range selectors. Emits filter changes upward to page. Used inside `MarketBriefingMessage`. | `frontend/src/features/market-health/FilterControls.tsx` |
| `TrendGrid` | Grid of demand, compensation, and layoff signals. Receives filtered data as props. Used inside `MarketBriefingMessage`. | `frontend/src/features/market-health/TrendGrid.tsx` |
| `TrendChart` | Individual trend chart with direction indicator and Data Freshness label. | `frontend/src/features/market-health/TrendChart.tsx` |
| `DataFreshnessLabel` | Reusable label showing age and source of a data-backed claim. | `frontend/src/components/DataFreshnessLabel.tsx` |

---

## State Management

**Filter state** lives in `MarketHealthPage` as local React state. Passed as props to `MarketBriefingMessage` → `FilterControls`. When filters change, TanStack Query refetches and `MarketBriefingMessage` re-renders in place — the opening message updates, the conversation thread below it is unaffected.

**Conversation state** is managed by the `useChat` hook (Vercel AI SDK). It handles user messages and AI follow-up responses only — the opening briefing is not part of the `useChat` message history. `useChat` starts with an empty message list.

**Prompt viewer state** is local to `PromptBadge` / `PromptViewer` — a single boolean open/closed flag.

No global Zustand store required for v1.

---

## Opening Prompt

The `MarketBriefingMessage` is not AI-streamed — it is rendered from data fetched via the existing REST endpoints. The "prompt" it represents is a static string stored as a constant, shown verbatim when the user taps "view prompt":

```
"Give me the current market health signal and search implication, followed by demand signals,
compensation signals, and layoff signals — with filter controls so I can narrow by role,
seniority, and location. I want to assess the current state of the tech job market."
```

This string is defined once in `MarketBriefingMessage.tsx` and passed to `PromptBadge` as a prop.

---

## Data Requirements

| Data | Source | When fetched |
|---|---|---|
| Market Health Signal + Search Implication | `GET /api/market-health/summary` | On page load; refetch when filters change |
| Trend data (Demand, Compensation, Layoff Signals) | `GET /api/market-health/trends` | On page load; refetch when filters change |
| Conversational follow-up responses | `POST /api/chat` (streaming) | On each user message via `useChat` |

The `GET /api/alerts/exceptions` call is removed from this layout — exceptions have no dedicated zone in the conversation model. Revisit when an alert system is designed.

---

## API Contract

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/market-health/summary` | Current Market Health Signal, Search Implication, and Data Freshness metadata. Accepts: `role`, `seniority`, `location`. |
| GET | `/api/market-health/trends` | Time-series data for Demand, Compensation, and Layoff Signals. Accepts: `role`, `seniority`, `location`, `period`. |
| POST | `/api/chat` | Accepts `{ messages: [...], context: { role, seniority, location } }`. Streams Claude response for user follow-up questions. |

---

## Tech Decisions

- **Vercel AI SDK `useChat`** for follow-up conversation only. The opening briefing is not streamed.
- **TanStack Query** for all REST data. Query keys: `['market-health', 'summary', filters]` and `['market-health', 'trends', filters]`.
- **CSS layout** for the three-zone structure: `TopBar` and `ChatInput` use `position: fixed`; `ConversationThread` uses padding-top and padding-bottom to clear both fixed zones.
- **Tailwind CSS** only — no additional component libraries.
- While briefing data reloads after a filter change, keep the previous content visible with a subtle loading indicator. Do not blank the briefing message.

---

## Out of scope

- Exception / alert banner (removed from this layout — no zone for it)
- Alert creation UI
- Company detail view
- Side-by-side market comparison
- Authentication and user session management
