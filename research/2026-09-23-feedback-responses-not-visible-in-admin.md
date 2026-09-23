source: bug
date: 2026-09-23

"I cannot see the written feedback in the admin"

Related: `changes/2026-09-23-user-feedback-mechanism.md` (the feature this bug is in).

Diagnosis (via Railway logs, not guessed): the admin service (`romantic-presence`) is running
the latest deployed commit (`c09c46d`, deploy status `SUCCESS`). The `api` service's logs show
both `POST /api/feedback/story-reaction` and `POST /api/feedback/platform-rating` returned
`201 Created` — the submissions reached the database. The admin service's own logs show the
user visited `GET /admin/feedback` (the summary page — average rating, per-story up/down
counts only; by design it never renders individual comment text) twice, but never visited
`GET /admin/feedback/responses` (the actual list of individual responses, where written
comments render via `feedback_responses.html`).

Root cause: `backend/src/admin_templates/base.html`'s sidebar nav has exactly one "Feedback"
link, pointing at the summary page. The Responses list has no nav entry at all — reachable only
via a small inline "view the full list →" text link inside the summary page's caption. Every
other admin list view (Postings, Market Observations, Skill Associations, Scraped Source Runs,
Sources & Licensing) gets its own direct sidebar nav entry, per
`design/pipeline-visibility/experience.md`'s Sidebar Nav enumeration — Feedback Responses was
never added to that enumeration when `backend/specs/pipeline-visibility/api.md` gained the two
new admin routes. This is a spec gap (the experience spec's Sidebar Nav list was never updated),
not a data-loss bug — the written feedback is very likely already in the database, just not
reachable from the nav.
