source: stakeholder-request
date: 2026-10-10

> "I am thinking on changing the approach and reduce the number of job post as it is becoming
> expensive, so I want to keep expanding but I thought maybe we can use an statistical approach
> and instead of capturing any single job from each source focus on just a few of similiar
> characteristics so that we don't need to process so many. what do you think, any ideas?"

Follow-up, after discussing a stratified-sampling proposal: "ok yes". On triage questions:
anchor to the spend outcome (amend it), and cap extraction at **50 postings per group**.

## Supporting evidence (read-only production queries, 2026-10-10)

- Postings ingested per month: Aug 6,269 / Sep 9,442 / Oct (to the 10th) 2,240.
- Latest classification per posting: `other` 9,497 / Engineer 6,697 / Product Manager 938 /
  Designer 434 / unknown 68. Only the three tracked roles (8,069 postings) go to requirements
  extraction.
- `posting_requirements` rows: 1,052. That leaves roughly 7,000 tracked postings unextracted.
- Requirements extraction is the volume-scaling LLM cost: one model read per posting, full
  description up to 3,000 chars, 15 per call, no cache (`backend/src/requirements.py`).
  Classification is already cheap: per unique title, cached, heuristic pre-filter, 100 titles
  per call.
- Share of tracked postings that would still be extracted under a per-group cap:

  | Grouping | Groups | Cap 30 | Cap 50 | Cap 100 | Cap 200 |
  |---|---|---|---|---|---|
  | role × specialization × level × country × month | 1,810 (avg 4.5) | 85% | 91% | 96% | 99% |
  | role × level × country × month | 484 | 42% | 51% | 63% | 76% |
  | role × specialization × month | 160 | 33% | 46% | 67% | 82% |

  Fine groups save nothing because most of them are tiny. Only coarse groups make sampling pay
  off, and the saving grows as volume grows.
- 62% of tracked postings (4,971 of 8,069) have no `country`, so country cannot be a sampling
  dimension today.
- Duplicates: 8,069 tracked postings have 6,802 distinct (company, title) pairs (about 16%
  repeats) and 7,791 distinct description hashes (about 3.5% exact repeats).
- Tracked postings by source: greenhouse 4,910 / ashby 2,594 / lever 448 / personio 80 /
  workable 37.
