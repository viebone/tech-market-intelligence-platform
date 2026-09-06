---
id: chat-answer-truncation-and-curated-match
date: 2026-09-06
trigger-type: bug
change-type: bug-fix, ux-change, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: A fluent chat conversation, answered only from platform data

## Signal

See: `research/2026-09-06-chat-answer-truncation-and-curated-match.md`

Stakeholder hit it live: asked "What skills are more in demand for product managers?", got an
answer that stopped mid-sentence with no error ("the system freeze there"). In refining the
fix the stakeholder set the direction:

> "what we need to make sure that we get a fluent conversation."
> "we don't want answers which are not based on our own data. avoid any kind of information
> that is not in our db."
> "If the user ask 'should I learn Rust?' then the system should analyse all the jobs skills
> required and provide an answer... we should have the backend ready to run these kind of
> questions and provide answers, because this is exactly what people will ask."

## Outcome

`outcomes/understand-market-health-before-searching.md` — chat is the outcome's conversational
exploration surface ("identify which roles and skills are in demand", "less than 5 minutes to
get a clear market read"). A truncated answer, a needlessly slow one, or one that quietly
leaves the platform's data for the open web all fail that outcome. No success criterion
changes.

Also serves `outcomes/ai-reasoning-transparency.md` — "users can see which data sources the
AI consulted". A chat that only ever consults the platform's own data is trivially, fully
inspectable; removing the external path makes every answer traceable to a specific owned-data
query.

## What "fluent conversation" means here (acceptance criteria)

1. **Complete** — an answer never stops mid-sentence. If the model is cut off, it is finished
   or the user is told plainly; never a dangling fragment with a normal "done" signal.
2. **Grounded** — every answer is composed **only** from the platform's own database
   (`query_market_data`, `query_compensation_data`, `query_requirements_data`). No web search,
   no model general knowledge, no blended answers. A question the data cannot touch gets a
   plain "that's not in the platform's data" plus what it *can* answer — never an outside
   answer.
4. **Willing** — open-ended and judgment questions ("should I learn Rust?", "is now a good
   time for PMs?") are answered *from the data*: the model queries the relevant slice and
   reasons from it (data first, then judgment built on that data), and only declines when the
   data genuinely holds nothing relevant or the sample is too small.
5. **Responsive** — common questions take the sub-second curated path even when phrased
   naturally, not only near-verbatim. Other answers are conversational length (a few
   sentences / a short list), not a multi-section report — faster to read, less likely to
   hit a limit.
6. **Continuous** — follow-ups in the same task keep context (the bounded windows already
   handle this — verify, don't regress).
7. **Provider-independent** — every rule above is a *product* rule, enforced above the
   provider line. Swapping Gemini for another LLM must not change grounding, completeness,
   length, or willingness. Nothing about "a fluent, data-only conversation" may live in a
   Gemini-specific file.

## Change Type

- `bug-fix` — the truncated stream and the curated-match miss both violate what specs already
  say ("never silence"; "common questions take the no-model path").
- `ux-change` — chat stops reaching outside the platform's data. Questions it can't answer
  from the data get a plain, redirecting reply instead of a web-researched one. This changes
  what the assistant does and how several User Flows / Edge Cases read.
- `api-change` — remove the external search-grounding stage; strengthen the data stages so a
  judgment question is answered from the data; synthesis token budget + incomplete-finish
  handling; a `raw_skill` filter on `query_requirements_data` so "is X in demand?" is a
  direct query; widen the curated matcher.

## Root Cause (the two bugs)

1. **`GeminiAdapter.stream()`** (`backend/src/llm/gemini.py`): `max_output_tokens=1024` (vs.
   `8192` elsewhere) and no `thinking_config`. `gemini-3.6-flash` spends budget on invisible
   reasoning then truncates at `MAX_TOKENS`; `stream()` yields only `chunk.text` and never
   reads the finish reason; `chat.py` Stage 3 treats a clean iterator end as success.
2. **`curated_answers.match()`** (`backend/src/curated_answers.py`): substring-only against a
   short phrasing list — natural rewordings miss.

## The redesign (DB-only chat)

- **Remove Stage 2.** Delete `_search_external_sources`, the `complete_with_search_grounding`
  call path from chat, and the `NEEDS_EXTERNAL` escape hatch. `gemini.py`'s
  `complete_with_search_grounding` may stay as an unused capability or be removed — decide in
  the backend spec.
- **Stage 1 always attempts a data answer.** The data-stage system prompt is rewritten: map
  the question onto the available queries (including `raw_skill` for specific technologies),
  never bail to "I can't". Only emit a "not covered" result when the data genuinely has
  nothing — and even then, name the nearest thing the data *can* speak to.
- **Stage 3 synthesises a concise, conversational, data-only answer.** Keep the data-then-
  judgment split for judgment questions. Drop all "external source" / "blend / attribute
  separately" language. Add length/tone guidance. Give it a real output budget (target
  ~2–3k tokens, not 1024, not 8192) and a bounded thinking budget. Detect a non-`STOP`
  finish and continue the generation once, or append a clear "…(cut off — ask me to
  continue)" line.
- **Curated matcher** recognises ordinary rephrasings (widen phrasings + a more forgiving
  match rule, e.g. keyword/token overlap with a confidence floor), still conservative enough
  that a wrong instant answer never fires.

Latency: removing Stage 2 already drops a model call for questions that used to trigger it.
Collapsing Stage 1+3 into one streamed call is **out of scope here** — noted as a possible
follow-up.

### Keeping it provider-independent (stakeholder, 2026-09-06)

> "I don't want this kind of principles specific to one AI like gemini, it should be something
> that persist even when I change the llm."

The grounding / completeness / length rules are enforced in `chat.py` and the system prompts
it builds — already provider-neutral. The gap is the streaming contract: `LLMProvider.stream()`
returns a bare `AsyncIterator[str]`, so today "make the answer complete, not truncated" can
only be done with Gemini-specific knobs (`max_output_tokens`, `thinking_config`, reading
`finish_reason`). Fix the contract, the same way `BatchState` already normalises batch state:

- `LLMProvider.stream()` (and `complete()`) take a provider-neutral `max_output_tokens: int | None`.
  Each adapter translates; the **value** (chat's conversational budget) is an app-layer
  constant, not in any adapter.
- The stream exposes a **normalised stop reason** — `"complete" | "truncated" | "filtered" |
  "error"` — every adapter maps its provider's own finish enum onto exactly those, and
  `chat.py` acts on the neutral value. No provider's raw `finish_reason` crosses the boundary
  (exact mechanism — trailing marker vs. returned object — decided in the backend spec).
- "Managing internal reasoning tokens so they don't starve the visible answer" is an adapter
  *quality bar*, not a chat concern — each adapter owns a sane default for its own model.
- `complete_with_search_grounding` (+ `GroundedResponse` / `GroundingSource`) removed from
  the `LLMProvider` protocol and the Gemini adapter — not kept dormant (see Decision Log).
  "DB-only" is a property of the chat pipeline's shape, not of a provider flag.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Outcome | `outcomes/ai-reasoning-transparency.md` | no-change — better served; note only |
| Outcome | `outcomes/ai-provider-flexibility.md` | **update** — amendment note: the provider contract now also normalises the streaming stop reason and carries a provider-neutral output bound, so a conversation's behavioural guarantees (complete, bounded, data-only) survive a provider swap — an extension of "the frontend contract is unchanged regardless of which provider is active" to the behavioural contract |
| LLM abstraction | `backend/src/llm/base.py` | **update** — `stream()`/`complete()` gain `max_output_tokens`; a normalised stream stop-reason type (sibling of `BatchState`) |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | review — it references external sources in the reasoning model; update if it implies chat *has* web search |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | **update** — remove/rewrite User Flow 7a (external) and the external-source Edge Cases; new framing "every answer from the platform's data; uncovered questions get a plain redirect, never an outside answer"; judgment questions answered from the data; incomplete-answer Edge Case; curated-matching note; conversational length |
| Experience Spec | `design/ai-reasoning-panel/experience.md` | **update** — the "fallback model" / external-tool Edge Cases; trace no longer lists external tools |
| Design | `design/market-health/data-stories.md`, `design/market-health/provenance-panel.md` | review — small edits where they mention external sources |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | **update** — remove external-source rendering expectations; confirm truncation marker needs no new component |
| Frontend Spec | `frontend/specs/ai-reasoning-panel/architecture.md` | review — reasoning panel no longer needs an external-tool branch |
| Backend Spec | `backend/specs/market-health/api.md` | **update** — remove the search-grounding stage; rewrite "Conversational data sourcing" (always attempt data; judgment-from-data); synthesis token budget + incomplete-finish handling; `raw_skill` filter; curated matcher |
| Backend Spec | `backend/specs/ai-reasoning-panel/api.md` | **update** — trace shape drops external-tool entries |
| Backend Impl | `backend/src/llm/base.py` (contract), `backend/src/llm/gemini.py` (adapter translates), `backend/src/chat.py`, `backend/src/market_query.py`, `backend/src/curated_answers.py` | update |
| Frontend Impl | `frontend/src/` | update only if the reasoning panel special-cases external sources |

## Execution Plan

- [x] Step 1: Read the full chain for the chat surface (2026-09-06). External-source
      touchpoints identified:
      - `design/market-health/experience.md` — User Flow step 6 (example "What was demand
        like in 2019?"), **step 7** (the core: "answers from real external sources it can
        point to… never blended"), step 7b (synthesis — KEEP, this is the "should I learn X"
        path), accordion "Sources" ("what… was searched externally"), Interactions row "Ask a
        question… that reaches outside the platform's data", Edge Cases "Question reaches
        outside the platform's data" / "Answer blends platform data and an external source" /
        part of "A claim would need a source". Also a stale accordion line ("if the assistant
        fell back to a secondary model, it names that model" — the tier list was removed
        2026-09-06) and a garbled Edge Case near line 500-502.
      - `design/ai-reasoning-panel/experience.md` (`directive: high`) — "Answer composed by a
        fallback model" edge case is stale; "No external tools used" placeholder stays (now
        always true for chat).
      - `backend/specs/market-health/api.md` — "Conversational data sourcing" step **2**
        (Google Search grounding) and step 3's "which parts came from which"; the
        anti-fabrication guard keys on the `NEEDS_EXTERNAL` marker; "Chat model tier" names a
        "Stage 2 search grounding"; trace section mentions "any Google Search grounding call".
        Tech Decisions line ~1318 (Google Search grounding capability) and ~1649 (two call
        modes: function tool vs. search grounding).
      - `backend/src/chat.py` — `_search_external_sources`, `_SEARCH_STAGE_SYSTEM`,
        `_needs_external`, `_query_platform_data`'s `NEEDS_EXTERNAL` prompt, Stage 2 block in
        `_stream_response`, `_build_synthesis_system`'s external-source sections.
      - `backend/src/llm/gemini.py` — `stream()` `max_output_tokens=1024`, no thinking config;
        `complete_with_search_grounding`.
      - `backend/src/llm/base.py` — `stream()` returns bare `AsyncIterator[str]`;
        `complete_with_search_grounding` in the protocol; `GroundedResponse`/`GroundingSource`.
      - `backend/src/market_query.py` — `query_requirements_data` returns `raw_skills` but has
        no `raw_skill` *filter*.
      - `backend/src/curated_answers.py` — `match()` substring-only.
- [x] Step 2: `/new-experience` (2026-09-06) —
      - `design/market-health/experience.md`: User Flow 7 rewritten (data-only, no external);
        7b tightened (judgment reasons *from* the data); "What we want to achieve" reframed as
        4 goals (instant + natural phrasing / data-only / always finishes / never a dead end);
        accordion Sources + Context sections de-external-ised; stale "secondary model" line
        removed; Interactions row rewritten + a truncation row added; Edge Cases — garbled
        bullet split and fixed, external-source bullets replaced with "we don't track that"
        redirect + a new "incomplete model answer" bullet; a "Revised 2026-09-06" note added.
      - `design/ai-reasoning-panel/experience.md`: "Answer composed by a fallback model" edge
        case removed (stale); "Answer was cut short" edge case added; `updated` bumped.
      - `design/market-health/provenance-panel.md`: intro line — no external service to
        disclose for chat.
      - `design/information-architecture.md`: "Source" taxonomy entry — chat consults only
        owned-data queries, not the open web.
      - `design/market-health/data-stories.md`: reviewed — its two "no external search"
        lines already state the DB-only rule; no change.
- [x] Step 3a: `outcomes/ai-provider-flexibility.md` (2026-09-06) — "Extended 2026-09-06"
      amendment: the streaming contract normalises the stop reason (`complete`/`truncated`/
      `filtered`/`error`) and carries a provider-neutral `max_output_tokens`, the same
      normalise-onto-a-fixed-set pattern `BatchProvider` uses. Lets "a chat answer always
      finishes, built only from platform data" survive a model swap.
- [x] Step 3: `/new-backend-spec` (2026-09-06) —
      - `backend/specs/market-health/api.md`: DB-only note added to Conversational data
        sourcing; step 2 (Google Search grounding) removed, step 3 rewritten (always attempt
        data, `NO_DATA:` marker replaces `NEEDS_EXTERNAL`, judgment-from-data); new
        "Provider-neutral streaming contract" block (max_output_tokens, normalised stop
        reason, chat acts on `truncated`); curated matcher rewritten (content-word overlap,
        widened phrasings + per-phrasing tests); `raw_skill` filter added to
        `query_requirements_data`; anti-fabrication guard + reasoning-trace + `POST /api/chat`
        purpose + Tech Decisions (protocol extensions, External Dependencies row) all updated;
        `complete_with_search_grounding` kept as dormant-or-remove decision for implement.
      - `backend/specs/ai-reasoning-panel/api.md`: chat traces carry no external entries;
        truncated answers marked in the final reasoning step + no clean `finishReason: "stop"`.
- [x] Step 4: `/new-frontend-spec` (2026-09-06) — `frontend/specs/market-health/architecture.md`
      gets a "Reviewed 2026-09-06" note: **no frontend change needed** (web-search removal is
      server-side; the "cut off" marker is plain appended text on the existing
      `whitespace-pre-wrap` path; reasoning-panel truncated step rides the generic
      `reasoning_steps` rendering; `SuggestedQuestions` untouched).
      `frontend/specs/ai-reasoning-panel/architecture.md` — reviewed, no change (the
      `source_type` union and "no external tools" placeholder are already generic).
- [x] Step 5: `/implement-backend` (2026-09-06) —
      - `llm/base.py`: `StreamStop` + `StreamOutcome`; `stream()`/`complete()` take
        `max_output_tokens`; `GroundingSource`/`GroundedResponse`/`complete_with_search_grounding`
        **removed from the protocol** (not kept dormant).
      - `llm/gemini.py`: `stream()` honours `max_output_tokens` (default 2048, was hard 1024),
        thinking budget pinned to 1, `_GEMINI_FINISH_MAP` (`finish_reason` → `StreamStop`) +
        `_finish_reason_name()`; `complete()` takes `max_output_tokens`;
        `complete_with_search_grounding` removed.
      - `chat.py`: Stage 2 / `_search_external_sources` / `_SEARCH_STAGE_SYSTEM` /
        `_needs_external` deleted; `NEEDS_EXTERNAL` → `NO_DATA:`; data + synthesis prompts
        rewritten (DB-only, concise/no headings, judgment-from-data); Stage 3 passes
        `CHAT_SYNTHESIS_MAX_OUTPUT_TOKENS` + a `StreamOutcome`, and on a non-`complete` stop
        appends a plain marker, sets `finishReason` (`length`/`content-filter`/`error`, never
        a false `stop`) and re-emits the trace with `truncated=True`; bare-error path now uses
        the calm degraded message.
      - `market_query.py`: `raw_skill` list filter on `query_requirements_data` (ILIKE
        substring `EXISTS` against `posting_skills`, scopes every count + `total_matching`).
      - `curated_answers.py`: content-word-overlap matcher (stopwords + singularise +
        ≥75%/≥2-word + clear-winner); substring fast path tightened to ≥60% of the message;
        ~2× more `match_phrasings` per entry.
      - `ai_interaction_settings.py`: `CHAT_SYNTHESIS_MAX_OUTPUT_TOKENS = 2048`; stale
        free-tier / "Stage 2" comments corrected.
      - `backend/tests/test_curated_match.py` (new — repo had no test infra): 4 assert tests,
        run directly or via pytest. All pass.
      - Docs: `backend/AI_INTERACTION_SETTINGS.md`, product `CLAUDE.md`.
      Two follow-up fixes in the same pass: (a) `_MIN_MSG_COVERAGE` — a matched phrasing must
      also cover ≥50% of the message's content words, so "engineer skill" no longer captures
      a long comparison question; (b) `raw_skill` EXISTS referenced `pr.posting_id` but the
      languages sub-query has no `posting_requirements` join → `UndefinedTable`; changed to
      `rp.id`. Both verified.
      **Local verification (backend on the prod DB):** curated rephrasing → curated path,
      no model; "compare backend vs frontend" → complete multi-part answer,
      `finishReason: stop` (previously truncated at 1024); "compare security vs ML engineers"
      → routed to the model, real per-specialization data (not the generic curated list);
      "should I learn Rust?" → `raw_skill`-filtered "84 of 2,259 Engineer postings" + a
      data-then-judgment answer; "market in 2019?" → "I do not have data for 2019… I can
      answer…", no fabrication.
- [x] Step 6: `/implement-frontend` — none needed (Step 4).
- [x] Step 7: **Verified in production** 2026-09-06 (deploy `bcf1a398`, commit `7c5f73f`):
      - "What skills are more in demand for product managers?" → curated instant path,
        "No language model was used" (the reported bug — fixed).
      - "Compare demand and required skills for security engineers versus ML engineers" →
        routed to the model with real per-specialization data, not the generic curated list.
      - "Should I learn Rust as an engineer?" → `query_requirements_data({'raw_skill': ['Rust'],
        'role_category': ['Engineer']})` → "Found 84 matching postings" → a data-then-judgment
        answer, `finishReason: stop`, no web content.
      - "What was the tech job market like in 2019?" → "The platform does not have historical
        job market data from 2019…" + answerable-question suggestions. No fabrication.
      - Long multi-part answers complete (`finishReason: stop`) instead of truncating at 1024.
- [x] Step 8: **Complete** — every box checked; specs match the shipped code.

## Decision Log

- 2026-09-06: Started as a two-bug `bug-fix`; the stakeholder's refinement ("only our own
  data", "no information that is not in our db", "backend ready to run 'should I learn X'
  questions") makes it a direction change for chat. Rescoped to `bug-fix` + `ux-change` +
  `api-change`, full chain reviewed.
- 2026-09-06: **No outcome promises external-source answers.** `ai-reasoning-transparency`
  only requires the trace to *show* what was consulted; "no external tools were used" is a
  valid, in fact stronger, trace. So removing web search is an owner design decision, not an
  outcome walk-back.
- 2026-09-06: **DB-only, but still willing.** "Should I learn Rust?" is answered by querying
  skill data, not by declining — the tools already support this (`query_requirements_data`
  returns raw-skill frequencies; docstring already anticipates "should I learn X"). The fix
  is to stop the model bailing to web search and to add a direct `raw_skill` filter.
- 2026-09-06: Collapsing Stage 1 + Stage 3 into one streamed call (bigger latency win) is
  deliberately deferred — removing Stage 2 is the safe latency gain now.
- 2026-09-06: **Provider-independence (stakeholder).** The fluency rules must survive an LLM
  swap. They already live in `chat.py`; the one leak is the streaming contract, so `base.py`
  gains a normalised stop reason + a neutral output bound — same "adapters map onto a fixed
  set, the pipeline never sees a raw provider enum" pattern `BatchState` already uses.
  Governed by `ai-provider-flexibility` (extends "frontend contract unchanged across
  providers" to the behavioural contract). "DB-only" is structural — the chat pipeline has no
  grounding stage — not a provider flag.
- 2026-09-06: Both original bugs confirmed by reproduction before writing (prod stream cut
  off at "Stakeholder Management: Required in"; `curated_answers.match()` returns `None` for
  the reported phrasings).
- 2026-09-06 (implementation): `complete_with_search_grounding` + `GroundedResponse` /
  `GroundingSource` were **removed outright**, not left dormant. Dead code that contradicts
  the current product direction ("only our own data") is a trap for a future reader; if web
  search is ever wanted it returns as a new capability with its own spec. Only chat used it.
- 2026-09-06 (implementation): truncation is handled by **appending a plain marker + a
  re-emitted `truncated` trace + a non-`stop` finishReason**, not by auto-issuing a
  continuation call. With the 2048-token budget and thinking pinned to 1, truncation is now
  rare; a second model call per truncation adds latency and cost for little gain. Revisit if
  truncation turns out to be common in real use.
- 2026-09-06 (implementation): the bare `"[The AI service returned an error…]"` string is
  gone — every synthesis-stage failure now streams the calm degraded message, matching the
  experience spec's "never a dead-end error" rule.
