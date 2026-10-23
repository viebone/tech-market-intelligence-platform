---
id: storage-stays-bounded-as-sources-grow
source: business
priority: high
status: active
created: 2026-10-23
---

# Outcome: The platform's stored data grows with how varied the market is, not with how many jobs it sees, while job counts stay exact

## Signal
See: `research/2026-10-23-storage-sampling.md`

> "I am getting way too many jobs, we don't need all jobs in the market to get an idea of what
> is going on. and it is increasing the cost."
>
> "but if I keep storing every job, my db is going to get huge right?" … "no I don't want to
> store every job, I would like to follow the sample technique"

At signal time the production database was 216 MB for 20,140 postings. About 97% of each stored
posting was the full original job-board response, and the platform was adding about 250 postings
a day, more each time a source is added.

## Context
The owner keeps adding job sources (new ATS adapters, the US/EU employer panel, UK sources). Each
one adds postings, and today every posting is kept in full forever. At the current pace that is
about 1 GB a year, and the pace rises with every new source. The owner's view is that understanding
the market does not need every job in full: a well-chosen sample of each kind of job tells the
same story.

What must not be lost: the platform's job counts, trends, coverage, pay figures and the ONS
cross-check are only trustworthy because they count every job. A sample saves space by keeping
less detail, never by counting fewer jobs.

If this is ignored, storage (and the backups, restores and queries that scale with it) keeps
growing in step with sources. The owner then has to choose between adding sources and keeping
the platform small.

## Success looks like
- Every job the platform sees is still counted. Job counts, trends, coverage over time, pay
  figures and the ONS cross-check give the same numbers as if every job were stored in full.
- Full job detail is kept for at most 50 jobs per role × specialization × month, across every
  role including those outside Engineer, Product Manager and Designer. Every Designer job is kept
  in full. Groups at or under the limit are kept in full. The limits are settings that can be
  changed without code changes.
- Adding a job source that brings more of the same kinds of jobs adds almost nothing to monthly
  storage growth. Measured: in a month when jobs seen go up, the number of jobs kept in full
  stays at or under (number of groups × the limit) plus Designer jobs. Only a short record
  per job grows with volume, a small fraction of the about 6.5 KB per job stored at signal time.
- Which jobs are kept in full is repeatable. Running the same day again keeps the same jobs, and
  a job kept in full is never later reduced.
- Wherever a figure is built from the jobs kept in full rather than from every job, it says so
  where it is shown (sample size, population size, margin), consistent with
  `llm-spend-is-bounded-and-isolated`'s labelling rule.
- The operator can see, without leaving the product, how many jobs were seen and how many were
  kept in full, per run and per group.

## Out of scope
- Removing detail from jobs already stored before this outcome. The owner chose "going forward
  only"; nothing stored at signal time is deleted.
- Counting fewer jobs, or fetching fewer jobs from sources. Every job is still seen and counted.
- Sampling for AI cost reasons. That is `llm-spend-is-bounded-and-isolated`. The two share one
  sample, but this outcome is about storage.
- Database hosting choices, plan sizes or backup policy.
