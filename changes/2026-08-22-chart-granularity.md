---
id: chart-granularity
date: 2026-08-22
trigger-type: user-feedback
change-type: ux-change, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Independent Chart Granularity (Day / Week / Month)

## Signal
See: `research/2026-08-22-chart-granularity.md`

Additional UX feedback: `research/2026-09-04-chart-filter-dropdown.md`.

Additional signal: `research/2026-09-04-chart-six-month-window.md`.

## Outcome
See: `outcomes/understand-market-health-before-searching.md`

Tracked against the existing outcome — its success criteria already promise users
"can see the trends clearly, how the hiring market numbers evolve through time,"
which this directly serves. Currently under-delivered while real data is sparse
(~3 weeks old) and the chart has no way to show it at a meaningful granularity.

## Change Type
`ux-change` — a new, independent Granularity control (Week / Month for this slice), decoupled
from the existing Time Range control (This Year / Past 5 Years / All Time); horizontal
scroll behavior for dense views (e.g. daily buckets over a year).
`api-change` — `backend/src/market_openings.py`'s `get_openings()` must aggregate by
week/month, not just the current hardcoded month bucketing, and support a six-month range.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change — success criteria already cover this |
| Design Foundations | `design/foundations.md` | update — filter-density principle added |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change — confirmed during Step 1: the new Granularity tabs reuse the existing Tab/range-selector component style verbatim (same as Time Range tabs), no new tokens or patterns needed |
| Experience Spec | `design/market-health/experience.md` | **update** — new Granularity control (Day/Week/Month) independent of Time Range; default-granularity behavior (smart/auto given sparse data vs. always-Month-default — open design decision, not decided at triage); Chart Specification's X-axis definition generalized beyond "always monthly"; horizontal-scroll behavior specified for dense views |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **update** — new granularity control component, horizontal-scroll container, API contract update |
| Backend Spec | `backend/specs/market-health/api.md` | **update** — new `granularity` and `six_months` params plus week/month aggregation logic |
| Frontend Implementation | `frontend/src/` | update |
| Backend Implementation | `backend/src/market_openings.py` | update |

## Execution Plan

- [x] Step 1: `/new-experience` — updated `design/market-health/experience.md`. New
      independent Granularity control (Day/Week/Month), confirmed with the stakeholder:
      default **Week** (not smart/adaptive — matches Principle 1, Intent First, Always
      Explicit, predictable regardless of how much data exists), and Day **restricted
      by Time Range** (This Year only; Past 5 Years/All Time cap at Week/Month
      respectively, avoiding 1,800+-point charts). Generalized X-axis ticks, subtitle,
      and hover delta language from hardcoded-monthly to per-granularity. Specified
      horizontal scroll: only the plot area scrolls (~24px/bucket minimum), Y axis and
      legend stay fixed. Added an explicit edge case distinguishing a real-but-sparse
      line (honest, shown as-is) from a genuine no-data state (existing behavior,
      unchanged). Visual Design confirmed no-change — new tabs reuse the existing
      Tab/range-selector style verbatim.
- [x] Step 2: `/new-backend-spec` — updated `backend/specs/market-health/api.md`: new
      `granularity` and `six_months` params plus week/month aggregation logic
- [x] Step 3: `/new-frontend-spec` — updated `frontend/specs/market-health/architecture.md`:
      new control component, horizontal scroll, updated API contract
- [x] Step 4: `/implement-backend` — added weekly/monthly aggregation and six-month filtering.
- [x] Step 5: `/implement-frontend` — added controls and wired Week / Month plus 6 Months.
- [x] Step 6: Filter UX refinement — replaced segmented button strips with two labelled
      dropdowns; Week remains selected by default.

## Decision Log
- 2026-08-22: Tracked against `understand-market-health-before-searching` — confirmed
  with the stakeholder, no new outcome needed.
- 2026-08-22: Classified as `ux-change` + `api-change` — a real new control and a real
  backend aggregation change, not a `bug-fix` (the current month-only behavior isn't
  wrong per any existing spec, it just doesn't yet support the granularity this
  request asks for).
- 2026-08-22: Default-granularity behavior (smart/auto vs. always-Month) deliberately
  left open for the experience-spec step — a real design decision, not something to
  presume at triage.
- 2026-09-04: The requested implementation slice is Week / Month plus a six-month range.
      Week is the explicit default; daily granularity remains deferred from this slice.
- 2026-09-04: Two filter groups remain visible directly as compact dropdowns. More than two
      filter groups should be grouped in a dropdown.
- 2026-09-04: Validation passed: frontend `npm run build`, backend `py_compile`, and
      `git diff --check`.
