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
- [ ] **Blocks**, each: a fixed heading → **one** chart or figure → its honesty qualifier
      (sample size / coverage caveat). No prose-only block except the framing line. **3–6
      blocks** for a single-theme story; a story that covers both current state and
      year-on-year change groups its blocks into **two labelled movements** ("the market
      right now", then "how it's shifting") and may run to ~8.
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
      back — never more), states both date ranges in words, and carries one plain sentence on
      what a shift in that mix means. Before ~13 months of data exists it shows the current
      window only + a muted "comparison starts {Month Year}" line — "coming soon", not an
      error (`visual-design.md` — Year-on-year comparison; Honesty and empty states, below).
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
2. **The roles being hired** — top 10 specializations (normalised roles such as "Machine
   Learning Engineer", "Security Engineer"), as a **Ranked bar list**. Once a year-earlier
   window exists, each row also carries its "+N pp" year-on-year delta; until then the delta
   column is absent. Specialization, not raw title (too fragmented); `unknown`/`other`
   excluded, not relabelled.
3. **What employers ask for** — top skill groups, Ranked bar list, must-have rows emphasised.
4. **Pay transparency** — a **Hero Figure + Meter**: the share of postings that state a salary
   (structured + parsed), "the rest don't disclose" stated plainly. The story's one Hero
   Figure.
5. **Where the roles are** — top locations (country or city), Ranked bar list, with the "only
   N postings have a normalised location" caveat.

**Movement 2 — "How it's shifting" (year on year)**

A short intro line names the two windows in plain words. Each block below is a **Year-on-year
comparison** (`design/visual-design.md`) with one "what this means" sentence. **At launch and
for the product's first year all three are in the "no prior window yet" state** — current
window only + "comparison starts {Month Year}".

6. **How the role mix is shifting** — `role_category` shares (Designer / Product Manager /
   Engineer; `other` shown as context, its own trend never presented as a signal). *Meaning:*
   which of the three areas is taking a bigger or smaller slice of new roles.
7. **How seniority is shifting** — `level` shares across the ladder. *Meaning:* whether the
   market is opening more junior or more senior roles than a year ago.
8. **IC vs. management** — `track` shares (`ic` / `management`; `unknown` excluded).
   *Meaning:* whether more of the new roles are for people who lead teams or do the work.

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

## Future catalogue direction

Later entries can cover narrower questions such as role demand, skills by specialization,
compensation coverage, source coverage, layoff activity, or market changes over time. **Every
one must meet "Visual standard every story must meet" (above)** — a new entry that can't be
composed into 3–6 heading/visual/qualifier blocks with a real mix of chart forms is a sign
the question is too narrow or too broad to be a story, not a reason to relax the standard. A
question well suited to a single number or a single list is better answered by the curated
instant-answer engine (`backend/specs/market-health/api.md`) than dressed up as a story.

New ingestion types (company websites, layoff portals, papers, and other sources) add source
adapters and source-specific aggregates; they do not change the meaning of this story's
source-aware contract. A future story may use those sources only after its own data contract
defines what they can support and how provenance is shown.