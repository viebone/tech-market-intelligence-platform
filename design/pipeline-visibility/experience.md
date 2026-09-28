---
id: pipeline-visibility
outcome: pipeline-processing-visibility
directive: low
status: ready
created: 2026-08-14
---

# Pipeline Visibility — Experience Spec

## Outcome this serves

See: `outcomes/pipeline-processing-visibility.md`

---

## Primary question this experience answers

> "What has the pipeline actually processed and indexed — and is anything broken?"

This is an operator-only surface, not part of the consumer-facing product. Per
`design/foundations.md`'s **Scope** section, this experience is exempt from the Agentic
Conversational UI paradigm and from Principle 5 (Direct Manipulation of Outcomes) — it is a
plain, traditional, read-only dashboard: tables, summary numbers, and charts the operator
reads and filters, not a conversation and not an editing surface. Confirmed directly with the
stakeholder during triage.

Requirements extraction runs in **two lanes**, and the operator needs to see both as one
picture: the daily interactive extraction (bounded by a per-run cost cap) and an automatic
**Batch catch-up** that drains whatever the daily lane couldn't reach (cheaper, slower,
~24h turnaround — see `changes/2026-09-01-requirements-backlog-batch-catchup.md`). The
operator never triggers or cancels either — both are pipeline-owned. The dashboard only has
to make the combined state legible: *is everything getting extracted, and if not, is the
catch-up working?*

---

## Information Architecture

**Location:** Outside `design/information-architecture.md`'s three-column Task Panel /
Working Space / Output Panel model. That model describes the consumer-facing product's
navigation; this is a separate, operator-only admin surface (e.g. reachable at its own
route such as `/admin`), not linked from or reachable through the consumer product's
navigation at all.

This is a deliberate deviation, not an oversight — flagged as an **open question for
`/new-information-architecture`** (Step 3 of `changes/2026-08-13-admin-pipeline-dashboard.md`)
to decide whether/how a product-wide IA spec should acknowledge an operator-only surface that
sits outside its navigation model entirely.

Because no IA entry exists for this surface, the zone names below are proposed by this spec,
not drawn from `design/information-architecture.md`'s Content Taxonomy:

| Zone | Priority | Contains |
|---|---|---|
| Sidebar Nav | Primary | Fixed left-hand navigation: Overview, Postings, Ingestion Runs, Employment Events, Sources & Licensing (added 2026-09-16 — `changes/2026-09-16-admin-licensing-visibility.md`; **merged with Scraped Source Runs and Statistics Sources 2026-09-28** — `changes/2026-09-28-consolidate-sources-licensing-views.md` — this one nav entry now covers every registered source of every kind), Market Observations, Skill Associations (added 2026-09-18 — `changes/2026-09-18-admin-market-benchmark-visibility.md`), Taxonomy Health (added 2026-09-21 — `changes/2026-09-21-emerging-role-detection.md`), **Trusted Statistics** (added 2026-09-24 — `changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md`), **Feedback, Feedback Responses** (added 2026-09-23 — `changes/2026-09-23-user-feedback-mechanism.md`, corrected 2026-09-23 — `changes/2026-09-23-feedback-responses-not-visible-in-admin.md`: Feedback Responses was missing from this list on first add, leaving it reachable only via an inline text link on the Feedback summary page instead of its own nav entry, unlike every other list view here), **Data Coverage & Quality** (added 2026-09-28 — `changes/2026-09-28-data-insight-coverage-quality-admin-view.md`), **Technical Data Visibility** (added 2026-09-28 — `changes/2026-09-28-technical-data-visibility-admin-view.md`). Always visible. Two entries retired 2026-09-28: **Scraped Source Runs** and **Statistics Sources**, both folded into Sources & Licensing. |
| Main Content | Primary | The active view's content — summary cards, charts, tables, or a posting's/event's detail. |

---

## Opening Prompt

Not applicable. This experience is explicitly exempt from the Agentic Conversational UI
paradigm (`design/foundations.md` — Scope). Nothing is AI-generated here; every view renders
data read directly from the pipeline's own stored results.

---

## User Flow

1. The operator navigates to the admin dashboard's URL and authenticates. (The authentication
   mechanism itself is a backend concern — see Open Questions — but from the operator's
   perspective: unauthenticated visitors see an access-denied state with no dashboard content
   or data visible, authenticated ones proceed straight to Overview.)
2. The operator lands on **Overview** — the default view. It shows, at a glance and without
   any filtering or navigation required:
   - Total postings processed, and how many are fully indexed (classified + requirements
     extracted) vs. partially processed vs. failed
   - Classification distribution: counts by Role Category, Level, Track, Specialization, and
     Classification Confidence, plus a count of `unknown` values in each dimension
   - Taxonomy version breakdown — how many postings are on the current taxonomy version vs.
     older versions, so an in-flight reprocessing backlog (like
     `changes/2026-08-11-classification-taxonomy-redesign.md`'s) is visibly draining, not a
     silent background fact
   - Requirements/skills extraction coverage — % of eligible postings with requirements
     extracted, and Skill Group distribution across them
   - **Requirements extraction backlog & batch status** — how many eligible postings are
     still waiting for requirements extraction, and the state of the pipeline's Batch
     catch-up: whether a batch job is in flight right now (how many postings it covers,
     when it was submitted, roughly when its results are expected), or — if none is in
     flight — when the last batch job completed and how many postings it processed, or
     whether the last one **failed**. The operator can tell at a glance whether the
     backlog is draining or stuck, without querying the database.
   - The most recent Ingestion Run's summary (when it ran, sources/companies attempted,
     fetched/inserted/error counts, budget usage, and whether that run collected a
     finished batch and/or submitted a new one)
