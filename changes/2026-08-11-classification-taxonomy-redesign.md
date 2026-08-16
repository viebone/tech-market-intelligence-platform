---
id: classification-taxonomy-redesign
date: 2026-08-11
trigger-type: stakeholder-request
change-type: api-change, technical-refactor
outcome: understand-market-health-before-searching
status: in-progress
---

# Change Request: Classification + Requirements Taxonomy Redesign

## Signal
See: `research/2026-08-11-classification-taxonomy-redesign.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md`

Same outcome as the Compensation Signal and Requirements/Industry Signal changes before it.
This one is a data-*accuracy* fix rather than a new capability: the outcome's success
criteria explicitly promise "they can identify which roles and skills are in demand" and
"they can see the trends clearly" — both are currently compromised for a large, real slice
of the data (management-track postings across all three role categories, and the
~265-posting Solutions Architect/Solutions Engineer/Support Engineer/Forward Deployed
population within Engineer), confirmed with real production queries, not assumed.

## Change Type
`api-change` — new/restructured data model fields (level/track replacing the seniority
ladder, occupation_family/specialization internal naming, classification_confidence, skills
raw_skill/skill_group restructuring, education_required/equivalent_experience_accepted,
years_experience_min, work_arrangement) and new business logic (reprocessing plan, salary
exclusion rule).
`technical-refactor` — corrects the meaning of already-stored data (the current
`seniority=manager` bucket has already destructively collapsed real level information); no
new user-facing capability is being added, existing Demand Signal and Requirements Signal
answers become more trustworthy.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change — success criteria already cover this, just currently under-delivered |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change — the IA's "Role Category" term (Designer/Product Manager/Engineer) is a fixed, product-facing label; this change keeps that label and only restructures the internal implementation beneath it. Confirm during Step 1, don't just assume. |
| Visual Design | `design/visual-design.md` | no-change |
| Taxonomy Reference Spec | `design/market-health/job-classification.md` | **update** — the primary target. Full taxonomy redesign per the converged scope in the research file: occupation_family/specialization/level/track/unknown-vs-other, classification_confidence, skills raw_skill+skill_group restructuring (normalized_skill deferred), education_required/equivalent_experience_accepted, years_experience_min, work_arrangement, explicit salary-exclusion rule. This is Designer's call (taxonomy content), same ownership precedent as the original taxonomy and the 2026-08-09 Requirements Taxonomy addition — not invented in the backend spec. |
| Experience Spec | `design/market-health/experience.md` | **review, likely no-change** — "seniority" and "track" are already presented as two separate filter-chip concepts in the current UX (line 178: "role, sub-specialization, seniority, track, location"); renaming the internal field (seniority ladder → level) shouldn't change any user-facing label or interaction, since the UI never enumerates the ladder values itself. Must be confirmed by actually reading the spec during execution, not assumed — same rigor as the frontend spec's prior "Reviewed" entries. |
| Backend Spec | `backend/specs/market-health/api.md` | **update** — new data model, the technical reprocessing/backfill plan for ~5,105 already-classified postings and ~82 already-requirements-extracted postings, taxonomy_version bump strategy, and a decision on whether external API field names change or only internal ones do. |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **review** — check for any hardcoded old seniority-ladder values (e.g. "manager"/"director" strings) in filter/chip rendering that would need updating even though the user-facing labels themselves don't change. Don't assume a 4th consecutive no-op without checking, per this file's own standing discipline. |
| Backend Implementation | `backend/src/` | update — schema migration, updated classification/requirements extraction logic, reprocessing run |
| Frontend Implementation | `frontend/src/` | update only if the frontend spec review finds a real gap; otherwise confirm no-op |

## Execution Plan

- [x] Step 1: `/new-experience` — rewrote `design/market-health/job-classification.md` in
      full: Role Category now documents the internal occupation_family backing concept (no
      product-facing change); specialization allows `unknown` and Designer gains 3 new
      specializations (Content Designer/UX Writer, Design Systems, Other Design); the old
      `seniority` ladder is replaced by orthogonal `Level` and `Track` sections, with the
      160-posting `seniority=manager` collapse documented as the concrete real-data proof of
      the bug being fixed; new "Unknown vs. Other" section explains the distinction and why
      it matters analytically; Requirements Taxonomy's Skills section restructured to
      raw_skill + skill_group (normalized_skill explicitly deferred, with reasoning), with
      skill_group selection now keyed to (Role Category, Track, Specialization) via a new
      table covering People Leadership, Pre-sales & Solutions, and two new Engineer groups
      (Data engineering/big data, Blockchain/Web3); Education gains `education_required` +
      `equivalent_experience_accepted`; new Years of Experience and Work Arrangement
      subsections; explicit salary-exclusion rule added to Other Requirements; Classification
      Method gains `classification_confidence` (self-reported low/medium/high); "What this
      rules out" extended with 5 new bullets covering the new rules. Confirmed
      `design/information-architecture.md`'s "Role Category" definition ("One of the three
      tracked job categories: Designer, Product Manager, Engineer") needs no change — verified
      by reading it directly, it names only the three category labels, nothing about
      specialization/level/track internals.
