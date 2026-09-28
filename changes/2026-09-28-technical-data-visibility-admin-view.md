---
id: technical-data-visibility-admin-view
date: 2026-09-28
trigger-type: stakeholder-request
change-type: new-feature
outcome: pipeline-processing-visibility
status: complete
---

# Change Request: Technical Data Visibility admin view

## Signal
See: `research/2026-09-28-technical-data-visibility-admin-view.md`

## Outcome
See: `outcomes/pipeline-processing-visibility.md` — a seventh extension of the same operator
need, applied to yet another facet: not processing status, not insight coverage/quality (the
sibling request, `changes/2026-09-28-data-insight-coverage-quality-admin-view.md`), but the
platform's own technical data footprint — how much data exists, across how many tables, and
which capabilities are actually reachable from MCP vs. the frontend vs. neither. Same audience,
same operator-only read-only scope as every prior extension.

## Change Type
`new-feature`

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/pipeline-processing-visibility.md` | update — add a "Success looks like" bullet: the operator can see, at a glance, the platform's technical data footprint (table/row counts and growth) and which capabilities are exposed via MCP vs. the frontend API vs. neither |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change — new page inside the existing admin dashboard |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/pipeline-visibility/experience.md` | update — add a new section alongside the existing ones |
| Frontend Spec | `frontend/specs/pipeline-visibility/architecture.md` | not-applicable — same as every prior admin view, no separate frontend spec/build |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | update — new route(s): a table/row-count summary and an MCP/frontend exposure summary; triggers `/mcp-access-review` automatically |
| Frontend Implementation | `frontend/src/` | no-change |
| Backend Implementation | `backend/src/` | update — new admin template + query functions |
| Plain-Language Overview | `OVERVIEW.md` | update — extend the same operator-only bullet again (or add one sentence), consistent with the sibling change request |
| MCP Access Review | `ACCESS.md` + MCP backend spec | update — new row under "Operator-only capabilities", `Not Exposed`, same reasoning as every existing row |
| Polite Scraping Review | `DATA_SOURCES.md` + affected backend spec | not-applicable — no scraped source introduced or changed |
| Data Surface Review | data-story catalogue / admin dashboard / ad-hoc query layer | not-applicable — no new data category; this reports on the shape/size of existing tables and existing exposure decisions, it doesn't introduce a new kind of fact |

## Execution Plan

- [x] Step 1: Manual edit — add the new "Success looks like" bullet to `outcomes/pipeline-processing-visibility.md`
- [x] Step 2: `/new-experience` — add the Technical Data Visibility section to `design/pipeline-visibility/experience.md`
- [x] Step 3: `/new-backend-spec` — update `backend/specs/pipeline-visibility/api.md` (runs `/mcp-access-review` automatically)
- [x] Step 4: `/implement-backend` — build the new admin view and its aggregation queries (verified end-to-end: `TestClient` GET `/admin/technical-data` → 200, against the real production database; `_parse_access_md()` correctly classified all 25 real capability rows — 9 MCP-reachable, 16 frontend/API-only, 0 unexposed)
- [x] Step 5: Manual edit — extend `OVERVIEW.md`'s operator-only bullet

## Decision Log
- 2026-09-28: Mapped to `outcomes/pipeline-processing-visibility.md` as an extension, not a new
  outcome — same reasoning as the sibling change request.
- 2026-09-28: Split from a single operator message into two change requests, at the operator's
  own explicit request — this one covers the technical/schema-and-exposure half; the
  insight-coverage-and-quality half is tracked separately in
  `changes/2026-09-28-data-insight-coverage-quality-admin-view.md`.
- 2026-09-28: `ACCESS.md` already exists as the per-capability frontend/backend-API/MCP
  reachability matrix (built for Rule 12). The "how many queries are open to MCP and to the
  frontend" part of this request is very likely best served by summarizing/counting `ACCESS.md`'s
  existing rows rather than building a second, parallel tracking mechanism — left as an explicit
  decision for the backend spec step, not resolved here, since `/new-backend-spec` is where that
  design call belongs.
- 2026-09-28: No frontend spec — same reasoning as the sibling change request.
- 2026-09-28: Implementation verified end-to-end against the real production database
  (`TestClient` GET `/admin/technical-data` → 200; `get_technical_footprint()` and
  `_parse_access_md()` both run directly against live data too). Real numbers on first run:
  29,095 job-posting-pipeline rows, 36,413 employment events, 341 market-benchmark rows, 7,602
  trusted-statistics rows, 2 feedback rows. The `ACCESS.md` parse correctly found all 25 real
  capability rows and classified them 9 MCP-reachable / 16 frontend-or-API-only / 0 fully
  unexposed — cross-checked by hand against `ACCESS.md`'s actual content, exact match, including
  two rows whose MCP Tool cell has no ✅/❌ at all ("N/A as a standalone capability," "❌ Not
  applicable") — both correctly fell into `frontend_or_api_only` via the Frontend/Backend API
  columns before the parser's fail-safe branch was ever reached.
