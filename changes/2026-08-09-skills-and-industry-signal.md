---
id: skills-and-industry-signal
date: 2026-08-09
trigger-type: stakeholder-request
change-type: new-feature, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Requirements/Skills Signal + Industry tagging

## Signal
See: `research/2026-08-09-skills-and-industry-signal.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md`

Same outcome as the Compensation Signal change — the outcome already promises "They can
identify which roles and skills are in demand vs. declining." This activates the
"skills" half of that promise (roles already covered by Demand Signal); industry tagging
extends the same outcome's Context ("target companies, geography" — industry is the same
class of decision-relevant dimension, not new scope).

## Change Type
`new-feature` — neither skills/requirements extraction nor industry tagging exist
anywhere in the product today.
`api-change` — new data model(s), new per-posting extraction pipeline, new query tool(s).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | **update** — Content Taxonomy needs a new entry, sibling to the existing "Demand Signal"/"Compensation Signal"/"Layoff Signal" — this capability has no existing named term to activate (unlike Compensation Signal, which activated an already-named-but-unbuilt concept). Working name: "Requirements Signal" (covers skills/responsibilities/education/language, broader than "skills" alone) — final name is the Designer's call in `/new-information-architecture`, not fixed here. |
| Visual Design | `design/visual-design.md` | no-change for this triage — revisit only if `/new-experience` determines a genuinely new visual token is needed |
| Experience Spec | `design/market-health/experience.md` | update — define how Requirements Signal surfaces (conversational, same pattern as Compensation Signal — no new opening-view chart), the confidence/sample-size disclosure rules for recommendation-style answers (e.g. "should I learn to code as a UX designer?"), and how a synthesis/recommendation answer differs from a plain data-lookup answer |
| Taxonomy Reference Spec | `design/market-health/job-classification.md` | update — extend with new closed-ish taxonomies for skills (per role category), education level, and language requirements, each with an explicit freeform catch-all — same "closed set + `other` escape hatch" discipline already used for Role Category/Seniority/Track. This is a real taxonomy design decision (which skills, which categories), same weight as the original Role Category decision — Designer's call, not invented in backend spec. |
| Backend Spec | `backend/specs/market-health/api.md` | update — new data model for extracted requirements (standard fields + catch-all, keyed to `posting_id`), static industry lookup + column, per-posting extraction business logic (with its own backlog/daily-budget handling, reusing the pattern already proven for classification — NOT a shared generic "signals" table, a purpose-built model for this signal type specifically), new query tool(s) for skill-frequency aggregation |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — verify against the pattern of the last three backend-only changes (each confirmed no frontend code needed); do not assume it holds again without checking |
| Backend Implementation | `backend/src/` | update |
| Frontend Implementation | `frontend/src/` | update only if the frontend spec review finds a real gap; otherwise confirm no-op |

## Execution Plan

- [x] Step 1: `/new-information-architecture` — added **"Requirements Signal"** to Content
      Taxonomy (final name, not just a working one): "A data point representing the skills
      (must-have vs. nice-to-have), responsibilities, education level, and language
      requirements extracted from a single job posting, with a freeform catch-all for
      anything outside that standard structure." Marked "Future tasks" (not yet built),
      same convention Compensation Signal used before it shipped. Did not add a separate
      term for synthesis/recommendation-style answers — the structural mechanism (a chat
      message in the Working Space) is identical to any other follow-up; the reasoning
      behind its content is an experience-level behavior, not a new IA concept, per the
      "don't define per-feature behavior here" rule. Also fixed a staleness bug found while
      here: "Compensation Signal" was still marked "Future tasks" despite having shipped
      2026-08-04 — corrected to "Working Space, Output Panel". Bumped IA version 2.0 → 2.1.
- [x] Step 2: `/new-experience` — updated `design/market-health/job-classification.md`:
      added a full "Requirements Taxonomy" section (skills per Role Category, education
      level ladder, language requirements, a deliberately non-taxonomized responsibilities
      summary, and the freeform "Other requirements" catch-all), plus a "Requirements
      Extraction Method" section establishing the "interpretation, not verified fact"
      honesty rule. Updated `design/market-health/experience.md`: added Requirements Signal
      to the secondary-questions list, a new User Flow step 7b defining the two-part
      data-then-judgment answer pattern for synthesis questions (never blended, declines to
      judge on too-small a sample), 2 new Interactions rows, 3 new Edge Cases, 2 new
      Evaluation Metrics, and Open Questions on a future skills visual and the v1 skills
      list being explicitly provisional.
