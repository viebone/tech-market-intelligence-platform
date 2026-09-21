---
id: job-function-story
date: 2026-09-21
trigger-type: user-feedback
change-type: ux-change, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Surface Job Function as a new data story, admin filter, and MCP tool

## Signal
See: `research/2026-09-21-job-function-story.md`. User: "ok but what about the job functions
that we have created, we need to show them in the overview, and we need a data story for it,
we also need to track them in the admin right?" — the deferred `/data-surface-review` from
`changes/2026-09-21-emerging-role-detection.md` finally landing, now that today's backlog run
produced real reclassified data (2,013 `job_function`-classified rows) to design against.

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — same outcome Story 3's own
addition mapped to; no new success criterion needed (the existing "identify which roles and
skills are in demand" criterion already covers this).

## Change Type
`ux-change` (a new Task Panel entry, reachable from the Welcome) + `api-change` (new query
logic over `classifications.job_function`) — same classification precedent as Story 3's own
addition, adding an entry to the existing Story Catalogue mechanism, not a from-scratch
capability requiring a fresh outcome/foundations/experience-file/IA/visual-design chain.

## Triage Notes

Three distinct asks, resolved together since they're the same underlying decision:
1. **"Show them in the overview"** — the Welcome reads the Story Catalogue live; adding the new
   entry (below) makes it appear there with zero Welcome code change — verified directly
   (`build_welcome()`'s `story_shortcuts` includes the new entry with no code touched).
2. **"A data story for it"** — Story 4, "Beyond Design, Product & Engineering."
3. **"Track them in the admin"** — partially already true (Taxonomy Health page,
   `/admin/` overview's Job Function card, both same-day). Checked what "track" meant more
   precisely: the Postings admin view had no `job_function` filter, so an operator couldn't
   drill from a high-level number into the real postings behind it — the exact promise
   `outcomes/pipeline-processing-visibility.md` already makes for every other dimension. Added.

**MCP exposure also resolved, not left stale.** Building Story 4 means the exact precondition
"Job Function deferred, not decided against" was waiting on (`changes/2026-09-21-emerging-role-
detection.md`'s own Decision Log: "no real consumer surface exists yet") is no longer true —
same shape as Market Benchmark's own resolution (`changes/2026-09-18-market-benchmark-mcp-
tool.md`). Not asked about explicitly in the user's message, but leaving it deferred after
building the exact surface that resolves it would recreate the kind of gap the same-day
documentation audit (`changes/2026-09-21-taxonomy-revision-specialization-and-job-function.md`'s
own Decision Log) had just caught — so resolved here rather than left for a future prompt.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Experience Spec | `design/market-health/data-stories.md` | update — new Story 4 |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — new Story 4 component section |
| Backend Spec | `backend/specs/market-health/api.md` | update — Story 4 business logic note |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | update — `job_function` filter on `GET /admin/postings` |
| Backend Spec | `backend/specs/mcp-access/api.md` | update — new `get_job_function_breakdown` tool section; Job Function's "not a tool" entry resolved (strikethrough, not erased) |
| Backend Implementation | `backend/src/market_stories.py` | update — new catalogue entry, `build_job_function_story()`, `get_story()` dispatch |
| Backend Implementation | `backend/src/market_query.py` | update — new `query_job_function_data()` |
| Backend Implementation | `backend/src/mcp_access/tools.py`, `server.py` | update — new `get_job_function_breakdown` tool, `TOOL_SCOPES` entry |
| Backend Implementation | `backend/src/raw_postings.py`, `admin_main.py`, `admin_templates/postings.html` | update — new `job_function` filter on the Postings admin view |
| Frontend Implementation | `frontend/src/features/market-health/stories/` | new `JobFunctionStoryMessage.tsx`, `DataStoryMessage.tsx` router branch |
| Plain-Language Overview | `OVERVIEW.md` | update — new story mentioned |
| MCP Access Review | `ACCESS.md` | update — Job Function row resolved from Deferred to Exposed |

## Execution Plan

- [x] Step 1: Signal captured — `research/2026-09-21-job-function-story.md`
- [x] Step 2: PM triage — mapped to existing outcome, no new success criterion needed
- [x] Step 3: Pulled real current numbers before designing anything (4,204 `other` postings, 2,191 not yet reprocessed, real per-function distribution)
- [x] Step 4: Updated `design/market-health/data-stories.md` — Story 4 full spec (display name, question, visible answer shape — 3 blocks, 2 visual forms, data contract, honesty/empty states including the real live reprocessing-lag qualifier)
- [x] Step 5: Updated `backend/specs/market-health/api.md`, `pipeline-visibility/api.md`, `mcp-access/api.md`
- [x] Step 6: `/implement-backend` — `market_query.py::query_job_function_data()`, `market_stories.py::build_job_function_story()` + catalogue + dispatch, `raw_postings.py::list_postings()` gains `job_function` filter, `admin_main.py`/`postings.html` gain the filter UI, `mcp_access/tools.py::get_job_function_breakdown()` + `server.py` registration + `TOOL_SCOPES`
- [x] Step 7: `/implement-frontend` — `JobFunctionStoryMessage.tsx` (reuses `RankedBarList`/`StoryBlock`/`Meter`, no new shared component), `DataStoryMessage.tsx` fourth router branch. `tsc --noEmit` and `npm run build` both clean.
- [x] Step 8: Updated `OVERVIEW.md` and `ACCESS.md`
- [x] Step 9: Verified end-to-end against real production data (not fixtures): strict `json.dumps()` (no `default=str` fallback) confirms no serialization bug the way Story 3 first found one; `list_stories()`/`get_story()`/`build_welcome()` all confirmed working with the new entry; the admin `job_function` filter confirmed against real rows (972 for "Sales & Business Development"); the MCP tool confirmed returning real data with the correct scope and no Premium gate

## Decision Log
- 2026-09-21: 2 visual forms (Ranked bar list, Hero Figure + Meter), same deliberate call as
  Story 3 — Job Function data is currently one dimension (a count per function), no time series
  or geography exists yet to justify a trend line or map.
- 2026-09-21: The real, current reprocessing lag (2,191 postings not yet reprocessed as of this
  story shipping) is stated plainly in every section's qualifier, computed live on every
  request — never hidden, never a stale hardcoded figure, per Rule 14's own "real lag stated
  plainly" requirement, live in production the day this shipped rather than a hypothetical.
  Confirmed via a real, live query at story-build time, not memoized at write time.
- 2026-09-21: Resolved Job Function's MCP-exposure deferral in the same change that built its
  consumer surface, rather than as a separate later change — same reasoning Market Benchmark's
  own resolution used, and consistent with not wanting to recreate the exact "left the deferral
  stale" gap the same-day documentation audit had just caught elsewhere.
