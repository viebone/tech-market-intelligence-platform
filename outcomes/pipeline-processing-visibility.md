---
id: pipeline-processing-visibility
source: business
priority: medium
status: active
created: 2026-08-13
---

# Outcome: The person running the platform can see exactly what the pipeline has processed and indexed

## Signal
See: `research/2026-08-13-admin-pipeline-dashboard.md`

"I need a way to have a clear picture of the different jobs extractions that has happened,
with a summary; need to know the status of classifications, skills, etc... like a dashboard
that only me can access." Refined: "I have clearly seen the jobs that the system has
processed and indexed, with all level of detail, high level numbers to each job post if
needed."

## Context
Today the only way to know what the ingestion/classification/requirements pipeline has
actually done — how many postings were fetched, how they were classified, whether skills
extraction succeeded, which ones errored — is to query the production database directly.
That doesn't scale as changes like the classification taxonomy redesign
(`changes/2026-08-11-classification-taxonomy-redesign.md`) roll out over days via a
reprocessing backlog, and it means pipeline health and data problems can go unnoticed until
they surface as bad answers in the user-facing Market Health experience.

This is a distinct audience and need from `understand-market-health-before-searching`: that
outcome is job seekers reading aggregate market trends; this one is the person operating the
platform verifying and drilling into what the system actually did, per run and per posting.

## Success looks like
- The operator can see, at a glance, high-level counts of what the pipeline has processed and
  indexed (postings fetched, classified, skills-extracted; by run, by source, by status)
- The operator can drill down from any high-level number into the individual job postings
  behind it
- For any single job posting, the operator can see its full processing detail — raw data,
  classification result and confidence, extracted requirements/skills, which ingestion run
  touched it, and any errors encountered
- The operator can tell, without querying the database, whether a batch of postings is fully
  processed, partially processed, or failed
- Only the operator — not end users or the public — can access this view
- Using this view answers "what has the pipeline actually done" faster than writing a
  one-off SQL query would

## Out of scope
- Any end-user-facing feature — this is purely for the person operating the platform
- Editing or correcting classification/extraction results from this view (read-only
  visibility, not a data-correction tool)
- Real-time/live-updating dashboards — periodic/on-demand refresh is sufficient
- Alerting or notifications on pipeline failures (future consideration, not this outcome)