- [x] Step 3: `/new-backend-spec` — updated `backend/specs/market-health/api.md`: 3 new
      data models (`PostingRequirements` 1:1, `PostingSkill` and `PostingLanguage` 1:many,
      each with a DB-enforced dedupe/uniqueness invariant matching the established
      discipline); `industry` column on `RawPosting`; new Business Logic sections for
      Industry tagging (static lookup, no LLM) and Requirements extraction (per-posting,
      own dedicated key/budget/batch-size constants, oldest-first, scoped to already-real
      classifications only); a third query tool `query_requirements_data` registered
      alongside the other two; extended the anti-fabrication guard and reasoning-trace
      notes to be three-tools-aware; added the synthesis-question data-then-judgment rule
      to Business Logic. Also fixed a dangling/duplicated sentence found in the
      Cross-run daily budget section from the 2026-08-05 change while working nearby.
- [x] Step 4: `/new-frontend-spec` — verified by reading the actual component code (not the
      stale spec): confirmed **no frontend changes needed**. Found and documented two real
      things: (1) this spec's component names are stale — no `AIMessage.tsx` exists; the
      real components are `MarketBriefingMessage.tsx` (opening) and inline rendering in
      `ConversationThread.tsx` (follow-ups), wrapped by `AITurn.tsx`; (2) follow-up answers
      render as plain `whitespace-pre-wrap` text, no markdown — which means a two-part
      synthesis answer's "never blended" separation is a content/wording discipline
      enforced by the backend's synthesis-stage prompt, not a rendering gap. Added a fourth
      "Reviewed 2026-08-09" entry to `frontend/specs/market-health/architecture.md`.
