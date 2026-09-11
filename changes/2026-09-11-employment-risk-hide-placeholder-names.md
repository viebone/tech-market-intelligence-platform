---
id: employment-risk-hide-placeholder-names
date: 2026-09-11
trigger-type: stakeholder-request
change-type: bug-fix, ux-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Never display a company-number placeholder as a company name

## Signal
See: `research/2026-09-11-employment-risk-hide-placeholder-names.md`

## Outcome
No change — same story, refined the same day.

## Change Type
`bug-fix` (`company_raw` was fabricated as `"Company {number}"` for the Companies House
Streaming API, which has no company name field — that string is not "exactly as the source
reported it," violating this pipeline's own "never fabricate/normalize `company_raw`" rule
documented in the backend spec) + `ux-change` (a numeric placeholder must never be displayed
as if it were a real company).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Data Story spec | `design/market-health/data-stories.md` (Story 2) | update — "Companies with the most reported impact" excludes events with no real company name |
| Backend Spec | `backend/specs/market-health/api.md` | update — Companies House adapter contract: `company_raw` is the bare company number, not a fabricated string |
| Backend Implementation | `backend/src/employment_events/companies_house.py`, `employment_events/base.py`, `market_stories.py` | update |

## Execution Plan

- [x] Step 1: Fix `companies_house.py` — `company_raw` = the bare company number (what the
      source actually gives us), not a fabricated `"Company {number}"` string
- [x] Step 2: Add a shared `is_real_company_name()` check (`employment_events/base.py`) —
      catches both the corrected bare-number form and the two already-inserted legacy
      `"Company {number}"` rows (immutable, never rewritten — Data Models discipline)
- [x] Step 3: Update `build_employment_risk_overview()`'s companies query to exclude
      no-real-name events, with an honest qualifier stating how many were excluded and why.
      Country/sector/direction aggregates are unaffected — they never reference `company_raw`,
      so those events still count as "generic" activity, per the user's direction.
- [x] Step 4: Update specs; verify against real production data (including the legacy rows)

## Decision Log
- 2026-09-11: Fixing this at the source (`company_raw` = bare id) rather than only filtering
  at display time, because storing a fabricated `"Company N"` string was itself a real spec
  violation (`company_raw`'s whole documented purpose is "exactly as the source reported it,
  never normalized or guessed") — not just a display preference. The display-time filter is
  still needed regardless, to also catch the two already-inserted legacy rows (immutable, not
  rewritten).