- [x] Step 2: Reviewed `design/market-health/experience.md` in full — confirmed no UX change
      needed. Line 178's filter-chip list already presents "seniority" and "track" as two
      separate concepts, and this spec never enumerates the underlying ladder values itself —
      the chips' values becoming more accurate doesn't change any wording or interaction here.
      Documented as a new "Resolved (2026-08-11)" entry in the Open Questions section,
      following this file's own existing convention for recording past decisions.
- [x] Step 3: `/new-backend-spec` — updated `backend/specs/market-health/api.md` in full:
      `Classification` table restructured (`sub_specialization`→`specialization` rename,
      `seniority` dropped in favor of new `level` + existing `track`, both plus
      `role_category` now allow `unknown`, new `classification_confidence` column) — with the
      column rename/drop explicitly flagged as a deliberate one-time exception to this
      product's normally-additive-only migration pattern, and reasoning given for why (old
      `seniority` data is actively wrong, not just incomplete, so preserving it has no value).
      `PostingRequirements` gains 4 new additive columns (`education_required`,
      `equivalent_experience_accepted`, `years_experience_min`, `work_arrangement`) plus an
      explicit rule barring salary extraction into `other_requirements`. `PostingSkill`
      restructured (`skill`→`skill_group` rename, new `raw_skill` column, `UNIQUE` constraint
      moved from `(posting_id, skill)` to `(posting_id, raw_skill)` since multiple raw
      mentions can now share one skill_group). New **Taxonomy reprocessing (2026-08-11)**
      Business Logic subsection: classification reprocessing (cheap, cache-able, UPDATE-in-
      place since `posting_id` is `UNIQUE`) must complete before requirements reprocessing
      (not cache-able, real cost against the ~82 already-extracted postings, done via delete-
      then-let-the-existing-backlog-query-repick-them-up rather than a bespoke script) —
      explicit ordering dependency stated (skill_group selection now depends on the posting's
      already-reprocessed classification). Requirements extraction's skill_group selection
      logic updated to be (role_category × track × specialization)-aware, batching regrouped
      accordingly. `query_market_data`/`query_compensation_data`/`query_requirements_data`
      all updated: filter param renames, `query_requirements_data` gains `skill_group`/
      `work_arrangement`/`education_required` filters and returns `raw_skills` breakdown per
      skill_group plus `equivalent_experience_accepted_count`/`years_experience_min`/
      `work_arrangement` aggregates. Left explicitly out of scope, confirmed by checking: the
      mocked `/api/market-health/summary` endpoint's `seniority` query param (unrelated,
      unused by the real pipeline, already documented as unchanged-by-prior-updates) and
      `/api/chat`'s `ChatContext.seniority` request field (appears vestigial/unused by the
      actual query logic, but renaming it wasn't part of this change's declared scope and
      would need its own verification pass).
- [x] Step 4: `/new-frontend-spec` — **not a clean no-op**, unlike the four prior reviews.
      Grepped the real component tree and found: (1) `FilterControls.tsx`,
      `ProvenancePanel.tsx`, `ConversationalArea.tsx` hardcode old field names/values but are
      confirmed dead code (no importers anywhere, matching this spec's own "Filter controls"
      out-of-scope note) — left untouched, fixing unreachable dead code is a separate future
      cleanup, not this change's scope; (2) `MarketHealthPage.tsx:111` — live, reachable code
      — sends a hardcoded `context: { seniority: "all", ... }` payload on every chat request;
      the value is always the sentinel `"all"`, never a real taxonomy value, and the field
      isn't read by any real backend query logic, so there's no data-correctness bug, but the
      stale field name is worth a one-line rename to `level` for consistency. Documented as a
      5th "Reviewed" entry in `frontend/specs/market-health/architecture.md`, and scoped as a
      trivial fix for Step 6 rather than silently left as debt.
