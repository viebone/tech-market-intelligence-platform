# AI Interaction Settings

Plain-language explanation of how this product manages LLM conversation
context and cost — for anyone (human or AI) working on this codebase who
doesn't already know why the chat feature is built the way it is.

## The core fact this all follows from

LLM APIs are stateless. The model remembers nothing between calls — every
request must include everything you want it to know, from scratch, every
time. There is no "the model remembers the last conversation." If you don't
send it, it doesn't exist to the model.

## What that means for cost

Since nothing is remembered, a naive chat implementation that resends the
*entire* conversation history on every turn gets more expensive as the
conversation gets longer — turn 20 costs more than turn 1, even if the new
message is one word, because you're paying to "remind" the model of
everything said before. This is true of every stateless chat API, not
specific to this product.

## How this product handles it

`/api/chat` makes up to two separate calls to the LLM per user turn, not one
(revised 2026-09-06 — the web-search stage was removed; chat answers only from
the platform's own data):

1. **Query the platform's own data** — the model decides what to look up in
   the real, live-classified job posting database for this specific question.
   If the data genuinely can't answer, this stage says so — it never reaches
   outside the platform.
2. **Write the final answer** — the reply the user actually reads, composed
   only from what step 1 found. It has a bounded output length so it stays a
   conversational answer, not a wall of text, and if it is ever cut short the
   user is told plainly rather than left with a sentence that stops mid-word.

Each of these needs *some* conversation history to make sense of short
follow-ups like "yes please" or "what about X" — but not the same amount:

- **Step 2** needs enough history to sound like a coherent conversation, so
  it gets a real, but bounded, window of recent messages.
- **Step 1** only needs to resolve what a short follow-up is actually asking
  about — which only ever depends on the last exchange or two, never the whole
  conversation. It gets a much smaller window.

Both windows are *sliding* — always "the most recent N messages," never
"every message ever." For an ordinary conversation this is invisible: nobody
notices a window they never hit. It only matters for unusually long
sessions, where it keeps cost from growing without limit instead of letting
one long conversation get arbitrarily expensive.

A single message that's unusually long is rejected with a clear message
asking the user to shorten it, rather than silently cut off (risks losing
the part that mattered) or sent through in full (unbounded cost from one
message).

## Why this matters beyond cost

Missing conversation history isn't just a cost problem — it's what caused a
real, serious quality bug found through testing: a short follow-up like "yes
please" sent to the data-query stage with zero prior context, and the model
had nothing sensible to work with. Rather than admitting that, it fabricated
plausible-sounding numbers under invented category names that don't exist in
this product's taxonomy, and doubled down when questioned. Bounded recent
history is what lets the model actually understand what a follow-up is
asking, instead of guessing.

## Where the actual numbers live

`backend/src/ai_interaction_settings.py` — not duplicated here on purpose.
Numbers get tuned over time; keeping them in exactly one place (the code
that enforces them) means this document and the actual running behavior
can never drift apart. Read that file for current values and the reasoning
behind each one.

## Related

- `backend/specs/market-health/api.md` — Business Logic — Conversational
  data sourcing (the two-stage flow) and "Provider-neutral streaming contract"
  (the output-length cap and the truncation guarantee).
- `design/market-health/experience.md` — the user-facing sourcing rule this
  implements: every answer comes only from the platform's own data; a question
  it can't reach gets a plain "we don't track that", never an outside answer.
- `changes/2026-09-06-chat-answer-truncation-and-curated-match.md` — the change
  that removed the web-search stage and added the length/completeness guarantees.
