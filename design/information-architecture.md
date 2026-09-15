---
id: information-architecture
version: 2.6
status: active
created: 2026-06-11
updated: 2026-09-14
---

# Information Architecture — Tech Market Intelligence Platform

## Scope

This document defines navigation, layout, and terminology for the **consumer-facing
product** — the experience job seekers use, described throughout this file. It does not
govern internal/operational tooling built for the people running the platform.

The admin pipeline-visibility dashboard (`design/pipeline-visibility/experience.md`, serving
`outcomes/pipeline-processing-visibility.md`) is a deliberate example: it is a separate,
operator-only surface — not reachable from, or linked within, this navigation model — served
by its own backend-rooted deployment (see `changes/2026-08-13-admin-pipeline-dashboard.md`'s
Decision Log). It defines its own local navigation (Sidebar Nav / Main Content) entirely
within its own experience spec, using terms that are intentionally absent from the Content
Taxonomy below — they are not part of this product's consumer-facing vocabulary and must not
be confused with it.

Any future internal-tooling surface follows the same pattern: it does not need an entry here
unless it becomes reachable from, or shares navigation with, the consumer-facing product
described below.

This carve-out mirrors `design/foundations.md`'s own Scope section (v1.1), which exempts
internal tooling from the product's Agentic Conversational UI paradigm for the same reason.

**Extended, then revised, 2026-09-14** (`changes/2026-09-13-mcp-ai-agent-access.md`, for
`design/mcp-access/experience.md`): **Connect Your AI** is the opposite case from
pipeline-visibility above — it **is** part of the consumer-facing product and **is** reachable
from it, matching `design/foundations.md` v1.2's Scope section, which names this a
consumer-facing "external access surface," distinct from operator-only tooling. Unlike
pipeline-visibility, though, it needs no carve-out from the three-column layout at all: it lives
inside the existing **Output Panel**, as a second tab alongside Output (see Layout Model and
Navigation Model, below) — a zone this document's own Content Taxonomy already defined as
showing "outputs *and settings*" for the active task, before this feature gave that second half
any real content. (A first version of this placed it behind a new TopBar "Account" menu instead;
superseded same day in favour of the simpler Output Panel tab, which needed no new layout
element at all. Kept here only so a future reader sees why that note briefly existed.)

---

## Layout Model

The product uses a **three-column layout**. The three columns are always present on
desktop. The left column sets the context for the other two.

```
┌─────────────────┬───────────────────────────────────┬──────────────────────┐
│  Task Panel     │         Working Space              │   Output Panel       │
│  (left)         │         (centre)                   │   (right)            │
│                 │                                    │                      │
│  240px fixed    │   max-w-[1200px] · centred         │   320px fixed        │
│                 │                                    │                      │
│  Navigation     │   Conversation interface           │  [Output | Settings] │
│  list of tasks, │   for the selected task.           │   two tabs, always   │
│  questions,     │   This is where the user           │   both present       │
│  and processes. │   and system exchange              │                      │
│                 │   messages. All content            │  Output tab:         │
│                 │   (charts, summaries) lives        │   reference index    │
│                 │   here.                            │   of outputs. Each   │
│  Selecting an   │                                    │   entry: icon +      │
│  item here      │   Width never changes.             │   label + one-line   │
│  loads context  │   Side panels open                 │   description.       │
│  into the other │   around it, not                   │                      │
│  two columns.   │   at its expense.                  │  Settings tab:       │
│                 │                                    │   account-level      │
│                 │                                    │   surfaces (e.g.     │
│                 │                                    │   Connect Your AI),  │
│                 │                                    │   same regardless    │
│                 │                                    │   of active Task     │
└─────────────────┴───────────────────────────────────┴──────────────────────┘
```

### Column responsibilities

| Column | Width | Role |
|---|---|---|
| Task Panel | 240px fixed | Primary navigation. Selecting an item here defines what the working space and output panel show. The hierarchy setter. |
| Working Space | max-w-[1200px], centred | The conversation. All user–system exchanges happen here, including charts and summaries embedded in AI messages. Width never compresses to accommodate the side panels. |
| Output Panel | 320px fixed | Two tabs, always both present: **Output** (default) — a persistent reference index of all outputs produced by the active conversation, each entry icon + label + one-line description, clicking scrolls the working space to that output, never rendering the actual content itself; and **Settings** (added 2026-09-14) — account-level surfaces such as Connect Your AI, whose content stays the same regardless of which Task is active, unlike Output's. |

### The relationship between columns

