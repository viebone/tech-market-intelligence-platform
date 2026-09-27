---
id: visual-design
version: 2.2
status: active
created: 2026-06-21
updated: 2026-09-27
---

# Visual Design — Tech Market Intelligence Platform

> **v2.2 (2026-09-27)** — `changes/2026-09-27-treemap-legibility.md`. The Treemap's first shipped
> version (all-one-fill indigo-400, 1px gap into an unset background) proved unreadable in
> practice — adjacent similarly-sized tiles were indistinguishable. Revises Treemap only: a
> validated 4-step sequential shade-by-volume ramp (indigo-600→400→300→200, dark-mode anchored
> so brighter reads as "more") as a secondary cue alongside area, and a real 2px gray-800 gap
> rendered on the treemap's own container rather than left to whatever sits behind it. No other
> chart form changes.
>
> **v2.1 (2026-09-26)** — `changes/2026-09-26-data-story-chart-variety.md`. Adds the Data Story
> chart forms that make stories varied without misrepresenting their data (Stacked share bar,
> Ordered columns, Diverging change bars, Range chart, Treemap, Stat Tile pair, Time series), a
> **Chart accessibility standard** (contrast measured with the dataviz validator, not assumed),
> a stronger **no-repeated-form-within-a-story** rule with a "choose the form by the data's job"
> table, and a chart **definition pattern**. Existing tokens change because measurement showed
> they fail: muted series `gray-600` → `gray-500`, small caption text `gray-500` → `gray-400`, and
> (same day, `changes/2026-09-26-role-palette-accessibility.md`) the **role accents** — Product
> Manager `purple-500` → `fuchsia-600`, Engineer `emerald-500` → `emerald-600`. Story 2's World
> risk map and its blocks are untouched.

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
| Product Manager | `fuchsia-600` | #c026d3 | Chart line, category tags, category indicators |
| Engineer | `emerald-600` | #059669 | Chart line, category tags, category indicators |

**Revised 2026-09-26** (`changes/2026-09-26-role-palette-accessibility.md`). Product Manager was
`purple-500` #a855f7 and Engineer `emerald-500` #10b981. Measured with the dataviz validator,
Designer + Product Manager were **indistinguishable under protanopia (ΔE 0.9) and only ΔE 11.3
apart with normal vision** (hard floor 15), and `emerald-500` sat outside the dark-mode lightness
band. The trio above passes every check on both `gray-800` and `gray-900`: normal-vision floor
ΔE 18.6 (fuchsia ↔ indigo, the closest pair), contrast 3.12–4.71:1, and a single colour-vision
**warning** — fuchsia ↔ indigo ΔE 6.5 under deuteranopia — which is legal only because a role is
**never told apart by colour alone** (Chart accessibility standard, rules 5–6). Fuchsia-600 was
chosen over the first candidate `pink-500` because pink sits at ΔE 14.5 from the `red-600`
"Declining" semantic (below the 15 floor) wherever a role line and a decline indicator share a
view; fuchsia is ≥ 25 from every semantic colour. **Engineer `emerald-600` is the same hue as the
"Rising / positive" semantic below** — direction is always also carried by a ▲/▼ glyph and text,
so no meaning ever depends on telling them apart. Fuchsia-600 is only 3.12:1 on `gray-800` —
it must never be made darker.

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
| Chart axis (trend chart only — legacy) | `text-[10px]` | 10px | 400 | 1 | The hiring-status trend chart's axis labels and ticks. **Below the 12px Data Story chart minimum** (row below) — left as-is because that chart is outside this change's scope; tracked as a follow-up in `changes/2026-09-26-data-story-chart-variety.md`. |
| Story chart text (added 2026-09-26) | `text-xs` | 12px | 400 | 1.4 | **Every** label, axis tick, direct value label, legend line, tooltip and table cell inside a Data Story chart. 12px is the floor — nothing smaller. Value labels use `tabular-nums`. |
| Story eyebrow (added 2026-09-26) | `text-xs font-medium uppercase tracking-widest text-gray-400` | 12px | 500 | 1.4 | The movement label opening each movement of a story ("The market right now"). Was 10px / `gray-500`; on `gray-800` that measured 3.04:1, under the 4.5:1 text minimum. The Welcome's own Eyebrow label (Entry-point components) is unchanged — outside this change. |

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
| Output panel (right) | 320px | Fixed. Two tabs — Output (default) and Settings (added 2026-09-14, see below). The Output tab shows a reference index of outputs for the active task, not the content itself; the Settings tab is account-level and doesn't change with the active task. |

The left panel drives the context loaded into the working space and output panel.
Selecting a task on the left changes what appears in both right zones simultaneously — this
holds for the Output tab only; the Settings tab is unaffected by task selection.

### Output Panel tabs (added 2026-09-14 — `changes/2026-09-13-mcp-ai-agent-access.md`)

The Output Panel's two tabs, **Output** and **Settings**, are switched using the existing **Tab
/ range selector** pattern below (Component Aesthetics) — the same pill-style control already
used for chart time ranges — reused as-is, no new tab component. The switcher is pinned at the
top of the Output Panel, above whichever tab's content is currently showing, and is present on
every Task since the Output Panel itself always is.

```
Output Panel (320px fixed)
┌───────────────────────────┐
│  [Output] [Settings]      │  ← Tab / range selector, pinned, gray-800 track
├───────────────────────────┤
│                            │
│  active tab's content     │
│                            │
└───────────────────────────┘
```

Switching tabs never affects the Task Panel or the Working Space. See "Output Panel — Settings
tab" (Component Aesthetics, below) for what the Settings tab contains.

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
Reused as-is (added 2026-09-14) for the Output Panel's Output/Settings tab switcher — same
container, same active/inactive treatment, just two fixed tabs instead of a chart's time-range
options. No new tab component was introduced.

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
               (**on a Data Story: text-xs text-gray-400** — gray-500 measured 3.04:1 on the
               story surface, under 4.5:1; see Chart accessibility standard. The Welcome is
               unchanged in v2.1.)
count:         exactly one per view
```

**Stat Tile**
```
value:         text-xl font-semibold text-gray-100
label:         text-xs text-gray-500, below the value (on a Data Story: text-xs text-gray-400,
               as for the Hero Figure label above)
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
               fuchsia-600 · Engineer emerald-600 — revised 2026-09-26, see Accent
               palette) — the same three hues the trend
               chart already uses for the same categories; never a new hue.
               Segment order: Design → Engineering → Product Management (Chart
               accessibility standard, rule 6) so the two closest hues never touch.
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
               encoding, not a new colour. **Superseded for skill demand specifically,
               2026-09-22** — that block now uses a real grouped bar chart (Charting
               library, below) with two named series instead of an opacity difference;
               this emphasis pattern remains valid for any future single-series list that
               needs it, just no longer the mechanism for that one block.
labels:        every row is directly labelled with its value (a short list, so this is
               not the "number on every point" anti-pattern); no axis
