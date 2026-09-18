---
id: admin-market-benchmark-visibility
date: 2026-09-18
trigger-type: user-feedback
change-type: api-change
outcome: pipeline-processing-visibility
status: complete
---

# Change Request: Admin visibility into market observations, skill associations, and scraped-source ingestion runs

## Signal
See: `research/2026-09-18-admin-market-benchmark-visibility.md`

## Outcome
See: `outcomes/pipeline-processing-visibility.md` — extended 2026-09-18 with a new success
criterion (this is the third pipeline this outcome has been extended to cover, after employment
events 2026-09-11 and licensing 2026-09-16 — same "don't make me query the database directly"
need, new data).

## Change Type
`api-change` — new read-only admin routes/views over existing tables (`market_observations`,
`skill_associations`, `scrape_ingestion_runs`, `scrape_extractions`). No new data model; no
change to the ingestion write path.

## Triage Notes (Step 2)

Maps directly to `outcomes/pipeline-processing-visibility.md`, following the exact precedent of
its two prior extensions (employment-events admin visibility, licensing visibility) — same
outcome, same admin-only surface, new pipeline's data. Not a new area.

Checked the real current state of `backend/specs/pipeline-visibility/api.md` and `admin_main.py`
before proposing anything (per the instruction not to assume from summary prose): 5 real routes
exist today — Overview, Postings (+detail), Ingestion Runs (+detail — job-sync only),
Employment Events (+detail), Licensing (flat list). None reads `market_observations`,
`skill_associations`, `scrape_ingestion_runs`, or `scrape_extractions`.