- [x] Step 5: `/implement-backend` — full implementation, verified against real production
      data at every layer, not just compile-checked.
      **Schema** (`db.py`): `classifications` restructured exactly per the backend spec —
      `sub_specialization`→`specialization` rename, `seniority` dropped, `level` +
      `classification_confidence` added, all via idempotent DO-block-guarded SQL (safe to
      re-run on every startup, same as every other migration in this file). `posting_requirements`
      gained 4 additive columns. `posting_skills` restructured (`skill`→`skill_group` rename,
      new `raw_skill` column, `UNIQUE` constraint moved to `(posting_id, raw_skill)`).
      **`classification.py`**: `_validate()` rewritten for the 3-way role_category branch
      (real category / `unknown` / invalid→`other`), `specialization`/`level`/`track` each
      independently allow `unknown`, new `classification_confidence` (defaults to `low` if
      missing/invalid — biased toward under-claiming). `TAXONOMY_VERSION` bumped to
      `2026-08-11`. Added `reclassify_all()` + `update_classifications()` (UPDATE-in-place,
      deliberately kept separate from the normal `insert_classifications()`'s
      `ON CONFLICT DO NOTHING` — that's a real safety net for ongoing operation, not something
      to share with reprocessing's overwrite-on-purpose behavior) + a version-scoped title
      cache (`_get_title_cache_for_version`) so a multi-day reprocessing pass converges instead
      of re-doing the same early titles forever.
      **`requirements.py`**: full rewrite. `applicable_skill_groups(role_category, track,
      specialization)` implements the union logic from job-classification.md's table (IC list
      always applies; People Leadership additive when `track=="management"`; Pre-sales &
      Solutions additive for the 6 named Engineer specializations). `_group_into_batches` now
      groups by the actual applicable-list key, not `role_category` alone. New fields
      (`years_experience_min`, `work_arrangement`, `education_required`,
      `equivalent_experience_accepted`, `raw_skill` alongside `skill_group`) added to
      extraction/validation/insert. Explicit "never extract compensation" instruction added to
      the system prompt. New `delete_requirements_for_reprocess()` for the reprocessing delete
      step.
      **`raw_postings.py`**: `get_all_needing_requirements()` now excludes `role_category
      NOT IN ('other', 'unknown')` (was just `!= 'other'`) and returns `track`/`specialization`
      too, since skill_group selection needs them. New
      `get_all_for_reclassification()`/`get_requirements_reprocess_targets()` for the
      reprocessing pass.
      **`reprocess_taxonomy.py`** (new, separate script — not folded into `ingest.py`,
      deliberately, since this is one-time migration work that becomes dead weight in the
      daily pipeline once the backlog clears): runs the two reprocessing phases in the correct
      order every invocation, safe to re-run repeatedly, shares classification's existing
      daily budget/key and records its own `ingestion_runs` row so budget accounting stays
      correct alongside regular `ingest.py` runs on the same day.
      **`market_query.py`**: all three query tools updated — renamed filters
      (`specialization`/`level`), `role_category` filter now also accepts `unknown` (not
      excluded by default, unlike `other`). `query_requirements_data` gained `skill_group`/
      `work_arrangement`/`education_required` filters and now returns a `raw_skills` breakdown
      per skill_group, `equivalent_experience_accepted_count`, `years_experience_min`
      {min/median/max}, and `work_arrangement` aggregate.
      **`chat.py`**: `_DATA_STAGE_SYSTEM_TEMPLATE` updated — renamed dimensions, new guidance
      to use `raw_skills` for specific-technology questions, explicit reminder that
      `query_requirements_data` never returns compensation. Left `ChatContext.seniority` and
      the mocked `/api/chat/context` debug endpoint's `seniority` param untouched — confirmed
      both belong to the same legacy/mocked pathway already documented as out of scope, not
      the real query logic.
      **Frontend**: `MarketHealthPage.tsx:111`'s hardcoded context payload renamed
      `seniority`→`level`, per Step 4's scoped finding.
      **Verification, not just compilation**: ran the real migration against production —
      confirmed via direct schema queries that every column/constraint landed exactly as
      specified, and that pre-migration data survived the renames correctly (real
      `specialization`/`track` values preserved on non-`other` rows; `posting_skills.skill_group`
      preserved with `raw_skill` correctly `NULL` pre-reprocessing). Ran a real, small
      (3-posting) `reclassify_all()` test on postings the original bug directly affected
      ("Specialist Solutions Architect, Tax/Radar/Payments") — results: `specialization:
      "Solutions Architect"`, `level: "unknown"` (correctly — the title gives no seniority
      signal, a real demonstration of the new honesty mechanism working, not a guess),
      `track: "ic"`, `classification_confidence: "high"`. Confirmed the reprocessing ordering
      dependency end-to-end on one real posting already in `posting_requirements`: reclassified
      it onto the new taxonomy → `get_requirements_reprocess_targets()` correctly found it →
      deleted its stale requirements → confirmed it reappeared in
      `get_all_needing_requirements()` → ran real extraction → **the posting that would have
      scored zero skills under the old taxonomy correctly extracted 5 real, accurate skills**
      (Technical pre-sales & discovery, Technical demoing & solution design, Executive
      stakeholder relationship-building, Escalation & incident troubleshooting, Customer-facing
      communication), each with real supporting text, plus a correct freeform note about tax
      domain expertise. This is concrete, real proof the fix works, not just that the code runs.
      **One honest miss, not fixed on n=1 evidence**: `years_experience_min` came back `null`
      for that same test posting despite the text explicitly stating "7+ years of experience"
      — likely LLM confusion from two different experience numbers in the same posting (7+
      years customer-facing, 3+ years tax-specific). Noted, not treated as a code bug, not
      prompt-tuned yet — consistent with this pipeline's standing "tuned as real data comes in"
      discipline rather than reacting to a single sample.
      **Addendum — first real backlog run (2026-08-11, user approved)**: kicked off
      `reprocess_taxonomy.py` for real. First attempt failed immediately with
      `psycopg.errors.UndefinedColumn: column "skill" does not exist` — a real idempotency bug
      in the db.py migration: `CREATE INDEX IF NOT EXISTS idx_posting_skills_skill ON
      posting_skills (skill)` still validates its column list even when the index name already
      exists, so it broke on the *second* startup after the rename (the first run created the
      index fine, before `skill` was renamed to `skill_group`). Fixed by removing the
      early/stale reference and adding a corrected one (same index name, `skill_group` column)
      positioned after the rename migration — verified genuinely idempotent this time by
      running `init_schema()` twice in a row before re-attempting. Re-ran successfully:
      5,105 postings checked, 826 heuristic-filtered, 1,314 reclassified via 11 real LLM
      requests across 11 batches, hit the daily budget cap cleanly (`budget_reached: true`,
      `status: "success"`, 26/37 batches left for future runs) — 2,143 postings now on
      `taxonomy_version: "2026-08-11"`. Verified the real level distribution: the old
      160-posting `seniority: "manager"` collapse is gone, replaced by senior (251),
      principal (70), mid (47), lead (11), director (10), entry/junior/executive (small
      counts), and `unknown` (270, genuine cases). Spot-checked a real `role_category:
      "unknown"` example — "Performance Solutions Lead" — exactly the kind of genuinely
      ambiguous title the taxonomy redesign was built to catch. 121 postings' stale
      requirements were deleted and are queued for re-extraction by the next `ingest.py` run.
      Remaining backlog (2,962 postings' classifications, plus whatever requirements
      reprocessing hasn't yet been triggered by classification catching up) will clear over
      the following days as `reprocess_taxonomy.py` and/or the deployed daily cron continue
      running — per the user's plan, deployment/rebuild is being handled separately.
- [x] Step 6: `/implement-frontend` — Step 4's one real finding (`MarketHealthPage.tsx:111`'s
      stale `seniority` field name) was small enough to implement directly as part of Step 5's
      pass rather than needing a separate invocation — done, see Step 5 notes. No other
      frontend change needed; the three confirmed-dead files are tracked separately (see
      memory note below), not part of this change.