zero/empty:    a list with no data renders its section's "not enough data yet" line,
               never an empty track
```

### Charting library (added 2026-09-22 — `changes/2026-09-22-nivo-charting-library.md`)

**[Nivo](https://nivo.rocks/)** (MIT licensed) — added specifically to give data stories real
visual variety beyond hand-rolled divs, after "What we know about the market" was found to
repeat the Ranked bar list form three times plus three more hand-rolled year-on-year
comparisons. Not a replacement for the hand-built vocabulary above — `RankedBarList`, `Meter`,
`StoryBlock`, and the Category Share Bar stay exactly as they are; Nivo is reached for
specifically where a real chart (grouped/comparative series, more than one dimension at once)
says more than a ranked list can.

```
theme:         a single shared theme object (frontend/src/features/market-health/stories/
               nivoTheme.ts) maps every Nivo theme slot to this spec's own tokens — text
               gray-400, axis/grid lines gray-700/gray-800, tooltip surface gray-800 with a
               gray-700 border, legend text gray-400. No chart in this product renders with
               Nivo's own (light-theme) defaults, ever.
colour:        role-category charts key off the same three role accents (indigo-500 /
               fuchsia-600 / emerald-600 — revised 2026-09-26), by the stored role_category value, never the
               display label (changes/2026-09-22-role-category-display-relabel.md). A
               2-series comparison (e.g. must-have vs. nice-to-have, current vs. a year ago)
               uses one accent hue for the primary series and a muted gray-500 for the
               secondary — never two accent hues in the same chart, which would read as two
               different categorical dimensions at once. **Revised 2026-09-26: the muted
               series was gray-600; measured, it is 2.35:1 on gray-900 and 1.94:1 on gray-800
               (the surface stories render on) — below the 3:1 a meaningful mark needs. gray-500
               is 3.04:1 on gray-800 and 3.67:1 on gray-900, and separates from indigo-500
               cleanly (validator: ΔE 18.5). It is the floor, not a target — never go darker.**
loading:       every Nivo-based component is lazy-loaded (React.lazy + Suspense, a
               `h-40 animate-pulse bg-gray-800` fallback) — Nivo's own weight (~86KB
               gzipped, confirmed by a real build) must never load for a visitor who never
               opens a story that uses it. This is enforced per-component, not assumed;
               check a real production build's chunk output if a future chart's bundle
               impact needs verifying.
current uses:  Story 1's skill-demand block (grouped bar, must-have vs. nice-to-have) and
               its three year-on-year blocks (grouped bar, current vs. one year back); Story
               1's pay-transparency block, Story 2's contraction-vs-expansion block, and
               Story 4's scale block (all three: a 2-slice donut, added 2026-09-22 —
               `changes/2026-09-22-nivo-pie-charts.md`); Story 5's official-statistic
               year-on-year block and its two-series comparison (added 2026-09-24) — see
               design/market-health/data-stories.md.
