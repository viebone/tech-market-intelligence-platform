source: stakeholder-request
date: 2026-10-23

Related: `research/2026-10-10-requirements-extraction-sampling.md` (sampling the paid
requirements extraction step; its CR is `changes/2026-10-10-requirements-extraction-sampling.md`).

## Raw input (owner, verbatim)

> "I am concerned about the sampling. I am getting way too many jobs, we don't need all jobs in
> the market to get an idea of what is going on. and it is increasing the cost. lets put in place
> some good sampling technique"

On being told that sampling only the paid extraction step would cover the AI cost:

> "but if I keep storing every job, my db is going to get huge right?"

On being told that growth is about 1 GB a year:

> "no I don't want to store every job, I would like to follow the sample technique"

## Owner's answers to the design questions (2026-10-23)

- **Design: sample the full job detail.** Every job keeps a short line of about 200 bytes. It is
  needed for dedupe and keeps counts, trends, pay and the ONS cross-check exact. The full original
  job-board response (about 6.4 KB, including the description) is stored only for the sample.
  Rejected: storing only the sample (bare id plus per-group counters). That would make every
  count an estimate for little extra saving.
- **Existing 20,140 jobs: going forward only.** Nothing already stored is deleted.
- **"Other" jobs (outside Engineer/PM/Designer): sample them too.** Full detail is stored for
  them, up to the cap per group, even though nothing reads it today.
- Carried over from the 2026-10-10 CR, decided 2026-10-23: **cap 50 per role × specialization ×
  month, Designer unlimited.** The current extraction backlog is left to finish.

## Production facts at the time (read-only, 2026-10-23)

- The database is 216 MB for 20,140 postings collected since 2026-08-03. `raw_postings` is
  159 MB, of which `raw_response` is 122 MB (6,365 bytes per row on average). The rest of a
  posting row is about 203 bytes.
- About 250 new postings a day. Each run fetches about 11.9k and inserts only new ids
  (`ON CONFLICT (id) DO NOTHING`).
- Growth at the current pace is about 60–95 MB a month, about 1 GB a year.
- Readers of `raw_response`: requirements extraction (description), `reclassify_unknowns.py`,
  the backfill scripts, and admin. Salary, country, company, industry and size band are already
  separate columns, filled at ingestion.