Left selects the subject. Centre is where the work happens. Right shows what the work
has produced. When the user selects a different task in the left panel, both the working
space and the output panel update to reflect that task.

The working space and the output panel are always in sync around the same selected item.
They are two views of the same task — not independent sections.

**Exception (added 2026-09-14):** this holds for the Output Panel's **Output** tab only. Its
**Settings** tab is account-level, not task-level — switching tasks in the left panel never
changes what Settings shows, and leaving the Settings tab open while switching tasks is
expected, not a bug. Only the Output tab tracks the active task.

**Each task carries its own conversation** (clarified 2026-09-06 —
`changes/2026-09-06-chat-input-dead-on-non-conversation-tasks.md`). The chat input at the
bottom of the working space queries the *active* task; the question and its answer join that
task's thread, below the task's opening content. Switching tasks switches the whole
conversation. This is what "Follow-up … extends the conversation thread for the active task"
(Content Taxonomy) has always meant.

### Reasoning Panel — universal inline primitive

Every AI-generated message in the working space carries a **Reasoning Panel** — a collapsed
toggle ("View thinking") that sits below the message content. Expanding it reveals the full
reasoning trail: what inputs the AI received, which tools and data sources it accessed, and
the reasoning steps it took to reach its answer.

The Reasoning Panel is not a column, a modal, or a separate view. It is an inline expansion
within the working space that pushes subsequent content down. It does not affect the Task Panel
or the Output Panel. It is present on every AI message, in every task, without exception.

This is the product's expression of Principle 4 (Progressive Transparency with Full
Inspectability) from `design/foundations.md`. It is a product-level primitive, not a feature.

---

## Navigation Model

### Task Panel items

The task panel contains a vertical list of tasks the user has initiated or can initiate.
Each item maps to a named task with a specific question or goal. Items are ordered by
recency of use; pinned items appear at the top.

#### Task Panel structure

Updated 2026-09-04 — `changes/2026-09-04-about-this-platform-welcome.md`. The Task Panel is
not a flat, hand-maintained list — it has three parts, front to back:

1. **A pinned welcome** — "About this platform" — always first, always the default selection
   on first load. It orients a new visitor and links to every task currently in the story
   catalogue (see part 2).
2. **The story catalogue** — one task per entry in `design/market-health/data-stories.md`.
   Grows as entries are added there; order follows the catalogue's own document order. Adding
   a story adds a row to the table below; it does not change this structure.
3. **Pinned feature tasks** — tasks tied to a specific working-space experience rather than a
   predefined question, such as "Tech market hiring status". Currently last; more may be
   pinned as new outcomes are prioritised by the PM.

#### Current task list (v1)

| Task | Panel part | Display name | What it shows in working space | What it shows in output panel |
|---|---|---|---|---|
| about-this-platform | Pinned welcome | **About this platform** | Platform orientation: what this is, the current data inventory, and a live shortcut for every task currently in the story catalogue | A reference entry for the welcome |
| market-data-briefing | Story catalogue | **What we know about the market** | A concise, plain-language briefing based on the platform's current market data | A reference entry for the market overview |
| market-health | Pinned feature | **Tech market hiring status** | Conversation starting with the job openings trend chart and written summary embedded in the opening AI message | A reference entry for each output in the conversation. Opening entry: "Job openings trend — chart". Each subsequent AI response that produces output adds an entry. |

Additional story-catalogue tasks are added as new stories are catalogued in
`design/market-health/data-stories.md`; additional pinned feature tasks are added as new
outcomes are prioritised by the PM. Neither requires changing the Task Panel structure above.

**About this platform** is always first and selected on first load. Story-catalogue tasks
follow it, in catalogue order; pinned feature tasks come after those.

#### Task types

| Type | Description | Status |
|---|---|---|
| **Query Task** | A stored prompt the system executes on demand or on a schedule, returning a result the user can read and follow up on conversationally. All current tasks are Query Tasks. | Active |
| **Monitor Task** | A continuous autonomous operation that surfaces exceptions and alerts when user-defined thresholds are crossed. | Future |
| **Action Task** | An end-to-end agentic operation with a defined goal, plan, and run contract. The system shows its plan before executing and pauses at configured decision points. | Future |

---

### Output Panel Settings tab

Added 2026-09-14 (`changes/2026-09-13-mcp-ai-agent-access.md`) — no new top-level navigation
element. **Connect Your AI** lives behind the Output Panel's **Settings** tab (see Layout Model,
above), reached from within any Task by switching the Output Panel from Output to Settings.
Because Settings content is account-level, not task-level, it looks identical no matter which
Task the user switched from to get there.

