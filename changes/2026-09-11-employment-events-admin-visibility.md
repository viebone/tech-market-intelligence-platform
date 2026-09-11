---
id: employment-events-admin-visibility
date: 2026-09-11
trigger-type: stakeholder-request
change-type: ux-change, api-change
outcome: pipeline-processing-visibility
status: in-progress
---

**Remaining work**: implementation is complete and verified locally against the real
production database (see Decision Log) — not yet deployed. Needs: commit, push, and a live
`curl`/browser check of `/admin/employment-events` on the deployed `romantic-presence`
service before this closes, same discipline as `changes/2026-09-11-employment-event-ingestion.md`.

# Change Request: Employment events visibility in the admin pipeline dashboard

## Signal
See: `research/2026-09-11-employment-events-admin-visibility.md`

## Outcome
See: `outcomes/pipeline-processing-visibility.md` — "The person running the platform can see
exactly what the pipeline has processed and indexed." Written before `employment_events`
existed; this change extends it to cover the employment-events pipeline the same way it
already covers the job-postings pipeline.

## Change Type
`ux-change` (a new view + nav item in the existing admin dashboard) + `api-change` (new
server-rendered read routes over an existing table — no new data model, `employment_events`
and `employment_event_cursors` already exist per `changes/2026-09-11-employment-event-ingestion.md`
and its follow-ons).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/pipeline-processing-visibility.md` | update — acknowledge the employment-events pipeline as a second pipeline this outcome covers |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change — this surface already sits outside the three-column IA model (see `design/pipeline-visibility/experience.md`'s own Open Questions); adding a sidebar item to an already-out-of-IA-scope dashboard doesn't touch it |
| Visual Design | `design/visual-design.md` | no-change — reuses existing table/card/badge/bar-row tokens already used by Postings/Overview, no new pattern needed |
| Experience Spec | `design/pipeline-visibility/experience.md` | update — new zone, User Flow step, Interactions, Edge Cases for Employment Events |
| Frontend Spec | n/a | no-change — this dashboard is server-rendered Jinja2, no separate frontend spec (see backend spec's Deployment topology) |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | update — new read endpoints, Business Logic, filter/sort rules |
| Frontend Implementation | `backend/src/admin_templates/` | update — new templates, new sidebar link |
| Backend Implementation | `backend/src/admin_main.py`, `backend/src/employment_events_storage.py` | update — new routes, new read/aggregate query functions |

## Execution Plan

- [x] Step 1: Capture signal — `research/2026-09-11-employment-events-admin-visibility.md`
- [x] Step 2: Update `outcomes/pipeline-processing-visibility.md` (manual edit)
- [x] Step 3: Update `design/pipeline-visibility/experience.md` (manual edit, scoped)
- [x] Step 4: Update `backend/specs/pipeline-visibility/api.md` (manual edit, scoped)
- [x] Step 5: Implement backend — `employment_events_storage.py` read/aggregate functions, `admin_main.py` routes, new templates, sidebar nav link
- [x] Step 6a: Verify new query functions locally against the real production database
      (`employment_events_storage.get_summary()`/`list_events()`/`get_event()`) — 79 real
      events, correct per-source counts, correct streaming cursor, correct filter/sort/404
      behaviour, all confirmed against live data
- [x] Step 6b: Render every new/changed template (`employment_events.html`,
      `employment_event_detail.html`, `overview.html`) with both real and empty-state data —
      no Jinja errors
- [ ] Step 6c: Commit, push, and verify `/admin/employment-events` live on the deployed
      admin service (not yet done — this session's changes are local only)

## Decision Log
- 2026-09-11: No new "ingestion run history" table for employment events — unlike job postings,
  employment-event ingestion has no `ingestion_runs`-equivalent row per run today (see
  `backend/EMPLOYMENT_EVENTS.md`). Rather than inventing one not called for by any spec, the
  Overview summary reads `MAX(ingested_at)` per source and the existing `employment_event_cursors`
  table directly — real state, no new tracking table added speculatively.
- 2026-09-11: Scoped to List + Detail + an Overview summary card, matching the existing
  Postings/Runs pattern exactly rather than inventing a different shape for this pipeline.
