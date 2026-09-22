---
id: nivo-charting-library
date: 2026-09-22
trigger-type: user-feedback
change-type: visual-change, technical-refactor
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Add Nivo as the product's charting library, starting with Story 1

## Signal
See: `research/2026-09-22-nivo-charting-library.md`. User asked for a free, high-quality
charting library specifically to add visual variety to "What we know about the market," which
was leaning heavily on the same Ranked bar list form. Recommended Nivo (MIT); user confirmed
"lets go with Nivo, your recommendation," then mid-turn: "make sure all of this is well
documented."

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — "they can see the trends
clearly" is served directly by real comparison charts replacing forms that under-communicated
the same data (an opacity difference nobody reliably notices; a hand-rolled ghost bar). No new
success criterion needed.

## Change Type
`visual-change` (product-wide — a new entry in the visual vocabulary, `design/visual-design.md`
— Charting library) + `technical-refactor` (a real component swap: `YearOnYearBars` removed,
replaced by `YearOnYearGroupedBars`; the skill-demand aggregation logic reshaped to keep two
real series instead of collapsing them). No backend/API change — both upgraded blocks use data
the API already returns; only the frontend aggregation and rendering changed.

## What was built

1. **`nivoTheme.ts`** — a single shared theme mapping every Nivo theme slot to
   `design/visual-design.md`'s own dark palette (text gray-400, axis/grid gray-700/gray-800,
   tooltip gray-800/gray-700 border). No chart in this product renders with Nivo's own
   light-theme defaults.
2. **`SkillDemandChart.tsx`** — a real grouped bar chart, must-have vs. nice-to-have as two
   named series with an explicit legend, replacing a single Ranked bar list that only
   distinguished the two by bar opacity (a difference the story's own inline caption had to
   explain in words — a real data-legibility improvement, not just a visual one).
3. **`YearOnYearGroupedBars.tsx`** — replaces the hand-rolled `YearOnYearBars.tsx` (deleted,
   real dead code once nothing imported it) with a real grouped bar chart for the current-vs-
   prior-year comparison, keeping the same "no prior window yet" single-window fallback
   behaviour and the same generic reuse across role_category/level/track.
4. **Lazy-loaded**, not bundled statically — `React.lazy` + `Suspense` in `DataStoryMessage.tsx`
   for both new components, after a real build showed the naive static-import approach grew
   the main bundle from 130KB to 218KB gzipped and triggered Vite's >500KB chunk warning. A
   second real build confirmed the fix: main bundle back to 131KB gzipped, Nivo's ~86KB gzipped
   weight in its own on-demand chunk.
5. **`@nivo/radar` installed, then removed** — considered for a future skill-intensity-by-role-
   category chart, no story currently has data shaped for it; installing it unused would have
   been designing for a hypothetical, the exact anti-pattern this framework's own
   `implement-frontend`/`implement-backend` skills warn against.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Visual Design | `design/visual-design.md` | update — new "Charting library" section (v1.7 → v1.8), a note on the superseded skill-demand emphasis pattern |
| Experience Spec | `design/market-health/data-stories.md` | update — Story 1's skill-demand and YoY block descriptions, the visual-forms vocabulary list |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — new/renamed components, new "Charting library" section documenting the lazy-load fix with real measured numbers |
| Plain-Language Overview | `OVERVIEW.md` | update — one sentence noting richer charts on the existing story |
| Frontend Implementation | `nivoTheme.ts`, `SkillDemandChart.tsx`, `YearOnYearGroupedBars.tsx` (new); `YearOnYearBars.tsx` (deleted); `DataStoryMessage.tsx` (updated) | new/update/delete |
| Dependencies | `frontend/package.json` | update — `@nivo/bar`, `@nivo/core`, `@nivo/theming` added; `@nivo/radar` added then removed (unused) |
| Everything else (backend, other stories, IA) | — | no-change |

## Execution Plan

- [x] Step 1: Confirmed the real, specific target (Story 1's repeated Ranked bar list pattern) before installing anything
- [x] Step 2: Installed `@nivo/core`/`@nivo/bar`/`@nivo/radar`, confirmed via a real `npm audit` diff that none of the 17 pre-existing vulnerabilities trace to Nivo
- [x] Step 3: Built `nivoTheme.ts` against real palette tokens read directly from `visual-design.md`
- [x] Step 4: Built `SkillDemandChart.tsx`, reshaped the skill aggregation in `DataStoryMessage.tsx` to keep must-have/nice-to-have as two real series instead of one collapsed number
- [x] Step 5: Built `YearOnYearGroupedBars.tsx`, confirmed via a real grep that `YearOnYearBars.tsx` had exactly one consumer before deleting it
- [x] Step 6: Real `tsc --noEmit` caught 2 real type errors (wrong theme type import; an invalid `legends.hover` theme key) — both fixed against the installed package's actual type definitions, not assumed
- [x] Step 7: Real `npm run build` measured the bundle-size regression (130KB → 218KB gzipped, Vite's own >500KB warning) — not left as a known cost; fixed with `React.lazy`/`Suspense`, confirmed by a second real build
- [x] Step 8: Removed the unused `@nivo/radar` install rather than leave it as a speculative, unbuilt dependency
- [x] Step 9: Updated `visual-design.md`, `data-stories.md`, `frontend/specs/market-health/architecture.md`, `OVERVIEW.md` — every doc surface a prior story's own visual-form change has updated
- [x] Step 10: Final `tsc --noEmit` + `npm run build` clean after all changes, including the dependency removal

## Decision Log
- 2026-09-22: Chose 2 concrete, justified upgrades (skill demand, year-on-year shifts) over
  "add Nivo everywhere for variety" — matches the user's own "apply only those that make sense"
  instruction, and the visual standard checklist's actual complaint (repeated ranked-list form,
  not "not enough chart types in the abstract").
- 2026-09-22: Lazy-loading was not optional once measured — a real build showed a genuine
  regression, not a hypothetical one, so it was fixed in this same change rather than deferred.
- 2026-09-22: Removed the unused `@nivo/radar` dependency rather than keep it "for later" —
  no story has data shaped for a radar chart yet; that's a real future change once one does,
  not a reason to carry an unused package now.