```

**Meter vs. a 2-slice donut — the actual dividing line, not a style preference.** Meter stays
the right form for a **coverage/completion** percentage — "X% of Y have this property," where
the un-named remainder isn't itself a meaningful category worth naming (Story 3's "X of Y
tracked roles have salary data reported"). A donut (`SharePieChart`) is for a **real 2-category
partition** — the population genuinely splits into exactly these two named things, both worth
seeing at a glance (disclosed vs. undisclosed pay; contraction vs. expansion; outside vs.
inside the 3 tracked categories). Colour convention: one accent hue for the named/primary
slice, `gray-500` for its muted complement (was `gray-600` — see the 2026-09-26 revision in
Charting library, above) — same "one accent, one neutral" rule as the grouped
bar charts above — **except** where a real semantic colour already exists for both sides
(contraction/expansion reuses the World risk map's own `red-600`/`emerald-600`, never a
separate guess at new colours for the same real-world meaning).

### Chart accessibility standard (added 2026-09-26 — `changes/2026-09-26-data-story-chart-variety.md`)

Applies to **every chart, figure and list inside a Data Story**. Figures below were *measured*,
not assumed: WCAG contrast computed from the token hexes, categorical separation from the
`dataviz` skill's `validate_palette.js` (OKLab ΔE under simulated colour-vision deficiency).
**Reference surface: `gray-800`** — stories render inside the AI turn (`bg-gray-800`, see
Message bubbles). `gray-900` is only the page behind it, so the tighter `gray-800` numbers rule.
Re-run the measurements whenever a token in this section changes.

**Measured contrast** (WCAG ratio; text needs 4.5:1, a mark that carries meaning needs 3:1):

| Token | On `gray-800` (stories) | On `gray-900` (page) | Verdict |
|---|---|---|---|
| Text `gray-100` / `gray-300` | 13.3 / 10.0 | 16.1 / 12.0 | ✅ any text |
| Text `gray-400` | **5.78** | 6.99 | ✅ the **minimum** for any caption, qualifier, legend, label |
| Text `gray-500` | **3.04** | 3.67 | ❌ **retired for text on story surfaces** |
| Mark role accents `indigo-500` / `fuchsia-600` / `emerald-600` | 3.29 / **3.12** / 3.90 | 3.97 / 3.77 / 4.71 | ✅ (`fuchsia-600` is near the floor — never darker) |
| Mark `emerald-600` / `red-600` (semantic) | 3.90 / 3.04 | 4.71 / 3.67 | ✅ (`red-600` is at the floor) |
| Mark `gray-500` (muted series) | **3.04** | 3.67 | ✅ at the floor — the darkest allowed muted mark |
| Mark `gray-600` | 1.94 | 2.35 | ❌ was the muted series; **retired** |
| Fill `gray-700` | 1.42 | 1.72 | ❌ for any bar that carries a value (a *track* behind a value bar is decorative and exempt) |
| Text `gray-900` on treemap fill `indigo-400` | 5.95 | — | ✅ (`gray-900` on `indigo-500` is only 3.97 ❌; white on it 4.47 ❌) |

**Categorical separation** (validator, dark, surface `gray-800`/`gray-900`):
- `emerald-600` + `red-600` → **all checks pass** (the contraction/expansion pair — unchanged).
- `indigo-500` + `gray-500` (accent + muted series) → pass, ΔE 18.5.
- **Role accents `indigo-500` · `fuchsia-600` · `emerald-600` (all pairs) → all checks pass**;
  one **warning**: fuchsia ↔ indigo ΔE 6.5 under deuteranopia (the 6–8 floor band), legal only with
  the secondary encoding rules 5–6 below require. Normal-vision worst pair ΔE 18.6 (floor 15).
  *History:* the previous trio (`indigo-500` · `purple-500` · `emerald-500`) **failed** — Designer ↔
  Product Manager ΔE 0.9 under protanopia and 11.3 normal-vision — and was replaced 2026-09-26
  (`changes/2026-09-26-role-palette-accessibility.md`; see Accent palette).
- `fuchsia-600` vs the semantic colours: `red-600` ΔE 25.5, `amber-600` 32.2, `emerald-600` 37.9 —
  all clear the floor, so a Product Manager line can share a view with a rising/declining
  indicator. (`pink-500` was rejected: ΔE 14.5 from `red-600`.)

**Rules — every chart:**
1. **Text size.** All chart text is **12px minimum** (Story chart text, Typography). No `text-[10px]`.
2. **Text colour.** Small text (caption, qualifier, legend line, axis, value label, table cell,
   eyebrow, Hero/Stat label) is **`gray-400` or lighter**. `gray-500` is not used for text on a story.
3. **Marks.** A mark that carries meaning is **≥ 3:1** against `gray-800`. The muted comparator
   series is `gray-500`; ghost/"a year ago" bars are `gray-500`, never `gray-700`/`gray-600`.
4. **Text never wears the data colour.** Labels use text tokens; identity comes from the mark
   beside the label. Text placed *inside* a fill uses `gray-900` on light fills (`indigo-400`,
   `gray-400`) — never light text on `indigo-500`.
5. **Never colour alone.** Every colour-coded mark also has a direct text label, or a glyph
   (▲ ▼ –), or a shape cue (hollow vs. filled, dashed vs. solid, position either side of a zero
   line). A legend line names every colour, glyph and shape used (Data Legibility, below).
6. **The two closest role accents never touch.** `indigo-500` (Designer) and `fuchsia-600`
   (Product Manager) are the palette's one remaining warning (ΔE 6.5 under deuteranopia). They are
   never adjacent segments/bars and are always directly labelled by role name; in any stacked or
   side-by-side role chart the order is **Design → Engineering → Product Management**, so an
   `emerald` element always sits between them.
7. **Hit targets.** Every interactive mark has a hit area of **at least 24 × 24 CSS px** even when
   the visible mark is thinner (a 6px bar sits in a ≥ 32px-tall row that is the target).
8. **Keyboard.** Every chart is reachable by keyboard: one tab stop per chart, arrow keys move
   between marks, the focused mark shows a `focus-visible` outline (`outline-2 outline-indigo-400`,
   5.95:1) **and the tooltip's content** — hover-only information does not exist.
9. **Text alternative.** Each chart has (a) `role="img"` with a one-sentence `aria-label` that
   states what the chart shows, its unit and window; (b) a visible **"Show as table"** disclosure
   (`text-xs`, ≥ 24px target, collapsed by default) revealing a real `<table>` with a caption,
   column headers with units, and every value — the full-precision data the labels sample.
10. **Reflow & zoom.** A chart is 100% of its container, works from a 320px container up, never
    causes horizontal page scroll, and stays legible at 200% browser zoom (sizes in `rem`/px,
    never viewport units). Text is never rotated. Ordered columns switch to ordered horizontal
    bars below 480px so nine labels never collide.
11. **Motion.** None on data (unchanged); `prefers-reduced-motion` has nothing to turn off.
12. **Texture is not built in v1.** Direct labels + glyphs + shape cues are the non-colour channel;
    the dataviz skill's opt-in texture (CVD / print / forced-colors) stays a documented option only.

**How to verify (do not skip):** `node validate_palette.js "<hexes>" --mode dark --surface "#1f2937"`
(dataviz skill; run as an ES module) for categorical pairs, plus a WCAG ratio check for every
text/mark token used. Any FAIL blocks the change; a WARN is legal only with the labels/shape cues
above. Record the result in the change request.

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
   how-to-read  text-xs text-gray-400, mt-1              (added 2026-09-26 — ONE line, only for a
                                                           form a first-time reader can't decode
                                                           unaided: range chart, treemap, diverging
                                                           bars, stacked share bar. See "Chart
                                                           definition pattern", Data Legibility)
   legend    text-xs text-gray-400                       (names every colour, glyph and shape in
                                                           the visual; sits between how-to-read
                                                           and the visual — absent only when one
                                                           colour is on screen)
   visual    one element from the vocabulary below      (carries the point)
   table     "Show as table" disclosure, text-xs         (added 2026-09-26 — Chart accessibility
                                                           standard, rule 9)
   qualifier text-xs text-gray-400, mt-2                 (sample size / coverage caveat —
                                                           was gray-500; see Chart accessibility
                                                           standard)
   ```
   A block is separated from the next by `border-t border-gray-800 pt-4` — the same divider
   rhythm the reference story uses. The whole story is wrapped `space-y-5`. Subtitle and
   qualifier read differently on purpose: subtitle states **what the numbers are**, qualifier
   states **how much to trust them** — never merge the two into one line. (`gray-800` dividers
   are decorative separators, not data marks, so the contrast rule does not apply to them.)

**Visual vocabulary** — a block's `visual` is one of these, never free prose:

| Element | Use it for | Spec |
|---|---|---|
| **Ranked bar list** | a "top N" magnitude comparison (roles, skills, locations) | "Ranked bar list", above |
| **Hero Figure** | the single number the story leads with — **at most one per story** | "Hero Figure" (Entry-point components), above |
| **Stat Tile** | a supporting number beside/below the Hero Figure | "Stat Tile", above |
| **Meter** | one share as a part-to-whole bar (e.g. "6% of postings state a salary") | below |
| **Category Share Bar** | a part-to-whole split across the 3 tracked Role Categories | "Category Share Bar", above |
| **Time series** (was "Trend line", expanded 2026-09-26) | a value over time, where the block's data is genuinely a time series (≥ 12 points). Never for two points. | "Time series", below; compact variant: Chart Specification, `design/market-health/experience.md` |
| **Year-on-year comparison** | how a set of proportions shifted between the trailing 12 months and the 12 months a year earlier — one year back, never more | below |
| **Two-series comparison** (added 2026-09-24) | two separately-sourced sets of shares over the same categories — e.g. the roles this platform tracks vs. an official statistic — shown side by side, never as a difference | below |
| **World risk map** | a geographic "where" comparison across countries — a choropleth, not a ranked list | below |
| **Stacked share bar** (added 2026-09-26) | a part-to-whole split of a *few* categories (≤ 4), compared across two periods (this year over a year ago) | "Stacked share bar", below |
| **Ordered columns** (added 2026-09-26) | a distribution over an **ordered** scale (seniority ladder, business size) — the order is the meaning | "Ordered columns", below |
| **Diverging change bars** (added 2026-09-26) | *change* between two periods (up or down from zero), one row per category | "Diverging change bars", below |
| **Range chart** (added 2026-09-26) | the *spread* of a value (a distribution) per entity — e.g. salary 10th–90th percentile with the median | "Range chart", below |
| **Treemap** (added 2026-09-26) | a part-to-whole split of **many** categories (≈ 6–14) with long labels, where "how big a slice" matters more than exact rank | "Treemap", below |
| **Stat Tile pair** (added 2026-09-26) | exactly two shares that sum to 100% (e.g. individual contributor vs. management), where a chart would add nothing | "Stat Tile pair", below |

