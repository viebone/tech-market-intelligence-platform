---
id: market-health
outcome: understand-market-health-before-searching
directive: low
status: ready
created: 2026-06-13
updated: 2026-09-06
---

# Market Health — Experience Spec

## Outcome this serves

See: `outcomes/understand-market-health-before-searching.md`

## Data stories

The curated instant-answer layer is documented separately in
`design/market-health/data-stories.md`. A data story is a predefined question with a fixed
answer structure and live platform-owned data, resolved with no model call. The **story
catalogue** is open-ended and expected to grow — each new story is a catalogue entry with its
own Task Panel item, added without changing this experience spec. "What we know about the
market" (answering "What do we currently know about the tech job market?") is the catalogue's
first example, not its ceiling; future entries can cover narrower questions the same way (see
`design/market-health/data-stories.md` — Future catalogue direction).

A story is **chart-first** and shows only what the "About this platform" welcome does not —
the welcome carries the data *inventory* (how much data, how many companies, since when, the
role-category split); a story carries the *substance* (the actual roles, skills, pay
transparency, locations). No figure appears in both. See
`design/market-health/data-stories.md` — Visible answer shape, and `design/visual-design.md`
— Ranked bar list (revised 2026-09-06 —
`changes/2026-09-06-market-story-visual-and-dedup.md`).

Task Panel order, front to back:

1. **"About this platform"** — a pinned welcome/orientation task, always first, always the
   default selection on first load. Not itself a member of the story catalogue — see Opening
   Welcome, below.
2. **The story catalogue**, in the order `design/market-health/data-stories.md` defines. Grows
   over time; this spec does not enumerate its members.
3. **"Tech market hiring status"** — pinned last, the trend-chart conversation.

Added 2026-09-04 — `changes/2026-09-04-about-this-platform-welcome.md`.

---

## Opening Welcome

**"About this platform"** is the first task in the Task Panel and is selected by default on
first load. Its job is orientation, not analysis: a first-time visitor should leave knowing
what the platform is, roughly what data backs it, and what kinds of questions it can already
answer instantly. It is structured like a data story — fixed layout, live owned-data figures,
no model call — but it is not itself a catalogue entry: it is the pinned front door that
points *into* the catalogue and the conversation, and it must keep working exactly as
specified no matter how many stories the catalogue holds.

### Structure (revised 2026-09-04 — `changes/2026-09-04-welcome-visual-data-points.md`)

Landing-page anatomy — hero, proof, call to action — not a paragraph. This is deliberately
distinct from every other AI-turn message in the product, because this one thing is the
entry point; no other data story adopts this treatment. Section order and roles are fixed;
the content within them is live or catalogue-driven, not hand-written per story.

1. **Hero** — a small eyebrow label, one bold headline naming the platform's purpose, and one
   supporting subhead sentence. Fixed copy, identical on every visit, never lists individual
   stories or features by name.
2. **Proof** — the live data, read at a glance rather than parsed from a sentence:
   - One **Hero Figure**: total job openings tracked. The single number this view leads with.
   - Two supporting **Stat Tiles**: companies tracked, and collection start date.
   - A **Category Share Bar**: every currently tracked Role Category with its share of
     classified postings, directly labelled. Replaces the old single "largest category"
     sentence with the real breakdown.
   - One fixed coverage-limit sentence and one fixed sentence naming which signals exist
     (skills, pay where disclosed, location where normalized).
   This section describes the platform's *data*, not its catalogue of questions — it does not
   change shape as stories are added or removed.
3. **Call to action** — a **live-rendered list of shortcuts, one per entry currently in the
   story catalogue**, each rendered as a Shortcut Card (see `design/visual-design.md`)
   showing that story's question, not a plain list item (see Interactions). Generated from
   `design/market-health/data-stories.md`'s catalogue: adding, removing, or reordering a story
   changes this list automatically, with no experience-spec or copy change required. Below the
   cards, one fixed, generic sentence points to open-ended conversation, followed by one fixed
   sentence naming what is out of scope today. Neither closing sentence names a specific story.

### Content

**Hero** (fixed):
> TECH MARKET INTELLIGENCE
>
> # Read the tech hiring market before you make a move.
>
> We track job openings, skills, and pay across company career pages — so you see where
> demand is heading, not guess.

**Proof** (live — see Data Contract below for the exact aggregates):
> **{N}** job openings tracked · **{M}** companies · tracking since **{month year}**
>
> {Category Share Bar: one segment per Role Category, e.g. Engineer / Product Manager /
> Designer, each labelled with its name and share.}
>
> This is a growing sample of the market, not every job out there — it reflects the companies
> and roles we follow today. For most of these we also have the skills employers mention, and
> pay figures where they're shared.

