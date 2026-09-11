---
id: data-legibility-market-health
date: 2026-09-11
trigger-type: user-feedback
change-type: visual-change, content-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Apply the new data-legibility principle to Market Health's data stories

## Signal
See: `research/2026-09-11-data-legibility-market-health.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — "A professional can look at one
view and know whether now is a good or bad time to search" depends on every figure being
readable unaided, not just present.

## Change Type
`visual-change` (product-wide — the shared `StoryBlock`/`YearOnYearBars` components every
story is built from) + `content-change` (the actual subtitle/legend copy for each block).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change — already covers "clear market read"; no new success criterion needed |
| Visual Design | `design/visual-design.md` | update — new "Data Legibility" section (per the framework's `data-legibility` skill); "Data Story composition" block anatomy gains a `subtitle` slot; Year-on-year comparison spec gains a rendered colour legend |
| Experience Spec | `design/market-health/data-stories.md` | update — "Visual standard every story must meet" checklist gains a subtitle/unit requirement; Story 1 and Story 2 block descriptions specify their real subtitle text |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — `StoryBlock`/`YearOnYearBars` component responsibilities note the new subtitle/legend |
| Backend Spec | `backend/specs/market-health/api.md` | no-change — no data/response-shape change, presentation-layer only |
| Frontend Implementation | `frontend/src/features/market-health/{StoryBlock,YearOnYearBars,DataStoryMessage,EmploymentRiskStoryMessage}.tsx` | update |
| Backend Implementation | `backend/src/` | no-change |

## Execution Plan

- [x] Step 1: Capture signal — `research/2026-09-11-data-legibility-market-health.md`
- [x] Step 2: Update `design/visual-design.md` (manual edit — new Data Legibility section + Data Story composition/Year-on-year updates)
- [x] Step 3: Update `design/market-health/data-stories.md` (manual edit — checklist + per-block subtitle text)
- [x] Step 4: Update `frontend/specs/market-health/architecture.md` (manual edit)
- [x] Step 5: Implement — `StoryBlock` subtitle slot, `YearOnYearBars` colour legend, subtitle text wired into both stories' renderers
- [x] Step 6: Verify — `npm run build` clean (`tsc` + `vite build`, no errors), every block reviewed against the `data-legibility` checklist

## Decision Log
- 2026-09-11: Unit stated **once per block, in the subtitle** — not repeated on every
  `RankedBarList` row. A per-row suffix ("21,880 jobs affected" × 10 rows) is noisier than
  stating it once where the block already establishes context, matching how a well-labelled
  chart states its unit in an axis/subtitle rather than on every point.
- 2026-09-11: `YearOnYearBars`'s ghost/solid bar colour legend was found during this audit,
  not in the original feedback — included here since it's the same class of gap (colour
  carrying meaning with no explanation) and the fix touches the same shared component pass.
- 2026-09-11: No backend/data-model change — every fix is presentation-layer (subtitle copy,
  a new legend line); the underlying data contract already states these facts precisely
  (`data-stories.md`'s Data contract tables), the gap was only in what reached the user.
- 2026-09-11: found and fixed a real, unrelated stale-spec bug while in this file —
  `data-stories.md`'s Story 2 Data contract table still said "Trailing 90 days" in its Window
  row after the window was revised to 12 months (`changes/2026-09-11-employment-risk-12-month-window.md`);
  the intro prose had been updated, the table row hadn't. A wrong stated window is exactly the
  kind of "data not correctly explained" this change exists to catch — fixed inline rather
  than opening a separate change request for one stale table cell.
