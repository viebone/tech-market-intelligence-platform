---
id: taxonomy-revision-specialization-and-job-function
date: 2026-09-21
trigger-type: user-feedback
change-type: api-change
outcome: understand-market-health-before-searching
status: in-progress
---

# Change Request: Taxonomy revision — widen specialization sets + add Job Function

## Signal
See: `research/2026-09-21-taxonomy-specialization-widening.md`. Two ideas from this session,
bundled into one revision deliberately: (1) "Job Function" — a new field, populated only when
`role_category = "other"`, giving the ~52% of postings currently dead-ended in `other` a real
breakdown (Sales, Marketing, Finance, Legal, People, ...) without touching the closed 3-category
`Role Category` set at all; (2) widening the documented `specialization` closed sets for
Designer/Product Manager/Engineer, grounded in real production data rather than guessed.

**Why bundled, not sequential**: both changes touch the same LLM call
(`classification.py::classify_batch`) and this project's Gemini free-tier budget is a hard
20-requests/day ceiling (`classification.py` — `DAILY_REQUEST_BUDGET`). Running two separate
reclassification backlogs would cost twice the scarce daily quota for no real benefit — one
combined `SYSTEM_INSTRUCTION` revision and one combined backlog pass is strictly cheaper.

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — "they can identify which roles
and skills are in demand vs. declining" depends on specialization granularity being accurate;
this refines that existing outcome, no success criteria change needed.

