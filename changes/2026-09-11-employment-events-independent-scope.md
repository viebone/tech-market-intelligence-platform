---
id: employment-events-independent-scope
date: 2026-09-11
trigger-type: stakeholder-request
change-type: ux-change, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Employment events as an independent market-intelligence dataset

## Signal
See: `research/2026-09-11-employment-events-independent-scope.md`

## Relationship to the parent change
This is a **companion/follow-on** to `changes/2026-09-11-employment-event-ingestion.md`
(status: in-progress, shipped earlier today), not a duplicate. That change built the
`employment_events` data model, three source adapters, the chart-strip surface, and the
Layoff Signal chat tool — all scoped to overlay-on-tracked-companies. This change revisits
only the **scoping decision**: whether/how employment events surface independently of the 35
job-posting companies, for broader market/sector-level strategic insight. The data model and
ingestion pipeline underneath do not change — `matched_company` was already built nullable and
source-agnostic; this is a surface/presentation-layer decision, not a re-architecture.

## Outcome
See: `outcomes/understand-market-health-before-searching.md`. Maps directly — its success
criteria already say employment risk should be visible "at the company **and sector** level,"
and this change is what actually delivers the sector/market-level half of that promise (today's
shipped version only delivers the company-level half, via the tracked-company chart overlay).
No outcome update needed — this was already anticipated in today's earlier revision.

## Change Type
`ux-change` (the experience of how employment events surface — a new/broadened view, not just
an overlay) + `api-change` (the endpoint's scoping and likely a new sector/market-aggregate
query shape).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change — already covers sector-level risk |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | review only — confirm the broadened `Layoff Signal` term still fits; likely no-change since it was already defined at "a company or sector" scope |
| Visual Design | `design/visual-design.md` | review only — likely reuses existing data-story visual vocabulary (Ranked bar list, Meter, Year-on-year comparison) for a market/sector aggregate view |
| Experience Spec | `design/market-health/experience.md` | **update** — the core decision lives here: resolve whether (a) the existing tracked-company chart strip stays as-is (it has its own real coherence value — "our own hiring vs. our own contraction") and a **new, separate** market-wide surface is added for the independent/broader insight, or (b) the chart strip itself broadens. Recommended starting hypothesis for the Designer to evaluate: **keep (a)** — the chart strip's per-company coherence is a different, still-valid job from the broader market-strategy insight the user is now asking for; a new Data Story (`design/market-health/data-stories.md` already names "layoff activity" as a future catalogue direction, from the original 2026-09-04 spec) is the more natural home for sector/market-wide trend, not a scoping change to the existing chart. |
| Backend Spec | `backend/specs/market-health/api.md` | **update** — likely a new aggregate query (event counts/direction by sector, country, or time, independent of `matched_company`) alongside the existing tracked-company-scoped endpoint (which may stay as-is per the experience spec's resolution) |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **update** — new components for the resolved surface |
| Backend Implementation | `backend/src/` | after specs |
| Frontend Implementation | `frontend/src/` | after specs |

## Execution Plan

- [x] Step 1: `/new-experience` — resolved in `design/market-health/experience.md`'s Open
      Questions: chart strip stays tracked-company-scoped (real coherence, kept as-is); a new,
      separate data story carries the company-independent view
- [x] Step 2: `/new-backend-spec` — `backend/specs/market-health/api.md` updated: Story 2
      reuses the existing generic story endpoints, no new route; the story itself specified in
      `design/market-health/data-stories.md`
- [x] Step 3: `/new-frontend-spec` — `frontend/specs/market-health/architecture.md` updated:
      `EmploymentRiskStoryMessage` + `DataStoryMessage` becomes a thin `story_id` router
- [x] Step 4: `/implement-backend` — `market_stories.py`: `build_employment_risk_overview()`,
      new catalogue entry, `get_story()` dispatch extended. **Verified against real production
      data** (25 live US WARN rows): correctly aggregates 100% contraction / 2,762 roles
      affected, ranks Amazon/Synopsys/DP World/Qualtrics and others by impact, breaks down by
      state and sector — all independent of `matched_company`.
- [x] Step 5: `/implement-frontend` — `EmploymentRiskStoryMessage.tsx` (Hero+Meter for the
      contraction/expansion split, 3× `RankedBarList` for companies/regions/sectors),
      `DataStoryMessage.tsx` routes to it by `story_id`. `TaskPanel.tsx` needed **zero
      changes** — already fully catalogue-driven (`stories.map(...)`), confirmed by reading
      the real code, not assumed. Verified with a real `npm run build` — clean, zero
      TypeScript errors.

Every step executed in this single session, immediately after the parent change's US WARN
data went live — the "Sequencing note" that originally deferred this became moot once real
data made the scoping gap concrete rather than hypothetical.

## Superseded, in part (2026-09-11, hours later same day)

`changes/2026-09-11-employment-events-no-company-matching.md` reverses this change's
`matched_company`-based chart-strip decision (Step 1's "Decision: the chart strip stays
tracked-company-scoped as-is"). This change request itself stays `complete` — everything in
its own Execution Plan was genuinely built and verified — but that one decision is no longer
current. See the superseding change for the final state: the chart strip is removed entirely;
this change's other deliverable, the **"Employment risk across the market" data story, is
unaffected and is now the sole surface for employment events**.

## Decision Log
- 2026-09-11: Triaged as a companion change to `changes/2026-09-11-employment-event-ingestion.md`
  rather than folded into it — the scoping decision is distinct enough (its own cascade through
  experience → backend → frontend specs) to warrant its own audit trail, while staying clearly
  linked to the parent.
- 2026-09-11: Outcome confirmed no-change — `outcomes/understand-market-health-before-searching.md`
  already names sector-level risk in its success criteria (added earlier today), so this change
  fulfills an existing promise rather than opening a new one.
- 2026-09-11: Flagged a recommended starting hypothesis (keep the chart strip tracked-company-
  scoped; add a new, separate market-wide surface) for whoever runs Step 1 — not a final
  decision, since that's properly the Designer's call during `/new-experience`, but worth
  recording the reasoning now so it isn't relitigated from scratch.
- 2026-09-11: Execution deliberately deferred — user asked to build the WARN Firehose adapter
  first; this stayed `triaged` (not `in-progress`) until that was picked back up.
- 2026-09-11: **Closed, `complete`.** Real WARN Firehose data (25 rows) made the scoping
  question concrete rather than hypothetical — every one of the 25 real companies was
  unmatched to the 35 tracked ones, so the gap this change addresses was directly observable,
  not theoretical. Ran the full chain in one pass and verified each layer against real
  production data before moving to the next, same discipline as the parent change. The
  recommended starting hypothesis (keep the chart strip as-is, add a separate story) held —
  no reason found during implementation to revisit it.
