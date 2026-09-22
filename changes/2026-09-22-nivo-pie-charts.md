---
id: nivo-pie-charts
date: 2026-09-22
trigger-type: user-feedback
change-type: visual-change, technical-refactor
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Apply Nivo across all 4 Data Stories — a real 2-slice donut for genuine partitions

## Signal
See: `research/2026-09-22-nivo-pie-charts.md`. User: "ok can you apply this new chart library
to the Data Stories" — following yesterday's Story 1-only Nivo integration
(`changes/2026-09-22-nivo-charting-library.md`).

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — same as yesterday's change; no
new success criterion needed.

## Change Type
`visual-change` (product-wide — a new visual form, `SharePieChart`, added to the vocabulary) +
`technical-refactor` (3 real component swaps: `Meter` → `SharePieChart` in 3 story files). No
backend/API change — all 3 upgraded blocks use data the API already returns.

## Triage: evaluated all 4 stories, applied to exactly 3 blocks

Full reasoning in the research file. Summary: found a real, consistent pattern — 3 `Meter`-only
blocks (Story 1's pay transparency, Story 2's contraction-vs-expansion, Story 4's scale) are
all genuine 2-category partitions of a meaningful whole population (disclosed/undisclosed,
contraction/expansion, outside/inside the 3 tracked categories) — the exact shape a donut
communicates better than a single percentage bar. Built one shared `SharePieChart` component,
not 3 bespoke ones.

**Deliberately not touched — Story 3.** Its own `Meter` states a coverage/completion
percentage ("X of Y tracked roles have salary data reported"), not a 2-way partition — a donut
there would misrepresent what the number means. Combining Story 3's demand/pay rankings into
one chart was also considered and rejected: the two series (vacancy counts, salary figures) are
on wildly different scales, and a shared-axis chart would visually mislead, not clarify.

**A real, honest correction made along the way**: `data-stories.md`'s and the frontend
architecture spec's own descriptions of Story 2's and Story 4's blocks (and, on closer look,
Story 1's original pay-transparency description too) claimed a separate "Hero Figure" component
that was never actually built — all three always used `Meter` alone, with the magnitude figure
folded into its `complement` text. Corrected in the same pass rather than perpetuated.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Visual Design | `design/visual-design.md` | update — the real Meter-vs-donut dividing line, named explicitly |
| Experience Spec | `design/market-health/data-stories.md` | update — Story 1/2/4 block descriptions, plus the pre-existing "Hero Figure" inaccuracies corrected |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — new component, 3 story-section corrections, the Reference story's own pay-transparency line corrected |
| Plain-Language Overview | `OVERVIEW.md` | update — broadened the existing sentence to cover all 3 stories |
| Frontend Implementation | `SharePieChart.tsx` (new); `DataStoryMessage.tsx`, `EmploymentRiskStoryMessage.tsx`, `JobFunctionStoryMessage.tsx` (updated) | new/update |
| Dependencies | `frontend/package.json` | update — `@nivo/pie` added |
| Everything else (Story 3, backend, IA) | — | no-change — deliberately |

## Execution Plan

- [x] Step 1: Evaluated all 4 stories' real distinct-visual-form usage before touching anything — found Story 3 was closest to Story 1's original repetition problem, but rejected upgrading it (wrong shape of data, would mislead)
- [x] Step 2: Confirmed the exact real data shape for each of the 3 target blocks by reading the actual current component code, not assumed
- [x] Step 3: Confirmed `red-600`/`emerald-600` (Story 2's colours) against `visual-design.md`'s real documented semantic tokens before reusing them — same hues the World risk map already uses for the same real-world meaning
- [x] Step 4: Built `SharePieChart.tsx`, installed `@nivo/pie@0.99.0`
- [x] Step 5: Wired into all 3 blocks, removing now-dead `Meter`/`disclosedPct` code and unused imports (confirmed `Meter.tsx` itself stays alive via Story 3, its only remaining consumer)
- [x] Step 6: Real `tsc --noEmit` caught 1 real unused-import error per file touched (3 total) — all from removing `Meter` usage — fixed and reverified
- [x] Step 7: Real `npm run build` confirmed the lazy-loading discipline held: main bundle 131.86KB gzipped (vs. 131.57KB before this change — effectively unchanged), `SharePieChart` in its own 13.37KB gzipped on-demand chunk
- [x] Step 8: Real `npm audit` diff confirmed no new vulnerabilities from `@nivo/pie`
- [x] Step 9: Updated `visual-design.md`, `data-stories.md`, the frontend architecture spec, and `OVERVIEW.md` — including correcting the pre-existing "Hero Figure" inaccuracies found along the way

## Decision Log
- 2026-09-22: Applied to exactly 3 blocks, not all `Meter` usages — the real dividing line
  (2-way partition vs. coverage percentage) is a genuine data-shape distinction, not a style
  preference, and Story 3's `Meter` sits on the other side of it.
- 2026-09-22: Rejected combining Story 3's demand/pay rankings into one chart despite it being
  the story closest to Story 1's original "repeated form" problem — the two series' scale
  mismatch would make a combined chart actively misleading, a worse outcome than leaving 2
  Ranked bar lists as they are.
- 2026-09-22: Corrected 3 pre-existing spec inaccuracies (claimed "Hero Figure" components that
  were never built) found while updating these same sections, rather than let them stand.
