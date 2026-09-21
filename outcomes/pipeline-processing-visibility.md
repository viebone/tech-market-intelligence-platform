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

**Extended 2026-09-11** (`changes/2026-09-11-employment-events-admin-visibility.md`): the
platform now runs a second, independent ingestion pipeline — employment events (layoffs,
closures, restructuring, bankruptcy, offshoring, expansion, hiring announcements; see
`backend/EMPLOYMENT_EVENTS.md`). The same operator need applies to it: seeing what's been
ingested, from which sources, without querying the database directly. This outcome now covers
both pipelines, read independently — visibility into one is not evidence about the other,
matching the pipelines' own data independence
(`changes/2026-09-11-employment-events-no-company-matching.md`).

**Extended 2026-09-16** (`changes/2026-09-16-admin-licensing-visibility.md`): a third pipeline —
scraped market benchmark sources (`backend/specs/scraped-data-sources/api.md`) — introduced its
own real, source-specific licence question (see `LICENSING.md`): is a source's licence
confirmed, does it permit commercial use, and under what exact attribution terms may this
platform use its data. The same operator need applies again: seeing that status without reading
code or a markdown file directly, the same "don't make me query/grep for it" pattern this
outcome already serves for postings, runs, and employment events.

**Extended 2026-09-18** (`changes/2026-09-18-admin-market-benchmark-visibility.md`): now that
real `market_observations`/`skill_associations` data exists (via the LLM-extraction rebuild,
`changes/2026-09-18-itjobswatch-llm-extraction.md`), the same operator need applies to the data
itself, not just its licence: seeing what's actually been captured (per role, per skill, per
period) and when each scraped source last ran, without querying the database directly.

**Extended 2026-09-21** (`changes/2026-09-21-emerging-role-detection.md`): the classification
taxonomy revision that added Job Function and widened specialization sets
(`changes/2026-09-21-taxonomy-revision-specialization-and-job-function.md`) surfaced a new,
recurring operator need distinct from the ones above: not "what has the pipeline processed" but
"what does the pipeline keep seeing that the taxonomy doesn't have a real category for yet."
Left as an ad hoc manual query, this drifts the same way `OVERVIEW.md` or `ACCESS.md` would
without their own mandatory-update rules — real recurring roles pile up under `other` or a
mismatched specialization, unnoticed, until someone happens to look. The same operator need
this outcome already serves for pipeline health applies here too: seeing this without writing a
one-off SQL query, on a real repeatable cadence rather than remembering to check.

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
- The operator can see, at a glance, how many employment events exist per source, per
  direction (contraction/expansion), and when each source last ingested — and drill into any
  single event's full stored record
- The operator can see, at a glance, every registered scraped source's licence status —
  confirmed or not, commercial-use permitted or not, the exact attribution text, and a link to
  the licence itself — without opening `LICENSING.md` or reading code (added 2026-09-16)
- The operator can see the market-benchmark data a scraped source has actually captured — every
  observation (role/skill, period, rank, vacancy count/share, salary distribution) and every
  weighted skill association — filterable by source and entity, and drill into any single row's
  full provenance (source URL, licence, fetch time, which model extracted it). The operator can
  also see, per registered scraped source, when it last ran and whether it's currently due for
  its next run (added 2026-09-18)
- The operator can see, on a real repeatable cadence (not a one-off manual query), which
  specialization values are recurring under a tracked Role Category but aren't yet in the
  documented taxonomy, which real titles are piling up under Job Function's "Other Non-Tech"
  catch-all, and the current `unknown` rate — real signal for the next taxonomy revision,
  never auto-applied (added 2026-09-21)
- Only the operator — not end users or the public — can access this view
- Using this view answers "what has the pipeline actually done" faster than writing a
  one-off SQL query would

## Out of scope
- Any end-user-facing feature — this is purely for the person operating the platform
- Editing or correcting classification/extraction results from this view (read-only
  visibility, not a data-correction tool)
- Real-time/live-updating dashboards — periodic/on-demand refresh is sufficient
- Alerting or notifications on pipeline failures (future consideration, not this outcome)
