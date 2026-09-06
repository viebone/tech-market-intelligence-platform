---
id: visual-design
version: 1.3
status: active
created: 2026-06-21
updated: 2026-09-06
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