**Call to action** (structure fixed, card content is the live catalogue):
> Get an instant answer
> {one Shortcut Card per current catalogue entry — for example, today's only entry, "What do
> we currently know about the tech job market?"}
>
> You can also ask your own question about demand, skills, pay, or specific roles once you're
> in a conversation. We don't cover layoffs, company reviews, or application tracking.

### Data contract

Resolved by the pinned welcome (`design/market-health/data-stories.md` documents it alongside
the catalogue entries it draws from, even though it is not itself an entry). Owned-data only,
no LLM.

| Fact | Source | Qualifier |
|---|---|---|
| Total job openings (Hero Figure) | `count(distinct raw_postings.id)` | Unique postings captured, not total jobs in the market |
| Companies (Stat Tile) | `count(distinct raw_postings.company)` | Non-null normalized company values only |
| Collection start (Stat Tile) | `min(raw_postings.fetched_at)` | Observation window, not historical market coverage |
| Role breakdown (Category Share Bar) — revised 2026-09-04, was a single "headline fact" | Every currently tracked Role Category with `count(distinct rp.id)` of its classified postings | Whatever the taxonomy currently defines — not hardcoded to today's three; each segment states its own count, not just a rank |
| Signals available | Fixed statement — skills, pay (where disclosed), location (where normalized) | Presence only; no counts in this section |
| "What you can ask" cards | `design/market-health/data-stories.md` catalogue — each entry's `question` | One card per current entry; the section is omitted if the catalogue is ever empty |

### Honesty rules

Same as `design/market-health/data-stories.md`: every figure is current as of the response's
query time and carries a coverage qualifier; a figure with insufficient data says so rather
than guessing; nothing here is inferred from external sources.

### Relationship to the other tasks

"About this platform" does not replace any catalogue story or "Tech market hiring status" — it
is a pinned index that points into both. It stays first and default regardless of how many
stories exist. See Data stories, above, for full Task Panel ordering.

---

## Primary question this experience answers

> "How is the tech job market trending right now — and has it been getting better or worse?"

The opening view answers this one question, deliberately kept singular (Principle 3,
`design/foundations.md` — Exceptions Define the Experience: the fixed view should not grow
into a dashboard of every available metric). Two other questions this experience now
answers — **only through follow-up conversation, never in the fixed opening view** — are:

> "What salary should I expect for this role?" (**Compensation Signal**)
> "How is demand shifting for a more specific slice of the market — a sub-specialization,
> a seniority level, a track, a location?" (**Demand Signal**, enriched)
> "What does the market actually want from someone in this role — skills, education,
> languages — and what does that mean for me?" (**Requirements Signal**, added 2026-08-09)

All three are reached the same way the existing example already works ("Is User Experience
Designer or Product Designer more in demand right now?") — by asking, not by a new control
appearing on load. Requirements Signal introduces a genuinely new *kind* of answer, not just
a new data dimension: a **synthesis question** ("should I learn to code as a UX designer?")
asks for a judgment, not a lookup — see User Flow step 7b and Edge Cases, below, for how
that's handled honestly.

### What we want to achieve — a fluent, data-only conversation (added 2026-09-03, expanded 2026-09-06)

Goals that don't change the design of this experience — the page is still a conversation and
every answer is still grounded in the platform's own data:

1. **The most common questions should answer instantly.** Questions that get asked
   constantly — "which roles are growing?", "what do Backend Engineers earn?", "what skills
   do Product Designer postings ask for?" — should return an answer built directly from the
   platform's current data, without waiting on the assistant to compose it. The answer obeys
   every honesty rule in this spec (time window stated, proportions never absolutes,
   disclosed-vs-estimated salary never blended). This is a curated set that should keep
   growing over time, so more and more questions answer instantly. **The instant path must
   recognise a question asked in ordinary words** — "what skills are in demand for PMs?"
   should hit the same instant answer as "what skills do product manager roles ask for?",
   not fall through to the slow path on a rephrasing.

2. **Every answer comes only from the platform's data.** No web search, no model general
   knowledge, no blending. A question the data can't reach gets a plain "we don't track
   that" and a pointer to what it can answer — never an outside answer. This is a product
   rule; it holds whichever AI model is in use, and swapping the model must not weaken it.

3. **A composed answer always finishes.** A model answer is never shown cut off mid-sentence
   as though it were complete — it either runs to a natural end or ends with a plain note
   that it was cut short and can be continued.

4. **A brief assistant outage should never be a dead end.** When the assistant genuinely
   can't compose an answer for a moment, the user sees a calm "try again shortly" message
   and can still get instant answers to the common questions — not a bare error with nowhere
   to go.

Each story is surfaced as a left-navigation task, and its visible answer stays concise and
business-oriented. Detailed source and calculation information remains available through the
existing transparency surface. See `changes/2026-09-03-chat-resilience-and-instant-answers.md`.
The task selected by default on first load is now **"About this platform"** (revised
2026-09-04 — previously "What we know about the market"; see Opening Welcome, below).

---

## Information Architecture

**Location:** Market Health (primary landing section)

The page is a conversation. There is no static layout — all content is AI-generated and appears
inside a scrollable conversation thread.

The opening AI message contains exactly two things: the trend chart and the written summary.
Nothing else is shown until the user asks.

| Zone | Priority | Contains |
|---|---|---|
| Top Bar | Primary | Product title. Fixed, always visible. |
| Conversation Thread | Primary | Scrollable. Opening AI message: trend chart + written summary. Subsequent messages: user questions and AI answers. |
| Chat Input | Primary | Fixed, full-width, pinned to the bottom. Always visible. |
| Prompt Transparency | Secondary | Every AI message exposes a "view prompt" affordance. |

---

## Opening Prompt

The system fires this prompt automatically on load. The user does not type anything.

This prompt embodies Principle 1 (Intent First, Always Explicit): outcome, constraints,
and delegation boundary are all stated explicitly. The system has no room to guess.

```
Show me the current trend in tech job openings by role category — Designer, Product Manager,
and Engineer — month over month.

Display total openings per month for each category as a line chart.
Provide four time range views the user can switch between: 6 Months, This Year, Past 5 Years,
All Time.

Then write a brief summary of what the data shows: the overall direction (rising, flat,
or declining), the magnitude of change, and any notable differences between the three role
categories. Keep the summary to 3–4 sentences. Use plain, direct language. Do not use
verdict labels (Cautious, Strong, Weak). Do not recommend an action — describe only.

Delegation boundary: retrieve the data, render the chart, generate the summary.
The user interprets and decides what to do with it.
```

---

## User Flow

1. The user opens the product. The page loads with a fixed top bar and an empty conversation thread.
2. The system fires the opening prompt. The opening AI message generates:
   first the trend chart, then the written summary directly below it.
3. The user reads the chart. The direction is visible before reading any text.
4. The user reads the written summary. It confirms what the chart shows in plain language.
5. The user optionally switches the time range (6 Months / This Year / Past 5 Years / All Time)
  and/or the granularity (Week / Month — added 2026-08-22,
   `changes/2026-08-22-chart-granularity.md`; see Chart Specification for which
   granularities are available at which range). The chart updates. The summary
   regenerates for the new window and bucket size.
6. The user types a follow-up question in the chat input (or picks one of the offered common
   questions) — anything from a specific comparison
   ("Is User Experience Designer or Product Designer more in demand right now?"), to a
   narrower demand slice ("Are Staff-level Engineering roles growing?", "Are IC or management
   roles more common right now?", "How does demand for Backend Engineers differ between the US
   and Europe?"), to a compensation question ("What salary should I expect for a Senior
   Product Designer?", "What's the typical pay range for a Backend Engineer in San
   Francisco?"), to a requirements question ("What skills are Senior UX Designer postings
   asking for?", "How often do Product Manager roles require SQL?", "What education level do
   most Engineering roles require?"), to a synthesis question that asks for a judgment, not
   a lookup ("Should I learn to code as a UX Designer?", "What should I focus on learning to
   move from Mid to Senior?"), to something the platform's data can't possibly cover ("What
   was demand like in 2019?").
7. The AI answers by actually analysing the platform's own data for that specific question —
   not repeating a fixed canned summary. It states the answer's time window plainly, grounded
   in when live data collection actually began (e.g. "since we started tracking on 20 July
   2026, Product Designer postings have outnumbered User Experience Designer postings").
   **Every answer is built only from the platform's own data.** The assistant does not consult
   the open web and does not answer from a model's general knowledge — not to fill a gap, not
   for "broader context," not for a question the data almost covers. If a question reaches
   outside what the data holds — a period before collection began, a company or place the
   dataset doesn't include, a topic job postings can't speak to — the AI says so plainly,
   names the nearest thing the data *can* address, and offers one or two questions it can
   actually answer. It never substitutes an outside answer for the missing one; an honest
   "we don't track that" beats a plausible answer from elsewhere. This is a rule about the
   product, not about a particular model — it holds whichever AI composes the answer. The
   detailed *how* — which queries ran, over what window — belongs in the drill-down (see
   Thinking process accordion, below); the visible answer stays concise and conversational,
   a few sentences or a short list, never a multi-section report.
7a. **Compensation Signal answers carry an additional, non-negotiable honesty requirement**:
   not every posting discloses salary, and the postings that do aren't equally reliable —
   some come from a structured field the source itself provides, others are inferred from
   free-text job descriptions. The AI never blends these into one undifferentiated number.
   It leads with the more reliable figures, states how many postings the figure is based on,
   and if a lower-confidence estimate is included at all, it is explicitly labelled as an
   estimate, never presented with the same certainty as a disclosed figure (e.g. "Based on
   14 postings with disclosed salary ranges, Senior Product Designers typically earn
   $130K–$165K. A further 6 postings mention compensation only within the job description
   text — those estimates are noisier and are not included in the range above unless you ask
   for them."). If no role in the queried slice has any disclosed compensation data, the AI
   says so plainly rather than guessing from seniority alone.
7b. **Requirements Signal answers carry their own honesty requirement, different in kind
   from Compensation Signal's**: every extracted skill, education level, or language
   requirement is the AI's *interpretation* of free text a company wrote, not a verified
   fact — there's no structured-vs-parsed confidence split the way compensation has, because
   no source ever provides this as a structured field. Answers must speak in proportional
   terms ("42% of postings mention X"), never absolute ones ("all postings require X"), and
   must state the sample size (e.g. "based on 38 Senior UX Designer postings"). **A synthesis
   question ("Should I learn to code as a UX Designer?") gets a two-part answer, and the two
   parts are never blended**: first the data — the actual aggregate (e.g. "Front-end coding
   appears in 27% of Senior UX Designer postings, almost always tagged nice-to-have rather
   than must-have — design systems and prototyping are far more commonly required") — then,
   clearly separated, the AI's judgment built on that data (e.g. "Given that, coding is
   unlikely to be the highest-leverage thing to learn next — design systems fluency would
   affect more of your applications"). The judgment is reasoning over the platform's own
   numbers, not outside advice — "should I learn Rust?" is answered by looking at how often
   Rust-family skills appear in the tracked postings and at what requirement level, then
   reasoning from that. If the sample is too small to support a confident judgment, the AI
   says so and gives the data alone rather than a shaky recommendation.
7c. **An instant answer to a common question is held to exactly the same bar.** It analyses
   the platform's own data for that specific question, states the time window, and obeys the
   Compensation and Requirements honesty rules (7a, 7b) — the numbers are always current as
   of when it's asked, never stored or stale. The only thing different is that no AI model
   composed it, and the drill-down says so.
8. The conversation grows downward. The user leaves with a clear directional read.

---

## Visual Design

**Top bar** — fixed, full width. Product title only. Does not scroll.

**Opening AI message** — the first and dominant message in the thread. Contains:

1. **Trend chart** — large. Three lines: Designer, Product Manager, Engineer, each in a
   distinct colour. A time range selector above the chart, right-aligned:
  `6 Months · This Year · Past 5 Years · All Time`. Default: 6 Months.
   Hover: vertical cursor snaps to the nearest month; tooltip shows the count and M-o-M Δ
   for each visible line.
   No verdict label, no colour-coded health state. Numbers and shape only.
   These three categories are the fixed `Role Category` set from
   `design/information-architecture.md` Content Taxonomy. Sub-specializations within each,
   plus the seniority and track taxonomy used elsewhere in this feature, are defined in
   `design/market-health/job-classification.md`.

2. **Written summary** — directly below the chart, inside the same message bubble.
   3–4 sentences. Names direction, magnitude, and category divergence where present.
   No verdict labels. Plain language. Regenerates when the time range changes.
   A "view prompt" affordance is anchored to this block.

**Chat input** — fixed, full width, pinned to the bottom. Placeholder: "Ask about the market…".
The offered common questions and the transient "assistant briefly unavailable" message both
sit within this existing conversational layout — quiet, not competing with the conversation,
in the product's established tone. Exact placement and styling are for the frontend and
visual-design work, not decided here.

**Thinking process accordion** — every AI message carries a secondary disclosure control below
its header: a small chevron link labelled "How this was generated". Collapsed by default.
When expanded, it shows:

- **Filters applied** — the active role, sub-specialization, seniority, track, location, and
  time range as tag chips, whichever the question actually used — a broad question shows
  fewer chips, a narrow one shows more. Role, sub-specialization, seniority, and track values
  follow the canonical taxonomy defined in `design/market-health/job-classification.md`.
  Location was previously listed here ahead of the data existing to back it; as of this
  update it reflects a real, normalized value per posting, not a placeholder.
- **Context sent to Claude** — the market signal verdict and trend direction, demand signal count,
  compensation signal count (and, when a compensation question was asked, how many of those
  postings had disclosed vs. inferred salary data), requirements signal count (and, when a
  synthesis question was asked, the sample size the judgment was built on — see User Flow
  7b), layoff event count, and the model used. For an instant answer this says plainly that
  no model was used — the user can always tell what produced their answer.
- **Sources** — for the opening briefing, the data source description — now potentially more
  than one, since postings are ingested from several company job boards rather than a single
  provider. When more than one source contributed to what's shown, each is named (e.g.
  "Company job boards hosted on Greenhouse, Lever, and Ashby"), not collapsed into a generic
  "job board data" label — the user can tell a Greenhouse-sourced count from a Lever-sourced one
  if they ask, even though the chart and summary blend all sources together by default. For a
  follow-up chat turn, this is where the *how* lives: which owned-data queries ran, over what
  time window, and why. Every chat answer is built from the platform's own data only — there
  is no external search to disclose — so this section is a complete account of what produced
  the answer, for the user who wants to verify rather than just trust. Never shows a source
  that wasn't actually consulted for that response. This is the same commitment
  `design/ai-reasoning-panel/experience.md` already makes product-wide (its "Sources & Tools"
  section) — a follow-up turn's Sources entry here is that same disclosure, applied to this
  feature's questions.
- **API calls** — the internal endpoints queried to build the response (briefing turns only)

The accordion is read-only. It cannot be edited or shared. It appears on every AI turn —
both the opening briefing and all follow-up responses.

Visual tone: the chart carries the emotional weight. The summary confirms it. No urgency
language or sentiment framing beyond what the numbers directly support.

---

## Chart Specification

| Property | Value |
|---|---|
| Chart type | Line chart, continuous. No bar fill. |
| **Chart title** | "Tech hiring demand" — top-left, `text-sm font-semibold text-gray-100` |
| **Chart subtitle** | Dynamic per granularity — "Daily job openings by role category" / "Weekly job openings by role category" / "Monthly job openings by role category" — below title, `text-xs text-gray-400` |
| **Time range filter** | Top-right of the title row, right-aligned dropdown. Options: `6 Months · This Year · Past 5 Years · All Time`. |
| **Granularity filter** (added 2026-08-22 — `changes/2026-08-22-chart-granularity.md`) | Directly below the time range filter, same right alignment. Dropdown options: `Week · Month`. Independent control from Time Range. Default: Week. |
| **Legend** | Below the title row, above the chart. Coloured line swatch + role label per category. |
| **Y axis label** | "Openings" — rotated 90°, left of the Y axis tick values. `text-[10px] fill-gray-500`. |
| **X axis label** | Dynamic per granularity — "Day" / "Week" / "Month" — centred below the X axis tick marks. `text-[10px] fill-gray-500`. |
| X axis ticks | Week granularity: week-start date labels (e.g. "Aug 3"). Month granularity: month names (Jan, Feb…) for 6 Months/This Year, year for Past 5 Years/All Time. Primary axis identifier — the label is supplemental. When the plot area does not scroll and there are more buckets than fit legibly, tick labels are thinned to an evenly spaced subset (never overlapping); the underlying line still uses every bucket. Long ranges (Past 5 Years / All Time) always show at least one tick per year regardless of granularity (updated 2026-09-04). |
| Y axis ticks | Absolute count, formatted (e.g. 5k, 10k). |
| Lines | Designer, Product Manager, Engineer |
| Default time range | 6 Months |
| Available ranges | 6 Months · This Year · Past 5 Years · All Time |
| **Default granularity** (added 2026-08-22) | **Week** — shows the shape of the live data without monthly sparsity. Fixed and predictable, not adaptive to data volume. |
| **Available granularities** | Week · Month. Both are available for every range in this slice. |
| **Horizontal scroll** (added 2026-08-22) | The plot area (X axis + lines) scrolls horizontally once the number of buckets exceeds what fits legibly at a minimum ~24px per bucket; the Y axis, title, subtitle, and legend never scroll. |
| Hover | Vertical cursor + tooltip with count + period-over-period Δ per line (day-over-day, week-over-week, or month-over-month, matching the active granularity — generalizes the previous "M-o-M Δ only" behaviour) |
| Loading state | Skeleton lines pulse in place. Chart frame does not shift. |
| No-data state | If a category has no data for a range, its line is hidden; legend shows "No data." A sparse-but-real line (e.g. only the most recent few buckets populated, the rest of the window empty because live data collection started recently) is not a no-data state — it's shown as-is, honestly reflecting how much real history actually exists. Never padded, interpolated, or hidden to look more complete than it is. |
| Flat / single-bucket data | A genuinely flat series (every bucket the same value) renders as a straight horizontal line, not a blank chart. When only one complete bucket is in range, its values render as labelled points (no line) with a caption naming the period and stating that a trend line needs at least two. The Y axis always shows a readable scale even when the value range is zero-width. |
| Complete periods only | The in-progress week or month is never plotted — see Written Summary Specification. The last point on the chart is always a period that has fully elapsed. |
| Baseline exclusion | The first collection day never appears as a bucket on the chart. The X axis begins at the first full bucket after it. This is why "6 Months" can legitimately show only a few weeks of line — the window before live collection started has no data and is not drawn (updated 2026-09-04 — `changes/2026-09-04-chart-baseline-and-render-fixes.md`). |

---

## Written Summary Specification

Generated with the opening prompt. Regenerates when the time range **or granularity**
changes (added 2026-08-22 — `changes/2026-08-22-chart-granularity.md`).

**Rules:**
- Always identifies the selected time range and granularity in the first sentence (for
  example, "In the weekly view for the past 6 months...").
- Always names the direction: rising, flat, or declining.
- States magnitude where data supports it (% change or absolute count).
- Only **complete** periods are shown or compared — a week whose final day has passed, a
  month before the current one. The in-progress week or month is not plotted at all: a
  4-day September drawn at full scale next to a 31-day August reads as an ~80% collapse that
  never happened. With fewer than two complete post-baseline buckets, the summary says the
  series is too short to state a trend yet (added 2026-09-04 —
  `changes/2026-09-04-chart-baseline-and-render-fixes.md`).
- Names divergence between categories if present (e.g., one category outperforming the others).
- Names a recent reversal if relevant (e.g., a decline that is slowing).
- Never uses verdict labels (Cautious, Strong, Weak, etc.).
- Never recommends an action.
- 3–4 sentences maximum.
- Trend counts begin the day **after** the first collection day. That first day is a one-time
  bulk load of everything the sources had open when the platform started crawling — it is the
  platform's baseline, reflects collection setup rather than market activity, and must never be
  described as a hiring surge. The baseline is identified by date (the earliest day the
  platform observed any posting), not by which ingestion run inserted a row (updated
  2026-09-04 — `changes/2026-09-04-chart-baseline-and-render-fixes.md`).

**Example outputs:**

↓ Declining: "Tech job openings are down 23% year-over-year, with the steepest drops in
Product Manager (−31%) and Designer roles (−28%). Engineering has held more stable at −12%.
The pace of decline has slowed in the last three months."

→ Flat: "Tech job openings have been broadly flat over the past 12 months, within a ±5% band.
Designer and Engineering roles are stable. Product Manager openings spiked in Q2 but have
since returned to the baseline."

↑ Rising: "Tech job openings have grown 18% year-over-year, led by Engineering (+27%).
Designer and Product Manager roles are also up, at +11% and +9% respectively. Growth was
concentrated in the first half of the year — the last three months have been flat."

---

## Interactions

| User action | System response |
|---|---|
| Open Market Health | "About this platform" is selected by default; its welcome resolves instantly (no model call). |
| Open Market Health, then select "Tech market hiring status" | Opening message generates: trend chart (6 Months default, Week granularity default), then written summary. |
| Tap a catalogue shortcut in "About this platform" (added 2026-09-04) | Task Panel selects that story's own task, exactly as if the user had clicked it directly — the same instant, no-model answer that task always gives. Works the same for any number of catalogue entries. |
| Switch time range | Chart updates. If the current granularity isn't available at the new range, granularity falls back to that range's coarsest option. Written summary regenerates for the new window. |
| Switch granularity (added 2026-08-22) | Chart updates — X axis re-buckets, horizontal scroll engages/disengages as needed. Written summary regenerates for the new bucket size. Time range selection is unaffected. |
| Hover over chart | Vertical cursor + tooltip with count + M-o-M Δ for each line. |
| Ask a question in chat (typed or via a suggested-question chip) from any task | **Each task is its own conversation.** The question and its answer appear in the current task's thread, below that task's opening content (its welcome, its story answer, or its chart + summary). Switching tasks switches the conversation; the chat input always queries the task you are looking at. It never redirects you elsewhere (added 2026-09-06 — `changes/2026-09-06-chat-input-dead-on-non-conversation-tasks.md`). |
| Ask a question in chat, answerable from the platform's data | AI analyses the platform's data specifically for that question (not a fixed canned summary), states the answer's time window, and the accordion shows what was queried. |
| Ask a question in chat that reaches outside the platform's data (e.g. a period before data collection began, a company or city not tracked) | AI says plainly that the platform doesn't have that data, names the nearest thing the data *can* speak to, and suggests 1–2 questions it can actually answer. Never an outside answer, a web search, or a general-knowledge fill-in. |
| A composed answer is cut off before it finishes (length limit, dropped stream) | The turn never ends on a sentence that just stops. The answer continues to a natural end, or ends with a plain note that it was cut short and can be continued. A partial answer is never presented as the whole answer. |
| Ask a compensation question in chat (e.g. "What should I expect to earn as a Senior Backend Engineer?") | AI answers using disclosed-salary postings first, states how many postings the figure is based on, and — if a lower-confidence, inferred-from-text estimate is included at all — labels it explicitly as an estimate rather than blending it into the headline range. States plainly if no postings in that slice disclose compensation. |
| Ask a narrower demand question (sub-specialization, seniority, track, or location) | AI filters the platform's data to that slice and answers the same way it does for role-category-level questions — same provenance and time-window discipline, just a narrower cut. |
| Ask a requirements question (e.g. "What skills are Senior UX Designer postings asking for?") | AI reports proportions from extracted requirements data, states the sample size, and never phrases a proportional finding as an absolute claim. |
| Ask a synthesis question that asks for a judgment (e.g. "Should I learn to code as a UX Designer?") | AI answers in two clearly separated parts: the underlying data first, then its judgment built on that data — never blended into one undifferentiated statement. If the sample is too small to support a confident judgment, gives the data alone and says so. |
| Pick an offered common question | It's asked as if typed. A curated question returns an instant answer from current platform data, held to the same time-window and honesty rules as any answer. |
| Assistant is briefly unavailable (transient outage) | The AI turn shows a calm "try again shortly" message and the common questions stay available. Not a red error state; retrying a moment later normally works. |
| Tap "view prompt" | Read-only overlay shows the exact prompt that produced that message. |
| Tap "How this was generated" | Accordion expands below the AI message header, showing filters, context sent to Claude, data counts, model, and sources. Tap again to collapse. |

---

## Edge Cases

- **"About this platform" before any postings have been collected (added 2026-09-04, revised
  2026-09-04 for the hero/proof/CTA structure):** The Hero renders as normal — it doesn't
  depend on data. Proof states plainly that collection hasn't produced results yet: the Hero
  Figure and Stat Tiles show a calm "not collected yet" state rather than `0`, and the
  Category Share Bar is omitted rather than rendered empty. The call to action still lists the
  catalogue's Shortcut Cards (they're about what questions exist, not about current results),
  but each linked story is responsible for its own no-data state once opened — the welcome
  does not pre-judge whether a story can currently answer.
- **The story catalogue is empty:** The call to action omits its Shortcut Cards entirely
  rather than rendering an empty section; the generic "ask your own question" sentence still
  shows.
- **Insufficient data for a time range:** Show what exists. X axis compresses to fit. A note
  below the chart: "Data available from [earliest date]." Summary reflects the available window.
- **No data at all:** Replace chart with a plain message. Summary does not generate.
- **Summary generation fails:** Show: "Ask a question below to explore the trend data."
- **The assistant is briefly unavailable (transient outage):** The AI turn shows a calm,
  non-alarming message — can't answer right now, try again in a moment — and the common
  questions stay available (they return answers straight from the platform's data and don't
  need the assistant). Never a dead-end error with no way forward. Explicitly *transient*
  wording ("right now" / "try again shortly"), not "failed".
- **Instant answer whose data slice is empty or too small:** It states that plainly — "No
  tracked postings match this yet", or the raw counts with "too few to read a trend from" —
  exactly as a composed answer would. It never invents a number to fill a template.
- **Question is entirely outside the tech job market (e.g. general life advice, an unrelated
  topic):** Say so plainly and suggest 1–2 related questions the platform can actually help
  with. Do not attempt an answer from outside the data.
- **Question reaches outside the platform's data (e.g. a period before data collection began,
  a company or place the dataset doesn't cover):** Say so plainly — the platform doesn't
  track that. Name the closest thing the data *can* address and suggest 1–2 answerable
  questions. Never fill the gap from the open web or from a model's general knowledge; an
  honest "we don't track that" beats a plausible answer from elsewhere.
- **A claim would need data the platform doesn't have:** The AI states plainly that it
  doesn't have that data, rather than inventing a plausible-sounding figure or citing
  something it didn't actually query. Never cite a source that wasn't consulted for that
  response.
- **A composed model answer comes back incomplete (a length limit, a dropped stream):** The
  user is never left with a sentence that just stops. The answer either continues to a
  natural end, or ends with a plain marker that it was cut short and an invitation to ask for
  the rest. A half-answer is never presented as if it were the whole answer, and its
  drill-down reflects that it was truncated. This holds regardless of which AI model is in
  use — completeness is a product guarantee, not a model setting.
- **Coverage is a curated set of companies, not the whole market:** Postings come from a
  maintained list of companies whose job boards are hosted on Greenhouse, Lever, or Ashby — not
  a survey of every employer. This is a real, honest limit, not a bug: large organisations
  running custom career sites or a legacy ATS aren't captured. The main chart and written
  summary describe what the tracked companies show ("tech job openings" shorthand, unchanged for
  readability) without claiming completeness; the accordion's Sources section is where the
  actual coverage (which platforms, i.e. not "the entire market") is disclosed for anyone who
  asks. If a user's chat question depends on coverage the tracked company list doesn't include
  (e.g. "what about jobs at [a company not on any tracked list]?"), the AI says so plainly rather
  than implying the platform tracks every employer.
- **No disclosed compensation data for the queried role/slice:** Say so plainly (e.g. "None of
  the tracked postings for this role currently disclose a salary range"). Never fall back to
  guessing a figure from seniority or role alone — an absent number is more honest than an
  invented one.
- **Compensation data exists but only at low confidence (inferred from free-text job
  descriptions, not a structured field):** Never presented as if it were a disclosed figure.
  Either offered only when the user asks for more detail beyond the headline range, or included
  with an explicit "estimated" label and the reasoning shown in the accordion — never silently
  blended into the same number as higher-confidence data.
- **Compensation or narrower demand question depends on location, but the posting's location
  couldn't be normalized to a specific country/city:** The AI excludes that posting from a
  location-specific answer rather than guessing its location, and says so if it materially
  affects the sample size (e.g. "12 of 20 matching postings had a usable location").
- **No extracted requirements data for the queried role/slice:** Say so plainly rather than
  guessing what a role "probably" requires from general knowledge — the same "absent is more
  honest than invented" rule as compensation.
- **Sample too small to support a synthesis question's judgment:** The AI gives the
  underlying data (even a small amount) but explicitly declines to draw a recommendation
  from it, rather than reasoning confidently over too few postings (e.g. "Only 4 postings
  match this slice — not enough to draw a reliable conclusion, but here's what they show...").
- **A requirement doesn't map to any tracked skill/education/language value:** Captured in
  the freeform catch-all (`design/market-health/job-classification.md` — Other requirements)
  rather than forced into the nearest standard value or dropped. If a user's question depends
  specifically on catch-all content, the AI can surface it, but always distinguishes it from
  the standard taxonomy's closed-set values.

---

## Evaluation Metrics

| Metric | How measured | Target |
|---|---|---|
| Time to directional read | Analytics — time from chart render to first scroll or interaction | < 15 seconds |
| Direction comprehension | Post-task question: "Is the market rising, flat, or declining?" | ≥ 85% correct |
| Time range switch rate | Analytics — % of sessions where user changes from default range | Track, no target yet |
| Chat engagement rate | Analytics — % of sessions where user sends at least one follow-up | Track, no target yet |
| Compensation question rate | Analytics — % of sessions that include at least one salary-related question | Track, no target yet |
| Confidence comprehension | Post-task question, after a compensation answer: "Was this figure based on disclosed salary data, an estimate, or a mix?" | ≥ 85% correct |
| Requirements question rate | Analytics — % of sessions that include at least one skills/requirements or synthesis question | Track, no target yet |
| Data-vs-judgment comprehension | Post-task question, after a synthesis answer: "Which part was factual data, and which part was the AI's opinion?" | ≥ 85% correct |
| Instant-answer coverage | Analytics — % of follow-up questions answered by the curated no-model path | Track; expected to rise as the catalogue grows |
| Degraded-state recovery | Analytics — % of "assistant unavailable" turns followed by a successful answer (retry or common question) in the same session | ≥ 90% |

---

## Open Questions

- Should the Y axis show absolute counts or index-normalised values? Absolute is more concrete;
  indexed makes cross-range trend comparison easier but feels less grounded.
- Should "All Time" include a smoothed trend line alongside raw monthly data to reduce noise?
- This spec's own "Thinking process accordion" (above) and `design/ai-reasoning-panel/experience.md`'s
  universal "Reasoning Panel" ("View thinking" toggle) describe overlapping but differently-named
  provenance UI, and the shipped product already uses the universal component's naming. This
  change updates this spec's accordion content (the Sources entry) to carry the new attribution
  rule without resolving which naming is canonical — that reconciliation is out of scope here
  and should be its own future change request.
- Should a Compensation Signal answer ever include a small inline visual (e.g. a min–max range
  bar) instead of prose-only numbers? Deliberately left text-only in this update to avoid
  inventing a new visual component and IA term before there's evidence users want one —
  revisit once the Compensation question rate metric (below) shows real usage.
- Should the fixed opening view ever surface Compensation Signal by default (e.g. a salary
  range annotation on the trend chart) rather than purely on request? Deliberately kept
  conversation-only in this update, per Principle 3 (Exceptions Define the Experience) — not
  every user's first question is about pay, and the opening view is already deliberately
  minimal. Revisit if the Compensation question rate metric shows most sessions ask for it
  anyway, which would argue for promoting it to the default view.
- Should skills/requirements ever get a dedicated visual (e.g. a frequency bar chart across
  the tracked skills for a role) instead of prose-only proportions? Same reasoning as
  Compensation Signal's equivalent open question — deliberately left text-only until the
  Requirements question rate metric shows real usage, rather than inventing a visual
  component speculatively.
- The tracked skills list per Role Category (`design/market-health/job-classification.md`)
  is a v1 starting point, explicitly expected to be reviewed and widened once real
  extraction data shows which mentioned skills don't map to any tracked value and recur
  often enough to justify adding — same "Raw Title" discipline already used for
  sub-specializations, not a one-time decision.
- The curated instant-answer catalogue (added 2026-09-03) starts small and is meant to grow
  continuously — which questions to add next should be driven by what users actually ask
  most, not guessed up front. Same review discipline as the skills list above.
- How the common questions are offered and how the transient "unavailable" message reads —
  placement, wording, styling — is deliberately left to the frontend and visual-design work,
  within the existing conversational design.

**Added (2026-09-03):** Two goals stated, no design change: (1) a curated, growing set of
common questions should answer instantly from current platform data with no AI model call;
(2) a brief assistant outage should show a calm "try again shortly" state with the common
questions still available, never a dead-end error. Every answer is still data-grounded and
held to the same honesty rules (User Flow 7c); the drill-down is honest about what produced
it. Opening chart, summary, and prompt untouched. How these surface is left to the frontend
and visual-design work. See `changes/2026-09-03-chat-resilience-and-instant-answers.md`.

**Revised (2026-09-06 — `changes/2026-09-06-chat-answer-truncation-and-curated-match.md`):**
The conversation is now explicitly **data-only and fluent**. The external web-search path is
removed — every chat answer is composed only from the platform's own data (User Flow 7,
"What we want to achieve" #2). A question the data can't reach gets a plain "we don't track
that" plus a pointer to what it can answer, never an outside answer; the corresponding
"answers from external sources" / "blends platform and external" language and Edge Cases are
gone. "Should I learn X" judgment questions (User Flow 7b) are unchanged in shape but
explicitly answered *from* the data. New guarantees: a composed answer is never shown cut off
mid-sentence as if complete (new Edge Case + "What we want to achieve" #3), and the instant
path recognises ordinary rephrasings, not just near-exact wording (#1). All of these are
product rules that hold regardless of which AI model is in use. Stale "fell back to a
secondary model" accordion line removed (the tier list was dropped 2026-09-06). Opening
chart, summary, and prompt untouched.

**Resolved (2026-08-11):** `design/market-health/job-classification.md` underwent a full
taxonomy redesign (`changes/2026-08-11-classification-taxonomy-redesign.md`) — the old
`seniority` ladder split into separate `level` and `track` fields, an `unknown` vs `other`
distinction added, skills restructured with raw text alongside category, and several new
Requirements fields (years of experience, work arrangement, education nuance) added. Reviewed
this spec in full against that change and confirmed **no update needed**: line 178's filter-chip
list already presents "seniority" and "track" as two separate concepts (this spec never
enumerates the underlying ladder values itself), so the values behind those chips becoming more
accurate doesn't change any wording, interaction, or chip here. Same reasoning for the trend
chart's three lines (line 156) — they're the fixed Role Category set, untouched by this
revision. Confirmed by reading the actual file, not assumed, per this product's standing
review discipline.

**Resolved (2026-08-09):** Requirements Signal (skills, education, language requirements,
plus a freeform catch-all) is now in scope, reached only through follow-up conversation —
same conversation-only pattern as Compensation Signal, never added to the fixed opening
view. This also introduces the experience's first **synthesis question** capability
(User Flow 7b) — a judgment built on data, always presented as two clearly separated parts,
never blended — distinct from every prior question type, which was a direct data lookup.
See `changes/2026-08-09-skills-and-industry-signal.md`.

**Resolved (2026-08-04):** Compensation Signal (salary) is now in scope, reached only through
follow-up conversation — never added to the fixed opening view. Demand Signal now supports
sub-specialization, seniority, track, and location as follow-up drill-down dimensions, using
the "Thinking process" accordion's already-anticipated filter chips (previously listed ahead
of real data existing to back them). Neither addition changes the opening chart, the written
summary, or the opening prompt — see `changes/2026-08-04-compensation-signal-gap.md`.

**Resolved (2026-08-03):** Job data now comes from multiple company-job-board sources
(Greenhouse, Lever, Ashby — see `changes/2026-07-28-multi-source-job-data-ingestion.md`), not a
single aggregator. This spec's User Flow and Edge Cases were already written in source-agnostic
language ("the platform's own data," never naming a specific provider) and needed only two
additions: the Sources accordion entry can now name more than one platform, and a new Edge Case
makes the curated-company-list coverage limit explicit rather than implied. No change to the
chart, written summary, or opening prompt — those already describe outcomes ("tech job
openings"), not where the data comes from.

**Resolved (2026-07-16):** Role categories are fixed in v1 — Designer, Product Manager,
Engineer. This was already committed by `design/information-architecture.md` Content Taxonomy
(`Role Category`), which defines exactly this set; it does not need to be decided again here.
The full classification taxonomy — sub-specializations within each category, the seniority
ladder, and the IC/management track — is defined in
`design/market-health/job-classification.md`. Backend and frontend specs reference that file
rather than redefining these values independently.
