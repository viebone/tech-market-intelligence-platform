---
id: story-visual-standard
date: 2026-09-10
trigger-type: stakeholder-request
change-type: visual-change, ux-change
outcome: understand-market-health-before-searching
status: in-progress
---

# Change Request: A visual standard every data story must meet

## Signal

See: `research/2026-09-10-story-visual-standard.md`. Every story added to the frontend should
look and feel like the last one shipped ("What we know about the market") — chart-first, a
combination of visual elements, engaging, "a bit fun", high-impact — by *standard*, not by
whoever happens to build it.

## Outcome

`outcomes/understand-market-health-before-searching.md` — "spend less than 5 minutes to get a
clear market read", "see the trends clearly", "identify which roles and skills are in demand".
A consistent, scannable, chart-first story is how a professional actually absorbs the market
read fast. "Engaging / a bit fun" is instrumental: a story people find inviting is a story
they finish, so they get the read. No new success criterion — this makes the existing ones
land more reliably across every catalogue entry, not just the one that was hand-polished.

## Change Type

- `visual-change` (product-wide) — a **Data Story composition standard** added to
  `design/visual-design.md`: the required visual vocabulary, the "combine several elements,
  chart-first" rule, the tone (inviting, a touch of delight — not a corporate report), and
  what it rules out (a wall of prose, an undifferentiated block, an empty section).
- `ux-change` — the story's shape stops being the builder's discretion. `data-stories.md`
  Catalogue rules gain a "Visual standard every story must meet" checklist; a new story's
  "Visible answer shape" must satisfy it.

Not `api-change`: the backend already returns each story's `sections` with typed content; the
frontend chooses the visual form per section from a documented convention. (If the spec work
finds a per-section `render_hint` genuinely necessary for consistency, that becomes a small
follow-on `api-change` — flagged, not assumed.)

## The standard, in principle (specs nail the details)

Every story, on open, is a short **composed piece**, not a report:

1. **A framing line** — one sentence naming what's being summarised. Numbers as context, never
   the point.
2. **At least one chart**, and a **combination of visual elements** — a story is never a
   single block. Draw from the validated vocabulary: `RankedBarList` (magnitude), a hero
   **figure** (one number that matters), a **stat tile**, a **meter / share bar**
   (part-to-whole), a sparkline/trend where the data is time-series. Each block is
   direct-labelled and self-explaining.
3. **Chart-first** — the visual carries the point; prose is a caption, not the content.
4. **Consistent rhythm** — the same vertical spacing, the same block anatomy (heading →
   visual → honesty qualifier), the same validated palette and type scale across every story.
