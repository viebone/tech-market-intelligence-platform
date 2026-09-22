---
id: market-health
experience: market-health
directive: low
status: implemented
created: 2026-06-13
updated: 2026-09-11
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
>
> **Status `implemented` (restored 2026-09-11, Step 8, then partially reverted hours later
> same day — `changes/2026-09-11-employment-events-no-company-matching.md`).** The Step 8
> additions (`EmploymentEventsStrip`, `EventMarkerDetail`, `JobOpeningsChart`'s `events` prop,
> the `employment-events` TanStack Query) were built, verified, then **removed** once the user
> directed that employment events must never be matched to tracked companies at any layer,
> including a chart overlay. `JobOpeningsChart` and `MarketBriefingMessage` are back to their
> pre-2026-09-11 shape. Employment events now surface only through `EmploymentRiskStoryMessage`
> (Story 2, below) and follow-up Layoff Signal conversation, both already independent of
> tracked companies. The Layoff Signal conversational path itself needed no change either
> time — confirmed against the real `ConversationThread.tsx` (`whitespace-pre-wrap` plain
> text) and `ReasoningPanel.tsx` (already generic).
>
> **Reorganized 2026-09-16** (`changes/2026-09-16-frontend-organization.md`, for
> `outcomes/codebase-stays-navigable-as-it-grows.md`) — this folder had grown to 30 flat files
> mixing page chrome, the data-story catalogue, and one chart feature together, plus 11 files
> that were dead code (confirmed by tracing every import across the real app, not guessed).
> Split into three subfolders — `layout/` (page chrome, present on every task), `stories/` (the
> data-story catalogue), `hiring-status/` (the one pinned-feature chart task) — every Location
> path below updated to match. Two of the dead files this pass found and removed —
> `PromptBadge.tsx` and `PromptViewer.tsx` — were still documented below as real components; see
> their entry, further down, for the correction. Verified with `tsc --noEmit` and `npm run build`
> before and after — 474 modules transformed either way, confirming nothing was lost or
> duplicated in the move.

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
| `TopBar` | Fixed header. Product title only. No navigation in v1. | `frontend/src/features/market-health/layout/TopBar.tsx` |
| `TaskPanel` *(catalogue-driven, added 2026-09-04)* | Left-column navigation. Renders one pinned welcome item ("About this platform"), then one item per entry in `GET /api/market-health/stories` (label = that entry's `display_name`, in catalogue order), then pinned feature tasks (currently just "Tech market hiring status"). A new backend story needs no change here — the list is fetched, not hardcoded. | `frontend/src/features/market-health/layout/TaskPanel.tsx` |
| `WelcomeMessage` *(added 2026-09-04, restructured 2026-09-04 as a landing-page-style hero — `changes/2026-09-04-welcome-visual-data-points.md`)* | Renders "About this platform" as Hero (eyebrow + headline + subhead) / Proof (Hero Figure + Stat Tiles + Category Share Bar, from `GET /api/market-health/welcome`) / Call to action (one Shortcut Card per entry in `welcome.story_shortcuts`). Selecting a shortcut calls the same task-select handler `TaskPanel` uses, with that entry's `id` — it does not send a chat message. The only entry-point-styled message in the product; see `design/visual-design.md` — Entry-point components. | `frontend/src/features/market-health/stories/WelcomeMessage.tsx` |
| `DataStoryMessage` | Renders a resolved story-catalogue answer (`POST /api/market-health/stories/{id}`'s response) inside an AI-turn. Composes a framing line + `StoryBlock`s from the shared story component set (see Data stories → "Every story: the shared build"). Unrelated to `WelcomeMessage` — a story's own task renders this when selected; the welcome only links to it. | `frontend/src/features/market-health/stories/DataStoryMessage.tsx` |
| `StoryBlock` *(added 2026-09-10, `subtitle` added 2026-09-11)* | The fixed data-story block anatomy — heading → optional subtitle (what's measured + its unit, `data-legibility`) → one visual → honesty qualifier + divider — and the per-block "not enough data yet" fallback. Used only inside `DataStoryMessage`. | `frontend/src/features/market-health/stories/StoryBlock.tsx` |
| `RankedBarList` / `StoryFigure` / `Meter` / `YearOnYearGroupedBars` *(added 2026-09-06 / 2026-09-10; `YearOnYearGroupedBars` replaces `YearOnYearBars` 2026-09-22)* | The data-story visual vocabulary components (`design/visual-design.md` — Data Story composition). Generic, reusable by any story. `YearOnYearGroupedBars` owns the "no prior window yet" render (falls back to `RankedBarList`) and, once a comparison is available, a real Nivo grouped bar chart with a legend — see "Charting library," below. | `frontend/src/features/market-health/stories/{RankedBarList,StoryFigure,Meter,YearOnYearGroupedBars}.tsx` |
| `SkillDemandChart` *(added 2026-09-22)* | A real Nivo grouped bar chart (must-have vs. nice-to-have, per skill group), with an explicit legend — replaces a single `RankedBarList` that only distinguished the two by bar opacity. Generic — takes `{skill_group, must_have, nice_to_have}[]`. | `frontend/src/features/market-health/stories/SkillDemandChart.tsx` |
| `SharePieChart` *(added 2026-09-22 — `changes/2026-09-22-nivo-pie-charts.md`)* | A real Nivo 2-slice donut for a genuine 2-category partition (not a coverage percentage — see "Charting library," below, for the dividing line against `Meter`). Generic — takes `{id, label, value, color}[]`. Used by Story 1's pay-transparency block, Story 2's contraction-vs-expansion block, and Story 4's scale block. | `frontend/src/features/market-health/stories/SharePieChart.tsx` |
| `WorldRiskMap` *(added 2026-09-13)* | A country-level choropleth — `react-simple-maps` over a bundled `world-atlas` `countries-50m` topology (the 50m resolution, not 110m — verified the 110m file drops Singapore/Malta, real countries in this product's data). Fill = net direction (emerald-600/red-600, existing semantic tokens, opacity by magnitude); gray-800 for no reported events. Owns its own legend line and hover tooltip (both totals, never just net). Generic — takes a `{country, contraction_affected, expansion_affected, contraction_events, expansion_events}[]` prop, not employment-risk-specific by name, reusable by a future story. | `frontend/src/features/market-health/stories/WorldRiskMap.tsx` |
| `ConversationThread` | Scrollable message list between TopBar and ChatInput. Renders the opening `AIMessage`, then user and AI follow-up messages in order. Auto-scrolls to bottom on new messages. | `frontend/src/features/market-health/layout/ConversationThread.tsx` |
| `AIMessage` | Wraps an AI turn. Left-aligned. `bg-gray-800 rounded-xl py-5 px-6`. Carries a `PromptBadge`. For the opening message, renders `TrendChart` then `WrittenSummary`. For follow-up responses, renders streamed markdown text. | `frontend/src/features/market-health/AIMessage.tsx` |
| `UserMessage` | Wraps a user turn. Left-aligned, no background, no border. First message in the thread: `text-2xl font-semibold text-gray-100`. Subsequent messages: `text-base font-medium text-gray-100`. Receives an `isFirst` boolean prop. | `frontend/src/features/market-health/UserMessage.tsx` |
| `JobOpeningsChart` *(real name — this spec previously called it `TrendChart`)* | Multi-line chart driven by `OpeningDataPoint[]` (`{ period, designer, product_manager, engineer }`). Owns two directly visible dropdown filters: granularity (`Week · Month`) and time range (`6 Months · This Year · Past 5 Years · All Time`). Week is the default granularity and 6 Months is the default range. Fetches trend data via TanStack Query when either control changes. **No employment-event layer** — `EmploymentEventsStrip`/`EventMarkerDetail` were added 2026-09-11 and removed the same day (`changes/2026-09-11-employment-events-no-company-matching.md`); this chart is unchanged from its pre-2026-09-11 shape. | `frontend/src/features/market-health/hiring-status/JobOpeningsChart.tsx` |
| `WrittenSummary` | The 3–4 sentence AI-generated summary below the chart. Receives streamed text. Shows bouncing-dots while streaming; fades in text as it arrives. | `frontend/src/features/market-health/WrittenSummary.tsx` |
| ~~`PromptBadge`~~ / ~~`PromptViewer`~~ | **Removed 2026-09-16** — confirmed dead (imported by nothing reachable from the real app) during `changes/2026-09-16-frontend-organization.md`'s dead-code trace, and deleted. This spec had documented them as real, live components; the real implementation's "view prompt" affordance, if it exists at all today, isn't these two files — worth confirming against the live UI next time this section is touched, rather than assumed from this row. | — |
| `ChatInput` | Fixed, full-width input bar pinned to the bottom of the viewport. Placeholder: "Ask about the market…". Disabled while AI is streaming. | `frontend/src/features/market-health/layout/ChatInput.tsx` |
| `DataFreshnessLabel` | Reusable label showing age and source of a data-backed claim. Used inside `TrendChart`. | `frontend/src/components/DataFreshnessLabel.tsx` |

---

## State Management

**Opening briefing** is separate from the follow-up conversation. `MarketHealthPage` fetches chart data and streams the written summary independently on mount. This is not part of `useChat`. The `AIMessage` and its children (`TrendChart`, `WrittenSummary`) are rendered directly by the page, not from a message list.

**Follow-up conversation** is managed by the `useChat` hook (Vercel AI SDK). It starts with an empty message list. The first user message submitted via `ChatInput` is the first entry — this is the message rendered with `isFirst: true` in `UserMessage`.

**Time range state** lives in `TrendChart` as local state (`'this-year' | 'past-5-years' | 'all-time'`). On range change, `TrendChart` refetches chart data and fires `onRangeChange(range)` to `MarketHealthPage`, which sends a summary regeneration request to `/api/chat` and streams the new text into `WrittenSummary`.

**Prompt viewer state** is local to `PromptBadge` — a boolean open/closed flag.

**Employment events state — removed 2026-09-11.** A chart-scoped employment-events query
briefly existed here (added and removed the same day —
`changes/2026-09-11-employment-events-no-company-matching.md`). `JobOpeningsChart` has no
employment-event state of any kind. Employment-events state now lives only where Story 2 needs
it — see "Story 2: employment risk across the market," below.

**Task selection** (added 2026-09-04 — `changes/2026-09-04-about-this-platform-welcome.md`)
lives in `MarketHealthPage` as `activeTaskId: string`, defaulting to `"about-this-platform"`.
Selecting any Task Panel item, or any shortcut inside `WelcomeMessage`, calls the same
`setActiveTaskId(id)` — a shortcut click is not a different code path from a Task Panel click,
it is the same handler with that entry's `id`.

**Story catalogue** (added 2026-09-04) is fetched once via TanStack Query
(`['market-health', 'stories']`, `GET /api/market-health/stories`) and consumed by both
`TaskPanel` (to render one item per entry, using `display_name`) and by routing logic that
decides what the working space renders for the active task — it is not re-fetched per
component. `WelcomeMessage` does not read this query directly; it gets its shortcut list from
`GET /api/market-health/welcome`'s own `story_shortcuts` field (same underlying catalogue,
fetched together with the welcome's inventory in one request).

No Zustand store required for v1.

---

## Chart rendering rules

Added 2026-09-04 — `changes/2026-09-04-chart-baseline-and-render-fixes.md`. The trend chart is
`frontend/src/features/market-health/hiring-status/JobOpeningsChart.tsx` (the spec's older `TrendChart` name).
It is a hand-rolled SVG line chart. These rules exist because the first implementation broke on
the shapes real sparse data actually takes:

- **Period parsing must handle both granularities.** `data[].period` is `YYYY-MM-DD` for
  `week` and `YYYY-MM` for `month`. Normalise a month period to `YYYY-MM-01` before
  constructing a `Date` — `new Date("2026-08T00:00:00")` is `Invalid Date` and leaks
  "Invalid Date" into axis labels and the tooltip.
- **Zero-width value range.** When every visible value is equal (a genuinely flat series, or a
  single bucket), the y-domain has zero height. Give it a synthetic pad so the line renders as
  a straight horizontal line and the y-axis still shows a readable tick — never divide by a
  zero span (produces `NaN` path coordinates and a blank chart).
- **Single bucket.** One data point renders as labelled dots (no line — a lone `M x,y` draws
  nothing) plus a caption in the plot area naming the period and saying a trend line needs at
  least two. This is the normal monthly view until a second month closes.
- **X-axis label density.** Never render more tick labels than fit without overlap. For short
  ranges at `week` granularity (up to ~26 buckets), thin labels to an evenly spaced subset.
  The line itself always uses every bucket.
- **Long ranges.** `past_5_years` / `all_time` show at least one tick per year at both
  granularities — do not rely on a period string ending in `-01`, which almost never happens
  for Monday-anchored week keys.
- **Baseline and in-progress period.** The backend already excludes the baseline day and the
  current in-progress week/month; the chart draws exactly what it receives, never back-fills or
  pads the empty pre-collection span of a wide range, and never re-adds a "today so far" point.

### Employment events strip rendering — removed 2026-09-11

Built and removed the same day — `changes/2026-09-11-employment-event-ingestion.md`, then
`changes/2026-09-11-employment-events-no-company-matching.md`. `JobOpeningsChart` has no
employment-event rendering logic; this section intentionally left empty as a marker of the
removal.

---

## Welcome rendering rules

Added 2026-09-04 — `changes/2026-09-04-about-this-platform-welcome.md`; restructured
2026-09-04 into a landing-page hero — `changes/2026-09-04-welcome-visual-data-points.md`.
`WelcomeMessage` must keep working unchanged as the story catalogue grows or shrinks:

- **Three bands, fixed order: Hero, Proof, Call to action.** Hero is static copy. Proof
  renders `welcome.inventory`. Call to action renders `welcome.story_shortcuts`. Do not
  reorder or merge them — the hierarchy (headline → hero figure → CTA cards) is the point.
- **Category Share Bar is fully data-driven.** Render one segment per row in
  `inventory.role_breakdown`, in the order the API returns (descending by count). Map each
  `role_category` to its existing accent colour by name (`design/visual-design.md`'s Accent
  palette — Designer/indigo-500, Product Manager/purple-500, Engineer/emerald-500); never
  assign colour by position or invent a colour for an unrecognised category — fall back to a
  neutral gray-600 segment rather than guessing a hue, and still label it by name.
- **Shortcut cards are fully data-driven.** Render exactly one Shortcut Card per entry in
  `welcome.story_shortcuts`, in the order the API returns. Never hardcode a story's id,
  question, or count in this component.
- **Selecting a shortcut selects a task, it does not send a message.** Call the shared
  `setActiveTaskId(shortcut.id)` — the same function `TaskPanel` calls on click. There is no
  chat-send path from the welcome.
- **Empty catalogue.** If `story_shortcuts` is `[]`, omit the Call to action's card list
  entirely (no empty box, no "no stories available" message) and still show the generic "ask
  your own question" sentence and the out-of-scope sentence.
- **Empty or partial inventory.** `inventory.collection_started_at` may be `null` and
  `inventory.role_breakdown` may be `[]` (nothing collected yet). The Hero Figure and Stat
  Tiles render the "not collected yet" phrasing from the experience spec's edge case rather
  than showing `0`; the Category Share Bar section is omitted rather than rendered empty.
- **No client-side computation.** Every figure in Proof is read directly from
  `GET /api/market-health/welcome`'s response — this component never derives a count,
  percentage, or share itself. A segment's share (for its label) is the one exception: it may
  be computed client-side from the returned counts (`count / total_postings`), since that's
  formatting a number the response already carries, not deriving a new fact.

---

## Data Requirements

| Data | Source | When fetched |
|---|---|---|
| Platform welcome (added 2026-09-04) | `GET /api/market-health/welcome` — returns `{ inventory, story_shortcuts, provenance, as_of }` | On page mount (default task); also whenever "About this platform" is selected, so figures stay current |
| Story catalogue (added 2026-09-04) | `GET /api/market-health/stories` — returns `{ stories: [{ id, display_name, question, example_phrasings }] }` | Once, on page mount — drives `TaskPanel`'s catalogue section |
| Chat suggestions (added 2026-09-06) | `GET /api/market-health/chat-suggestions` — returns `{ suggestions: [{ id, question }] }` | Once, on page mount — drives `SuggestedQuestions` chips |
| Trend chart data + written summary (weekly or monthly openings per Role Category, from post-baseline live-classified postings) | `GET /api/market-health/openings?range={range}&granularity={granularity}` — returns `{ range, granularity, data: [{ period, designer, product_manager, engineer }], summary, as_of, source }`; `summary` names the selected range and granularity | On page mount; refetch when range or granularity changes |
| Opening written summary | `POST /api/chat` (streaming) — opening prompt sent on mount | On page mount |
| Summary for new time range | `POST /api/chat` (streaming) — range-specific prompt | On time range change |
| Follow-up AI responses | `POST /api/chat` (streaming) via `useChat` | On each user message |

---

## API Contract

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/market-health/openings` | Time-series data for the trend chart plus a written summary. Params: `range` (`six_months` \| `this_year` \| `past_5_years` \| `all_time`) and `granularity` (`week` \| `month`). Returns one row per bucket (`{ period, designer, product_manager, engineer }`) — sourced from live-ingested, LLM-classified postings, not mock data. See `backend/specs/market-health/api.md`. |
| GET | `/api/market-health/welcome` *(added 2026-09-04)* | Platform inventory + one shortcut per current story-catalogue entry, for `WelcomeMessage`. No auth, no LLM. See `backend/specs/market-health/api.md` — Welcome. |
| GET | `/api/market-health/stories` *(added 2026-09-04 to this spec — endpoint pre-existing)* | The story catalogue's presentation metadata (`{ id, display_name, question, example_phrasings }[]`), for `TaskPanel`. No answer content. |
| POST | `/api/market-health/stories/{story_id}` *(added 2026-09-04 to this spec — endpoint pre-existing)* | Resolves one story's answer for `DataStoryMessage`, when that story's task is selected. No LLM. |
| GET | `/api/market-health/chat-suggestions` *(added 2026-09-06)* | The curated instant-answer catalogue's questions (`{ id, question }[]`), for `SuggestedQuestions` chips. No answers, no LLM. |
| POST | `/api/chat` | Accepts `{ messages: [...] }`. Streams the response. A message matching the curated catalogue is answered instantly with no model call; otherwise it goes to the paid Gemini tier (10–30s). Also used for the opening summary and range-change summary regeneration. |

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

**Reviewed 2026-09-06** (change: fluent DB-only chat + provider-neutral streaming,
`changes/2026-09-06-chat-answer-truncation-and-curated-match.md`) — confirmed **no frontend
change needed**, checked against the real component tree, not assumed:

1. **Web-search removal is server-side.** Chat becoming DB-only removes the Stage 2 grounding
   call inside `chat.py`. The SSE contract (`reasoning_trace` → text → `finish_message`) and
   the `/api/chat` request shape are unchanged. `sources_and_tools` simply never carries an
   external entry now — the reasoning panel already renders that list generically
   (`ai-reasoning-panel` frontend spec, `source_type: 'data_source' | 'tool'`), and "no
   external tools" is an existing rendered state, not a new one.
2. **The "cut off — ask me to continue" marker is plain appended text.** When Stage 3's
   answer is `truncated`, the backend appends a short sentence to the streamed text (or
   streams a continuation). Follow-up answers render as `whitespace-pre-wrap` plain text
   (see the 2026-08-09 review, finding 2) — an appended sentence needs no new component and
   no markdown capability.
3. **The reasoning panel's truncated-answer step** rides the same generic `reasoning_steps`
   rendering — one more plain-language step, no shape change.
4. **`SuggestedQuestions` unchanged.** Widening the curated matcher is entirely inside
   `curated_answers.py`; the chip list (`GET /api/market-health/chat-suggestions`) and the
   chip-click = `append` path are untouched.

Same pattern as the 2026-07-22 / 08-03 / 08-04 reviews — a backend behaviour change fully
absorbed by existing generic frontend infrastructure.

**Reviewed 2026-09-11** (change: Layoff Signal + employment events,
`changes/2026-09-11-employment-event-ingestion.md`) — **not a clean no-op**, unlike most of
the reviews above; real new components were required (Component Breakdown, above: the chart
strip, State Management: its state). Traced the two parts against the real component tree
before assuming either the "conversation absorbs it" or "new component" pattern:

1. **Layoff Signal conversational answers need no new rendering component** — same finding
   as the 2026-08-09 (Requirements Signal) review: `query_employment_events_data` is a fourth
   server-side chat tool (`backend/specs/market-health/api.md`), consumed entirely inside
   `/api/chat`'s existing SSE contract. The two-part "data, then judgment" answer
   (`design/market-health/experience.md` User Flow 7d) is achieved the same way Requirements
   Signal's synthesis answer already is — two paragraphs, a blank line between them, rendered
   by `ConversationThread.tsx`'s existing `whitespace-pre-wrap` text path. No markdown, no new
   component, no change to `ConversationThread.tsx` itself.
2. **`ReasoningPanel.tsx` needs no change** — it already renders `sources_and_tools` and
   `reasoning_steps` generically (2026-08-04 review's finding: no tool name hardcoded
   anywhere in the component), so a `query_employment_events_data` trace entry, and the
   registries named in its `sources_checked` (Eurofound ERM / US WARN / UK Companies House),
   render correctly with zero code change — same mechanism that already lets it name
   Greenhouse/Lever/Ashby individually.
3. **The chart strip and event-detail expansion were genuinely new** — built, then **removed
   the same day** (`changes/2026-09-11-employment-events-no-company-matching.md`) once the
   user directed that employment events must never be matched to tracked companies at any
   layer, including a chart overlay. Finding 1 and 2 above still hold: the conversational path
   remains exactly as described, no change needed there either time.

---

## Tech Decisions

- **Vercel AI SDK `useChat`** for follow-up conversation only. The opening briefing and summary regeneration use direct streaming fetches, not `useChat`.
- **TanStack Query** for trend chart data. Query key: `['market-health', 'trends', range]`.
  (A chart-scoped employment-events query briefly existed alongside this, added and removed
  2026-09-11 — `changes/2026-09-11-employment-events-no-company-matching.md`. See "Story 2:
  employment risk across the market," below, for where that query now lives.)
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
- Authentication and user session management — **still true for this feature specifically**
  (Market Health itself stays fully anonymous-accessible); a real session now exists in this
  codebase as of `frontend/specs/mcp-access/architecture.md`, scoped to the `account` and
  `mcp-access` features only. This line isn't stale, it's a deliberate boundary — see that
  spec's Architecture Overview for what did and didn't change here.
- Side-by-side market comparison

## Data stories

See `design/market-health/data-stories.md` for the product-facing catalogue, the per-story
**"Visual standard every story must meet"** checklist, and the first story contract; and
`design/visual-design.md` — **Data Story composition** for the aesthetic. The frontend treats
a story as a normal assistant turn with additional structured content, not as a separate page.

### Every story: the shared build (added 2026-09-10 — `changes/2026-09-10-story-visual-standard.md`)

A story's renderer is bespoke per catalogue entry ("add one entry, its deterministic
renderer"), but it **composes from a shared component set** so every story looks and reads
like the last one. No new backend field: the renderer maps its own known section ids to
visual forms; a generic `render_hint` in the API would only pay off if stories shared one
fully generic component, which the catalogue model deliberately avoids.

| Component | Responsibility | Location |
|---|---|---|
| `DataStoryMessage` | The per-story renderer. Composes the framing line + `StoryBlock`s from the story's resolved `sections`. One per catalogue entry, or a `switch` on `story_id` inside one file while the catalogue is small. | `frontend/src/features/market-health/stories/DataStoryMessage.tsx` |
| `StoryBlock` | The fixed block anatomy: heading (`text-sm font-semibold text-gray-200`) → one visual (child) → honesty qualifier (`text-xs text-gray-500`), with the `border-t border-gray-800 pt-4` divider. Renders the section's "not enough data yet" line instead of the child when `status === "insufficient_data"` or the child has no data. Enforces the anatomy so a story can't drift. | `frontend/src/features/market-health/stories/StoryBlock.tsx` (extract from `DataStoryMessage`'s current inline `Block`) |
| `RankedBarList` | Generic `{ label, value, emphasis? }[]` magnitude list — one muted hue, length = value, direct-labelled, capped (no scroll). | `frontend/src/features/market-health/stories/RankedBarList.tsx` (exists) |
| `StoryFigure` | The one Hero Figure a story may lead a block with — `text-3xl`/`text-4xl font-bold text-gray-100` value + `text-sm text-gray-400` caption. Never an accent colour. | `frontend/src/features/market-health/stories/StoryFigure.tsx` (new — generalise the inline figure in `DataStoryMessage`) |
| `Meter` | One share as a part-to-whole bar: the `StoryFigure` percentage + an `h-2` track (`bg-gray-800`) with an `indigo-500` fill at that width + a plain complement line below. Per `design/visual-design.md` — Meter. | `frontend/src/features/market-health/stories/Meter.tsx` (new) |
| Category Share Bar / Trend line | Reuse `WelcomeMessage`'s share bar and the opening chart's trend rendering when a story's data is part-to-whole or time-series. Not built ahead of a story that needs them. | — |

The framing line is plain `text-sm leading-relaxed text-gray-300` markup in `DataStoryMessage`
— not a component.

**Story acceptance checklist (frontend / review time).** Before a story ships, its
`DataStoryMessage` output must satisfy `design/market-health/data-stories.md` — "Visual
standard every story must meet". In frontend terms:
- framing line first, then 3–6 `StoryBlock`s, nothing else at the top level;
- every `StoryBlock` child is a `RankedBarList` / `StoryFigure` / `Meter` / share bar / trend /
  a real Nivo chart (added 2026-09-22 — `changes/2026-09-22-nivo-charting-library.md`, "Charting
  library" below) — never a bare `<p>`;
- **≥2 distinct** of those form components across the story;
- **≤1** `StoryFigure` in the whole story;
- no block renders the welcome's *current-snapshot* figures — total postings, company count,
  collection start, current role-category split (a *year-on-year shift* in the same dimension
  is allowed; it answers a different question);
- `npm run build` + `tsc` clean; eyeball against the running welcome to confirm no duplication
  and consistent rhythm.

### Year-on-year comparison component (added 2026-09-10 — `changes/2026-09-10-story-yoy-breakdowns.md`; revised 2026-09-22 — `changes/2026-09-22-nivo-charting-library.md`)

| Component | Responsibility | Location |
|---|---|---|
| `YearOnYearGroupedBars` | Renders a YoY section's `content` as a real Nivo grouped horizontal bar chart — one bar pair per row, `current_share` (indigo-500) vs. `prior_share` (muted gray-600), with an explicit legend ("Now" / "A year ago") and the `delta_pp` figure surfaced in the tooltip rather than as an inline glyph. Per `design/visual-design.md` — Charting library. When `content.comparison_available === false`: renders **only** the current window (plain `RankedBarList` of `current_share`, no chart, no delta) + a muted `text-xs text-gray-500` line derived from the section `qualifier` ("Year-on-year comparison starts {Month Year}"). Never renders a prior bar or delta from a `null`. Generic across role_category/level/track — a caller relabels `row.value` before this component sees it (see the Charting library note on `role_category`'s display relabel) rather than this component knowing about any one dimension. | `frontend/src/features/market-health/stories/YearOnYearGroupedBars.tsx` |

The two window date ranges come from `content.current_window` / `content.prior_window` and
are shown once under the block heading (`StoryBlock` already owns the heading; the dates go in
the block's own markup, `text-xs text-gray-500`). The "what this means" sentence is per-block
copy in `DataStoryMessage`, not from the API.

### Charting library (added 2026-09-22 — `changes/2026-09-22-nivo-charting-library.md`)

**Nivo** (`@nivo/bar`, `@nivo/theming`, MIT licensed) — reached for specifically where a real
multi-series comparison says more than the hand-built vocabulary above can, not a replacement
for it. A single shared theme (`nivoTheme.ts`) maps every Nivo theme slot to this product's own
dark palette — no chart ever renders with Nivo's own light-theme defaults.

**Lazy-loaded, not bundled into the initial page load.** `SkillDemandChart` and
`YearOnYearGroupedBars` are both `React.lazy` + `Suspense` (fallback: a `h-40 animate-pulse
bg-gray-800` block) in `DataStoryMessage.tsx`. Measured directly, not assumed: adding Nivo
statically grew the main bundle from 130KB to 218KB gzipped and triggered Vite's >500KB chunk
warning; lazy-loading brought the main bundle back to 131KB gzipped, with Nivo's ~86KB gzipped
weight split into its own chunk, loaded only when a story that actually renders one of these
two blocks is opened. Any future Nivo-based component must follow the same pattern — check a
real production build's chunk output (`npm run build`), don't assume tree-shaking alone handles
it.

`SkillDemandChart` and `YearOnYearGroupedBars` are documented above, in their own sections.

**Extended 2026-09-22** (`changes/2026-09-22-nivo-pie-charts.md`) — `SharePieChart` (`@nivo/pie`)
added for a genuinely different case than the grouped bar charts above: a real 2-category
partition of a whole population, not a multi-series comparison. Same lazy-loading discipline —
confirmed by a real build that the main bundle stayed at ~131.86KB gzipped (essentially
unchanged) with `SharePieChart` in its own on-demand chunk. Applied to 3 blocks that were
previously `Meter`-only: Story 1's pay transparency, Story 2's contraction-vs-expansion, Story
4's scale. **Deliberately not applied to Story 3** — its "coverage and pay data availability"
`Meter` states a completion percentage ("X of Y tracked roles have salary data reported"), not
a 2-way partition of a meaningful population; forcing a donut there would misrepresent what the
number actually means. `Meter` itself is unchanged and still real, live code (Story 3 remains
its only consumer).

### Story 2: employment risk across the market (added 2026-09-11 — `changes/2026-09-11-employment-events-independent-scope.md`)

| Component | Responsibility | Location |
|---|---|---|
| `EmploymentRiskStoryMessage` | Renders `POST /api/market-health/stories/employment-risk-overview`'s resolved sections: framing line → `WorldRiskMap` (where it's happening, leads the story — reordered 2026-09-13, `changes/2026-09-13-employment-risk-world-map.md`) → `SharePieChart` *(revised 2026-09-22, was `Meter`)* (direction split, contraction vs. expansion, with the contraction-roles figure as a plain caption) → 2× `RankedBarList` (top companies / sectors by roles affected). One movement, no year-on-year block (event data isn't a 12-month-comparable series the way posting volume is). | `frontend/src/features/market-health/stories/EmploymentRiskStoryMessage.tsx` |

`DataStoryMessage` becomes a thin router (added 2026-09-11): it branches on `story.story_id`
— `"market-data-briefing"` renders inline as before (unchanged), `"employment-risk-overview"`
delegates to `EmploymentRiskStoryMessage`. `ConversationThread.tsx` is untouched — it already
renders whatever `DataStoryMessage` returns for the active story, generically. This is the
"a switch on story_id inside one file while the catalogue is small" option this spec's own
"Every story: the shared build" section anticipated, now exercised for the first time with a
second catalogue entry.

### Story 3: independent market benchmark (added 2026-09-18 — `changes/2026-09-18-market-benchmark-story.md`)

| Component | Responsibility | Location |
|---|---|---|
| `MarketBenchmarkStoryMessage` | Renders `POST /api/market-health/stories/market-benchmark`'s resolved sections: framing line (+ visible attribution text, rendered directly — not only in the Reasoning Panel) → `RankedBarList` (demand by role) → Hero Figure + Meter (total tracked vacancies + salary-data coverage) → `RankedBarList` (pay by role, currency-formatted) → `RankedBarList` (top skills, summed across roles). One movement, no year-on-year block (each tracked role has exactly one observed period so far). | `frontend/src/features/market-health/stories/MarketBenchmarkStoryMessage.tsx` |

`DataStoryMessage` gains a third branch: `story.story_id === "market-benchmark"` delegates to
`MarketBenchmarkStoryMessage` — same thin-router pattern Story 2 established, no other file
changes. Reuses `RankedBarList`/`StoryBlock`/`Meter` — no new shared component needed, unlike
Story 2's `WorldRiskMap` (this story's data has no geography dimension).

### Story 4: beyond Design, Product & Engineering (added 2026-09-21 — `changes/2026-09-21-job-function-story.md`)

| Component | Responsibility | Location |
|---|---|---|
| `JobFunctionStoryMessage` | Renders `POST /api/market-health/stories/beyond-tracked-roles`'s resolved sections: framing line → `RankedBarList` (Job Function breakdown of `other`-classified postings) → `SharePieChart` *(revised 2026-09-22, was `Meter`)* (outside vs. inside the 3 tracked categories, with the real counts/percentage as a plain caption) → `RankedBarList` (real, un-normalized titles within the single largest function, heading built dynamically from the response's own `job_function` value). One movement, no year-on-year block (Job Function is brand new — no prior-year window exists yet). | `frontend/src/features/market-health/stories/JobFunctionStoryMessage.tsx` |

`DataStoryMessage` gains a fourth branch: `story.story_id === "beyond-tracked-roles"` delegates
to `JobFunctionStoryMessage` — same thin-router pattern as Stories 2-3. Reuses `RankedBarList`/
`StoryBlock`/`Meter` — no new shared component needed. `tsc --noEmit` and `npm run build` both
clean.

### Reference story: market data briefing

The Task Panel item **"What we know about the market"** — `DataStoryMessage` from
`POST /api/market-health/stories/market-data-briefing`. It is the reference implementation of
the standard above, in **two labelled movements**:

**Movement 1 — the market right now**
1. framing sentence (numbers as context only);
2. **the roles being hired** — `roles-offered.top_specializations` → `RankedBarList` (top 10;
   specialization, not `top_titles`; `unknown`/`other` excluded). Once the API sends
   `prior_share`/`delta_pp` on these items, each row also carries its `±N pp` delta; until
   then the delta column is simply absent.
3. **what employers ask for** — `employer-mentioned-skills.skills` → `SkillDemandChart`
   *(revised 2026-09-22)* — a real Nivo grouped bar chart, must-have vs. nice-to-have as two
   named series with a legend, replacing the original single `RankedBarList` with an opacity
   difference;
4. **pay transparency** — `compensation-coverage.coverage_by_confidence` → `SharePieChart`
   *(revised 2026-09-22, was `Meter` — this section's earlier "StoryFigure + Meter, the
   story's one Hero Figure" description was already inaccurate; no `StoryFigure` was ever
   built here)*, disclosed vs. undisclosed;
5. **where the roles are** — `geographic-coverage` → `RankedBarList`, normalised-location caveat.

**Movement 2 — how it's shifting (year on year)** — a short intro line naming the windows,
then:
6. **how the role mix is shifting** — `role-mix-shift` → `YearOnYearGroupedBars`;
7. **how seniority is shifting** — `seniority-shift` → `YearOnYearGroupedBars`;
8. **IC vs. management** — `track-shift` → `YearOnYearGroupedBars`.

At launch and through the platform's first year, sections 6–8 arrive with
`comparison_available: false` — `YearOnYearGroupedBars` shows each current window + the
"comparison starts …" line. Distinct form components: `RankedBarList`, `SharePieChart`,
`SkillDemandChart`, `YearOnYearGroupedBars` → four, well past the ≥2 minimum. Shows none of the
welcome's *current* figures. Provenance in the Reasoning Panel.

### Catalogue and response state

- The Task Panel owns story selection. The frontend does not render the story as an inline
   suggested-question block beneath the opening briefing.
- The initial task id is `market-data-briefing`; selecting `market-health` switches back to
   the hiring-status chart and conversation.
- A story request carries `story_id` when selected. The frontend does not duplicate intent
   matching or aggregate logic in the browser.
- Story answers show freshness and provenance in the existing Reasoning Panel. The trace must
   say that no language model was used and identify the owned-data aggregates queried.
- Loading, empty, partial-coverage, and unavailable states use the existing assistant-turn
   layout. A story must never render a blank panel when one section has no data.
- **Chat degraded-service message (added 2026-09-04 — Step 0 of
   `changes/2026-09-03-chat-resilience-and-instant-answers.md`).** When the chat model is
   unavailable or its daily cap is spent (`backend/specs/market-health/api.md` — Chat model
   tier and retry), the backend streams the calm "briefly unavailable" message as an ordinary
   text chunk — it renders through the existing follow-up `AITurn` text path with no new
   component. No frontend change needed for the message itself.

### Suggested questions (curated instant answers — added 2026-09-06, Step 14)

The curated instant-answer engine (`backend/specs/market-health/api.md` — Curated
instant-answer engine) answers common questions from the database with **no model call**, in
under a second. The frontend surfaces them so the fast path is one tap:

| Component | Responsibility | Location |
|---|---|---|
| `SuggestedQuestions` | Fetches `GET /api/market-health/chat-suggestions` once on mount. Renders each `question` as a chip (the existing Shortcut-Card-lite / button token — no new visual pattern). Clicking a chip submits that exact question through the same `useChat` `append` path as typing it — the backend then matches it to the curated catalogue and returns the instant answer. | `frontend/src/features/market-health/layout/SuggestedQuestions.tsx` |

- **Placement**: inside `ConversationThread`, directly below the active task's opening turn
  (welcome / chart+summary / story answer) and above that task's conversation turns — on
  **every** task (added 2026-09-06 —
  `changes/2026-09-06-chat-input-dead-on-non-conversation-tasks.md`). No new layout zone.
- **Each task is its own conversation.** `MarketHealthPage` calls
  `useChat({ id: activeTaskId, … })` — the Vercel AI SDK keys `messages`, streamed `data`,
  `isLoading`, and `error` by `[api, id]` (SWR), so one hook instance with a changing `id`
  yields fully isolated per-task histories. Switching tasks switches the conversation.
  `handleSubmit` (typed) and the chip handler (`append`) do **not** change the active task —
  the question and its answer join whichever task is active. `ConversationThread` renders,
  for every task: opening turn → `SuggestedQuestions` → that task's `pairs` (from `messages`).
  A stream in flight when the user switches away completes in its origin task.
- **Behaviour**: a chip click is identical to typing that question — same request, same
  streamed response, same Reasoning Panel. A curated hit streams instantly and its trace says
  "No language model was used"; if the catalogue ever changes and a chip no longer matches, it
  simply falls through to the model like any typed question (no special-casing in the client).
- **Empty/failed fetch**: render nothing (no error, no empty box) — the chips are an
  enhancement, not a dependency.
- The chip list is server-owned; adding a curated question is a backend catalogue change with
  zero frontend edits.

### Components

| Component | Responsibility | Location |
|---|---|---|
| `DataStoryMessage` | Renders a resolved story's fixed sections, freshness, and limitations | `frontend/src/features/market-health/stories/DataStoryMessage.tsx` |
| `ReasoningPanel` | Shows story provenance and the explicit no-model path | Existing reasoning-panel component |

The catalogue and story response are server-owned contracts. Adding a story should not require
changing the generic assistant message parser; adding a navigation entry is an explicit product
task change.
