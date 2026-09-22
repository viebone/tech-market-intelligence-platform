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
      Figure, Stat Tile, Meter, Category Share Bar, Trend line, Year-on-year comparison, and
      — added 2026-09-22, `changes/2026-09-22-nivo-charting-library.md` — a real Nivo chart
      where a genuine multi-series comparison says more than a ranked list can). A story that
      is five ranked bar lists in a row is under-composed.
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

A short intro line names the two windows in plain words. Each block below is a **Year-on-year
comparison** (`design/visual-design.md`) — subtitle: "Share of postings by {dimension}, this
year vs. the year before" — with one "what this means" sentence and, once a comparison is
available, a real grouped bar chart (`YearOnYearGroupedBars`, **revised 2026-09-22** —
`changes/2026-09-22-nivo-charting-library.md` — replaces the original hand-rolled ghost-bar
comparison) with an explicit legend naming the two bars (indigo = now, muted gray = a year
ago — Data Legibility, `visual-design.md`). **At launch and for the product's first year all
three are in the "no prior window yet" state** — current window only + "comparison starts
{Month Year}", no legend needed (only one colour is on screen).

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
4. **Typical pay by role** — subtitle: "Median annual salary (50th percentile), by role."
   Ranked bar list, bar length = `salary_median`, formatted as currency. Qualifier states the
   salary sample size per role and that the median alone understates the real spread — the
   full 10th-90th percentile range is available in the platform's own stored data
   (`backend/specs/scraped-data-sources/api.md`) but not charted here, to keep this block to
   one visual form per the Visual standard checklist.
5. **Skills most associated with these roles** — subtitle: "Summed mention count across the
   tracked roles' vacancies, from IT Jobs Watch's own weighted skill data." Ranked bar list,
   top 10 skills by `job_count` summed across all currently-observed roles. Qualifier states
   this is summed across the hand-curated role set, not a market-wide skill ranking.

This story leans on 2 distinct visual forms (Ranked bar list, Hero Figure + Meter) rather than
3+ — a deliberate judgment call given the data's real shape (demand and pay are each
fundamentally one dimension per role; forcing a trend line or map here would mean inventing a
time series or geography this data doesn't actually have yet). Revisit once a second period of
data exists and a real year-on-year block becomes honestly possible.

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
   Management, and Engineering, by function." Ranked bar list, one row per Job Function
   (`job-classification.md`'s closed set), bar length = posting count. Qualifier states how many
   of the `other` population currently have a Job Function assigned vs. how many are still
   awaiting reprocessing (see Honesty and empty states, below — a real, current lag, not
   hidden).
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

This story leans on 2 distinct visual forms (Ranked bar list, Hero Figure + Meter), same
deliberate judgment call as Story 3 — Job Function data is currently one dimension (a count per
function), no time series or geography exists yet to justify a trend line or map.

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

## Future catalogue direction

Later entries can cover narrower questions such as role demand, skills by specialization,
compensation coverage, source coverage, or market changes over time — **layoff activity is
now Story 2**, **an independent third-party benchmark is now Story 3**, and **what's beyond the
3 tracked categories is now Story 4**, all above, no longer future directions. **Every
one must meet "Visual standard every story must meet" (above)** — a new entry that can't be
composed into 3–6 heading/visual/qualifier blocks with a real mix of chart forms is a sign
the question is too narrow or too broad to be a story, not a reason to relax the standard. A
question well suited to a single number or a single list is better answered by the curated
instant-answer engine (`backend/specs/market-health/api.md`) than dressed up as a story.

New ingestion types (company websites, layoff portals, papers, and other sources) add source
adapters and source-specific aggregates; they do not change the meaning of this story's
source-aware contract. A future story may use those sources only after its own data contract
defines what they can support and how provenance is shown.