---
id: adzuna-ingestion-resilience
date: 2026-07-27
trigger-type: bug
change-type: bug-fix, technical-refactor
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Make daily ingestion resilient to Adzuna API failures

## Signal
See: `research/2026-07-27-adzuna-ingestion-resilience.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md`

This outcome depends on the market data actually being current and continuous
("they can see the trends clearly, how the hiring market numbers evolve through
time"). A daily pipeline that crashes on the first transient upstream error it
meets breaks that continuity by design, not by bad luck — Adzuna having an
off day is a "when," not an "if," at daily cadence. No change to the outcome's
scope or success criteria; this is about the pipeline actually delivering what
the outcome already requires.

## Change Type
`bug-fix` — the fetch step doesn't live up to a resilience pattern the backend
spec already assumes exists: `IngestionRun.status`'s `"partial"` value is
documented as "completed but stopped early (e.g. hit an unresolvable rate
limit)," and `classification.py` already implements exactly that
(`stopped_early`, per-batch persistence, graceful stop on exhausted retries) —
but `adzuna_client.py`/`ingest.py`'s fetch step has no equivalent, so a single
bad term crashes the whole run instead of degrading to `"partial"`.
`technical-refactor` — no user-facing behavior changes; this is entirely
ops-facing pipeline hardening.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | no-change — purely backend/ops resilience, nothing user-facing changes |
| Backend Spec | `backend/specs/market-health/api.md` | update — extend the ingestion Business Logic section to document per-term fault isolation, empty-result handling, and Adzuna rate-limit pacing/backoff, so the fetch step's resilience is spec'd the same way classification's already is |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | no-change |
| Backend Implementation | `backend/src/ingest.py`, `backend/src/adzuna_client.py` | update |
| Frontend Implementation | `frontend/src/` | no-change |

## Execution Plan

- [x] Step 1: Update `backend/specs/market-health/api.md` — Business Logic section:
      documented (a) per-search-term fault isolation, (b) empty results as a normal
      outcome, (c) Adzuna's actual documented quota (25/min, 250/day, 1000/week,
      2500/month, confirmed via their Terms of Service — not assumed) and the pacing
      policy that follows from it, (d) redefined `status: "partial"` to cover
      degraded fetch runs, reserving `"failed"` for a run that produced nothing
      usable at all. Also updated `IngestionRun.terms_processed` to carry a
      per-term `error` field, and the External Dependencies table with the quota
      numbers.
- [x] Step 2: `/implement-backend` — implemented against the updated spec.
      `backend/src/adzuna_client.py`: added `AdzunaFetchError`, `_pace()` (3s
      minimum interval between requests, called from the one place all Adzuna
      HTTP calls go through, so it covers both pagination-within-term and
      term-to-term transitions), and `_get_with_retry()` (retries HTTP 429/5xx
      and connection errors/timeouts up to 3 attempts with 2s/4s/8s backoff;
      non-429 4xx fails immediately, no retry). `backend/src/ingest.py`:
      `ingest_search_term` now catches `AdzunaFetchError` and returns
      `{term, fetched: 0, inserted: 0, error: str}` instead of raising;
      `terms_processed` entries now always carry an `error` field
      (`None` on success); `run()`'s status logic sets `"partial"` when any
      term failed or classification stopped early, reserving `"failed"` for
      the outer try/except (unexpected failures outside per-term isolation,
      e.g. the database itself). Verified both files compile (`py_compile`
      via the project's WSL venv). Not re-tested live against a real Adzuna
      503 (would require forcing that condition); confirmed by code review
      against the exact failure captured in the 2026-07-27 crash logs.

## Decision Log
- 2026-07-27: Tracked against `understand-market-health-before-searching` only
  (not `ai-reasoning-transparency`) — this is pipeline reliability, not a
  reasoning/transparency concern; the closest precedent is the 2026-07-22
  change, which tracked the same ingestion pipeline's scheduling work against
  this same outcome.
- 2026-07-27: Classified `bug-fix` + `technical-refactor`, not `api-change` —
  nothing about the endpoint contracts or data models changes, only the
  fetch step's internal fault-handling. No experience-spec cascade needed
  since nothing user-facing is affected.
- 2026-07-27: Deliberately scoped the backend-spec update to precede
  implementation rather than skipping straight to code — the spec already
  makes an implicit promise (`"partial"` status exists for exactly this kind
  of scenario) that the fetch step currently breaks; formalizing what
  "resilient" means (which errors get retried, how many times, what still
  counts as a failed run) avoids re-litigating those decisions ad hoc while
  writing the fix.
- 2026-07-27: Confirmed Adzuna's actual rate limit before writing anything
  into the spec, rather than assuming a number — their Terms of Service
  documents 25 hits/minute, 250/day, 1000/week, 2500/month (free tier).
  Chose a 3-second minimum interval between requests (20/min sustained,
  a safety margin under the 25/min cap) enforced at the single point all
  Adzuna HTTP calls pass through, so it applies uniformly to pagination and
  term-to-term transitions without every call site needing to remember to
  pace itself. Also extended retryable failures beyond just HTTP 429/5xx to
  include connection errors and timeouts (`httpx.TransportError`) — not
  explicitly named in the original bug report, but the same class of
  transient failure the user's "control all different scenarios" framing
  was asking for, and the existing code had zero protection against either.
- 2026-07-27: Exact retry/backoff numbers (3 attempts, 2s/4s/8s) and the
  pacing interval are implementation constants, not spec'd exactly — kept
  the spec at the level of policy (what's retryable, that pacing exists,
  the real Adzuna quota) and left precise tuning to code, matching how
  `classification.py`'s existing rate-limit handling is already documented
  in this codebase (numbers live in code comments, not in `api.md`).
