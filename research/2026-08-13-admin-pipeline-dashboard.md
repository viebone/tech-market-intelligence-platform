---
source: stakeholder-request
date: 2026-08-13
---

Raw request (product owner, in conversation):

> ok, I need a way to have a clear picture of the different jobs extractions that has
> happened, with a summary; need to know the status of classifications, skills, etc...
> like a dashboard that only me can access. what do you suggest

## Context gathered during the conversation

The stakeholder wants operator-facing visibility into the job data pipeline that today can
only be inspected by querying the database directly:

- Ingestion runs — what happened per run (sources/companies fetched/inserted, errors, budget
  usage), sourced from the existing `ingestion_runs` table.
- Classification status — distribution of `role_category` / `level` / `track` /
  `specialization` / `classification_confidence`, `unknown` counts, and `taxonomy_version`
  breakdown (topical right now: `changes/2026-08-11-classification-taxonomy-redesign.md` is
  still draining a reprocessing backlog — 2,143 of 5,105 postings reclassified as of the last
  run, ~2,962 remaining).
- Skills/requirements extraction status — coverage % (postings with requirements extracted vs.
  total), `skill_group` distribution, extraction failures.

Explicitly operator-only ("only me can access"), not part of the existing consumer-facing
Market Health experience aimed at UX/tech job seekers — this is a different audience
(the product owner running the pipeline) with a different need (trust/debug the pipeline)
than the existing `understand-market-health-before-searching` outcome (job seekers assessing
the market).

Access-control mechanism was explicitly left open by the stakeholder — asked to be raised as
an open question for whichever spec layer owns it, rather than decided here. Noted during the
conversation: the product's backend spec already documents "No auth middleware in v1. Add it
as a separate layer when needed" (`backend/specs/market-health/api.md`), and this product's
own `CLAUDE.md` tech stack section names `JWT` as the intended auth mechanism, though nothing
using it exists yet — both are relevant inputs for whoever designs this, not decisions made
here.
