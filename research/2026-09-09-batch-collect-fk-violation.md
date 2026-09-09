---
source: bug
date: 2026-09-09
---

Stakeholder: "the batches are failing, why?"

The requirements batch catch-up lane's collect step has failed on every run since
2026-09-06 (runs 54, 55, 56 → `requirements_phase: batch_collect_failed`). Job 4 sat
`submitted` for 4 days until `reconcile()` force-failed it at +72h on run 57 (09-09), dumping
its 500 postings to `posting_requirements_failures`. Run 57 then submitted job 5, which would
have hit the same wall on run 58.

## Root cause (from Railway job-sync logs, run 56, 2026-09-08 06:05)

```
ERROR:__main__:requirements batch collect failed: insert or update on table
"posting_requirements" violates foreign key constraint "posting_requirements_posting_id_fkey"
  File "/app/src/ingest.py", line 133, in run_requirements_phase
    collected = reqs.collect_batch_results(batch_results, postings, active["model"])
  File "/app/src/requirements.py", line 792, in collect_batch_results
    insert_requirements(entries, model=model)
psycopg.errors.ForeignKeyViolation
```

`collect_batch_results` builds `entries` from `parse_and_validate(model output)`.
`parse_and_validate` keeps an entry for **any** `id` the model echoes back, even one not in
the job's real posting set — and `_validate` just passes it an empty valid-skills list rather
than dropping it. `insert_requirements` then does one `executemany` insert; a single row
whose `posting_id` has no `raw_postings` FK aborts the **entire** transaction → the whole
collect fails, nothing is saved, the job stays active, and it repeats every day until the 72h
reconcile.

A stray id gets in two ways, both real: (1) the model occasionally emits a malformed/invented
id in its JSON (job 4 had exactly 1 of 500); (2) a batch that sits for days can name a
posting pruned from `raw_postings` since submission.

`poll()`, `fetch()`, `prep_postings()`, `parse_and_validate()` all work fine — verified by
running the full collect for job 4 and job 5 by hand. The failure is only the final insert.

## Immediate state (fixed by hand 2026-09-09)

- Collected job 4 (499 rows) and job 5 (500 rows) manually with the fixed code; both marked
  `collected`. `insert_requirements` auto-cleared their `posting_requirements_failures` rows.
- Tracked-role backlog: ~1,597 (CR start) → 652 (this morning) → **152**.
- Failures table: 474 → 1.
