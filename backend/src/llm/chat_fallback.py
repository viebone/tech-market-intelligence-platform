"""
Retry helper for interactive (chat) LLM calls.

History: this started (2026-09-04) as an ordered free→paid *tier fallback*
(`ChatTier` / `call_with_fallback` / `stream_with_fallback`). The free tier was
removed from chat 2026-09-06 (its 20-requests/day ceiling and latency made it
unusable — see changes/2026-09-03-chat-resilience-and-instant-answers.md,
2026-09-06 decision-log entries), so this is now a single-tier retry helper:
retry a transient error a couple of times, then give up. No tier list.

Provider-agnostic: operates only on llm.base.LLMProvider, never a provider's SDK
or exception types.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator, Awaitable, Callable, TypeVar

from llm.base import LLMProvider

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Interactive-appropriate: a person is watching a spinner, unlike the batch
# pipeline's patient policy (requirements.py / classification.py: 5 attempts at
# 60s). Two quick attempts, short backoff, then surface the failure so chat can
# degrade to the curated instant-answer path / the "briefly unavailable" message.
CHAT_MAX_RETRIES = 2
CHAT_RETRY_BASE_DELAY_SECONDS = 1.0

# Same string-matching approach as requirements.py's _is_retryable_error /
# classification.py's — provider exceptions don't expose a stable typed status
# code across SDKs, so text-matching the known Gemini/HTTP signals is what those
# retry paths already do. Chat reuses the same signals with a shorter delay.
_TRANSIENT_MARKERS = (
    "429", "500", "502", "503", "504",
    "resource_exhausted", "rate limit", "unavailable", "timeout", "connection",
)


def is_transient_llm_error(exc: Exception) -> bool:
    """True for an error worth retrying; false for anything else (a hard error
    won't be fixed by retrying)."""
    text = str(exc).lower()
    return any(marker in text for marker in _TRANSIENT_MARKERS)


class ChatModelUnavailable(Exception):
    """The chat model failed after its retries. Caller degrades gracefully
    (the curated path still works; otherwise the calm 'briefly unavailable'
    message) — never a bare stack trace to the user."""


async def call_with_retry(
    provider: LLMProvider,
    call: Callable[[LLMProvider], Awaitable[T]],
) -> T:
    """Non-streaming call (Stage 1 tools, Stage 2 search grounding). Retries a
    transient error up to CHAT_MAX_RETRIES with short exponential backoff, then
    raises ChatModelUnavailable. A non-transient error raises immediately."""
    for attempt in range(1, CHAT_MAX_RETRIES + 1):
        try:
            return await call(provider)
        except Exception as exc:
            if not is_transient_llm_error(exc):
                raise
            if attempt == CHAT_MAX_RETRIES:
                logger.warning("Chat model exhausted its retries: %s", exc)
                raise ChatModelUnavailable(str(exc)) from exc
            delay = CHAT_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "Chat model transient error (attempt %d/%d), retrying in %.0fs: %s",
                attempt, CHAT_MAX_RETRIES, delay, exc,
            )
            await asyncio.sleep(delay)
    raise ChatModelUnavailable("unreachable")


async def stream_with_retry(
    provider: LLMProvider,
    call: Callable[[LLMProvider], AsyncIterator[str]],
) -> AsyncIterator[str]:
    """Streaming call (Stage 3 synthesis). If it fails *before* yielding any
    chunk, retry like call_with_retry. If it fails *after* streaming real content
    to the caller, that content already reached the user — re-raise rather than
    restart and duplicate it."""
    for attempt in range(1, CHAT_MAX_RETRIES + 1):
        started = False
        try:
            async for chunk in call(provider):
                started = True
                yield chunk
            return
        except Exception as exc:
            if started:
                raise
            if not is_transient_llm_error(exc):
                raise
            if attempt == CHAT_MAX_RETRIES:
                logger.warning("Chat model (stream) exhausted its retries: %s", exc)
                raise ChatModelUnavailable(str(exc)) from exc
            delay = CHAT_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.warning(
                "Chat model (stream) transient error (attempt %d/%d), retrying in %.0fs: %s",
                attempt, CHAT_MAX_RETRIES, delay, exc,
            )
            await asyncio.sleep(delay)
    raise ChatModelUnavailable("unreachable")