**MCP Access Review**: this product has an MCP layer. Every prior pipeline-visibility addition
(employment-events admin visibility, licensing) added its own explicit `ACCESS.md` row rather
than skipping the review — same reasoning applies again: this is an operator-only admin surface,
JWT-protected, no end-user data, `outcomes/pipeline-processing-visibility.md` scopes it to the
person running the platform. Adding the same row, same reasoning, rather than re-running the
full skill for what is the third identical case.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/pipeline-processing-visibility.md` | update (done — new success criterion added) |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change (admin dashboard is explicitly carved out of the consumer nav model, same as every prior pipeline-visibility addition) |
| Visual Design | `design/visual-design.md` | no-change (admin dashboard's own plain server-rendered look is out of scope of the consumer visual system, same precedent) |
| Experience Spec | `design/pipeline-visibility/experience.md` | update — new List/Detail flows for the two new tables, a new flat-list flow for scrape run cadence, following the existing User Flow numbering |
| Frontend Spec | none (admin dashboard has none by design — server-rendered, folded into backend spec) | no-change |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | update |
| Frontend Implementation | `frontend/src/` | no-change |
| Backend Implementation | `backend/src/` (`admin_main.py`, `scraping_storage.py`, new templates) | update |
| Plain-Language Overview | `OVERVIEW.md` | no-change — this is an internal operator tool addition, no real end user notices anything |
| MCP Access Review | `ACCESS.md` + `backend/specs/mcp-access/api.md` | update — new row, `Not Exposed`, same reasoning as the two prior admin-visibility rows |
| Polite Scraping Review | `DATA_SOURCES.md` + affected backend spec | no-change — this doesn't touch scraping mechanics (cadence, robots.txt, dedupe), only adds a read-only view over already-stored data |

## Design (Backend Engineer judgment, `directive: low`)

**Three new admin surfaces, all read-only, all JWT-protected (existing `require_admin_session`):**

1. **Market Observations** — List (filter: `source`, `entity_type`, `entity_name`, `employment_type`; sort: `period_end`, `entity_name`, `rank`, `vacancy_count`) → Detail (full row incl. `raw_response` pretty-printed, plus — if `scrape_extractions` has a row for the observation's `source_url` — the extraction's `content_hash`/`model`/`extracted_at`, so an operator can see directly whether this observation came from a fresh extraction or a reused cache hit). Same List→Detail pattern as Postings/Employment Events, not the flat-list pattern (Licensing) — this table is filterable and will grow as more roles/sources are added.
2. **Skill Associations** — same List→Detail pattern, filtered by `source`/`role_name`, sorted by `rank`/`percentage`/`job_count`.
3. **Scraped Source Runs** — a flat list (same pattern as Licensing, not List→Detail): one row per **registered** adapter (`scraping.ALL_SCRAPED_SOURCE_ADAPTERS`), not merely one per row present in `scrape_ingestion_runs` — deliberately different from the Employment Events summary's "only sources present in data" convention, because the entire point of this view is showing an operator when a registered source last ran (or that it's *never* run), which the "only if present" convention would hide. Each row: `source`, `last_run_at` (or "never run"), `min_run_interval_days` (from `scraping.MIN_RUN_INTERVAL_DAYS`), `next_due_at` (computed), `is_due` (bool, badge).

No new tables, no new columns — purely additive read functions in `scraping_storage.py`
(mirrors `employment_events_storage.py`'s `list_events`/`get_event`/`get_distinct_countries`
pattern exactly: closed-set-validated `sort`, `WHERE` built from named optional params, never
raw SQL fragments) and new routes/templates in `admin_main.py`/`admin_templates/`.

## Execution Plan

- [x] Step 1: Signal captured — `research/2026-09-18-admin-market-benchmark-visibility.md`
- [x] Step 2: PM triage — mapped to `pipeline-processing-visibility`, extended its success criteria
- [x] Step 3: Updated `design/pipeline-visibility/experience.md` — new Sidebar Nav entries, User Flow step 10, Visual Design notes, Interactions rows, and Edge Cases for Market Observations/Skill Associations (List→Detail) and Scraped Source Runs (flat list)
- [x] Step 4: `/new-backend-spec` — updated `backend/specs/pipeline-visibility/api.md` in place: Data Models note, 5 new API Endpoints sections (Market Observations list+detail, Skill Associations list+detail, Scraped Source Runs flat list), Business Logic (query construction, extraction-provenance fresh/reused, scrape-run cadence status reusing `_due_from_last_run()`), Tech Decisions (new `scraping_storage.py` read functions, no new tables/columns)
- [x] Step 5: `/implement-backend` — added to `scraping_storage.py`: `list_market_observations`/`get_market_observation`, `list_skill_associations`/`get_skill_association`, `get_extraction_for_url`, `list_scrape_runs` (reuses `_due_from_last_run()`), plus distinct-value helpers for filter dropdowns. Added 5 routes to `admin_main.py` and 5 templates (`market_observations.html`, `market_observation_detail.html`, `skill_associations.html`, `skill_association_detail.html`, `scrape_runs.html`), updated `base.html`'s nav. No new tables/columns.
- [x] Step 6: MCP Access Review — added the `ACCESS.md` row (`Not Exposed`, same operator-only reasoning as the two prior admin-visibility rows)
- [x] Step 7: Verified against the real production data already in place — all 5 routes smoke-tested via `TestClient` against the real production DB (not fixtures): `/admin/market-observations` (200), `/admin/skill-associations` (200), `/admin/scrape-runs` (200, correctly shows `itjobswatch` last run 2026-09-18, next due 2026-09-25, "Up to date"), and both detail pages (200, correctly showing "Fresh extraction — gemini-2.5-flash" provenance for a real observation). Existing test suites (`test_scraping.py` 37/37, `test_source_licences.py` 4/4) still pass; `admin_main.py` imports cleanly.

## Decision Log
- 2026-09-18: Chose List→Detail for Market Observations/Skill Associations (growing, filterable,
  each row has enough provenance to warrant a detail page) and a flat list for Scraped Source
  Runs (tiny, one row per registered adapter, no deeper record to drill into) — following the
  existing precedent split this dashboard already has (Postings/Employment Events are
  List→Detail; Licensing is flat).
- 2026-09-18: Scraped Source Runs shows every *registered* adapter, not just ones present in
  `scrape_ingestion_runs` — a deliberate, noted deviation from the Employment Events summary's
  "present in data only" convention, because this view's whole purpose is surfacing a
  never-yet-run source, not hiding it.
