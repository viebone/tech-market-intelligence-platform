---
id: admin-licensing-visibility
date: 2026-09-16
trigger-type: stakeholder-request
change-type: ux-change, api-change
outcome: pipeline-processing-visibility
status: complete
---

# Change Request: Data source licensing visibility in the admin dashboard

## Signal
See: `research/2026-09-16-admin-licensing-visibility.md`

## Outcome
See: `outcomes/pipeline-processing-visibility.md` — amended today (Extended 2026-09-16) —
this is the third extension of the same operator-visibility pattern (postings → employment
events → now scraped-source licensing), same bucket, no new outcome needed.

## Change Type
`ux-change` (a new sidebar view in the existing admin dashboard) + `api-change` (a new read-only
endpoint serving it).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/pipeline-processing-visibility.md` | update (done — Extended 2026-09-16 note + Success-looks-like bullet) |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change — the admin dashboard's own sidebar is scoped inside `design/pipeline-visibility/experience.md`'s own Information Architecture section, not the product-wide IA (same precedent as the 2026-09-11 Employment Events sidebar addition) |
| Visual Design | `design/visual-design.md` | no-change — reuses existing table/badge/sidebar tokens, no new visual language needed |
| Experience Spec | `design/pipeline-visibility/experience.md` | update — new Sidebar Nav item, Information Architecture zone, User Flow step, and a data-legibility pass on the new table (per the `data-legibility` skill — every licence-status value must be self-explanatory: what "confirmed" means, what "commercial use" means, plain-language not raw booleans) |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | update — new `GET /admin/licensing` endpoint (or equivalent), following the exact List pattern `GET /admin/employment-events` already established; reads `scraping.licences.SOURCE_LICENCES` directly (an in-memory registry, not a DB table — no new Data Model needed) |
| Frontend Spec | — | no-change — `pipeline-visibility` has none by design (server-rendered, folded into the backend spec, per `CLAUDE.md`) |
| Frontend Implementation | `frontend/src/` | no-change |
| Backend Implementation | `backend/src/` | update — new route in `admin_main.py`, new Jinja2 template |
| Plain-Language Overview | `OVERVIEW.md` | update — the existing "(Operator only) See what the data pipeline actually did" bullet already names postings and employment events; extend it to mention licensing status, for the same reason that bullet exists at all |
| MCP Access Review | `ACCESS.md` + MCP backend spec | not-applicable — admin-only, no MCP-relevant backend capability |
| Polite Scraping Review | `DATA_SOURCES.md` + affected backend spec | not-applicable — this change adds *visibility* into existing licence data, it doesn't introduce or change a scraped source itself |

## Execution Plan

- [x] Step 1: Signal captured — `research/2026-09-16-admin-licensing-visibility.md`
- [x] Step 2: Outcome amended — `outcomes/pipeline-processing-visibility.md`
- [x] Step 3: `/new-experience` — updated `design/pipeline-visibility/experience.md` in place
      (new Sidebar Nav item "Sources & Licensing", User Flow step 9, Visual Design badge
      treatment, two new Edge Cases)
- [x] Step 4: `/new-backend-spec` — updated `backend/specs/pipeline-visibility/api.md` in place
      (new `GET /admin/licensing` endpoint, Data Models + Tech Decisions notes on the deliberate
      in-memory-registry exception)
- [x] Step 5: `/implement-backend` — new `admin_main.py` route (`/admin/licensing`), new
      `licensing.html` template, sidebar link in `base.html`. Verified end-to-end with a real
      test client: renders real registry data (itjobswatch's confirmed CC BY-NC-SA 4.0, correct
      badges), auth-redirects when unauthenticated, and the commercial-mode-on banner renders
      correctly when `TMIP_COMMERCIAL_MODE=true`.
- [x] Step 6: Manual edit — `ACCESS.md`'s Operator-only capabilities table, new row
- [x] Step 7: Manual edit — `OVERVIEW.md`'s operator-only bullet, mentions licensing status

## Decision Log
- 2026-09-16: Triaged as Bucket A against `outcomes/pipeline-processing-visibility.md` — same
  "operator can see X without querying the DB/reading code" shape already extended once for
  employment events (`changes/2026-09-11-employment-events-admin-visibility.md`). Amended the
  outcome in place, same precedent, no new outcome.
- 2026-09-16: No frontend spec/implementation — `pipeline-visibility` is server-rendered by
  design, confirmed against `CLAUDE.md`'s Spec Chain Status table and every existing admin view.
- 2026-09-16: No new Data Model — `SOURCE_LICENCES` is an in-memory Python registry
  (`scraping/licences.py`), not a database table; the new endpoint reads it directly, same as
  how `GET /admin/employment-events` reads a real table. Worth flagging in the backend spec
  update: if this registry pattern is ever moved to the database (e.g. to support per-source
  audit history), this endpoint's implementation would need revisiting — not a concern today.