**Choose the form by the data's job** (added 2026-09-26) — the form follows the question, never
the other way round. Adapted from the `dataviz` skill's form heuristic:

| The reader must… | Use | Not |
|---|---|---|
| Rank a "top N" | Ranked bar list | Treemap, pie |
| See parts of one whole, many categories | Treemap | Ranked bars of shares |
| See parts of one whole, ≤ 4 categories, across two periods | Stacked share bar | Grouped bars, pie |
| See a distribution over an ordered scale | Ordered columns | Ranked bars (order is not rank) |
| See how much something rose or fell | Diverging change bars | Two grouped bars (the gap is the point) |
| See the spread of a value per entity | Range chart | Bars of the median from zero |
| See one ratio, or one coverage % | Meter | Pie of 2 slices |
| See a real 2-category partition worth naming | 2-slice donut | Meter |
| See two shares that sum to 100% | Stat Tile pair | Any chart |
| See one headline number | Hero Figure | A one-bar chart |
| Compare two sources over the same categories | Two-series comparison | A difference, score or ratio |
| Follow a value over time (≥ 12 points) | Time series | Bars for a smooth series; a line for two points |
| See "where" across countries | World risk map | Ranked bars |
| See two periods of one measure | Year-on-year comparison / Diverging change bars | A line (two points imply a trend) |

