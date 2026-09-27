---
id: story-5-tech-lens
date: 2026-09-26
trigger-type: stakeholder-request
change-type: ux-change, api-change
outcome: understand-market-health-before-searching
status: in-progress
---

# Change Request: Story 5 gains a "Tech and communications" block

## Signal
See: `research/2026-09-26-story-5-tech-lens.md`

PM: "on story 5 ... we need to make it useful for the tech market. can we extract from those trusted
stats anything related to tech industry?" — then approved option 1 (a block built from already-ingested
data) with "ok go ahead".

## Outcome
See: `outcomes/understand-market-health-before-searching.md` (primary — a tech professional reading the
market before searching; a tech-sector official vacancy trend serves "identify which roles and skills
are in demand vs. declining" and the 5-minute market read). Secondary:
`outcomes/job-data-source-flexibility.md` (the trusted-statistics source type Story 5 reads).
Neither's success criteria change. **Triage note:** the PM was not asked to confirm the primary outcome
separately; the mapping is stated here so it can be redirected.

## Change Type
`ux-change` (a new block inside the existing Story 5 — what it shows, its visual form, its caveats) and
`api-change` (a new section in the story's response, built from a query the story composer does not
make today). **No new ingestion, no new table, no new source.**

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change (checked by `/new-experience` when it reads them) |
| Information Architecture | `design/information-architecture.md` | no-change — a block inside an existing story, no navigation or taxonomy change |
| Visual Design | `design/visual-design.md` | review; **update only if** the block needs a chart form the vocabulary lacks (see Open Questions 2) |
| Experience Spec | `design/market-health/data-stories.md` | update — Story 5 revised in place: new block, its place in the movements, qualifiers, empty states |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — Story 5 section (`UkVacanciesStoryMessage` + whatever the block renders with) |
| Backend Spec | `backend/specs/market-health/api.md` | update — Story 5 section table gains one section id |
| Backend Spec (source) | `backend/specs/trusted-statistics/api.md` | review — update only if `query_trusted_statistics_data` cannot return one industry's history alongside the total (Open Questions 3) |
| Frontend Implementation | `frontend/src/features/market-health/stories/` | update |
| Backend Implementation | `backend/src/market_stories.py` (+ tests) | update |
| Plain-Language Overview | `OVERVIEW.md` | update — the UK vacancies capability gains a tech lens |
| MCP Access Review | `ACCESS.md` + `backend/specs/mcp-access/api.md` | update — runs automatically inside `/new-backend-spec`. Not a new capability (the `get_trusted_statistics` tool already reaches section J), but the "J is not tech" caveat must reach external AI clients too (Open Questions 4) |
| Polite Scraping Review | — | not-applicable (ONS is a published file download, no scraped source) |
| Data Surface Review | — | not-applicable as a full review (no new data category — same VACS02 series). **One check carried into the backend spec:** the chat tool `query_trusted_statistics_data` must be able to answer "how are tech vacancies trending?" — Rule 14 item 4 |

## Open Questions (to be resolved by the named step, not before)

1. **Where does the block sit?** Story 5 is three labelled movements (right now / shifting / vs our roles).
   A fourth movement, or a block inside Movement 2 ("how it's shifting")? A fourth changes the story's
   stated standard. → `/new-experience`.
2. **Which chart form?** Story 5 already uses Hero Figure, ranked bar list (×2), year-on-year grouped
   bars and a two-series comparison; the new block must not duplicate one of them (PM criteria on
   `research/2026-09-26-data-story-chart-variety.md`: no repeated charts within a story, clarity and
   statistical meaning first). The data is a ~7-year trend of one industry against the whole market, at
   three-month resolution — the honest form for that is a time series, and the product's own visual
   vocabulary has none for a Data Story. → `/new-experience`, then visual-design review.
3. **Read path.** Whether `query_trusted_statistics_data` can already return J for several periods plus
   `AP2Y` in one call, or needs a small addition. → `/new-backend-spec`.
4. **Where the "J is broader than tech" caveat lives for external AI.** The stored J series'
   `definition_note` is generic ("Estimated job vacancies ... in this industry (SIC 2007)"). Options:
   story copy + MCP tool docstring only (no re-ingest), or also strengthen that series' stored note
   (needs a re-ingest or a data migration). → `/new-backend-spec` with `/mcp-access-review`.
5. **Which baseline year** ("since 2019" vs "since 2022 peak" vs both) and whether section M is shown as
   "tech-adjacent". → `/new-experience`; the evidence table is in the research file.

## PM decisions (2026-09-26, after the change request was shown)

- **Q1 placement — decided:** place the block in the order that tells the story; a **time series** is the
  wanted form. → `/new-experience` picks the exact slot (candidate: straight after the UK-wide total and
  the industry ranking, before "how it's shifting", so the reader goes: how big → where → how it moved
  over the years → the last year's changes → how that compares with our roles).
- **Q2 chart form — decided by Q1:** time series.
- **Q3 read path — decided:** yes, add whatever small read-path change is needed.
- **Q4 (caveat for external AI) — PM did not follow the question; re-explained in plain words in chat.**
  Still undecided; **default proposal (2026-09-26, prompted by `f2`'s v2.1 rule that a data point's definition wording lives in ONE place shared by the story and the MCP tool `meta`):** write the "J is broader than tech" definition once, in the backend, and use it in both block 4a's qualifier and `get_trusted_statistics`' `meta` for the industry series — no re-ingest, no change to stored series notes. Settled in `/new-backend-spec`.
- **Q5 baseline — decided:** start "from wherever we have solid data". Checked 2026-09-26 against the
  production DB: section J and the all-industries total both run **Apr–Jun 2001 to Jun–Aug 2026, 303
  periods, no gaps** (298 final, 4 revised, 1 provisional). So the series starts in 2001, the earliest
  point ONS publishes — no cut-off needed. It includes the 2008–09 slump, the 2020 low (14k) and the
  2022 peak (78k), so the story is honest about a long run, not a hand-picked window.
- **Coordination — decided:** do not mix this change with other sessions' work; coordinate with them;
  **commit only when all sessions have finished their work** (not before), one clean commit per change.

## Coordination with other sessions (2026-09-26)

- **`changes/2026-09-26-data-story-chart-variety.md`** (`visual-change` + `api-change`, `triaged`, owner
  session **`f2`** (identified 2026-09-26; `4f` confirmed it is not theirs) — `f2` owns the v2.1 edit of
  `design/visual-design.md`, in progress): edits the *other* Story 5 blocks
  (ordered columns, diverging change bars) and `design/visual-design.md` v2.0→2.1. **Rules this change
  follows:** (1) only ADD a block — never edit Stories 1–4 or an existing Story 5 block; (2) re-read each
  shared file immediately before each edit, edit only inside this change's own block/section; (3) never
  edit `design/visual-design.md` — `f2` agreed (reply received) to expand the existing Trend line into a
  general Time series entry and was given this block's specifics; (4) the new block must meet that CR's acceptance
  criteria (no repeated form within a story, ≥12px chart text, view-as-table, one-sentence text summary,
  meaning never by colour alone, title + subtitle + unit + legend); (5) its MCP table already says Story 5
  data is reachable through `get_trusted_statistics` — this change keeps that true for the J history.
- **`changes/2026-09-26-personio-adapter.md`** and the uncommitted headcount/licensing edits: unrelated to
  Story 5. Files this change does NOT touch: `backend/src/sources/*`, `employer_headcount.py`,
  `industries.py`, `requirements.py`, `source_licences.py`, `admin_main.py`, `LICENSING.md`,
  `DATA_SOURCES.md`, `EMPLOYER_PANEL.md`, `trusted_stats/crosswalks.py`.
- **Commit rule:** nothing is staged or committed by this session until the PM says every session is
  done. Then: list this change's files explicitly (never `git add -A`), commit them as their own commit.
- **Files both changes are expected to touch** (so whoever commits knows to check): `design/market-health/data-stories.md`,
  `backend/specs/market-health/api.md`, `frontend/specs/market-health/architecture.md`,
  `backend/src/market_stories.py`, `frontend/src/features/market-health/stories/UkVacanciesStoryMessage.tsx`,
  `OVERVIEW.md`, `ACCESS.md`, `CLAUDE.md`. `backend/specs/market-health/api.md` is **already modified in the
  working tree by the Personio change** (one table row + one line) — a shared-file commit will need
  `git add -p`, not a whole-file add.

## Execution Plan

- [x] Step 1: `/new-experience` (**drafted 2026-09-26, awaiting PM review** — `design/market-health/data-stories.md`, Story 5: new block **4a** "Tech and communications vacancies since 2001" in Movement 2, plus two example phrasings, the forms sentence, one data-contract row and five honesty bullets. Design choice to confirm: both lines are **indexed** (same months in 2019 = 100) because thousands can't share an axis; real thousands are in the labels, tooltip and table.)
- [x] Step 2: Visual-design — **DONE 2026-09-26: `f2`'s v2.1 landed; block 4a checked against its Time series entry and Chart accessibility standard, and aligned (axis title wording, aria-label + announced tooltip, table caption). Two intended differences: lines are 2px (not 1.5), small text gray-400 at 12px minimum — both inherited from the standard.** Owned by the chart-variety change (session `f2`, edit in progress); this
      change does not edit `design/visual-design.md`.** Correction to the triage: the vocabulary already lists
      a **Trend line** form (`visual-design.md` Data Story vocabulary; spec in `design/market-health/experience.md`
      Chart Specification), so no new form is needed — `f2` is expanding it into a general Time series entry in
      v2.1 and was sent this block's specifics (indexed to a common base, no dual axis, direct end labels,
      peak + latest markers, hollow provisional point, no event annotations, arrow-key stepping, view-as-table).
      Also from `f2`: muted comparator series is now **gray-500** (gray-600 measured 2.35:1, under the 3:1
      needed) and small caption/legend text **gray-400** — block 4a uses those. After v2.1 lands, re-read it and
      confirm block 4a matches; add block-specific detail only in the Story 5 spec, not the vocabulary.
- [x] Step 3 (**DONE 2026-09-26**, spec `ready` for review; nothing implemented): `/new-backend-spec` — update `backend/specs/market-health/api.md` Story 5 (new section id,
      content shape, `limitations`, provenance); review `backend/specs/trusted-statistics/api.md`; **runs
      `/mcp-access-review` automatically** (Open Questions 4); confirm the chat tool can answer the
      question (Rule 14 item 4).
- [x] Step 4 (**DONE 2026-09-27**, spec `ready` for review; nothing implemented): `/new-frontend-spec` — update `frontend/specs/market-health/architecture.md` Story 5 section
      (API contract must match Step 3).
- [x] Step 5 (**DONE 2026-09-27**, all tests pass): `/implement-backend` — `market_stories.py` (+ tests, incl. empty/insufficient-data and
      rounding-caveat cases); chat tool if Step 3 requires.
- [x] Step 6 (**DONE 2026-09-27**, `tsc --noEmit` + `npm run build` both clean): `/implement-frontend` — the block; `tsc` + `vite build` clean.
- [x] Step 7 (**DONE 2026-09-27**): Verify against real data, not fixtures — render the live story from the production DB and
      read the visible copy for jargon and ISO dates (lesson from the first Story 5 build); run
      `data-legibility` over the new block; open it in a real browser (Story 5's charts have never
      been checked in one).
- [x] Step 8 (**DONE 2026-09-27**): Update `OVERVIEW.md`; `ACCESS.md` if Step 3's decision changes it; `CLAUDE.md` spec-chain
      status line for Story 5.
- [ ] Step 9: Commit **only this change's files** (the working tree holds unrelated uncommitted Personio /
      headcount work); deploy only on the operator's explicit go, batched with other real changes (a
      docs-only push redeploys every service and drops live MCP sessions).

