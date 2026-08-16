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
| Sidebar Nav | Primary | Fixed left-hand navigation: Overview, Postings, Ingestion Runs. Always visible. |
| Main Content | Primary | The active view's content — summary cards, charts, tables, or a posting's detail. |

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
   - The most recent Ingestion Run's summary (when it ran, sources/companies attempted,
     fetched/inserted/error counts, budget usage)
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
   and click a run to see its per-source, per-company breakdown.
7. The operator refreshes any view on demand to see the latest state. Nothing here
   auto-updates or streams live — matching `outcomes/pipeline-processing-visibility.md`'s
   explicit "periodic/on-demand refresh is sufficient" scope.

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
  `design/visual-design.md` (indigo/purple/emerald) only where the split is genuinely by Role
  Category; every other distribution (Level, Track, Specialization, Confidence, Taxonomy
  Version, Requirements Status) uses a single neutral series colour (`gray-300`) with the
  semantic colours (`emerald-600` / `amber-600` / `red-600`) reserved for status meaning
  (e.g. `unknown` counts, failures) — not decoration.
- **Tables** (Postings, Ingestion Runs): `gray-800` surface, `gray-700` row dividers, `text-sm`
  body rows, `text-xs font-medium` column headers — same tokens as the rest of the product's
  Label/Body scale. Row hover uses `gray-700` (Surface raised).
- **Status indicators** (Requirements Status, run errors, `unknown`/failed classification
  values) always pair colour with a text label — never colour alone, per Visual Design's
  "What this rules out."
- **Detail view**: a single-column stacked layout of labelled fields, using the same
  Surface/card treatment (`gray-800`, `border-gray-700`, `rounded-lg`) as the rest of the
  product.

---

## Chart Specification

**Classification Distribution charts** (Overview)
- Type: horizontal bar chart, one per dimension (Role Category, Level, Track, Specialization,
  Classification Confidence)
- Title: the dimension name (e.g. "Level")
- Subtitle: total postings counted
- Axis: bar length = posting count; category labels on the y-axis, count on the x-axis
- Series colour: `gray-300` (neutral), except the Role Category chart which uses the three
  accent tokens (indigo/purple/emerald) per category, and any `unknown` bar in any chart which
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
| Operator clicks an ingestion run row | Expands (or navigates to) that run's per-source/per-company breakdown |
| Operator clicks "Refresh" on any view | Re-fetches current view's data; skeleton pulse shown during the fetch; view updates in place |
| Operator hovers a chart bar/segment | Tooltip shows exact count and percentage for that value |
| Operator clicks a chart bar for a specific value (e.g. `unknown` Level) | Navigates to Postings, pre-filtered to that exact value |

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

---

## Evaluation Metrics

| Metric | How measured | Target |
|---|---|---|
| Time to answer "what happened in the most recent run" | Observed usage / operator self-report | Under 30 seconds from opening the dashboard |
| Clicks to reach a single posting's full detail from Overview | Observed usage | 3 clicks or fewer |
| Frequency of falling back to direct database queries to answer a pipeline question | Operator self-report | Trends toward zero after adoption |
| Failure/error discoverability | Observed usage | Every classification or extraction failure is visible from the dashboard without cross-referencing logs |

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
