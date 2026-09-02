# Batch Processing — how the requirements backlog gets cleared

Plain-language explanation of the requirements-extraction Batch catch-up lane —
for anyone (human or AI) working on this codebase who needs to know why it
exists and how it behaves. Same intent as `AI_INTERACTION_SETTINGS.md`.

## The problem it solves

Requirements extraction (skills, education, seniority signals — see
`design/market-health/job-classification.md`) calls an LLM once per posting.
The daily cron does this **interactively**, capped at `MAX_BATCHES_PER_RUN`
batches per run — a deliberate cost cap.

New postings arrive slower than that cap, so day to day the interactive lane
keeps up. But it has no way to *catch up* once it falls behind — and it does
fall behind: a week of the LLM endpoint returning `503`s in August 2026 left a
backlog of ~1,650 postings that the daily cap would take a month to work
through.

## What the batch lane does

Every provider's batch API runs the same requests **asynchronously, at ~half
the price**, returning results within ~24h. That's a perfect fit for a
backlog: not time-sensitive, large, and cheaper in bulk. The batch lane:

1. **Collects** any finished batch job at the start of each daily run — its
   results go through the *exact same* parse/validate/insert code the
   interactive lane uses, so a batch-extracted `posting_requirements` row is
   identical to an interactively-extracted one (only the recorded `model` may
   differ).
2. Lets the **interactive lane run unchanged**.
3. **Submits one new batch job** if — and only if — the backlog is big enough
   to be worth it (`REQUIREMENTS_BATCH_MIN_BACKLOG`) and no batch job is
   already in flight. It takes up to `MAX_BATCH_POSTINGS` oldest-first,
   estimates the cost, and **refuses to submit if the estimate exceeds
   `MAX_BATCH_USD`** — at which point a human decides whether to raise the cap;
   the run does not.

A ~1,650 backlog clears in ~4 daily cycles (500 per job), then the lane goes
dormant until the next time the interactive lane falls behind.

## The mental model

> The daily run does what its cost cap allows. Whatever it couldn't reach is
> the backlog. The backlog drains through the cheaper batch lane, one job at a
> time, also under a cost cap.

Nothing new conceptually — the daily cap already existed for cost control. The
only new idea: the work the cap defers goes to batch instead of just waiting.

## Cost control

- **Per job:** the pre-submit token→USD estimate must be under `MAX_BATCH_USD`
  (~$1). One job per run, maximum.
- **Overall:** the prepaid Gemini project balance (auto-recharge OFF — see
  `DEPLOYMENT.md`) is the hard backstop for *all* LLM lanes combined. If it's
  exhausted, calls simply fail.
- The batch lane is **independent of `REQUIREMENTS_DAILY_REQUEST_BUDGET`**
  (that governs interactive request *count*, not dollars).

## "It's not idempotent" — why the ordering matters

Submitting the same batch twice creates two billable jobs. So the code
**writes the `batch_jobs` row before calling the provider's submit**, and
every run *reconciles*:

- a `batch_jobs` row stuck in `submitted` with no provider job reference =
  the submit call never completed → marked `failed`, its postings stay in the
  backlog, safe to retry (nothing was charged).
- a job still `running` far past the provider's stated turnaround
  (`BATCH_STUCK_AFTER_HOURS`) = treated as failed so it surfaces on the
  dashboard and its postings get retried, rather than blocking the lane
  forever.

## Switching to a different batch provider

The pipeline only ever imports `llm.base.BatchProvider` and the neutral
`BatchRequest` / `BatchResult` / `BatchState` types. To move the lane to, say,
OpenAI or Anthropic batch:

1. Add a `{Provider}BatchAdapter` in `llm/{provider}.py` implementing
   `BatchProvider` (three methods: `submit`, `poll`, `fetch`).
2. Register it in `llm/providers.py`'s `_BATCH_ADAPTERS`.
3. Change `_BATCH_PROVIDER` in `ingest.py` (one line).

No pipeline code changes. This is the `ai-provider-flexibility` outcome applied
to the batch capability.

## Where the numbers live

`backend/src/requirements.py`, near the top:
`REQUIREMENTS_BATCH_MIN_BACKLOG`, `MAX_BATCH_POSTINGS`, `MAX_BATCH_USD`, the
dated per-token price constants, `BATCH_STUCK_AFTER_HOURS`. Each carries a
"why this value" comment. They are tuned from real batch cost and turnaround
data — this document is not re-updated when they change.

## Watching it work

The admin dashboard's Overview shows the backlog count and current batch state
("Batch running / Last batch / Batch failed / No batch needed"). Each Ingestion
Run row shows what that run did with batch (collected / submitted / failed).
See `backend/specs/pipeline-visibility/api.md`.

## Related

- `backend/specs/market-health/api.md` — Business Logic — Requirements
  extraction — Batch catch-up lane (the full technical design)
- `changes/2026-09-01-requirements-backlog-batch-catchup.md` (the change record)
- `AI_INTERACTION_SETTINGS.md` (the chat side of this product's LLM cost story)
