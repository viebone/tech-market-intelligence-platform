source: stakeholder-request
date: 2026-09-11

See also: `outcomes/pipeline-processing-visibility.md` (the existing outcome this maps to —
operator visibility into what the pipeline has processed), `backend/specs/pipeline-visibility/api.md`
(the existing admin dashboard spec), and today's employment-events work
(`backend/EMPLOYMENT_EVENTS.md` for the full data-model history).

Raw trigger:

> "please include this new layoff events in the backend panel"

The admin pipeline-visibility dashboard (`/admin/`, `/admin/postings`, `/admin/runs`) today
only covers the job-posting pipeline (`raw_postings`/`classifications`/`ingestion_runs`). It
has no visibility into `employment_events` at all — an operator checking the dashboard has no
way to see how many employment events exist, which of the 4 adapters are actually live, or
recent ingestion activity, without querying the database directly (exactly the gap
`pipeline-processing-visibility`'s own outcome statement describes, just for a data type that
didn't exist when that outcome was written).
