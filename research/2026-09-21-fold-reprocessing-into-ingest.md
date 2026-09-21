---
source: user-feedback
date: 2026-09-21
---

User: "ok what would happen in the future, would we have to run it manually?" — followed by,
after the tradeoffs were laid out, "like your thinking please go ahead."

Real answer given: yes, today, by design — `reprocess_taxonomy.py`'s own docstring frames it as
deliberate one-time migration tooling, kept out of `ingest.py`'s daily flow on purpose. This is
the second taxonomy revision in six weeks (2026-08-11, 2026-09-21) to hit this same friction —
someone has to remember to re-trigger reprocessing for several days after each one.

Proposed fix: fold a "reprocess anything on a stale `taxonomy_version`" step into `ingest.py`'s
existing daily run, which already runs forever on a permanent Railway cron
(`backend/railway.json`, `0 6 * * *`). `reclassify_all()` already early-returns instantly when
nothing is stale — confirmed real (the previous revision's backlog sat untouched all day today
until manually triggered) — so this costs nothing on the ~358 days a year with no active
revision.

Two real correctness/design points, not hand-waved:
1. The daily LLM request ceiling (`outcomes/llm-spend-is-bounded-and-isolated.md`) is shared
   across `classify_postings()` and the new reprocessing step *within the same run*, not just
   across separate runs — the exact shape of gap that outcome's own signal names
   (`research/2026-08-05-cross-run-daily-budget-gap.md`, multiple same-day runs each getting a
   fresh allowance). Fixed by carrying `already_used_today + stats["llm_requests_used"]` forward
   into the reprocessing call.
2. Folding into `ingest.py` (rather than giving `reprocess_taxonomy.py` its own permanent cron)
   structurally avoids the "hundreds of empty `ingestion_runs` rows over a year" clutter concern
   raised before the user's go-ahead — there's no new row being added, just added detail on the
   row `ingest.py` already writes every day for real ingestion work.