## Out of scope — separate change requests if wanted
- Ingesting the VACS02 `job openings rate` sheet (vacancies per 100 jobs — would say whether tech hiring
  is tight or slack, not just how large). A new measure, so it would need `/data-surface-review`.
- Any other ONS dataset (online job adverts by occupation, workforce jobs by industry). Never inspected;
  no claim made about their contents.
- A separate tech-only story (advised against — it would compare "our roles" against a group that does
  not match them).

## Decision Log
- 2026-09-27: **Post-Step-8 touch-up.** `f2`'s chart-variety frontend implementation landed in the shared
  `UkVacanciesStoryMessage.tsx` (swapped the size block to `OrderedColumns`, "Which industries are
  changing" to `DivergingChangeBars`, fixed `MovementLabel` and the file's other stray `text-gray-500`
  spots to `text-gray-400`) and, as promised, fixed `StoryBlock.tsx`'s shared qualifier-colour bug.
  Re-read the file fresh, confirmed block 4a's own JSX (heading, `TechCommsTrendChart` props, position)
  untouched by them. Simplified block 4a's own qualifier rendering back to the normal `blockProps(...)`
  path now that the shared fix has landed, removing the manual gray-400 workaround and its now-stale
  comment. `tsc --noEmit` clean afterward.
- 2026-09-27: **Documentation updated (Step 8).** `OVERVIEW.md`: added the tech-and-communications trend
  as a new bullet under the existing UK-vacancies capability. **Found and fixed a pre-existing gap while
  there**: `OVERVIEW.md` never mentioned Story 5 at all since its 2026-09-24 launch (said "Four standing
  reports", listing only the first four) — a real miss from that change, not this one; corrected the
  count to five and named it, flagged inline as "corrected here, missed at the time" per this file's own
  "flag it, don't quietly fix it" rule. `CLAUDE.md`: added a dated note to each of the three Story 5 rows
  (Experience Specs, Backend Specs, Frontend Specs) describing this change's addition and its real
  verification results; each note ends "**Spec + code written, not yet committed or deployed**" so the
  status table stays accurate until Step 9. `ACCESS.md` needed no further edit — the Step 3 MCP decision
  ("not exposed", the indexed series is a pre-composed report) was already recorded there.
- 2026-09-27: **Verified against real production data (Step 7).** No browser automation tool is
  available in this session (only `WebFetch`, which refuses `localhost`, and nothing is deployed yet
  to fetch instead) — deploying just to look would need the operator's go, which hasn't been given.
  Did the strongest check actually possible instead: called `market_stories.get_story(...)` live
  against the **production** database (read-only) and confirmed the real numbers match what was
  quoted to the PM earlier (36k now vs 43k in 2019, peak 78k Apr–Jun 2022, 303 points, no gaps,
  latest flagged provisional); the existing visible-copy check (no "SIC"/"dataset"/raw ISO date) was
  re-run against this block's own text and passed. Then bundled `UkVacanciesStoryMessage.tsx` with
  esbuild (a temporary harness, deleted after) and rendered it with real `react-dom/server` against
  that same live payload — **stronger than the original Story 5 build's own SSR check**, since
  `TechCommsTrendChart` isn't lazy and so actually renders (the original check only reached a loading
  fallback for its two Nivo blocks). Confirmed in the real HTML output: both `<path>` elements carry
  303 real, non-empty coordinates (no `NaN`, no `undefined`); the latest marker renders **hollow**
  (`fill="#1f2937"`, `stroke="#6366f1"`) because the real latest ONS figure is provisional right now;
  the peak marker, both end labels, the legend (with its "Hollow point…" line), both year-axis ticks,
  the 100 gridline, the `aria-live` region, the "Show as table" button, and the qualifier line at
  `text-gray-400` (confirming the `StoryBlock` workaround actually works) are all present with the
  exact expected text; the table itself correctly does not render until toggled (collapsed by
  default). Block order confirmed: size → **tech-and-communications** → shift, inside "How it's
  shifting". The other five Story 5 blocks (unaffected by this change) still render their real
  figures with no regression. **Rule 14 item 4, settled with real numbers, not a guess:** the MCP
  tool's full published history for the `J` series is ~52 KB / ~13,000 estimated tokens; the
  docstring's suggested 2019-onward range is ~18 KB / ~4,500 tokens. Decision: keep this as **stated
  guidance in the docstring, not a hard-enforced cap** — a single deliberate trend call at ~13k tokens
  is not a meaningful cost or context risk on today's models, and the guidance already steers toward
  the smaller range for the common case; revisit only if real usage shows models ignoring the
  guidance. `data-legibility` checklist re-applied to block 4a specifically: title, subtitle with
  scope/unit, y-axis unit, legend for both colour and shape (dashed vs. solid, hollow vs. filled),
  table caption with unit, and a first-time reader can restate any point from the tooltip/announcement
  alone — satisfied. Still not done, and not claimed: an actual visual check in a real browser window
  (no tool for it in this session) and a real Postgres integration test (standing gap across
  `trusted-statistics` generally, not introduced by this change).
