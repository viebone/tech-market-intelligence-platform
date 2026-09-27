---
id: market-data-stories
feature: market-health
directive: low
status: ready
created: 2026-09-04
---

# Market Health - Data Stories

## Purpose

A **data story** is a predefined user question with a fixed answer structure and live data.
The question and presentation are authored ahead of time; the figures are computed when the
user asks for the story. A story is not a stored answer, a static report, or a new navigation
task.

Stories are the fast, deterministic layer of the market-health conversation. The system
checks the story catalogue before invoking an LLM. A matching story runs its owned-data
queries, fills its prepared sections, and reports that no model was used. A question that
does not match a story continues through the existing conversational routing and LLM path.

## Catalogue rules

Each story is documented as one catalogue entry containing:

| Field | Meaning |
|---|---|
| `id` | Stable identifier for routing and analytics |
| `display_name` | Short label for the Task Panel item (added 2026-09-04). May differ from `question` — a nav label, not a sentence. E.g. "What we know about the market" for the question "What do we currently know about the tech job market?". Required so the Task Panel and the Welcome's shortcut list can be built entirely from this catalogue, with no per-story frontend copy. |
| `question` | The canonical user-facing question, shown as the clickable shortcut text in the Welcome and as the opening prompt for the task |
| `example_phrasings` | A small set of equivalent phrasings accepted by the matcher |
| `audience_job` | The decision or understanding the story supports |
| `sections` | Fixed ordered answer sections, each with its own data contract |
| `queries` | Owned-data aggregates required to fill the sections |
| `freshness_rule` | The timestamp and source coverage shown with the answer |
| `limitations` | Conditions that must be disclosed rather than inferred around |
| `no_data_state` | Exact behaviour when a section has insufficient coverage |

Adding a story should be a catalogue operation: add one entry, its aggregate query, its
deterministic renderer, and focused tests. It must not require changing the generic chat
router, source adapter interface, or frontend conversation shell. It also must not require
changing the Welcome (below) — the Welcome reads this catalogue at request time, so a new
entry here appears there automatically.

## Visual standard every story must meet

Added 2026-09-10 — `changes/2026-09-10-story-visual-standard.md`. So a new catalogue entry
looks and reads like the last one shipped without a bespoke design pass. The full aesthetic
is `design/visual-design.md` — Data Story composition; this is the checklist a new entry's
**Visible answer shape** must satisfy:

- [ ] Opens with a **framing line** — one sentence naming what's summarised, numbers as
      context only, not a heading.
- [ ] **Blocks**, each: a fixed heading (+ a subtitle stating what's measured and its unit,
      whenever the heading alone doesn't make that obvious — added 2026-09-11,
      `changes/2026-09-11-data-legibility-market-health.md`, see `design/visual-design.md` —
      Data Legibility) → **one** chart or figure → its honesty qualifier (sample size /
      coverage caveat). No prose-only block except the framing line. **3–6 blocks** for a
      single-theme story; a story that covers both current state and year-on-year change
      groups its blocks into **two labelled movements** ("the market right now", then "how
      it's shifting") and may run to ~8.
- [ ] **At least one chart**, and **≥2 distinct visual forms** across the story (3+
      preferred) — drawn from the vocabulary in `visual-design.md` (Ranked bar list, Hero
      Figure, Stat Tile, Meter, Category Share Bar, Time series, Year-on-year comparison,
      Two-series comparison, World risk map, and — added 2026-09-26,
      `changes/2026-09-26-data-story-chart-variety.md` — Stacked share bar, Ordered columns,
      Diverging change bars, Range chart, Treemap, Stat Tile pair). A story that is five
      ranked bar lists in a row is under-composed.
- [ ] **No form repeats within a story except Ranked bar list** (added 2026-09-26), which may
      repeat **at most twice, never adjacent**, and only where both instances are genuinely a
      ranking question. Choose the form by the data's own job — `visual-design.md`'s "Choose
      the form by the data's job" table — never for variety alone; a form that doesn't fit its
      data is worse than a repeat.
- [ ] **Every chart meets the Chart accessibility standard** (added 2026-09-26,
      `design/visual-design.md`) — 12px minimum text, a legend for every colour/glyph/shape
      used, a "Show as table" disclosure, a one-sentence text alternative for assistive
      technology, and keyboard access. Not a finishing touch — a chart failing this is
      incomplete, same as a chart with no qualifier.
- [ ] **Chart-first** — the visual carries the point; heading and qualifier are labels.
- [ ] **At most one Hero Figure.**
- [ ] Consistent block anatomy, divider rhythm, palette (one muted hue for magnitude; only
      the three role accents for categorical), and type scale — identical across every story.
- [ ] Every block keeps its honesty qualifier. An `insufficient_data` block shows its "not
      enough data yet" line (Honesty and empty states, below), never an empty chart.
- [ ] **A year-on-year block** shows exactly two 12-month windows (current, and one year
      back — never more), states both date ranges in words, names what its two bar colours
      mean (added 2026-09-11 — the two-colour encoding was documented but never explained to
      the end user until this fix), and carries one plain sentence on what a shift in that mix
      means. Before ~13 months of data exists it shows the current window only + a muted
      "comparison starts {Month Year}" line — "coming soon", not an error (`visual-design.md`
      — Year-on-year comparison; Honesty and empty states, below).
- [ ] **A story built from an outside publisher's statistics** (added 2026-09-24,
      `changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md` — Story 5) **names the publisher
      visibly beside the framing line**, with the exact attribution text from the licence
      registry, never only in the Reasoning Panel; states each figure's period in words; and
      flags a provisional figure. A **cross-check** against platform figures is allowed only
      as two labelled, separately-sourced series — never a difference, a score, or a verdict —
      only on a dimension with an honest mapping, and always with the "not expected to match"
      qualifier. A story that shows such a cross-check may carry a **third labelled movement**
      ("how this compares with…") on top of the usual two; the ~8-block ceiling still applies.
- [ ] **A year-on-year block built from an official statistic** (added 2026-09-24) compares two
      periods of the same length a year apart *as the publisher defines them* (for the ONS
      vacancy series: two overlapping three-month averages, e.g. Jun–Aug 2026 against Jun–Aug
      2025), not the platform's two 12-month windows; it states both periods in words and names
      what the two bar colours mean, exactly like the platform's own year-on-year block.
- [ ] **No *current-snapshot* duplication of the welcome** — job count, company count,
      collection start, and the *current* role-category split all belong to "About this
      platform". A story may show a *year-on-year shift* in the same dimension (a different
      question — change, not state); it never repeats the welcome's current figures as-is.
- [ ] No visible source-adapter names, database fields, query names, model names, or
      extraction mechanics — those stay in the Reasoning Panel.
- [ ] Engaging by composition only — no entrance animation on the data
      (`visual-design.md` — Motion, unchanged).
- [ ] Ends with the **feedback reaction** (thumbs up / thumbs down) — added 2026-09-23,
      `changes/2026-09-23-user-feedback-mechanism.md`, see "Feedback reaction — every story"
      below. Every story gets it automatically; it is chrome around the story, not a block
      within it, and does not count toward the 3–6 block range above.

## Feedback reaction — every story

Added 2026-09-23 — `changes/2026-09-23-user-feedback-mechanism.md`, for
`outcomes/user-feedback-is-heard-and-shapes-the-platform.md`. Every Data Story ends with the
same reaction control, generic across the catalogue exactly like the rest of this file's
contract — adding a new story never means adding its own feedback handling.

**Placement:** immediately below the story's last block (after Movement 2 for a story that has
one), outside the honesty-qualifier/block structure — it reacts to the story as a whole, not to
any one figure in it.

**Shape:** two icon buttons, thumbs up and thumbs down, unselected by default, side by side,
with a short label above them ("Was this useful?").

