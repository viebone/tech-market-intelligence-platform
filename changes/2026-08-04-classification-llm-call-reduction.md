---
id: classification-llm-call-reduction
date: 2026-08-04
trigger-type: internal
change-type: bug-fix, technical-refactor
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Cut classification LLM calls to fit the confirmed 20/day free-tier quota

## Signal
See: `research/2026-08-04-classification-llm-call-reduction.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md`

Same outcome as `changes/2026-07-27-adzuna-ingestion-resilience.md` and
`changes/2026-08-03-classification-transient-error-retry-gap.md` — market data must stay
current and continuous. The 2026-08-03 fix made the pipeline resilient to *transient*
failures, but production logs since then reveal a *structural* one: Gemini's free tier is
capped at exactly 20 requests/day/project/model (confirmed via Google's own error payload),
while real ingestion runs surface 3,000-4,700+ unique titles/day needing classification.
Demand structurally exceeds throughput, so the unclassified backlog grows every day, not
occasionally — no retry logic fixes a daily-quota ceiling. Left alone, Market Health's
trend data falls permanently further behind "actual," which directly breaks this outcome's
"they can see the trends clearly, how the hiring market numbers evolve through time."

## Change Type
`bug-fix` — the pipeline doesn't operate sustainably within a now-confirmed external
constraint, same framing as the 2026-07-27 Adzuna resilience fix. Two concrete defects
found during triage:
1. No pre-filter exists before spending an LLM call — titles that are unambiguously
   non-tech (sales, legal, finance, HR, ops roles pulled in by Greenhouse/Lever/Ashby's
   unfiltered full-board fetch) still cost a full request just to land on `"other"`.
2. `raw_postings.get_all_unclassified()` has no `ORDER BY` — when the backlog exceeds
   daily throughput (now the normal case, not an edge case), which postings actually get
   classified is effectively arbitrary rather than oldest-first.
3. `classify_postings` has no upper bound on how much it attempts — it always tries every
   unclassified title it's handed and only stops when the provider forces it to. Per the
   user's follow-up ("we just need a sample of data not everything"), Market Health needs a
   representative read on the market, not an exhaustive classification of every posting —
   so the run should deliberately cap how much it attempts per day to a number the free
   tier can actually sustain, rather than always racing the quota and calling it `"partial"`
   whenever it loses.

`technical-refactor` — no user-facing behavior or taxonomy change. A pre-filtered posting
still ends up `role_category: "other"`, the same result an LLM call would produce for an
obviously non-tech title — this only changes *how cheaply* that result is reached.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | no-change — purely backend/ops, nothing user-facing changes |
| Taxonomy Reference Spec | `design/market-health/job-classification.md` | update — Classification Method section: document the pre-filter as a second, cheaper path to the same `"other"` outcome for unambiguous cases; no change to Role Category/Seniority/Track sets or the escape hatch's meaning. Narrow technical clarification, not a taxonomy decision — safe for the backend engineer to add without reopening design judgment calls. |
| Backend Spec | `backend/specs/market-health/api.md` | update — Business Logic — Classification: (a) record the confirmed real quota (20 requests/day/project/model, replacing the uncertain "documented 20/day" framing in current code comments), (b) document the pre-filter heuristic (denylist of unambiguous non-tech keywords, chosen over an allowlist specifically to preserve recall for novel/emerging tech titles per job-classification.md's "Raw Title" intent), (c) document backlog processing order (oldest-first by `fetched_at`), (d) introduce a deliberate per-run classification budget (a fixed max batch count, set with headroom under the 20/day ceiling) and redefine `IngestionRun.status`: reaching the budget on purpose is `"success"` (the run did exactly what it was designed to do), reserving `"partial"` for when a batch fails after exhausting retries on a genuine, non-budget error |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | no-change |
| Backend Implementation | `backend/src/classification.py`, `backend/src/raw_postings.py` | update |
| Frontend Implementation | `frontend/src/` | no-change |

## Execution Plan

- [x] Step 1: Manual edit — `design/market-health/job-classification.md`, Classification
      Method section: documented that a posting is resolved either by an LLM call or by a
      cheap heuristic pre-filter for unambiguously non-tech titles, both constrained to the
      same closed sets, with which-path framed explicitly as a cost optimization, not a
      taxonomy decision.
- [x] Step 2: `/new-backend-spec` — updated `backend/specs/market-health/api.md`: added
      four new Business Logic — Classification paragraphs (confirmed 20/day quota,
      pre-classification denylist filter, oldest-first backlog ordering, per-run budget with
      redefined success/partial semantics); added `heuristic_filtered` and `budget_reached`
      fields to `IngestionRun` (Data Models) and updated the `model`/`status` field
      descriptions; updated the "Scheduled ingestion agent" section's status-writing rule to
      match; and — found while re-reading Tech Decisions — fixed a now-contradictory prior
      decision that said to upgrade Gemini billing rather than filter more aggressively,
      reversed in favor of staying on the free tier for now.
- [x] Step 3: `/implement-backend` — implemented across five files, verified with
      `py_compile`:
      - `classification.py`: added `DENYLIST_KEYWORDS` (36 curated non-tech phrases) and
        `_is_denylisted()`; novel titles are now split into denylisted (resolved straight
        to `"other"`, `model: "heuristic-keyword-filter"`, zero LLM calls) vs. LLM-bound
        before batching. Added `MAX_BATCHES_PER_RUN = 12` (headroom for up to 8 retry
        requests under the 20/day ceiling); the batch loop now checks budget before each
        attempt and sets `budget_reached=True` on a clean stop, distinct from
        `stopped_early`. `classify_postings()`'s stats dict gained `heuristic_filtered` and
        `budget_reached`; `total_classified` now sums all three paths (cache + heuristic +
        LLM). Also fixed `insert_classifications()`, which previously stamped every row
        with the global `CLASSIFICATION_MODEL` regardless of path — needed a per-row
        `model` override for the heuristic tag to actually persist (not explicitly called
        out in the spec text, but required for the provenance requirement it does state).
      - `raw_postings.py`: `get_all_unclassified()` now has `ORDER BY rp.fetched_at ASC`.
      - `db.py`: `ingestion_runs` gained `heuristic_filtered INTEGER` and `budget_reached
        BOOLEAN` via the same idempotent `ALTER TABLE ADD COLUMN IF NOT EXISTS` pattern
        used for the 2026-08-03 `raw_postings` migration (production already has rows).
      - `ingestion_runs.py`: `record_run()` accepts and inserts both new fields.
      - `ingest.py`: threads `heuristic_filtered`/`budget_reached` into `record_run()`;
        `status` logic unchanged in structure (`"partial"` iff `any_company_failed or
        stats["stopped_early"]`) — `budget_reached` was already excluded from that
        condition by construction, matching the spec's redefinition.

## Decision Log
- 2026-08-04: Tracked against `understand-market-health-before-searching`, same as the two
  prior changes in this pipeline's lineage (07-27 Adzuna resilience, 08-03 retry gap) — same
  outcome, same pipeline, escalating from transient-failure handling to structural
  throughput management.
- 2026-08-04: Classified `bug-fix` + `technical-refactor`, not `api-change` — the
  `classifications.model` field already accepts any string (no schema change needed for a
  new value), and no endpoint contract changes. No experience-spec cascade — nothing
  user-facing changes.
- 2026-08-04: Chose a denylist (block obvious non-tech keywords) over an allowlist (only
  send recognized tech keywords to the LLM) specifically because `job-classification.md`'s
  "Raw Title" section exists to catch emerging/unusual tech titles (e.g. "Founding
  Engineer," "AI Product Manager") — an allowlist would silently starve exactly the novel
  titles that section cares about, while a denylist only ever skips titles that are
  unambiguously not tech regardless of phrasing (e.g. "Account Executive," "Payroll
  Specialist," "Legal Counsel").
- 2026-08-04: Did not scope this change to reducing the curated company lists
  (`sources/greenhouse.py` / `lever.py` / `ashby.py`) — that's a separate, coarser lever
  (fewer companies = less data breadth) the user didn't ask for and that trades off against
  `outcomes/job-data-source-flexibility.md`'s intent; left as a future option if the
  pre-filter and backlog-ordering fixes together still aren't enough.
- 2026-08-04: Left the "only get new jobs" ask as already satisfied by existing behavior
  (`raw_postings.insert_new_postings` dedupes by id; `get_all_unclassified` already only
  selects postings with no classification row) rather than building anything new for it —
  confirmed by reading both functions during triage, not assumed.
- 2026-08-04: Capped the classification *budget* (how much gets sent to the LLM per run),
  not the ingestion/storage volume — raw postings stay fully stored regardless of the cap
  (storage is cheap and preserves complete provenance for any future reclassification), only
  how many of them get an LLM call this run is bounded. If fetch/storage volume itself needs
  capping later (e.g. to control database growth), that's a separate, smaller change — not
  needed to solve the LLM-quota problem this change targets.
- 2026-08-04: Chose oldest-first backlog ordering over newest-first despite newest-first
  arguably giving fresher data sooner — the outcome's own language ("how the hiring market
  numbers evolve through time") is about reliable historical continuity, and newest-first
  would let the initial-ingestion backlog (the bulk of today's unclassified volume) get
  perpetually deprioritized behind each day's new arrivals, leaving a permanent gap rather
  than one that closes over the following days.
- 2026-08-04: Redefined `"success"` to include "hit the deliberate per-run budget with zero
  errors," not just "classified everything" — under a real daily ceiling, "classified
  everything" is no longer an achievable definition of success, and conflating a
  by-design stopping point with a failure (`"partial"`) would make every future run look
  degraded when it's actually working exactly as intended.
