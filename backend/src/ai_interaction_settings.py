"""
AI interaction settings — the tunable limits governing how much conversation
context gets sent to the LLM on each /api/chat call, and how long a single
user message can be.

Why this exists: LLM APIs are stateless — nothing is remembered between
calls unless it's explicitly resent. A naive chat implementation resends the
entire conversation history on every turn, so cost grows without bound as a
conversation gets longer. This module is the single source of truth for the
limits that keep that bounded, without demoting the experience for the vast
majority of ordinary-length conversations. See AI_INTERACTION_SETTINGS.md
(backend/) for the full plain-language explanation of why this design exists
— this file intentionally only has the numbers and the reasoning behind each
one, so the two documents can't drift out of sync with each other.

Change the numbers here, not inline in chat.py — this is the one place they
live, so the running code and this file can never disagree about what the
actual limit is.
"""

from __future__ import annotations

# Stage 3 (the final synthesis call — the reply the user actually reads)
# needs enough history to sound like a coherent conversation. Full history
# is correct and expected for a chat product; sending literally every
# message since the conversation began would let cost grow without limit
# for unusually long sessions, though. This bounds it to a sliding window —
# only the most recent N messages are sent, not the whole transcript.
# Invisible for a normal conversation (nobody notices a window they never
# hit); only matters for pathologically long sessions.
SYNTHESIS_HISTORY_WINDOW_MESSAGES = 15

# Stage 1 (query the platform's own data) only needs enough context to
# understand what a short follow-up like "yes please" or "what about X" is
# actually referring to — never the full conversation. A follow-up realistically
# only ever references the immediately preceding exchange, not something from 20
# turns ago, so this window is much smaller than Stage 3's without losing
# anything a user would notice. (~3 user/assistant exchanges.)
TOOL_STAGE_HISTORY_MESSAGES = 6

# Stage 3 (synthesis) output length — a provider-neutral cap passed to
# LLMProvider.stream(max_output_tokens=...); each adapter maps it to its own SDK.
# A chat reply is a conversational answer, not a report: this is big enough for a
# complete short answer plus a comfortable margin (a data-then-judgment "should I
# learn X" answer, a short bullet list of several figures), and deliberately far
# below the model's hard maximum, which invites a wall of text. It replaces the
# Gemini stream() adapter's old hard-coded 1024, which — minus the model's
# invisible reasoning tokens — truncated ordinary answers mid-sentence
# (changes/2026-09-06-chat-answer-truncation-and-curated-match.md).
CHAT_SYNTHESIS_MAX_OUTPUT_TOKENS = 2048

# A single user message beyond this length is rejected with a clear message
# asking the user to narrow it down, rather than silently truncated (risks
# cutting off exactly the part that mattered, producing a confusing
# partial-context answer) or sent through in full (unbounded cost from one
# message). Rejecting with clear feedback is both cheaper and a better
# experience than either alternative.
MAX_USER_MESSAGE_CHARS = 4000

# Chat runs on one paid, isolated Gemini project (the free tier was removed
# 2026-09-06 — its 20-requests/day ceiling and latency made it unusable). This
# caps that project's spend: a small number of model requests per UTC day
# (pennies/day at typical Gemini flash-tier pricing), same mechanism as the
# ingestion pipeline's daily budgets. Once reached, the model stages are skipped
# for the rest of the day — the curated instant-answer path and the
# data-story/welcome zero-LLM paths still work. See
# changes/2026-09-03-chat-resilience-and-instant-answers.md.
CHAT_PAID_DAILY_REQUEST_CAP = 100
