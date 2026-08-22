---
id: market-health
experience: market-health
directive: low
status: implemented
created: 2026-06-13
updated: 2026-08-22
---

# Market Health — Frontend Architecture Spec

## Experience this implements
See: `design/market-health/experience.md`

## Taxonomy this uses
See: `design/market-health/job-classification.md` — canonical `Role Category` names
(`Designer`, `Product Manager`, `Engineer`).

> **Note on this spec vs. the real implementation**: this document (and this feature's
> shipped code) has drifted further from the layout below than this update alone fixes —
> the real `MarketHealthPage.tsx` has a three-column layout (`TaskPanel`, `OutputPanel`,
> `ReasoningTrace`) that this spec doesn't describe, built in later change requests
> (ai-reasoning-transparency, provenance panel) without this file being updated. Reconciling
> that is out of scope here — this update only corrects the pieces this change touches: the
> taxonomy reference above and the `/openings` API contract below, which now matches the real
> endpoint (`market_openings.py`) exactly. A full spec-vs-code reconciliation pass is a
> candidate for its own future change request.

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
| `JobOpeningsChart` *(real name — this spec previously called it `TrendChart`)* | Multi-line chart driven by `OpeningDataPoint[]` (`{ month, designer, product_manager, engineer }`, one row per month — the real `/openings` response shape). Each of the three fixed series keys maps to its accent colour from `design/visual-design.md` (indigo / purple / emerald), matching `job-classification.md` Role Category names. Owns the time range tab selector (`This Year · Past 5 Years · All Time`). Fetches trend data via TanStack Query on mount and on range change. | `frontend/src/features/market-health/JobOpeningsChart.tsx` |
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
| Trend chart data + written summary (monthly openings per Role Category, from live-classified postings) | `GET /api/market-health/openings?range={range}` — returns `{ range, data: [{ month, designer, product_manager, engineer }], summary, as_of, source }` | On page mount; refetch on time range change |
| Opening written summary | `POST /api/chat` (streaming) — opening prompt sent on mount | On page mount |
| Summary for new time range | `POST /api/chat` (streaming) — range-specific prompt | On time range change |
| Follow-up AI responses | `POST /api/chat` (streaming) via `useChat` | On each user message |

---