**Behaviour:**
- **Thumbs up:** captured immediately on click. The button shows a brief selected state
  (matching the emerald "positive" semantic used elsewhere in this document, e.g. Story 2's
  contraction/expansion donut). No further UI — no text field, no confirmation dialog.
- **Thumbs down:** captured immediately on click, same selected-state treatment (this
  product's neutral/negative badge colour — never a colour implying the *user* did something
  wrong). Immediately reveals an inline optional free-text field beneath the buttons ("What
  could be better about this story?") with a small Submit and a Dismiss action — same inline
  reveal pattern as the Connected Assistant card's Revoke confirmation
  (`design/visual-design.md` — Output Panel Settings tab), not a modal. Dismissing the text
  field does not undo the thumbs-down capture — the reaction and the optional comment are two
  separate captures, and the reaction is already recorded before the comment field even
  appears.
- **Re-reacting:** clicking the other thumb after one is already selected replaces the
  reaction (never both selected at once). Clicking the already-selected thumb again clears it.
  Each change is its own capture — no attempt to "undo" a prior one server-side; the most
  recent reaction for that story-view is what admin's aggregate reflects (see backend spec).
- **Which story a reaction belongs to:** the story's own `id` from this catalogue (Story 1's
  `id`, Story 2's `id`, etc.) — the same identifier already used for routing, so admin can
  aggregate per Data Story without any new per-story wiring.

This control is unrelated to — and must not be confused with — the Reasoning Panel's "View
thinking" toggle (`design/information-architecture.md`). The Reasoning Panel explains how an
answer was produced; the feedback reaction is the user's own opinion of it. Both can appear on
the same story with no interaction between them.

## Relationship to the Welcome

Added 2026-09-04 — `changes/2026-09-04-about-this-platform-welcome.md`. **"About this
platform"** (see `design/market-health/experience.md` — Opening Welcome) is the Task Panel's
pinned, always-first, always-default item. It is **not a catalogue entry** — it has no row in
this file, no `id` in the catalogue sense, and it is never itself matched by the chat router.
Instead, at request time it reads this catalogue's `id` and `question` for every current entry
(the same shape `list_stories()`/`GET /api/market-health/stories` already returns) and renders
one shortcut per entry. Adding, removing, or reordering a story here changes what the Welcome
offers with no change to the Welcome's own code, copy, or spec. Selecting a shortcut opens that
story's own task — the Welcome does not compute or cache an answer on a story's behalf.

## Story 1 - What do we currently know about the tech job market?

### Display name

**What we know about the market** — the Task Panel item label. Distinct from the question
below, which is the sentence shown as the clickable shortcut and used as the task's opening
prompt.

### User question

> What do we currently know about the tech job market?

### Audience job

Show a professional **what the platform's data says about the tech job market right now** —
the actual roles, skills, pay transparency, and locations — before they ask a narrower
question or commit to a search.

### Visible answer shape

Revised 2026-09-06 (`changes/2026-09-06-market-story-visual-and-dedup.md`), then 2026-09-10
(`changes/2026-09-10-story-yoy-breakdowns.md` — the year-on-year movement). This story is the
**reference implementation** of the "Visual standard every story must meet" checklist above.
It never repeats the welcome's *current* figures as-is; where a dimension overlaps (role
category), the story shows how it's *shifting*, not what it is.

Two labelled movements. Fixed order; values live; headings fixed.

**Movement 1 — "The market right now"**

1. **Framing line** — one sentence naming what's being summarised. Numbers as context only.
2. **The roles being hired** — subtitle: "Open postings currently tracked, by specialization."
   Top 10 specializations (normalised roles such as "Machine Learning Engineer", "Security
   Engineer"), as a **Ranked bar list**. Once a year-earlier window exists, each row also
   carries its "+N pp" year-on-year delta; until then the delta column is absent.
   Specialization, not raw title (too fragmented); `unknown`/`other` excluded, not relabelled.
3. **What employers ask for** — subtitle: "Postings mentioning each skill group, must-have vs.
   nice-to-have." **Revised 2026-09-22** (`changes/2026-09-22-nivo-charting-library.md`) — a
   real grouped bar chart (`SkillDemandChart`, `design/visual-design.md` — Charting library),
   two named series with an explicit legend, replacing the original single Ranked bar list
   that only distinguished must-have via bar opacity.
4. **Pay transparency** — subtitle: "Postings that state a salary range vs. those that don't."
   **Revised 2026-09-22** (`changes/2026-09-22-nivo-pie-charts.md`) — a real 2-slice donut
   (`SharePieChart`, `design/visual-design.md` — Charting library), disclosed vs. undisclosed,
   replacing a Meter: this is a genuine 2-category partition of all postings, not a coverage
   percentage, so the donut's "Meter vs. donut" dividing line applies.
5. **Where the roles are** — subtitle: "Open postings currently tracked, by city." Top
   locations (country or city), Ranked bar list, with the "only N postings have a normalised
   location" caveat.

**Movement 2 — "How it's shifting" (year on year)**

A short intro line names the two windows in plain words. **Revised 2026-09-27**
(`changes/2026-09-26-data-story-chart-variety.md`) — before this revision all three blocks were
the same grouped-bar Year-on-year comparison, which was itself the pattern this change exists to
fix (three copies of one chart form in one movement). Each block below now uses the chart form
that fits its own question, per the no-repeat rule (Visual standard, above):

| Block | Question shape | Form |
|---|---|---|
| 6. Role mix | 3 categories, a real part-to-whole split | **Stacked share bar** |
| 7. Seniority | an ordered ladder, not a ranking | **Ordered columns** |
| 8. IC vs. management | exactly two shares summing to 100% | **Stat Tile pair** — no chart needed |

**At launch and for the product's first year (until ~August 2027) there is no year-earlier
window.** Each block has its own current-only state, decided below — because block 6's dimension
already appears in the Welcome, its current-only state is different from blocks 7 and 8's.

6. **How the role mix is shifting** — subtitle: "Share of postings by role category, this year
   vs. the year before." A **Stacked share bar** (`design/visual-design.md`): two 100% stacked
   bars, "This year" over "A year ago", segments in the fixed order Design (indigo-500) →
   Engineering (emerald-600) → Product Management (fuchsia-600) — the **three tracked areas
   only**, matching the trend chart and the welcome's Category Share Bar. `other` / `unknown`
   are coverage, not segments here, and their own trend is never a signal.
   **Current-only state — decided here:** the current role split already appears in the
   Welcome's own Category Share Bar, so drawing this block's "This year" bar alone, before a
   year-ago bar exists, would repeat that figure — forbidden by "No current-snapshot duplication
   of the welcome" (Visual standard, above). Until the year-ago window exists, this block shows
   **no bars at all** — only the muted "Year-on-year comparison starts {Month Year}. Tracking
   since {date}." line. Once the year-ago window exists, both bars render as specified above.
   *Meaning:* which of the three areas is taking a bigger or smaller slice of new roles.
7. **How seniority is shifting** — subtitle: "Share of postings by seniority level, this year
   vs. the year before." An **Ordered columns** chart (`design/visual-design.md`): one column
   per level of the ladder, left to right junior → senior — the order is the meaning, never
   sorted by value. This dimension does not appear in the Welcome, so — unlike block 6 — a real
   chart can honestly show before the comparison exists. **Current-only state:** the current
   year's columns alone (indigo-500, value on the cap), with the muted "Year-on-year comparison
   starts {Month Year}. Tracking since {date}." line beneath in place of a second column set.
   Once the year-ago window exists, a second, narrower gray-500 column appears beside each,
   with the legend "Solid column: now. Lighter column: a year ago." *Meaning:* whether the
   market is opening more junior or more senior roles than a year ago.
8. **IC vs. management** — subtitle: "Share of postings by track, this year vs. the year
   before." A **Stat Tile pair** (`design/visual-design.md`): two tiles, "Individual-contributor
   roles" and "Management roles" (`track` values `ic` / `management`; `unknown` excluded), each
   showing this year's share. **Current-only state** (the form's own default): each tile's
   change line reads the muted "Comparison starts {Month Year}" instead of a delta. Once the
   year-ago window exists, each tile's change line shows its real "▲ +N pp" / "▼ −N pp" / "–  no
   change" versus a year ago. *Meaning:* whether more of the new roles are for people who lead
   teams or do the work.

