---
id: market-health
outcome: understand-market-health-before-searching
directive: low
status: ready
created: 2026-06-13
updated: 2026-08-09
---

# Market Health — Experience Spec

## Outcome this serves

See: `outcomes/understand-market-health-before-searching.md`

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
Provide three time range views the user can switch between: This Year, Past 5 Years, All Time.

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
5. The user optionally switches the time range (This Year / Past 5 Years / All Time).
   The chart updates. The summary regenerates for the new window.
6. The user types a follow-up question in the chat input — anything from a specific comparison
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
   2026, Product Designer postings have outnumbered User Experience Designer postings"). If the
   question reaches outside what the platform's data can answer — a time period before
   collection began, or something the dataset was never going to contain — the AI says so
   plainly, then answers from real external sources it can point to (an article, a report, a
   named study), never from unverified recall. An answer is never presented without saying
   whether it came from the platform's own data or an external source — the two are never
   blended without saying which is which. The detailed *how* — what was queried, what was
   searched — belongs in the drill-down (see Thinking process accordion, below), not
   necessarily spelled out in the visible answer; the *source* always is.
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
   affect more of your applications"). If the sample is too small to support a confident
   judgment, the AI says so and gives the data alone rather than a shaky recommendation.
8. The conversation grows downward. The user leaves with a clear directional read.

---

## Visual Design

**Top bar** — fixed, full width. Product title only. Does not scroll.

**Opening AI message** — the first and dominant message in the thread. Contains:

1. **Trend chart** — large. Three lines: Designer, Product Manager, Engineer, each in a
   distinct colour. A time range selector above the chart, right-aligned:
   `This Year · Past 5 Years · All Time`. Default: This Year.
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
  7b), layoff event count, and the model used
- **Sources** — for the opening briefing, the data source description — now potentially more
  than one, since postings are ingested from several company job boards rather than a single
  provider. When more than one source contributed to what's shown, each is named (e.g.
  "Company job boards hosted on Greenhouse, Lever, and Ashby"), not collapsed into a generic
  "job board data" label — the user can tell a Greenhouse-sourced count from a Lever-sourced one
  if they ask, even though the chart and summary blend all sources together by default. For a
  follow-up chat turn, this is where the *how* lives: what the platform's data was queried or
  analysed for (and the data's time window), what — if anything — was searched externally, and
  why. The visible answer always states which source class it came from (platform data vs.
  external); this section is where the specific queries and searches behind that are
  inspectable, for the user who wants to verify rather than just trust. Never shows a source
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
| **Chart subtitle** | "Monthly job openings by role category" — below title, `text-xs text-gray-400` |
| **Time range tabs** | Top-right of the title row, right-aligned. `This Year · Past 5 Years · All Time`. |
| **Legend** | Below the title row, above the chart. Coloured line swatch + role label per category. |
| **Y axis label** | "Openings" — rotated 90°, left of the Y axis tick values. `text-[10px] fill-gray-500`. |
| **X axis label** | "Month" — centred below the X axis tick marks. `text-[10px] fill-gray-500`. |
| X axis ticks | Month names for This Year (Jan, Feb…). Year for Past 5 Years and All Time. Primary axis identifier — the label is supplemental. |
| Y axis ticks | Absolute count, formatted (e.g. 5k, 10k). |
| Lines | Designer, Product Manager, Engineer |
| Default time range | This Year (Jan–current month) |
| Available ranges | This Year · Past 5 Years · All Time |
| Hover | Vertical cursor + tooltip with count + M-o-M Δ per line |
| Loading state | Skeleton lines pulse in place. Chart frame does not shift. |
| No-data state | If a category has no data for a range, its line is hidden; legend shows "No data." |

---

## Written Summary Specification

Generated with the opening prompt. Regenerates when the time range changes.

**Rules:**
- Always names the direction: rising, flat, or declining.
- States magnitude where data supports it (% change or absolute count).
- Names divergence between categories if present (e.g., one category outperforming the others).
- Names a recent reversal if relevant (e.g., a decline that is slowing).
- Never uses verdict labels (Cautious, Strong, Weak, etc.).
- Never recommends an action.
- 3–4 sentences maximum.

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
| Open Market Health | Opening message generates: trend chart (This Year default), then written summary. |
| Switch time range | Chart updates. Written summary regenerates for the new window. |
| Hover over chart | Vertical cursor + tooltip with count + M-o-M Δ for each line. |
| Ask a question in chat, answerable from the platform's data | AI analyses the platform's data specifically for that question (not a fixed canned summary), states the answer's time window, and the accordion shows what was queried. |
| Ask a question in chat that reaches outside the platform's data (e.g. a period before data collection began) | AI says plainly that the platform doesn't have that data, then answers from a real, citable external source (article, report, named study) — never from unverified recall. Response and accordion both make clear it's an external source, not platform data. |
| Ask a compensation question in chat (e.g. "What should I expect to earn as a Senior Backend Engineer?") | AI answers using disclosed-salary postings first, states how many postings the figure is based on, and — if a lower-confidence, inferred-from-text estimate is included at all — labels it explicitly as an estimate rather than blending it into the headline range. States plainly if no postings in that slice disclose compensation. |
| Ask a narrower demand question (sub-specialization, seniority, track, or location) | AI filters the platform's data to that slice and answers the same way it does for role-category-level questions — same provenance and time-window discipline, just a narrower cut. |
| Ask a requirements question (e.g. "What skills are Senior UX Designer postings asking for?") | AI reports proportions from extracted requirements data, states the sample size, and never phrases a proportional finding as an absolute claim. |
| Ask a synthesis question that asks for a judgment (e.g. "Should I learn to code as a UX Designer?") | AI answers in two clearly separated parts: the underlying data first, then its judgment built on that data — never blended into one undifferentiated statement. If the sample is too small to support a confident judgment, gives the data alone and says so. |
| Tap "view prompt" | Read-only overlay shows the exact prompt that produced that message. |
| Tap "How this was generated" | Accordion expands below the AI message header, showing filters, context sent to Claude, data counts, model, and sources. Tap again to collapse. |

---

## Edge Cases

- **Insufficient data for a time range:** Show what exists. X axis compresses to fit. A note
  below the chart: "Data available from [earliest date]." Summary reflects the available window.
- **No data at all:** Replace chart with a plain message. Summary does not generate.
- **Summary generation fails:** Show: "Ask a question below to explore the trend data."
- **Chat query genuinely unanswerable:** Neither the platform's data nor a real external source
  applies (e.g. a question entirely outside the tech job market). Say so plainly and suggest
  1–2 related questions the platform can actually help with.
- **Question reaches outside the platform's data (e.g. a time period before data collection
  began):** Say so plainly first — never silently substitute an external answer for a data
  question without flagging the gap. Then, if a real external source can address it, answer
  from that source with the source named. If no real source can be found, say so rather than
  guessing.
- **Answer blends platform data and an external source:** Both are used in the same response
  (e.g. "our data shows demand rising since July; a 2025 industry report found similar broader
  trends — [source]"). The response and the accordion both distinguish the two — never
  presented as a single undifferentiated source.
- **A claim would need a source the platform doesn't have:** The AI states plainly that it
  doesn't have that data or a source for it, rather than inventing a plausible-sounding one.
  Never cite a source — platform data or external — that wasn't actually consulted for that
  response.
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
