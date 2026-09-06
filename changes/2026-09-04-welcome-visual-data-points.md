---
id: welcome-visual-data-points
date: 2026-09-04
trigger-type: stakeholder-request
change-type: ux-change, visual-change, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Give the welcome a landing-page hero, with stat tiles + a role-share bar

## Signal

See: `research/2026-09-04-welcome-visual-data-points.md`

Related: `changes/2026-09-04-about-this-platform-welcome.md` (built the welcome this
revises).

## Outcome

`outcomes/understand-market-health-before-searching.md` — "they spend less than 5 minutes to
get a clear market read" and "can see the trends clearly" both favor figures a professional
reads at a glance over a paragraph they have to parse.

## Change Type

`ux-change` — the welcome becomes a landing-page-style entry point (hero headline + hero
figure + supporting stats + a role-category share chart + card-style CTAs), not a chat-bubble
paragraph. This is deliberately specific to the welcome — the *entry point* — not every
data-story message; other stories keep the current AI-turn prose treatment unless a future
change asks for them to match.
`visual-change` (feature-scoped, but the new Hero Figure, Stat Tile, Category Share Bar, and
Shortcut Card patterns are documented in Visual Design so future entry-point-style surfaces
can reuse them without re-inventing the look).
`api-change` — the welcome's `inventory.headline` (single largest category) becomes
`inventory.role_breakdown` (all tracked categories with counts), so the frontend can render a
real share chart instead of one fact.

## Design direction (landing-page anatomy, within the existing dark system)

Per `design/foundations.md` and `design/visual-design.md` — dark surfaces, no shadows, no
gradients on primary surfaces, the existing three-colour accent palette, restrained motion.
"Landing page" is expressed through **hierarchy and pacing**, not new chrome:

1. **Hero** — a small eyebrow label, a large bold headline (bigger than any existing AI-turn
   text), and a one-sentence subhead. This is the "what this is" content, restyled.
2. **Proof** — one **Hero Figure** (dataviz term: the single number the view leads with, large,
   not accent-coloured) for total job openings, smaller supporting **Stat Tiles** for companies
   and collection start, and a **Category Share Bar** (the role-category breakdown — a
   categorical stacked bar reusing the existing Designer/PM/Engineer accent colours) directly
   beneath.
3. **Call to action** — each story-catalogue shortcut becomes a **Shortcut Card**: a bordered,
   hoverable row with the question and a trailing arrow, not a plain list item — inviting a
   click the way a landing page's feature links do.

Still inside the AI-turn container with its Reasoning Panel toggle underneath (Information
Architecture's universal primitive) — the hero treatment is internal layout, not a new page
chrome or a surface exempt from the Reasoning Panel.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | update — add Hero Figure, Stat Tile, Category Share Bar, and Shortcut Card to Component Aesthetics, reusing the existing accent palette and mark-spec conventions |
| Experience Spec | `design/market-health/experience.md` | update — Opening Welcome restructured as hero + proof + CTA (landing-page anatomy); update the data contract and the "what you can ask" interaction |
| Backend Spec | `backend/specs/market-health/api.md` | update — `GET /api/market-health/welcome`: `inventory.headline` → `inventory.role_breakdown` (all categories, counts, ordered) |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — `WelcomeMessage`'s stat tiles + share bar, mark specs (2px gap between segments, direct labels for ≤4 series, accent-color reuse) |
| Backend Implementation | `backend/src/market_stories.py` | update — `build_welcome()` returns `role_breakdown` |
| Frontend Implementation | `frontend/src/features/market-health/WelcomeMessage.tsx` | update |

## Execution Plan

- [x] Step 1: `/new-experience` — restructured Opening Welcome as Hero / Proof / Call to
      action; data contract now includes the full role breakdown instead of one headline
      fact; edge cases updated for the hero/proof/CTA shape.
- [x] Step 2: `/new-visual-design` — added a Hero headline / Hero figure typography scale and
      an "Entry-point components" section (Eyebrow label, Hero Figure, Stat Tile, Category
      Share Bar, Shortcut Card) to Component Aesthetics, explicitly scoped to entry points.
      Version 1.1 → 1.2.
- [x] Step 3: `/new-backend-spec` — `inventory.headline` → `inventory.role_breakdown` (full
      ordered breakdown) in `GET /api/market-health/welcome`; empty-collection behavior updated.
- [x] Step 4: `/new-frontend-spec` — rewrote "Welcome rendering rules" for the three-band
      hero/proof/CTA structure, role-category-to-accent-colour mapping rule, and the
      empty-state behaviour for the new fields.
- [x] Step 5: `/implement-backend` — `build_welcome()` now returns `role_breakdown` (all
      tracked categories, counts, descending) instead of a single `headline`; verified against
      production data (Engineer 2,833 / Product Manager 303 / Designer 143).
- [x] Step 6: `/implement-frontend` — rewrote `WelcomeMessage.tsx`: Hero (eyebrow + headline +
      subhead), Proof (Hero Figure + two Stat Tiles + a flex-ratio Category Share Bar with a
      direct-labelled legend, role-category colours mapped by name with a neutral fallback),
      Call to action (Shortcut Cards with a hover arrow).
- [x] Step 7: Validated — `GET /api/market-health/welcome` returns `role_breakdown` through a
      live uvicorn stack and through the running `:5173` dev proxy (Engineer 2,833 / Product
      Manager 303 / Designer 143 of 6,628 total); `npm run build` / `tsc` pass; `git diff --check`
      clean.

## Decision Log

- 2026-09-04: Tracked against the existing outcome — a faster, more scannable read is exactly
  what "spend less than 5 minutes" and "see trends clearly" already call for.
- 2026-09-04: Per the dataviz method — three headline counts (postings, companies, since-date)
  are a KPI row of stat tiles, not a chart; role-category share (3 parts of a whole) is a
  categorical stacked bar, reusing the product's existing Designer/PM/Engineer accent colors
  (already validated and used identically in the trend chart) rather than inventing new hues.
- 2026-09-04: `headline` (single fact) is replaced by `role_breakdown` (full breakdown) rather
  than keeping both — the share bar makes the single-fact summary redundant, and two fields
  describing the same thing would drift.
- 2026-09-04 (same-day follow-up): stakeholder asked for a landing-page feel, specifically for
  the welcome as the entry point. Scoped to this one surface, not a product-wide direction —
  every other AI-turn message keeps its current prose treatment. Expressed through hierarchy
  (eyebrow, hero headline, hero figure, CTA cards) within the existing dark, no-shadow,
  three-accent-colour system — not new chrome, gradients, or imagery, which the Visual Design
  spec's "What this rules out" section excludes.
