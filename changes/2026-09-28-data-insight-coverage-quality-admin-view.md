---
id: data-insight-coverage-quality-admin-view
date: 2026-09-28
trigger-type: stakeholder-request
change-type: new-feature
outcome: pipeline-processing-visibility
status: complete
---

# Change Request: Data Insight Coverage & Quality admin view

## Signal
See: `research/2026-09-28-data-insight-coverage-quality-admin-view.md`

## Outcome
See: `outcomes/pipeline-processing-visibility.md` — this is the sixth extension of the same
operator need ("don't make me query the database directly to know what the pipeline has
captured"), applied here to a new facet: not processing *status* (did it run, did it error) but
analytical *coverage and strength* — where the platform's captured data supports confident
insight vs. where it's thin. Confirmed as an extension (bucket A), not a new outcome — same
audience, same "operator-only, read-only visibility" scope, same pattern as the five prior
extensions (employment events, licensing, market-benchmark data, taxonomy health).

## Change Type
`new-feature`

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/pipeline-processing-visibility.md` | update — add a "Success looks like" bullet: the operator can see, at a glance, which countries/company sizes/sources/business areas the platform's data supports stronger vs. weaker insight for |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change — new page inside the existing admin dashboard, no navigation-model change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/pipeline-visibility/experience.md` | update — add a new section (own IA placement, user flow, edge cases) alongside the existing licensing/market-benchmark/taxonomy-health sections |
| Frontend Spec | `frontend/specs/pipeline-visibility/architecture.md` | not-applicable — `pipeline-visibility` has no separate frontend spec/build by design (server-rendered admin templates), same as every prior admin view |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | update — new query/aggregation logic and a new admin route; triggers `/mcp-access-review` automatically |
| Frontend Implementation | `frontend/src/` | no-change |
| Backend Implementation | `backend/src/` | update — new admin template + query functions |
| Plain-Language Overview | `OVERVIEW.md` | update — extend the existing "(Operator only) See what the data pipeline actually did" bullet to mention coverage/quality visibility, same as the 2026-09-16 licensing extension |
| MCP Access Review | `ACCESS.md` + MCP backend spec | update — new row under "Operator-only capabilities", `Not Exposed`, same reasoning as every existing row there (operator-only, no end-user data) |
| Polite Scraping Review | `DATA_SOURCES.md` + affected backend spec | not-applicable — no scraped source introduced or changed |
| Data Surface Review | data-story catalogue / admin dashboard / ad-hoc query layer | not-applicable — no new data category; this aggregates existing companies/postings/industry/country/source data, it doesn't introduce a new kind of fact |

## Execution Plan

- [x] Step 1: Manual edit — add the new "Success looks like" bullet to `outcomes/pipeline-processing-visibility.md`
- [x] Step 2: `/new-experience` — add the Data Insight Coverage & Quality section to `design/pipeline-visibility/experience.md`
- [x] Step 3: `/new-backend-spec` — update `backend/specs/pipeline-visibility/api.md` (runs `/mcp-access-review` automatically)
- [x] Step 4: `/implement-backend` — build the new admin view and its aggregation queries (verified end-to-end: `TestClient` GET `/admin/coverage-quality` → 200, against the real production database — 15,158 postings, real per-country/size/industry/source breakdowns)
- [x] Step 5: Manual edit — extend `OVERVIEW.md`'s operator-only bullet

## Decision Log
- 2026-09-28: Mapped to `outcomes/pipeline-processing-visibility.md` as an extension rather than a
  new outcome — same operator audience and "don't query the DB directly" pattern the outcome
  already serves five times over; this is a sixth facet (coverage/quality) rather than a new need.
- 2026-09-28: Split from a single operator message into two change requests, at the operator's
  own explicit request — this one covers the insight-coverage-and-quality half; the technical
  schema/exposure half is tracked separately in
  `changes/2026-09-28-technical-data-visibility-admin-view.md`.
- 2026-09-28: No frontend spec — `pipeline-visibility` has none by design (server-rendered, no
  separate frontend build), matching every prior admin view in this product.
- 2026-09-28: Scoping note carried into the backend spec step, not resolved here — "country"
  today only exists as posting-level free text (no per-company country field; Personio-sourced
  companies always have NULL country), and "industry"/"business area" today is a single flat tag
  per company (`COMPANY_INDUSTRY`). The backend spec must decide, explicitly, what "coverage by
  country" and "coverage by business area" honestly mean given these real data shapes, rather
  than implying a precision the underlying data doesn't have.
- 2026-09-28: Implementation verified end-to-end against the real production database (`TestClient`
  GET `/admin/coverage-quality` → 200; function-level and template-render checks also run
  directly against live data) — real, honest finding on first run: **63.5% of all 15,158 postings
  have no recorded country** (the "unknown" bucket dominates the By Country list), and `GB`/`UK`
  are currently stored as two separate country values rather than one normalized code — both are
  pre-existing data realities this view surfaces exactly as designed, not implementation bugs
  introduced by this change. The `GB`/`UK` split is a real gap worth a future `bug-fix` CR against
  `normalize_country()`, but is out of scope here — this change's job was making it visible, not
  fixing it.
