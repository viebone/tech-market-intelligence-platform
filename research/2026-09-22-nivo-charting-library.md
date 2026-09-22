---
source: user-feedback
date: 2026-09-22
---

User: "we need something for the charts, we need variety, apply only those that make sense, but
they need more variety, specially on 'What we know about the market', which library would you
recommend that is free to use and provides amazing graphics?"

Recommended Nivo (MIT licensed) over Recharts (lighter, less variety) and ECharts (most
variety, but a config-object API that fights the existing component architecture) — real
variety (Bar, Line, Radar, Sankey, TreeMap, Calendar, Bump, Sunburst...), native React
components, full theming API to match the existing dark palette exactly. User: "lets go with
Nivo, your recommendation" — then, mid-turn: "make sure all of this is well documented."

Concrete target identified before building anything: "What we know about the market" repeats
the Ranked bar list form three times (roles, skills, cities) plus three more hand-rolled
year-on-year comparisons — exactly the "under-composed" pattern `data-stories.md`'s own visual
standard checklist warns against. Two real, justified upgrades chosen — not variety for its
own sake: the skill-demand block (must-have vs. nice-to-have, currently only an opacity
difference) and the three year-on-year shift blocks (currently a hand-rolled ghost-bar
comparison). A third candidate (a Radar chart comparing skill intensity across the 3 role
categories) was considered and explicitly not built this pass — no story currently has the
data shaped for it; installing `@nivo/radar` speculatively and leaving it unused was reverted.

Real cost found and fixed before shipping, not left as a known issue: adding Nivo statically
grew the production bundle from 130KB to 218KB gzipped and triggered Vite's own >500KB chunk
warning. Fixed with `React.lazy` + `Suspense` on both new components — confirmed by a second
real build that the main bundle returned to 131KB gzipped with Nivo's ~86KB gzipped weight
split into its own on-demand chunk.
