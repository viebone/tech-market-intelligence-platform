---
id: requirements-extraction-sampling
date: 2026-10-10
trigger-type: stakeholder-request
change-type: api-change, ux-change
outcome: llm-spend-is-bounded-and-isolated
status: in-progress
---

# Change Request: Sample requirements extraction per group so its cost stops growing with posting volume

## Signal
See: `research/2026-10-10-requirements-extraction-sampling.md`

## Outcome
See: `outcomes/llm-spend-is-bounded-and-isolated.md` (amended as Step 1 below).
The quality bar for what users see still comes from
`outcomes/understand-market-health-before-searching.md` ("identify which roles and skills are in
demand"). This change must not weaken that bar. It changes skill figures from full counts to
honestly labelled estimates.

## Change Type
- `api-change`: requirements extraction becomes sampled and weighted; every requirements query
  returns weighted estimates with their sample size.
- `ux-change`: every skills/requirements surface states that its figure is an estimate (n of N,
  ± margin) and suppresses or flags low-n cells.

## Scope: what changes and what explicitly does not

**Unchanged.** Ingestion of every posting from every source. Classification of every posting.
Every count-based surface: volumes, trends, coverage, year on year, ONS cross-check, pay. These
need the full population, and their LLM cost is already small (per-title cache, heuristic
filter, 100 titles per call).

**Changed. Requirements extraction only** (`requirements.py`, both the interactive and the
batch lane):
1. **Duplicate reuse.** A posting whose (company, normalised title, description fingerprint)
   matches an already-extracted posting copies that extraction instead of making a model call.
   Expect about 3.5% to 16% fewer calls.
2. **Capped sampling per group.** The group is role_category × specialization × month (by
   ingestion month). Each group gets up to **50** extracted postings. Groups at or under 50 are
   extracted in full. Postings are chosen by a deterministic hash of the posting id, so the
   choice is repeatable and needs no stored state. A posting already extracted is never thrown
   away. Postings that are not chosen are recorded as `not_sampled`, which is distinct from
   "pending" and from "failed".
3. **Weights.** Each extracted posting carries a weight: group size ÷ number extracted in that
   group. Every skills/requirements aggregate (`market_query.query_requirements_data`,
   `market_stories`, `curated_answers`, chat tools, MCP tools) uses weighted shares and returns
   `sample_n`, `population_n` and a margin of error alongside the estimate.
4. **Honest labelling (Rule 10).** Every surface showing a requirements figure says it is an
   estimate. For example: "Estimated from 50 of 712 postings, ±14 pts". Below a minimum sample
   size (set in the experience spec), the figure is suppressed or clearly flagged as
   low-confidence, never shown as if it were solid.

**Effect, using today's data.** At a cap of 50, about 46% of tracked postings would still be
extracted, about 54% fewer calls. More importantly, extraction becomes bounded by
(groups × 50) per month rather than growing with every new source. That bound is what lets the
owner keep expanding.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/llm-spend-is-bounded-and-isolated.md` | update. Add a success criterion: extraction cost stays bounded as posting volume grows. Narrow the out-of-scope "reducing coverage" line so honest-estimate sampling is allowed. |
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change (quality bar still applies, referenced above) |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | review. It mentions the requirements signal; update only if wording implies full coverage. |
| Visual Design | `design/visual-design.md` | no-change (estimate labelling reuses existing subtitle/caption tokens; revisit if a new "low-confidence" treatment is needed) |
| Experience Spec | `design/market-health/experience.md`, `design/market-health/data-stories.md`, `design/market-health/job-classification.md` (Requirements Taxonomy section) | update |
| Backend Spec | `backend/specs/market-health/api.md` | update. Sampling, duplicate reuse, weights, `not_sampled` state, weighted query contract. |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | update. The admin backlog metric must exclude `not_sampled`. Show sampled / not-sampled / reused counts per run. |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update. Estimate captions, low-n suppression, consume `sample_n` / `population_n` / margin. |
| Backend Implementation | `backend/src/` | update (`requirements.py`, `ingest.py`, `batch_jobs.py`, `market_query.py`, `market_stories.py`, `curated_answers.py`, `chat.py` prompts, `mcp_access/tools.py`, `db.py`, admin dashboard) |
| Frontend Implementation | `frontend/src/` | update |
| Plain-Language Overview | `OVERVIEW.md` | update. Skill figures are estimates from a sample per role/specialization/month. |
| MCP Access Review | `ACCESS.md` + `backend/specs/mcp-access/api.md` | update. MCP tools return requirements data, and their response shape gains estimate fields. Runs inside `/new-backend-spec`. |
| Polite Scraping Review | `DATA_SOURCES.md` | not-applicable. No scraped source is added or changed; ingestion is untouched. |
| Data Surface Review | stories / admin / ad-hoc query layer | no-change as a review. No new data category: sampling metadata describes the existing requirements data. The admin and query-layer updates are already in the backend spec rows above. |

## Execution Plan

- [x] ✅ Step 1: Amend `outcomes/llm-spend-is-bounded-and-isolated.md` (manual PM edit). Add the
      "bounded as volume grows" criterion and narrow the out-of-scope coverage line, citing this CR.
- [x] ✅ Step 2: `/new-experience`. Revise `design/market-health/experience.md`, `data-stories.md`
      and `job-classification.md` in place: estimate labelling, minimum sample size, low-n
      behaviour, wording for chat/curated answers. Run `/data-legibility` and `/end-user-content`
      on the new captions.
- [x] ✅ Step 3: Review `design/information-architecture.md` for full-coverage wording (edit only if
      needed).
- [ ] Step 4: `/new-backend-spec`. Update `backend/specs/market-health/api.md` (sampling,
      duplicate reuse, weights, `not_sampled`, weighted query contract) and
      `backend/specs/pipeline-visibility/api.md` (backlog definition, per-run sampling counts).
      Settle the open design questions in the Decision Log. `/mcp-access-review` runs inside this
      step.
- [ ] Step 5: `/new-frontend-spec`. Update `frontend/specs/market-health/architecture.md`.
- [ ] Step 6: `/implement-backend`. Back up the requirements tables before any backfill or
      reprocessing script runs.
- [ ] Step 7: `/implement-frontend`.
- [ ] Step 8: Update `OVERVIEW.md`.
- [ ] Step 9: Verify in production: run one cron and compare its extraction call count with the
      previous run. Confirm the backlog shown in admin drops to sampled-only. Spot-check that
      one weighted skill share falls within its stated margin of the share from the 1,052
      already-extracted postings.

## Decision Log
- 2026-10-10: **Sample extraction, never ingestion or classification.** Count-based surfaces need
  the full population, and classification is already cheap per title. Narrowing ingestion to
  postings with "similar characteristics" would bias every trend and break the coverage and ONS
  comparisons.
- 2026-10-10: **Anchored to `llm-spend-is-bounded-and-isolated`, amended.** The owner chose this
  over a new outcome. That outcome's out-of-scope line ("reducing coverage to save money")
  conflicted, so it is amended in Step 1 rather than ignored.
- 2026-10-10: **Groups are role × specialization × month.** Data showed fine groups
  (+level +country) average 4.5 postings, so a cap of 50 still extracts 91%. Country is also
  null for 62% of tracked postings. Level and country stay available as breakdowns at query
  time, weighted, but are not sampling dimensions.
- 2026-10-10: **Cap = 50 per group** (owner's choice over 100). Worst-case margin is about
  ±14 pts at 95%, less with the finite-population correction on smaller groups. Accepted
  knowingly: niche specializations are mostly under 50 and stay fully extracted anyway.
- Open, for Step 4 (backend spec):
  - **How selection behaves while a month fills.** Pure lowest-hash-50 can displace postings
    already extracted. Proposal: "hash below a threshold, never un-extract", which may slightly
    overshoot 50.
  - **The existing ~7,000 backlog.** Proposal: apply the same sampling retroactively, keep every
    posting already extracted, and mark the rest `not_sampled`.
  - **Matching key for duplicate reuse.** Exact description hash is safe. Company + title alone
    may merge genuinely different postings, such as the same title at different levels.
  - **How weights interact with level/country breakdowns at query time.** Small cells need the
    low-n rule from Step 2.
- 2026-10-10: **Per-role caps (proposed default, owner asked "should we sample more on UX/PM/Eng?").**
  Only Engineer, Product Manager and Designer are ever extracted. `other`/`unknown` postings cost
  classification only: 6,873 went through the model, 2,616 were filtered by keywords for free, at
  100 titles per call with a title cache, so a few dozen calls in total. Sampling them saves
  nothing, and they are needed for full-market counts. Effect of a uniform cap of 50 on today's
  data: Engineer 6,697 → 44% extracted, PM 938 → 49%, Designer 434 → 78%. Proposal: **Designer
  uncapped** (the core audience per `understand-market-health-before-searching`; only about 94
  extra postings), **PM and Engineer capped at 50**, with caps configured per role so they can be
  tuned without code changes. To confirm in Step 4.
- 2026-10-10: ✅ Step 1 done. The outcome gains two success criteria ("bounded as volume grows",
  "estimates always labelled"). The out-of-scope coverage line is narrowed so it still protects
  ingestion and classification but allows labelled sampling of requirements extraction.
- 2026-10-10: ✅ Step 2 done.
  - **`design/market-health/experience.md`:**
    - New **Requirements estimates** section: what is and isn't sampled, the terms n / N /
      margin, thresholds, wording per surface, and breakdowns finer than the sample.
    - Thresholds: n = N shows "Based on all N". n ≥ 30 shows an estimate with ± margin.
      10–29 is marked "small sample, treat as a rough guide", with no judgment. Under 10,
      sampled slices show no shares, and fully read slices show plain counts.
    - The unit changes **from counts to % of postings**.
    - Also updated: the welcome skills sentence (it said "for most of these", already untrue),
      User Flow 7b ("too small" = n < 30), the accordion line, the requirements-question
      interaction, two new edge cases, two new metrics, two open questions.
  - **`data-stories.md`:** Story 1's skill block becomes estimated % with the n-of-N
    qualifier. The data contract's Skills row is updated. A new honesty rule applies to every
    story.
  - **`job-classification.md`:** new "Which postings are read" subsection (Designer all,
    PM/Engineer up to 50 per specialization per month, duplicate reuse, limits are settings).
  - **Extra, not in the original table:** `design/mcp-access/experience.md` gains an "estimate
    always arrives labelled" rule. It is the MCP surface's own experience spec, and sampled
    figures reach external AIs too.
  - `data-legibility` and `end-user-content` were run on the new copy: "slice" removed from
    visible text, "indicative only" changed to "treat as a rough guide", the how-to-read line
    simplified.
- 2026-10-10: ✅ Step 3, no change. The IA defines Requirements Signal per posting and makes no
  claim about how many postings are read.
- Open, for Step 5 (frontend spec): whether a text label is enough for small-sample bars in
  `SkillDemandChart`, or `design/visual-design.md` needs a bar treatment (it only has the
  hollow-dot one for range charts).
- 2026-10-10: ⏸ **Step 4 paused: a re-extraction loop was found while reading the backlog code.**
  - Since `changes/2026-09-21-fold-reprocessing-into-ingest.md`, `ingest.run_taxonomy_reprocessing_phase()`
    calls `raw_postings.get_all_for_reclassification()`. That function returns *every* posting;
    it was a one-time helper. So every daily run reports `total_classified` > 0. It then calls
    `get_requirements_reprocess_targets(TAXONOMY_VERSION)`, which returns every extracted
    posting on the current version, and `delete_requirements_for_reprocess()` wipes them all.
    The batch lane then re-submits the oldest 500. Those are the same postings each day.
  - Evidence (prod, read-only): batch jobs 14–29 (09-27..10-08) carried 9,500 posting slots
    but only **1,056 distinct postings**. No `posting_requirements` row older than 10-08
    survives. Estimated batch spend over that stretch was about $4.20 of the $5/month ceiling,
    almost all of it repeat work.
  - Impact on this CR: the "expensive" signal is mostly this bug, not volume. Once it is fixed,
    the real cost of reading every tracked posting at batch prices (~$0.00044 each, from
    `est_cost_usd`) is roughly $1.80/month at today's ~4k tracked postings/month, plus about
    $3 one-off for the existing backlog. Sampling still bounds cost as sources grow, but its
    urgency and the size of the cap should be re-decided with the owner after the fix.
  - Action: a separate `bug-fix` change request goes first. This CR stays `in-progress`, with
    Steps 1–3 done.
