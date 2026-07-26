---
id: chat-data-sourcing-and-scheduled-classification-agent
date: 2026-07-22
trigger-type: internal
change-type: ux-change, api-change, technical-refactor
outcome: understand-market-health-before-searching, ai-reasoning-transparency
status: complete
---

# Change Request: Chat data sourcing/attribution fix + scheduled classification agent

## Signal
See: `research/2026-07-22-chat-data-sourcing-and-scheduled-classification-agent.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` and
`outcomes/ai-reasoning-transparency.md`

The chat fix directly serves `ai-reasoning-transparency`'s success criteria — "users can see
which data sources... the AI consulted for any given response" — which chat currently violates
by citing a fabricated source. Both halves of this change serve
`understand-market-health-before-searching`: the outcome depends on real, current data, and
today chat still answers from mock data while the pipeline that keeps the chart's data current
is manually triggered rather than reliable. No change to either outcome's scope or success
criteria — this is how both outcomes get served correctly rather than partially.

## Change Type
`ux-change` — chat's response behavior changes (when to use real data vs. general knowledge,
always attributing which is which). `api-change` — `/api/chat`'s context-injection logic is
rewritten to source real classified data instead of mock data, and new backend business logic
(run summaries, anomaly flagging) is added to the ingestion pipeline. `technical-refactor` —
the ingestion pipeline moves from manually-triggered-locally to a scheduled Railway service
with its own dedicated API key.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Outcome | `outcomes/ai-reasoning-transparency.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | update — chat sourcing/attribution rule: real data when the question is answerable from it, general knowledge otherwise, always explicitly attributed; reuse existing provenance/accordion patterns rather than inventing new UI |
| Backend Spec | `backend/specs/market-health/api.md` | update — (1) rewrite `/api/chat` context-injection to source real classified data instead of `mock_data.py`, with attribution instructions in the system prompt; (2) add scheduled-agent business logic: dedicated classification API key, structured run-summary record, anomaly-flagging rules, Railway cron deployment |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | review — update only if attribution needs more than streamed markdown text in the existing chat message component |
| Backend Implementation | `backend/src/` | update — after backend spec is finalized |
| Frontend Implementation | `frontend/src/` | update — only if the frontend spec's contract changes require it |

## Execution Plan

- [x] Step 1: `/new-experience` — update `design/market-health/experience.md` (chat sourcing/attribution rule)
- [x] Step 2: `/new-backend-spec` — update `backend/specs/market-health/api.md` (chat context-injection rewrite + scheduled-agent business logic)
- [x] Step 3: `/new-frontend-spec` — review `frontend/specs/market-health/architecture.md`; update only if needed. Reviewed — no changes needed, see that file's "Reviewed 2026-07-22" note in its API Contract section.
- [x] Step 4: `/implement-backend` — chat.py real-data context injection + attribution prompt; wire `GEMINI_API_KEY_CLASSIFICATION`; run-summary + anomaly-flagging in `ingest.py`; Railway deployment config
- [x] Step 5: `/implement-frontend` — not needed (frontend spec review found no contract change)

## Decision Log
- 2026-07-22: Tracked against both `understand-market-health-before-searching` and
  `ai-reasoning-transparency` rather than one — confirmed with user. The chat fix is a direct
  instance of the transparency outcome's success criteria; both halves of this change ultimately
  serve the market-health outcome's dependency on real, current data.
- 2026-07-22: Classified as `ux-change` + `api-change` + `technical-refactor` rather than
  `new-feature` — chat and the ingestion pipeline both already exist; this corrects/hardens
  their behavior rather than introducing new user-facing surface. The agent's run-summary and
  anomaly-flagging are new backend capabilities but ops-facing, not user-facing — no new
  frontend surface requested, so scoped as `api-change` rather than `new-feature` (which would
  pull in the full outcome→foundations→experience→IA→visual-design cascade unnecessarily).
- 2026-07-22: Scheduled-agent scope agreed during planning discussion: daily Railway cron job,
  dedicated `GEMINI_API_KEY_CLASSIFICATION` (already created, saved to `backend/.env`, not yet
  wired into code) separate from chat's key so the two never compete for the same quota.
  "Agent" here means tool-use + one delegated reasoning step (classification) within
  user-set constraints (the closed taxonomy) — not autonomous decision-making about what to do.
  Matches `design/foundations.md` Principle 1 (Intent First, Always Explicit).
- 2026-07-22: In scope for "agent" behavior: structured run summaries (inspectable outcome per
  run, not just ephemeral logs) and basic anomaly flagging (zero results from a term, abnormal
  `other` rate). Explicitly out of scope: autonomous taxonomy-change suggestions — deferred
  until there's real run history to build thresholds against. If ever built, must propose
  changes for human review, never edit `job-classification.md` directly.
- 2026-07-22: Chat sourcing rule clarified by user: not "only ever use our data" and not "ignore
  our data" — scope-based. Real data when the question is answerable from it, model's own
  knowledge when it isn't, always explicitly attributed which is which. Never repeat the
  fabricated-source-citation bug found during testing (chat cited "LinkedIn job postings" for
  what was actually synthetic mock data).
- 2026-07-22: Sourcing rule refined further, superseding the entry above — user gave concrete
  examples ("is UX Designer or Product Designer more in demand", "which skills are in demand
  for frontend developers") that clarified the intent is stricter than "general knowledge is
  fine": (1) the LLM should have real query/analysis access to the database per-question, not a
  fixed pre-computed context blob — genuine tool use, not a canned summary; every data-grounded
  answer states its time window relative to when live collection actually began. (2) For
  anything the data can't cover, "general knowledge" is not good enough — the model must ground
  the claim in a real, citable external source (article, report, study) or say it doesn't have
  one. Decided: wire up Gemini's native Google Search grounding tool for this, rather than
  prompting for citations the model can't verify — asking an ungrounded model to "always cite a
  source" reliably produces fabricated citations, which is a worse version of the exact bug this
  change exists to fix. This is new infrastructure (and additional API cost/quota), not a prompt
  change. (3) "Which skills are in demand" was explicitly confirmed as illustrative of the
  principle, not a literal near-term feature — skills extraction from posting content is a
  separate future data capability, out of scope here. (4) The detailed *how* (queries run,
  searches made) belongs in the accordion drill-down; the *source* (platform data vs. external)
  always shows in the visible answer regardless of whether the user drills down.
- 2026-07-22: `design/market-health/experience.md` updated (User Flow, accordion Sources
  content, Interactions, Edge Cases, Open Questions) to reflect the refined rule above. Flagged
  but did not resolve a pre-existing naming drift between this spec's own "Thinking process
  accordion" and the product-wide "Reasoning Panel" component in
  `design/ai-reasoning-panel/experience.md` — reconciliation is its own future change request.
- 2026-07-22: `backend/specs/market-health/api.md` updated. Chat data sourcing designed as two
  tools with a fixed order: `query_market_data` (read-only parameterised query over
  `raw_postings`/`classifications`, always tried first, returns `data_range` so the model can
  detect out-of-window questions) then, only if that can't answer the question, a *separate*
  model call with Google Search grounding enabled — not combined in one call, since current
  Gemini API versions don't support mixing custom function tools with search grounding.
  Documented that this breaks `ai-reasoning-panel/api.md`'s "trace assembled pre-LLM" premise
  for `/api/chat` specifically (sources are now built from actual tool calls, not pre-computed)
  — noted, not fixed there, since that spec is out of this change's scope. Added `IngestionRun`
  data model (every run recorded, including failures, with concrete anomaly-flagging thresholds:
  zero-result term with prior nonzero history, `other` rate deviating >50%/15pp from a 5-run
  trailing average). Specified two required `LLMProvider` protocol extensions: explicit API key
  per call, and tool-enabled calls — neither exists today. Railway deployment decided
  concretely: cron-scheduled service in the same project as the database, using Railway's
  internal network URL for Postgres, `railway.json` for the cron schedule.
- 2026-07-22: `frontend/specs/market-health/architecture.md` reviewed, no changes made — the
  backend's new tools are entirely server-side, the reasoning-trace `SourceAccess` shape is
  unchanged (new source types just populate existing fields), and citations render as plain
  markdown within `AIMessage`'s existing rendering. Noted the review directly in that spec
  rather than leaving Step 3 looking skipped.
- 2026-07-22: Implemented and verified live against the real API (not just written blind).
  New files: `market_query.py` (`query_market_data` tool), `ingestion_runs.py` (recording +
  anomaly detection), `backend/railway.json` (cron deployment config). Extended
  `llm/base.py`/`llm/gemini.py`/`llm/providers.py` with an explicit `api_key` parameter and two
  new protocol methods, `complete_with_tools` and `complete_with_search_grounding`. Rewrote
  `chat.py` around three stages: query the platform's data (tool-enabled call) → search
  grounding only if that can't answer → a final streamed synthesis call, wire format unchanged.
  `classify_postings` now returns stats and stops gracefully on an exhausted rate limit instead
  of crashing the whole run — the exact failure mode hit repeatedly earlier this session.
  Real bugs found and fixed through live testing, not caught by writing the spec or code alone:
  - `from __future__ import annotations` in `market_query.py` broke the Gemini SDK's runtime
    type introspection for automatic function calling (`isinstance() arg 2 must be a type...`)
    — removed from that file. `chat.py`/`gemini.py` keeping it is fine; only the module
    defining the tool function itself is affected.
  - The model naturally wants to pass multiple values when comparing categories (e.g. "UX
    Designer" vs "Product Designer" in one call) — `query_market_data`'s filter parameters were
    redesigned from scalar `str | None` to `list[str] | None` to match, rather than fighting it.
  - The SDK wraps a tool's return value as `{"result": ...}` (or `{"error": ...}` on failure) —
    initially missed, causing the reasoning trace to show "Found 0 matching postings, data
    available from None to None" even when the actual answer was correct (the final synthesis
    call used the model's own text, not the mis-parsed structured result, so only the trace was
    wrong, not the answer users saw). Fixed by unwrapping in `gemini.py`.
  Verified end-to-end via the real HTTP endpoint (not just internal function calls): correct
  tool-based answers for in-data questions, correct search-grounded answers with real cited
  sources for out-of-data questions, and confirmed the trend chart (`/openings`) and
  `/api/chat/context` debug endpoint — both untouched by this change — still work.
  **Not done, requires the user's own Railway account access**: actually creating the Railway
  service, connecting the repo, setting its root directory to `backend/`, and configuring
  `ADZUNA_APP_ID`/`ADZUNA_APP_KEY`/`GEMINI_API_KEY_CLASSIFICATION`/`DATABASE_URL` (internal
  network URL) in the dashboard. `railway.json` is ready for that service once created.
  Also discovered during testing: chat's own `GEMINI_API_KEY` hit the same free-tier daily
  limit from live-testing volume alone — confirms the dedicated classification key was the
  right call, and that heavy manual chat testing has the same real budget constraint.
- 2026-07-25: **Severe fabrication bug found by the user in real use, post-implementation** —
  a multi-turn conversation ("breakdown by category" → "yes please") produced a completely
  fabricated category breakdown (invented category names like "Data Science," "Cloud
  Engineering," "Cybersecurity" that don't exist anywhere in `job-classification.md`, with
  invented numbers), and when questioned, the system fabricated a *second* layer of false
  justification for its own hallucination rather than admitting it. Root cause: Stage 1/2 only
  ever received the latest message, never conversation history, so a context-dependent
  follow-up like "yes please" was meaningless to them — and the model fabricated rather than
  admitting it didn't understand, despite the system prompt instructing it not to.
  Fixed with four changes, all now live and re-tested against the exact failure scenario
  (confirmed clean — real categories, and "yes please" now correctly recognized as already
  answered rather than fabricated):
  1. Bounded conversation-history windows for all three stages (not full history — cost
     grows with conversation length on a stateless API) — new `ai_interaction_settings.py`
     (the single source of truth for the actual numbers) and `AI_INTERACTION_SETTINGS.md`
     (human-facing explanation of why, referenced from this product's `CLAUDE.md` so it's
     surfaced to any future session touching `/api/chat`) — deliberately kept the exact
     numbers out of the `.md` so the two documents can't drift apart, the same drift problem
     surfaced repeatedly earlier in this session.
  2. Code-level anti-fabrication guard: zero tool calls + no `NEEDS_EXTERNAL` marker means the
     text is discarded outright, never trusted, since prompt instructions alone proved
     insufficient.
  3. Stage 3 synthesis grounded in the raw `query_market_data` return values directly, not
     just Stage 1's prose summary of them.
  4. Current date injected into Stage 1's system prompt (a smaller bug found in the same
     transcript — "today" confused the model outright).
  Updated `backend/specs/market-health/api.md` — Business Logic — Conversational data sourcing
  to document all four as the spec's actual behavior, not just a code comment.
