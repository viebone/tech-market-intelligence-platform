---
id: treemap-legibility
date: 2026-09-27
trigger-type: user-feedback
change-type: visual-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Fix Treemap gap and add shade-by-volume

## Signal
See: `research/2026-09-27-treemap-legibility.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — same outcome Story 4's own
addition mapped to (`changes/2026-09-21-job-function-story.md`). This is a legibility fix to an
existing chart within that story, not a new success criterion.

## Change Type
`visual-change`, product-wide in scope even though only Story 4 currently uses this form: the
Treemap is a shared chart-form definition in `design/visual-design.md` (available to any future
story that needs a many-category part-to-whole view), not a one-off style embedded in a single
experience spec.

## Triage Notes

Two distinct defects, both traced to the same block:
1. **Gap between tiles was effectively invisible.** The spec already said "2px gray-800 gap,"
   but the implementation padded 1px into an *unset* ambient background rather than a real
   gray-800 fill — a straightforward implementation bug (code didn't match a spec that was
   already correct on this point).
2. **Uniform single fill gave no secondary cue for "how big."** The original design decision
   ("ONE fill … colour carries nothing") was reasonable in principle but proved to make adjacent,
   similarly-sized tiles hard to distinguish in practice — the user's actual complaint. This is a
   real design-decision change, not a bug: it required revising `visual-design.md`'s Treemap
   definition to add a validated sequential shade-by-volume ramp, and updating the Data
   Legibility legend/how-to-read line accordingly (colour now carries meaning — Rule 10).

Resolved together as one `visual-change`, since fixing (1) alone would not have addressed the
user's actual "difficult to differentiate" complaint, and (2) requires (1) to even be visible
(a shade difference between tiles is only legible once a real gap separates them).

**Colour ramp validated, not eyeballed** (`dataviz` skill): indigo-500 excluded (3.97:1 / 4.06:1
text contrast either way — a dead zone under the 4.5:1 floor for 12px text); indigo-700 excluded
(1.86:1 against the gray-800 gap — blends in — and ΔL 0.054 from indigo-600 — indistinguishable).
Final ramp `indigo-600 → indigo-400 → indigo-300 → indigo-200` (dimmest → brightest as volume
rises — dark-mode sequential ramps anchor opposite light mode) passes
`node validate_palette.js "#4f46e5,#818cf8,#a5b4fc,#c7d2fe" --ordinal --mode dark --surface "#1f2937"`
with all checks clear. Binned by each named tile's rank-quartile among the story's own named
tiles, not an absolute share threshold, so the ramp holds regardless of how concentrated or
spread the data is.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | update — Treemap definition (v2.1 → v2.2) |
| Experience Spec | `design/market-health/data-stories.md` | update — Story 4 how-to-read line |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | no-change — already defers Treemap's exact colours/spacing to `visual-design.md`; no component structure or prop change |
| Backend Spec | `backend/specs/market-health/api.md` | no-change |
| Frontend Implementation | `frontend/src/features/market-health/stories/Treemap.tsx` | update |
| Backend Implementation | `backend/src/` | no-change |
| Plain-Language Overview | `OVERVIEW.md` | no-change — `OVERVIEW.md` describes Story 4 as a capability ("what data story exists"), not chart rendering detail; no capability changed, only how the existing chart is drawn |
| MCP Access Review | `ACCESS.md` + MCP backend spec | not-applicable — no backend capability changed |
| Polite Scraping Review | `DATA_SOURCES.md` + affected backend spec | not-applicable — no scraped source touched |
| Data Surface Review | data-story catalogue / admin dashboard / ad-hoc query layer | not-applicable — no new data category, purely a rendering fix on already-modeled data |

## Execution Plan

- [x] Step 1: Update `design/visual-design.md` — Treemap definition: validated shade-by-volume
      ramp, real gray-800 gap rendered on the container, updated legend wording
- [x] Step 2: Update `design/market-health/data-stories.md` — Story 4 how-to-read line
- [x] Step 3: Implement — `Treemap.tsx`: shade lookup by rank-quartile, `bg-gray-800` container
      + `p-0.5` (2px) tile padding for a real gap, conditional text colour (gray-900/gray-100)
      per shade, updated caption copy
- [x] Step 4: Verify — `tsc --noEmit` and `npm run build` both clean

## Decision Log
- 2026-09-27: Classified as `visual-change` (product-wide) rather than `bug-fix` alone, because
  the shading half of the request is a genuine revision of a documented design decision
  ("colour carries nothing"), not code failing to match an already-correct spec.
- 2026-09-27: `OVERVIEW.md` left as `no-change` — it's a capability map, not a styling changelog;
  nothing a reader of "what does this product do" would need restated here.
