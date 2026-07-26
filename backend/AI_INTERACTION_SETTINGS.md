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

`/api/chat` makes up to three separate calls to the LLM per user turn, not
one:

1. **Query the platform's own data** — the model decides what to look up in
   the real, live-classified job posting database for this specific question.
2. **Search the web** — only if step 1 couldn't answer the question from the
   platform's data; finds real, citable external sources instead of guessing.
3. **Write the final answer** — the reply the user actually reads, combining
   whatever was found in steps 1–2.

Each of these needs *some* conversation history to make sense of short
follow-ups like "yes please" or "what about X" — but not the same amount:

- **Step 3** needs enough history to sound like a coherent conversation, so
  it gets a real, but bounded, window of recent messages.
- **Steps 1 and 2** only need to resolve what a short follow-up is actually
  asking about — which only ever depends on the last exchange or two, never
  the whole conversation. They get a much smaller window.

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
  data sourcing, for the full technical design of the three-stage flow above.
- `design/market-health/experience.md` — the user-facing sourcing rule this
  implements (real data first, real external sources second, never fabricate).
