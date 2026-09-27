---
id: data-story-chart-variety
date: 2026-09-26
trigger-type: stakeholder-request
change-type: visual-change, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Diversify Data Story chart forms (bar-heavy → fit-for-data variety)

## Signal
See: `research/2026-09-26-data-story-chart-variety.md`. The stakeholder found the Data Stories
too repetitive in one chart form ("bar charts", corrected from a slip of "line charts") and
asked for variety **without applying the wrong chart to the data**. Story 2 (employment risk,
the world-map story) is explicitly out of scope — it is the reference example of variety.

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — "identify which roles and skills
are in demand", "set a realistic salary target", "see the trends clearly", and the 5-minute clear
read. No new success criterion is needed; this makes existing ones easier to meet. Same mapping
as the precedent `changes/2026-09-22-nivo-charting-library.md`.

## Change Type
- `visual-change` (product-wide: new entries in the Data Story visual vocabulary and a chart
  accessibility standard in `design/visual-design.md`, then per-story block changes).
- `api-change` (small, additive): Story 3's pay block needs the salary percentiles, and the
  `get_market_benchmark` MCP tool needs the same fields so an external AI can reproduce what the
  story shows. No new table, column, source or endpoint.

## What was found (evidence, 2026-09-26)

Current block inventory, 23 blocks across Stories 1–5:

| Form | Blocks |
|---|---|
| Ranked bar list | 11 (S1 ×2, S2 ×2, S3 ×3, S4 ×2, S5 ×2) |
| Nivo grouped bars | 6 (S1 skills + 3 year-on-year; S5 year-on-year + comparison) |
| 2-slice donut | 3 |
| Map / Meter / Hero figure | 1 each |

Story 3 is three ranked lists plus a meter. Story 1's Movement 2 is three identical grouped-bar
blocks. **Until ~August 2027 all three of Story 1's year-on-year blocks show only the current
window** (no prior year of data exists yet), so what a user sees today is the *current-only*
state of each — the redesign must be good in that state, not only once a comparison exists.

## Target composition (per story, after this change)

The rule: **no chart form repeats within one story unless the data genuinely needs it** (a
ranking question is best answered by ranked bars). Where a form repeats, the two blocks are
separated by other forms and the reason is recorded.

| Story | Block | Now | After | Why this form is honest for this data |
|---|---|---|---|---|
| **S1** | Roles being hired | Ranked bars | Ranked bars (unchanged) | A "top N" ranking — exact order matters |
| | What employers ask for | Grouped bars | Grouped bars (unchanged) | Two real series (must-have / nice-to-have) |
| | Pay transparency | Donut | Donut (unchanged) | Genuine 2-category partition |
| | Where the roles are | Ranked bars | Ranked bars (unchanged, **accepted repeat**) | Same ranking question as roles; separated by two other forms |
| | Role mix shift | Grouped bars | **Stacked 100% bar** (this year over a year ago, three role accent colours + legend) | Part-to-whole comparison of 3 categories across two periods |
| | Seniority shift | Grouped bars | **Ordered vertical columns** (junior → senior; lighter column = a year ago) | An ordered ladder is a distribution, not a ranking |
| | IC vs. management | Grouped bars | **Paired Stat Tiles** ("IC 84% ▲ 2 pp" · "Management 16% ▼ 2 pp") | Two shares summing to 100% need no chart |
| **S2** | all | — | **No change** | Explicitly out of scope |
| **S3** | Demand across roles | Ranked bars | Ranked bars (unchanged) | A ranking |
| | Coverage / pay availability | Hero + Meter | Hero + Meter (unchanged) | Coverage percentage, not a partition |
| | Typical pay by role | Ranked bars of the median | **Range chart** (P10–P90 whisker, P25–P75 band, median marker, per role, sample size shown) | Pay is a distribution; bars from zero exaggerate differences and hide the spread (already stored, never charted) |
| | Skills most associated | Ranked bars | Ranked bars (unchanged, **accepted repeat**) | A ranking; summed mentions are not part-to-whole, so no treemap |
| **S4** | What the wider picture looks like | Ranked bars | **Treemap** | Part-to-whole across ~11 functions with long labels; each tile also carries its count and % as text |
| | How much of all hiring | Donut | Donut (unchanged) | Genuine 2-category partition |
| | Most common titles | Ranked bars | Ranked bars (unchanged) | A ranking; now the story's only ranked list |
| **S5** | UK job vacancies | Hero figure | unchanged | |
| | By industry | Ranked bars | Ranked bars (unchanged) | A ranking; a treemap of 18 groups would leave many tiles too small to read |
| | By size of business | Ranked bars in size order | **Ordered vertical columns** (1–9 → 2,500+ employees) | The order is the meaning; columns read as a distribution |
| | Which industries are changing | Grouped bars | **Diverging change bars** around a zero line (thousands, ▲/▼ glyph on every row) | The question is up or down, not two levels |
| | Where our roles sit | Grouped bars | Grouped bars (unchanged) | Two separately-sourced share series; a dumbbell would visually stress a gap, which the spec forbids showing |