## API Contract

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/market-health/openings` | Time-series data for the trend chart plus a written summary. Param: `range` (`this_year` \| `past_5_years` \| `all_time`). Returns one row per month (`{ month, designer, product_manager, engineer }`) — sourced from live-ingested, LLM-classified postings, not mock data. See `backend/specs/market-health/api.md`. |
| POST | `/api/chat` | Accepts `{ messages: [...] }`. Streams Claude responses. Used for the opening summary, range-change summary regeneration, and user follow-up questions. |

**Reviewed 2026-07-22** (change: chat data sourcing/attribution fix + scheduled classification
agent, `backend/specs/market-health/api.md`): confirmed no frontend changes needed. The
backend's new `query_market_data` tool and Google Search grounding both happen server-side —
the request/response shape and SSE event sequence above are unchanged. New source types
populate the existing reasoning-trace `SourceAccess` fields (`name`, `purpose`), which the
`ai-reasoning-panel` frontend spec already renders generically. Citations appear as plain
markdown text/links within the streamed answer, already covered by `AIMessage`'s existing
markdown rendering.

**Reviewed 2026-08-03** (change: multi-source job data ingestion — Adzuna retired, replaced by
Greenhouse/Lever/Ashby, `changes/2026-07-28-multi-source-job-data-ingestion.md`): confirmed no
frontend changes needed. `/api/market-health/openings`'s response shape is unchanged (`{ month,
designer, product_manager, engineer }` per row); only the *content* of its `source` string
changes (now names three platforms instead of one), which `DataFreshnessLabel` and the
provenance panel already render as an opaque string — no shape assumption to update. `/api/chat`
and its SSE contract are unaffected; `query_market_data` isn't changed by this backend update.
Same pattern as the 2026-07-22 review above: a backend sourcing change that's fully absorbed
server-side.

**Reviewed 2026-08-04** (change: Compensation Signal + enriched Demand Signal,
`changes/2026-08-04-compensation-signal-gap.md`): confirmed no frontend changes needed —
verified against the actual `ReasoningPanel.tsx` code, not just the spec. Both new
capabilities are conversation-only per the updated `design/market-health/experience.md`
(reached exclusively through follow-up chat, never a new chart element or filter control on
the opening view — this file's existing "Out of scope" entry, "Filter controls (role family,
seniority, location)," still holds unchanged). The backend's new `query_compensation_data`
tool (`backend/specs/market-health/api.md`) runs server-side alongside the existing
`query_market_data` tool, in the same `/api/chat` request/response contract — no SSE event
shape change, no new endpoint. `ReasoningPanel.tsx` already renders `sources_and_tools` and
`reasoning_steps` generically (`s.name`, `s.purpose`, `s.content` — no tool name hardcoded
anywhere in the component), so a `query_compensation_data` entry in the trace renders
correctly with zero code change. Compensation answers (including the confidence-caveat
language from the experience spec's User Flow 7a) are plain prose text streamed through
`AIMessage`'s existing follow-up markdown rendering — same as any other follow-up answer,
no new component. Same pattern as the two reviews above: a backend-and-design change fully
absorbed by existing generic frontend infrastructure.

**Reviewed 2026-08-09** (change: Requirements Signal + industry tagging + synthesis
questions, `changes/2026-08-09-skills-and-industry-signal.md`): confirmed no frontend
changes needed — but this one required tracing the *specific* rendering concern (a
two-part, "data then judgment, never blended" answer) against the real component, not just
the general pattern of the three reviews above. Two real findings from that trace:

1. **This file's component names are stale** (as the disclaimer at the top of this
   document already warns) — there is no `AIMessage.tsx`. The opening turn is
   `MarketBriefingMessage.tsx`; follow-up turns are rendered inline in
   `ConversationThread.tsx`, both wrapped by `AITurn.tsx`. Noted here rather than silently
   worked around, consistent with this file's standing disclaimer that a full
   spec-vs-code reconciliation is a separate future pass, not something to do piecemeal.
2. **Follow-up answers are not markdown-rendered at all** — `ConversationThread.tsx`
   renders `assistant.content` as plain text in a single `<p className="...
   whitespace-pre-wrap">`, no markdown library, no rich formatting. This actually answers
   the open question cleanly: a two-part synthesis answer's separation is achieved by the
   model writing two paragraphs (a blank line between them), which `whitespace-pre-wrap`
   already renders as a visible paragraph break — the same mechanism that already displays
   every other multi-sentence answer today. The "never blended" requirement
   (`design/market-health/experience.md` User Flow 7b) is a **content/wording discipline**
   enforced by the synthesis-stage system prompt (`backend/specs/market-health/api.md`),
   not a rendering capability this frontend lacks. `query_requirements_data` (the third
   query tool) needs no frontend change for the same reason as the other two — it's
   consumed server-side only.

Same underlying pattern as the three reviews above, arrived at with more scrutiny given the
genuinely new *kind* of answer involved.

**Reviewed 2026-08-11** (change: Classification + Requirements Taxonomy Redesign,
`changes/2026-08-11-classification-taxonomy-redesign.md`) — **not a clean no-op**, unlike the
four reviews above. Grepped the real component tree for the old field names
(`sub_specialization`, `seniority`) and old ladder values rather than assuming the pattern
held a fifth time. Two real findings:

