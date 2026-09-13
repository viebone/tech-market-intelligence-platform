---
id: employment-risk-world-map
date: 2026-09-13
trigger-type: user-feedback
change-type: ux-change, api-change, visual-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: World map for Employment risk across the market

## Signal
See: `research/2026-09-13-employment-risk-world-map.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — "see employment risk alongside
demand... at the company and sector level" and the original framing for this whole
employment-events pipeline: "provide a full picture of the market but showing hiring but also
layoffs." A map answers "where" more directly than a ranked list.

## Change Type
`ux-change` (reorders and replaces a block in Story 2) + `api-change` (the country aggregate
needs a direction split it doesn't have today) + `visual-change` (a genuinely new entry in the
Data Story visual vocabulary, product-wide).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Visual Design | `design/visual-design.md` | update — new "World risk map" vocabulary entry + Data Legibility legend convention for it |
| Experience Spec | `design/market-health/data-stories.md` | update — Story 2's Visible answer shape reordered, "By country" block replaced, Data contract table's country aggregate revised |
| Backend Spec | `backend/specs/market-health/api.md` | no-change — the story endpoint's `sections[].content` is already documented as a free-form per-section shape; the real content contract lives entirely in `data-stories.md` (already updated) |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — new `WorldRiskMap` component, new dependencies |
| Backend Implementation | `backend/src/market_stories.py` | update |
| Frontend Implementation | `frontend/src/features/market-health/{EmploymentRiskStoryMessage,WorldRiskMap}.tsx`, `package.json` | update/new |

## Execution Plan

- [x] Step 1: Capture signal — `research/2026-09-13-employment-risk-world-map.md`
- [x] Step 2: Update `design/visual-design.md` (manual edit — World risk map vocabulary + legend)
- [x] Step 3: Update `design/market-health/data-stories.md` (manual edit — reordered blocks, new data contract)
- [x] Step 4: Update `backend/specs/market-health/api.md` (manual edit — section content shape)
- [x] Step 5: Update `frontend/specs/market-health/architecture.md` (manual edit)
- [x] Step 6: Implement backend — `market_stories.py`'s country aggregate grouped by `country, direction`; section reordered to lead the story
- [x] Step 7: Implement frontend — `react-simple-maps` + `world-atlas` (50m, verified — 110m drops Singapore/Malta), `WorldRiskMap.tsx`, wired into `EmploymentRiskStoryMessage.tsx`
- [x] Step 8: Verify — real API response shape confirmed (29 real countries, correct contraction/expansion split, section correctly leads), `npm run build` clean. Found and fixed a real bundle-size regression along the way: importing the topology as a JS module grew the main bundle 262KB->1.1MB (gzip 82KB->352KB); moved it to `public/` served as a fetched static asset instead — 360KB main bundle (gzip 118KB), topology loads lazily only when this story opens.

## Decision Log
- 2026-09-13: Folium rejected in favour of a native React component — see research file for
  the full reasoning (rendering-paradigm consistency, dark theme, live re-render, contract
  consistency with every other data-story block).
- 2026-09-13: `world-atlas`'s 50m topology, not the more commonly used 110m — verified the 110m
  version silently drops Singapore and Malta, both real countries in this product's data.
- 2026-09-13: Colour encodes **net** direction (expansion minus contraction, by jobs affected),
  reusing the existing `emerald-600`/`red-600` semantic tokens (no new accent colour) — a
  country with no reported events in the window gets a neutral, undecorated fill, never
  implied to be "calm" (same "zero events is a different message" rule as the direction-split
  block).
- 2026-09-13, follow-up (real user feedback after deploy): the map appeared cropped at the top
  ("Alaska not very visible"). Root cause: d3's default `geoEqualEarth` scale (~177) is tuned
  for a ~960x500 canvas; at 800x400 it overflows and clips the poles. Fixed with
  `projectionConfig={{ scale: 140, center: [0, 15] }}` and `height` 400->440 — the centre shift
  trades unused Antarctica margin (no country in this dataset is there) for full Arctic
  visibility (Alaska/Scandinavia/Russia are all real data points). `npm run build` clean;
  visual confirmation of the exact framing is pending the user's next look, not yet re-verified
  in a live browser from this environment.
