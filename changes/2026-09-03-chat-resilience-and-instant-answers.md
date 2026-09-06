---
id: chat-resilience-and-instant-answers
date: 2026-09-03
trigger-type: bug
change-type: bug-fix, ux-change, api-change, new-feature
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Chat resilience — curated instant answers + tiered free→paid model fallback

## Signal
See: `research/2026-09-03-chat-resilience-and-instant-answers.md`

Additional product-direction signal: `research/2026-09-04-market-data-stories.md`.

## Outcome
Primary: `outcomes/understand-market-health-before-searching.md`

The conversational assistant is how a professional explores demand, skills, and
salary beyond the opening chart — it directly serves *"they can identify which
roles and skills are in demand vs. declining"*, *"they can set a realistic salary
target"*, and *"less than 5 minutes to get a clear market read"*. Right now every
chat prompt fails in production, so that outcome is not being delivered at all.

Touched outcomes:
- `outcomes/llm-spend-is-bounded-and-isolated.md` — **scope change.** That outcome
  currently lists "Billing/upgrading the chat workload — chat stays on the free
  tier 'for now'; if that changes it is a new change request against this same
  outcome" as out of scope. This is that change request. Chat moves from "runs
  where a billable call cannot succeed" to "runs on its own isolated, per-day-
  capped project, free-tier first, paid only on fallback". Its per-workload
  budget-isolation criteria ("each paid workload has its own share of the
  ceiling", "adding a new LLM-using workload requires giving it its own budgeted
  share") now apply to chat.
- `outcomes/ai-provider-flexibility.md` — the tiered fallback must be an
  **explicit, ordered, named** tier list at the call site. That outcome excludes
  "automatic switching between providers/models based on price or load" — the
  fallback here is *availability* failover along a fixed declared order, triggered
  by hard quota/unavailability signals (`429 RESOURCE_EXHAUSTED`, repeated
  `503 UNAVAILABLE`), not an optimiser picking the cheapest model per request.
  Design must keep that distinction sharp (see Decision Log).

## Change Type

- `bug-fix` — chat returns `[The AI service returned an error. Please try again.]`
  on every prompt; no retry/backoff on transient `503`/`429` in the chat path
  (the classification and requirements paths already retry these); error
  classification doesn't distinguish "provider briefly overloaded" from a hard
  error; backend spec's `502` error row doesn't match the streamed-200-with-error
  reality.
- `new-feature` — a curated set of common market-health questions answered with
  **no model call at all**: the answer is built deterministically in code from
  live `query_market_data` / `query_compensation_data` / `query_requirements_data`
  results, honouring the same sourcing and honesty rules as a model answer. Goal:
  the most common questions never touch Gemini.
- `ux-change` — how the curated questions are surfaced (suggested-question set),
  and a real degraded-service state ("assistant briefly unavailable — here's what
  I can answer instantly") that routes to the curated set instead of a dead-end
  error string.
- `api-change` — tiered `LLMProvider` fallback (free-tier model → paid model on a
  dedicated project), per-tier retry/backoff, a new dedicated chat Gemini project
  + `GEMINI_API_KEY_CHAT_PAID` env var + a chat-specific daily request cap, and
  the curated-answer intent-match + answer-builder path.

## The design in principle (specs nail the details)

### 1. Curated instant-answer layer (no model call)

> Before any model call, check whether the question matches one of a curated set
> of well-understood market-health questions. If it does, answer it directly from
> the platform's own data using a deterministic, code-built response — same
> time-window statement, same proportions-not-absolutes and structured-vs-parsed
> honesty rules a model answer must follow. Only questions that *don't* match fall
> through to the model.

- **Fixed questions, live data.** The catalogue of questions is pre-authored;
  every answer is computed from *current* platform data at request time via the
  real `query_*` tools — never a stored or cached answer string. A predefined
  question asked twice a week apart gives two different, up-to-date answers.
- The curated set is a maintained catalogue (the "very well built pre-populated
  set of questions"): each entry = an intent + the query it runs + a response
  template. Surfaced to the user as a suggested-question set so the common path is
  one tap, not free typing.
- **Built to grow.** Adding a predefined question must be a cheap, repeatable
  catalogue operation (one entry, no new plumbing) — the explicit long-term goal
  is to keep expanding coverage so more and more common questions are answered
  super-fast with zero LLM call. The backend spec must make "add a question" a
  one-file change, and the catalogue's shape is a first-class part of that spec.
- The reasoning trace for a curated answer is honest: it shows the real query
  that ran and states no model was used for the answer.
- This is the primary lever for "provide as many answers as possible without
  touching the model" — it also makes chat usable even when *every* model tier is
  down.

### 2. Chat model tier — REVISED 2026-09-06: paid-only, no free tier

> **Original design** (2026-09-03): free-first, ordered `[free, paid]` tier list,
> fall through to paid only on a hard `429 RESOURCE_EXHAUSTED` / repeated `503`.
> That was built (Step 0) and verified working. **Then the stakeholder tested it
> and set a hard requirement: chat must be *fast*, and the free tier only stays if
> it can be fast.** It can't:
> - The free-tier project's `gemini-3.6-flash` quota is **20 requests/day** — with
>   up to 3 model calls per chat turn (Stages 1/2/3), that is ~6–7 chat turns per
>   day, total, across all users. It is spent within minutes of normal use.
> - Once spent, every request wastes ~8s failing the free tier twice (with backoff)
>   before falling to paid — measured live.
> - Free-tier latency is also higher and less predictable than paid (4–8s+ vs a
>   steady ~3s for a plain completion).
>
> **Decision (2026-09-06): remove the free tier from chat entirely.** Chat runs on
> the dedicated paid project only. The `GEMINI_API_KEY` free-tier key is no longer
> used by `/api/chat` (it stays in the env for now; nothing else reads it).

- Chat uses **one model tier**: `providers.gemini("gemini-3.6-flash",
  GEMINI_API_KEY_CHAT_PAID)`. No ordered tier list, no free→paid failover.
- Each model call still retries a transient `503`/`429`/timeout with a short,
  interactive backoff (2 attempts, 1s then 2s — the `llm/chat_fallback.py` pattern,
  now single-tier) before giving up.
- The paid tier is bounded by a **chat-specific daily request cap**
  (`CHAT_PAID_DAILY_REQUEST_CAP`, `chat_paid_usage` table). When the cap is reached,
  or the paid tier is genuinely unavailable after retries, chat streams the calm
  degraded message (section 4) — the curated instant-answer path (section 1) still
  works with zero model access.

### 2a. Latency reality — the curated set is the only "fast" path (added 2026-09-06)

Measured on the paid tier: a single `complete_with_tools` call for a real question
takes **9–29 seconds** (model reads the question → picks a query → waits for data →
reasons → writes the answer). A full chat turn (Stage 1 + Stage 3) is worse. This is
`gemini-3.6-flash` doing live-data tool-calling — it is the model, not the plumbing,
and no tier choice or pipeline tweak makes an LLM answer "super fast".

**Therefore section 1 (curated instant answers) is promoted from "nice to have,
slice 2" to the primary way chat meets the speed bar.** A curated question is a DB
query + a template — **sub-second, no model call**. Free-form questions that miss the
curated set still go to the paid model and still take 10–30s; that becomes the
exception, and the suggested-question set makes the fast path one tap.

### 3. Dedicated, isolated project for paid chat

- A **new Gemini project**, separate from `gen-lang-client-0963554051`
  (classification + requirements). New key `GEMINI_API_KEY_CHAT_PAID`, its own
  small prepaid balance, auto-recharge OFF.
- Satisfies `llm-spend-is-bounded-and-isolated`: a chat spike cannot drain the
  pipeline's balance and vice versa; chat has its own budgeted share.

### 4. Degraded-service UX + honest error surface

- When curated-answer doesn't match AND the paid model tier is exhausted (its
  daily cap, or genuinely unavailable after retries): stream a clear "the
  assistant is briefly unavailable, try again shortly — meanwhile here are
  questions I can answer instantly" message pointing at the curated set, not the
  flat generic error. (Revised 2026-09-06: "every model tier" → "the paid model
  tier", since there is now only one.)
- `chat.py` error classification recognises `429` / `503` / `RESOURCE_EXHAUSTED` /
  `UNAVAILABLE` as "temporarily unavailable, retry" distinct from a hard error.
- Correct the backend spec's `POST /api/chat` error table (the `502` row) to
  match the streamed-200-with-error-chunk reality.

### Not in scope

- The app-level spend ledger / single monthly $ ceiling / in-product spend panel
  still open against `llm-spend-is-bounded-and-isolated` — this CR adds a
  per-day *request* cap for chat's paid tier (pennies/day, same mechanism as the
  existing pipeline budgets), not the dollar ledger.
- Changing classification / requirements model tiers or projects.
- Provider-side project creation and balance loading (operator actions — listed
  as a prerequisite step, not software behaviour).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | ✅ reviewed — no-change (existing "<5 min clear read" / "identify roles and skills in demand" criteria already cover instant answers; no criterion changes) |
| Outcome | `outcomes/llm-spend-is-bounded-and-isolated.md` | ✅ updated 2026-09-03 — amendment note under "Success looks like" (chat → free-first + isolated capped paid fallback + zero-LLM curated path); reworded the isolation/ceiling bullets; struck the out-of-scope line that anticipated this CR |
| Outcome | `outcomes/ai-provider-flexibility.md` | ✅ updated 2026-09-03 — amendment note carving in *one* explicit form of fallback (ordered, call-site-declared tier list, advance only on hard availability signal); still excludes cost/latency routing and general cross-provider rerouting |
| Design Foundations | `design/foundations.md` | review — no-change expected (no AI-facing paradigm shift; note separately that this file still lacks the framework's "AI Involvement" section, out of scope here) |
| Information Architecture | `design/information-architecture.md` | ✅ reviewed — no-change. Per stakeholder (2026-09-03) the original design is not changing; the common questions and the transient notice live inside the existing conversational layout, no new zone/node/Task Panel item. |
| Visual Design | `design/visual-design.md` | ✅ reviewed — no-change here. Placement/styling of the offered questions and the transient "unavailable" notice is left to the frontend spec, within existing tone/tokens; revisit only if that work finds it genuinely needs a new product-wide pattern. |
| Experience Spec | `design/market-health/experience.md` | ✅ updated 2026-09-03 — **intent only, no design change** (per stakeholder). New "What we want to achieve" block (instant answers to common questions; never a dead end on a brief outage); User Flow 7c (instant answer held to the same bar); accordion notes no-model / fallback-model; 2 Interactions rows; 2 Edge Cases; 2 metrics. How it surfaces left to the frontend spec. Opening chart/summary/prompt untouched. |
| Data Stories Spec | `design/market-health/data-stories.md` | ✅ created 2026-09-04 — catalogue rules and first market-data briefing contract |
| Experience Spec | `design/ai-reasoning-panel/experience.md` | ✅ updated 2026-09-03 — minimal (`directive: high`): 2 Edge Cases in the file's existing style — answer with no model used, answer from a fallback model. No structural/visual change. |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **update** — suggested-question component, degraded-state rendering, fast-path request wiring |
| Frontend Spec | `frontend/specs/ai-reasoning-panel/architecture.md` | review — update only if the trace shape changes for curated answers |
| Backend Spec | `backend/specs/market-health/api.md` | **update** — curated-answer intent matcher + deterministic answer builders; ordered/named tiered `LLMProvider` fallback with per-tier retry/backoff; new dedicated chat project + `GEMINI_API_KEY_CHAT_PAID` + chat daily request cap; corrected `/api/chat` error surface |
| Backend Spec | `backend/specs/ai-reasoning-panel/api.md` | **update** — trace for no-model answers + model-tier provenance |
| Backend Implementation | `backend/src/` | **update** — `chat.py` (tiered call, error classification, degraded message), `llm/` (ordered-fallback helper — stays provider-agnostic), new curated-answers module, `ai_interaction_settings.py` / a budget constant for the chat paid cap, `db.py` only if the chat cap needs a counter table |
| Frontend Implementation | `frontend/src/` | **update** — suggested-question set, degraded-state UI |

## Execution Plan

- [x] **Step 0 — Priority slice 1 (acute outage).** ✅ 2026-09-04. Implemented and
  verified live against production: per-tier retry/backoff, error classification,
  degraded-service message, and the tiered fallback (active once the paid project
  exists; runs free-tier-only until then). **Root cause confirmed**: the free-tier
  project's `gemini-3.6-flash` quota is **20 requests/day**
  (`generate_content_free_tier_requests`, from Google's own `429` payload) — a
  handful of real conversations (up to 3 requests each: data-query, optional
  search-grounding, synthesis) exhausts it for the rest of the day. That is why
  chat "froze" — no hang was ever infinite, but with no retry/backoff/fallback a
  slow or quota-exhausted call had no way to resolve into anything the user could
  see. Chat now fails fast (seconds, not an indefinite wait) and always shows a
  real answer or a clear, actionable message — never silence.
- [x] **Step 1 — Outcome updates (manual edit).** ✅ 2026-09-03.
  `outcomes/llm-spend-is-bounded-and-isolated.md`: amendment note + reworded
  isolation bullets + struck the out-of-scope line this CR fulfils.
  `outcomes/ai-provider-flexibility.md`: amendment note carving in the ordered
  call-site tier list (availability failover only). `understand-market-health-
  before-searching.md`: reviewed, no-change (no success criterion moves).
- [x] **Step 2 — Design foundations review.** ✅ 2026-09-03, reviewed
  `design/foundations.md` (v1.1) — **no-change**. Suggested-question chips fit the
  paradigm's "dual-mode interaction always available" + the Principle 1 anchor
  "Aided Prompt Understanding"; the no-LLM curated-answer trace fits Principle 4
  (full inspectability). Nothing about degraded-service or the tier list conflicts.
  Separately noted: this file still lacks the framework's "AI Involvement" section
  (predates it) — out of scope for this CR, worth a dedicated pass later.
- [x] **Step 3 — `/new-experience`.** ✅ 2026-09-03. **Stakeholder was explicit:
  don't change the original design, just make the goal clear.** So the edits state
  intent and leave UI to the frontend spec:
  - `design/market-health/experience.md` — "What we want to achieve" block (two
    goals: instant answers to common questions; never a dead end on a brief
    outage); User Flow step 6 mentions offered questions; new 7c (instant answer
    held to the same honesty bar, current data, drill-down says no model);
    accordion notes no-model / fallback-model; 2 Interactions rows; 2 Edge Cases
    (transient outage, empty/small slice); 2 metrics; short "Added (2026-09-03)"
    note. No zone, no visual spec, no change to chart/summary/prompt.
  - `design/ai-reasoning-panel/experience.md` (`directive: high` — minimal,
    in-style): 2 Edge Cases — no-model answer, fallback-model answer. No
    structural or visual change.
- [x] **Step 4 — Information architecture review.** ✅ 2026-09-03 — no-change. The
  common questions and transient notice live inside the existing conversational
  layout; no new zone, node, or Task Panel item.
- [x] **Step 5 — Visual design review.** ✅ 2026-09-03 — no-change at this layer.
  Placement/styling deferred to the frontend spec within existing tone/tokens;
  reopen only if that work proves a new product-wide pattern is genuinely needed.
- [x] **Step 6 (slice 1 only — resilience) — `/new-backend-spec`.** ✅ 2026-09-04.
  Added "Chat tier fallback and retry" to `backend/specs/market-health/api.md`
  (ordered/named tiers, retry policy, `GEMINI_API_KEY_CHAT_PAID` + the
  `CHAT_PAID_DAILY_REQUEST_CAP`/`chat_paid_usage` daily cap, the confirmed 20/day
  free-tier quota) and corrected the `POST /api/chat` error table (removed the
  never-returned `502` row, explained why: SSE has already committed to `200`
  once the stream starts). `backend/specs/ai-reasoning-panel/api.md` needed no
  change — the added "answered via the backup tier" note is an ordinary
  `ReasoningStep`, not a shape change to the trace. The curated-answer engine
  part of this step is still open (slice 2).
- [x] **Step 6a — First data story contract.** ✅ 2026-09-04. Added the dedicated data-story
  catalogue and documented the deterministic API contract for `market-data-briefing` in the
  market-health backend spec.
- [x] **Step 7 (slice 1 only — degraded state) — `/new-frontend-spec`.** ✅
  2026-09-04. Added a note to `frontend/specs/market-health/architecture.md`:
  the degraded message needs no new component — it streams as an ordinary text
  chunk through the existing follow-up `AITurn` path. The suggested-question
  component is still open (slice 2, Step 10).
- [~] **Step 8 — Operator prerequisite (user).** Partially done 2026-09-06.
  ✅ New paid key created by the operator, added to local `backend/.env` as
  `GEMINI_API_KEY_CHAT_PAID`, backend restarted, and **verified working** — a
  direct `providers.gemini("gemini-3.6-flash", api_key=<paid>).complete(...)`
  authenticated and returned a completion; the free tier's daily quota had reset
  (new day) so live chat is answering on the free tier again with the paid tier
  wired and ready behind it.
  ✅ Full free→paid fallback chain proven locally 2026-09-06 (simulated free-tier
  `429` → retries → advance → paid tier streams the answer).
  ✅ (a) `GEMINI_API_KEY_CHAT_PAID` set on the Railway `api` service by the operator
  (2026-09-06) — confirmed by prod behaviour (see Step 17). ⚠️ still operator-only:
  (b) confirm the project's prepaid balance is loaded and auto-recharge is OFF;
  (c) record the GCP project id / tier in `DEPLOYMENT.md` and product `CLAUDE.md`
  (placeholders left in both). Not code — tracked in Step 11's residual list.
- [x] **Step 9 (slice 1 only — resilience) — `/implement-backend`.** ✅ 2026-09-04.
  `backend/src/llm/chat_fallback.py` (provider-agnostic `ChatTier`,
  `call_with_fallback`, `stream_with_fallback`, `is_transient_llm_error`);
  `backend/src/chat.py` (`_chat_tiers()`, all three stages routed through
  fallback, paid-tier usage recording, the degraded message, trace note);
  `backend/src/db.py` (`chat_paid_usage` table); `backend/src/ai_interaction_settings.py`
  (`CHAT_PAID_DAILY_REQUEST_CAP`). The curated-answer engine is still open
  (slice 2).
- [x] **Step 9a — First story backend slice.** ✅ 2026-09-04. Added the
  `market-data-briefing` catalogue entry, live aggregate renderer, and
  `GET /api/market-health/stories` plus `POST /api/market-health/stories/{story_id}`.
- [x] **Step 10 — `/implement-frontend`.** ✅ 2026-09-06. Superseded by Steps 16
  (chips) and 7 (degraded state needs no component — streams through the existing
  `AITurn` text path). `SuggestedQuestions.tsx` wired into `ConversationThread`
  below every task's opening turn; chip click = `append` as if typed.

### Steps added 2026-09-06 (paid-only pivot + slice 2)

- [x] **Step 12 — Outcome updates for the paid-only pivot.** ✅ 2026-09-06.
  `outcomes/llm-spend-is-bounded-and-isolated.md`: second amendment note — free
  tier removed, chat is paid-project-only, the daily request cap is the spend
  guard. `outcomes/ai-provider-flexibility.md`: walked back the 2026-09-03 tier-
  list carve-out — chat now names one `(model, key)` like every other feature;
  within-call retry stays (retry ≠ rerouting).
- [x] **Step 13 — `/new-backend-spec` (paid-only + curated engine).** ✅ 2026-09-06.
  `backend/specs/market-health/api.md`: "Chat tier fallback and retry" → "Chat
  model tier and retry" (single paid tier, no list); new "Curated instant-answer
  engine" section (`curated_answers.py` catalogue shape, conservative matcher,
  deterministic builders, honesty-parity rule, one-file-to-add rule, no-model
  trace) + `GET /api/market-health/chat-suggestions`.
- [x] **Step 14 — `/new-frontend-spec` (suggested-question chips).** ✅ 2026-09-06.
  `frontend/specs/market-health/architecture.md`: `SuggestedQuestions` component,
  placement (below the opening briefing), chip-click = `append` as if typed,
  server-owned list, render-nothing-on-empty. `design/visual-design.md`: added a
  "Suggested-question chip" aesthetic (interactive variant of the filter chip).
- [x] **Step 15 — `/implement-backend` (paid-only + curated engine).** ✅ 2026-09-06.
  New `backend/src/curated_answers.py` (6 entries: roles-in-demand, {engineer,
  designer, pm}-pay, {pm, engineer}-skills — pay builder guards implausible
  disclosed ranges). `chat.py` rewritten: curated check first → single paid
  provider → degraded message; `_chat_tiers`/`used_paid_tier` removed.
  `llm/chat_fallback.py` → single-tier `call_with_retry` / `stream_with_retry` /
  `ChatModelUnavailable`. `GET /api/market-health/chat-suggestions` in
  `market_health.py`.
- [x] **Step 16 — `/implement-frontend` (chips).** ✅ 2026-09-06.
  `frontend/src/features/market-health/SuggestedQuestions.tsx`; wired into
  `ConversationThread` (below the opening briefing) via `MarketHealthPage`'s
  `useChat` `append`. Build + `tsc` pass.
- [~] **Step 17 — Verify + deploy.** Local verification done 2026-09-06 (against
  production DB, via the `:5173` proxy):
  - Curated question → **~1s**, no model call, trace says "No language model was
    used", `chat_paid_usage` not incremented.
  - Non-curated question → paid model, ~17s, real answer, `chat_paid_usage` +2.
  - `GET /api/market-health/chat-suggestions` returns the 6 questions.
  - Pay builder's implausible-range guard fires (engineer disclosed data spans
    USD 230–555,000 → "too inconsistent to state as one band").
  **Closed 2026-09-06.** (a) `GEMINI_API_KEY_CHAT_PAID` set on the Railway `api`
  service by the operator. (b) committed + pushed (`41a8205`…`8d4c04e`, `13427e8`).
  (c) **confirmed live in prod** 2026-09-06:
  - Curated question (`POST /api/chat` "What do engineers earn?") → **0.3s**,
    trace `reasoning_steps` says "No language model was used", `generation_time_ms: 45`,
    the implausible-range guard fires on the engineer pay data.
  - Non-curated question ("backend vs frontend engineers?") → the paid model runs
    7 real `query_*` tool calls and streams an answer — proves the paid key is set
    and working on `api`.
  - `GET /api/market-health/chat-suggestions` → the 6 questions.
  (d) daily-cap-trips-cleanly is a passive observation left to real use — the
  mechanism (`chat_paid_usage` + `_model_available()`) is unit-covered and the
  degraded path is proven; not a completion blocker.
- [x] **Step 10a — First story frontend slice.** ✅ 2026-09-04. Added the suggested-story
  prompt, data-story assistant turn, live fetch, section-level empty states, and provenance
  through the existing reasoning panel.
- [~] **Step 11 — Verify against production.** Local verification done 2026-09-04–06:
  - Retry/backoff fires on a real `429 RESOURCE_EXHAUSTED` from the actual free-tier
    project; stage 1 and the synthesis stream both exhaust the free tier correctly (2026-09-04).
  - Degraded message renders in seconds (never a hang) when the tier list is fully
    exhausted (2026-09-04, before the paid key existed).
  - Paid key authenticates and returns a completion directly (2026-09-06).
  - **Full fallback chain proven** (2026-09-06): a simulated free-tier `429` → 2 retries →
    advance → the paid tier streams a real answer. `tiers that produced output: ['paid']`.
  **Closed 2026-09-06.** (a) `GEMINI_API_KEY_CHAT_PAID` is set on the Railway `api`
  service — verified by prod behaviour (non-curated chat runs paid-model tool calls;
  curated chat returns in 0.3s with a no-model trace). Slice 2 (curated engine +
  suggested-question chips) is implemented and live. Completion gate met.
  (b) the 100/day cap stopping paid calls in real use remains a passive observation —
  the enforcement code is unit-covered; not held open as a blocker.

**Residual operator bookkeeping (not code, tracked for the record):**
- Confirm the chat Gemini project's prepaid balance is loaded and auto-recharge is OFF.
- Record that project's GCP id / prepaid balance in `DEPLOYMENT.md` and product
  `CLAUDE.md` (both currently carry a "_operator to record here_" placeholder).

## Decision Log
- 2026-09-03: Triaged against `understand-market-health-before-searching` (chat is
  that outcome's conversational exploration surface, currently 100% failing in
  prod). `llm-spend-is-bounded-and-isolated` is a touched outcome with a real
  scope change — this is exactly the "new change request against this same
  outcome" its out-of-scope line anticipated for upgrading chat off the free tier.
- 2026-09-03: Change type is `bug-fix` + `new-feature` + `ux-change` +
  `api-change`, not just `bug-fix` — the curated no-model answer layer and the
  tiered paid fallback are new capabilities, so the full chain is reviewed
  (with review gates on foundations/IA/visual-design, which are expected
  no-change).
- 2026-09-03: **Free-first, paid-fallback, not paid outright.** Stakeholder:
  "if the free model is as good as the paid one, lets use it until it reach the
  limit, then lets move to paid" — and the earlier standing signal "I just want
  whatever comes for free". Paid is a capped safety net, not the default path.
- 2026-09-03: **Paid chat gets its own Gemini project**, separate from the
  classification/requirements prepaid project — stakeholder: "a separated project
  from the backend so that i can control better the cost". Satisfies
  `llm-spend-is-bounded-and-isolated`'s per-workload isolation criteria.
- 2026-09-03: **Ordered availability failover ≠ cost/load routing.** The tier list
  is fixed, declared, and named at the call site; it advances only on hard
  quota/unavailability errors after per-tier retries. This is consistent with
  `ai-provider-flexibility` (which excludes an optimiser choosing models by price
  or load), not a violation of it — to be stated explicitly in the backend spec.
- 2026-09-03: **Curated answers are deterministic, code-built, and rule-bound** —
  they run the same real `query_*` tools and must state the same time window and
  the same proportions-not-absolutes / structured-vs-parsed honesty a model answer
  must. They are not canned prose disconnected from live data (the exact failure
  mode the 2026-08-04 conversational-data-sourcing redesign removed).
- 2026-09-03: The acute outage is real now — priority slice 1 is the
  bug-fix/resilience path; the curated-answer feature is slice 2. Kept as one CR
  (one coherent change to the chat surface), sequenced via Step 0, not split.
- 2026-09-03 (stakeholder follow-up): **Quality parity across tiers** — the free
  model must be as good as the paid one; the fallback is availability-only, not a
  quality downgrade. To be verified against the actual Gemini line-up in the
  backend spec, not assumed.
- 2026-09-03 (stakeholder follow-up): **Do not redesign the experience — state the
  goal.** The original conversational design stands. The experience spec change is
  an intent statement (instant answers to common questions; never a dead end on a
  brief outage) plus the honesty bar those answers must meet; how they surface is
  the frontend spec's job. IA and visual design: reviewed, no-change.
- 2026-09-03 (stakeholder follow-up): **Predefined = fixed questions, live data.**
  Answers are always computed from current platform data at request time, never
  stored. The catalogue is built to grow continuously — adding a question is a
  one-entry change — with the explicit goal of covering as many common questions
  as possible with the zero-LLM path over time.
- 2026-09-04: **Reopened for Step 0 (user report: "chat is frozen, no answer").**
  Reproduced directly: 4 manual chat requests over a few minutes showed increasing
  latency (23s, 38s with the reply cut off mid-word) before a 5th failed outright.
  Backend logs pinpointed the exact cause: `429 RESOURCE_EXHAUSTED` — the free-tier
  project's `gemini-3.6-flash` allows only **20 requests/day**
  (`generate_content_free_tier_requests`). With zero retry/backoff/fallback in the
  code at the time, a slow or quota-exhausted call had no way to resolve into
  anything visible — that is the "frozen" the user saw. This is exactly the acute
  outage Step 0 already described; only Step 0 (resilience) was executed now, not
  the full CR — Steps 8 (operator) and 11 (full production verification with a
  real paid tier) remain, and slice 2 (curated-answer engine, suggested-question
  UI) is unchanged.
- 2026-09-04: **Paid tier uses the identical model as the free tier**
  (`gemini-3.6-flash`), just a different project/key — the simplest way to
  satisfy "quality parity across tiers" by construction rather than by
  comparing two different models' output quality. Revisit only if the free
  project's model lineup ever diverges from what a paid project offers.
- 2026-09-04: **Chat's retry policy is deliberately much shorter than the batch
  pipeline's** (2 attempts, 1s/2s backoff vs. `requirements.py`'s 5 attempts at
  60s) — a live user is waiting; the batch pipeline runs unattended overnight.
  Same transient-error detection approach (string-matching known Gemini/HTTP
  signals — see `llm/chat_fallback.py::is_transient_llm_error`), different
  timing, per the CR's "reuse the pattern, not the code" instruction.
- **2026-09-06 (stakeholder, after testing): remove the free tier — paid-only.**
  "I need speed, i need 20 chats a day free, but it has to be super fast, if not
  we remove the free tier." The free tier cannot be fast: 20 requests/day hard
  cap (~6 chat turns), higher and less predictable latency than paid, and ~8s
  wasted per request retrying it once it's spent. This reverses the 2026-09-03
  "free-first" decision. Chat now runs on `GEMINI_API_KEY_CHAT_PAID` only; the
  daily request cap (`CHAT_PAID_DAILY_REQUEST_CAP`) is the spend guard.
  `ai-provider-flexibility` is *more* satisfied, not less — there is now exactly
  one explicitly-named model at the call site and zero automatic switching.
- **2026-09-06: an LLM chat answer is inherently 10–30s** on `gemini-3.6-flash`
  with live-data tool-calling (measured on the paid tier: 9s / 12s / 29s for
  three real questions). No tier or pipeline change makes it "super fast". The
  **curated instant-answer set (section 1) is the only sub-second path** and is
  therefore promoted from slice 2 to a co-priority of this pivot — a curated
  question is a DB query + a template, no model call. Free-form misses still use
  the paid model at 10–30s; the suggested-question chips make the fast path the
  default action.
