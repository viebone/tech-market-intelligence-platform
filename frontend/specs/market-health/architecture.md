---
id: market-health
experience: market-health
directive: low
status: draft
created: 2026-06-13
updated: 2026-06-22
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
│  ┌──────────────────────────────────┐   │  ← first AI message, auto-rendered on load
│  │ AIMessage                        │   │
│  │   TrendChart (+ time selector)   │   │
│  │   WrittenSummary                 │   │
│  │   [view prompt]                  │   │
│  └──────────────────────────────────┘   │
│                                         │
│  UserMessage  ← first typed; title size │
│  AIMessage    ← follow-up response      │
│  UserMessage  ← subsequent; body size   │
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
| `MarketHealthPage` | Top-level page. Orchestrates the opening briefing fetch and the follow-up conversation. Composes all zones. | `frontend/src/pages/MarketHealthPage.tsx` |
| `TopBar` | Fixed header. Product title only. No navigation in v1. | `frontend/src/features/market-health/TopBar.tsx` |
| `ConversationThread` | Scrollable message list between TopBar and ChatInput. Renders the opening `AIMessage`, then user and AI follow-up messages in order. Auto-scrolls to bottom on new messages. | `frontend/src/features/market-health/ConversationThread.tsx` |
| `AIMessage` | Wraps an AI turn. Left-aligned. `bg-gray-800 rounded-xl py-5 px-6`. Carries a `PromptBadge`. For the opening message, renders `TrendChart` then `WrittenSummary`. For follow-up responses, renders streamed markdown text. | `frontend/src/features/market-health/AIMessage.tsx` |
| `UserMessage` | Wraps a user turn. Left-aligned, no background, no border. First message in the thread: `text-2xl font-semibold text-gray-100`. Subsequent messages: `text-base font-medium text-gray-100`. Receives an `isFirst` boolean prop. | `frontend/src/features/market-health/UserMessage.tsx` |
| `TrendChart` | Multi-line chart: Designer, Product Manager, Engineer — monthly openings over a selected time range. Owns the time range tab selector (`This Year · Past 5 Years · All Time`). Fetches trend data via TanStack Query on mount and on range change. Fires `onRangeChange(range)` callback so the parent can trigger summary regeneration. | `frontend/src/features/market-health/TrendChart.tsx` |
| `WrittenSummary` | The 3–4 sentence AI-generated summary below the chart. Receives streamed text. Shows bouncing-dots while streaming; fades in text as it arrives. | `frontend/src/features/market-health/WrittenSummary.tsx` |
| `PromptBadge` | Small "view prompt" affordance anchored to every AI message. On click, opens `PromptViewer`. Receives the prompt string as a prop. | `frontend/src/features/market-health/PromptBadge.tsx` |
| `PromptViewer` | Read-only overlay showing the prompt behind an AI message. Dismissible with Escape or outside click. | `frontend/src/features/market-health/PromptViewer.tsx` |
| `ChatInput` | Fixed, full-width input bar pinned to the bottom of the viewport. Placeholder: "Ask about the market…". Disabled while AI is streaming. | `frontend/src/features/market-health/ChatInput.tsx` |
| `DataFreshnessLabel` | Reusable label showing age and source of a data-backed claim. Used inside `TrendChart`. | `frontend/src/components/DataFreshnessLabel.tsx` |

---

## State Management

**Opening briefing** is separate from the follow-up conversation. `MarketHealthPage` fetches chart data and streams the written summary independently on mount. This is not part of `useChat`. The `AIMessage` and its children (`TrendChart`, `WrittenSummary`) are rendered directly by the page, not from a message list.

**Follow-up conversation** is managed by the `useChat` hook (Vercel AI SDK). It starts with an empty message list. The first user message submitted via `ChatInput` is the first entry — this is the message rendered with `isFirst: true` in `UserMessage`.

**Time range state** lives in `TrendChart` as local state (`'this-year' | 'past-5-years' | 'all-time'`). On range change, `TrendChart` refetches chart data and fires `onRangeChange(range)` to `MarketHealthPage`, which sends a summary regeneration request to `/api/chat` and streams the new text into `WrittenSummary`.

**Prompt viewer state** is local to `PromptBadge` — a boolean open/closed flag.

No Zustand store required for v1.

---

## Data Requirements

| Data | Source | When fetched |
|---|---|---|
| Trend chart data (monthly openings by role category) | `GET /api/market-health/trends?range={range}` | On page mount; refetch on time range change |
| Opening written summary | `POST /api/chat` (streaming) — opening prompt sent on mount | On page mount |
| Summary for new time range | `POST /api/chat` (streaming) — range-specific prompt | On time range change |
| Follow-up AI responses | `POST /api/chat` (streaming) via `useChat` | On each user message |

---

## API Contract

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/market-health/trends` | Time-series data for the trend chart. Param: `range` (`this-year` \| `past-5-years` \| `all-time`). Returns monthly openings per role category. |
| POST | `/api/chat` | Accepts `{ messages: [...] }`. Streams Claude responses. Used for the opening summary, range-change summary regeneration, and user follow-up questions. |

---

## Tech Decisions

- **Vercel AI SDK `useChat`** for follow-up conversation only. The opening briefing and summary regeneration use direct streaming fetches, not `useChat`.
- **TanStack Query** for trend chart data. Query key: `['market-health', 'trends', range]`.
- **CSS layout** for the three-zone structure: `TopBar` and `ChatInput` use `position: fixed`; `ConversationThread` uses `padding-top` and `padding-bottom` to clear both fixed zones.
- **Tailwind CSS** only — no additional component libraries.
- While the written summary regenerates on range change, keep the previous text visible with a bouncing-dots overlay. Do not blank `WrittenSummary`.
- `UserMessage` receives an `isFirst` boolean: first message renders at `text-2xl font-semibold`; subsequent messages at `text-base font-medium`.

---

## Out of scope

- Filter controls (role family, seniority, location)
- Market Health Signal and Search Implication components
- Exception / alert banner
- Authentication and user session management
- Side-by-side market comparison