**Two-series comparison** (added 2026-09-24 — `changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md`,
Story 5's third movement). No new tokens — it reuses the Charting-library rule for a 2-series
chart (one accent hue for the primary series, `gray-500` for the secondary — was `gray-600`, revised
2026-09-26, see Chart accessibility standard):
```
form:     Nivo grouped horizontal bars (same component family as the year-on-year comparison),
          one row per category, two bars per row
series:   PRIMARY   the platform's own figure     indigo-500  — "the roles we track"
          SECONDARY the outside publisher's figure gray-500    — named for the publisher
          The publisher is the muted, reference series on purpose: the platform's own view is
          the thing being placed against it, and the muted bar reads as "the yardstick".
legend:   one line, always shown, above the chart, naming BOTH series in words with their
          denominators and dates — e.g. "Solid bar: roles we track — share of 1,240 UK-based
          roles, as of 24 Sep 2026. Lighter bar: UK vacancies — share of all vacancies, ONS
          estimate for Jun–Aug 2026." Colour is never the only signal (Data Legibility).
values:   both series are SHARES (%), never one share and one count — the only honest way to
          put two different-sized populations on one axis. Unit stated once in the subtitle.
tooltip:  names the row, then each series with its own source name and figure —
          "Information and communication — roles we track: 61% · ONS UK vacancies: 9%".
          No difference, ratio, or "over/under-represented" wording anywhere, including the tooltip.
last row: a row whose category has no honest counterpart on the other side (e.g. "Not placed in
          an industry group", platform side only) renders only the bar that exists, with an
          inline caption saying why — never a zero bar for the missing side.
qualifier: always the "not expected to match" line (data-stories.md, Story 5) — required, not
          optional, wherever this form is used.
```

**Year-on-year comparison for an official statistic** (added 2026-09-24): identical anatomy to
the platform's own year-on-year comparison above — same ghost/solid bars, same legend line, same
glyph-plus-number delta — with two differences: the bars are **levels in thousands** rather than
shares, so the delta reads "▲ +6 thousand" / "▼ −12 thousand" (never "pp"); and the two windows
are the publisher's own same-length periods a year apart (e.g. "Jun–Aug 2026" and "Jun–Aug
2025"), stated in words under the heading.

**New forms (added 2026-09-26 — `changes/2026-09-26-data-story-chart-variety.md`).** All seven
follow the Chart accessibility standard above (12px text, ≥ 3:1 marks, direct labels + glyph/shape
cues, one tab stop, "Show as table", a one-sentence text summary) and add **no new accent hue**.
Only the three role accents, `indigo-400/500`, `gray-400/500`, and the existing red/emerald semantic
pair appear. Each is used **only** where the data's job is the one named in the table above.

**Stacked share bar** — a few categories' shares, this year over a year ago:
```
form:      two horizontal 100% stacked bars, "This year" above "A year ago", one shared 0–100% axis
           (ticks 0/25/50/75/100%, 12px). Bars ≤ 24px thick, 2px surface gap between segments,
           4px rounded outer ends only, square where segments meet.
segments:  the three role accents, by stored role_category value, in the FIXED order
           Design (indigo-500) → Engineering (emerald-600) → Product Management (fuchsia-600) —
           the order keeps the two colours that fail together apart (Chart accessibility
           standard, rule 6). Never a fourth segment, never `other`/`unknown` (they are coverage,
           not a share — same rule as the year-on-year role-mix block).
labels:    role name + share ("Design 48%") ABOVE each segment of the "This year" bar, text-xs
           gray-300 — never inside the fill. A segment narrower than 8% drops its inline label;
           the legend line, tooltip and table still carry it.
change:    one text-xs gray-400 line under the bars, one item per role: "Design ▲ +2 pp · Engineering
           ▼ −1 pp · Product Management ▼ −1 pp" — glyph + sign + "pp" spelled out.
legend:    one line naming the two bars and the periods in words: "Top bar: this year (Sep 2026 –
           Sep 2027). Bottom bar: the year before." The role colours need no separate legend —
           they are named on the bar.
unit:      "% of postings with a role area", denominator in the qualifier.
current-only: before a prior year exists, the block shows the "comparison starts {Month Year}" line
           (see "No prior window yet"). Whether a single current bar may also be drawn is decided
           in the experience spec — a lone current bar would repeat the Welcome's Category Share Bar
           (composition rule "No current-snapshot duplication").
```

**Ordered columns** — a distribution over an ordered scale:
```
form:      vertical columns, one per step of the scale, left → right = low → high (junior → senior;
           1–9 → 2,500+ employees). The order is the data's own ladder — NEVER sorted by value.
column:    ≤ 24px wide, 4px rounded top, square at a zero baseline (a column always starts at 0).
           Fill indigo-500. One hue: position carries the order, so no colour ramp.
compare:   the year-on-year variant adds a second, narrower column beside each — muted gray-500 = a
           year ago, indigo-500 = now (pair ≤ 2×20px + 2px gap). Legend: "Solid column: now.
           Lighter column: a year ago."
values:    the value on the cap, text-xs gray-300 tabular-nums ("14%"), never inside the column. In
           the comparison variant only the "now" column is labelled; the year-ago value is in the
           tooltip and the table. Step labels sit under each column, horizontal, text-xs gray-300,
           never rotated.
axis:      none when every column is directly labelled; otherwise 0-based hairline gridlines.
reflow:    below a 480px container the columns become ordered horizontal bars (same order, top →
           bottom) so no step label ever collides or rotates.
unit:      once, in the subtitle ("% of postings", "thousands of vacancies").
```

**Diverging change bars** — how much something rose or fell:
```
form:      horizontal bars either side of a vertical zero line, one row per category, rows ≥ 32px
           tall (the hit area), bar ≤ 20px thick.
colour:    ONE hue, indigo-500, in both directions. Direction is carried by which side of the line
           the bar sits, the ▲/▼ glyph and the signed number — NOT by red/emerald: those would say
           "good" and "bad", and this product's own copy says a drop in vacancies "can mean slower
           hiring or roles being filled faster". (Two-hue diverging is for a polarity that means
           something; here it is only direction.)
zero line: 1px gray-400, labelled "No change" above the chart.
scale:     symmetric around zero (the same maximum on both sides) so an equal rise and fall are
           equal length; tick labels signed ("−20", "0", "+20"), unit in the subtitle.
labels:    category at left (text-sm gray-300); the change at the bar tip: "▲ +6 thousand" /
           "▼ −12 thousand" / "– no change" — glyph + sign + unit spelled out, never colour alone.
order:     by signed change, largest rise at the top → largest fall at the bottom.
legend:    one line stating what position means: "Right of the line: more vacancies than a year
           earlier. Left: fewer." Both periods stated in words under the heading (the
           official-statistic year-on-year rule).
tooltip:   category, both period values, then the change — the levels live here and in the table,
           never as a second bar.
zero:      a value of exactly 0 draws a hairline tick on the zero line, not nothing.
```

**Range chart** — the spread of a value per entity (salary percentiles):
```
form:      horizontal, one row per entity (≥ 40px tall), ordered by median, high → low, one shared
           value axis at the bottom (12px ticks, currency). The axis need NOT start at zero —
           position encodes the value and there is no bar length to distort — but its starting
           value is printed on the axis and named in the how-to-read line ("The scale starts at
           £40,000"). This is exactly why it replaces bars-from-zero for pay.
marks:     whisker  2px line, 10th → 90th percentile, indigo-500
           band     h-3 rounded rect, 25th → 75th percentile, indigo-500 (sits over the whisker)
           median   dot r=5 (10px), fill gray-100, 2px gray-800 surface ring
row label: entity name at left (text-sm gray-300) with the sample size beneath (text-xs gray-400,
           "n = 412") on EVERY row. The median in full at the row's right end (text-xs gray-300,
           "£62,000"). The other percentile values are in the tooltip and the table, never on the marks.
legend:    always shown, three glyph keys: "Line: the middle 80% of advertised salaries (10th to
           90th percentile). Bar: the middle 50% (25th to 75th). Dot: the median." — worded from the
           single shared definition (Data Legibility — Chart definition pattern).
small n:   a row whose sample is below the threshold set in the experience spec draws a HOLLOW
           median dot (stroke gray-100, no fill) and its row label gains "small sample"; the legend
           adds "Hollow dot: fewer than {N} salaries — indicative only" only when such a row exists.
missing:   a row with no P10/P90 draws the median dot alone with the caption "range not reported" —
           never an invented, interpolated or zero-filled range.
unit:      currency and period from the record ("£, per year"), in the subtitle. Permanent (annual)
           and contract (day rate) are never on one axis.
```

**Treemap** — parts of one whole across many categories. **Revised 2026-09-27**
(`changes/2026-09-27-treemap-legibility.md`) — adds sequential shading by volume and fixes the
gap, after the first shipped version (all-one-fill, 1px unset-background gap) proved unreadable
in practice: adjacent similarly-sized tiles were indistinguishable at a glance.
```
form:      squarified treemap, tile area ∝ count, largest top-left, container ≈ 2:1 and ≥ 240px
           tall. Used for ≈ 6–14 categories; beyond that or below, use a Ranked bar list.
tile:      sequential indigo shade by volume — a secondary cue reinforcing what area already
           shows, never the only one. 4 discrete steps, binned by each named tile's RANK among
           the story's own named tiles (quartile of position in the sorted list, not an absolute
           share threshold — so the ramp works the same regardless of how concentrated or spread
           the data is): indigo-600 (lowest quartile) → indigo-400 → indigo-300 → indigo-200
           (highest quartile). Dark-mode sequential ramps anchor opposite light mode — bright
           reads as "more" against a dark surface, dim recedes toward it — so brightness rises
           with volume, not falls. indigo-500 is never used: measured 3.97:1 (gray-900 text) /
           4.06:1 (gray-100 text) on this ramp, both under the 4.5:1 floor for 12px text — a dead
           zone no text colour clears. indigo-700 is also never used: 1.86:1 against the gray-800
           gap (below the ordinal ramp's light-end-of-scale 2:1 floor, i.e. it blends into the
           gap), and only ΔL 0.054 from indigo-600 (below the 0.06 step-visibility floor, i.e.
           indistinguishable from its neighbour). Validated: `node validate_palette.js
           "#4f46e5,#818cf8,#a5b4fc,#c7d2fe" --ordinal --mode dark --surface "#1f2937"` — all
           checks pass.
gap:       2px gray-800, rendered as a real background colour on the treemap's own container —
           never left to whatever sits behind it. (The original implementation padded 1px into
           an unset ambient background, which on this product's near-black page surface read as
           no gap at all — the defect this revision fixes.) 4px radius.
text:      name (text-xs font-semibold) then "1,240 · 18%" (text-xs), INSIDE the tile. gray-900
           on indigo-400/300/200 (5.95:1 or better); gray-100 on indigo-600 (5.71:1) — the one
           flip point in the ramp, always at the dimmest, lowest-volume step.
not-a-name: tiles that are not one named category are HOLLOW — no fill, 1px outline, gray-300 text:
           "Function not stated" (a real category, solid gray-400 outline) and "{N} smaller
           functions" (an aggregate of tiles too small to label, DASHED gray-400 outline). Never a
           grey fill — beside the sequential ramp it fails the normal-vision floor at the range
           this product measured (ΔE 14.4 < 15 against indigo-400). `unknown`
           is never folded into the aggregate tile.
min tile:  a tile that cannot fit its name at 12px with 8px padding merges into the aggregate tile;
           the threshold is set in the experience spec; the merged members are all in the table.
legend:    one line, now that colour carries meaning too (Data Legibility, Rule 10): "Tile size
           and shade both show each {thing}'s share of {population} — larger, brighter tiles hold
           more. Outlined tiles are not a single named {thing}."
focus:     arrow keys visit tiles in descending size; tooltip = name, count, share.
```

**Stat Tile pair** — exactly two shares that sum to 100%:
```
layout:    two Stat Tiles side by side (`grid grid-cols-2 gap-3`; stacked below 360px), each
           `rounded-lg border border-gray-700 bg-gray-800/60 p-4`.
tile:      label (text-xs gray-400, "Individual-contributor roles") → value (text-2xl font-semibold
           gray-100, "84%") → change line (text-xs gray-400, "▲ +2 pp vs. a year ago" / "▼ −2 pp" /
           "– no change").
colour:    none — tiles are neutral, so there is nothing to put in a legend. Direction is glyph +
           sign + words.
sum:       the two values sum to 100% of postings with a stated {dimension}; stated in the qualifier.
current-only: the change line is replaced by muted "Comparison starts {Month Year}".
```

**Time series** (was "Trend line"; expanded 2026-09-26, drawing on the Story 5 "Tech and
communications" block specified in `changes/2026-09-26-story-5-tech-lens.md`):
```
when:      ≥ 12 contiguous points of a genuine time series. Never two points (a line would imply a
           trend that does not exist — use Diverging change bars / Year-on-year comparison).
lines:     primary series indigo-500 solid, 2px, round join/cap. A comparator series is gray-500
           and DASHED (`4 3`), 2px — so colour is never the only cue. No markers on every point.
axis:      ONE y axis, ever. Two measures of different scale are INDEXED to a stated common base
           (base period = 100), named in the subtitle AND the axis title ("Index (Jun–Aug 2019 =
           100)"), with the 100 gridline labelled; real levels live in the tooltip and table.
           Never dual-axis. x ticks every 5 years (every 10 on a narrow panel), 12px.
markers:   data-derived only — the primary series' PEAK and its LATEST point, each ≥ 8px with a 2px
           surface ring, labelled with period + value. The latest point is HOLLOW when the
           publisher flags it provisional; the legend adds "Hollow point: first estimate, may be
           revised" only then.
labels:    direct end labels at each line's right end (name + latest value); on a narrow panel they
           become a legend line with a 16px solid or dashed key.
annotations: none. No event or recession shading, no causal note — a cause is not in the data, so
           it is never asserted. Only data-derived markers.
gaps:      a missing period breaks the line; never interpolate.
keyboard:  ONE tab stop; ←/→ step one period, Home/End jump to first/latest; the focus marker and
           the tooltip's content are announced (`aria-live="polite"`).
summary:   one visible templated sentence under the chart, facts only, no verdict.
table:     "Show as table" disclosure, collapsed; the experience spec sets the row granularity.
```

**World risk map** (added 2026-09-13 — `changes/2026-09-13-employment-risk-world-map.md`; **unchanged in v2.1**):
```
library:  react-simple-maps (ComposableMap/Geographies/Geography) over a world-atlas
          countries-50m topology — the 50m resolution, not the more common 110m, because the
          110m file was found to drop small/island nations (Singapore, Malta) that appear in
          this product's real data; verified directly against the topology file, not assumed.
          Served as a static asset (`public/world-countries-50m.json`), fetched at runtime
          only when this story opens — not imported as a JS module, which was tried first and
          found to grow the app's main bundle by ~750KB for every visitor regardless of
          whether they ever open this story
map:      flat SVG country shapes, no basemap tiles/imagery — the question is "which country,
          how much," not street-level geography, so tiles would be noise, not signal
fill:     one colour per country, by NET direction (expansion total minus contraction total,
          by jobs reported affected) — reuses the existing semantic tokens, no new accent hue:
            net > 0 (more expansion)     emerald-600, opacity scaled to magnitude (min ~30%,
                                          max 100%, relative to the largest |net| on the map)
            net < 0 (more contraction)   red-600, same opacity scaling
            no reported events           gray-800 (neutral — "no data," never implied calm,
                                          same rule as the direction-split block's zero-events
                                          state)
borders:  gray-700, thin — countries read as distinct shapes without competing with the fill
legend:   one line, always shown, pairing each colour with its meaning — e.g. "● More reported
          hiring   ● More reported layoffs   ● No reported events in this window" — required
          per Data Legibility (below): colour is never the only signal
hover:    a small dark tooltip (gray-800, border-gray-700, same Surface treatment as elsewhere)
          following the cursor, naming the country and both totals — "Germany — 620 jobs
          reported affected by contraction, 210 by expansion" — never just the net figure,
          since net alone can hide real activity in both directions
zero/empty: a country with no reported events in the window is still drawn (neutral fill), never
          omitted from the map — omitting it would read as "not part of the world," not "no
          data"
```

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
          text-xs text-gray-400 (e.g. "Sep 2026 – Sep 2027, compared with the year before")
legend:   one line naming what the two bar colours mean — text-xs text-gray-400, directly
          below the windows line — e.g. "Lighter bar: a year ago. Solid bar: now." Required
          whenever the comparison is available (two colours are on screen); omitted in the
          "no prior window yet" state below, where only one colour appears. Added 2026-09-11
          (`changes/2026-09-11-data-legibility-market-health.md`) — found missing during a
          data-legibility audit: the two-colour encoding was documented here but never
          explained to the end user.
row:      one per category, ordered by current-window share, descending. Each row:
            label   text-sm text-gray-300, left, truncate
            bars    a shared track (bg-gray-800, rounded, h-1.5). Two fills on it
                    (**this hand-rolled description is superseded by the Nivo comparison
                    chart since 2026-09-22; where it is still referred to, the prior-year fill
                    is `gray-500`, never `gray-700` — 1.42:1, see Chart accessibility
                    standard**):
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
`text-xs text-gray-400` — "Year-on-year comparison starts {Month Year}. Tracking since {date}."
This is the block's state at ship time and for the product's first year; it must read as
"coming soon", not "broken". **Each of the new comparison forms defines its own current-only
state** (Ordered columns: the columns without the year-ago column; Stat Tile pair: the change line
replaced by this same muted line; Stacked share bar: this line, see its spec) — the state is
designed, not left as whatever the chart happens to draw with one series.

**Combination rule** (strengthened 2026-09-26 — `changes/2026-09-26-data-story-chart-variety.md`).
1. At least **two distinct visual forms** across a story (3+ preferred) — a story that is five
   ranked bar lists in a row is under-composed.
2. **No form repeats within a story** unless the repeated blocks are each genuinely a *ranking*
   question (Ranked bar list is the only form allowed to repeat). Even then: **at most two ranked
   lists in one story, never adjacent**, and the experience spec records a one-line reason. Any
   other repeat (two donuts, two treemaps, two columns charts in one story) is a violation.
   **Recorded exception — Story 2 (employment risk):** it predates this rule and has two adjacent
   ranked lists (companies, sectors). It is deliberately left unchanged at the stakeholder's
   direction (2026-09-26: "leave the work events … that one is very nice with the map and is an
   example of variety") — its map and donut already give it the variety this rule is after.
3. **Match the form to the data's job** using the "Choose the form by the data's job" table above.
   A form chosen for variety that the data does not support (a scatter of 8 points, a treemap of
   3 categories, a line through 2 points, a pie of 5 slices) is worse than a repeat — pick the
   honest form, and record any accepted repeat rather than bend the data.
4. **Sample size and denominator are part of the chart**, not a footnote hidden elsewhere — a chart
   whose validity depends on n shows n (Range chart: n on every row).

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
- A form repeated within a story other than a Ranked bar list (Combination rule, above), or a
  form picked for variety that the data does not support.
- A chart with no "Show as table" disclosure, no one-sentence text alternative, or no keyboard
  access (Chart accessibility standard, rules 8–9).

**Which form each story block uses now** is decided per block in
`design/market-health/data-stories.md` (revised for v2.1 in the same change — see
`changes/2026-09-26-data-story-chart-variety.md`); the list below is the *original* reference
implementation, kept for history.

**Reference implementation (original):** `market-data-briefing` (`DataStoryMessage.tsx`), two labelled
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

### Output Panel — Settings tab (added 2026-09-14 — `changes/2026-09-13-mcp-ai-agent-access.md`)

Everything here fits the Output Panel's fixed 320px width — narrower than any surface this
product has designed for before. Every element below is vertically stacked; nothing is
side-by-side.

**Settings tab header:**
```
title:         "Connect your AI" — Section-heading scale (text-sm font-medium), gray-100
                (not Conversation-title scale — that would crowd a 320px column)
explanation:   one line, Caption scale, gray-400
MCP endpoint:  Monospace scale, gray-100, bg-gray-800 border border-gray-700 rounded-lg,
               py-2 px-3, truncated with text-overflow: ellipsis (the value never force-wraps
               or overflows the panel width) + an inline "Copy" ghost/text action, right-aligned
per-client
instructions:  collapsed by default, one row per client (Claude / ChatGPT / Gemini CLI / other),
               Body scale gray-300; expands inline on click using the same height transition as
               the Reasoning Panel (`duration-200`)
```

**Connected Assistant card** (one per connection, stacked with `gap-3` between cards):
```
container:     bg-gray-800, border border-gray-700, rounded-lg (same Surface as everywhere
               else), p-3 (tighter than the standard p-4 — the column is narrower)
client row:    icon (16px) + client name, Section-heading scale, gray-100
timestamp:     "Connected {relative time}" — Caption scale, gray-400, directly below the
               client row
scope chips:   Filter-chip pattern (existing), wrapped onto multiple lines as needed
               (flex-wrap, gap-1.5) — never truncated or scrolled horizontally; always
               plain language, never a raw scope identifier (e.g. "Can read job market
               data", never "jobs.read" — see Data Legibility, below)
plan badge:    Status badge / pill pattern (existing), placed on its own line below the
               scope chips — see the Plan tier mapping, below
revoke:        Ghost/text action, "Revoke", right-aligned on its own row at the card's
               bottom edge; on click, replaces itself inline with "Revoke access? [Yes] [No]"
               at the same position — no modal, matching Principle 5's direct-manipulation bar
```

**Plan tier badge** — new mapping onto the existing Status badge / pill pattern, no new colours:

| Plan tier | Semantic colour | Label |
|---|---|---|
| Free | `amber` (Stable / neutral) | "Free" |
| Premium | `emerald` (Rising / positive) | "Premium" |

Free is amber, not a "problem" colour — it is a neutral state, the same logic that already
gives `unknown` and "Pending" the amber treatment elsewhere in this document.

**Empty State** (zero connections): same Surface treatment as a card, but centred text instead
of the structure above — Body scale, gray-300, explaining what connecting does, with the MCP
endpoint and instructions still shown above it (per the experience spec, the endpoint/
instructions block is never hidden, connected or not).

### OAuth consent screen (added 2026-09-14 — same change)

Rendered when an external AI client initiates the connection — not part of the three-column
layout, no Task Panel, no Output Panel, no TopBar. May be the first thing a visitor ever sees on
this platform, so it must be legible with zero assumed context.

```
background:    gray-900 (Page background — same as everywhere else, no special "auth" theme)
container:     centred, max-w-[420px], bg-gray-800 Surface, border border-gray-700,
               rounded-lg, p-6
requester:     client icon + name, Section-heading scale, gray-100, top of the card
               ("Claude is requesting access")
scope
checklist:     one row per requested scope, plain language (same phrasing as the Connected
               Assistant card's scope chips), a small checkmark glyph (gray-400) before each —
               Body scale, gray-300
actions:       "Allow" — Primary button (existing), full-width
               "Cancel" — Ghost/text action, centred, below Allow
```

No accent colour is introduced for this screen — it uses the same dark surfaces, type scale,
and button styles as the rest of the product, so a user recognises it as this platform even on
a first visit.

### Task Panel Footer & Feedback Panel (added 2026-09-23 — `changes/2026-09-23-user-feedback-mechanism.md`)

**Task Panel Footer entry ("Give Feedback"):**
```
container:     no background at rest; matches other Task Panel item rows
divider:       1px border-gray-800 above the Footer, separating it from the task list
icon + label:  16px icon + "Give Feedback", text-sm gray-400 at rest, gray-100 on hover
               (same treatment as an inactive Task Panel item — it must not look more or
               less important than a Task)
```

**Feedback Panel (overlay):**
```
backdrop:      bg-gray-900/70, covers the full viewport, click-to-dismiss
container:     centred, max-w-[420px], bg-gray-800 Surface, border border-gray-700,
               rounded-lg, p-6 — same recipe as the OAuth consent screen's card, above
title:         "How satisfied are you with this platform?" — Section-heading scale
               (text-sm font-medium), gray-100
rating control: 5 equal-width buttons in a row, gap-2, each rounded-md border
               border-gray-700; unselected = gray-800 background, gray-400 text;
               selected = emerald-600 background, white text (same "positive/selected"
               semantic as the Complete/success status colour, never a new hue)
rating labels: "Not satisfied" (left, below button 1) / "Very satisfied" (right, below
               button 5) — Caption scale, gray-500
comment label: "Anything you'd like to tell us? (optional)" — Body scale, gray-300
comment field: Inputs pattern (existing), `rows=3`, resizes vertically only
actions:       "Submit" — Primary button (existing), right-aligned, disabled (gray-700
               background, gray-500 text, no hover) until a rating is selected
               close icon — top-right corner of the card, Ghost/text action treatment
confirmation:  replaces the form in place (not a second overlay) — a centred checkmark
               glyph (emerald-400) + "Thanks — that helps us improve the platform." at
               Body scale gray-300, auto-dismissing per the experience spec's timing
```

No new accent colour: the rating control's selected state reuses `emerald-600`/`emerald-400`,
the same "positive" semantic already used for the Complete/success status badge, the
contraction/expansion donut's expansion slice, and the thumbs-up state below — never a
purpose-built "feedback" hue.

### Data Story — Feedback reaction (added 2026-09-23 — same change)

Chrome below every Data Story's last block, per `design/market-health/data-stories.md` —
Feedback reaction. Not a `StoryBlock` — no heading, no subtitle slot, sits outside the
block-anatomy rhythm entirely.

```
label:         "Was this useful?" — Caption scale, gray-400 (was gray-500 — 3.04:1 on the story
               surface, under 4.5:1; revised 2026-09-26, Chart accessibility standard), centred
               above the two buttons
buttons:       two icon buttons (thumbs up / thumbs down), 32px square, rounded-md,
               border border-gray-700, gray-400 icon at rest, gray-100 on hover
selected up:   emerald-600 background, white icon (same positive semantic as the
               Feedback Panel's rating control, above)
selected down: gray-600 background, white icon — a neutral "acknowledged" treatment,
               never red/amber (the semantic-colour table's negative colours are
               reserved for platform states like "Failed"; a user's own negative
               reaction to a story is not a system error)
comment reveal: on thumbs down, an Inputs-pattern text field (`rows=2`) fades/expands in
               beneath the buttons using the same height-transition recipe as the
               Reasoning Panel (`duration-200`) — never a layout jump
comment actions: small "Submit" (Ghost/text action) + "Dismiss" (Ghost/text action),
               right-aligned below the comment field
```

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
- **Added 2026-09-26** — Currency: symbol + full figure with thousands separators ("£62,000"), the
  period named once in the subtitle ("per year"); axis ticks may compact to "£60k" because the
  table view and tooltip carry the full figure. Levels published in thousands: "▲ +6 thousand"
  (the word, not a bare "k", in a change label). A percentage-point change is `pp` (above). An
  indexed value: "Index (Jun–Aug 2019 = 100)" — the base is always named where the index is used.
  A sample size: "n = 412" (or "based on 412 salaries" in prose). A range: "£46,250 to £78,000",
  never "£46–78k" in prose.

### Chart definition pattern (added 2026-09-26)

Every data point a chart shows is *defined once*, in plain words, at the place a reader meets it —
never assumed. Three parts:
1. **Subtitle** — what is measured, its unit, its window (already required, above).
2. **How-to-read line** — one sentence, **only** for a form a first-time reader cannot decode
   unaided: Range chart ("Each bar spans the middle 80% of advertised salaries; the dot is the
   median. The scale starts at £40,000."), Treemap ("Tile size shows each function's share…"),
   Diverging change bars (the position-of-bar sentence), Stacked share bar. Ranked bars, Hero
   Figures, Meters and Stat Tiles need none.
3. **Term definitions** — a term of art ("median", "percentile", "size of business", "share of
   postings") carries its definition in the how-to-read line or the subtitle the first time it
   appears in a block — the Reasoning Panel is for *how it was computed*, not for what the words mean.

**One source of truth, shared with the MCP tools.** The wording that defines a data point (what
P10–P90 means, what "business size" means, what a "share of postings" is measured over) is
written **once in the backend** and used both by the story's subtitle/how-to-read/qualifier and by
the corresponding MCP tool's `meta`, so a person reading a story and an external AI describing
the same number use the same words (`backend/specs/market-health/api.md` and
`backend/specs/mcp-access/api.md` decide the mechanism in the same change). A definition that
exists only in frontend copy is a defect.

### Colour & shape legends
Colour or shape carrying meaning is always paired with a text label — this product's existing
"Colour as the sole encoding" rule (What this rules out, below) already required this; treat
it as covering every new use, not only the ones enumerated when that rule was written (trend
arrows, chart lines, status tags). Concretely: a semantic colour states its direction in a
caption or subtitle at least once per view; an opacity/shape distinction (e.g. `RankedBarList`'s
`emphasis` — full opacity vs. ~70%) gets an inline caption naming what the two states mean
(e.g. "Solid bars are must-have mentions."); `YearOnYearBars`'s two bar colours get a legend
line stating which is which (Year-on-year comparison, above). The Plan tier badge's colour
(added 2026-09-14) is always paired with its text label ("Free"/"Premium") per the Status badge
/ pill pattern — never colour alone.

**Shapes and glyphs need a key too (added 2026-09-26).** Every non-colour cue a chart relies on is
named in its legend line, in words: position either side of a zero line ("Right of the line: more
vacancies than a year earlier"), a hollow vs. filled dot ("Hollow dot: fewer than N salaries"), a
dashed vs. solid line ("Dashed line: all industries"), an outlined vs. filled tile ("Outlined
tiles are not a single named function"), and the ▲ ▼ – glyphs (always paired with a signed number
and the unit, never bare). A legend line appears only for cues actually on screen — no key for a
state that is not showing — and a chart with a single colour and no shape cue needs none.

### Plain language over raw identifiers (added 2026-09-14)
Any backend identifier a human would otherwise see verbatim — a scope name (`jobs.read`), an
enum value, an internal code — is translated to a plain-language label before it reaches this
product's UI. The Connected Assistant card's scope chips ("Can read job market data") are the
first instance of this rule; it applies to any future surface that would otherwise expose a raw
identifier to a person. This mirrors `design/foundations.md`'s Principle 9 (Curated Access,
Never Raw) applied to this platform's own UI, not only to what an external AI agent receives.

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
- **More than three accent colours.** The three role-category colours (indigo, fuchsia, emerald)
  are the only accents in the product. Do not introduce additional accent colours for new
  features without updating this spec.
- **Decorative motion.** Every animation must have a functional reason (loading, state change,
  expand/collapse). No animations for visual interest.
- **Dense or compact layouts that sacrifice readability.** The user is processing data under
  stress. Generous line-height and padding are not optional.
- **Chart text under 12px, small text in `gray-500`, or a meaningful mark below 3:1** (added
  2026-09-26 — Chart accessibility standard). `gray-600` and `gray-700` are never a data mark.
- **Indigo (Designer) and fuchsia (Product Manager) touching in a chart, or told apart by colour
  alone** (added 2026-09-26) — even after the palette fix they are the closest pair (ΔE 6.5 under
  deuteranopia); they always carry a direct label and never sit side by side.
- **A bar whose baseline is not zero, and a "line through two points"** (added 2026-09-26). A
  value bar/column always starts at 0; a range/dot plot may not, and says where it starts. Two
  periods are a comparison, never a trend line.
- **Two y axes, or a pie/donut of more than two slices** (added 2026-09-26) — index to a common
  base, facet, or use a different form.
- **A chart chosen for variety the data cannot support** (added 2026-09-26) — e.g. a scatter of
  eight points, a treemap of three categories. Variety comes from matching the form to the job.
- **A raw backend identifier shown directly to a user** (added 2026-09-14) — a scope name like
  `jobs.read`, an enum value, an internal code. Always translate to plain language first (the
  Connected Assistant card's scope chips are the reference case).
- **A settings surface forced into a modal, a separate route, or a new top-level navigation
  element when it fits an existing zone** (added 2026-09-14) — the Output Panel's Settings tab
  reused the panel's own pre-existing "outputs and settings" definition rather than inventing a
  new layout element; the same judgement applies to whatever account-level surface comes next.