5. **Engaging by composition, not motion** (stakeholder call, 2026-09-10) — the "bit of fun"
   comes from strong visual rhythm, varied elements, chart-first hierarchy and generous
   spacing. **No entrance animation on data** — the existing Motion rule ("charts render
   immediately") stands unchanged.
6. **Honest by construction** — every block keeps its sample-size / coverage qualifier; an
   `insufficient_data` block shows its "not enough data yet" line, never an empty chart.
7. **De-duplicated** — a story shows the *substance*; it never repeats the "About this
   platform" welcome's inventory. No figure appears in both.

"Adding a story" stays a catalogue operation — one entry + its renderer built from the shared
components — and the standard is what makes that renderer look right without a bespoke design
pass each time.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | review — expected no-change (criteria are about comprehension speed, which this serves); note only |
| Design Foundations | `design/foundations.md` | **no-change** (stakeholder call, 2026-09-10) — "engaging / worth finishing" stays scoped to the market-health story surface, not a product-wide design goal. The rationale lives in `visual-design.md`'s new section. |
| Information Architecture | `design/information-architecture.md` | no-change — no nav or taxonomy change |
| Visual Design | `design/visual-design.md` | **update** — new "Data Story composition" section under Component Aesthetics: required vocabulary, combination rule, block anatomy, rhythm, scoped rationale, what it rules out. **Motion section: no-change** — no entrance animation on data. |
| Experience Spec | `design/market-health/experience.md` | **update** — Data stories section: a story is chart-first, composed, and engaging *by standard*, not builder discretion |
| Data Stories Spec | `design/market-health/data-stories.md` | **update** — Catalogue rules: add "Visual standard every story must meet" (a checklist referencing `visual-design.md`); "Future catalogue direction" points to it; Story 1's "Visible answer shape" reframed as the reference implementation of the standard |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **update** — the shared component set a story composes from (`RankedBarList`, a story **Figure**, a **Meter/ShareBar**, the framing line), a `DataStoryMessage` "story acceptance checklist", and whether a thin `DataStoryLayout` wrapper is worth extracting |
| Backend Spec | `backend/specs/market-health/api.md` | review — expected no-change; decide the `render_hint` question here |
| Frontend Implementation | `frontend/src/` | update — `DataStoryMessage.tsx` conforms to the checklist; extract the shared Figure / Meter components alongside the existing `RankedBarList`; add the load-in motion |
| Backend Implementation | `backend/src/` | no-change expected |

## Execution Plan

- [x] Step 1: Read the chain (2026-09-10) — outcome, foundations (Paradigm + Design Goals),
      visual-design (Component Aesthetics + Motion), experience (Data stories), data-stories,
      frontend spec, `DataStoryMessage.tsx` / `RankedBarList.tsx`. Two decisions taken:
      **engaging by composition only, no data-entrance motion**; **no foundations change**
      (scoped to the story surface).
- [x] Step 2: `design/foundations.md` — **no-change**, per the stakeholder call. Recorded here.
- [x] Step 3: `/new-visual-design` (2026-09-10) — `design/visual-design.md` → v1.4. New
      "Data Story composition" section under Component Aesthetics: composed-piece structure
      (framing line → 3–6 blocks of heading/visual/qualifier), the visual vocabulary table
      (ranked bar list / Hero Figure / Stat Tile / Meter / Category Share Bar / Trend line),
      a new **Meter** spec, the ≥2-distinct-forms combination rule, chart-first rule,
      consistency requirements, scoped rationale (professional audience; not operator
      surfaces; not a product-wide goal), and a story-specific rules-out list. Motion section
      untouched.
- [x] Step 4: `/new-experience` (2026-09-10) —
      - `design/market-health/experience.md` — Data stories section: a story is chart-first
        AND composed, its look is a standard not the builder's choice, pointer to the
        visual-design section + the per-story checklist; "Revised 2026-09-10" note; `updated`
        bumped.
      - `design/market-health/data-stories.md` — new "Visual standard every story must meet"
        checklist under Catalogue rules; Story 1's "Visible answer shape" reframed as the
        reference implementation (with a note that it clears the ≥2-form minimum and future
        stories should reach for Trend/Share forms); dropped the optional prose "block 6"
        (provenance lives in the Reasoning Panel); "Future catalogue direction" now requires
        the standard and notes a single-number/single-list question belongs in the curated
        engine, not dressed up as a story.
- [x] Step 5: `/new-frontend-spec` (2026-09-10) — `frontend/specs/market-health/architecture.md`:
      new "Every story: the shared build" subsection — the shared component set
      (`DataStoryMessage` renderer, new `StoryBlock`, existing `RankedBarList`, new
      `StoryFigure`, new `Meter`, reuse of share bar / trend), a frontend story-acceptance
      checklist, and the decision that `DataStoryMessage` stays a per-story renderer (not a
      generic `DataStoryLayout`) while the catalogue is small. "First story" renamed to
      "Reference story". Component Breakdown table updated. No `render_hint` — the renderer
      maps section ids to forms.
- [x] Step 6: `/new-backend-spec` — **no-change**. `backend/specs/market-health/api.md` Data
      stories section got a "Reviewed 2026-09-10" note: the standard is a frontend composition
      concern; `render_hint` considered and rejected; the existing `sections[]` shape suffices.
- [ ] Step 7: `/implement-frontend` — bring `DataStoryMessage.tsx` to the checklist, extract
      the shared Figure / Meter components, verify against the running story and the welcome
      (no duplication). `npm run build` + `tsc`.
- [ ] Step 8: Commit + push; mark `complete` when specs and the shipped story match.

## Decision Log

- 2026-09-10: Tracked against `understand-market-health-before-searching` — same outcome as
  the story-redesign CR (`2026-09-06`). This is the "make it a repeatable standard" follow-
  through of that one-off redesign. No success criterion moves.
- 2026-09-10: `visual-change` (product-wide) + `ux-change`, not `new-feature` — stories
  exist; this codifies how they must look and feel. The composition standard is product-wide
  (a new `visual-design.md` section), which is why it's product-wide `visual-change` not
  feature-scoped.
- 2026-09-10: Kept out of `api-change` deliberately. The backend's typed `sections` already
  carry enough for the frontend to pick a visual form per a documented convention. A
  `render_hint` field is only added if the frontend spec proves it's needed for consistency —
  not upfront.
- 2026-09-10 (stakeholder): **"A bit fun" comes from composition, not motion.** The
  visual-design Motion section already bans entrance animation on data ("the user is
  processing data under stress") — that stays. Engagement is delivered by chart-first
  hierarchy, a varied element mix, consistent rhythm, and generous spacing. No count-ups, no
  bars growing in.
- 2026-09-10 (stakeholder): **No foundations change.** "Engaging / worth finishing" is scoped
  to the market-health story surface (a professional audience, not an operator), documented
  in `visual-design.md`'s new section — it does not become a product-wide design goal and
  does not extend to operator surfaces.
