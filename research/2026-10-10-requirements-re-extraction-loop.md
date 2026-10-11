source: bug
date: 2026-10-10

Found while drafting Step 4 of `changes/2026-10-10-requirements-extraction-sampling.md`
(related signal: `research/2026-10-10-requirements-extraction-sampling.md`, where the owner reported
the pipeline "is becoming expensive").

Owner, on being told: "oh good spot, yeah lets fix the gap and then we need to make sure things
like this don't happen again"

## Observed (read-only production queries, 2026-10-10)

- `batch_jobs` 14–29 (submitted 2026-09-27 → 2026-10-08, all `collected`): 16 × 500 = 8,000
  posting slots. Across every collected job since 09-25: 9,500 slots, **1,056 distinct
  postings**.
- `posting_requirements`: 1,052 rows in total. `extracted_at` dates: 500 on 10-09, 521 on 10-08,
  and only about 30 scattered earlier rows (mostly interactive-lane writes 09-05..09-21). Every batch
  result older than 10-08 is gone.
- `ingestion_runs` 83–92: `batch_collected` = 500 every day, `total_classified` ≈ 17,000 every
  day (the whole corpus). Runs 93–94: `requirements_phase = interactive_failed`. Batch job 30
  (10-09) `failed`. Job 31 (10-10) `submitted`, 500 postings, est. $0.21.
- `est_cost_usd` per job ≈ $0.22. 16 jobs ≈ $3.5, plus jobs 14–15 and the interactive lane:
  about $4.20 estimated, almost all of it repeat work. `actual_cost_usd` is never populated, so
  real billing is unknown.
- Classifications: 17,580 on `2026-09-21`, 54 still on `2026-08-11`. 317 postings unclassified.

## Mechanism (code as of commit 643060c)

1. `ingest.run_taxonomy_reprocessing_phase()` (added by `changes/2026-09-21-fold-reprocessing-into-ingest.md`)
   calls `raw_postings.get_all_for_reclassification()`. That function returns every
   `raw_postings` row; it was written for the one-time 2026-08-11 pass.
2. `classification.reclassify_all()` then rewrites every posting from the title cache and counts
   each one in `total_classified`, so the result is always > 0.
3. That triggers `raw_postings.get_requirements_reprocess_targets(TAXONOMY_VERSION)`. It returns
   every posting with a requirements row whose classification is on the current version, which
   after the migration is all of them. `requirements.delete_requirements_for_reprocess()`
   deletes them.
4. Those postings re-enter `get_all_needing_requirements()` (oldest-first). The batch lane
   submits the oldest 500, the same 500 every day, collects them, and the next run deletes
   them again.
