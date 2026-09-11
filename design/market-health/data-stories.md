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
      Figure, Stat Tile, Meter, Category Share Bar, Trend line, Year-on-year comparison). A
      story that is five ranked bar lists in a row is under-composed.
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
- [ ] **No *current-snapshot* duplication of the welcome** — job count, company count,
      collection start, and the *current* role-category split all belong to "About this
      platform". A story may show a *year-on-year shift* in the same dimension (a different
      question — change, not state); it never repeats the welcome's current figures as-is.
- [ ] No visible source-adapter names, database fields, query names, model names, or
      extraction mechanics — those stay in the Reasoning Panel.
- [ ] Engaging by composition only — no entrance animation on the data
      (`visual-design.md` — Motion, unchanged).

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
3. **What employers ask for** — subtitle: "Postings mentioning each skill group." Top skill
   groups, Ranked bar list, must-have rows emphasised (full-opacity hue), with its existing
   inline caption "Solid bars are must-have mentions" as the opacity legend.
4. **Pay transparency** — a **Hero Figure + Meter**: the share of postings that state a salary
   (structured + parsed), "the rest don't disclose" stated plainly. The story's one Hero
   Figure. The Meter's own caption already states the unit inline — no separate subtitle
   needed (Data Legibility, `visual-design.md`).
5. **Where the roles are** — subtitle: "Open postings currently tracked, by city." Top
   locations (country or city), Ranked bar list, with the "only N postings have a normalised
   location" caveat.

**Movement 2 — "How it's shifting" (year on year)**

A short intro line names the two windows in plain words. Each block below is a **Year-on-year
comparison** (`design/visual-design.md`) — subtitle: "Share of postings by {dimension}, this
year vs. the year before" — with one "what this means" sentence and, once a comparison is
available, a legend naming the two bar colours (lighter = a year ago, solid = now — Data
Legibility, `visual-design.md`). **At launch and for the product's first year all three are in
the "no prior window yet" state** — current window only + "comparison starts {Month Year}",
no legend needed (only one colour is on screen).

6. **How the role mix is shifting** — subtitle: "Share of postings by role category, this year
   vs. the year before." `role_category` shares over the **three tracked areas only** (Designer
   / Product Manager / Engineer), matching the trend chart and the welcome's Category Share
   Bar. `other` / `unknown` are coverage, not rows here, and their own trend is never a
   signal. *Meaning:* which of the three areas is taking a bigger or smaller slice of new
   roles.
7. **How seniority is shifting** — subtitle: "Share of postings by seniority level, this year
   vs. the year before." `level` shares across the ladder. *Meaning:* whether the market is
   opening more junior or more senior roles than a year ago.
8. **IC vs. management** — subtitle: "Share of postings by track, this year vs. the year
   before." `track` shares (`ic` / `management`; `unknown` excluded). *Meaning:* whether more
   of the new roles are for people who lead teams or do the work.

Every block keeps its honesty qualifier (sample size, coverage caveat, both window dates for
Movement 2). A block with too little data shows its "not enough data yet" line, not an empty
chart. Which job boards the data came from is provenance — Reasoning Panel, not a visible
block.

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
  enough data yet": the current window *does* have data and *is* shown (as a plain share bar
  / ranked list, no ghost bar, no delta column). Only the comparison is unavailable, and the
  block says so plainly — "Year-on-year comparison starts {Month Year}. Tracking since {date}."
  It reads as pending, not broken. This is the state at launch and for the product's first
  year of operation.
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
2. **Contraction vs. expansion** — a **Hero Figure + Meter**: total roles reported affected by
   contraction events (layoff/closure/restructuring/bankruptcy/offshoring) in the window (Hero
   Figure), with a Meter showing what share of *events* (not roles) were contraction vs.
   expansion. The Meter's own caption already states the unit inline ("of reported events were
   contraction…") — no separate subtitle needed (Data Legibility, `visual-design.md`).
3. **Companies with the most reported impact** — subtitle: "Ranked by jobs reported affected,
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
4. **By country** — subtitle: "Jobs reported affected, summed by country, over the trailing 12
   months." Every country with a reported event, ranked by roles affected, Ranked bar list.
   **Revised 2026-09-11** (`changes/2026-09-11-employment-risk-country-dimension.md`) —
   originally specified as region (US state, or country for non-US sources), which conflated
   two different granularities into one ranking the moment a second country's data existed.
   State-level detail is deferred (still stored in `region`, not dropped), not built into this
   block.
5. **By sector** — subtitle: "Jobs reported affected, summed by sector — only events whose
   source reports one." Top sectors by roles affected, Ranked bar list, **only for events whose
   source reports a sector** — the qualifier states what share of events that covers (today:
   Eurofound ERM and some WARN records report it; Companies House never does).

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
| By country | `country`, grouped, `sum(jobs_affected)` | Only events with a non-null `country`. `region` (state-level) is deliberately not broken out here — deferred, see the "Revised 2026-09-11" note above |
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

## Future catalogue direction

Later entries can cover narrower questions such as role demand, skills by specialization,
compensation coverage, source coverage, or market changes over time — **layoff activity is
now Story 2, above**, no longer a future direction. **Every
one must meet "Visual standard every story must meet" (above)** — a new entry that can't be
composed into 3–6 heading/visual/qualifier blocks with a real mix of chart forms is a sign
the question is too narrow or too broad to be a story, not a reason to relax the standard. A
question well suited to a single number or a single list is better answered by the curated
instant-answer engine (`backend/specs/market-health/api.md`) than dressed up as a story.

New ingestion types (company websites, layoff portals, papers, and other sources) add source
adapters and source-specific aggregates; they do not change the meaning of this story's
source-aware contract. A future story may use those sources only after its own data contract
defines what they can support and how provenance is shown.