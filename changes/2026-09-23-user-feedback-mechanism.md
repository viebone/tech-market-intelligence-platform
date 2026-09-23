---
id: user-feedback-mechanism
date: 2026-09-23
trigger-type: stakeholder-request
change-type: new-feature
outcome: user-feedback-is-heard-and-shapes-the-platform
status: complete
---

# Change Request: User feedback — product-level rating and per-Data-Story reactions

## Signal
See: `research/2026-09-23-user-feedback-mechanism.md`

## Outcome
See: `outcomes/user-feedback-is-heard-and-shapes-the-platform.md`

## Change Type
new-feature

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/user-feedback-is-heard-and-shapes-the-platform.md` | create |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | update — new persistent Task Panel element ("Give Feedback"), pinned at the bottom, distinct from the existing three-part structure (welcome / story catalogue / pinned feature tasks) |
| Visual Design | `design/visual-design.md` | update — new component patterns: feedback modal, 1–5 rating control, thumbs up/down control, confirmation/thank-you state |
| Experience Spec | `design/feedback/experience.md` (new) + `design/market-health/data-stories.md` / `design/market-health/experience.md` (update — thumbs at bottom of each Data Story) | create + update |
| Frontend Spec | `frontend/specs/user-feedback/architecture.md` | create |
| Backend Spec | `backend/specs/user-feedback/api.md` (create) + `backend/specs/pipeline-visibility/api.md` (update — new admin routes) | create + update |
| Frontend Implementation | `frontend/src/` | update |
| Backend Implementation | `backend/src/` (incl. admin surface, folded into `admin_main.py` per existing pattern) | update |
| Plain-Language Overview | `OVERVIEW.md` | update |
| MCP Access Review | `ACCESS.md` + `backend/specs/mcp-access/api.md` | update — product has an MCP layer; runs automatically as part of `/new-backend-spec` |
| Polite Scraping Review | `DATA_SOURCES.md` | not-applicable (no scraped source involved) |
| Data Surface Review | admin dashboard (new "User Feedback" view) | update — genuinely new data category (satisfaction ratings + reactions + written comments); runs `/data-surface-review` explicitly |

## Execution Plan

- [x] Step 1: `/new-outcome` (manual — `pm: manual` per `.outcome/config.yaml`) — `outcomes/user-feedback-is-heard-and-shapes-the-platform.md`
- [x] Step 2: `/new-experience` — new `design/feedback/experience.md` for the product-level feedback entry (Task Panel Footer → overlay: 1–5 rating, optional text)
- [x] Step 3: `/new-experience` (update in place) — added thumbs up/down "Feedback reaction" section to `design/market-health/data-stories.md`, plus Interactions/Edge Cases rows in `design/market-health/experience.md`
- [x] Step 4: `/new-information-architecture` (update) — added the Task Panel Footer (4th part) + Give Feedback, Feedback Panel, Feedback Reaction taxonomy terms, v2.6 → v2.7
- [x] Step 5: `/new-visual-design` (update) — Task Panel Footer, Feedback Panel, Data Story feedback reaction component specs, v1.8 → v1.9
- [x] Step 6: `/new-backend-spec` — `backend/specs/user-feedback/api.md` (created) + `backend/specs/pipeline-visibility/api.md` (updated — `GET /admin/feedback`, `GET /admin/feedback/responses`). MCP Access Review completed inline (both write endpoints + admin summary: not exposed, reasons recorded in the spec).
- [x] Step 7: `/data-surface-review` — no story surface needed (meta-data, not market data), admin visibility updated (Step 6), MCP not exposed (recorded in `ACCESS.md`), ad-hoc chat query path deliberately unreachable. See `backend/specs/user-feedback/api.md` — Data Surface Review.
- [x] Step 8: `/new-frontend-spec` — `frontend/specs/user-feedback/architecture.md`
- [x] Step 9: `/implement-backend` — `feedback_storage.py`, `feedback.py` (router), `db.py`/`main.py`/`admin_main.py` updates, two new admin templates, `test_feedback.py`. Verified import-level/route-level/template-render (no live `DATABASE_URL` in this environment — same "not run against a live Postgres" precedent as `test_mcp_access.py`/`test_scraping.py`); full existing test suite still passes.
- [x] Step 10: `/implement-frontend` — new `frontend/src/features/feedback/` (`RatingControl.tsx`, `FeedbackPanel.tsx`, `StoryFeedbackReaction.tsx`), `TaskPanel.tsx` Footer, `DataStoryMessage.tsx` single-change-point wrap. Verified: `tsc --noEmit` clean, `npm run build` clean.
- [x] Step 11: Updated `OVERVIEW.md` — new "Tell us how it's going" capability + admin feedback visibility line.

## Verification note
Neither backend nor frontend verification ran against a live Postgres or a live browser session
(no `DATABASE_URL` configured in this environment, no browser/screenshot tool available to the
implementing agents) — consistent with several prior change requests in this product's own
history. Before this ships, run the two new tables' real SQL against an actual database (the
`UNION ALL` in `list_feedback_responses()`, the `INSERT ... RETURNING` paths, `init_schema()`'s
new `CREATE TABLE` statements) and click through the real flow in a browser (Give Feedback →
submit → confirmation; thumbs down on a live Data Story → comment → submit) before calling this
fully done end-to-end.

## Decision Log
- 2026-09-23: New outcome created (bucket B — no existing outcome covered user satisfaction
  feedback). Outcome framed from the user's perspective at the user's explicit direction: "as a
  user I feel listened to and my feedback helps making this platform more useful" (not a
  PM/business-metrics framing).
- 2026-09-23: Feedback is anonymous — no login required, matching the rest of the consumer app
  (no auth on `/api/*` today). Not tied to the separate MCP/Connect-Your-AI account system.
  Confirmed with user over the alternative (attach identity when an MCP session happens to be
  logged in) as unnecessary complexity for a system most users never touch.
