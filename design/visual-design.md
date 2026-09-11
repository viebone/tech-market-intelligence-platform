---
id: visual-design
version: 1.6
status: active
created: 2026-06-21
updated: 2026-09-11
---

# Visual Design — Tech Market Intelligence Platform

## Colour System

### Mode
Dark-first. The product is used by professionals making high-stakes decisions, often under
stress. A dark interface reduces visual fatigue, signals seriousness, and keeps data the
focus rather than the chrome. Light mode is out of scope for v1.

### Palette

All values are Tailwind CSS colour tokens. Use the token name in code, not the hex.

| Role | Token | Hex | Used for |
|---|---|---|---|
| Page background | `gray-900` | #111827 | Root background of every page |
| Surface | `gray-800` | #1f2937 | Cards, panels, message bubbles, input backgrounds |
| Surface raised | `gray-700` | #374151 | Hover states, tooltips, active states on surfaces |
| Border | `gray-700` | #374151 | Dividers, card borders, input borders |
| Border subtle | `gray-800` | #1f2937 | Section separators within a surface |
| Text primary | `gray-100` | #f3f4f6 | Headings, values, primary labels |
| Text secondary | `gray-300` | #d1d5db | Body text, descriptions, AI responses |
| Text muted | `gray-400` | #9ca3af | Labels, metadata, timestamps, placeholder text |
| Text disabled | `gray-600` | #4b5563 | Disabled state text |

### Accent palette

Three accent colours correspond to the three role categories tracked by the product.
They are used consistently across charts, tags, and status indicators.

| Role category | Token | Hex | Usage |
|---|---|---|---|
| Designer | `indigo-500` | #6366f1 | Chart line, category tags, category indicators |
| Product Manager | `purple-500` | #a855f7 | Chart line, category tags, category indicators |
| Engineer | `emerald-500` | #10b981 | Chart line, category tags, category indicators |

### Semantic colours

| Semantic role | Token | Hex | Used for |
|---|---|---|---|
| Rising / positive | `emerald-600` | #059669 | Trend arrows, positive signal indicators |
| Stable / neutral | `amber-600` | #d97706 | Flat trend indicators |
| Declining / negative | `red-600` | #dc2626 | Trend arrows, negative signal indicators |
| Error background | `red-950/30` | — | Error state card backgrounds |
| Error border | `red-900/40` | — | Error state card borders |
| Error text | `red-400` | #f87171 | Error messages |

**Reviewed 2026-09-11, then reverted same day** (`changes/2026-09-11-employment-event-ingestion.md`
Step 4, superseded by `changes/2026-09-11-employment-events-no-company-matching.md`): the trend
chart briefly gained event markers reusing Rising/Declining/Stable, then the whole marker
layer was removed once the user directed that employment events must never be matched to
tracked companies at any layer, including a chart overlay. No lasting change to this section —
kept here only so a future reader sees why this note briefly existed.

---

## Typography

### Typeface
System font stack — no custom typeface in v1.
`font-family: ui-sans-serif, system-ui, -apple-system, sans-serif`

Rationale: system fonts render crisply on all platforms, load instantly, and feel native.
Do not introduce a web font unless there is a specific brand reason to do so.

### Scale

All sizes are Tailwind text utilities. Line heights are Tailwind leading utilities.

| Role | Tailwind class | Size | Weight | Line height | Used for |
|---|---|---|---|---|---|
| Page title | `text-base font-semibold` | 16px | 600 | 1.5 | TopBar product name |
| Hero headline (added 2026-09-04) | `text-3xl font-bold` | 30px | 700 | 1.2 (`leading-tight`) | The welcome's landing-page-style headline only — see Component Aesthetics — Hero Figure & the entry-point pattern. Not used elsewhere; a conversation's own title stays at Conversation title, below. |
| Hero figure (added 2026-09-04) | `text-4xl font-bold` | 36px | 700 | 1.1 | A single leading number (dataviz "Hero Figure"), proportional (not tabular) figures. Exactly one per view. |
| Conversation title | `text-2xl font-semibold` | 24px | 600 | 1.3 (`leading-tight`) | First user message in each conversation |
| User message | `text-base font-medium` | 16px | 500 | 1.5 | Subsequent user messages |
| Section heading | `text-sm font-medium` | 14px | 500 | 1.4 | Card headers, panel titles |
| Body | `text-sm` | 14px | 400 | 1.6 (`leading-relaxed`) | AI responses, descriptions, summaries |
| Label | `text-xs font-medium` | 12px | 500 | 1.4 | Tags, column headers, form labels |
| Caption | `text-xs` | 12px | 400 | 1.4 | Metadata, timestamps, data freshness |
| Monospace | `text-xs font-mono` | 12px | 400 | 1.4 | API call references, code snippets |
| Chart axis | `text-[10px]` | 10px | 400 | 1 | Chart axis labels and tick marks |