## Change Type
`api-change` — no user-facing experience-spec change needed for the specialization-widening half
(specialization is already surfaced today, e.g. the admin Postings filter dropdown via
`get_distinct_specializations()` — this makes what's already shown more accurate, not new).
**Job Function is a genuinely new data category** (Rule 14) — its own `/data-surface-review`
(story/admin/MCP/ad-hoc-query decisions) is deliberately deferred to a follow-up change, once the
field exists and has real reclassified data to show; not resolved here, and not silently skipped
either — named explicitly as the next step.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Reference Spec | `design/market-health/job-classification.md` | update — widened specialization tables (grounded in real data), new Job Function section, revision notes for the 3 real inconsistencies found |
| Backend Spec | `backend/specs/market-health/api.md` | update — `Classification` data model gains `job_function`; `taxonomy_version` bump noted |
| Backend Implementation | `backend/src/classification.py` | update — `SYSTEM_INSTRUCTION` widened + `job_function` field + guidance fixing the 3 inconsistencies; `TAXONOMY_VERSION` bumped |
| Backend Implementation | `backend/src/db.py` | update — `ALTER TABLE classifications ADD COLUMN IF NOT EXISTS job_function TEXT` |
| Backend Implementation | `backend/src/classification.py` (insert/update) | update — INSERT/UPDATE statements gain `job_function` column |
| Admin visibility | `classification.py::get_classification_distribution`, `admin_templates/overview.html` | update — `job_function` added as a distribution dimension **and** rendered on the main `/admin/` overview page (initially computed but not wired into the template's own hardcoded dimension list — caught by the same-day audit below, not the original commit) |
| MCP Access Review | `ACCESS.md`, `backend/specs/mcp-access/api.md` | update — Job Function recorded as **deferred, not decided against** in both, same pattern as Market Benchmark before its own resolution. **Caught by a same-day audit, not the original commit** — see Decision Log. |
| Data Surface Review | — | **deferred, named explicitly** — run `/data-surface-review` once Job Function has real reclassified data, before deciding story/admin/MCP exposure |
| Everything else (IA, visual design, frontend) | — | no-change — no new tracked Role Category, no new accent colour, no new chart |

## Execution Plan

- [x] Step 1: Pulled real specialization distribution per Role Category from production, not guessed
- [x] Step 2: Identified 3 real classification inconsistencies (Technical Program Manager, Data Scientist, Engineering Manager) to fix via prompt guidance, not just document around
- [x] Step 3: Updated `job-classification.md` — widened tables + Job Function section + revision notes + 2 new anti-pattern bullets
- [x] Step 4: Updated `classification.py` — `SYSTEM_INSTRUCTION` (job_function field, widened specialization guidance, the 3 fixes), `TAXONOMY_VERSION` bumped to `2026-09-21`, `JOB_FUNCTIONS` closed set + `DENYLIST_JOB_FUNCTIONS` clusters + `_denylisted_job_function()`, `_validate()` updated, `RECOVERY_SYSTEM_INSTRUCTION` updated. Sanity-checked directly (not assumed): denylist→job_function mapping correct for 4 real sample titles, `_validate` correctly nulls `job_function` for tracked/`unknown` categories and only populates it for `other`, invalid values fall back to `"unknown"` honestly.
- [x] Step 5: Updated `db.py` schema (`ALTER TABLE classifications ADD COLUMN IF NOT EXISTS job_function TEXT`, applied live against production and confirmed via `information_schema.columns`), `insert_classifications`/`update_classifications` SQL
- [x] Step 6: Updated `backend/specs/market-health/api.md` — `Classification` data model gains `job_function`
- [x] Step 7: Updated `get_classification_distribution`'s `DISTRIBUTION_DIMENSIONS` to include `job_function`
- [x] Step 8: User confirmed ("6 days to clean the backlog is good to me"). First real batch run same day (12/58 batches, 2,956/8,189 rows). The remaining backlog no longer needs a manual re-trigger at all — `changes/2026-09-21-fold-reprocessing-into-ingest.md` folded reprocessing into `ingest.py`'s permanent daily cron, so it drains on its own going forward.
- [x] Step 9 (partial): MCP-exposure decision recorded — Job Function is **deferred, not decided against** (`ACCESS.md`, `backend/specs/mcp-access/api.md`), same treatment as Market Benchmark before its own resolution. The full `/data-surface-review` (story/admin/ad-hoc-query decisions) remains genuinely not run — that part stays open.

## Decision Log
- 2026-09-21: Bundled Job Function + specialization widening into one taxonomy revision to
  spend the scarce daily LLM budget once, not twice.
- 2026-09-21: Deliberately did not resolve Job Function's story/admin/MCP exposure in this
  change — named it as a real, explicit follow-up rather than skipping or forcing it prematurely
  before real data exists to design against.
- 2026-09-21 (second real pass, same day, before the backlog ran): user pushback
  (`research/2026-09-21-emerging-role-detection-request.md`) checked against real data rather
  than re-argued — found Content Designer/UX Writer already diverging organically (un-bundled
  in the spec to match), Delivery Manager confirmed as `other`/Job Function not Product Manager,
  and — via the first real run of `get_emerging_taxonomy_candidates()`
  (`changes/2026-09-21-emerging-role-detection.md`) — 7 more real ≥10-occurrence specialization
  gaps and a 4th inconsistency (Technical Program Manager under both Engineer and Product
  Manager) that the original manual top-25 pull had missed. All folded in before the
  reclassification backlog spent any quota.
- 2026-09-21 (caught by a same-day audit, "is all of the changes today well documented?"):
  Job Function's MCP-exposure decision had been stated in `job-classification.md` and this
  file's own body text, but never actually recorded in `ACCESS.md` or `backend/specs/
  mcp-access/api.md` — the two places Rule 12 and this project's own precedent (Market
  Benchmark's identical "deferred, not decided against" entry) require it. Fixed same-day,
  not carried forward as a known gap.
- 2026-09-21 (caught by a follow-up question, "are data stories, queries and mcp updated to
  access new data, categories and etc?"): checked concretely rather than asserted. Widened
  `specialization` values need zero code change anywhere — `market_query.py` has always
  treated it as a plain string filter (`c.specialization = ANY(%s)`), never a hardcoded list,
  and Story 1 already renders a live, ungated `GROUP BY c.specialization` ranked list — so
  today's new values surface automatically the moment real postings carry them, in the query
  layer, chat, `get_job_demand`, and Story 1 alike. `job_function` genuinely reaches none of
  the query/story/MCP surface yet (confirmed by grep — the string appears only in
  `classification.py`/`db.py`) — consistent with the deliberate deferral, not a gap. One real
  gap found and fixed: `job_function` had been added to `get_classification_distribution()`'s
  dimensions, but the main `/admin/` overview page's template hardcodes which dimensions to
  render and was never updated — computed but silently unused there until now.