Net effect: Ranked bar lists 11 → 6, none adjacent; five forms new to the stories (stacked share
bar, ordered columns, Stat Tile pair, range chart, treemap) plus diverging bars. Every story other
than S2 gains at least one new form.

**Considered and not planned:**
- **Demand-vs-pay scatter (S3).** Only 8 roles are tracked, so it would be 8 points, and it would
  show pay a second time beside the range chart. Revisit only if demand-vs-pay becomes an actual
  user question and the tracked role set grows.
- **Treemap for S5 industries, or for S1 roles/cities.** Precise ranking matters more there than
  part-to-whole.
- **Line / slope charts for year-on-year.** Two points imply a trend that does not exist.
- **Pie/donut with >2 slices, radar, word cloud, a city bubble map** (only a minority of postings
  have a normalised location, so a map would look more complete than the data is).

## Quality criteria (from the stakeholder — these are the acceptance test)

1. **No repeated chart form within a story** unless recorded above as an accepted repeat.
2. **Clarity and statistical meaningfulness first.** Each form matches the data's job (table
   above). Every chart states its denominator and sample size; small samples are flagged, never
   silently charted; a range chart states what the whiskers mean ("the middle 80% of advertised
   salaries", to be confirmed against the source's own definition in the experience step); a
   comparison never implies a trend from two points.
3. **Visually attractive:** same palette discipline as today (one accent hue for the named
   series, `gray-600` for the muted comparator, the three role accents for role categories,
   red/emerald only where a real contraction/expansion meaning already exists), no new
   decoration, no entrance animation on data (unchanged rule).
4. **Every chart** has a title, a subtitle (what is measured, its unit, its window), a stated
   unit on values, and a legend naming every colour, glyph and shape (Rule 10 /
   `data-legibility`). Every data point is defined in plain words (`end-user-content`).
5. **Accessibility sizing — to be fixed as a standard in `design/visual-design.md`** and
   checked with the dataviz validator: chart text (labels, axes, legend, tooltip) at least 12px;
   values/labels not left at 10px (the current story "movement" eyebrow is 10px); interactive
   targets at least 24×24px; text contrast at least 4.5:1 and meaningful marks at least 3:1
   against the surface (the muted `text-gray-500` qualifier/attribution text on the dark surface
   looks to be below 4.5:1 — to be measured, and fixed story-wide if confirmed, since it is a
   one-token change); meaning never carried by colour alone (labels, ▲/▼ glyphs, or pattern);
   every chart has a "view as table" alternative and a one-sentence text summary for assistive
   tech; marks are keyboard-focusable with a visible focus ring; layout reflows to a narrow
   panel with no horizontal page scroll.
6. **MCP integration** — see the decision table below.

## MCP Access Review (Rule 12 — decided here, recorded in `ACCESS.md` + `backend/specs/mcp-access/api.md` when `/new-backend-spec` runs)

Data stories themselves stay **not exposed** (unchanged — `outcomes/bring-your-own-ai-agent-access.md`:
"data primitives, not pre-written reports"; chart form is a presentation choice and never an
MCP concern). What matters is that **every number a redesigned block shows is reachable through a
primitive tool, with the same definition wording.** Checked against the real tools on 2026-09-26:

| Data behind a changed block | Reachable via | Decision |
|---|---|---|
| S1 role / seniority / track share, this year vs. a year ago | `get_job_demand` (`group_by` role_category / level / track + `date_from`/`date_to` for each window) | **Exposed already — no change.** No "year-on-year" tool is added: that would be a pre-composed report. |
| S3 salary range (P10, P25, median, P75, P90) + sample size per role | `get_market_benchmark` returns only `salary_median` and `salary_sample_size` | **Gap → Exposed (extend existing tool, additive):** add `salary_p10`, `salary_p25`, `salary_p75`, `salary_p90` and `salary_unit` to each `roles[]` entry, and state the percentile definition in the tool's `meta`. Same scope (`jobs.read`), same plan tier, same `is_source_usable` licence gate, same attribution in `meta.source`. No new tool. |
| S4 function breakdown | `get_job_function_breakdown` (functions, `other_count`, `total_count`, `not_yet_reprocessed`) | **Exposed already — no change.** |
| S5 size-of-business, industry, change vs. a year ago | `get_trusted_statistics` (`dimension` = size_band / industry, `period="year_ago"`; each series carries `unit`, `definition_note`, `source`) | **Exposed already — no change.** |
| Chart type, colours, legend, tiles, table view | — | **Not exposed:** presentation layer, not data. |

**Definition parity (the part of "MCP integration" beyond reachability):** a data point's
definition (e.g. what P10–P90 means, what "business size" means, what "share of postings" is
measured over) is written **once** and used by both the story's subtitle/qualifier and the MCP
tool's `meta`, so a user reading the story and an external AI describing the same number use the
same words. The backend spec decides where that single source of truth lives.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change (no UX principle changes; AI Involvement not touched) |
| Information Architecture | `design/information-architecture.md` | no-change (no navigation or taxonomy change) |
| Visual Design | `design/visual-design.md` | **update** (v2.0 → v2.1): new vocabulary entries (Stacked share bar, Ordered columns, Diverging change bars, Range chart, Treemap, Stat Tile pair), the chart accessibility standard, and the "no repeated form within a story" composition rule |
| Experience Spec | `design/market-health/data-stories.md` | **update**: Stories 1, 3, 4, 5 block descriptions; the "Visual standard every story must meet" checklist gains the no-repeat rule, the view-as-table requirement and the accessibility sizing. **Story 2 untouched.** |
| Experience Spec (other) | `design/market-health/experience.md`, `design/ai-reasoning-panel`, `design/feedback`, `design/mcp-access` | review for references to the changed vocabulary; expected no-change |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **update**: new chart components, new Nivo package(s) and lazy-loading, per-story block wiring, table-view pattern |
| Backend Spec | `backend/specs/market-health/api.md` | **update**: Story 3 pay section payload gains the percentiles and unit; Story 1 current-only/role-mix contract if the decision below changes it |
| Backend Spec (MCP) | `backend/specs/mcp-access/api.md` | **update**: `get_market_benchmark` response and `meta` definition |
| Backend Spec (scraped) | `backend/specs/scraped-data-sources/api.md` | no-change (the percentile columns already exist) |
| Frontend Implementation | `frontend/src/features/market-health/stories/` | **update** (new chart components; Stories 1, 3, 4, 5 renderers; `package.json`) |
| Backend Implementation | `backend/src/market_stories.py`, `market_query.py`, `mcp_access/tools.py`, tests | **update** (small, additive) |
| Plain-Language Overview | `OVERVIEW.md` | **update** (users will notice the new charts) |
| MCP Access Review | `ACCESS.md` + `backend/specs/mcp-access/api.md` | **update** — decisions above; runs automatically inside `/new-backend-spec` |
| Polite Scraping Review | `DATA_SOURCES.md` | not-applicable (no scraped source introduced or changed; the percentile columns are already stored) |
| Data Surface Review | stories / admin / query path | not-applicable — **no new data category** (existing columns and existing aggregates, re-presented). Its ad-hoc-query-path question was still answered above in the MCP table |

## Open decisions to settle at the experience step (recommendations, not yet decided)

1. **S1 role-mix block before a prior year exists (until ~Aug 2027).** A current-only stacked bar
   would repeat the welcome's current role split, which the de-dup rule forbids. *Recommendation:*
   show only the "comparison starts {Month Year}" notice for this one block until the comparison
   exists. The seniority columns and IC/management tiles are not in the welcome, so they keep a
   useful current-only state.
2. **Small-sample threshold for the S3 range chart** (which role gets a "small sample" flag) — pick
   the number from the real `salary_sample_size` distribution, not a guess.
3. **Treemap tail handling for S4** — minimum tile size before a tile is grouped into a labelled
   "smaller functions" tile. `unknown` stays its own real tile (existing rule: never folded away).
4. **Range chart implementation** — hand-drawn accessible SVG (like the world map) versus a Nivo
   package; decided in the frontend spec.

## Step 1 result — `design/visual-design.md` v2.0 → v2.1 (2026-09-26)

Added: seven forms (Stacked share bar, Ordered columns, Diverging change bars, Range chart, Treemap,
Stat Tile pair, and Time series — the last expanded from "Trend line" with the specifics requested by
the parallel Story 5 change `changes/2026-09-26-story-5-tech-lens.md`); a "choose the form by the
data's job" table; a strengthened no-repeat rule; the **Chart accessibility standard**; the chart
**definition pattern** (one wording shared with the MCP tools); unit rules for currency / thousands /
index / sample size; a shape-and-glyph legend rule. Story 2 and the World risk map are unchanged.

**Measured, not assumed** (dataviz validator run as an ES module + WCAG ratios; reference surface is
`gray-800`, because stories render inside the AI turn):
- `gray-500` **text** = 3.04:1 on `gray-800` (needs 4.5) → ❌. Small text on stories moves to `gray-400` (5.78:1).
- `gray-600` muted series = 1.94:1 → ❌; `gray-500` = 3.04:1 → ✅ at the floor. Muted series is now `gray-500`.
- `gray-700` "a year ago" fill = 1.42:1 → ❌ (not a valid data mark).
- Treemap text: `gray-900` on `indigo-400` = 5.95:1 ✅; on `indigo-500` only 3.97 ❌, white 4.47 ❌. A grey "unknown" tile
  beside `indigo-400` fails the normal-vision floor (ΔE 14.4 < 15) → non-named tiles are hollow (outlined) instead.
- `red-600` + `emerald-600` → all checks pass. `indigo-500` + `gray-500` → pass (ΔE 18.5).
- ⚠️ **`indigo-500` (Designer) + `purple-500` (Product Manager) FAIL** — ΔE 0.9 under protanopia, 11.3 with
  normal vision (hard floor 15). **Pre-existing**, affects the trend chart and Category Share Bar too.
  Mitigated for the new stacked bar (Design → Engineering → Product Management order + direct labels).
  A validated replacement exists: `indigo-500` · `pink-500` · `emerald-600` passes every check.

**Knock-on effects the later steps must carry:**
- Frontend: donut muted complement constants `#4b5563` → `#6b7280` (Story 1 pay, Story 4 scale — Story 2's
  donut uses red/emerald and is unaffected); the muted series in `SkillDemandChart`, `YearOnYearGroupedBars`,
  `SourceComparisonBars`; `StoryBlock` qualifier and the story eyebrow, Hero/Stat labels, `StoryFeedbackReaction`
  label `gray-500` → `gray-400` / 12px. **These are shared components, so Story 2's caption text lightens
  slightly too** (its charts, map and layout are untouched) — flagged as an open decision below.
- Every chart gets "Show as table", an `aria-label` summary, keyboard access, ≥ 24px hit areas.

## Open decisions added at Step 1 — RESOLVED 2026-09-26 by the stakeholder

- **5 → done, as its own change:** `changes/2026-09-26-role-palette-accessibility.md`. Product Manager
  `purple-500` → **`fuchsia-600`** and Engineer `emerald-500` → `emerald-600` (the first-proposed `pink-500` was
  replaced after it failed against the "declining" red — disclosed in that CR). `visual-design.md`, the
  frontend spec line, the 3 frontend files and `admin.css` are already updated; the stacked share bar uses the new
  colours.
- **6 → accepted:** Story 2's caption text lightens (`gray-500` → `gray-400`) via the shared components.
- **7 → deferred:** the accessibility follow-ups outside Data Stories are **not** part of this or any current
  change; to be raised later.

*(Original text of the three decisions, kept for the audit trail:)*

5. **Fix the role palette?** Designer/Product Manager (`indigo-500`/`purple-500`) are indistinguishable to a
   protanopic reader and too close for full-colour readers. Recommend a **separate change request**
   (`visual-change`, product-wide: trend chart, tags, Category Share Bar, stories) adopting
   `indigo-500` · `pink-500` · `emerald-600`. Not done here — a role colour is a brand decision.
6. **Shared caption tokens touch Story 2.** Lightening the qualifier/eyebrow/label text from `gray-500` to
   `gray-400` is an accessibility fix applied through shared components, so Story 2's captions get slightly
   lighter (nothing else about it changes). Recommend accepting; the alternative — an exemption for Story 2
   — would leave one story with failing contrast.
7. **Accessibility follow-ups outside Data Stories** (not in this change's scope, found while measuring):
   the trend chart's 10px axis text; the Welcome's and Task Panel's `gray-500` 10px eyebrow; the Feedback
   Panel captions and input placeholder in `gray-500`. Recommend one small `visual-change` CR for them.

## Execution Plan

- [x] Step 1: ✅ `/new-visual-design` — `design/visual-design.md` v2.1: vocabulary entries, accessibility standard (contrast measured with the dataviz validator — results above), no-repeat composition rule, legend/definition pattern
- [x] Step 2: ✅ `/new-experience` — `design/market-health/data-stories.md` updated for Stories 1, 3, 4 (Story 2 untouched; Story 5's block 4a is another session's work, re-read before every edit, left untouched). Decisions:
  1. **Story 1 role-mix (block 6):** no chart before the year-ago window exists — a current-only bar would repeat the Welcome's Category Share Bar. Blocks 7 (seniority, ordered columns) and 8 (IC/mgmt, stat tile pair) do show current-year data, since neither is in the Welcome.
  2. **Story 3 range-chart small-sample threshold:** `salary_sample_size < 30` (the standard floor for a stable percentile estimate) — no live DB access to fit a real distribution, so `/implement-backend` must check real sample sizes against this and flag back if wrong.
  3. **Story 4 treemap tail:** a Job Function under 3% of the outside-3-categories total merges into a "{N} smaller functions" aggregate tile; `unknown` never merges. `/implement-backend` to confirm against the real distribution.
  4. **Story 3 range-chart build:** recommended hand-drawn SVG (no Nivo box-and-whisker package installed) — final call deferred to the frontend spec, as planned.
  Net form count: Ranked bar list 11 → 6 (unchanged from Step 1's plan); Stories 1, 3, 4 and 5 each now use 3+ distinct forms with no unintentional repeat.
- [x] Step 3: ✅ Reviewed `market-health/experience.md`, `mcp-access/experience.md`, `provenance-panel.md`, `job-classification.md`, `foundations.md`, `information-architecture.md` — no stale chart-vocabulary references found. `market-health/experience.md`'s Welcome Category Share Bar is a fixed product-wide component outside this change's scope (unaffected by the Data Story vocabulary or, in colour, already handled by `changes/2026-09-26-role-palette-accessibility.md`). Other hits were the `seniority`/`level` taxonomy field, unrelated to chart forms.
- [x] Step 4: ✅ `/new-backend-spec` — `backend/specs/market-health/api.md` (Story 3: percentile fields, `employment_type` never blended, the 30-sample threshold + open verification, and the shared `data_definitions.py` mechanism, spec-only — no `.py` file written, confirmed with the Story 5 session first), `backend/specs/mcp-access/api.md` (`get_market_benchmark` gains the percentile fields, `salary_unit`, `employment_type`, and `meta.definitions`, additive/non-breaking), `ACCESS.md` (Market benchmark datasets row — no new MCP-exposure decision needed, same tool/scope/tier). Verified `ACCESS.md` had been touched concurrently by the Story 5 session (its own, separate row) — no conflict, confirmed by re-reading before editing.
- [x] Step 5: ✅ `/new-frontend-spec` — `frontend/specs/market-health/architecture.md` updated: 6 new hand-rolled components (`StackedShareBar`, `OrderedColumns`, `StatTilePair`, `RangeChart`, `Treemap`, `DivergingChangeBars`) + 1 shared primitive (`ShowAsTable`), no new npm dependency for any of them; none needs `React.lazy` (no heavy dependency to defer). Story 1 blocks 6–8, Story 3's pay block, Story 4's function block, and Story 5's size/industry-shift blocks rewired. **`YearOnYearGroupedBars.tsx` flagged as dead code** — confirmed by grep that this change removes its only two callers (Story 1 share-mode, Story 5 level-mode); `/implement-frontend` re-confirms and deletes it. Retrofitting pre-existing charts (`SharePieChart`, `SkillDemandChart`, `WorldRiskMap`) with the new accessibility standard recorded as explicitly out of scope. Coordinated with the Story 5 session: `UkVacanciesStoryMessage.tsx` is now a file both changes touch (their block 4a; my blocks 4 and 5) — no conflict, re-read at implementation as usual.
- [x] Step 6: ✅ `/implement-backend`. Added `benchmark.salary.percentiles` to the existing `data_definitions.py` (re-read fresh first, both of the Story 5 session's keys untouched). Extended `market_stories.py`'s `build_market_benchmark_story()` and `market_query.py`'s `query_market_benchmark_data()` — both had their own separate, pre-existing SQL for `market_observations` (not shared code), so both SELECTs and row-shaping were extended in parallel, matching that existing duplication rather than introducing a new shared layer. Added `salary_p10/p25/p75/p90`, `salary_unit`, `employment_type`, a server-computed `small_sample` flag (`salary_sample_size < 30`), and a `definitions` dict (non-empty only when at least one role has salary data). `mcp_access/tools.py`'s `get_market_benchmark` now copies `result["definitions"]` into `envelope["meta"]["definitions"]` — same pattern `get_trusted_statistics` already established, not a new one. **Tests:** created `tests/test_data_definitions.py` (the traceability check `data_definitions.py`'s own docstring already promised but that didn't exist yet — verifies every key is referenced somewhere and every literal `DEFINITIONS[...]` lookup resolves to a real key; passes for both this change's key and the Story 5 session's two) and `tests/test_market_benchmark_pay.py` (a mocked-DB unit test — deviates from this suite's usual "skip if no DATABASE_URL" convention, disclosed in the file's own docstring, because the thing being tested is pure row-shaping logic, not SQL). All new tests pass; full regression re-run of `test_mcp_access.py` (9), `test_source_licences.py` (4) also clean, verified in the real WSL venv (not just import-checked). No frontend touched.
- [x] Step 7: ✅ `/implement-frontend`. Built 6 new hand-rolled components + 1 shared primitive (`StackedShareBar`, `OrderedColumns`, `StatTilePair`, `RangeChart`, `Treemap`, `DivergingChangeBars`, `ShowAsTable`) — none uses Nivo or any new dependency. Wired into `DataStoryMessage.tsx` (Story 1 blocks 6–8), `MarketBenchmarkStoryMessage.tsx` (Story 3 pay), `JobFunctionStoryMessage.tsx` (Story 4 function breakdown), `UkVacanciesStoryMessage.tsx` (Story 5 blocks 4 and 5 — block 4a re-read fresh and left untouched). Fixed `StoryBlock.tsx`'s `qualifier` colour (the known gap flagged by the Story 5 session) plus the same stray `text-gray-500` in the story eyebrow/attribution/legend lines across the four files this step touched (not a full retrofit — Story 2 and the not-yet-touched pre-existing charts stay out of scope, as decided at the frontend-spec step).

  **`tsc --noEmit` and `npm run build` both clean** (1109 modules). Main bundle: 445.60 kB / 143.02 kB gzip (was 422.24 kB / 136.26 kB before this step) — a real, measured +6.76 kB gzip from the 6 new non-lazy components, as expected (none needed deferring). The `YearOnYearGroupedBars` lazy chunk is gone from the build output.

  **Two real gaps found and fixed while wiring, beyond the frontend spec's own plan:**
  1. *Story 1's seniority block had no real ladder order to render in.* The generic year-on-year backend endpoint sorts every dimension by current-window count descending — right for a ranking, wrong for `OrderedColumns`' "order is the meaning" contract. Fixed client-side with a `LEVEL_LADDER_ORDER` constant (`design/market-health/job-classification.md`'s documented order — the backend has no ordered constant, only an unordered `set`).
  2. *Story 4's treemap needed server-computed shares, kind flags, and the 3%-merge* — the frontend spec assumed this existed; `query_job_function_data()`/`build_job_function_story()` only returned raw counts. Added a shared pure function, `market_query._job_function_tiles()`, imported by both (matching this codebase's existing "duplicate the SQL, share the pure shaping logic" pattern) — computes share, classifies each row `named`/`aggregate`/`unknown`, and merges anything under 3% (never `unknown`). Covered by a new `tests/test_job_function_tiles.py` (6 tests, all passing) — this is a small, disclosed extension of Step 6's backend scope, done here rather than left as a silent mismatch between spec and code.

  **`YearOnYearGroupedBars.tsx` — confirmed dead by a fresh grep, but not fully deleted.** Its two render functions and the level-mode types (`LevelYoYRow`/`LevelYoYContent`) had zero remaining callers and were removed. `YoYRow`/`YearOnYearContent` are kept — `DataStoryMessage.tsx` still uses them to type-parse the raw section content before reshaping it for the new components. The file now holds only those two type exports plus a header explaining what was removed and why (this project's "mark removed, don't erase" convention).

  **Verification, given no browser automation tool is available in this environment (confirmed by the parallel session):** built a temporary `react-dom/server` harness (esbuild-bundled, deleted after use, confirmed by `git status` afterward) rendering all 7 new components against realistic data covering every real state — comparison vs. no-comparison, small-sample vs. full vs. range-not-reported, named/aggregate/unknown/single/empty tiles, positive/negative/zero deltas. All 16 checks passed with no `NaN`/`undefined`/`[object Object]` in the output; the `RangeChart` and `Treemap` markup was also inspected directly and its computed pixel/percentage positions checked by hand against the input data (e.g. a whisker from £48,000–£85,000 on a £40k–£90k domain lands at exactly x=160–900 of 1000). **Not verified: actual visual rendering in a real browser** — layout, colour contrast on real pixels, and keyboard behaviour still need that check, folded into Step 8.

  **Backend regression** (full re-run in the real WSL venv): `test_market_benchmark_pay` (4), `test_data_definitions` (3), `test_job_function_tiles` (6, new), `test_mcp_access` (9), `test_source_licences` (4), `test_curated_match` (0 failures) — all green.
- [x] Step 8: ✅ Verified against **real, live production data** (a working `DATABASE_URL` exists in this environment — confirmed by connecting and counting `raw_postings`: 9,885 rows). Fetched the actual `market-data-briefing`, `market-benchmark`, `beyond-tracked-roles`, and `uk-vacancies-official` story payloads straight from the real backend functions (no mocks), then rendered the real `DataStoryMessage`/`MarketBenchmarkStoryMessage`/`JobFunctionStoryMessage`/`UkVacanciesStoryMessage` components against them via a temporary `react-dom/server` harness (esbuild-bundled, deleted afterward, confirmed by `git status`). All four rendered cleanly with no bad tokens, and every new component actually appears in the real output (confirmed by presence checks, not just absence of errors). Spot-checked real numbers by hand: Story 3's `RangeChart` shows real percentile spreads (e.g. Data Engineer: median £70,000, P10 £45,000–P90 £100,000, n=1,518, correctly not flagged small); Story 4's `Treemap` correctly merged 4 real functions each under 3% share into "4 smaller functions" (6.1%) while keeping the real `unknown` tile (3.2%) separate, exactly as designed. This is stronger evidence than the earlier synthetic-data check — it exercises the real backend query, the real row-shaping, and the real component tree together, end to end, against data nobody hand-picked.
  **Still not verified — the one gap a browser alone could close:** actual visual layout, colour contrast on real rendered pixels, and interactive keyboard behaviour (focus rings, arrow-key stepping) in a real browser window. No browser automation tool exists in this environment (confirmed independently by the parallel session). Recorded as a known, disclosed limitation, not silently skipped.
- [x] Step 9: ✅ `OVERVIEW.md` updated — added a plain-language paragraph (dated 2026-09-27) describing the four stories' new chart forms in end-user terms (no "treemap"/"diverging"/"stacked" jargon), plus the new "Show as table", keyboard, and screen-reader support.
- [x] Step 10: ✅ `ACCESS.md` and `backend/specs/mcp-access/api.md` reconfirmed against what was actually built (Step 6) — `get_market_benchmark`'s additive percentile fields and `meta.definitions` match the spec exactly (verified live in Step 8's harness, not just by reading the code). No further MCP-exposure decision needed. **Change marked `complete`** — see frontmatter.

## Decision Log
- 2026-09-26: Mapped to `understand-market-health-before-searching` (bucket A), same as the 2026-09-22 Nivo precedent, without a separate confirmation round — the stakeholder had already approved the direction and criteria.
- 2026-09-26: Classified `visual-change` (product-wide vocabulary) + `api-change` (additive percentiles). Not `new-feature` — no new capability, source or table.
- 2026-09-26: Story 2 excluded per the stakeholder.
- 2026-09-26: Dropped the S3 demand-vs-pay scatter from the original proposal: 8 tracked roles is too few points to be statistically meaningful and it duplicates the range chart's pay information. Recorded above so it can be revisited.
- 2026-09-26: Kept ranked bars for S5 industry (18 groups too many for a legible treemap) and accepted one separated repeat of ranked bars in S1 and S3, because both are genuine ranking questions.
- 2026-09-26: Step 1 measured contrast instead of assuming it and changed two existing tokens on story surfaces (muted series `gray-600` → `gray-500`; small text `gray-500` → `gray-400`) because they failed. The role-palette failure was **recorded, not silently fixed** (open decision 5). A parallel session (`changes/2026-09-26-story-5-tech-lens.md`) adds one Story 5 time-series block; agreed that this change owns `visual-design.md` and the Time series entry, and that it owns its own block in `data-stories.md` and the S5 code region — the two changes stay in separate files/regions and neither commits until the PM says all sessions are finished. Ping that session so its block 4a can be checked against the Time series entry.
- 2026-09-26: **Shared-definition mechanism adopted** (proposed by the Story 5 session, accepted here so there is only one): a new pure-constants module `backend/src/data_definitions.py` holding `DEFINITIONS: dict[str, str]`, keyed by stable dotted ids (this change's first key: `benchmark.salary.percentiles`, the P10–P90 / P25–P75 / median wording). Story composers take subtitle/how-to-read/qualifier text from it; MCP tools put the same string in `meta.definitions = {key: text}`; a test fails on an unused key or a reference to a missing one. No stored-data change. Whichever `/implement-backend` runs first creates the file; the other only adds its own keys. Specs cite "`data_definitions.py`, key X" instead of restating the wording. To be written into `backend/specs/market-health/api.md` (Story 3) and `backend/specs/mcp-access/api.md` (`get_market_benchmark`) at Step 4.
- 2026-09-26: `/data-surface-review` and `/polite-scraping-review` judged not applicable (no new data category, no scraped-source change); the MCP review is applicable and its decisions are recorded above.