---

## Spacing

### Base unit
4px (`1` in Tailwind's spacing scale). All spacing is a multiple of 4px.

### Scale

| Token | Tailwind | Value | Used for |
|---|---|---|---|
| xs | `gap-1` / `p-1` | 4px | Icon-to-label gaps, tight inline spacing |
| sm | `gap-2` / `p-2` | 8px | Within-component padding (compact) |
| md | `gap-4` / `p-4` | 16px | Standard component padding, card padding |
| lg | `gap-6` / `p-6` | 24px | Between related components, section padding |
| xl | `gap-8` / `py-8` | 32px | Between conversation turns, major section gaps |
| page | `px-4` | 16px | Horizontal page margin (mobile-first) |

---

## Layout

### Three-column structure

The product uses a three-column layout. Column widths are fixed; the working space
never shrinks to accommodate the side panels.

| Zone | Width | Behaviour |
|---|---|---|
| Task panel (left) | 240px | Fixed. Contains the task/question navigation list. |
| Working space (centre) | max-w-[1200px] | Max width, centred. Fills available space between the side panels. Charts fill the full working space width. |
| Output panel (right) | 320px | Fixed. Shows a reference index of outputs for the active task — not the content itself. |

The left panel drives the context loaded into the working space and output panel.
Selecting a task on the left changes what appears in both right zones simultaneously.

### Sidebar + Main Content (operator surfaces)

Used only by internal/operator-only surfaces exempt from the three-column model per
`design/foundations.md` v1.1's Scope section and `design/information-architecture.md`
v2.2's Scope section — e.g. the admin pipeline-visibility dashboard
(`design/pipeline-visibility/experience.md`). Same colour, type, and spacing tokens as the
rest of the product; a different, simpler two-zone shape, not a three-column layout with a
zone removed.

| Zone | Width | Behaviour |
|---|---|---|
| Sidebar Nav (left) | 220px fixed | Static page-navigation list. `bg-gray-800`, `border-r border-gray-700`. Unlike the consumer product's Task Panel, entries are fixed links (e.g. Overview, Postings, Ingestion Runs), not a dynamic, reorderable task list. |
| Main Content | Fluid, `max-w-[1400px]`, centred, `px-6` | Fills the remaining width. No Output Panel counterpart — operator surfaces have no reference-index concept; content (summary numbers, tables, detail views) renders directly here. |

---

## Component Aesthetics

### Surfaces — cards and panels

```
background:    gray-800 (bg-gray-800)
border:        1px solid gray-700 (border border-gray-700)
border-radius: 8px (rounded-lg)
shadow:        none (dark surfaces do not use drop shadows — borders do the work)
padding:       16px (p-4) standard · 24px (p-6) for message bubbles
```

### Message bubbles

All messages — AI and user — are left-aligned within the working space.
There is no left/right split by speaker. Turn distinction is communicated through
visual hierarchy and surface treatment, not position.

**User turn (left-aligned, no bubble)**
```
background:    none
border:        none
padding:       vertical only (py-3)
text-align:    left
max-width:     75% of working space width
```
First message in a conversation:
  `text-2xl font-semibold` · gray-100 · styled as the conversation's page title

Subsequent user messages:
  `text-base font-medium` · gray-100

**AI turn (left-aligned, with surface)**
```
background:    gray-800
border:        none
border-radius: 12px (rounded-xl)
padding:       20px 24px (py-5 px-6)
width:         100% of working space width
```

### Inputs

```
background:    gray-800 (bg-gray-800)
border:        1px solid gray-700 (border-gray-700)
border-radius: 8px (rounded-lg)
text:          gray-100
placeholder:   gray-500
focus:         ring-1 ring-indigo-500 — indigo focus ring, border stays gray-700
padding:       10px 14px (py-2.5 px-3.5)
```

### Buttons

**Primary**
```
background:    indigo-600
text:          white
border:        none
hover:         indigo-700
border-radius: 6px (rounded-md)
padding:       8px 16px (py-2 px-4)
font:          text-sm font-medium
```

**Ghost / text action**
```
background:    transparent
text:          gray-400
hover text:    gray-200
border:        none
padding:       4px 8px (py-1 px-2)
```

**Tab / range selector**
```
container:     gray-800 background, rounded-md, p-0.5
active tab:    gray-600 background, white text, rounded
inactive tab:  transparent, gray-400 text, hover gray-200
font:          text-xs
padding:       4px 12px (py-1 px-3)
```

### Entry-point components (added 2026-09-04)

Added for the "About this platform" welcome (`changes/2026-09-04-welcome-visual-data-points.md`)
— the product's one landing-page-style surface. Follow the `dataviz` skill's form and mark
rules; documented here so a future entry-point-style surface reuses them rather than
reinventing the look. **Scoped to entry points, not a general replacement for the plain
AI-turn prose treatment** every other message keeps.

**Eyebrow label**
```
text:          gray-500, text-[10px] font-medium uppercase tracking-widest
usage:         one per hero, directly above the Hero headline — same token as the
               existing Task Panel section label ("Tasks"), reused for consistency
```

**Hero Figure**
```
value:         text-4xl font-bold text-gray-100 (Hero figure type scale, above) —
               never an accent colour; a hero figure is a headline metric, not a
               categorical data point (dataviz: "text never wears the data colour")
label:         text-xs text-gray-500, below the value, sentence case, no trailing colon
count:         exactly one per view
```

**Stat Tile**
```
value:         text-xl font-semibold text-gray-100
label:         text-xs text-gray-500, below the value
layout:        supporting tiles sit beside or below the Hero Figure, smaller and
               lower-emphasis than it — never equal visual weight to the hero
```

**Category Share Bar**
```
type:          horizontal stacked bar (categorical, part-to-whole) — dataviz form
               rules: 3 tracked Role Categories, ≤4 series, so every segment is
               direct-labelled, no separate legend box required
height:        12px (h-3) track, ≤24px per dataviz's bar-thickness cap
segment ends:  4px rounded on the bar's outer left/right ends only; square where
               segments meet
segment gap:   2px gap in the surface colour (gray-800) between touching segments —
               the gap separates them, never a stroke
colour:        the existing Accent palette (Designer indigo-500 · Product Manager
               purple-500 · Engineer emerald-500) — the same three hues the trend
               chart already uses for the same categories; never a new hue
labels:        role name + share, placed above or beside each segment (inside only
               if the text fits with padding on both sides — see dataviz's label
               rule); values also available via the Reasoning Panel / provenance
```

**Shortcut Card**
```
background:    gray-800/60, hover gray-800
border:        1px solid gray-700, hover gray-500 (transition-colors duration-150)
border-radius: 8px (rounded-lg)
padding:       10px 14px (py-2.5 px-3.5)
text:          text-sm text-gray-200, question text left-aligned
trailing icon: a small arrow, gray-500, hover gray-300
usage:         one per story-catalogue entry in the welcome's call-to-action list;
               replaces a plain list item with a clickable, hoverable row
```

### Chart event marker — removed 2026-09-11

Added and removed the same day (`changes/2026-09-11-employment-event-ingestion.md`, then
`changes/2026-09-11-employment-events-no-company-matching.md`) — a marker layer for the trend
chart's tracked-company-matched employment events, retired once the user directed that
employment events must never be matched to tracked companies at any layer. No component to
reuse; documented here only so the removal is traceable.

### Ranked bar list (added 2026-09-06 — `changes/2026-09-06-market-story-visual-and-dedup.md`)

A short, ranked "top N" comparison — top job titles, most-requested skills, top
locations. The magnitude form from the `dataviz` method (compare low → high → one
hue, not categorical colour). Used in data stories, not entry points.

```
row:           label (left, text-sm text-gray-300, truncate) then the bar then the
               value (text-xs tabular-nums text-gray-400, right)
bar:           a track (gray-800, rounded, h-1.5) with a fill (indigo-500 at ~70%
               opacity — one hue for the whole list, magnitude by length only);
               fill width = value / max(values) in the list
rows:          5–8; gap-2 between rows; never a scrollbar — cap the list, don't scroll it
emphasis:      an optional first-class subset (e.g. skills marked "must-have") may use
               the full-opacity hue while the rest stay at ~70% — a second, ordered
               encoding, not a new colour
labels:        every row is directly labelled with its value (a short list, so this is
               not the "number on every point" anti-pattern); no axis
zero/empty:    a list with no data renders its section's "not enough data yet" line,
               never an empty track
```

### Data Story composition (added 2026-09-10 — `changes/2026-09-10-story-visual-standard.md`)

The standard **every data-story renderer must follow**, so a new catalogue entry looks and
reads like the last one shipped ("What we know about the market") without a bespoke design
pass. A data story is the fixed-structure, no-model answer a catalogue entry produces when
its Task Panel item is selected (`design/market-health/data-stories.md`).

**Why this surface gets composition polish.** The market-health story surface faces a
*professional audience* deciding whether the market is worth engaging — not an operator
supervising a pipeline. A story people find inviting is a story they finish, so they get the
market read (`outcomes/understand-market-health-before-searching.md`). This rationale is
**scoped to data stories and the Welcome**. It does not extend to operator surfaces (admin
dashboard, reasoning panels), it does not relax any Motion rule, and it is not a product-wide
design goal.

**A story is a composed piece, not a report.** In order:

1. **Framing line** — one sentence naming what's being summarised. `text-sm leading-relaxed
   text-gray-300`. Numbers appear only as context here, never as the point. Not a heading.
2. **3–6 blocks**, each with the same anatomy:
   ```
   heading   text-sm font-semibold text-gray-200        (what this block answers)
   subtitle  text-xs text-gray-400, mt-0.5               (what's being measured and its unit —
                                                           present whenever the heading alone
                                                           doesn't make that obvious; see Data
                                                           Legibility, below)
   visual    one element from the vocabulary below      (carries the point)
   qualifier text-xs text-gray-500, mt-2                 (sample size / coverage caveat)
   ```
   A block is separated from the next by `border-t border-gray-800 pt-4` — the same divider
   rhythm the reference story uses. The whole story is wrapped `space-y-5`. Subtitle and
   qualifier read differently on purpose: subtitle states **what the numbers are**, qualifier
   states **how much to trust them** — never merge the two into one line.

**Visual vocabulary** — a block's `visual` is one of these, never free prose:

| Element | Use it for | Spec |
|---|---|---|
| **Ranked bar list** | a "top N" magnitude comparison (roles, skills, locations) | "Ranked bar list", above |
| **Hero Figure** | the single number the story leads with — **at most one per story** | "Hero Figure" (Entry-point components), above |
| **Stat Tile** | a supporting number beside/below the Hero Figure | "Stat Tile", above |
| **Meter** | one share as a part-to-whole bar (e.g. "6% of postings state a salary") | below |
| **Category Share Bar** | a part-to-whole split across the 3 tracked Role Categories | "Category Share Bar", above |
| **Trend line** | a value over time, where the block's data is genuinely time-series | Chart Specification, `design/market-health/experience.md` (compact variant) |
| **Year-on-year comparison** | how a set of proportions shifted between the trailing 12 months and the 12 months a year earlier — one year back, never more | below |

**Meter** (new here):
```
figure:   the share as a percentage — text-3xl font-bold text-gray-100, with a
          text-sm text-gray-400 caption beside it ("of postings state a salary range")
track:    h-2 w-full rounded-full bg-gray-800
fill:     h-full rounded-full bg-indigo-500, width = the share (min 1% so it's visible)
below:    one text-sm text-gray-400 line stating the complement plainly
          ("The other 94% don't disclose compensation.")
```

**Year-on-year comparison** (added 2026-09-10 — `changes/2026-09-10-story-yoy-breakdowns.md`):

A block that answers "how is this mix *changing*", not "what is it now". Exactly two 12-month
windows — the trailing 12 months and the 12 months ending one year before that. Not a
multi-year sparkline, not a rolling series.

```
windows:  both date ranges stated in words, once, directly under the block heading —
          text-xs text-gray-500 (e.g. "Sep 2026 – Sep 2027, compared with the year before")
legend:   one line naming what the two bar colours mean — text-xs text-gray-500, directly
          below the windows line — e.g. "Lighter bar: a year ago. Solid bar: now." Required
          whenever the comparison is available (two colours are on screen); omitted in the
          "no prior window yet" state below, where only one colour appears. Added 2026-09-11
          (`changes/2026-09-11-data-legibility-market-health.md`) — found missing during a
          data-legibility audit: the two-colour encoding was documented here but never
          explained to the end user.
row:      one per category, ordered by current-window share, descending. Each row:
            label   text-sm text-gray-300, left, truncate
            bars    a shared track (bg-gray-800, rounded, h-1.5). Two fills on it:
                      prior year   bg-gray-700 (a muted ghost of the earlier share)
                      current      bg-indigo-500 at ~70% opacity (same magnitude hue
                                   as Ranked bar list) — width = current share
                    the ghost sits behind; the current fill overlays from the same
                    left edge, so the visible gap between their right ends IS the change
            delta   right, text-xs tabular-nums:
                      "+3 pp" rising  ·  "−2 pp" falling  ·  "no change"
                    with a ▲ / ▼ / – glyph BEFORE the number — the glyph and the sign
                    both carry the direction; colour never carries it alone
rows:     the categories of the dimension (role_category: the 3 tracked + `other` as
          context; level: the LEVEL_LADDER; track: ic/management). For an open-ended
          dimension (specialization) it is a Ranked bar list of the top 10 by current
          share, each row carrying the same "+N pp" delta on the right.
meaning:  one plain sentence under the block — what a shift in this mix means for the
          reader ("A rising management share means more of the new roles are for people
          who lead teams rather than do the work directly."). text-sm text-gray-400.
```

**"No prior window yet" state.** Until the platform has ~13 months of data there is no
year-earlier window to compare against. The block does **not** hide and does **not** show a
"not enough data" blank — it renders the **current window only** (as a plain Ranked bar list
or share bar, no ghost, no delta column) plus one muted line:
`text-xs text-gray-500` — "Year-on-year comparison starts {Month Year}. Tracking since {date}."
This is the block's state at ship time and for the product's first year; it must read as
"coming soon", not "broken".

**Combination rule.** At least **two distinct visual forms** across a story (3+ preferred) —
a story that is five ranked bar lists in a row is under-composed. Where a form repeats, each
instance stays visually distinct through its heading and values, and the author should check
whether a different form fits some of the data better (a share where it's part-to-whole, a
trend where it's time-series).

**Chart-first.** The visual carries the point; the heading and qualifier are labels, not the
content. No block is prose-only except the framing line.

**Consistent across every story:** the block anatomy and divider rhythm above; the validated
palette (magnitude = one muted hue by length; categorical = only the three role accents);
the type scale in this table; `space-y-5` outer rhythm. A reader should recognise "this is a
data story" before reading a word.

**Rules out** (in addition to the product-wide list at the end of this doc):
- A story that is one undifferentiated block, or all prose.
- A block rendered as an empty chart — an `insufficient_data` block shows its "not enough
  data yet" line (`design/market-health/data-stories.md` — Honesty and empty states), never
  an empty track.
- Repeating the "About this platform" welcome's *current-snapshot* figures (job count,
  company count, collection start, current role-category split). A story may show a
  *year-on-year shift* in the same dimension — that is a different question (change, not
  state). It never repeats the welcome's current numbers as-is.
- More than one Hero Figure per story.
- A new accent hue, or any entrance animation on the data (Motion rules unchanged).

**Reference implementation:** `market-data-briefing` (`DataStoryMessage.tsx`), two labelled
movements (revised 2026-09-10 — `changes/2026-09-10-story-yoy-breakdowns.md`):
- *The market right now* — framing line → roles being hired (ranked bars) → what employers ask
  for (ranked bars, must-have emphasised) → pay transparency (Hero Figure + Meter) → where the
  roles are (ranked bars).
- *How it's shifting (year on year)* — role mix / seniority / IC vs. management, each a
  Year-on-year comparison. In the "no prior window yet" state until the product's data spans a
  year.

### Reasoning Panel toggle — "View thinking / Hide thinking"

The toggle is the entry point to the Reasoning Panel. It appears inside every AI turn,
between the message header and the answer content.

**Position within an AI turn:**
```
[Avatar]  AI Name
          Subtitle (if any)
          ⌄ View thinking  ·  2.3s        ← toggle line
          ─────────────────────────────
          Answer content...
```

**Toggle line anatomy:**

| Element | Style | Notes |
|---|---|---|
| Arrow icon | `↓` collapsed · `↑` expanded | Inline, before the label |
| Label | "View thinking" collapsed · "Hide thinking" expanded | Switches on state change |
| Separator | ` · ` | `text-gray-600` |
| Generation time | e.g. "2.3s" | `text-gray-600` — how long the AI took to produce this response |

**Toggle style:**
```
font:        text-xs (12px, 400 weight)
color:       gray-500 (text-gray-500)   ← tertiary link — lighter than ghost button
hover color: gray-300 (hover:text-gray-300)
background:  none
border:      none
cursor:      pointer
display:     inline-flex, items-center, gap-1
margin-top:  4px (mt-1) below subtitle or avatar/name line
```

This is a **tertiary link** — one level below the ghost/text action style. It is intentionally
unobtrusive. The user should notice it is there without it competing with the answer content.

**Expanded state:**

When expanded, the Reasoning Panel appears immediately below the toggle line, before the
answer content. It pushes the answer down. The answer content is never hidden — the panel
inserts between the toggle and the answer.

```
[Avatar]  AI Name
          Subtitle (if any)
          ↑ Hide thinking  ·  2.3s

          ┌─────────────────────────────────┐  bg-gray-800
          │  Reasoning Panel content        │  border-y border-gray-700
          │  (inputs, sources, steps)       │  py-4 px-4
          └─────────────────────────────────┘

          Answer content...
```

**Panel background:** `bg-gray-800` — one step above the page background (`gray-900`).
This visually separates the reasoning trace from the answer content below it. The panel
reads as metadata/supporting context, not as part of the answer itself. No rounding — the
panel spans the full content width as a horizontal band, bounded only by top and bottom borders.

**Panel wrapper:**
```
bg-gray-800 border-y border-gray-700 py-4 px-4 my-2 space-y-4
transition-all duration-200 ease-in-out
```

**Transition:**
`transition-all duration-200 ease-in-out` on the panel height.
The toggle label and arrow swap instantly on click (no transition on the text itself).

### Dividers

```
colour:  gray-700 (border-gray-700)
weight:  1px
style:   solid
```

Use dividers to separate zones within a surface. Never use dividers as decoration.

### Data table (operator surfaces)

New pattern — the consumer product has no tabular data view today. Used by the admin
pipeline-visibility dashboard's Postings and Ingestion Runs tables.

```
header row:    bg-gray-800, border-b border-gray-700
               label: text-xs font-medium text-gray-400, uppercase, tracking-wide
               sortable column: cursor-pointer, hover text-gray-200
               active sort: ↑/↓ arrow (text-gray-400) inline after the label
body row:      border-b border-gray-800 (Border subtle)
               text: text-sm text-gray-300
               hover: bg-gray-700 (Surface raised)
cell padding:  16px 16px (py-4 px-4) — matches md spacing token
```

### Filter chip (operator surfaces)

New pattern — represents one active filter on a table; removable.

```
background:    gray-700 (Surface raised)
text:          text-xs font-medium, gray-100
border-radius: 9999px (rounded-full)
padding:       4px 10px (py-1 px-2.5)
remove icon:   × inline after label, gray-400, hover gray-200
```

**Suggested-question chip (consumer, added 2026-09-06 — `changes/2026-09-03-chat-resilience-and-instant-answers.md`).**
Interactive variant of the filter chip — a tappable pill that submits a curated
instant-answer question. Not removable; no × icon.
```
background:     gray-800/60, hover gray-800
border:        1px solid gray-700, hover gray-500 (transition-colors duration-150)
text:          text-xs, gray-300, hover gray-100
border-radius: 9999px (rounded-full)
padding:       6px 12px (py-1.5 px-3)
disabled:      opacity-40 (while a request is streaming)
```

### Status badge / pill (operator surfaces)

New pattern — a small inline label for row/record status (e.g. Requirements Status:
"Extracted" / "Pending" / "Failed"; a `taxonomy_version` freshness marker; an ingestion run's
outcome). Reuses the existing Semantic colours table below — no new colours introduced.
Always pairs colour with a text label, per "What this rules out."

```
background:    {semantic colour}/15  e.g. emerald-600/15, amber-600/15, red-600/15
text:          {semantic colour} at full strength, e.g. emerald-400, amber-400, red-400
border-radius: 4px (rounded)
padding:       2px 8px (py-0.5 px-2)
font:          text-xs font-medium
```

| Meaning | Semantic colour | Example labels |
|---|---|---|
| Complete / success / current | `emerald` (Rising / positive) | "Extracted", current `taxonomy_version` |
| Not yet resolved, not an error | `amber` (Stable / neutral) | "Pending", stale `taxonomy_version`, `unknown` classification value |
| Failed | `red` (Declining / negative) | "Failed", ingestion run error |

`unknown` classification values and "Pending" status intentionally share the amber
treatment — both mean "not yet resolved," not "broken." Only "Failed" states use red. This
matches the amber/red distinction `design/pipeline-visibility/experience.md`'s Chart
Specification and Edge Cases sections already rely on.

---

## Data Legibility

Added 2026-09-11 — `changes/2026-09-11-data-legibility-market-health.md`, applying the
framework-level `data-legibility` skill (workspace root `CLAUDE.md`, Rules for AI #10) to this
product. Every chart, data-story block, ranked list, meter, and badge in this product follows
these conventions — decided once here, not reinvented per experience spec.

### Titles & subtitles
A data-story block's `heading` names what it answers; its `subtitle` (new slot, "Data Story
composition" below) states what's being measured and its unit whenever the heading alone
doesn't make that obvious — e.g. heading "Companies with the most reported impact", subtitle
"Ranked by jobs reported affected, summed across contraction events in the window." A subtitle
is required unless the heading is already fully self-contained (e.g. a Meter's own caption
already states the unit inline — see Meter, above — so its `StoryBlock` doesn't need a
separate subtitle too).

### Units
- Counts (postings, mentions, jobs affected): plain `toLocaleString()` numbers, unit named
  once in the block's subtitle — never repeated on every row of a `RankedBarList`.
- Percentages: `N%` (or `<1%` below one point), via `RankedBarList`'s `formatValue`.
- Percentage-point deltas (year-on-year): `+N pp` / `−N pp` / "no change" — `pp` always
  spelled out, never bare.
- Dates/windows: stated in words ("Sep 2026 – Sep 2027"), never a raw ISO string in visible copy.

### Colour & shape legends
Colour or shape carrying meaning is always paired with a text label — this product's existing
"Colour as the sole encoding" rule (What this rules out, below) already required this; treat
it as covering every new use, not only the ones enumerated when that rule was written (trend
arrows, chart lines, status tags). Concretely: a semantic colour states its direction in a
caption or subtitle at least once per view; an opacity/shape distinction (e.g. `RankedBarList`'s
`emphasis` — full opacity vs. ~70%) gets an inline caption naming what the two states mean
(e.g. "Solid bars are must-have mentions."); `YearOnYearBars`'s two bar colours get a legend
line stating which is which (Year-on-year comparison, above).

---

## Motion

### Default transition
`transition-colors duration-150 ease-in-out`

150ms is fast enough to feel responsive, slow enough to be perceived.
Use it on all colour/background state changes (hover, focus, active).

### Loading states

**Skeleton pulse:** `animate-pulse` on placeholder shapes. Background `gray-700`.
Use for content areas where the shape is known before content arrives.

**Bouncing dots:** Three `w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce`
dots with staggered 150ms delays. Use for streaming/generating states where
duration is unknown.

**Spinner:** `animate-spin` SVG circle. Use for point-in-time fetch operations
(e.g. refetching data after a filter change).

### Allowed motion types
- Colour transitions (hover, focus, active)
- Opacity transitions (appear/disappear)
- Height transitions for expand/collapse (Reasoning Panel, user turn truncation)
- Loading animations (pulse, bounce, spin)

### Not allowed
- Page transitions or route animations
- Parallax or scroll-driven effects
- Entrance animations on data (charts render immediately, not animated in)
- Motion that conveys meaning without a text or icon equivalent

---

## What this rules out

- **Light backgrounds on primary surfaces.** No white cards, no off-white panels.
  The entire product is dark. Any light surface would break visual coherence.
- **Colour as the sole encoding.** Every colour-coded element (trend arrows, chart lines,
  status tags) must also carry a text label or icon. Colour reinforces meaning; it does not
  replace it.
- **Custom typefaces.** System fonts only in v1. Do not add Google Fonts or variable fonts.
- **Drop shadows on dark surfaces.** Borders do the work. Shadows read poorly on dark
  backgrounds and add visual noise.
- **More than three accent colours.** The three role-category colours (indigo, purple, emerald)
  are the only accents in the product. Do not introduce additional accent colours for new
  features without updating this spec.
- **Decorative motion.** Every animation must have a functional reason (loading, state change,
  expand/collapse). No animations for visual interest.
- **Dense or compact layouts that sacrifice readability.** The user is processing data under
  stress. Generous line-height and padding are not optional.
