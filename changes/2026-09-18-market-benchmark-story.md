---
id: market-benchmark-story
date: 2026-09-18
trigger-type: user-feedback
change-type: ux-change, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Surface market-benchmark data as a new data story ("Independent market benchmark")

## Signal
See: `research/2026-09-18-market-benchmark-story.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — updated with a new success
criterion (seeing this platform's own read alongside an independent benchmark). Maps to an
existing outcome this data was always a strong candidate for, per
`backend/specs/scraped-data-sources/api.md`'s own "What this doesn't decide" note, written
2026-09-16 before real data existed to act on.

## Change Type
`ux-change` (a new Task Panel entry, reachable from the Welcome) + `api-change` (new query
logic over `market_observations`/`skill_associations`, filtered/licence-gated). Same
classification precedent as the original Story 2 addition
(`changes/2026-09-11-employment-events-independent-scope.md`) — adding an entry to the
existing Story Catalogue mechanism, not a brand-new capability requiring a fresh
outcome/foundations/experience-file/IA/visual-design chain from scratch.

## Triage Notes (Step 2)

**Terminology clarified with the user first**: "entry story"/"overview" map to this platform's
own terms — the **Welcome** ("About this platform") and **Story 1** ("What we know about the
market"). The Welcome reads the Story Catalogue live and adds no code of its own for a new
entry; Story 1's own data contract is explicitly scoped to platform-owned postings data only.
So the right shape is a **new, dedicated Story** (Story 3), same pattern Story 2 already
established — confirmed with the user before proceeding.

**Licence decision, raised before any implementation** (every prior spec pass on this data
flagged it as unresolved, explicitly saying it must be resolved "before this data is ever
exposed through anything monetized — not something to discover after the fact"): IT Jobs
Watch's licence is CC BY-NC-SA 4.0 (NonCommercial); this platform has a paid Premium tier.
Asked the user how to handle this. User answered "Free tier only" — clarified back that the
consumer web app has no Free/Premium tier at all today (unlike the MCP layer's
`get_salary_stats — Premium plan only` gating), so this is satisfied by construction: the new
story lives in the same free, open experience everyone already gets. Documented as a flag to
revisit if a paid consumer feature is ever built on this data later (`backend/specs/market-health/api.md`
— Business Logic). User confirmed: "please go ahead."

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | update — new success criterion |
| Design Foundations | `design/foundations.md` | no-change — no new AI behavior (deterministic story, no LLM call, same as Stories 1-2) |
| Information Architecture | `design/information-architecture.md` | no-change — the Welcome/Story Catalogue mechanism already covers this; no new nav concept |
| Visual Design | `design/visual-design.md` | no-change — reuses existing block vocabulary (Ranked bar list, Meter) |
| Experience Spec | `design/market-health/data-stories.md` | update — new Story 3 |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — new Story 3 component section |
| Backend Spec | `backend/specs/market-health/api.md` | update — Data Models read-only note, Story 3 business logic, licence gate/attribution |
| Frontend Implementation | `frontend/src/features/market-health/stories/` | update — new `MarketBenchmarkStoryMessage.tsx`, `DataStoryMessage.tsx` router branch + `attribution_text` field |
| Backend Implementation | `backend/src/market_stories.py` | update — new catalogue entry, `build_market_benchmark_story()`, `get_story()` dispatch |
| Plain-Language Overview | `OVERVIEW.md` | update — new story mentioned; also corrected a small inconsistency found while here (the 2026-09-18 admin dashboard additions from the *previous* change request were reasoned as "no user-visible impact" and left out, but the precedent this file already set for the 2026-09-16 licensing admin view says otherwise — added retroactively) |
| MCP Access Review | `ACCESS.md` + `backend/specs/mcp-access/api.md` | no-change — this is a consumer web UI story, not an MCP tool; MCP exposure for this data remains deferred |
| Polite Scraping Review | `DATA_SOURCES.md` + affected backend spec | no-change — doesn't touch scraping mechanics, only adds a read-only consumer surface |

## Execution Plan

- [x] Step 1: Signal captured — `research/2026-09-18-market-benchmark-story.md`, including the licence decision
- [x] Step 2: PM triage — mapped to `understand-market-health-before-searching`, updated its success criteria
- [x] Step 3: Updated `design/market-health/data-stories.md` — Story 3 ("What does an independent market benchmark say?"): display name, question, audience job, visible answer shape (4 blocks: demand, coverage/pay-availability, pay by role, skills), data contract, honesty/empty states, relationship to existing experience. Updated "Future catalogue direction" to record Story 3 as no longer a future direction.
- [x] Step 4: Updated `backend/specs/market-health/api.md` — read-only Data Models note over `market_observations`/`skill_associations`, Story 3 paragraph (no new route, catalogue operation), licence-gate/attribution Business Logic note, explicit no-paid-tier-gating note with a flag to revisit later
- [x] Step 5: Updated `frontend/specs/market-health/architecture.md` — Story 3 component section, `DataStoryMessage` third router branch
- [x] Step 6: `/implement-backend` — `market_stories.py`: `STORY_CATALOGUE` gains `market-benchmark`; `build_market_benchmark_story()` (licence-gated via `is_source_usable("itjobswatch")`, queries `market_observations`/`skill_associations` filtered to `source="itjobswatch"`, never joined to postings data); `get_story()` dispatch. **Found and fixed a real bug during verification**: `salary_median` (Postgres `NUMERIC` → Python `Decimal`) isn't JSON-serializable by Starlette's plain `JSONResponse` — confirmed by a real `TestClient` call against the endpoint (raised `TypeError: Object of type Decimal is not JSON serializable`), fixed by casting to `float` before returning.
- [x] Step 7: `/implement-frontend` — new `MarketBenchmarkStoryMessage.tsx` (reuses `RankedBarList`/`StoryBlock`/`Meter`, no new shared component needed), `DataStoryMessage.tsx` gains a third router branch and an optional `attribution_text` field on the shared `DataStoryResult` interface. `tsc --noEmit` clean, `npm run build` clean.
- [x] Step 8: Updated `OVERVIEW.md` — new story mentioned; corrected the admin-dashboard omission from the prior change request
- [x] Step 9: Verified end-to-end against real production data (not fixtures) via `TestClient`: `GET /api/market-health/stories` includes `market-benchmark`; `POST /api/market-health/stories/market-benchmark` returns 200 with real demand/pay/skill figures for the 3 currently-observed roles (of 8 tracked); `build_welcome()` automatically includes the new shortcut with zero Welcome code changes, confirming the catalogue-operation design held.

## Decision Log
- 2026-09-18: Classified `ux-change` + `api-change`, not `new-feature` — the Story Catalogue
  mechanism already exists; adding an entry is the same weight as Story 2's own addition, not
  a from-scratch capability requiring a new experience-spec file.
- 2026-09-18: Chose 2 distinct visual forms (Ranked bar list, Meter) rather than 3+ — a
  deliberate call given the data's real shape (demand and pay are each one dimension per role;
  no geography or time-series dimension exists yet to justify a map or trend line). Documented
  explicitly in `data-stories.md` as a judgment call, not an oversight.
- 2026-09-18: No paid/Premium gating built — the consumer web app has no account/tier system to
  gate against. Flagged explicitly in the backend spec to revisit if that ever changes, so the
  NC-licence question isn't silently forgotten a second time.
- 2026-09-18: Corrected the previous change request's (`changes/2026-09-18-admin-market-benchmark-visibility.md`)
  OVERVIEW.md determination — reasoned "no-change" for an operator-only addition, but this
  file's own real precedent (the 2026-09-16 licensing admin view) already treats admin-only
  additions as worth a line here. Fixed retroactively rather than left inconsistent.
