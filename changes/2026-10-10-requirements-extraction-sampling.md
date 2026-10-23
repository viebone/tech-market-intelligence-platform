---
id: requirements-extraction-sampling
date: 2026-10-10
trigger-type: stakeholder-request
change-type: api-change, ux-change
outcome: llm-spend-is-bounded-and-isolated, storage-stays-bounded-as-sources-grow
status: in-progress
---

# Change Request: Sample requirements extraction per group so its cost stops growing with posting volume

> **Scope widened 2026-10-23.** The same sample now also decides which postings keep their full
> job detail in storage. See "Scope addition 2026-10-23" below and
> `research/2026-10-23-storage-sampling.md`. The slug is kept for audit continuity.

## Signal
See: `research/2026-10-10-requirements-extraction-sampling.md`
and `research/2026-10-23-storage-sampling.md` (storage scope addition).

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

**Scope addition 2026-10-23: storage follows the same sample**
(`outcomes/storage-stays-bounded-as-sources-grow.md`).
5. **Every posting is still fetched, deduped, stored as a short record and classified.** The short
   record holds the columns already on `raw_postings` (title, company, country, salary, industry,
   size band, and so on). Counts, trends, coverage, pay and the ONS cross-check stay exact and
   unchanged.
6. **Full job detail (`raw_response`, about 6.4 KB) is kept only for sampled postings.** The
   sample uses the same rule as item 2: up to 50 per role × specialization × month, Designer
   unlimited, groups at or under the cap kept in full, chosen by deterministic hash. Unlike
   item 2, it applies to **every role, including `other` and `unknown`** (owner's choice), even
   though nothing reads their detail today. For tracked roles the stored sample and the
   extracted sample are the same set by construction.
7. **The daily run's order changes.** A posting's group must be known before its detail is
   stored or dropped. Detail for an unsampled posting is never written; it is not written and
   then deleted. That keeps the steady state non-destructive under Rule 15.
8. **Going forward only.** The 20,140 postings already stored keep their full detail. There is
   no trimming or backfill (owner's choice).
9. **Admin visibility.** Per run and per group: postings seen vs. postings kept in full.

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
| Outcome (2026-10-23) | `outcomes/storage-stays-bounded-as-sources-grow.md` | create (done 2026-10-23, priority high) |
| Experience Spec (2026-10-23) | `design/pipeline-visibility/experience.md`; `design/market-health/job-classification.md` ("Which postings are read") | update. Admin shows seen vs. kept-in-full; the classification spec states which postings keep full detail. No end-user surface changes, because counts stay exact. |
| Backend Spec (2026-10-23) | `backend/specs/market-health/api.md` | update (in Step 4). Ingestion order, store-detail-only-if-sampled, short record contract, the Rule 15 steady-state test for the daily run. |
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
- [x] ✅ Step 3a (2026-10-23): `/new-outcome`, creating `outcomes/storage-stays-bounded-as-sources-grow.md`
      (priority high, active).
- [x] ✅ Step 3b (2026-10-23): `/new-experience`. Update `design/pipeline-visibility/experience.md`
      (seen vs. kept-in-full per run and group) and `design/market-health/job-classification.md`
      (which postings keep full detail, all roles). Review `OVERVIEW.md` wording in Step 8.
- [x] ✅ Step 4: `/new-backend-spec`. Also covers the storage scope addition (items 5–9 above),
      including the Rule 15 steady-state test for the daily ingestion run. Update `backend/specs/market-health/api.md` (sampling,
      duplicate reuse, weights, `not_sampled`, weighted query contract) and
      `backend/specs/pipeline-visibility/api.md` (backlog definition, per-run sampling counts).
      Settle the open design questions in the Decision Log. `/mcp-access-review` runs inside this
      step.
- [x] ✅ Step 5: `/new-frontend-spec`. Update `frontend/specs/market-health/architecture.md`.
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
- 2026-10-23: **Resumed with the owner, using real numbers from after the loop fix**
  (re-extraction-loop CR Step 6). Production numbers, read-only:
  - **Volume:** about 250 new postings a day. Each run fetches about 11.9k and inserts only the
    new ones. Over the last 14 days: Engineer 746, PM 114, Designer 73 new tracked postings,
    about 67 a day.
  - **Spend:** batch jobs 32–43 collected cleanly, 500 postings each, about $0.23 a job, so about
    $6.80 a month while the backlog clears. Tracked backlog: 2,472 (Engineer 1,974, PM 342,
    Designer 156), about 5 more batch days. Steady state without sampling: about
    2,000 postings a month, about $0.90 a month. Classification costs about 2 calls a day.
  - **Storage:** the database is 216 MB for 20,140 postings (about 8 KB each). `raw_postings`
    is 159 MB, of which 122 MB is `raw_response`. Growth is about 60–95 MB a month, about
    1 GB a year.
  - **Owner asked whether to sample ingestion too, because the database will get huge.**
    Answer given: storage growth is about 1 GB a year, which costs cents. Each run must fetch
    every posting anyway to detect new ones, and sampling ingestion turns every count, trend
    and the ONS cross-check into an estimate. If storage ever matters, trimming `raw_response`
    to the fields actually used after extraction is the better lever. That would be a separate
    change, with destructive-step care under Rule 15. It was not raised as a CR. Owner to
    confirm scope (extraction only) before Step 4.
  - ✅ **Cap decided: 50 per role × specialization × month, Designer unlimited** (owner's
    choice). Caps are configuration, so they can be tuned without code changes.
  - ✅ **Backlog: let it finish** (owner's choice). It drains before sampling can ship. Every
    posting already extracted is kept, and sampling applies to new postings.
- 2026-10-23: **Scope widened to storage (owner's decision): "I don't want to store every job, I
  would like to follow the sample technique."** This supersedes the 2026-10-10 entry "sample
  extraction, never ingestion" for *storage of job detail only*. Fetching, dedupe, the short
  record and classification still cover every posting, so the reasons in that entry (unbiased
  counts, trends, coverage, the ONS comparison) still hold.
  - **Design chosen: sample the full detail, keep a short record for every job.** Rejected:
    storing only the sample plus per-group counters. Every count would become an estimate
    (weighted), company/country/pay views would cover only the sample, and an id-only dedupe
    table would be needed anyway, for little extra saving (about 200 B vs. about 60 B per job).
  - **Owner chose "going forward only"** over trimming existing rows after a backup. No
    destructive step is in this CR.
  - **Owner chose to sample `other`/`unknown` detail too** rather than keep no detail for them,
    in case it is needed later. The cost is accepted knowingly: roughly double the full-detail
    storage of the tracked-only option, and nothing reads it today.
  - **Anchoring:** no existing outcome covered storage (`llm-spend-is-bounded-and-isolated` is
    AI-spend only), so `outcomes/storage-stays-bounded-as-sources-grow.md` was created first
    (priority high).
  - **Amended rather than a new CR:** one selection rule serves both storage and extraction, so
    the two can't drift apart, and Steps 1–3 already cover the shared design.
  - Open, for Step 4: ingestion currently inserts before classifying (`insert_new_postings`,
    `ON CONFLICT (id) DO NOTHING`). Under the new design the group is needed before detail is
    written: either classify first, or insert the short record, classify, then write detail for
    sampled postings in the same run. That decision belongs in the backend spec, and so does
    how `reclassify_unknowns.py` and the backfill scripts behave for postings with no detail.
- 2026-10-23: ✅ Step 3b done. Owner direction: "data, charts and mcp all aligned with the sample
  technique, and it is clear that we don't track every single job but we do a good sampling to
  get accurate reading."
  - **`design/market-health/experience.md`:**
    - New **How we read the market** section. It separates two limits that the old welcome
      wording blurred into one word, "sample": *who we follow* (a set of companies, which applies
      to every job figure) and *what we read in full* (a fair sample, which applies to
      requirements only).
    - One canonical method text in two lengths, with live {M}/{cap} values. A word list: never
      "every job in the market", and never "we don't count every job", because counts are full
      and saying so would undersell them.
    - A surface map: welcome, stories, chat, instant answer, accordion, MCP.
    - The welcome Proof copy is rewritten, with a "How we read the market" disclosure.
    - A new instant answer, "How do you get these numbers?".
    - A new **"about level" rule**: estimated shares closer than their margin are never ranked
      against each other in words.
    - Two new metrics: method comprehension, and method text consistency (automated).
    - Interactions added.
  - **`data-stories.md`:** every posting-based story ends with the one-line method text. A new
    rule: counts are never worded as estimates, and estimates never as counts.
  - **`job-classification.md`:** new "Which postings keep their full details" section. All roles
    use the same rule, and Designer postings are always kept.
    - **Proposed (owner to confirm): `unknown` postings keep full details until resolved.** The
      second-look recovery reads the description; there were 71 at the time.
    - A stated consequence: future description-based fields exist only for kept postings.
  - **`design/mcp-access/experience.md`:** new "The method travels with the data" rule:
    - Count responses state that they are full counts of the followed companies.
    - Requirements responses carry the canonical method note.
    - The server description and taxonomy tool carry the full text.
    - The "about level" rule is passed on to the external AI.
  - **`design/pipeline-visibility/experience.md`:**
    - User Flow 14 adds the Sampling panel, the Sampling by group table, seen/kept per run, the
      Postings "Full details" filter and column, and the not-kept Detail message.
    - Data footprint gains the kept/short split.
    - "Not sampled" is added as a Requirements Status.
    - Chart specs, interactions, four edge cases and a metric are added.
  - `data-legibility`: every new number states its unit and scope, and "not kept" is neutral
    (not a failure colour). `end-user-content`: plain words, no statistics jargon. The example
    margin is set to ±12 pts, which is realistic for n = 50.
  - Step 4 (backend spec) inherits: the method-text source of truth with live values, the
    instant-answer entry, the "about level" comparison, MCP method fields, admin sampling
    counts, and the `unknown` keep rule.
- 2026-10-23: ✅ The owner confirmed the `unknown` rule: `unknown` postings keep their full
  details until resolved.
- 2026-10-23: ✅ **Step 4 done.** Open design questions settled. They are written into
  `backend/specs/market-health/api.md` (Data Models: RawPosting, PostingSample, PostingDetail,
  IngestionRun, PostingRequirements; Business Logic — Sampling; Sampling across the other
  response surfaces; Welcome `method`), `backend/specs/pipeline-visibility/api.md` (Not
  sampled status, `GET /admin/sampling`, Postings/Detail/Overview/runs/technical-data
  additions), `backend/specs/mcp-access/api.md` and `ACCESS.md`.
  - **Immutability kept.** `raw_postings` is still never updated, so the design stores no
    payload and then deletes it. New postings are inserted with `raw_response = NULL`. The
    decision goes in a new insert-only `posting_samples` table, and payloads for kept postings
    go in a new insert-only `posting_details` table. Readers use one
    `COALESCE(pd.raw_response, rp.raw_response)` helper.
  - **Ingestion order.** Fetch + insert the short record → classify → reprocess → **decide** →
    requirements. Payloads are held in memory for the run, for new and still-pending ids. Every
    run re-fetches full live boards, so a crash or a classification-budget stop just leaves
    postings pending until the next run, with no staging table. Pending more than 14 days and
    gone from the board → `not_kept / unavailable`.
  - **How selection behaves while a month fills: rate-based (Poisson) sampling on a fixed
    per-posting hash.**
    - `r = min(1, K / previous month's group size)`.
    - From day 7, `r` can only fall: `r = min(r, K / projected size)`.
    - Hard ceiling of 2K per group per month.
    - A decision is never revisited.
    - Rejected: lowest-K-hashes. Deciding daily without un-keeping overshoots to about
      `K(1 + ln(N/K))`, about 180 for a 700-posting group.
  - **Existing backlog.** The one-time migration marks every pre-go-live posting
    `kept_before_sampling` and the backlog of 2,472 is extracted in full (owner: let it finish).
    Nothing is marked `not_sampled` retroactively. That supersedes the 10-10 proposal.
  - **Duplicate-reuse key.** Exact `sha256(company | normalised title | cleaned description)`
    only. Company + title alone is rejected. Copies record `reused_from` and are counted in
    `requirements_reused`, separate from paid extraction.
  - **Weights with breakdowns.** Post-stratified by role × specialization × month:
    `share = Σ N_g · x_g/n_g / Σ N_g`. Level and country filters narrow N, n and x inside each
    group. One worst-case margin per response, with the finite-population correction. Groups
    with nothing read are excluded and reported as `unread_n`. The experience thresholds map
    to `confidence` = `full` / `estimate` / `small_sample` / `too_few` / `full_small`.
  - **Per-role limits, confirmed.** Designer unlimited, Engineer / PM / `other` 50, `unknown`
    always kept. Configured in `sampling_settings.py` with env overrides.
  - **One source for wording.** `method_text.py` renders the method text, the estimate
    `qualifier` and the admin rule line for every surface. A test asserts identical output.
  - **MCP review (`/mcp-access-review`).** 6 capabilities reviewed. Exposed or updated: the
    `get_skill_demand` estimate, the method text via `get_taxonomy.method` + server
    instructions + `meta.coverage` on count tools, and the "about level" rule in the docstring.
    Not exposed, with reasons in `ACCESS.md` and the MCP spec: admin sampling visibility, raw
    sample decisions and payloads, and the `how-numbers` curated answer (its content reaches MCP
    via `get_taxonomy.method`).
  - **Data surface review: no-change, reconfirmed.** `posting_samples` / `posting_details` are
    metadata and storage for the existing postings category, not a new kind of fact. The admin
    and query-path changes are already specified.
  - **Polite scraping review: not applicable.** No scraped source is touched.
  - **Rule 15.** The steady state is written into the spec: no paid work, no deletes, no
    overwrites. It is proved by `test_sampling_steady_state.py`, plus rate/estimate tests and
    `test_sampling_counts_unchanged.py`.
  - **Dependency (new).** `/implement-backend` here (Step 6) ships after, or together with, the
    re-extraction-loop CR's guardrails (its Steps 2–4). Sampling changes the requirements
    selection path, and the repeat-work tripwire must be on it.
  - Expected effect, from September 2026 data: about 19% of postings kept in full (1,815 of
    9,442 across 62 groups). Full-detail storage growth drops by about 80%.
- 2026-10-23: ✅ **Step 5 done.** `frontend/specs/market-health/architecture.md` gains
  "Sampling and the method text".
  - **The rule:** the frontend never writes method or estimate wording. It renders
    `method.one_line` / `method.full` / `method_line` / `estimate.qualifier` from the API. The
    only fixed client text is the "± pts" how-to-read line from the experience spec.
  - **New component:** `MethodDisclosure` ("How we read the market", collapsed by default).
  - **Changed components:**
    - `WelcomeMessage`: the old hardcoded Proof sentence is removed, with no fallback to it.
    - Every story renderer shows a non-null `method_line`.
    - `StoryBlock` gains an `estimate` prop; `too_few` renders the qualifier instead of a chart.
    - `SkillDemandChart` moves to shares, with "% of postings" labels; `full_small` uses counts.
    - Story 1 shows the how-to-read line once.
    - `ReasoningPanel` shows `trace.method_line`.
  - **No change:** `SuggestedQuestions` (the `how-numbers` chip is server-owned) and the admin
    (server-rendered, built in `/implement-backend`).
  - **Contract alignment:** the chat trace's method line is the named field `trace.method_line`,
    not a fake `sources_and_tools` entry. `backend/specs/market-health/api.md` is updated to
    match.
  - **Experience Open Question (small-sample bars), answered from the frontend side:** no bar
    treatment needed. Confidence is per block (one n and one margin per chart), so the block's
    qualifier text carries "small sample, treat as a rough guide", and `visual-design.md` needs
    no new token. The Designer should close the open question in
    `design/market-health/experience.md` the next time it is touched.