## Decision Log
- 2026-08-11: Tracked against `understand-market-health-before-searching` — same outcome as
  the two prior Signal changes; this one repairs accuracy of promises already made by that
  outcome's success criteria rather than adding new scope.
- 2026-08-11: Classified as `api-change` + `technical-refactor`, not `new-feature` — nothing
  new is being exposed to the user; existing Demand Signal and Requirements Signal answers
  become more accurate for management-track and Solutions Architect/Engineer-type postings
  that are currently structurally unable to produce meaningful results.
- 2026-08-11: The reprocessing cost (all ~5,105 classified postings, not just the ~82
  requirements-extracted ones) is treated as in-scope execution work for Step 5, not a
  separate future change — named explicitly here so it isn't discovered mid-implementation.
- 2026-08-11: `normalized_skill` (canonicalized spelling variants, e.g. "React.js"→"React")
  is explicitly deferred out of this change — `raw_skill` + `skill_group` ship now;
  building a global skill-name dictionary upfront was judged premature, same reasoning
  already applied elsewhere in this taxonomy (don't design ahead of real data).
- 2026-08-11: The ~64% NULL-seniority rate observed while gathering evidence is explicitly
  out of scope — it's a classification extraction-rate question, not a taxonomy-structure
  question; noted for a possible future change, not folded into this one.
