---
id: periodic-source-ingestion-in-job-sync
date: 2026-09-25
trigger-type: stakeholder-request
change-type: technical-refactor
outcome: production-deploy-readiness
status: complete
---

# Change Request: Run the ONS and IT Jobs Watch ingestions from the existing daily job-sync cron, each isolated

## Signal
See: `research/2026-09-25-scheduling-periodic-source-ingestions.md`

## Outcome
`outcomes/production-deploy-readiness.md` — a live source that nothing runs is not "working for real users". Bucket A; no outcome
change. (Adjacent: `outcomes/job-data-source-flexibility.md`, `outcomes/pipeline-processing-visibility.md` for the admin warning.)

## Change Type
`technical-refactor` (scheduling/operations; no new user-visible capability). One small operator-visible addition (an "overdue" warning
on an existing admin page) — no experience-spec change needed; recorded in the admin spec.

## What changes (PM decisions, 2026-09-25: **Option A, IT Jobs Watch included, one failing must never bother the others**)

1. **`ingest_periodic.py` — a small runner** that executes each periodic source's own ingestion script **as a separate child process**
   with its own hard timeout: (a) `ingest_trusted_statistics.py` (ONS), (b) `ingest_scraped_sources.py` (IT Jobs Watch). A step that
   exits non-zero, crashes, hangs (killed at its timeout), or is misconfigured **cannot** affect the other step or `job-sync`. Every step
   still enforces its own cadence gate in code, so running the runner daily is safe — a step that is not due makes no request.
2. **`ingest.py` calls the runner after its own work, in a `finally`** — job postings are the time-sensitive, cost-sensitive job and
   keep priority; the periodic step still gets its attempt even if the postings run raised; and the call is itself guarded so nothing it
   does can propagate. (Employment events keep their own service — unchanged.)
3. **A 2-day settle rule for ONS**: `release_settle_days = 2` on the publisher; a release is ingested only once its release date is at least
   2 days old ("in case there are issues on their side"). Enforced in code, so cron timing is irrelevant.
4. **Cadence gate for a daily cron**: ONS `min_check_interval_hours` 24 → **20**. A daily cron starts a few minutes either side of the same
   time; an exact-24h gate would randomly skip a day when a run starts seconds early. (IT Jobs Watch's 7-day permission-conditioned gate
   is deliberately **not** changed; consequence — it will drift to about every 8 days under a daily cron, which respects "at most weekly".)
5. **An "overdue" warning** on the admin Statistics Sources page: no new release ingested for more than 45 days (the normal maximum gap
   is 35; two 63-day gaps exist in 129 releases).
6. **Documentation**: `DEPLOYMENT.md` (job-sync now runs the periodic step; env vars; the stale employment-events claim corrected; the
   separate `trusted-statistics` service section replaced), `DATA_SOURCES.md`, `backend/TRUSTED_STATISTICS.md`, the trusted-statistics spec.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome / Foundations / IA / Visual / Experience / Frontend | — | no-change |
| Backend Spec | `backend/specs/trusted-statistics/api.md` (cadence, settle rule, scheduling) | update |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` (`GET /admin/statistics-sources`: settle days, overdue) | update |
| Backend Implementation | `ingest_periodic.py` (new), `ingest.py`, `trusted_stats/{registry,base}.py`, `statistics_storage.py`, admin template, tests | update |
| Docs | `DEPLOYMENT.md`, `DATA_SOURCES.md`, `backend/TRUSTED_STATISTICS.md`, `.env.example`, `backend/railway.trusted-statistics.json` (delete — no separate service) | update |
| Plain-Language Overview | `OVERVIEW.md` | no-change (nothing a user notices) |
| MCP Access Review / Polite Scraping Review / Data Surface Review | — | not-applicable (no new capability, no new source, no new data category); the existing cadence/politeness constraints are unchanged and re-checked (below) |

## Polite-scraping re-check (Rule 13 constraint 1 — enforced cadence)
Running the IT Jobs Watch script daily must not increase its load: `scraping_storage.is_due()` (7 days) is enforced **before** the adapter
is constructed, so a not-due run makes no request. Verified by the existing `test_scraping.py` cadence tests plus a new runner test.

## Execution Plan
- [x] ✅ Step 1: `ingest_periodic.py` + tests (isolation: failure, crash, hang/timeout, misconfigured, unlaunchable script) — `test_periodic_sources.py`, 14 tests with real child processes
- [x] ✅ Step 2: hook into `ingest.py` (after the work, in a `finally`, guarded)
- [x] ✅ Step 3: settle rule + cadence 20h + overdue warning, with tests
- [x] ✅ Step 4: documentation (list above) + spec updates
- [x] ✅ Step 5: verify locally (dry run; the real ONS step live as a gate-skip; **not** a real IT Jobs Watch scrape — it will run at the first deployed daily run once contacts are set)
- [x] ✅ Step 6: commit and deploy — **needs the operator's `STATISTICS_CONTACT` and `SCRAPER_CONTACT` values set on the Railway `job-sync` service first** (the runner skips a misconfigured step loudly until then)

## Decision Log
- 2026-09-25: PM chose Option A (run inside `job-sync`'s daily cron) over a new Railway service, with IT Jobs Watch included.
- 2026-09-25: Child-process isolation chosen over in-process try/except: it also survives a crash, a hard exit, a memory blow-up, and — via a
  timeout — a hung network call, which try/except cannot.
- 2026-09-25: Periodic steps run **after** job postings in a `finally`, not before: postings keep priority, and a hung periodic step (bounded
  by its timeout) can never delay them.
- 2026-09-25: Verified locally: `test_trusted_stats.py` 55, `test_periodic_sources.py` 14, `test_scraping.py` 37, `test_source_licences.py` 4,
  `test_employer_headcount.py` 14 — all pass. `ingest_periodic.py --dry-run` with no contacts reports both steps loudly; `--only trusted_statistics`
  ran the real ONS step against production (gate held: "checked within the last 20h — skipped, no request made", exit 0). Admin data and template
  render with the new fields (`overdue` false, 10 days since release). A real IT Jobs Watch scrape was deliberately **not** run locally.
- 2026-09-25: A regression the new settle rule caused in an existing test (a release dated in the test's future) was fixed by moving the test clock,
  not by weakening the rule. `backend/railway.trusted-statistics.json` (never connected to a service) deleted.
- 2026-09-25: Corrected stale docs found on the way: `DEPLOYMENT.md` and `DATA_SOURCES.md` described `employment-events` as "not yet deployed", daily;
  the committed config says weekly (Mondays) and the service is connected.
- 2026-09-25: PM supplied the contact (`viebone.com info@viebone.com`, explicitly authorised for User-Agent use) and asked for commit + push. Set on Railway
  `job-sync` as `STATISTICS_CONTACT` and `SCRAPER_CONTACT` (variables only; deploy came from the push). Both pass the placeholder check.