Every block keeps its honesty qualifier (sample size, coverage caveat, both window dates once a
comparison exists). Which job boards the data came from is provenance — Reasoning Panel, not a
visible block.

### Data contract

The story may use only platform-owned data from `raw_postings`, `classifications`,
`posting_skills`, `posting_requirements`, and their source metadata. It may not use an LLM,
external search, or unstated market assumptions to fill a value.

| Story fact | Aggregate | Required qualifier |
|---|---|---|
| Coverage window | `min(raw_postings.fetched_at)`, `max(raw_postings.fetched_at)` | Observation window; not historical market coverage |
| Dataset size | `count(distinct raw_postings.id)` | Unique captured postings, not total jobs in the market |
| Companies | `count(distinct raw_postings.company)` | Only non-null normalized company values |
| Sources | `count(distinct raw_postings.source)` and source names | Source adapters that contributed rows |
| Role distribution | Classified rows grouped by `role_category` | Classification coverage and sample size |
| Titles/specializations | Classified rows grouped by raw title and specialization | Only classified postings; unknown/other remain visible as coverage limits |
| Skills | `posting_skills` grouped by `skill_group` and `requirement_level` | Posting sample size; mentions are interpreted extraction, not verified facts |
| Compensation | `salary_confidence` grouped by `structured` and `parsed` | Structured and parsed figures are never blended |
| Geography | Non-null `country` and `city` grouped separately | Normalized-location coverage; null locations are not guessed |
| **Year-on-year shift** (role_category, level, track, specialization) | The admin's per-dimension distribution (`classification.get_classification_distribution`) computed for two windows: `[now − 12mo, now]` and `[now − 24mo, now − 12mo]`, keyed on `raw_postings.fetched_at`. Per category: current share, prior share, delta in percentage points. | Both window date ranges stated; shares carry their denominators; the two windows are never blended into one number. Windowed on `fetched_at` (when we observed the posting), which is the only date this platform can trust — same rule as the trend chart. |
| **Year-on-year availability** | `min(raw_postings.fetched_at)` — the prior window is only computable once it is ≥ 12 months before now | Below the availability threshold each shift block renders the current window only and states when the comparison begins; a prior-year figure is never estimated or zero-filled |

### Honesty and empty states

- Counts are current as of the response's query time and carry a data-freshness label.
- Percentages use the relevant denominator and state the sample size.
- A section with too little data says **"Not enough data yet"** and explains what coverage is
  missing. It does not disappear silently and it does not borrow from external sources.
- **A year-on-year shift block before the prior window exists** is a distinct state from "not
  enough data yet". **Revised 2026-09-27:** blocks 6–8 no longer share one chart form, so they no
  longer share one current-only treatment either — each is specified block by block above (block
  6: no chart, since a current-only version would repeat the Welcome; blocks 7–8: their current
  year's data does show, since neither appears in the Welcome). Every block still says plainly
  when the comparison starts — "Year-on-year comparison starts {Month Year}. Tracking since
  {date}." — and reads as pending, not broken. This is the state at launch and for the product's
  first year of operation.
- A year-on-year block never estimates, interpolates, or zero-fills the prior-year window. If
  the prior window has data but is thin, the delta is shown with its sample size and a
  "small sample" caveat, not suppressed.
- `unknown`, `other`, null, and unclassified records are not silently converted into a known
  role, title, skill, company, or location. `other`'s own year-on-year trend is never
  presented as a market signal (it tracks sourcing breadth, not the market).
- The story must distinguish "no rows exist" from "rows exist but this field is not yet
  populated".
- The response includes a provenance entry naming the queried platform tables/aggregates and
  explicitly states **"No language model used"**.

### Relationship to the existing experience

This story is a dedicated Query Task named **"What we know about the market"**, placed above
**"Tech market hiring status"** in the Task Panel. Selecting it replaces the working-space
content with the concise briefing. It does not replace the hiring-status task or create a
dashboard. The resulting story is an AI-turn-shaped output so it can use the same Reasoning
Panel and Output Panel reference pattern as other market-health outputs.

## Story 2 - What does employment risk look like across the market?

Added 2026-09-11 — `changes/2026-09-11-employment-events-independent-scope.md`. The first
catalogue entry built from `employment_events` (`changes/2026-09-11-employment-event-ingestion.md`)
rather than `raw_postings`/`classifications` — and, deliberately, **not scoped to the 35
tracked job-posting companies** at all. This is what "Future catalogue direction" (below)
already anticipated as "layoff activity," now concrete.

### Display name

**Employment risk across the market** — the Task Panel item label.

### User question

> What does layoff and hiring activity look like across the market right now?

### Example phrasings
- "Is the market seeing more layoffs or hiring?"
- "What's happening with layoffs right now?"
- "Show me employment risk"

### Audience job

Show a professional **what's happening market-wide** — contraction and expansion signals
across any company or sector the platform's employment-event registries cover — independent
of which 35 companies this platform happens to track job postings for. This is the
company-independent half of Layoff Signal's promise
(`outcomes/understand-market-health-before-searching.md`); the trend chart's events strip
(`design/market-health/experience.md`) remains the tracked-company-scoped half — two
different questions, two surfaces, not one trying to do both.

### Visible answer shape

One movement (no year-on-year split — event data is sparse and recent-news-oriented, not a
12-month-comparable time series the way posting volume is). Trailing 12-month window, fixed
(revised 2026-09-11 from an initial 90 days — `changes/2026-09-11-employment-risk-12-month-window.md`:
a source-registry "event" date and its underlying case's own date can diverge — e.g. UK
Companies House's Streaming API can push a live update about a case that itself started many
months earlier — so a window tied to *when the platform observed* the update would silently
drop real, recently-surfaced events whose underlying date is older; 12 months is wide enough
to absorb that lag while still being a bounded "recent activity" window, not all-time).

1. **Framing line** — one sentence naming what's being summarised, and that this is
   independent of the platform's own tracked companies.
2. **Where it's happening** — subtitle: "Hiring and layoff activity by country, over the
   trailing 12 months." (Added 2026-09-13, `changes/2026-09-13-employment-risk-world-map.md`
   — replaces the former "By country" Ranked bar list and moves to lead the story, since
   *where* is the more natural first question for a market-wide risk view.) A **World risk
   map** (`design/visual-design.md`): every country with a reported event in the window is
   coloured by net direction (more hiring vs. more layoffs), with a legend and a hover tooltip
   giving both totals per country — never just the net figure, since net can hide real
   activity happening in both directions at once.
3. **Contraction vs. expansion** — subtitle: "Share of reported events by direction, over the
   trailing 12 months." **Revised 2026-09-22** (`changes/2026-09-22-nivo-pie-charts.md`) — a
   real 2-slice donut (`SharePieChart`), what share of *events* (not roles) were contraction
   vs. expansion, reusing the World risk map's own semantic colours (`red-600`/`emerald-600`)
   rather than a new guess. Total roles reported affected by contraction events in the window
   is stated as a plain caption line beneath the chart — a magnitude fact, not part of the
   same 2-way proportion, so it stays out of the donut itself.
   *(Corrects this section's earlier "Hero Figure" description — the real implementation
   never built a separate Hero Figure component here; the roles-affected figure was always a
   caption, not a standalone visual.)*