- 2026-09-27: **Frontend implemented (Step 6).** New file `TechCommsTrendChart.tsx` — hand-rolled inline
  SVG per the frontend spec: indexed two-line chart (solid indigo group line, dashed gray-400 comparator),
  peak/latest markers (latest drawn hollow when provisional), direct end labels (dropped below 480px in
  favour of the legend line), one-sentence aria-label + `aria-live` announcement kept in sync with
  keyboard (arrows/Home/End) and mouse-hover focus, a "Show as table" disclosure, and the summary
  sentence — all wording taken verbatim as props, nothing composed client-side. Wired into
  `UkVacanciesStoryMessage.tsx` as the first block of Movement 2 ("How it's shifting"), before "Which
  industries are changing". **Not a lazy import** (no heavy dependency to defer), matching the spec.
  **The flagged `text-gray-500` issue**: fixed for block 4a specifically — its qualifier line is rendered
  inline at `text-gray-400`, bypassing `StoryBlock`'s buggy `qualifier` prop rather than editing the
  shared `StoryBlock.tsx` (still `f2`'s to fix, unchanged by this commit). `tsc --noEmit` and
  `npm run build` both clean; the new chunk is small enough to sit in the main bundle un-lazy as
  intended. **Not yet checked in a real browser** — tracked as Step 7, same standing gap the original
  Story 5 build already had for its two chart blocks.
- 2026-09-27: **Backend implemented (Step 5).** New files: `backend/src/data_definitions.py` (created —
  this change reached `/implement-backend` first, per the agreed rule; `f2` will add
  `benchmark.salary.percentiles` to this same file, not a new one, when they reach their own).
  Changed: `market_query.py` (`query_trusted_statistics_data` now accepts `date_from`/`date_to` as an ISO
  string or a `date`, and returns a top-level `definitions` dict), `market_stories.py` (new
  `_tech_comms_points` pure function + `_tech_comms_section`, wired into `build_uk_vacancies_story`
  between the size and year-on-year blocks; `_UK_SECTION_TITLES` gained the new id), `mcp_access/tools.py`
  (`get_trusted_statistics` passes `definitions` through as `meta.definitions`; docstring gained the
  history hint and the J-breadth instruction; simplified to let the shared function do date parsing).
  **6 new tests added** to `backend/tests/test_trusted_stats.py` (index maths against the real ONS
  fixture — J 43k→36k since the 2019 base, peak 78k in Apr–Jun 2022, matches production; the
  insufficient-history and no-base pure-function edge cases; the empty-story state; `date_from` as string
  and as `date`; the MCP tool's `meta.definitions`; `data_definitions.py`'s own completeness). **2
  existing tests updated** (the section-id list and the attribution loop now include
  `uk-tech-and-communications`) — a deliberate, spec-driven change to Story 5's shape, not a fix.
  **All 61 tests in `test_trusted_stats.py` pass** (`venv/Scripts/python.exe ../tests/test_trusted_stats.py`
  from `backend/src`, this repo's plain runner — no pytest installed here), plus the untouched
  `test_mcp_access.py` (9), `test_story_yoy.py` (3), `test_feedback.py` (7) re-run clean as a regression
  check since they touch `market_stories`/`market_query`. Not yet run against a live Postgres (same
  standing caveat as the rest of `trusted-statistics`). Nothing committed.
- 2026-09-27: **Frontend spec written (Step 4).** New component `TechCommsTrendChart.tsx` — hand-rolled
  inline SVG (no `@nivo/line` dependency; not currently installed and this block's per-series dash pattern,
  conditional hollow marker, and exact-point keyboard stepping are more than Nivo's line chart gives without
  fighting its API — same reasoning Story 5 already used once for its delta glyphs, and the World risk map
  used for its own custom SVG). Wired between "Vacancies by size of business" and "Which industries are
  changing" in `UkVacanciesStoryMessage`. Uses `gray-400` (not `gray-500`) for its own legend/summary/caption
  text, per the Chart accessibility standard `f2` published in v2.1.
- 2026-09-27: **Flagged, not fixed:** `StoryBlock`'s `qualifier` slot and the existing cross-check block's
  `legend` paragraph in `UkVacanciesStoryMessage` still render `text-gray-500`, which the new accessibility
  standard retires for story text. Out of this change's scope (shared component / pre-existing code); the
  chart-variety change owns that standard's rollout. `/implement-frontend` re-checks whether `f2` has fixed
  it before this change ships, and fixes block 4a's own paragraph regardless of whether the shared fix has
  landed yet.
- 2026-09-26: `f2` reports the role-palette change done (`changes/2026-09-26-role-palette-accessibility.md`); the files
  listed in the previous entry are free again. Final palette: Designer indigo-500, Product Manager fuchsia-600,
  Engineer emerald-600. Block 4a unaffected. `f2` starts chart-variety Step 2 (`data-stories.md`, Stories 1, 3, 4, 5)
  next and will work around block 4a.
- 2026-09-26: **Ownership settled:** `f2` owns `changes/2026-09-26-data-story-chart-variety.md` (`4f` withdrew).
  `f2` is starting a separate role-colour palette change (Product Manager → fuchsia-600, Designer indigo-500,
  Engineer emerald-600). **Files this change must not touch until `f2` says done:** `design/visual-design.md`,
  `frontend/src/features/market-health/JobOpeningsChart.tsx`, `WelcomeMessage.tsx`,
  `frontend/src/features/market-health/stories/nivoTheme.ts`, `admin.css`, and the frontend spec's colour line.
  Block 4a uses no role colours (indigo-500 primary + gray-500 dashed comparator), so its design is unaffected;
  if `/implement-frontend` wants `nivoTheme.ts` for the chart, wait for `f2` or re-read it first.
- 2026-09-26: **Backend spec written (Step 3).** New section `uk-tech-and-communications` in
  `backend/specs/market-health/api.md` (Story 5): two reads of the existing function, alignment on common
  periods, index = 100 × value ÷ own value in the same months of 2019, all visible strings composed
  server-side, peak/latest/table derived from the same points, `insufficient_data` rules, tests listed.
  **Read-path finding (PM's "add whatever is needed"):** the full history is reachable with no new query,
  but `query_trusted_statistics_data`'s `date_from`/`date_to` were **unannotated** (siblings use
  `str | None`) — the chat tool's schema for them was unreliable, so a chat trend question was not
  actually reachable. Fix specified (annotate; accept `str` or `date`) in both the market-health and
  trusted-statistics specs. The result also gains a top-level `definitions` dict (shared wording).
- 2026-09-26: **MCP Access Review (Rule 12) — decided.** No new tool. `get_trusted_statistics` is extended
  additively: `meta.definitions` + docstring (history hint, J-breadth caveat). The indexed series is
  **not exposed** as a pre-composed report (recorded in "What's deliberately not a tool"); the primitives are
  already exposed. `ACCESS.md` trusted-statistics row updated. Only my regions were edited
  (`get_trusted_statistics`, the not-a-tool list, the trusted-statistics ACCESS row); `git diff` on
  `ACCESS.md` shows only that one row changed.
- 2026-09-26: **Data Surface Review (Rule 14) — the one live check answered:** the ad-hoc chat path reaches
  the new view only after the `date_from` annotation fix above; chat token cost of a full-history result is
  bounded by docstring guidance (`date_from` ≥ 2019 unless asked) and must be **measured during
  verification** — if too large it becomes a hard cap. No new data category, no admin change: the admin
  statistics views already list the J series and every stored period.
- 2026-09-26: Polite Scraping Review not-applicable (unchanged).
- 2026-09-26: **Shared-definition mechanism agreed with `f2` (also recorded in their CR):** pure-constants
  `backend/src/data_definitions.py` — `DEFINITIONS: dict[str, str]` keyed by dotted ids; stories import from it,
  MCP responses carry `meta.definitions = {key: text}`; a test fails on an unused or missing key. This change's
  first key: `ons.industry.J.breadth`. `f2`'s: `benchmark.salary.percentiles`. Whichever `/implement-backend`
  runs first creates the file; the other re-reads and only adds its keys. Resolves Open Question 4 (no re-ingest).
- 2026-09-26: **Waiting on PM** to confirm the indexed two-line design of block 4a before `/new-backend-spec`.
- 2026-09-26: **Block 4a designed (Step 1).** Placement: Movement 2, before the year-on-year block — the story
  reads how big → where → how it got here → what changed lately → how our roles sit. Form: two-line trend
  line, both series **indexed** (same months in 2019 = 100) because 14–78 thousand and 400–1,257 thousand
  can't honestly share an axis and two axes are never used; thousands stay visible in labels/tooltip/table.
  Range: the full published history from Apr–Jun 2001 (PM: "from wherever we have solid data"). No event
  annotations or verdict words (no cause is in the data). Open Question 2's claim that the vocabulary had no
  time-series form was wrong — a Trend line form exists (corrected in Step 2).
- 2026-09-26: Number "4a" used for the new block so the other change's blocks 5–6 keep their numbers.
- 2026-09-26: Classified `ux-change` + `api-change`, not `new-feature` — it is a new block inside an
  existing story, on data already stored; no new source, table, or route (Story 5 is a catalogue
  operation, same pattern as Stories 2–4).
- 2026-09-26: Data Surface Review recorded as not-applicable in full — same shape (VACS02 industry series)
  presented differently; the one live concern (chat can reach it) is a named check in Step 3, not a review.
- 2026-09-26: Polite Scraping Review not-applicable — ONS is a file download under OGL v3.0, nothing scraped.
- 2026-09-26: **Overlap flagged** — `research/2026-09-26-data-story-chart-variety.md` (PM, same day, no CR
  yet) reviews chart forms across all Data Stories, Story 5 included. Whichever CR reaches
  `/new-experience` second re-reads Story 5 as the other left it; neither may assume the other's block
  list.
- 2026-09-26: Working tree carries unrelated uncommitted changes (Personio adapter, employer headcount,
  CLAUDE.md, licensing docs). This change must not be mixed into that commit.
