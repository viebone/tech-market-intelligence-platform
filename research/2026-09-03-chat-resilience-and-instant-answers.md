source: bug + stakeholder-request
date: 2026-09-03

## Bug (trigger)

Chat is broken in production. Every prompt to the market-health assistant returns:

> [The AI service returned an error. Please try again.]

Reproduced 2026-09-03 against `https://api-production-df13.up.railway.app/api/chat`
(65s wait, then the error string). `api` service logs, 13:35–13:37 UTC:

```
Stage 1 (query_market_data) failed: 503 UNAVAILABLE. {'error': {'code': 503,
  'message': 'This model is currently experiencing high demand. Spikes in demand
  are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}
Stage 1 produced ungrounded text with no tool call and no NEEDS_EXTERNAL marker; discarding it.
LLM provider error (gemini-3.6-flash): 503 UNAVAILABLE. {'error': {'code': 503, ...}}
```

Root cause: the pinned free-tier chat model `gemini-3.6-flash` (`GEMINI_API_KEY`,
free-tier project `gen-lang-client-0003173949`) is returning `503 UNAVAILABLE`
("high demand") on nearly every call, failing both Stage 1 (data-tool query) and
Stage 3 (synthesis) in `backend/src/chat.py`.

Contributing code gaps:
- **No retry/backoff on 503/429 in the chat provider path.** `GeminiAdapter` has a
  60s timeout but no retry — unlike `requirements.py`'s `_complete_with_retry` and
  the classification retry policy, both of which already retry `503 "high demand"`
  and `429` with backoff (see `backend/specs/market-health/api.md` — Business Logic
  — Classification — Retry policy).
- **Error classification is too coarse** (`chat.py` ~L424-428): only
  `connection|timeout|network|unreachable` map to the "unreachable, try again"
  message; `503` / `UNAVAILABLE` / `429` / `RESOURCE_EXHAUSTED` fall through to the
  flat generic "[The AI service returned an error. Please try again.]".
- The backend spec's `POST /api/chat` error table lists `502 Gemini API
  unreachable`, but the implementation streams a `200` with an error-text chunk
  (it can't change status mid-stream). Spec/impl mismatch.

This was foreseen. `changes/2026-08-29-chat-free-tier-key-isolation.md` Step 5
noted: "the `gemini-flash-latest` alias endpoint returned intermittent `503 'high
demand'` / timeouts today... If chat sees persistent 503s in Step 6, pinning
`_CHAT_MODEL` to `gemini-3.6-flash` is a trivial follow-up" — it is already pinned,
and Step 6.3 already saw `[The AI service returned an error…]` from free-tier rate
limiting during rapid calls. The free-tier project simply does not have the
capacity to serve chat reliably.

Related: `research/2026-08-29-llm-cost-governance.md`,
`changes/2026-08-29-chat-free-tier-key-isolation.md` (chat isolated onto the
free-tier project), `outcomes/llm-spend-is-bounded-and-isolated.md`.

## Stakeholder direction (2026-09-03, on how to fix it)

Verbatim:

> "if the free model is as good as the paid one, lets use it until it reach the
> limit, then lets move to paid but i would like to have it in a separated
> project from the backend so that i can control better the cost. and we should
> always try to provide as many answers as possible without touching the model,
> and for that we will need to have some very well built pre populated set of
> questions"

Three asks:

1. **Tiered model fallback.** Use the free-tier model while it works; when it hits
   its limit (quota exhaustion / persistent unavailability), fall back to a paid
   model. Ordered, not cost-optimising.
2. **Dedicated project for paid chat.** The paid chat model must run in its own
   Gemini project, separate from the classification/requirements prepaid project
   (`gen-lang-client-0963554051`), so chat cost is independently controllable and
   a chat spike cannot drain the pipeline's balance (and vice versa).
3. **Curated no-LLM answer set.** A "very well built pre-populated set of
   questions" the platform can answer without any model call at all — serve as
   many answers as possible straight from platform data, so common questions
   never touch Gemini.

Earlier stakeholder signal, still standing (`chat-free-tier-key-isolation`
Decision Log): "it doesn't matter which model is for chat, I just want whatever
comes for free" — free-first is the preference; paid is the fallback, capped and
isolated.

## Stakeholder clarifications (2026-09-03, follow-up)

> "free tier must have the same quality than paid one, paid one must have its own
> paid project, separated from the others. then pre-defined questions must bring
> up to date data, questions are pre made, but data must be up to date. The idea
> would have to, eventually have as many predefined questions as possible so that
> we provide super fast answer to users without touching the LLM"

- **Quality parity across tiers.** The free-tier model must be chosen for
  quality-equivalence with the paid model — the fallback is about *availability*,
  not accepting a worse answer on the free tier. If no free model matches the paid
  model's quality, that gap must be surfaced, not silently shipped.
- **Dedicated paid project, hard requirement.** The paid chat model runs in its
  own Google Cloud project, separate from classification/requirements
  (`gen-lang-client-0963554051`) and from the free chat project.
- **Predefined questions = fixed questions, live data.** The catalogue of
  questions is pre-authored, but every answer is computed from current platform
  data at request time — never a stored/stale answer string.
- **Grow the catalogue continuously.** The long-term goal is to cover as many
  common questions as possible with the no-LLM path, so adding a predefined
  question must be a cheap, repeatable operation (a catalogue entry: intent +
  query + template), and the set is expected to keep growing over time.
