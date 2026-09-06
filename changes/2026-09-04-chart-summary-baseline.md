---
id: chart-summary-baseline
date: 2026-09-04
trigger-type: user-feedback
change-type: bug-fix, ux-change, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Make chart summaries time-aware and baseline-correct

## Signal

See: `research/2026-09-04-chart-summary-baseline.md`

## Outcome

`outcomes/understand-market-health-before-searching.md` - users need a trustworthy view of
how hiring demand evolves over time.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | update - summary names selected range/view and excludes initial collection baseline |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update - summary receives range and granularity context |
| Backend Spec | `backend/specs/market-health/api.md` | update - post-baseline trend aggregation and summary contract |
| Backend Implementation | `backend/src/market_openings.py` | update |
| Frontend Implementation | `frontend/src/features/market-health/JobOpeningsChart.tsx` | update - display backend summary context |

## Execution Plan

- [x] Capture the signal and map it to the existing market-health outcome.
- [x] Update experience and technical specs.
- [x] Exclude the first posting-ingestion run from trend data.
- [x] Name the selected range and granularity in the summary.
- [x] Validate backend syntax and frontend build.

## Decision Log

- 2026-09-04: The baseline is the earliest ingestion run with `total_inserted > 0`, identified
  through `raw_postings.ingestion_run_id`; its postings are excluded from trend counts.
- 2026-09-04: The summary describes the active range and bucket size, for example
  "Weekly view for the past 6 months". It does not imply the first observed bulk collection
  was market growth.
- 2026-09-04: The WSL backend summary test, frontend build, frontend diagnostics, and
  `git diff --check` all passed.