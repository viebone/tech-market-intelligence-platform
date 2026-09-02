source: internal
date: 2026-09-01

Raw input (from a working session, after isolating chat onto the free Gemini tier
and pinning models off the throttled `gemini-flash-latest` alias):

---

User:

"but now we need to discuss the bulk option to clean the backlog. remember that
the api allows for scheduled bulk actions which are cheaper"

"can we not do a functionality that clears the backlog when it has accumulated
more than 100 jobs and then it run a batch process to clear the backlog with
some kind of limit to not go crazy. wouldn't that work better, so we have the
daily run plus a support batch for when daily run reach it limit. is that a good
idea? does it makes sense?"

---

## Facts established this session (DB, 2026-09-01)

- `raw_postings`: 6,361 — all classified, all on taxonomy_version `2026-08-11`.
  **Classification backlog: 0.**
- `posting_requirements`: 1,496 (1,380 from a one-off `claude-sonnet-5-interactive`
  backfill on 2026-08-12; the rest from Gemini).
- **Requirements-extraction backlog: 1,651** real-role postings with no
  `posting_requirements` row — Engineer 1,468, Product Manager 126, Designer 57.
- Cause of the backlog: the interactive `gemini-flash-latest` alias has returned
  persistent `503 "high demand"` / `504 DEADLINE_EXCEEDED` for ~a week across both
  Gemini projects. Cron runs 47 (key missing), 48 (66 extracted, fought 503s for
  27 min), 49 (0 extracted, 5×503/504). Pinning to `gemini-3.6-flash` (change
  `chat-free-tier-key-isolation`) fixes the interactive path but does nothing for
  the accumulated 1,651.
- Interactive daily capacity: `MAX_BATCHES_PER_RUN=12` × `BATCH_SIZE=15` ≈ 180
  postings/day. New real-role inflow ≈ 30–45/day. So once caught up, the daily
  interactive run keeps pace; it just cannot *catch up*.
- Descriptions are truncated to `MAX_DESCRIPTION_CHARS=3000` before prompting.

## Design discussed and agreed in principle

Daily interactive cron stays the primary path, unchanged. Add a self-healing
Batch catch-up:

1. Each `ingest.py` run first collects + validates + inserts the results of any
   **finished** Gemini Batch job.
2. Then the normal interactive extraction runs, unchanged.
3. Then, if `requirements backlog > THRESHOLD` (default 100) **and** no batch job
   is currently in flight: take up to `MAX_BATCH_POSTINGS` (default 500,
   oldest-first), estimate token cost, abort if over `MAX_BATCH_USD` (default
   ~$1.00), submit **one** Gemini Batch job, and record it in a new `batch_jobs`
   table **before** the submit call (Batch API is not idempotent — resubmitting
   creates a second billable job).

- `batch_jobs`: provider job name, purpose, state
  (submitted/running/collected/failed), item_count, est_cost_usd, submitted_at,
  completed_at. In-flight guard = at most one row in (submitted, running).
- New Gemini Batch adapter in `llm/` (submit JSONL, poll state, retrieve
  results), reusing `requirements.py`'s existing prompt-build / `_parse` /
  `_validate` / `insert_requirements` path (~90% shared).
- Latency ~24h, so a submitted job's results land on the next day's run. A
  1,651 backlog clears over ~3–4 daily cycles at 500/job, then goes dormant.
- Cost cap is self-contained (pre-submit estimate + `MAX_BATCH_USD` + the $5
  prepay backstop), so this does **not** depend on the spend-ledger follow-on CR.

## Why this over the alternatives

- vs. raising the interactive daily budget: forbidden until the spend-ledger CR,
  and still fights the same interactive congestion.
- vs. a one-off throwaway backfill script: the automated trigger shares ~90% of
  the code and additionally covers every *future* accumulation (daily run down
  for days, a prompt change, a taxonomy v3 reprocess).

Related: `research/2026-08-29-llm-cost-governance.md` (same session's cost-governance
work), `changes/2026-08-29-chat-free-tier-key-isolation.md` (the model pins this
builds on), `changes/2026-08-09-skills-and-industry-signal.md` (requirements
extraction's original design and its per-posting cost concern).