1. **Three components are confirmed dead code, unreachable from the live app**:
   `FilterControls.tsx` (hardcodes a `seniority: "all" | "Mid" | "Senior"` filter type — a
   value set that doesn't even match any version of the real taxonomy, old or new),
   `ProvenancePanel.tsx`, and `ConversationalArea.tsx`. Verified by grepping for importers of
   each — none exist outside the files themselves. This matches this spec's own "Out of
   scope" section, which already lists "Filter controls (role family, seniority, location)"
   as not part of the shipped experience — these are leftover files from an earlier direction,
   never deleted, not something this taxonomy change needs to touch (fixing unreachable dead
   code is its own separate cleanup, not part of this change's scope).
2. **One live line does carry the old field name**: `MarketHealthPage.tsx:111` sends
   `body: { context: { role: "all", seniority: "all", location: "all" } }` on every
   `useChat` call. This is real, reachable code — but the value is always the literal string
   `"all"`, never an actual taxonomy value, and `ChatContext.seniority` doesn't appear to be
   read by any real query logic in `chat.py` (the real filtering happens through the model's
   own tool-calling, not this static context object). So there's no data-correctness bug —
   nothing this revision changes was ever actually driven by this field's value — but the
   field name is stale and worth a one-line rename to `level` for consistency, now that
   `seniority` no longer exists as a concept anywhere else in the taxonomy. Scoped as a
   trivial `/implement-frontend` fix (Step 6) rather than left as spec-only debt, since it
   costs nothing and prevents a future reader from assuming this field is wired to something
   real when it isn't.

**Reviewed 2026-08-16** (change: production-ready CORS configuration,
`changes/2026-08-16-production-cors-config.md`) — confirmed no-change, and confirmed by
actually reading this section rather than assuming a sixth consecutive no-op. The backend
change adds a `CORS_ALLOWED_ORIGINS` env var so `api` accepts requests from the real deployed
`web` origin once known — purely server-side middleware config. No endpoint path, request/
response shape, or SSE event sequence in the table above changes; this frontend's calls are
already relative paths (`/api/market-health/openings`, `/api/chat`), routed through Vite's
dev-only proxy locally and (per this file's Out of scope and the still-open `web` hosting
decision) presumably a host-level rewrite in production — neither depends on knowing the
backend's allowed-origins list, which is enforced entirely server-side. No API Contract
assumption here relied on, or conflicted with, the old hardcoded-localhost-only behavior.

---

## Tech Decisions

- **Vercel AI SDK `useChat`** for follow-up conversation only. The opening briefing and summary regeneration use direct streaming fetches, not `useChat`.
- **TanStack Query** for trend chart data. Query key: `['market-health', 'trends', range]`.
- **CSS layout** for the three-zone structure (corrected 2026-08-17 —
  `changes/2026-08-17-chat-scroll-white-gap.md` — this bullet previously described
  `position: fixed` for `TopBar`/`ChatInput` with padding-based clearing, which was
  never actually what got built; same "spec describes a stale implementation detail"
  pattern already flagged for component names in the 2026-08-09 review below):
  `MarketHealthPage.tsx` uses a flexbox column (`h-screen` root → `flex flex-1
  overflow-hidden` row → `flex flex-col flex-1 overflow-hidden` centre column),
  with `TopBar` and `ChatInput` as fixed-height flex children (`shrink-0`) and
  `ConversationThread` as the single scrolling middle (`flex-1 overflow-y-auto`).
  **`min-h-0` must be set on every flex container between the `h-screen` root and
  the scrollable `ConversationThread`** (the centre column and the row) — flex
  items default to `min-height: auto`, which lets a child with `overflow-y-auto`
  grow to fit its content instead of scrolling internally, exactly the bug this
  change fixed. `<body>`/`html` also carry an explicit dark background
  (`design/visual-design.md`'s `gray-900` page-background token) as defense in
  depth — if containment ever breaks again, the app's own background shows through
  rather than the browser's default white.
- **`html`/`body` always carry `overflow: hidden` (added 2026-08-22 —
  `changes/2026-08-17-chat-scroll-white-gap.md` — the `min-h-0` fix above was real
  but not sufficient alone: the document itself must never be scrollable at all,
  independent of the flex containment fix).** `ConversationThread.tsx`'s
  `scrollIntoView` call (see below) walks up through every scrollable ancestor,
  and if the document is even marginally scrollable it will scroll the *whole
  page* — not just the intended container — to satisfy alignment. `overflow:
  hidden` on `html`/`body` removes the document as a candidate ancestor entirely,
  so all scroll adjustment is forced into `ConversationThread`'s own
  `overflow-y-auto`.
- **`ConversationThread`'s auto-scroll uses `scrollIntoView({ behavior: "smooth",
  block: "nearest" })`, not the default `block: "start"`** (added 2026-08-22, same
  change as above). `block: "start"` asks every scrollable ancestor to align the
  target with the *top* of its own viewport — including the document, before the
  `overflow: hidden` fix above, which is what was scrolling the whole page and
  leaving the loading indicator stranded near the top of the browser viewport
  with empty space below it. `block: "nearest"` only scrolls the minimum needed
  to bring the target into view, never forces a start-alignment.
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
