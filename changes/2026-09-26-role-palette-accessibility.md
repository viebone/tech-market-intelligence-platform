---
id: role-palette-accessibility
date: 2026-09-26
trigger-type: internal
change-type: visual-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Make the three role colours distinguishable (Product Manager purple → fuchsia, Engineer emerald-500 → emerald-600)

## Signal
See: `research/2026-09-26-role-palette-accessibility.md`. Found by measuring the palette with the `dataviz`
validator during `changes/2026-09-26-data-story-chart-variety.md`; the stakeholder then directed "fix the role
palette with your fix".

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — "they can see the trends clearly". A trend
chart whose Designer and Product Manager lines are the same colour to a protanopic reader (and only ΔE 11.3
apart to everyone else) does not meet it. Operator side: `outcomes/pipeline-processing-visibility.md` (the
admin dashboard's role bars use the same colours) — no criterion change needed for either.

## Change Type
`visual-change` (product-wide — the role accent tokens in `design/visual-design.md`).

## The change

| Role | Was | Now | Why |
|---|---|---|---|
| Designer | `indigo-500` #6366f1 | **unchanged** | anchor of the palette |
| Product Manager | `purple-500` #a855f7 | **`fuchsia-600` #c026d3** | purple failed against indigo (ΔE 0.9 protan / 11.3 normal) |
| Engineer | `emerald-500` #10b981 | **`emerald-600` #059669** | emerald-500 sat outside the dark lightness band (0.696 vs ≤ 0.67); -600 passes and is the existing "Rising" semantic token |

**Measured** (dataviz validator, `--mode dark --pairs all`, surfaces `gray-800` and `gray-900`):
- Lightness band ✅ · chroma floor ✅ · contrast vs surface ✅ (indigo 3.29/3.97, fuchsia 3.12/3.77, emerald 3.90/4.71).
- Normal-vision floor ✅ worst pair ΔE **18.6** (fuchsia↔indigo; needs 15).
- CVD separation ⚠️ WARN — worst pair **fuchsia↔indigo ΔE 6.5 (deutan)**; in the 6–8 band that is legal **only with
  secondary encoding**, which the Chart accessibility standard already requires (direct labels, 2px gaps; roles
  never touch, order Design → Engineering → Product Management).
- Against the semantic colours a role can share a view with: fuchsia-600 vs red-600 ΔE 25.5, vs amber-600 32.2,
  vs emerald-600 37.9 (all ✅).

**Deviation from what was proposed to the stakeholder:** the palette recommended earlier was `pink-500`. Checked
against the semantic reds it fails (pink-500 vs red-600, ΔE 14.5 < 15), i.e. it would have swapped one failure
for another wherever a Product Manager line and a "declining" indicator share a view. Fuchsia-600 was the only
candidate of eleven with no hard failure. **Reversible** — the colour is a handful of constants (below); swap to
pink-500 if the stakeholder prefers it, accepting the pink/red warning.

**Known, accepted limits:** fuchsia-600 is only 3.12:1 on `gray-800` (the story surface) — passes 3:1 with little
margin, so it must never be made darker; and Engineer `emerald-600` is now exactly the "Rising" semantic hue
(it was already near it as emerald-500) — direction is always also carried by a ▲/▼ glyph and text, so no
meaning depends on telling them apart.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | **update** — Accent palette table, Category Share Bar and Charting-library colour rules, and the v2.1 accessibility sections that recorded the failure |
| Experience Spec | `design/pipeline-visibility/experience.md` | **update** — two prose mentions "(indigo/purple/emerald)" → "(indigo/fuchsia/emerald)" (lines ~185, ~239) |
| Experience Spec | `design/market-health/experience.md`, `data-stories.md` | review — no hard-coded role hues found; `data-stories.md` is also being edited by other sessions, so nothing is written there by this change |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **update** — the "Designer/indigo-500, Product Manager/purple-500, Engineer/emerald-500" line (~193) |
| Backend Spec | `backend/specs/**` | no-change (no backend spec names a role hue) |
| Frontend Implementation | `JobOpeningsChart.tsx`, `WelcomeMessage.tsx`, `nivoTheme.ts` | **update** — hex constants |
| Backend Implementation | `backend/src/admin_static/admin.css` | **update** — `.bar-fill.role-product-manager`, `.bar-fill.role-engineer` (operator dashboard, static CSS) |
| Plain-Language Overview | `OVERVIEW.md` | no-change — it describes capabilities and never names a colour |
| MCP Access Review | `ACCESS.md` | not-applicable — no backend capability changes |
| Polite Scraping Review | — | not-applicable |
| Data Surface Review | — | not-applicable — no data category |

## Execution Plan

- [x] Step 1: ✅ `/new-visual-design` — Accent palette table + the Category Share Bar, Charting-library, Chart-accessibility-standard (rule 6, contrast table, separation results), stacked share bar and "rules out" text in `design/visual-design.md`, with the measured results and the pink→fuchsia rationale recorded
- [x] Step 2: ✅ Experience specs reviewed — `pipeline-visibility/experience.md` updated (2 mentions); no hard-coded role hue in `market-health/experience.md` or `data-stories.md`
- [x] Step 3: ✅ Frontend spec colour line updated (`frontend/specs/market-health/architecture.md`)
- [x] Step 4: ✅ `/implement-frontend` — `JobOpeningsChart.tsx`, `WelcomeMessage.tsx`, `nivoTheme.ts`, `admin.css`; grep shows the old role hex now only in explanatory comments
- [x] Step 5: ✅ Verify — `tsc --noEmit` clean, `npm run build` clean, validator re-run on the exact hexes in code (all checks pass on `gray-800` and `gray-900`; one legal CVD warning, fuchsia↔indigo ΔE 6.5). **Partially closed by `changes/2026-09-26-data-story-chart-variety.md`'s Step 8:** that step fetched real production data and rendered the real `DataStoryMessage`/`StackedShareBar` component tree end to end — confirming the new role colours (`#6366f1`/`#059669`/`#c026d3`) actually render correctly on real data, for the story surface. **Still genuinely open:** the trend chart (`JobOpeningsChart.tsx`) and the Welcome's own Category Share Bar (`WelcomeMessage.tsx`) were not exercised by that check (neither is part of the four data stories) — their colours are correct by code inspection and the `tsc`/build pass, but not confirmed by an actual render. No browser automation tool exists in this environment to close that last gap.
- [x] Step 6: ✅ Marked `complete` — see frontmatter. The one remaining gap (trend chart / Welcome visual render) is recorded here rather than silently dropped, and applies equally to every other visual change in this session for the same reason (no browser tool available).

## Decision Log
- 2026-09-26: Stakeholder approved fixing the role palette with the proposed fix and accepted Story 2's caption text lightening; other low-contrast text (trend-chart 10px axis, Welcome/Task Panel eyebrows, Feedback Panel captions, input placeholder) explicitly **deferred** — not in this change.
- 2026-09-26: Replacement colour changed from the proposed `pink-500` to `fuchsia-600` after checking against the semantic colours (see "Deviation"). Disclosed to the stakeholder; reversible.
- 2026-09-26: Treated as its own change request, not folded into `data-story-chart-variety`, because it touches the trend chart, the Welcome and the operator dashboard as well as the stories (Rule 8: every change gets its own audit record).