3. The operator can navigate to **Postings** from the sidebar to see every processed posting
   as a filterable, sortable table (see Interactions).
4. The operator narrows the table using filters — by Role Category, Level, Track,
   Specialization, Classification Confidence, Taxonomy Version, Requirements Status
   (extracted / pending / failed), source, or a free-text search over posting title/company —
   to find the specific slice of postings they want to inspect.
5. The operator clicks a row to open that posting's **Detail** view: the posting's raw stored
   data, its classification result and confidence, its extracted requirements/skills (if any),
   which Ingestion Run(s) touched it, and any errors recorded against it.
6. Independently, the operator can navigate to **Ingestion Runs** from the sidebar to see the
   full run history — one row per run, with fetched/inserted/error counts and budget usage —
   and click a run to see its per-source, per-company breakdown. Each run's row also shows
   its **batch activity** for that run: whether it collected a finished batch (and how many
   postings that added), whether it submitted a new batch (and how large), and whether a
   batch collection or submission errored. A run that did interactive extraction and nothing
   with batch reads plainly as that — no batch activity is a normal state, not a gap.
7. The operator refreshes any view on demand to see the latest state. Nothing here
   auto-updates or streams live — matching `outcomes/pipeline-processing-visibility.md`'s
   explicit "periodic/on-demand refresh is sufficient" scope.
8. **(Added 2026-09-11.)** Independently of the job-postings pipeline above, the operator can
   navigate to **Employment Events** from the sidebar to see the employment-events pipeline —
   a genuinely separate pipeline, never joined or cross-referenced with postings data (per
   `backend/EMPLOYMENT_EVENTS.md`, the same independence rule the consumer-facing product
   itself follows). This view shows, at a glance: total events, a breakdown by source and by
   direction (contraction/expansion), and — per source — when it last ingested anything and,
   for a streaming source, its current stream position. The operator narrows the events table
   by source, event type, direction, confidence, or country, and clicks a row to see that
   event's full stored record (including the source's raw response, verbatim) — the same
   List → Detail shape as Postings, applied to a different table.
