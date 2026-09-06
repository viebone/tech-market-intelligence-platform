---
id: chat-answer-truncation-and-curated-match
date: 2026-09-06
trigger-type: bug
change-type: bug-fix
outcome: understand-market-health-before-searching
status: triaged
---

# Change Request: Chat answers truncate mid-sentence; curated fast-path misses natural phrasings

## Signal

See: `research/2026-09-06-chat-answer-truncation-and-curated-match.md`

Stakeholder hit it live: asked "What skills are more in demand for product managers?", got an
answer that stopped mid-sentence ("Stakeholder Management: Required in") with nothing after
and no error — "the system freeze there".

## Outcome

`outcomes/understand-market-health-before-searching.md` — the chat assistant is how a
professional explores demand, skills, and pay beyond the opening chart. "They can identify
which roles and skills are in demand" and "less than 5 minutes to get a clear market read"
are not met when the answer is cut off halfway or takes 10-30s for a question that should be
instant. No success criterion changes — this is the outcome not being delivered, not a new
promise.

Touched: `outcomes/llm-spend-is-bounded-and-isolated.md` — a curated-match miss spends a paid
model call that shouldn't happen. No-change to the outcome; a reason the fix matters.

## Change Type

`bug-fix` — both failures violate what specs already say:

- The chat-resilience work (`changes/2026-09-03-chat-resilience-and-instant-answers.md`,
  `design/market-health/experience.md` — "never a dead end") promised chat "always shows a
  real answer or a clear, actionable message — never silence". A silently truncated answer
  is exactly that silence.
- `backend/specs/market-health/api.md` — "Curated instant-answer engine" says common
  questions take the no-model path. A catalogued question that misses the matcher on an
  ordinary rephrasing is the engine not doing what the spec says.

The finish-reason handling is a small streamed-behaviour addition (arguably `api-change`),
kept under `bug-fix` because it exists to make the promised "never silence" behaviour real,
not to add a capability.

## Root Cause

1. **`GeminiAdapter.stream()`** (`backend/src/llm/gemini.py`): `max_output_tokens=1024` (vs.
   `8192` everywhere else) and no `thinking_config`. `gemini-3.6-flash` burns budget on
   invisible thinking, then truncates the visible answer at `MAX_TOKENS`. `stream()` yields
   only `chunk.text`; `chat.py` Stage 3 treats a clean end as success. → the user sees a
   half-answer, no error.
2. **`curated_answers.match()`** (`backend/src/curated_answers.py`): substring-only match
   against a short phrasing list. Natural rewordings ("...are more in demand for...",
   "...do product managers need") miss and fall through to the model.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change — criteria already cover it |
| Outcome | `outcomes/llm-spend-is-bounded-and-isolated.md` | no-change — note only |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | update — add an Edge Case: the model returns an incomplete answer → surfaced clearly (finish it or flag it), never shown as a silent cut-off. Note that the curated fast-path is expected to recognise ordinary rephrasings of a catalogued question, not only near-exact wording. |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | review — expected no-change; a truncation marker streams through the existing `AITurn` text path. Confirm. |
| Backend Spec | `backend/specs/market-health/api.md` | update — synthesis stream token budget + thinking config; `MAX_TOKENS`/incomplete-finish handling in Stage 3; curated matcher robustness (matching rule + phrasing coverage). |
| Frontend Implementation | `frontend/src/` | no-change expected (confirm in step 5) |
| Backend Implementation | `backend/src/llm/gemini.py`, `backend/src/chat.py`, `backend/src/curated_answers.py` | update |

## Execution Plan

- [ ] Step 1: Read `design/market-health/experience.md` + `backend/specs/market-health/api.md`
      + `frontend/specs/market-health/architecture.md` for the chat/synthesis sections
      (root cause already established — code is wrong; specs are silent on truncation).
- [ ] Step 2: `/new-experience` — update `design/market-health/experience.md`: new Edge Case
      for an incomplete model answer; note curated matching must handle ordinary rephrasings.
- [ ] Step 3: `/new-backend-spec` — update `backend/specs/market-health/api.md`: synthesis
      `max_output_tokens` + thinking budget; Stage 3 detects a non-`STOP` / incomplete finish
      and either continues the generation or appends a clear "answer was cut off — ask me to
      continue" line (decide in the spec); curated matcher rule + widened phrasing set (and
      whether to move from substring to token-overlap / keyword matching).
- [ ] Step 4: `/new-frontend-spec` — review `frontend/specs/market-health/architecture.md`;
      confirm no component change (truncation marker rides the existing text path).
- [ ] Step 5: `/implement-backend` —
      - `gemini.py`: `stream()` → `max_output_tokens=8192` + a bounded `thinking_config`
        (match the `complete()` pattern, incl. the budget-0-rejection fallback); expose the
        finish reason from the stream.
      - `chat.py`: Stage 3 inspects the finish reason; on `MAX_TOKENS`/incomplete, act per
        the spec decision (continue or flag). Keep the existing degraded/error paths.
      - `curated_answers.py`: widen matching so the reported phrasings (and siblings for the
        other 5 entries) hit; add a regression test per phrasing.
- [ ] Step 6: `/implement-frontend` — only if step 4 finds a change.
- [ ] Step 7: Verify against production — re-ask the exact question (full answer, no cut-off),
      re-ask 3-4 rephrasings of each curated entry (instant, no-model trace), confirm a
      genuinely long answer no longer truncates. Commit + push (auto-deploys `api` + `web`).
- [ ] Step 8: Mark `complete` when every box is checked and specs match the code.

## Decision Log

- 2026-09-06: Tracked against `understand-market-health-before-searching` — chat is that
  outcome's exploration surface; a truncated or needlessly slow answer is that outcome
  failing, so no criterion moves. `llm-spend-is-bounded-and-isolated` is touched (a matcher
  miss = an avoidable paid call) but unchanged.
- 2026-09-06: `bug-fix`, not `new-feature` / `api-change` — both fixes make already-specified
  behaviour real ("never silence"; "common questions take the no-model path"). The
  finish-reason check is new streamed behaviour but exists only to honour the existing promise.
- 2026-09-06: Scope held to these two bugs per stakeholder ("just the chat bugs now"). The
  broader "prepare it to grow in functionality and data sources" is deliberately not in this
  CR — it needs its own framing once the growth direction is described.
- 2026-09-06: Both root causes confirmed by reproduction (prod stream cut off at
  "Stakeholder Management: Required in"; `curated_answers.match()` returns `None` for the
  reported phrasings) before writing this CR — not inferred.
