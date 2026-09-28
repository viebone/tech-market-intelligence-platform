---
id: consolidate-sources-licensing-views
date: 2026-09-28
trigger-type: stakeholder-request
change-type: ux-change, api-change
outcome: pipeline-processing-visibility
status: complete
---

# Change Request: Consolidate Sources & Licensing, Scraped Source Runs, and Statistics Sources into one view

## Signal
See: `research/2026-09-28-consolidate-sources-licensing-views.md`

## Outcome
See: `outcomes/pipeline-processing-visibility.md` — an eighth extension of the same operator
need. Not a new capability (bucket A, not B): every fact in the merged view already exists on
one of the three current pages; this is a restructuring of how existing pipeline-visibility
information is organized, for the same "operator shouldn't have to hunt across pages to
understand one thing" reason the outcome already serves.

## Change Type
`ux-change` (restructures three existing admin views into one) + `api-change` (the three
underlying routes/query functions consolidate into one)

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/pipeline-processing-visibility.md` | update — note this consolidation under a new "Extended 2026-09-28" paragraph; no new "Success looks like" bullet needed, since the existing bullets about seeing licence status and scraped/statistics-source state already cover what this view shows, just not where |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change — still inside the existing operator-only admin surface, sidebar item count decreases, no navigation-model change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/pipeline-visibility/experience.md` | update — merge User Flow steps 9 ("Sources & Licensing"), part of 10 ("Scraped Source Runs"), and 11 ("Statistics Sources") into one step; update the Sidebar Nav zone description (two fewer nav entries); update Visual Design's per-view notes accordingly |
| Frontend Spec | `frontend/specs/pipeline-visibility/architecture.md` | not-applicable — no separate frontend spec, same as this whole admin surface |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | update — merge `GET /admin/licensing`, `GET /admin/scrape-runs`, and `GET /admin/statistics-sources` into one route (keeping the `/admin/licensing` path — it already covers every source type; the other two paths are removed); merge their three query functions into one; triggers `/mcp-access-review` |
| Frontend Implementation | `frontend/src/` | no-change |
| Backend Implementation | `backend/src/` | update — `admin_main.py` route removal/merge, a new combined query function, one merged template, `base.html` nav update |
| Plain-Language Overview | `OVERVIEW.md` | no-change — purely an admin-UI reorganization; the operator-only bullet already describes "every external data source's licence status," which stays true, just consolidated onto one page instead of three (no real end user notices anything, same reasoning as the 2026-09-18 admin-view precedent) |
| MCP Access Review | `ACCESS.md` + MCP backend spec | update — corrected during backend-spec triage: `/admin/scrape-runs`/`/admin/statistics-sources` were never their own `ACCESS.md` rows, they were already bundled into "Market-benchmark data admin visibility" and "Trusted statistics admin visibility." Those two rows lose the now-removed routes from their route lists; "Data source licensing status" gains a note that it now also covers cadence for every source type. Same `Not Exposed` decision throughout |
| Polite Scraping Review | `DATA_SOURCES.md` + affected backend spec | not-applicable — no change to scraping mechanics (cadence, pacing, dedupe, licence enforcement) themselves, only to how their status is displayed |
| Data Surface Review | data-story catalogue / admin dashboard / ad-hoc query layer | not-applicable — no new data category; this reorganizes existing facts, it doesn't introduce a new kind of fact |

## Execution Plan

- [x] Step 1: Manual edit — add an "Extended 2026-09-28" paragraph to `outcomes/pipeline-processing-visibility.md`
- [x] Step 2: `/new-experience` — merge the three relevant User Flow steps and the Sidebar Nav zone in `design/pipeline-visibility/experience.md`
- [x] Step 3: `/new-backend-spec` — merge the three endpoints/query functions in `backend/specs/pipeline-visibility/api.md` (runs `/mcp-access-review` automatically)
- [x] Step 4: `/implement-backend` — merge the routes, query function, and template; remove the two now-redundant routes/templates/nav entries (verified end-to-end: `TestClient` GET `/admin/licensing` → 200 with all 4 categories, correct cadence, and trusted-statistics sub-detail, against the real production database; `GET /admin/scrape-runs` and `GET /admin/statistics-sources` both now 404, confirming actual removal)

## Decision Log
- 2026-09-28: Mapped to `outcomes/pipeline-processing-visibility.md` as an extension (bucket A) —
  this reorganizes existing operator-visibility facts, it doesn't introduce a new one.
- 2026-09-28: Confirmed during triage (reading `source_licences.py` directly) that the *licence*
  dimension is already unified across all 11 registered sources via `SOURCE_LICENCES` — the real
  fragmentation is *cadence* (only scraped + trusted-statistics sources have one, since
  job-posting/employment-event adapters run on a shared cron rather than an individually-gated
  cadence) and *collected volume* (series/observation counts, trusted-statistics only today).
  The merged view must show "—" or an honest "runs on the shared daily schedule" note for
  sources that don't have a per-source cadence, rather than inventing one.
- 2026-09-28: Decision on which URL survives — keep `/admin/licensing`'s path (it already covers
  every source type) and fold `/admin/scrape-runs`/`/admin/statistics-sources` into it, rather
  than introducing a fourth new path. Kept the "Sources & Licensing" label rather than renaming
  it, since the merge extends what it covers without changing what the name promises.
- 2026-09-28: During the backend-spec step, discovered the initial triage's MCP Access Review
  assumption was wrong — `/admin/scrape-runs` and `/admin/statistics-sources` never had their own
  `ACCESS.md` rows; they were already bundled into broader "Market-benchmark data admin
  visibility" and "Trusted statistics admin visibility" rows. Corrected: those two rows lose the
  removed routes from their lists instead of two rows collapsing into one.