4. **Companies with the most reported impact** — subtitle: "Ranked by jobs reported affected,
   summed across contraction events in the window." (Added 2026-09-11,
   `changes/2026-09-11-data-legibility-market-health.md` — the heading alone didn't state a
   unit; found via real user feedback.) Top 10 companies by roles affected, Ranked bar list.
   `company_raw` as reported (never assumed to be a tracked company). **Revised 2026-09-11**
   (`changes/2026-09-11-employment-risk-hide-placeholder-names.md`) — a source that gives no
   real company name, only a bare id (UK Companies House's Streaming API, so far), is excluded
   from this specific block: a numeric id is never displayed as if it were a company. The
   underlying events still count in every other block (contraction/expansion, by country, by
   sector) — only the name-specific ranking omits them, with an honest qualifier stating how
   many were excluded and why.
5. **By sector** — subtitle: "Jobs reported affected, summed by sector — only events whose
   source reports one." Top sectors by roles affected, Ranked bar list, **only for events whose
   source reports a sector** — the qualifier states what share of events that covers (today:
   Eurofound ERM and some WARN records report it; Companies House never does).

**"By country" as a Ranked bar list — removed 2026-09-13**
(`changes/2026-09-13-employment-risk-world-map.md`), replaced by the World risk map (block 2,
above). The original "Revised 2026-09-11" region-vs-country note still applies to the map:
state-level detail stays deferred, not built in. History preserved here, not deleted, per this
project's own "mark removed, don't erase" convention.

### Data contract

Queries `employment_events` only — **no join to `raw_postings`, no `matched_company` filter**.
This is the one deliberate exception to this catalogue's "platform-owned data" scope being
job-posting data — employment events are platform-owned in the same sense (ingested,
deduplicated, stored) but sourced from external registries, not observed postings.

| Story fact | Aggregate | Required qualifier |
|---|---|---|
| Window | Trailing 12 months from `event_date`, `superseded_by IS NULL` | Stated in the framing line |
| Contraction total | `sum(jobs_affected)` where `direction = 'contraction'` | Roles reported, not roles actually eliminated (some sources don't size every event) |
| Direction split | `count(*)` grouped by `direction` | Event count share, not role-count share — stated explicitly, the two can diverge |
| Top companies | `company_raw` grouped, `sum(jobs_affected)`, events missing a jobs-affected figure excluded from the sum but the qualifier states how many events had no figure | Company names are exactly as the source registry reported them, not normalized |
| By country (World risk map) | `country`, `direction`, grouped, `sum(jobs_affected)` and `count(*)` per (country, direction) pair — no `LIMIT`, every country with data is mapped, not a top-N | Only events with a non-null `country`. `region` (state-level) is deliberately not broken out here — deferred, see the "Revised 2026-09-11" note above. Revised 2026-09-13 (`changes/2026-09-13-employment-risk-world-map.md`) from a single combined total to a per-direction split, so the map can show net hiring vs. net layoff, not just total activity |
| By sector | `sector` grouped, `sum(jobs_affected)` | States the share of in-window events that report a sector at all |
| Sources | `count(distinct source)` + names via `SOURCE_DISPLAY_NAMES` | Every registry that contributed at least one in-window event, named individually — same "name each source" discipline as Story 1's `sources` fact |

### Honesty and empty states

- Same base rules as Story 1 (current as of query time, sample sizes stated, `insufficient_data`
  state per section, never estimated/zero-filled).
- **Never states or implies a causal link between a reported event and any hiring-trend
  figure** — this story doesn't reference `raw_postings` at all, so the risk doesn't arise
  here the way it does for a Layoff Signal chat answer, but the same product-wide rule holds
  if a future revision ever cross-references the two.
- **A `"reported"`-confidence event is never presented with the same certainty as a
  `"confirmed"` one** — if a block's ranking would visibly change confidence composition
  (e.g. one contraction event dominates a region's total and it's `"reported"`, not
  `"confirmed"`), that's disclosed in the block's qualifier, not silently averaged away.
- **Zero events in the window**: the whole story reports `insufficient_data` for every
  section rather than a misleadingly quiet "no employment risk" — genuinely no data is a
  different message from "the market is calm," and this story must not conflate the two.

### Relationship to the existing experience

A dedicated Query Task, placed in the story catalogue like any entry (Task Panel order follows
catalogue document order — this file). Selecting it replaces the working-space content with
this briefing. Does not replace or alter the "Tech market hiring status" task or its events
strip (`design/market-health/experience.md`) — the two surfaces answer different questions and
stay independent, per the resolved Open Question in that spec.

---

## Story 3 - What does an independent market benchmark say?

Added 2026-09-18 — `changes/2026-09-18-market-benchmark-story.md`. The first catalogue entry
built from `market_observations`/`skill_associations` (`backend/specs/scraped-data-sources/api.md`)
— a **third-party benchmark**, not platform-owned postings data, and deliberately never
compared or blended against Story 1's own numbers (that comparison logic is explicitly out of
scope — the two sources measure different populations by different methods; presenting a diff
between them would imply a rigor this platform hasn't earned). This is what
`outcomes/understand-market-health-before-searching.md`'s newest success criterion (added
2026-09-18) asks for: seeing this platform's read *alongside* an independent one, not merged
into it.

### Display name

**Independent market benchmark** — the Task Panel item label.

### User question

> What does an independent market benchmark say about tech hiring demand and pay?

### Example phrasings
- "How does this compare to an outside source?"
- "What does IT Jobs Watch say?"
- "Show me an independent market benchmark"

### Audience job

Give a professional a **second, independent read** on demand and pay for a curated set of
tech roles — sourced from a specialist third-party site, not this platform's own observed
postings — so they can sanity-check the platform's own numbers against an outside source
rather than relying on one dataset alone.

### Visible answer shape

One movement — no year-on-year block yet (each tracked role currently has exactly one observed
period; a comparison needs a second one to exist first, same "not enough history yet" honesty
state Story 1 uses before its own YoY data existed).

1. **Framing line** — one sentence naming this as an independent third-party benchmark, not
   this platform's own postings data. Immediately beneath it, the source's own attribution
   text renders visibly on the page itself (not only in the Reasoning Panel) — "Source: IT
   Jobs Watch (itjobswatch.co.uk)" — satisfying the CC BY-NC-SA 4.0 licence's attribution
   condition wherever this data is actually shown, per `data-legibility`'s Provenance rule.
2. **Demand across tracked roles** — subtitle: "Permanent vacancies currently tracked by IT
   Jobs Watch, by role." Ranked bar list, one row per role currently observed, bar length =
   `vacancy_count`. Qualifier states this covers only the hand-curated roles this platform
   tracks on IT Jobs Watch (`DATA_SOURCES.md` §3b), not the full market, and names how many
   roles are tracked vs. how many currently have an observation (a role added to `ROLE_SLUGS`
   but not yet ingested is a coverage gap, not an error — same "not due yet" honesty as any
   other scraped-source state).
3. **Coverage and pay data availability** — a **Hero Figure + Meter** (the second distinct
   visual form the checklist requires, given this story's data is otherwise a single
   dimension repeated across two rankings): Hero Figure = total permanent vacancies tracked
   across every currently-observed role (`sum(vacancy_count)`); Meter = the share of
   currently-observed roles that have a `salary_median` figure reported ("X of Y tracked
   roles have salary data reported"). Its own caption states the unit inline, no separate
   subtitle needed (Data Legibility, `visual-design.md`).
4. **Typical pay by role** — subtitle: "Advertised salary range by role, most recent period."
   **Revised 2026-09-27** (`changes/2026-09-26-data-story-chart-variety.md`) — a **Range chart**
   (`design/visual-design.md`), one row per currently-observed role, ordered by median
   descending: a whisker spanning the 10th to 90th percentile, a shaded band for the 25th to
   75th, and a dot at the median; every row also states its `salary_sample_size`. This replaces
   the earlier Ranked bar list of the median alone, which showed one point of a real spread the
   platform already stores (`backend/specs/scraped-data-sources/api.md`) — bars from zero also
   made pay differences look bigger than they are.
   **How-to-read line** (Chart accessibility standard): "Each bar spans the middle 80% of
   advertised salaries for that role; the shaded band is the middle 50%; the dot is the
   median." Both this story and `get_market_benchmark`'s MCP response state this wording from
   the same place (`backend/src/data_definitions.py`, key `benchmark.salary.percentiles` — the
   shared-definition mechanism, `design/visual-design.md` — Chart definition pattern), so a
   person reading the chart and an external AI quoting a figure use identical words.
   **Small-sample threshold — decided here:** a role whose `salary_sample_size` is **below 30**
   draws a hollow median dot and its row label gains "small sample"; the legend then adds
   "Hollow dot: fewer than 30 salaries — indicative only." 30 is the smallest sample size
   generally treated as giving a stable percentile estimate — adopted here because this story
   reads a third party's aggregate rows, not raw salaries, so there is no distribution of this
   platform's own to fit a threshold to. `/implement-backend` must check the real
   `salary_sample_size` values against this cutoff and flag back here if the real data makes 30
   clearly wrong for this data set (all roles far above or below it, or a natural break
   elsewhere).
   **Implementation approach — recommendation only, decided at the frontend spec step:** the
   installed Nivo packages (`@nivo/bar`, `@nivo/pie`) have no box-and-whisker form; recommend a
   hand-drawn SVG component, the same precedent as the World risk map, rather than adding a new
   Nivo package for one chart.
   Qualifier states the sample size (already on every row, above) and that a role with no
   `salary_p10`/`salary_p90` on record shows its median dot alone with the caption "range not
   reported" — never an invented or interpolated range.
5. **Skills most associated with these roles** — subtitle: "Summed mention count across the
   tracked roles' vacancies, from IT Jobs Watch's own weighted skill data." Ranked bar list,
   top 10 skills by `job_count` summed across all currently-observed roles. Qualifier states
   this is summed across the hand-curated role set, not a market-wide skill ranking.

**Revised 2026-09-27:** the story now uses 3 distinct visual forms — Ranked bar list (demand,
skills), Hero Figure + Meter (coverage), and Range chart (pay) — up from 2, once the pay block's
own real spread was worth charting. The Ranked bar list still repeats twice (demand, skills);
allowed under the no-repeat rule because both are genuine ranking questions, and the coverage and
pay blocks sit between them so the two repeats are never adjacent. A trend line or map still
doesn't fit this data (demand and pay are each one dimension per role, not a time series or a
geography) — revisit once a second observed period exists and a real year-on-year block becomes
honestly possible.

### Data contract

Queries `market_observations`/`skill_associations` only, filtered to `source = "itjobswatch"`
— no join to `raw_postings`/`classifications`/`employment_events`. Gated on
`source_licences.is_source_usable("itjobswatch")` before any query runs (Business Logic,
`backend/specs/market-health/api.md`).

| Story fact | Aggregate | Required qualifier |
|---|---|---|
| Demand by role | `market_observations` rows for `source='itjobswatch'`, most recent `period_end` per `entity_name` | States the tracked-role set is hand-curated (`DATA_SOURCES.md` §3b), not exhaustive; states how many tracked roles have no observation yet |
| Coverage & pay availability | `count(*)` observed roles vs. `len(ROLE_SLUGS)`; `sum(vacancy_count)`; `count(*) WHERE salary_median IS NOT NULL` | States how many tracked roles are currently observed vs. registered |
| Pay by role | Same rows' `salary_median`, `salary_sample_size` | States the sample size per role; states the full percentile spread exists but isn't charted here |
| Skills | `skill_associations` rows for `source='itjobswatch'`, `job_count` summed per `skill_name` across all currently-observed roles, top 10 | States this is summed across the tracked role set, not a market-wide figure |
| Attribution | `source_licences.get_licence("itjobswatch")` | `attribution_text` rendered visibly in the framing block, always — never omitted, never only in the Reasoning Panel |

### Honesty and empty states

- Same base rules as Stories 1-2 (current as of query time, sample sizes stated,
  `insufficient_data` per section, never estimated/zero-filled).
- **A tracked role with no observation yet** (added to `ROLE_SLUGS` but not yet ingested, or a
  source not yet due for its next run) is simply absent from the ranked lists — never
  backfilled with a guessed value. The qualifier states the count of tracked-but-unobserved
  roles so this reads as a coverage gap, not a hidden one.
- **`is_source_usable("itjobswatch")` returns `False`** (a human has set `rejected=True`
  since this was last checked): every section renders `insufficient_data` with "This data
  source isn't currently available" — never a stale render of previously-fetched rows.
- **Never implies a comparison with Story 1's own numbers** — this story's framing line states
  plainly that this is an independent, separately-sourced read, not a reconciliation. Building
  that comparison is a distinct, not-yet-taken decision (`scraped-data-sources/api.md`'s "What
  this doesn't decide").

### Relationship to the existing experience

A dedicated Query Task, placed after Story 2 in the catalogue (document order). Selecting it
replaces the working-space content with this briefing. Does not alter "Tech market hiring
status" or "What we know about the market" — a fully independent third surface, same
"different questions, different surfaces" discipline as Story 2.

## Story 4 - What roles exist beyond Design, Product Management, and Engineering?

Added 2026-09-21 — `changes/2026-09-21-job-function-story.md`. The first catalogue entry built
from `classifications.job_function` (`job-classification.md` — Job Function, added the same
day). Real production data shows roughly half of all classified postings fall outside the 3
tracked Role Categories — until this story, that half had no breakdown at all beyond the bare
label `other`. **Job Function is never a fourth tracked Role Category** — this story exists
specifically to describe what's genuinely outside Design/Product Management/Engineering, never
to widen what those three mean or to appear in the trend chart's own 3-line split.

**Display relabel, added 2026-09-22** (`changes/2026-09-22-role-category-display-relabel.md`):
"Design" / "Product Management" / "Engineering" is the display-only occupation-family name for
what's stored as `role_category` values `"Designer"` / `"Product Manager"` / `"Engineer"` —
the underlying value is unchanged everywhere; only what a user reads changed.

### Display name

**Beyond Design, Product & Engineering** — the Task Panel item label.

### User question

> What roles exist beyond Design, Product Management, and Engineering?

### Example phrasings
- "What else are these companies hiring for?"
- "Show me the wider workforce breakdown"
- "What jobs aren't Design, Product Management, or Engineering?"

### Audience job

Show a professional **what a tracked company's hiring actually looks like in full** — not just
the tracked slice. A company's real hiring posture (aggressive commercial expansion vs. lean
operations, say) often shows up more in its Sales/Marketing/Ops volume than in its Engineering
count alone; this story makes that visible instead of silently discarding it as `other`.

### Visible answer shape

One movement — no year-on-year block yet (Job Function is brand new; there is no prior-year
window to compare against, same "not enough history yet" honesty state Stories 1 and 3 use
before their own YoY/second-period data existed).

1. **Framing line** — one sentence naming this as the picture beyond the 3 tracked categories,
   never a reconciliation or a fourth category.
2. **What the wider hiring picture looks like** — subtitle: "Postings outside Design, Product
   Management, and Engineering, by function." **Revised 2026-09-27**
   (`changes/2026-09-26-data-story-chart-variety.md`) — a **Treemap** (`design/visual-design.md`),
   one tile per Job Function (`job-classification.md`'s closed set), tile area = posting count,
   each tile labelled with its name, count and share. This replaces the Ranked bar list: with
   around a dozen functions and some long names ("Sales & Business Development"), a
   part-to-whole treemap shows how big a slice each one is at a glance, which a ranked list of
   similar-length bars does not.
   **How-to-read line** (Chart accessibility standard): "Tile size shows each function's share
   of postings outside the 3 tracked categories."
   **Tail handling — decided here:** a Job Function holding **less than 3%** of the
   outside-the-3-categories total merges into one hollow-outlined, dashed-border aggregate tile
   labelled "{N} smaller functions" (naming which ones in its tooltip and the table view).
   **`unknown`** (a posting confidently outside the 3 tracked categories whose title doesn't
   disclose its function) never merges into that aggregate — it is always its own real,
   hollow-outlined (solid border) tile, per the existing rule that `unknown` is never hidden or
   folded away. 3% was chosen so the aggregate only catches genuinely marginal functions, not one
   that's simply smaller than Sales or an Engineering-adjacent function; `/implement-backend`
   should confirm against the real function-count distribution and flag back here if 3% merges
   more or fewer functions than intended.
   Qualifier states how many of the `other` population currently have a Job Function assigned vs.
   how many are still awaiting reprocessing (see Honesty and empty states, below — a real,
   current lag, not hidden).
3. **How much of all hiring this actually is** — subtitle: "All classified postings, split by
   whether they're inside or outside the 3 tracked categories." **Revised 2026-09-22**
   (`changes/2026-09-22-nivo-pie-charts.md`) — a real 2-slice donut (`SharePieChart`, the
   second distinct visual form), outside vs. inside the 3 tracked categories; the real
   counts and percentage are stated as a plain caption line beneath the chart. *Meaning:* the
   trend chart and Story 1 only ever show the tracked slice — this quantifies how much of real
   hiring that slice actually represents.
4. **Most common titles in {largest function}** — subtitle names the actual largest Job
   Function found (e.g. "Most common titles in Sales & Business Development"). Ranked bar
   list of real, un-normalized job titles within that one function, top 10. *Meaning:* gives
   real texture to a function label — what it actually contains, not just its name.

**Revised 2026-09-27:** the story now uses 3 distinct visual forms — Treemap (the function
breakdown), 2-slice donut (scale), and Ranked bar list (top titles) — up from 2, once a
part-to-whole form replaced the function breakdown's own Ranked bar list. Job Function data is
still one dimension (a count per function), so no time series or geography exists yet to justify
a trend line or map — same judgment call as Story 3.

### Data contract

Queries `classifications`/`raw_postings` only — platform-owned data, no LLM, no join to
`market_observations`/`skill_associations` (a different data source, Story 3's own scope).

| Story fact | Aggregate | Required qualifier |
|---|---|---|
| Job Function breakdown | `classifications` grouped by `job_function` where `role_category = 'other'`, `job_function IS NOT NULL` | States how many `other` postings have a Job Function assigned vs. how many are still awaiting reprocessing |
| Scale | `count(*) WHERE role_category = 'other'` vs. `count(*)` (all classified) | States this is a share of *all* classified postings, not just tracked companies |
| Top titles in largest function | `raw_postings.title` grouped, filtered to the single largest Job Function found this query, top 10 | Real title text, not normalized — same discipline as Story 1's own title/specialization fact |

### Honesty and empty states

- Same base rules as Stories 1-3 (current as of query time, sample sizes stated,
  `insufficient_data` per section, never estimated/zero-filled).
- **A real, current lag, stated plainly, not hidden**: as of this story's addition, the
  2026-09-21 taxonomy revision's reclassification backlog is still draining
  (`changes/2026-09-21-fold-reprocessing-into-ingest.md`) — a real share of `other` postings
  genuinely have `job_function IS NULL` right now because they haven't been reprocessed onto
  the current taxonomy version yet. Every section states this as a real backlog still
  draining, never presented as if the picture were already complete.
- **Job Function is never conflated with `role_category`** — this story never claims a Job
  Function value for a Designer/Product Manager/Engineer posting, and never presents Job
  Function as if it were a 4th value of `role_category` anywhere in its language.
- **`unknown`** (a posting confidently outside the 3 tracked categories, but whose function the
  title doesn't disclose) is its own real row in the breakdown, never hidden or folded into
  "Other Non-Tech."

### Relationship to the existing experience

A dedicated Query Task, placed after Story 3 in the catalogue (document order). Selecting it
replaces the working-space content with this briefing. Does not alter the trend chart, Story 1,
Story 2, or Story 3 — a fully independent fourth surface, same "different questions, different
surfaces" discipline as every prior story.

## Story 5 - What does official UK data say about job vacancies?

Added 2026-09-24 — `changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md`, for
`outcomes/job-data-source-flexibility.md` (trusted external statistics) and
`outcomes/understand-market-health-before-searching.md`. The first catalogue entry built from
the **trusted external statistics** category (`backend/specs/trusted-statistics/api.md`) — the
Office for National Statistics' Vacancy Survey. It is a **new story, not an extension of Story
3**: Story 3 is one specialist website's ranking for a hand-picked set of IT roles and never
blends with platform numbers; this is an economy-wide, official estimate by industry and by
business size. Different publisher, different population, different question — merging them
under one heading would mix two populations.

It is also the first story that puts a **platform figure beside an outside figure**. That is
allowed here, under strict rules (see the third movement and "Honesty and empty states"): two
labelled, separately-sourced values; never a difference, a score, or a verdict; and only on a
dimension where an honest mapping exists (industry — yes; employer size — **not yet**, because
this platform's size bands and the official ones don't line up).

### Display name

**UK vacancies (official data)** — the Task Panel item label.

### User question

> What does official UK data say about job vacancies by industry and company size?

### Example phrasings
- "How many job vacancies are there in the UK?"
- "What does the ONS say about vacancies?"
- "Which industries have the most vacancies?"
- "How does this compare with official figures?"
- "Are tech vacancies going up or down in the UK?" *(added 2026-09-26)*
- "How are technology and communications jobs doing compared with the whole market?" *(added 2026-09-26)*

### Audience job

Give a professional the **wider, official picture** — how many vacancies the UK economy has,
where they are, how that is shifting — and let them see how the roles this platform tracks sit
against it, so they can judge how far this platform's own view leans (towards technology and
finance employers, for instance) before relying on it. A second, authoritative read — always
named as such.

### Visible answer shape

Three labelled movements (an extension of the standard's two — see "Visual standard", above,
amended for this story): **the UK market right now**, **how it's shifting**, and **how this
compares with the roles we track**.

1. **Framing line** — one sentence: official estimates of UK job vacancies from the Office for
   National Statistics, for the three months to {Month Year}, covering the whole UK economy
   rather than only the roles this platform tracks. Immediately beneath it, the attribution
   text renders visibly on the page itself, never only in the Reasoning Panel: "Source: Office
   for National Statistics — Vacancy Survey. Contains public sector information licensed under
   the Open Government Licence v3.0." (read from the licence registry, not typed into the
   story). If the latest figure is provisional, a short muted line says so ("This is a first
   estimate and may be revised.").

**Movement 1 — The UK market right now**

2. **UK job vacancies** — a **Hero Figure**: the total estimated vacancies for the latest three
   months (e.g. "702,000"), caption "estimated job vacancies, three months to Aug 2026", and one
   plain line beneath with the change since the previous non-overlapping three months, in words
   with a direction glyph ("▼ 8,000 fewer than the three months to May 2026 (−1.1%)"). No
   separate subtitle — the caption states the unit. *Qualifier:* it is an estimate from a
   monthly survey of businesses; the latest figure is provisional; it leaves out farming,
   forestry and fishing, households employing staff, and employment agencies; and the survey covers
   Great Britain, which the publisher scales up to the whole UK.
3. **Vacancies by industry** — subtitle: "Estimated vacancies by industry, in thousands, three
   months to Aug 2026." **Ranked bar list**, the 10 largest of the 18 industry groups, bar
   length = vacancies. *Qualifier:* industry groups follow the official UK classification;
   the 8 smaller groups are not shown.
4. **Vacancies by size of business** — subtitle: "Share of all vacancies, by how many people
   the employing business has." **Revised 2026-09-27**
   (`changes/2026-09-26-data-story-chart-variety.md`) — an **Ordered columns** chart
   (`design/visual-design.md`), five columns left to right from the smallest business size to
   the largest (1–9, 10–49, 50–249, 250–2,499, 2,500 or more employees — never sorted by value,
   because the order *is* the meaning), column height = share, the count in thousands labelled
   beneath each column's share value. This replaces the Ranked bar list: a ranked list's own
   form implies sorting by value, which this fixed order deliberately isn't, so a size-ordered
   column chart says directly what the ranked-list version only said through a caveat.
   *Qualifier:* business size means the number of people the business employs, not how big the
   vacancy is.

**Movement 2 — How it's shifting**

Movement 2 now reads long view first, then the latest year: block 4a shows how one industry group
has moved over the whole published history, block 5 zooms in on the last twelve months across
all industries. A reader goes from "how big is it" (blocks 2–4) → "how did it get here" (4a) →
"what changed lately" (5) → "how do our roles sit against it" (6).

4a. **Tech and communications vacancies since 2001** — a **trend line** (two lines on one
   scale). *Added 2026-09-26 — `changes/2026-09-26-story-5-tech-lens.md`, for a tech professional
   who wants the official picture for their own field. Numbered 4a so that blocks 5 and 6, which
   another change is editing, keep their numbers; renumber once both changes have landed.*
   - **Heading:** "Tech and communications vacancies since 2001".
   - **Subtitle:** "The official group closest to tech — software and IT services, plus telecoms,
     publishing and broadcasting. Estimated vacancies, three-month averages from Apr–Jun 2001 to
     Jun–Aug 2026, adjusted for the time of year. Each line is scaled so the three months to Aug
     2019 = 100." (The adjustment wording comes from what the publisher states for each series,
     never assumed; the "2019" months are the same months as the latest period.)
   - **The chart:** two lines over the whole published history. **Solid line** — information and
     communication, the official name for that group. **Dashed line** — all industries. Both are
     shown as an index so they share one scale (a group of ~40 thousand vacancies and a market of
     ~700 thousand cannot honestly share an axis in thousands, and two axes are never used). The
     vertical scale is labelled "Index (Jun–Aug 2019 = 100)", runs from 0 to 200, and
     the 100 line is marked "2019 level". The horizontal scale shows years. Colour is never the
     only difference between the lines — one is solid and one is dashed.
   - **Direct labels:** each line is labelled at its right-hand end with its name and latest value
     — "Information and communication 84 (36 thousand vacancies)" and "All industries 85 (702
     thousand vacancies)". On a narrow panel these move into the legend line.
   - **Two marked points, on the solid line only:** its **highest point** ("Highest: Apr–Jun
     2022, 78 thousand") and its **latest point** ("Latest: Jun–Aug 2026, 36 thousand"). Nothing
     else is annotated — no shaded bands or event labels, because a cause is not in this data and
     the story never asserts one. If the latest figure is provisional, its point is drawn hollow.
   - **Legend line (always shown, above the chart):** "Solid line: information and communication.
     Dashed line: all industries. Above 100 means more vacancies than in the three months to Aug
     2019; below 100 means fewer." When the latest point is provisional it adds "Hollow point:
     first estimate, may be revised."
   - **Hover / keyboard:** hovering, or stepping with the left and right arrow keys (the chart is
     one tab stop; Home and End jump to the first and latest period), shows one tooltip for that
     period naming the period in words and both lines — "Three months to Aug 2022 — Information
     and communication: 68 thousand vacancies (index 158) · All industries: 1,257 thousand
     (index 151)" — plus "first estimate" or "revised" where the publisher flags it. The focused
     period has a visible marker.
   - **For assistive technology:** the chart carries a one-sentence label — "Line chart of
     estimated UK job vacancies in information and communication and in all industries, as an index
     where Jun–Aug 2019 = 100, from Apr–Jun 2001 to Jun–Aug 2026." — and stepping through periods
     with the keyboard announces the same text the tooltip shows. Chart text is at least 12px and
     small text uses the lighter grey required by the Chart accessibility standard
     (`design/visual-design.md`); the lines, markers, labels and keyboard behaviour follow that
     file's **Time series** entry, which this block is the worked example for.
   - **One plain sentence beneath the chart**, facts only,
     no verdict word ("boom", "slump", "recovery"): "Information and communication stands at 84
     (36 thousand vacancies) and all industries at 85 (702 thousand), where 100 is the three
     months to Aug 2019. The group's highest point was Apr–Jun 2022, at 78 thousand."
   - **View as table:** a "Show as table" control beneath the sentence, collapsed by default —
     one row per year for the same three months as the latest period (Jun–Aug), columns: period,
     information and communication (thousand vacancies), all industries (thousand vacancies),
     and each one's index, under a caption naming the window and units ("Estimated vacancies in
     thousands and index, Jun–Aug of each year, 2001 to 2026"). The chart and the table always
     show the same numbers.
   - **Qualifier (two short lines, both always shown):** "Information and communication is the
     closest official group to tech, but it is broader — it also covers telecoms, publishing, film,
     TV and radio, alongside software and IT services. Engineering and research roles are counted
     in a different group (professional, scientific and technical activities)." / "Estimates are
     published in whole thousands, so small moves in a group this size are within rounding. The
     survey leaves out employment agencies." When the latest point is provisional a third short
     line adds "The latest figure may be revised."
   - **Loading:** a same-size placeholder shows while the chart loads; the sentence and qualifier
     do not wait on it. **Empty:** see "Honesty and empty states" — never an empty axis.

5. **Which industries are changing** — **Revised 2026-09-27**
   (`changes/2026-09-26-data-story-chart-variety.md`) — **Diverging change bars**
   (`design/visual-design.md`), replacing the grouped-bar year-on-year comparison this block used
   before: the real question here is "how much did it move," not "what were the two levels," so
   the change itself carries the point instead of a reader subtracting two bars. Subtitle:
   "Change in estimated vacancies by industry, in thousands: three months to Aug 2026 vs. the
   same three months a year earlier." One indigo-500 bar per industry, either side of a labelled
   zero line ("No change"), the 8 industries with the most vacancies now, ordered by the size of
   the change (the largest rise at the top). Each bar ends in its signed change with a ▲ / ▼ / –
   glyph and the unit spelled out ("▲ +6 thousand") — colour never carries direction alone.
   Legend: "Right of the line: more vacancies than a year earlier. Left: fewer." Both period
   labels are stated in words above the chart, as before. One plain sentence beneath states what
   a shift means: "A drop can mean slower hiring or roles being filled faster — this shows the
   change, not the reason." *Qualifier:* both periods are official estimates; the newer one may
   be revised. The two source levels behind each bar's change are in the tooltip and the table,
   never drawn as a second bar.

**Movement 3 — How this compares with the roles we track**

6. **Where our roles sit against the UK market** — a **two-series comparison** (grouped
   horizontal bars, one row per industry group). Subtitle: "Share of the UK-based roles we
   track, and share of all UK vacancies, by industry group." A legend names both series: "Solid
   bar: roles we track — share of {n} UK-based roles we hold as of {date}. Lighter bar: UK
   vacancies — share of all vacancies, official estimate for Jun–Aug 2026." Rows: the five
   industry groups with the most UK vacancies, plus any group holding at least 5% of the roles
   we track (up to 8 rows), plus a final row **"Not placed in an industry group"** carrying only
   the platform side. *Qualifier (always shown):* "These are not expected to match. The official
   figures estimate vacancies across the whole UK economy from a business survey; we track
   hiring at a chosen set of employers, most of them technology and finance companies. This
   shows how our view leans — not whether either one is right." A second qualifier line states
   the coverage gap: "{x} of {n} UK-based roles are at employers whose industry we couldn't place
   in a group."

**Revised 2026-09-27:** the story now uses **six** distinct visual forms, each chosen for the
shape of its own question, with no repeat: Hero Figure (block 2), Ranked bar list (block 3, the
story's only ranking question), Ordered columns (block 4, an ordered scale), Time series (block
4a, added 2026-09-26 — movement over 25 years), Diverging change bars (block 5, a one-year
change), and Two-series comparison (block 6, two sources side by side). It never repeats the
welcome's current-snapshot figures (the platform's own job count, company count, or current role
split) — the only platform figure it shows is the industry *share* in block 6, which is a
different question (how our sample leans against an outside reference).

### Data contract

Reads trusted statistics only through `query_trusted_statistics_data` (never the tables
directly) and the platform's own postings only inside `statistics_crosscheck.industry_mix()`
(`backend/specs/trusted-statistics/api.md`). No LLM. Gated on
`source_licences.is_source_usable("ons_vacancy_survey")` before any query runs.

| Story fact | Aggregate | Required qualifier |
|---|---|---|
| Total vacancies + change | Latest-vintage `AP2Y` value for the latest period; the value for the period three months earlier (non-overlapping) for the change | Estimate; provisional flag stated; sectors excluded; period stated in words |
| By industry | Latest-vintage 18 SIC-section series for the latest period, top 10 | States 8 groups are not shown; classification named in the Reasoning Panel, not the visible copy |
| By business size | Latest-vintage five size-class series, shown as shares of `AP2Y`, in size order | States what "size" means |
| Tech and communications over time *(block 4a, added 2026-09-26)* | Latest-vintage series for SIC section J (information and communication) and `AP2Y` (all industries), **every** period from the first published (Apr–Jun 2001) to the latest; each value divided by that series' own value for the same months in 2019 (× 100) to give the index; the value in thousands kept alongside; the series' highest point and its latest point picked from the same data | Names the group's breadth (telecoms, publishing, broadcasting as well as software and IT); whole-thousand rounding; employment agencies left out; base period stated in words; provisional flag on the latest point; adjustment status from the stored field |
| Year-on-year | Same series, latest period vs the same period one year earlier; both stated in words | Both periods official estimates; newer may be revised |
| Comparison | Platform side: share of UK-located postings by industry group via the versioned crosswalk; ONS side: share of the all-industries total | Not expected to match; how many roles are unplaced; dates and denominators for both sides |
| Attribution | `source_licences.get_licence("ons_vacancy_survey").attribution_text` | Rendered visibly in the framing block, always |

### Honesty and empty states

- Same base rules as Stories 1-4 (current as of query time, denominators stated,
  `insufficient_data` per section, never estimated or zero-filled).
- **Not collected yet** (the ingestion has not run against the published files): every section
  renders "We haven't collected the official UK figures yet." This is an expected, temporary
  state, not an error — and never a stale or invented number. After the first collection, the
  story updates whenever the Office for National Statistics publishes its next monthly release;
  a newer release simply shows newer figures. (Lag statement required by `data-surface-review`.)
- **`is_source_usable("ons_vacancy_survey")` returns `False`** (a human has set `rejected=True`):
  every section renders "This data source isn't currently available." — never a stale render.
- **A rejected release** (the parser refused a file it didn't recognise) leaves the previously
  stored figures showing, with their own dates — the story states the period it is showing, so
  an older period is visibly older, never passed off as current.
- **Seasonal adjustment is stated, not assumed.** The industry figures are seasonally adjusted (a few
  series are footnoted by the publisher as not adjusted); the size-of-business figures are described as
  seasonally adjusted in the publisher's methodology notes, though not in the data file itself. Block 4's
  qualifier says which, in plain words, rather than silently treating the two sets as identical.
- **The survey behind these figures covers Great Britain**, and the publisher scales it up to the whole
  UK (Northern Ireland is about 3% of UK employment). Block 2's qualifier says so — "UK" in this story
  means the publisher's own UK estimate, not a UK-wide survey.
- **Provisional figures** are flagged in words (framing line). Revisions are never announced in
  this story; the newest value simply shows.
- **Block 4a — the tech lens is a stand-in, and says so** *(added 2026-09-26)*. The official
  statistics have no "technology" group; information and communication is the closest, and it is
  broader (the Reasoning Panel names its parts: publishing; film, video, TV, sound and music
  production; programming and broadcasting; telecoms; computer programming and consultancy;
  information services). The block therefore always shows the official group name in its legend,
  always carries the breadth qualifier, and no copy anywhere calls the line "tech vacancies" or
  "technology jobs" as a plain fact.
- **Block 4a — never a verdict, never a cause.** The sentence beneath the chart states levels,
  index values and the highest point, and nothing else: no direction words such as "boom",
  "slump", "recovery" or "outperforming", no reason for any movement, no annotation of outside
  events. Both lines come from the same publisher, so showing them together is allowed; the block
  still shows no gap, ratio or score between them.
- **Block 4a — index basis.** The 100 mark is the same months in 2019 as the latest period, for
  each line separately. If that 2019 value is missing for either series, or fewer than 24 monthly
  periods exist, the block renders "We don't have enough official history to draw this yet." —
  never a shortened or re-based chart. A gap in the series (none exists today) breaks the line;
  it is never joined across or filled in.
- **Block 4a — small numbers.** A group of this size is published as whole thousands, so single
  months can move by a thousand or two on rounding alone; the qualifier says so, and the
  sentence never states a change between adjacent months.
- **Block 4a — adjustment status** is read from each series' stored status. If the two series
  differ, or either is unadjusted, the subtitle says so in words instead of "adjusted for the time
  of year".
- **A cross-check is context, not proof.** The story never states or implies that the platform
  is "accurate", "biased", or "validated" by the official figures, never shows a difference or
  a score between the two series, and never uses colour to imply one side is right. The
  comparison block is shown only for **industry**. A size comparison is **deliberately absent**:
  this platform's employer size bands don't line up with the official ones, and inventing a
  match would be worse than showing none (follow-up tracked in the backend spec's Open
  Questions).
- **No UK-based roles** (or none placed in an industry group): block 6 renders "We don't hold
  enough UK-based roles to compare yet." — the first five blocks still render.
- **Provenance of the platform side** (block 6) is named as "roles we track" — never presented
  as the market. The Reasoning Panel lists both sources, the crosswalk version, and the
  unplaced-role count.

### Relationship to the existing experience

A dedicated Query Task, placed after Story 4 in the catalogue (document order). Selecting it
replaces the working-space content with this briefing. It appears in the Task Panel and the
Welcome's shortcut list automatically (catalogue rule) — no navigation or IA change. Does not
alter the trend chart or Stories 1-4. Story 3 (IT Jobs Watch) is unchanged and remains a
separate, independent benchmark; the two are never blended or diffed against each other.

## Future catalogue direction

Later entries can cover narrower questions such as role demand, skills by specialization,
compensation coverage, source coverage, or market changes over time — **layoff activity is
now Story 2**, **an independent third-party benchmark is now Story 3**, **what's beyond the
3 tracked categories is now Story 4**, and **official UK vacancy statistics (with an
industry cross-check) are now Story 5**, all above, no longer future directions. **Every
one must meet "Visual standard every story must meet" (above)** — a new entry that can't be
composed into 3–6 heading/visual/qualifier blocks with a real mix of chart forms is a sign
the question is too narrow or too broad to be a story, not a reason to relax the standard. A
question well suited to a single number or a single list is better answered by the curated
instant-answer engine (`backend/specs/market-health/api.md`) than dressed up as a story.

New ingestion types (company websites, layoff portals, papers, and other sources) add source
adapters and source-specific aggregates; they do not change the meaning of this story's
source-aware contract. A future story may use those sources only after its own data contract
defines what they can support and how provenance is shown.