- [x] Step 5: `/implement-backend` — implemented all 3 new tables (`posting_requirements`,
      `posting_skills`, `posting_languages`) plus `raw_postings.industry`; new
      `backend/src/industries.py` (35-company static lookup, wired into
      `insert_new_postings()`); new `backend/src/requirements.py` (full per-posting
      extraction pipeline — category-specific prompts, HTML-cleaning/truncation to 3000
      chars, batching by same role_category ≤15/batch, own dedicated daily budget/retry
      constants, `GEMINI_API_KEY_REQUIREMENTS` as its own key per the dedicated-key-per-
      concern discipline); `raw_postings.get_all_needing_requirements()` (real
      classifications only, oldest-first); `ingestion_runs.get_requirements_requests_used_today()`
      and 3 new `record_run()` fields for cross-run budget tracking (same pattern as
      classification's); wired as a new phase in `ingest.py` after classification;
      `market_query.query_requirements_data()` (skill/education/language aggregation,
      same filter set and `total_matching`/`data_range` shape as the other two tools);
      registered as a third tool in `chat.py`, plus the two-part data-then-judgment
      synthesis rule added to `_build_synthesis_system`; fixed two hardcoded
      `"query_market_data"` string references in `chat.py` found while extending the
      reasoning trace to be three-tools-aware, so all three tools now label correctly.
      Schema migration applied live (`init_schema()`), verified against real production
      data at every stage: `get_all_needing_requirements()` found 2,332 real postings
      needing extraction; `_extract_description()` verified against a real Stripe posting
      (clean text, correct 3000-char truncation); `_group_into_batches()` verified against
      real data; `query_requirements_data()` verified to return the correct empty shape
      pre-data. Ran one real, small-scale (3-posting) end-to-end extraction test — succeeded
      (`requirements_extracted: 3, requirements_requests_used: 1, stopped_early: False`) —
      and manually verified the written rows: correct education_level, real per-role skills
      extracted for the Engineering Manager posting (5 must-have skills, matching the closed
      Engineer list), and — checked specifically rather than assumed — zero skills correctly
      extracted for the two "Technical Support Engineer" postings, whose description
      genuinely doesn't map to any closed Engineer skill (support/API-troubleshooting prose,
      not frontend/backend/cloud/etc.) — confirms the LLM is honoring the closed-taxonomy
      discipline rather than force-fitting matches. The duplicate responsibilities_summary
      across those same two postings was also checked, not assumed a bug: both are the same
      req ("Technical Support Engineer, Metronome") with byte-identical description text, so
      identical output is correct. **Known gap flagged, not fixed here**: descriptions are
      truncated at 3000 chars before extraction; a posting whose must-have/nice-to-have list
      appears after that cutoff would have it silently missed — worth watching once the
      backlog runs at scale, not addressed as part of this change since no real evidence of
      it happening yet (same "don't fix what isn't observed" discipline as elsewhere in this
      pipeline).
      **Outstanding, not something this step can resolve**: `GEMINI_API_KEY_REQUIREMENTS`
      is not yet set in the real `backend/.env` — the test above used
      `GEMINI_API_KEY_CLASSIFICATION`'s value temporarily exported for verification only,
      never persisted. Production needs an explicit decision: a genuinely separate Google
      Cloud project (for real quota isolation) vs. reusing an existing key (classification's
      real usage is now only ~1 request/day at steady state, so shared headroom is likely
      ample either way) — same unconfirmed-assumption caveat already on record for the
      classification key.

      **Addendum, 2026-08-10**: `GEMINI_API_KEY_REQUIREMENTS` was created as a genuinely
      separate Google Cloud project and set in the real `backend/.env`. Re-running the
      verification test against the real key (not a borrowed one) surfaced two real defects
      the earlier test couldn't have caught, both fixed and re-verified against real
      production data:
      1. `EXTRACTION_MODEL = "gemini-2.5-flash"` (`requirements.py`) failed with
         `404 NOT_FOUND: This model ... is no longer available to new users` —
         confirmation the new project is genuinely isolated (Google has since restricted
         `gemini-2.5-flash` from new projects; the classification key's older project is
         grandfathered in). Changed to `"gemini-flash-latest"`, a Google-maintained alias
         that always tracks the current default flash model — chosen specifically so this
         pipeline doesn't break again the next time Google rotates model generations,
         which a pinned version would.
      2. With the model fixed, calls then failed with `400 INVALID_ARGUMENT` — isolated by
         direct testing to `llm/gemini.py`'s `complete()` hardcoding
         `ThinkingConfig(thinking_budget=0)`: confirmed empirically that this exact model
         rejects `budget=0` but accepts `budget=1`. Fixed in the shared adapter with a
         narrow fallback (try `budget=0` first; on a `400`/`invalid_argument` response,
         retry once with `budget=1`) rather than changing the default — `gemini-2.5-flash`
         callers (classification, chat) are completely unaffected since their first
         attempt already succeeds and the fallback branch never triggers for them.
      Re-ran the 3-posting extraction test against real, previously-untouched backlog
      postings end-to-end with the real key: succeeded (`requirements_extracted: 3,
      requirements_requests_used: 2`; one batch hit the 400 and transparently recovered
      via the new fallback, visible in logs as a 400 immediately followed by a 200 for the
      same batch). Manually verified the written rows again: a Designer posting correctly
      got "Visual/UI design" and "Design systems" as must-haves, with portfolio/craft
      language correctly routed to the freeform catch-all instead of force-fit into a
      skill tag; two Technical Solutions Engineer postings correctly got zero closed-list
      Engineer skills (one despite mentioning several programming languages/frameworks in
      "familiarity with" phrasing — a conservative, defensible LLM judgment call, not a
      code defect, consistent with the non-forcing behavior already accepted in the
      original test). `model` column correctly shows `gemini-flash-latest` for these new
      rows, distinct from the earlier test rows' `gemini-2.5-flash` — honest per-row
      provenance intact.

      **Addendum, 2026-08-10 (real backlog backfill + a second real defect found)**: at
      the user's request, ran the real `ingest.py` locally against production (fetch +
      classify + extract), to make real progress on the ~2,356-posting backlog today and
      leave a clean baseline for the deployed cron to continue "from tomorrow." Result:
      `status: partial`, 53 postings' requirements extracted (batches 1-5 of 348), then a
      real `429 RESOURCE_EXHAUSTED` on batch 6 — Google's own error confirmed the daily
      cap: `limit: 20, model: gemini-3.6-flash` (the concrete model `gemini-flash-latest`
      currently resolves to). This is expected/designed behavior (graceful stop, run
      correctly recorded as `partial`, not a crash) — but the *number* of batches
      completed before hitting it exposed a real defect: our own budget ledger
      (`requirements_requests_used`) only counts outer retry attempts in
      `_complete_with_retry`, but each successful call on this model was silently costing
      **two** real Google API calls — the guaranteed-fail `budget=0` attempt plus the
      `budget=1` fallback from the 2026-08-10 fix above — both billed against the same
      real 20/day quota, only one counted against ours. So the ledger thought it had
      spent ~5 requests when Google's server-side count was ~10, causing real exhaustion
      well before our own cap would have stopped it. Fixed in `llm/gemini.py`: a
      module-level `_MODELS_REJECTING_ZERO_THINKING_BUDGET` set, populated the first time
      a model's `budget=0` attempt fails this way, consulted on every subsequent call
      (any adapter instance, since a fresh one is constructed per call site) to skip
      straight to `budget=1` — eliminating the wasted doomed-to-fail call for the rest of
      the process's lifetime. `gemini-2.5-flash` never populates this set, so
      classification/chat are unaffected. This roughly doubles real daily throughput for
      `gemini-flash-latest` going forward (each successful batch now costs 1 real call,
      not 2), meaning `MAX_BATCHES_PER_RUN` (12) should become the binding constraint
      instead of real quota exhaustion on future runs. Not re-verified end-to-end today
      since real quota for this key is now genuinely exhausted until Google's daily reset
      — compile-checked only; will be confirmed by the first real run after deploy.
      **Backlog status after today**: 59 of 2,362 real classified postings now have
      requirements extracted (2,303 remaining). At the pre-fix rate this would have taken
      ~40+ days; post-fix, roughly 12 batches/day × ~14 postings/batch ≈ 160-170/day is
      the realistic expectation, ballparking full backlog clearance around 2-3 weeks of
      daily cron runs — an estimate, not a commitment, per this pipeline's standing
      "tuned as real data comes in" precedent.
      **Still outstanding**: none of this session's code (including today's fixes) is
      deployed. `job-sync`'s Railway cron is still running the pre-this-change `ingest.py`
      and has no `GEMINI_API_KEY_REQUIREMENTS` env var. For the backlog to keep clearing
      automatically "from tomorrow" as intended, this needs: commit + push to `main`, add
      `GEMINI_API_KEY_REQUIREMENTS` to `job-sync`'s Railway env vars, and an explicit
      Railway deploy trigger (auto-deploy is off for this repo per `DEPLOYMENT.md`) —
      pending the user's go-ahead, not yet done.