9. **(Added 2026-09-16; merged 2026-09-28 —
   `changes/2026-09-28-consolidate-sources-licensing-views.md`.)** Independently of every
   pipeline above, the operator can navigate to **Sources & Licensing** from the sidebar to see,
   at a glance, **every registered external data source of every kind** — job-posting adapters,
   employment-event adapters, scraped sources, and trusted-statistics publishers alike — as one
   flat list, not four. No filtering or drill-down — the full detail *is* the list, same
   reasoning as always (there's no larger underlying record per source to drill into). Every row
   shows the same core facts regardless of source type:
   - The source's name and its category (Job Posting / Employment Event / Scraped /
     Trusted Statistics)
   - Its confirmed licence variant (or an honest "not yet confirmed" state), whether commercial
     use is permitted, the exact attribution text to use if this data is ever shown or
     republished, and a link to the licence itself — unchanged from before the merge, since this
     fact was already tracked identically for every source type
   - Its cadence, stated honestly for what that source type actually has: a scraped or
     trusted-statistics source shows whether it's up to date, due for its next run, or has never
     run (unchanged from the former Scraped Source Runs / Statistics Sources views); a
     job-posting or employment-event adapter — which has never had an individually-gated cadence,
     only a shared cron schedule — states that plainly ("Runs on the shared daily ingestion
     schedule," linking to Ingestion Runs) rather than a fabricated per-source due/not-due state
   - For a trusted-statistics publisher specifically: its trust-bar sign-off (reviewer, date),
     how often it's checked, its latest release and period, how many days old that release is
     (flagged **Overdue** past the normal cadence), how many series and figures it holds, and any
     release the system refused to accept and why — every fact the former Statistics Sources view
     showed, now a sub-line on this source's one row here instead of a second page to visit
   - No source's row is omitted for having never run or produced data yet — a
     registered-but-silent source is exactly the state this view exists to make visible, the same
     principle the pre-merge Scraped Source Runs and Statistics Sources views both already
     followed

   This view answers "can we actually use this data, how do we credit it, and is it current" for
   *any* registered source, in one place — without opening `LICENSING.md`, reading
   `scraping/licences.py`, or checking three different admin pages depending on which kind of
   source it happens to be.
10. **(Added 2026-09-18.)** Independently of every pipeline above, the operator can navigate to
    **Market Observations** to see every captured demand/salary snapshot from a scraped
    market-benchmark source (role/skill, employment type, location, period, rank, vacancy
    count/share, salary percentile spread) as a filterable, sortable table — filtered by source,
    entity type, entity name, or employment type. Clicking a row opens its **Detail** view: the
    full row including its raw scraped fragment, plus — when available — which LLM extraction
    produced these values and whether that extraction was fresh or reused from cache (the same
    "show your provenance" discipline every other detail view here already follows). The
    operator can separately navigate to **Skill Associations** to see the weighted role↔skill
    graph the same source produced — same List → Detail shape, filtered by source or role.
    (**Scraped Source Runs**, previously a third view reachable from this step, merged into
    Sources & Licensing 2026-09-28 — see step 9.)

11. **(Added 2026-09-24.)** Independently of every pipeline above, the operator can navigate to
    **Trusted Statistics** to see every stored figure from a trusted external publisher (today:
    the Office for National Statistics' vacancy estimates) as a filterable, sortable table —
    filtered by source, dataset, dimension (total / industry / business size) or series code —
    showing each value **with its unit and its publisher**, its period in the publisher's own
    words, whether it is provisional, its release date, and whether its licence is confirmed. By
    default only the latest value for each period is shown; a switch shows every stored version,
    including values a later release changed. Clicking a row opens its **Detail** view: the full
    row, the series definition (what it counts, what it leaves out, seasonal adjustment, links to
    the publisher's methodology and dataset page), the release it came from and how that release
    was checked, the licence and exact attribution text, and the **version history** for that
    period ("Never revised" when there is only one). (**Statistics Sources**, previously a second
    view reachable from this step, merged into Sources & Licensing 2026-09-28 — see step 9.)

12. **(Added 2026-09-28.)** Independently of every pipeline above, the operator can navigate to
    **Data Coverage & Quality** to see, on one pragmatic summary page, where the platform's
    captured data supports strong insight versus where it's thin — a single flat page, no
    filtering or List → Detail drill-down, since the point is an at-a-glance cross-cut, not a
    per-record inspection tool (the underlying records are already inspectable from Postings,
    Employment Events, Market Observations, etc.). Four ranked lists, one per axis:
    - **By Country** — every country with at least one posting, ranked by posting volume, plus an
      explicit **"Unknown / not reported"** row for postings with no country recorded. This row
      is never hidden or folded into the ranking silently — some sources (Personio) never report
      a country at all, so pretending every posting has a known country would misstate coverage
      rather than reveal it.
    - **By Company Size** — every `employer_size_band` value present among tracked companies,
      ranked by number of companies in that band and their combined posting volume. A band held
      up by very few companies reads as limited, not blended into a false sense of breadth.
    - **By Source** — every registered source (Greenhouse, Lever, Ashby, Workable, Personio,
      IT Jobs Watch, ONS Vacancy Survey), ranked by data volume, each paired with that source's
      own known structural gaps (e.g. "No salary field," "No country field") pulled from
      `DATA_SOURCES.md` rather than re-derived — this view surfaces those caveats, it doesn't
      duplicate their source of truth.
    - **By Business Area** — every `COMPANY_INDUSTRY` tag present among tracked companies, ranked
      by number of companies and combined posting volume. A tag held up by a single company reads
      as single-company coverage, not sector-wide insight, since a lone employer's hiring pattern
      is not a sector trend.

    Each list uses the same three-tier strength language throughout, defined once in Business
    Logic (deferred to `/new-backend-spec` — see Open Questions): **Strong**, **Limited**, and
    **Negligible/none**. This page never invents a numeric "quality score" — every row shows its
    real underlying counts (postings, companies) alongside its tier, so the tier reads as a
    plain-language summary of real numbers, never as an opaque verdict.

13. **(Added 2026-09-28.)** Independently of every pipeline above, the operator can navigate to
    **Technical Data Visibility** to see, on one pragmatic summary page, the platform's own
    technical data footprint — a distinct question from every other view here, which all show
    *what the pipeline has done* or *how good the result is*; this page answers *how big is this
    platform, structurally, right now*. Two sections, no filtering or drill-down:
    - **Data footprint** — one row per storage category the platform holds today (job postings +
      classifications + requirements, employment events, market benchmark observations + skill
      associations, trusted statistics series + observations, user feedback), each showing how
      many tables back it and a total row count. This is a structural inventory, not a coverage
      judgement — it carries no strength tier, unlike Data Coverage & Quality's lists, because
      "how much data exists" and "is that data good enough" are different questions answered by
      two different pages.
    - **Exposure summary** — a plain count of the platform's capabilities broken down by where
      they're reachable from: via MCP (an external AI acting on a user's behalf), via the
      frontend/backend API (this platform's own product), or neither. This reads the same
      reachability decisions `ACCESS.md` already records capability-by-capability (built for the
      MCP-exposure-review process) — this page is a summary view of that existing record, not a
      second, separately-maintained tracking mechanism. Clicking through shows the same
      capability-by-capability detail `ACCESS.md` already documents, in this page's own layout
      rather than sending the operator to a raw markdown file.

---

## Visual Design

Reuses `design/visual-design.md`'s existing tokens in full — dark-first palette, typography
scale, spacing scale, surface/input/button component aesthetics, and motion rules all carry
over unchanged. This is the same visual language, applied to a different layout shape:

- **Layout**: a conventional sidebar-plus-content shape, not the consumer product's
  three-column layout. Sidebar Nav uses the same fixed-width, `gray-800` surface treatment as
  the Task Panel (visual consistency), but its contents are static navigation links, not a
  dynamic task list.
- **Summary numbers** (Overview): large numerals in `text-2xl font-semibold` / `gray-100`
  (matching the existing Conversation title scale), each with a `text-xs` / `gray-400` label
  beneath it — the existing Label/Caption scale, not a new one.
  and coverage percentages use the three role-category accent colours from
  `design/visual-design.md` (indigo/fuchsia/emerald — revised 2026-09-26, `changes/2026-09-26-role-palette-accessibility.md`) only where the split is genuinely by Role
  Category; every other distribution (Level, Track, Specialization, Confidence, Taxonomy
  Version, Requirements Status) uses a single neutral series colour (`gray-300`) with the
  semantic colours (`emerald-600` / `amber-600` / `red-600`) reserved for status meaning
  (e.g. `unknown` counts, failures) — not decoration.
- **Tables** (Postings, Ingestion Runs): `gray-800` surface, `gray-700` row dividers, `text-sm`
  body rows, `text-xs font-medium` column headers — same tokens as the rest of the product's
  Label/Body scale. Row hover uses `gray-700` (Surface raised).
- **Status indicators** (Requirements Status, run errors, `unknown`/failed classification
  values, **batch job state**) always pair colour with a text label — never colour alone,
  per Visual Design's "What this rules out." Batch state uses the same semantic mapping as
  the rest of the dashboard: an in-flight batch is neutral/informational (`gray-300` with a
  "Batch running" label — it's expected work in progress, not a warning), a completed batch
  is `emerald-600` ("Batch complete"), a failed batch is `red-600` ("Batch failed") and
  reads as a failure at a glance, consistent with a failed Ingestion Run.
- **Detail view**: a single-column stacked layout of labelled fields, using the same
  Surface/card treatment (`gray-800`, `border-gray-700`, `rounded-lg`) as the rest of the
  product.
- **Sources & Licensing table** (added 2026-09-16; **merged with Scraped Source Runs and
  Statistics Sources 2026-09-28** — `changes/2026-09-28-consolidate-sources-licensing-views.md`):
  same table tokens as Postings/Ingestion Runs. One row per registered source, of every kind, in
  one list. Each row carries:
  - A neutral `gray-300` category label (Job Posting / Employment Event / Scraped / Trusted
    Statistics) — never a semantic colour, since a source's category is a fact, not a status
  - Two licence status badges, each pairing colour with a plain-language label — never a raw
    `True`/`False` or the bare word "confirmed": **Confirmation status** (`emerald-600` "Licence
    confirmed" vs. `amber-600` "Not yet confirmed" — amber, not red, since an unconfirmed licence
    is a real, honest, working state per Business Logic — polite scraping, not an error) and
    **Commercial-use status** (`emerald-600` "Commercial use OK" vs. `red-600` "Non-commercial
    only" — red here because using non-commercial-licensed data commercially would be a real
    problem, not a benign pending state; an unconfirmed source shows `amber-600` "Unknown — treat
    as non-commercial," never a false "OK")
  - A cadence badge, unchanged in meaning from the pre-merge Scraped Source Runs/Statistics
    Sources views: `emerald-600` "Up to date," `amber-600` "Due for next run," `gray-300` "Never
    run" (neutral, not a failure) for a scraped or trusted-statistics source; a plain `gray-300`
    "Runs on shared schedule" label (no due/not-due state at all) for a job-posting or
    employment-event adapter, since those were never individually cadence-gated — inventing a
    due/not-due state for them would fabricate a distinction that doesn't exist
  - For a trusted-statistics publisher only: a sub-line beneath the main row carrying its
    trust-bar sign-off, check interval, latest release/period, an `amber-600` **Overdue** badge
    when past the normal cadence, series/figure counts, and any rejected release — the same facts
    the pre-merge Statistics Sources view showed, unchanged, just relocated
  - The attribution text and licence link render as plain text/link beneath the badges, not
    hidden behind a further click — per `data-legibility`'s Provenance rule, unchanged from
    before the merge
- **Market Observations / Skill Associations tables** (added 2026-09-18): same table tokens as
  every other List view here — no new tokens needed. One addition: the Detail view's extraction
  provenance line pairs a `gray-300` "Fresh extraction" or "Reused from cache" label with the
  model name and timestamp — informational, not a warning state, so neither uses a semantic
  colour (unlike the licence badges above, where colour carries real meaning).
- **Data Coverage & Quality page** (added 2026-09-28): four `RankedBarList`-style horizontal
  ranked lists stacked on one page (same visual family as the existing Classification
  Distribution charts), each row pairing a bar (length = the row's real count) with a strength
  badge. Strength badges reuse the dashboard's existing semantic mapping — never a new colour
  meaning: `emerald-600` "Strong," `amber-600` "Limited" (a caveat, not a failure — the same
  register as "Not yet confirmed"), `gray-500` "Negligible" (matches Taxonomy Version Progress's
  "stale" grey, not an error state). The "Unknown / not reported" row (By Country list) always
  renders last, visually separated by a thin `border-gray-700` rule, so it reads as "outside the
  ranking" rather than competing with real countries for rank position.
- **Technical Data Visibility page** (added 2026-09-28): the Data Footprint section uses the
  same summary-card treatment as Overview's summary numbers (`text-2xl font-semibold`/`gray-100`
  numeral, `text-xs`/`gray-400` label beneath) — one card per storage category, no bars, since
  there is no "more/less of the max" comparison to draw, only a flat inventory. The Exposure
  Summary section uses three summary numbers side by side (MCP-reachable / frontend-reachable /
  neither), each in the same neutral `gray-300` treatment — never a semantic colour, since a
  capability being MCP-only, frontend-only, or neither is a design fact, not a status to flag as
  good or bad.

---

## Chart Specification

**Classification Distribution charts** (Overview)
- Type: horizontal bar chart, one per dimension (Role Category, Level, Track, Specialization,
  Classification Confidence)
- Title: the dimension name (e.g. "Level")
- Subtitle: total postings counted
- Axis: bar length = posting count; category labels on the y-axis, count on the x-axis
- Series colour: `gray-300` (neutral), except the Role Category chart which uses the three
  accent tokens (indigo/fuchsia/emerald) per category, and any `unknown` bar in any chart which
  uses `amber-600` to visually flag it as distinct from a real classified value
- Hover: shows exact count and % of total for that bar
- Loading state: skeleton pulse bars (`animate-pulse`, `gray-700`)
- Empty state: "No postings classified yet" (see Edge Cases)

**Taxonomy Version Progress** (Overview)
- Type: horizontal stacked bar — one segment per `taxonomy_version` present in the data
- Title: "Taxonomy Version"
- Subtitle: "{current version} vs. earlier versions" — current version highlighted
- Series colour: current version = `emerald-600` (up to date), all earlier versions =
  `gray-500` (stale, pending reprocessing)
- Hover: version string + exact count + %
- Loading state: skeleton pulse
- Empty state: not shown when only one version exists (nothing to compare — falls back to a
  plain count, not a chart)

**Requirements Coverage** (Overview)
- Type: single horizontal progress bar
- Title: "Requirements Extraction Coverage"
- Subtitle: "{extracted} of {eligible} postings"
- Fill colour: `emerald-600`; unfilled track: `gray-700`
- Hover: exact extracted/eligible/pending/failed counts
- Loading state: skeleton pulse
- Empty state: "No postings eligible for requirements extraction yet"
- Directly beneath the bar, a one-line **backlog & batch status** (not a chart — a
  number plus a status badge): "{backlog} awaiting extraction" and one of:
  "Batch running — {n} postings, submitted {relative time}, results expected within ~24h"
  / "Last batch: {n} postings, completed {relative time}" / "Last batch failed
  {relative time} — see Ingestion Runs" / "No batch needed" (backlog below the trigger
  floor). This is the operator's single answer to "is the backlog draining?"

**Coverage by Country / Company Size / Source / Business Area** (Data Coverage & Quality, added
2026-09-28) — four instances of the same chart shape, one per axis:
- Type: horizontal ranked bar list, one bar per value on that axis, sorted descending by the
  list's stated volume metric
- Title: the axis name — "By Country," "By Company Size," "By Source," "By Business Area"
- Subtitle: what's counted and its scope, stated in full every time (never assumed from the
  title alone) — e.g. "Job postings by country, across all tracked sources, as of {last
  ingestion run time}"
- Bar length: postings count (By Country, By Business Area) or a stated combination of company
  count + posting count (By Company Size, By Source — both numbers shown as text alongside the
  bar, not silently combined into one)
- Unit: always "postings" or "companies," stated per bar via hover and inline text, never a bare
  number with no unit
- Colour / legend: three-tier strength badge per row (`emerald-600` "Strong," `amber-600`
  "Limited," `gray-500` "Negligible") — a fixed legend renders once above each list, not
  per-row, naming what each colour means; colour is never the only signal, every badge carries
  its text label
- Hover: exact counts (postings, companies as applicable) and the row's %-of-total
- Loading state: skeleton pulse bars, same as every other chart on this dashboard
- Empty state: "No coverage data yet — run the ingestion pipeline to populate this view" (By
  Country / By Source) — mirrors the dashboard's existing "no data yet" pattern
- By Country only: the "Unknown / not reported" row never carries a strength badge (it isn't a
  coverage tier, it's the acknowledgement that no country was recorded) — shown in `gray-400`
  text with its own count and %, visually separated per the Visual Design note above
- By Source only: each bar's row also shows that source's known structural gaps as small inline
  text beneath the bar (e.g. "No salary field · No country field" for Personio) — pulled from
  `DATA_SOURCES.md`, not re-derived from the data itself

**Data Footprint** (Technical Data Visibility, added 2026-09-28)
- Type: a grid of summary cards, one per storage category — not a chart, a plain inventory
- Title: the category name (e.g. "Job Postings," "Employment Events," "Market Benchmark Data,"
  "Trusted Statistics," "User Feedback")
- Subtitle: which tables back it (e.g. "raw_postings + classifications + posting_requirements")
  and the total row count across them, as of the current page load
- Unit: always "rows," stated per card, never a bare number
- No colour, no hover beyond a plain tooltip repeating the subtitle text — this is a structural
  fact, not a state to flag
- Loading state: skeleton pulse cards, same as every other summary-card view on this dashboard
- Empty state: not applicable — every category always has at least its own tables, even at zero
  rows; a zero-row category reads as "0 rows," not as a missing card

**Exposure Summary** (Technical Data Visibility, added 2026-09-28)
- Type: three summary numbers side by side, plus a link through to the full capability list
- Title: "Reachable via MCP" / "Reachable via frontend/API" / "Not exposed anywhere"
- Subtitle: "{n} of {total} capabilities," so each number is legible against the whole, not in
  isolation
- Unit: always "capabilities"
- Colour: none — `gray-300` neutral throughout (Visual Design, above); this is a design fact, not
  a status
- Hover: not applicable to the summary numbers themselves; the linked-through detail list reuses
  whatever table treatment `ACCESS.md`'s own capability rows already imply
- Loading state: skeleton pulse
- Empty state: not applicable on a product that already has an MCP layer (this page only exists
  because one does)

---

## Interactions

| User action | System response |
|---|---|
| Operator opens the dashboard without valid credentials | Access-denied state shown; no summary numbers, tables, or posting data rendered anywhere |
| Operator selects a sidebar item (Overview / Postings / Ingestion Runs) | Main Content swaps to that view; Sidebar Nav highlights the active item |
| Operator applies a filter on the Postings table | Table re-queries and re-renders with the filtered set; active filters shown as removable chips above the table; row count updates |
| Operator types in the Postings free-text search | Table filters to postings whose title or company matches, after a short debounce |
| Operator clicks a column header on a sortable table | Table re-sorts by that column; a second click reverses sort direction |
| Operator clicks a posting row | Navigates to that posting's Detail view |
| Operator clicks an ingestion run row | Expands (or navigates to) that run's per-source/per-company breakdown, including that run's batch activity (collected / submitted / errored) |
| Operator hovers the backlog & batch status line on Overview | Tooltip shows the batch job's exact posting count, estimated cost, submitted/completed timestamps, and — if failed — the recorded error |
| Operator clicks "Refresh" on any view | Re-fetches current view's data; skeleton pulse shown during the fetch; view updates in place |
| Operator hovers a chart bar/segment | Tooltip shows exact count and percentage for that value |
| Operator clicks a chart bar for a specific value (e.g. `unknown` Level) | Navigates to Postings, pre-filtered to that exact value |
| Operator applies a filter on the Employment Events table (source, event type, direction, confidence, country) | Table re-queries and re-renders with the filtered set, same filter-chip/pagination pattern as Postings |
| Operator clicks an Employment Events row | Navigates to that event's Detail view, showing every stored field and the source's raw response verbatim |
| Operator applies a filter on the Market Observations table (source, entity type, entity name, employment type) | Table re-queries and re-renders with the filtered set, same filter-chip/pagination pattern as Postings |
| Operator clicks a Market Observations row | Navigates to that observation's Detail view, including its raw scraped fragment and — when available — its extraction provenance (model, fresh vs. cached) |
| Operator applies a filter on the Skill Associations table (source, role) | Table re-queries and re-renders with the filtered set, same pattern |
| Operator clicks a Skill Associations row | Navigates to that association's Detail view |
| Operator opens Sources & Licensing | Shows one row per registered source of every kind (job-posting, employment-event, scraped, trusted-statistics) — licence badges, category label, and cadence badge (or "Runs on shared schedule" for job-posting/employment-event sources); a trusted-statistics row also shows its trust-bar/release sub-line — no filtering or pagination needed at this scale (merged 2026-09-28, folding in the former Scraped Source Runs and Statistics Sources interactions) |
| Operator opens Data Coverage & Quality | Shows all four ranked lists at once — no filtering, sorting, or drill-down; this page is a fixed cross-cut summary, not an explorable table |
| Operator hovers a Coverage & Quality bar | Tooltip shows exact counts (postings and/or companies) and %-of-total for that row |
| Operator opens Technical Data Visibility | Shows the Data Footprint cards and the Exposure Summary numbers at once — no filtering; a fixed structural snapshot |
| Operator clicks through from the Exposure Summary | Navigates to a flat capability-by-capability list (the same information `ACCESS.md` records), showing each capability's name and its frontend/API/MCP reachability |

---

## Edge Cases

- **No ingestion has ever run.** Overview shows all summary numbers as zero/empty with a "No
  data yet — run the ingestion pipeline to populate this view" message, mirroring the
  consumer product's existing "no data yet" pattern for `/api/market-health/openings`. No
  chart renders in this state; a static empty-state message replaces it.
- **A posting is classified but not yet requirements-extracted.** Its Requirements Status
  reads "Pending," not "Failed" or blank — this is expected mid-pipeline state, not an error,
  and must read as such at a glance.
- **A posting's requirements extraction failed.** Requirements Status reads "Failed," visually
  distinct (colour + label, per Visual Design rules) from "Pending," with the recorded error
  visible in that posting's Detail view.
- **Postings span multiple taxonomy versions at once** (mid-reprocessing, as during
  `changes/2026-08-11-classification-taxonomy-redesign.md`'s backlog drain). The Taxonomy
  Version chart and a per-posting version badge in the Postings table make this visible rather
  than presenting classification data as if it were all on one consistent taxonomy.
- **A posting's `role_category`, `level`, `track`, or `specialization` is `unknown`.** These
  are genuine, honestly-reported values (per `design/market-health/job-classification.md`),
  not errors — shown in classification distributions and the Postings table using the
  `amber-600` "flag, not failure" treatment, distinguishable from both a real classified value
  and a hard failure.
- **The Postings table has thousands of rows** (5,000+ postings in production today). The
  table is paginated; filters narrow the result set before rendering, not after.
  Implementation detail (page size, virtualization) is left to the frontend spec.
- **An ingestion run partially failed** (some sources/companies fetched, others errored). The
  run's row shows a mixed-status indicator, and its detail breakdown shows exactly which
  source/company pairs succeeded vs. failed — matching the existing `terms_processed` JSON
  shape already recorded in `ingestion_runs` (`backend/specs/market-health/api.md`).
- **A batch job is in flight across a day boundary.** Overview shows "Batch running" for as
  long as the provider takes (typically well under 24h). This is a normal state, not a
  stuck one — the status line still shows when it was submitted so a genuinely stuck job
  (submitted long ago, still running) is visually obvious.
- **A batch job failed provider-side.** The last-batch status reads "Batch failed" in
  `red-600`; the failing run's Ingestion Runs row shows the batch-submission/collection
  error; the individual postings that were in the batch show Requirements Status "Failed"
  with the error in their Detail view — the same surface a failed interactive extraction
  already uses. The postings stay in the backlog and are retried, so the backlog count does
  not drop for that batch.
- **A batch job returned some malformed results.** Postings whose batch result failed
  validation are treated exactly as an interactive validation failure — folded into the
  catch-all / marked Failed per the existing extraction rules, not silently dropped. The
  Overview backlog count reflects only what genuinely landed.
- **The interactive run itself crashed before finishing** (e.g. the LLM provider was down).
  The Ingestion Runs row for that run must read as a failure, distinct from a run that
  simply had no requirements work to do — the operator can tell "extraction broke" from
  "nothing to extract" without opening the database. (This closes an observability gap
  found during `changes/2026-08-29-chat-free-tier-key-isolation.md`.)
- **(Added 2026-09-11.) No employment events have ever been ingested for a source, or at
  all.** Same "No data yet" empty-state pattern as the job-postings pipeline — zero counts and
  an explanatory message, no chart. A source with zero events reads plainly as "hasn't run
  yet / found nothing," never as an error.
- **(Added 2026-09-11.) An employment event's `company_raw` is a bare id, not a real company
  name** (see `backend/EMPLOYMENT_EVENTS.md` — Companies House Streaming API rows that predate
  the placeholder-name fix). The Detail view shows the stored value exactly as-is — it is a
  read-only mirror of the database, so it never re-applies the consumer-facing product's
  `is_real_company_name()` display filter to hide it. This is a deliberate difference from the
  consumer-facing story: the admin dashboard's whole purpose is showing operators what is
  actually stored, including known data-quality gaps.
- **(Added 2026-09-11.) No ingestion-run history exists for employment events**, unlike job
  postings' `ingestion_runs` table — each adapter re-fetches a trailing window (or resumes a
  stream position) on every scheduled run, with no per-run row recorded anywhere. The
  Employment Events view does not pretend otherwise: it shows a per-source "last ingested at"
  timestamp (derived from the events themselves) and, for a streaming source, its current
  cursor position — not a fabricated run history.
- **(Added 2026-09-16.) A source's licence isn't yet confirmed.** Shown plainly as "Not yet
  confirmed," never hidden or defaulted to looking resolved — the whole point of this view is
  surfacing exactly this state. Its commercial-use badge reads "Unknown — treat as
  non-commercial," the same conservative default `scraping.licences.is_source_usable()` applies
  in code (Business Logic, `backend/specs/scraped-data-sources/api.md`).
- **(Added 2026-09-16.) No scraped sources are registered yet.** Same "No data yet" empty-state
  pattern as every other view here — not an error, just nothing to show yet.
- **(Added 2026-09-18.) No market observations or skill associations have been captured yet.**
  Same "No data yet" empty-state pattern.
- **(Added 2026-09-18; view merged into Sources & Licensing 2026-09-28.) A registered scraped or
  trusted-statistics source has never run.** Its cadence badge reads "Never run" (neutral,
  `gray-300`), not an error and not omitted from the list — this view's whole purpose is making a
  never-run source visible, unlike the Employment Events summary's "only sources present in data"
  convention (a deliberate difference, not an inconsistency — see
  `changes/2026-09-18-admin-market-benchmark-visibility.md`'s Decision Log). A job-posting or
  employment-event source is never shown "Never run" — it always shows "Runs on shared schedule,"
  since it was never individually cadence-gated in the first place (Business Logic).
- **(Added 2026-09-28.) A trusted-statistics publisher's latest release is older than its normal
  cadence.** Its sub-line shows an `amber-600` "Overdue" badge with the day count, distinct from
  "Never run" (which means no release has ever been ingested at all, a different, earlier state)
  — carried over unchanged from the pre-merge Statistics Sources view.
- **(Added 2026-09-18.) An observation has no matching `scrape_extractions` row** (predates the
  LLM-extraction rebuild, or the extraction-cache row was since superseded). The Detail view
  shows "Extraction provenance unavailable" rather than a blank or fabricated value.
- **(Added 2026-09-28.) A posting has no recorded country** (Personio-sourced postings, always —
  and any other source's posting where the free-text location didn't resolve via
  `COUNTRY_NAME_TO_ISO2`). Counted in the By Country list's "Unknown / not reported" row, never
  silently dropped from the total and never guessed at.
- **(Added 2026-09-28.) A tracked company has no `employer_size_band`** (not yet added to
  `COMPANY_HEADCOUNT`/`UNKNOWN_HEADCOUNT` per `EMPLOYER_SIZE_STANDARDS.md`). Counted in its own
  explicit "Unknown" row in By Company Size, same treatment as country.
- **(Added 2026-09-28.) A company's board resolves but currently lists zero roles** ("returns 0"
  in `DATA_SOURCES.md` §4) or 404s entirely (e.g. `plaid`). Neither is hidden from this page —
  both depress that company's contribution to its source/country/industry/size rows exactly as
  the real data does; this page never back-fills a dead or empty board with an assumed value.
- **(Added 2026-09-28.) A business area or company-size band has exactly one company in it.**
  Reads as "Limited" or lower regardless of that one company's own posting volume — a single
  employer's hiring pattern is never presented as if it were sector- or band-wide insight, no
  matter how much data that one employer happens to produce.
- **(Added 2026-09-28.) A storage category has zero rows** (e.g. a fresh deployment before any
  ingestion has run). Its Data Footprint card reads "0 rows" plainly — not omitted, not shown as
  an error — since a category can exist structurally before it holds any data.
- **(Added 2026-09-28.) `ACCESS.md` is out of date relative to the actual code** (a capability
  was shipped without its MCP-exposure decision being recorded, the exact failure Rule 12 exists
  to catch). This page has no way to detect that on its own — it can only summarize what
  `ACCESS.md` currently says, honestly, not verify it against the running MCP server's actual
  tool list. This is a real limitation, not silently glossed over — see Open Questions.

---

## Evaluation Metrics

| Metric | How measured | Target |
|---|---|---|
| Time to answer "what happened in the most recent run" | Observed usage / operator self-report | Under 30 seconds from opening the dashboard |
| Clicks to reach a single posting's full detail from Overview | Observed usage | 3 clicks or fewer |
| Frequency of falling back to direct database queries to answer a pipeline question | Operator self-report | Trends toward zero after adoption |
| Failure/error discoverability | Observed usage | Every classification or extraction failure — interactive **or batch** — is visible from the dashboard without cross-referencing logs |
| Time to answer "is the requirements backlog draining or stuck?" | Observed usage / operator self-report | Under 15 seconds from opening Overview |
| Time to answer "where is our data weakest right now?" | Observed usage / operator self-report | Under 30 seconds from opening Data Coverage & Quality |
| Time to answer "how big is this platform, structurally, right now?" | Observed usage / operator self-report | Under 20 seconds from opening Technical Data Visibility |

---

## Open Questions

- **Auth mechanism** — deliberately left open per `changes/2026-08-13-admin-pipeline-dashboard.md`'s
  Decision Log. To be decided in `/new-backend-spec` (Step 5). This experience only specifies
  the operator-facing behaviour (access-denied state when unauthenticated), not the mechanism.
- **IA documentation** — whether/how `design/information-architecture.md` should acknowledge
  this operator-only surface, given it sits entirely outside the three-column model. To be
  resolved in `/new-information-architecture` (Step 3).
- **Visual design gap check** — whether the reused tokens above (in particular a sidebar-nav
  pattern and data-table row styling) need a small addition to `design/visual-design.md`, or
  whether existing tokens fully cover it. To be resolved in `/new-visual-design` (Step 4).
- **Ingestion run detail — inline expand vs. separate page** — left as an implementation
  choice for the frontend spec; this experience only requires that the per-source/company
  breakdown be reachable from the run's row.
- **(Added 2026-09-28.) Strong / Limited / Negligible thresholds** — the exact numeric cutoffs
  (e.g. postings-per-country, companies-per-industry) that separate the three tiers are a
  Business Logic decision, deferred to `/new-backend-spec`. This experience specifies the
  three-tier language and its visual treatment, not the numbers behind it.
- **(Added 2026-09-28.) Company-size volume basis** — whether "combined posting volume" per
  `employer_size_band` should weight by company count too (so one very large board doesn't make
  a thinly-covered band look strong), or report raw totals with company count shown alongside for
  the operator to judge themselves. Deferred to `/new-backend-spec`.
- **(Added 2026-09-28.) `ACCESS.md` parsing mechanism** — how the Exposure Summary reads
  `ACCESS.md`'s existing markdown tables into the three counts (a runtime parse of the file vs.
  some other mechanism) is a technical decision, deferred to `/new-backend-spec`. This experience
  only requires that the three numbers reflect `ACCESS.md`'s current content, whatever the
  mechanism — never a separately-maintained duplicate of that record.
- **(Added 2026-09-28.) Staleness detection** — whether this page should ever attempt to flag
  that `ACCESS.md` might be out of date relative to the real MCP server's tool list (Edge Cases,
  above), versus accepting that limitation as out of scope for a first version. Deferred to
  `/new-backend-spec`; leaning toward out-of-scope unless that spec finds a cheap, reliable way to
  cross-check the two.
