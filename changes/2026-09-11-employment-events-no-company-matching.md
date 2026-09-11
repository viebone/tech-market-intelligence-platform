---
id: employment-events-no-company-matching
date: 2026-09-11
trigger-type: stakeholder-request
change-type: ux-change, api-change, technical-refactor
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Employment events — remove all company-matching, keep only the independent surface

## Signal
See: `research/2026-09-11-employment-events-no-company-matching.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — no change; this sharpens, not
alters, the same success criteria the two earlier changes already served today.

## Change Type
`ux-change` (the tracked-company chart-strip surface is removed, not just descoped) +
`api-change` (`matched_company` dropped from the data model; `GET /api/market-health/employment-events`
removed; `query_employment_events_data`'s `hiring_trend` removed) + `technical-refactor`
(`company_aliases.py` and its call sites removed as dead machinery).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Experience Spec | `design/market-health/experience.md` | **update** — remove the "Employment events strip" section (chart marker layer, hover, click-detail) and Layoff Signal's `hiring_trend` framing; Layoff Signal answers about events only |
| Data Story spec | `design/market-health/data-stories.md` | update — Story 2's framing already says "independent"; confirm/tighten, no structural change needed |
| Information Architecture | `design/information-architecture.md` | review — `Layoff Signal`'s "Where it appears" listed the Trend Chart; remove that, keep the story/conversation locations |
| Visual Design | `design/visual-design.md` | update — remove the "Chart event marker" component pattern (no longer used anywhere) |
| Backend Spec | `backend/specs/market-health/api.md` | **update** — drop `matched_company` from `EmploymentEvent`; remove `GET /api/market-health/employment-events`; remove `hiring_trend` from `query_employment_events_data`; redesign the UK Companies House adapter contract away from a tracked-company candidate list (Companies House Streaming API — real-time, all-UK insolvency events, no company targeting — found via live research this pass) |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **update** — remove `EmploymentEventsStrip`/`EventMarkerDetail`, `JobOpeningsChart`'s `events` prop, the employment-events query |
| Backend Implementation | `backend/src/` | migration dropping `matched_company`; delete `company_aliases.py`, `market_employment_events.py`; update `employment_events_storage.py`, `market_query.py`, `chat.py`; rewrite `companies_house.py` for the Streaming API + a new small cursor table |
| Frontend Implementation | `frontend/src/` | delete `EmploymentEventsStrip.tsx`; revert `JobOpeningsChart.tsx`, `MarketBriefingMessage.tsx`, `MarketHealthPage.tsx` |

## Execution Plan

- [x] Step 1: Updated `design/market-health/experience.md` (removed the "Employment events
      strip" section, User Flow 7d's hiring-trend comparison, the chart-spec rows, related
      Interactions/Edge Cases/Metrics rows), `design/information-architecture.md` (Layoff
      Signal's "Where it appears" no longer lists the Trend Chart), `design/visual-design.md`
      (removed the "Chart event marker" pattern)
- [x] Step 2: Updated `backend/specs/market-health/api.md` — `matched_company` dropped from
      `EmploymentEvent`; `GET /api/market-health/employment-events` removed;
      `query_employment_events_data`'s `hiring_trend` removed; UK Companies House's adapter
      contract redesigned around the Streaming API (found via live research this pass — a
      real-time, all-UK-companies insolvency feed, no candidate-list targeting needed); added
      the `employment_event_cursors` table for stream resumption
- [x] Step 3: Updated `frontend/specs/market-health/architecture.md` — removed
      `EmploymentEventsStrip`/`EventMarkerDetail` from Component Breakdown, State Management,
      Data Requirements, API Contract, Tech Decisions, and the 2026-09-11 review-log entry
- [x] Step 4: `/implement-backend` — migration (`ALTER TABLE employment_events DROP COLUMN IF
      EXISTS matched_company`, new `employment_event_cursors` table) applied to the **real
      production database**; deleted `company_aliases.py` and `market_employment_events.py`;
      updated `employment_events_storage.py`, `market_query.py`, `chat.py`; rewrote
      `companies_house.py` for the Streaming API. **Verified against real production data**:
      all 25 live WARN rows survived the migration; `build_employment_risk_overview()` and
      `query_employment_events_data()` both re-run successfully afterward with correct output
      and no `matched_company`/`hiring_trend` anywhere.
- [x] Step 5: `/implement-frontend` — deleted `EmploymentEventsStrip.tsx`; reverted
      `JobOpeningsChart.tsx` (removed `events` prop, `dateToFractionalIndex`, the render
      block — confirmed via a smaller compiled bundle, 260.85 kB vs. 265.17 kB, and one fewer
      transformed module, that the removal took real effect, not just a spec-only claim),
      `MarketBriefingMessage.tsx`, `MarketHealthPage.tsx`. Verified with a real `npm run
      build` — clean, zero errors.

## Decision Log
- 2026-09-11: This reverses part of `changes/2026-09-11-employment-events-independent-scope.md`
  (which kept the chart strip alive as a *second*, tracked-company-scoped surface alongside
  the new independent story). Reversing shipped work is unusual but the right call here — the
  user's direction is unambiguous and repeated, and the code being removed was built and
  verified only hours earlier in the same session, so the cost of removing it is low.
- 2026-09-11: UK Companies House's per-company insolvency lookup inherently needs *some* set of
  companies to query — Companies House's REST API has no "all UK insolvencies" endpoint. Found
  a genuine solution via live research: the **Companies House Streaming API**
  (`stream.companieshouse.gov.uk/insolvency-cases`) pushes real-time insolvency events across
  *all* UK companies, no targeting needed — same key, different base URL. This is what makes
  the adapter genuinely independent rather than just removing the feature. Response field
  shape not yet confirmed (no live key) — same "fails loudly, not guessed" pattern already
  proven correct once for WARN Firehose.