- [x] Step 6: `/implement-frontend` — confirmed no-op, verified two ways rather than trusting
      Step 4's spec review alone: (1) read `ConversationThread.tsx` directly — line 100-102
      renders `assistant.content` in a single `<p className="... whitespace-pre-wrap">`,
      exactly as documented; (2) actually ran the feature — started the real backend
      (`uvicorn main:app`) and sent a live `POST /api/chat` request with a genuine synthesis
      question ("Should I learn to code as a UX designer?"). The real raw SSE stream showed
      the model's own output containing a literal `\n\n` between the data-availability
      statement and the external-sourced judgment — exactly the mechanism the frontend
      relies on to render "two clearly separated parts" with zero markdown/rendering code,
      confirming User Flow 7b's requirement is fully satisfied by existing `whitespace-pre-wrap`
      text. This same live run also exercised a real edge case correctly: `query_requirements_data`
      returned `total_matching: 0` (no Designer/UX Designer postings have requirements
      extracted yet — expected, since the backlog hasn't run at scale in this environment),
      which correctly triggered the "don't guess from insufficient data" path (`NEEDS_EXTERNAL`
      → external search fallback) rather than fabricating a data-backed claim. **Residual
      note, not a gap**: this run proved the "insufficient internal data" branch of the
      two-part answer; the "confident internal data + judgment" branch (the more common
      case once the requirements backlog is populated) uses the identical rendering
      mechanism and needs no separate frontend verification, but will only be observable in
      practice once `GEMINI_API_KEY_REQUIREMENTS` is set and the backlog runs (see Step 5's
      outstanding flag). No frontend files changed.

## Decision Log
- 2026-08-09: Tracked against `understand-market-health-before-searching` — the outcome
  already names "skills in demand" as a success criterion; this closes that gap the same
  way the Compensation Signal change closed the salary one.
- 2026-08-09: Scoped to categories 1-6 of the user's 10-category vision, minus
  company-level and applicant-count questions (excluded per existing outcome scope and
  structural data availability respectively). Categories 7-10 (company risk, Application
  Tracker, CV matching, personalized search-funnel intelligence) explicitly deferred as a
  different product surface needing its own future outcome — discussed at length, not an
  oversight.
- 2026-08-09: Chose not to build a generic "signals" table to pre-accommodate Layoff
  Signal or other future data types speculatively — discussed explicitly as premature
  abstraction likely to guess wrong. The extensibility this change protects is
  architectural discipline (dedicated data model/adapter/query tool per signal type,
  proven three times already: sources, classification, compensation), not a shared schema.
- 2026-08-09: Revisited the per-posting cost concern that originally deferred this work —
  real production data since (changes/2026-08-04-classification-llm-call-reduction.md
  onward) shows steady-state new-posting volume (~43-115/day) is far smaller than
  originally assumed, making daily full-treatment of new arrivals plausible; the backlog
  of ~4,700+ pre-existing postings is the real cost, addressed with the same
  oldest-first/daily-budget pattern already proven for classification, not a new design.
- 2026-08-09: Flagged the IA gap (no existing term for this capability, unlike
  Compensation Signal) rather than assuming "Requirements Signal" as final — that's the
  Designer's naming call in `/new-information-architecture`, not fixed by PM triage.
