---
id: market-health
outcome: understand-market-health-before-searching
directive: low
status: ready
created: 2026-06-13
updated: 2026-07-22
---

# Market Health — Experience Spec

## Outcome this serves

See: `outcomes/understand-market-health-before-searching.md`

---

## Primary question this experience answers

> "How is the tech job market trending right now — and has it been getting better or worse?"

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
   ("Is User Experience Designer or Product Designer more in demand right now?") to something
   the platform's data can't possibly cover ("What was demand like in 2019?").
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

- **Filters applied** — the active role, seniority, location, and time range as tag chips.
  Role and seniority values follow the canonical taxonomy defined in
  `design/market-health/job-classification.md`.
- **Context sent to Claude** — the market signal verdict and trend direction, demand signal count,
  compensation signal count, layoff event count, and the model used
- **Sources** — for the opening briefing, the data source description. For a follow-up chat
  turn, this is where the *how* lives: what the platform's data was queried or analysed for
  (and the data's time window), what — if anything — was searched externally, and why. The
  visible answer always states which source class it came from (platform data vs. external);
  this section is where the specific queries and searches behind that are inspectable, for the
  user who wants to verify rather than just trust. Never shows a source that wasn't actually
  consulted for that response. This is the same commitment `design/ai-reasoning-panel/experience.md`
  already makes product-wide (its "Sources & Tools" section) — a follow-up turn's Sources entry
  here is that same disclosure, applied to this feature's questions.
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

---

## Evaluation Metrics

| Metric | How measured | Target |
|---|---|---|
| Time to directional read | Analytics — time from chart render to first scroll or interaction | < 15 seconds |
| Direction comprehension | Post-task question: "Is the market rising, flat, or declining?" | ≥ 85% correct |
| Time range switch rate | Analytics — % of sessions where user changes from default range | Track, no target yet |
| Chat engagement rate | Analytics — % of sessions where user sends at least one follow-up | Track, no target yet |

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

**Resolved (2026-07-16):** Role categories are fixed in v1 — Designer, Product Manager,
Engineer. This was already committed by `design/information-architecture.md` Content Taxonomy
(`Role Category`), which defines exactly this set; it does not need to be decided again here.
The full classification taxonomy — sub-specializations within each category, the seniority
ladder, and the IC/management track — is defined in
`design/market-health/job-classification.md`. Backend and frontend specs reference that file
rather than redefining these values independently.
