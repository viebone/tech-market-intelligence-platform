---
source: user-feedback
date: 2026-09-06
---

Raw report (stakeholder, testing production chat):

> before building anything new lets refine what we have and prepare it to grow in
> functionality and in data sources. I just asked this and got the answers which never
> returned the second part: "What skills are more in demand for product managers?" and the
> system freeze there, nothing else is coming
>
> The answer shown was: "Based on platform data collected from **236 Product Manager job
> postings** between **August 3, 2026, and September 6, 2026**, here is the breakdown of skill
> demand ranked.." and the system froze there, nothing else came.

## Investigation (same day)

Reproduced against production with the exact question. The stream sent the reasoning trace,
then streamed answer text that cut off mid-sentence at "**Stakeholder Management**: Required
in", then sent a normal `finish_message` (`finishReason: "stop"`, `generation_time_ms: 17654`).
No error surfaced; the frontend rendered the partial text and the turn just ended.

Two independent root causes:

1. **Truncated synthesis stream.** `GeminiAdapter.stream()` (`backend/src/llm/gemini.py`) sets
   `max_output_tokens=1024` and leaves thinking enabled — every sibling method uses `8192` and
   sets a thinking budget. `gemini-3.6-flash` spends part of the 1024 on invisible reasoning,
   then runs out of budget partway through the visible answer. Gemini ends the stream with a
   `MAX_TOKENS` finish reason, but `stream()` only yields `chunk.text` and never inspects the
   finish reason, and `chat.py`'s Stage 3 loop treats a clean iterator end as success — so a
   cut-off answer reaches the user with no error and no indication it is incomplete.

2. **Curated fast-path misses natural phrasings.** "What skills do product manager roles ask
   for?" is catalogue entry `pm-skills` in `curated_answers.py` — a sub-second, no-model
   answer. But `match()` is a pure substring check against a short phrasing list, so
   "What skills are more in demand for product managers?" and "what skills do product managers
   need" both miss and fall through to the 10-30s model path (which then hit cause 1).

Related: `research/2026-09-03-chat-resilience-and-instant-answers.md`,
`research/2026-09-06-chat-input-dead-on-non-conversation-tasks.md`.
