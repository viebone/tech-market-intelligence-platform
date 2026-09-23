---
id: feedback-responses-not-visible-in-admin
date: 2026-09-23
trigger-type: bug
change-type: bug-fix
outcome: user-feedback-is-heard-and-shapes-the-platform
status: complete
---

# Change Request: Feedback Responses has no sidebar nav entry — written comments unreachable

## Signal
See: `research/2026-09-23-feedback-responses-not-visible-in-admin.md`

## Outcome
See: `outcomes/user-feedback-is-heard-and-shapes-the-platform.md` — "the team can read every
individual response — its rating or reaction, its written comment if any, and when it was
given." Not violated in principle (the page exists and works), but unreachable in practice.

## Change Type
bug-fix

## Root Cause
`design/pipeline-visibility/experience.md`'s Sidebar Nav enumeration was never updated to
include the Feedback Responses view when `backend/specs/pipeline-visibility/api.md` gained
`GET /admin/feedback/responses` (`changes/2026-09-23-user-feedback-mechanism.md`). Every other
admin list view gets its own direct sidebar entry per that enumeration; this one didn't, because
the spec never named it. **Spec is incorrect/incomplete — fix the spec first, then the
implementation**, per the bug-fix flow.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/user-feedback-is-heard-and-shapes-the-platform.md` | no-change |
| Experience Spec | `design/pipeline-visibility/experience.md` | update — add "Feedback Responses" to the Sidebar Nav enumeration |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | no-change (routes already correct; this is a nav-wiring gap only) |
| Backend Implementation | `backend/src/admin_templates/base.html` | update — add a second sidebar nav link |
| Plain-Language Overview | `OVERVIEW.md` | no-change (bug-fix, no new capability — the capability already exists) |

## Execution Plan

- [x] Step 1: Updated `design/pipeline-visibility/experience.md`'s Sidebar Nav enumeration to
      name "Feedback Responses" alongside "Feedback" (also corrected a pre-existing separate
      omission found while here: "Taxonomy Health" was live since 2026-09-21 but never listed
      in this enumeration either — added for accuracy, not itself a behavior change)
- [x] Step 2: Added a second sidebar nav link in `backend/src/admin_templates/base.html`
      ("Feedback Responses" → `/admin/feedback/responses`) and gave that route its own
      `active_page: "feedback_responses"` in `admin_main.py` (previously shared `"feedback"`
      with the summary page, so the new nav link would never have highlighted as active)
- [x] Step 3: Verified — `admin_main.py` parses clean; rendered `feedback_responses.html`
      directly via Jinja2 with `active_page="feedback_responses"` and confirmed both "Feedback
      Responses" text and the `class="active"` highlight are present in the output. No live DB
      in this environment, so the actual data behind the page (whether the two real production
      submissions' comments render) is not independently re-verified here — only the nav fix
      itself.
- [x] Step 4: Commit and push

## Decision Log
- 2026-09-23: Diagnosed via Railway logs rather than assumption — confirmed both feedback
  endpoints returned 201 in production, and confirmed the admin service only ever received
  requests for the summary page, never the responses page. This is a discoverability/nav bug,
  not a data-loss bug — no evidence the written comment itself failed to store.
