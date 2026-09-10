---
id: story-visual-standard
date: 2026-09-10
trigger-type: stakeholder-request
change-type: visual-change, ux-change
outcome: understand-market-health-before-searching
status: triaged
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
5. **A touch of delight** — subtle, purposeful motion (bars grow in on load, a figure counts
   up once) within the existing Motion rules. Never gratuitous, never blocking the read.
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
| Design Foundations | `design/foundations.md` | review — the paradigm is operator/serious; the *consumer* market-health surface can carry a light "inviting, worth reading" note without a whole new design goal. Update only if that reads as genuinely product-wide. |
| Information Architecture | `design/information-architecture.md` | no-change — no nav or taxonomy change |
| Visual Design | `design/visual-design.md` | **update** — new "Data Story composition" section under Component Aesthetics: required vocabulary, combination rule, block anatomy, rhythm, the delight/motion allowance, what it rules out |
| Experience Spec | `design/market-health/experience.md` | **update** — Data stories section: a story is chart-first, composed, and engaging *by standard*, not builder discretion |
| Data Stories Spec | `design/market-health/data-stories.md` | **update** — Catalogue rules: add "Visual standard every story must meet" (a checklist referencing `visual-design.md`); "Future catalogue direction" points to it; Story 1's "Visible answer shape" reframed as the reference implementation of the standard |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **update** — the shared component set a story composes from (`RankedBarList`, a story **Figure**, a **Meter/ShareBar**, the framing line), a `DataStoryMessage` "story acceptance checklist", and whether a thin `DataStoryLayout` wrapper is worth extracting |
| Backend Spec | `backend/specs/market-health/api.md` | review — expected no-change; decide the `render_hint` question here |
| Frontend Implementation | `frontend/src/` | update — `DataStoryMessage.tsx` conforms to the checklist; extract the shared Figure / Meter components alongside the existing `RankedBarList`; add the load-in motion |
| Backend Implementation | `backend/src/` | no-change expected |

## Execution Plan

- [ ] Step 1: Read the chain — `outcomes/understand-market-health-before-searching.md`,
      `design/foundations.md` (Design Goals, Paradigm), `design/visual-design.md`
      (Component Aesthetics, Motion), `design/market-health/experience.md` (Data stories),
      `design/market-health/data-stories.md`, `frontend/specs/market-health/architecture.md`,
      and the current `DataStoryMessage.tsx` / `RankedBarList.tsx` (the reference).
- [ ] Step 2: `design/foundations.md` review (manual) — add a one-line consumer-surface
      "inviting, worth finishing" note only if it's genuinely product-wide; otherwise record
      "no-change" with the reasoning.
- [ ] Step 3: `/new-visual-design` — add the "Data Story composition" standard to
      `design/visual-design.md` (vocabulary, combination rule, block anatomy, rhythm,
      delight/motion, rules-out). Bump the version.
- [ ] Step 4: `/new-experience` — update `design/market-health/experience.md` (Data stories:
      chart-first, composed, engaging by standard) and `design/market-health/data-stories.md`
      (Catalogue rules → "Visual standard every story must meet" checklist; Story 1 as the
      reference implementation; Future direction points to the standard).
- [ ] Step 5: `/new-frontend-spec` — update `frontend/specs/market-health/architecture.md`:
      shared component set, the story acceptance checklist, the `DataStoryLayout` decision,
      the load-in motion. Decide the `render_hint` question (default: no backend change).
- [ ] Step 6: `/new-backend-spec` — only if Step 5 decides `render_hint` is needed.
- [ ] Step 7: `/implement-frontend` — bring `DataStoryMessage.tsx` to the checklist, extract
      the shared Figure / Meter components, add subtle load-in motion, verify against the
      running story and the welcome (no duplication). `npm run build` + `tsc`.
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
- 2026-09-10: "A bit fun" is scoped to *subtle, purposeful* motion + a strong visual rhythm,
  staying inside `visual-design.md`'s existing Motion rules and the product's serious
  intelligence-tool character. Not animations for their own sake.