*(A first version of this section put the entry point behind a new TopBar "Account" menu
instead — superseded same day by the simpler Settings-tab placement, which reuses a zone that
already existed rather than adding one. Kept here only so a future reader sees why a TopBar
change briefly existed in this document.)*

| Zone | Priority | Contains |
|---|---|---|
| Output Panel — Settings tab | Primary | Account-level surfaces. Today: **Connect Your AI** only — the platform's MCP endpoint, setup instructions, and the user's Connected Assistants. |

---

## Content Taxonomy

All labels, headings, statuses, and terminology across the product must use these exact
terms. Experience specs must not introduce synonyms or alternate names.

| Term | Definition | Where it appears |
|---|---|---|
| **Task** | A named goal or question the user is working on. Appears as an item in the Task Panel. | Task Panel |
| **Welcome** (added 2026-09-04) | The pinned, always-first Task Panel item ("About this platform"). Orients a new visitor and links to every task currently in the story catalogue. Not itself a story-catalogue member. | Task Panel, Working Space |
| **Data Story** (added 2026-09-04) | A predefined question with a fixed answer structure, resolved from the platform's own data with no model call. Documented in `design/{feature}/data-stories.md`. Each one is a Task Panel item. | Task Panel, Working Space |
| **Story Catalogue** (added 2026-09-04) | The ordered, growing set of Data Stories for a feature. Adding an entry adds a Task Panel item; it never requires changing the Welcome or the Task Panel's structure. | Task Panel |
| **Working Space** | The conversation interface for the active task. | Layout label |
| **Output Panel** | The panel showing outputs and settings for the active task. | Layout label |
| **Trend Chart** | A multi-line chart showing monthly job opening counts by role category over a selected time range. | Working Space, Output Panel |
| **Trend Reading** | A 3–4 sentence AI-generated summary of what the trend chart shows: direction, magnitude, and category divergence. | Working Space |
| **Role Category** | One of the three tracked job categories: Designer, Product Manager, Engineer. | Charts, labels, filters |
| **Time Range** | The period shown by a trend chart: This Year, Past 5 Years, or All Time. | Chart controls |
| **Demand Signal** | A data point representing job posting volume trend for a given role or skill. | Working Space, Output Panel |
| **Compensation Signal** | A data point representing salary range trend for a given role, seniority, or location. | Working Space, Output Panel |
| **Requirements Signal** | A data point representing the skills (must-have vs. nice-to-have), responsibilities, education level, and language requirements extracted from a single job posting, with a freeform catch-all for anything outside that standard structure. | Future tasks |
| **Layoff Signal** (broadened 2026-09-11 — `changes/2026-09-11-employment-event-ingestion.md`; scope clarified same day — `changes/2026-09-11-employment-events-no-company-matching.md`) | A reported employment event affecting a company or sector, sourced from an external registry — **never the platform's own job-posting data, and never matched or compared against it**: a layoff, closure, restructuring, bankruptcy, or offshoring (contraction), or an expansion or hiring announcement (growth). The name stays `Layoff Signal` — it was the only term already reserved for this concept — but its scope now spans both directions, not layoffs alone. | Working Space ("Employment risk across the market" data story; conversational answers in "Tech market hiring status"), Reasoning Panel (source + event detail on drill-down) |
| **Data Freshness** | The age and source of the data behind any given output. | Shown as a label on all data-backed claims |
| **Exception** | A signal or event that crosses a threshold and requires the user's attention. | Future: Alert Centre |
| **Reasoning Panel** | The expandable inline section beneath any AI message. Shows inputs, tools accessed, data sources, and reasoning steps. Collapsed by default; expanded on demand. Never absent. | Every AI message in Working Space |
| **Reasoning Step** | A single logical step in the AI's thinking process, shown inside the Reasoning Panel. | Reasoning Panel |
| **Source** | A data source or tool the AI consulted to produce an answer, shown inside the Reasoning Panel. For Market Health chat this is always one of the platform's own owned-data queries — the assistant does not consult the open web. | Reasoning Panel |
| **Follow-up** | A user message sent in the Working Space after the initial Task Result has loaded. Extends the conversation thread for the active task. | Working Space |
| **Output Tab** (added 2026-09-14) | The Output Panel's default tab — the pre-existing reference index of outputs for the active task. Named explicitly now that the panel has a second tab to distinguish it from. | Output Panel |
| **Settings Tab** (added 2026-09-14) | The Output Panel's second tab. Account-level, not task-level — its content doesn't change when the active Task changes. Today holds Connect Your AI only. | Output Panel |
| **Connect Your AI** (added 2026-09-14 — `changes/2026-09-13-mcp-ai-agent-access.md`) | The settings surface where a user connects, inspects, and revokes external AI clients (Claude, ChatGPT, Gemini CLI, or any MCP-compatible client), and sees each one's granted access and plan tier. Reachable from the Output Panel's Settings tab. See `design/mcp-access/experience.md`. | Output Panel (Settings tab) |
| **Connected Assistant** (added 2026-09-14) | A single external AI client the user has authorized, as it appears in Connect Your AI: which client, when connected, what it can see (in plain language, never a raw scope name), and its plan tier. | Connect Your AI |

---

## Key Pathways

1. **Market read before searching** — User selects "Tech market hiring status" in the Task
   Panel → reads the trend chart in the working space → reads the trend reading below it →
   switches time range to contextualise the current position → types a follow-up question →
   receives a focused answer in the conversation → exits with a directional read on the market.

2. **Conversational market query** — User types a question in the working space
   ("What does this mean for a senior UX designer in London?") → system responds in the
   conversation thread with a focused answer → output panel updates to reflect the latest
   output produced by the exchange.

3. **Drill down and verify** — User reads an AI claim they want to validate → clicks
   "View thinking" on that message → Reasoning Panel expands inline → user reviews
   Sources and Reasoning Steps → either trusts the answer or asks a targeted follow-up →
   collapses the panel and continues reading.

4. **Output access** — User sees a reference entry in the output panel → clicks the entry →
   the working space scrolls to that output in the conversation → the user reviews it in
   context without losing their position in a long conversation.

5. **Market overview** — User selects "What we know about the market" from the story catalogue
   → reads a concise business briefing → opens the reasoning panel only when they want
   source or calculation detail → selects the hiring-status task for the trend chart.

6. **First-time orientation** (added 2026-09-04 — `changes/2026-09-04-about-this-platform-welcome.md`)
   — User opens the product → "About this platform" loads by default → reads what the
   platform is and what data currently exists → taps a shortcut for one of the current
   story-catalogue tasks (or opens "Tech market hiring status" directly) → continues from
   there. Identical regardless of how many stories the catalogue currently holds.

7. **Connecting an external AI assistant** (added 2026-09-14 — `changes/2026-09-13-mcp-ai-agent-access.md`)
   — User switches the Output Panel to its Settings tab (from any Task) → Connect Your AI shows
   → copies the platform's MCP endpoint and reads setup instructions → leaves the product to add
   it inside their AI client of choice → that client redirects back to this platform's consent
   screen → user grants access → is returned to their AI client, connected → the new Connected
   Assistant appears under the Settings tab the next time the user opens it. See
   `design/mcp-access/experience.md` — Part 1, Flows A and B.

---

## Entry Points

- **Default** — User opens the product. "About this platform" is selected in the Task Panel
  (corrected 2026-09-04 — this previously named "Tech market hiring status", stale since the
  2026-09-04 briefing-task and welcome changes). The welcome — platform orientation, current
  data inventory, and shortcuts into the current story catalogue — loads in the working space
  as the opening AI message. The output panel shows one reference entry: the welcome.
- **Returning user** — Same as default. The working space restores the previous conversation
  for the selected task. The output panel shows a reference entry for every output produced
  in that conversation.
- **Direct task link** — A notification or shared link selects a specific task in the Task
  Panel and scrolls the working space to the relevant exchange.
- **Settings tab (added 2026-09-14)** — User switches the Output Panel from Output to Settings,
  from any Task → Connect Your AI loads, showing the MCP endpoint, setup instructions, and the
  user's current Connected Assistants (or the Empty State if there are none). Reachable
  identically from every Task, since the Output Panel is present everywhere; unlike the Output
  tab, what's shown never changes based on which Task the user switched from.
- **External consent redirect (added 2026-09-14)** — A user may land directly on this
  platform's OAuth consent screen without ever having opened the rest of the product — triggered
  from inside Claude, ChatGPT, Gemini CLI, or another MCP-compatible client when they add this
  platform's endpoint there. This screen carries no TopBar and no navigation; it must be legible
  entirely on its own (who's requesting access, what it's asking to do), since it may be a
  first-time visitor's only contact with this platform. See `design/mcp-access/experience.md` —
  Part 1, Flow B and Visual Design.
