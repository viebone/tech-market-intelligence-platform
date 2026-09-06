from __future__ import annotations

import os
from typing import Callable

from google import genai
from google.genai import types

from llm.base import (
    BatchRequest,
    BatchResult,
    BatchState,
    StreamOutcome,
    StreamStop,
    ToolCall,
    ToolCallResponse,
)

# gemini-3.6-flash's own finish_reason names -> the four provider-neutral
# StreamStop values (llm.base). Anything not listed — FINISH_REASON_UNSPECIFIED,
# OTHER, MALFORMED_FUNCTION_CALL, or a name a future SDK adds — maps to "error":
# an abnormal end the caller should treat as a failed answer, not a clean stop.
_GEMINI_FINISH_MAP: dict[str, StreamStop] = {
    "STOP": "complete",
    "MAX_TOKENS": "truncated",
    "SAFETY": "filtered",
    "RECITATION": "filtered",
    "PROHIBITED_CONTENT": "filtered",
    "BLOCKLIST": "filtered",
    "SPII": "filtered",
    "IMAGE_SAFETY": "filtered",
}

# stream() is used for the conversational synthesis reply. The heavy reasoning
# happened in an earlier tool-calling stage, so this call needs almost no
# "thinking" budget — and must not spend the visible-output budget on invisible
# thinking (the bug fixed 2026-09-06: stream() hard-capped output at 1024 with
# thinking left on, so gemini-3.6-flash truncated normal answers mid-sentence).
# 1 is the minimum every current flash model accepts (0 is rejected by
# gemini-3.6-flash / gemini-flash-latest; see complete()).
_STREAM_THINKING_BUDGET = 1
# Fallback when a caller passes no max_output_tokens — a full conversational
# answer with comfortable margin, not the model's hard maximum.
_DEFAULT_STREAM_MAX_OUTPUT_TOKENS = 2048

# Models confirmed (at runtime, in this process) to reject thinking_budget=0
# outright — see complete()'s fallback. Remembered process-wide, keyed by
# model name, so once a model's rejection is known, every subsequent call
# skips straight to budget=1 instead of spending a real API call (and real
# daily quota) on an attempt already known to fail. A fresh GeminiAdapter is
# constructed per call site (see requirements.py's _complete_with_retry), so
# this can't live on the instance — it has to be module-level to actually
# save anything across calls.
_MODELS_REJECTING_ZERO_THINKING_BUDGET: set[str] = set()


def _finish_reason_name(chunk) -> str | None:
    """The finish_reason on a streamed chunk's first candidate, as a bare string
    (e.g. "STOP", "MAX_TOKENS"), or None if this chunk carries no finish reason
    yet. Defensive against SDK shape changes — never raises."""
    candidates = getattr(chunk, "candidates", None) or []
    if not candidates:
        return None
    reason = getattr(candidates[0], "finish_reason", None)
    if reason is None:
        return None
    return getattr(reason, "name", str(reason)) or None


class GeminiAdapter:
    """Adapter for the Google Gemini API (google-genai SDK)."""

    def __init__(self, model: str, api_key: str | None = None) -> None:
        self._model = model
        # http_options timeout: without this, a stalled network call has no
        # ceiling and can hang indefinitely — observed in practice during a
        # classification run (process alive, near-zero CPU, no progress, no
        # error, for many minutes past what retry/backoff should allow).
        self._client = genai.Client(
            api_key=api_key or os.environ.get("GEMINI_API_KEY"),
            http_options=types.HttpOptions(timeout=60_000),  # ms
        )

    async def stream(
        self,
        messages: list[dict],
        system: str,
        *,
        max_output_tokens: int | None = None,
        outcome: StreamOutcome | None = None,
    ):
        """Yield plain-text chunks from the Gemini model.

        If `outcome` is given, its `.stop` is set to a provider-neutral StreamStop
        as the stream ends — mapped from Gemini's `finish_reason`, so the caller
        never sees the raw enum. A stream that ends without ever reporting a
        finish reason is treated as "error" (an abnormal end), not "complete"."""
        contents = [
            types.Content(
                role="model" if m["role"] == "assistant" else "user",
                parts=[types.Part(text=m["content"])],
            )
            for m in messages
        ]
        stop: StreamStop = "error"
        saw_finish_reason = False
        async for chunk in await self._client.aio.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_output_tokens or _DEFAULT_STREAM_MAX_OUTPUT_TOKENS,
                thinking_config=types.ThinkingConfig(thinking_budget=_STREAM_THINKING_BUDGET),
            ),
        ):
            if chunk.text:
                yield chunk.text
            reason = _finish_reason_name(chunk)
            if reason is not None:
                saw_finish_reason = True
                stop = _GEMINI_FINISH_MAP.get(reason, "error")
        if outcome is not None:
            outcome.stop = stop if saw_finish_reason else "error"

    async def complete(
        self, prompt: str, system: str = "", *, max_output_tokens: int | None = None
    ) -> str:
        """Return a single complete response from the Gemini model."""
        # thinking_budget=0: complete() is for simple, single-shot completions
        # (e.g. structured extraction), not open-ended reasoning. Without this,
        # gemini-2.5-flash spends its output budget on invisible "thinking"
        # tokens before ever producing visible text — observed truncating a
        # classification response to a few tokens, well before the output
        # budget's worth of real text. stream() sets its own small budget too.
        starting_budget = 1 if self._model in _MODELS_REJECTING_ZERO_THINKING_BUDGET else 0
        config_kwargs: dict = {
            "max_output_tokens": max_output_tokens or 8192,
            "thinking_config": types.ThinkingConfig(thinking_budget=starting_budget),
        }
        if system:
            config_kwargs["system_instruction"] = system
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
        except Exception as exc:
            # Some newer model generations reject thinking_budget=0 outright
            # (400 INVALID_ARGUMENT) — confirmed empirically on gemini-flash-latest,
            # which only accepts budget=0 disabled entirely; a minimal non-zero
            # budget (1) is the closest equivalent it does accept. gemini-2.5-flash
            # never hits this branch since budget=0 already succeeds for it.
            if starting_budget != 0 or "400" not in str(exc) or "invalid_argument" not in str(exc).lower():
                raise
            # Remember this model rejects budget=0 so every later call (this
            # process, any adapter instance) skips straight to budget=1 —
            # each fallback here is a second real API call against the same
            # daily quota as the first, so repeating the doomed attempt on
            # every single call effectively halves real throughput per day.
            _MODELS_REJECTING_ZERO_THINKING_BUDGET.add(self._model)
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=1)
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
        return response.text or ""

    async def complete_with_tools(
        self, prompt: str, system: str, tools: list[Callable]
    ) -> ToolCallResponse:
        """
        Single call with custom function tools. Plain Python callables passed
        as `tools` enable the SDK's automatic function calling: the model may
        call any of them zero or more times, the SDK executes them and feeds
        results back, all within this one call. `automatic_function_calling_history`
        is parsed afterward for an honest record of what was actually called —
        never reconstructed from the final answer alone.
        """
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                tools=tools,
                max_output_tokens=8192,
            ),
        )

        tool_calls: list[ToolCall] = []
        history = getattr(response, "automatic_function_calling_history", None) or []
        for content in history:
            for part in getattr(content, "parts", None) or []:
                fc = getattr(part, "function_call", None)
                if fc is not None:
                    tool_calls.append(ToolCall(name=fc.name, args=dict(fc.args or {}), result=None))
                fr = getattr(part, "function_response", None)
                if fr is not None and tool_calls and tool_calls[-1].result is None:
                    # AFC wraps the callable's actual return value one level
                    # deeper, as {"result": <value>} on success or {"error": <msg>}
                    # on failure (confirmed empirically) — unwrap it so
                    # ToolCall.result is the function's real return value, not
                    # the SDK's envelope around it.
                    payload = fr.response
                    if isinstance(payload, dict) and "result" in payload:
                        payload = payload["result"]
                    tool_calls[-1].result = payload

        return ToolCallResponse(text=response.text or "", tool_calls=tool_calls)

    # Note: a `complete_with_search_grounding` method lived here until 2026-09-06.
    # It was removed with the chat web-search stage
    # (changes/2026-09-06-chat-answer-truncation-and-curated-match.md) — the
    # product answers only from its own data. If a future feature needs real web
    # search it comes back as a new capability with its own spec, not as dormant
    # code that contradicts the current product direction.


# Gemini's JobState names -> the four provider-neutral BatchState values.
# Anything not listed (UNSPECIFIED, UPDATING, PAUSED) is treated as "running"
# — transient, keep waiting — except the terminal-but-bad ones mapped to failed.
_GEMINI_STATE_MAP = {
    "JOB_STATE_PENDING": "submitted",
    "JOB_STATE_QUEUED": "submitted",
    "JOB_STATE_RUNNING": "running",
    "JOB_STATE_SUCCEEDED": "succeeded",
    "JOB_STATE_PARTIALLY_SUCCEEDED": "succeeded",  # fetch() surfaces the per-unit errors
    "JOB_STATE_FAILED": "failed",
    "JOB_STATE_CANCELLED": "failed",
    "JOB_STATE_CANCELLING": "failed",
    "JOB_STATE_EXPIRED": "failed",
}


class GeminiBatchAdapter:
    """Adapter for the Gemini batch API (google-genai `client.batches`).

    Implements llm.base.BatchProvider. Uses **inlined** requests (no GCS/file
    upload) — MAX_BATCH_POSTINGS worth of extraction prompts is comfortably
    under the inline size limit, and it keeps the whole round trip inside the
    SDK with no bucket to manage. All Gemini-specific batch mechanics live in
    this class; nothing above the `llm/` package imports `google.genai`.
    """

    def __init__(self, model: str, api_key: str | None = None) -> None:
        self._model = model if model.startswith("models/") else f"models/{model}"
        self._client = genai.Client(
            api_key=api_key or os.environ.get("GEMINI_API_KEY"),
            http_options=types.HttpOptions(timeout=120_000),  # ms
        )

    async def submit(self, requests: list[BatchRequest]) -> str:
        inlined = [
            types.InlinedRequest(
                model=self._model,
                contents=[types.Content(role="user", parts=[types.Part(text=r.prompt)])],
                config=types.GenerateContentConfig(
                    system_instruction=r.system or None,
                    max_output_tokens=8192,
                    # Same reasoning as GeminiAdapter.complete(): structured
                    # extraction, not open-ended reasoning. gemini-3.6-flash
                    # rejects budget=0, so 1 is the minimum it accepts.
                    thinking_config=types.ThinkingConfig(thinking_budget=1),
                ),
                metadata={"custom_id": r.custom_id},
            )
            for r in requests
        ]
        job = await self._client.aio.batches.create(
            model=self._model,
            src=inlined,
            config=types.CreateBatchJobConfig(display_name="requirements-extraction"),
        )
        return job.name

    async def poll(self, job_ref: str) -> BatchState:
        job = await self._client.aio.batches.get(name=job_ref)
        state_name = getattr(job.state, "name", str(job.state))
        return _GEMINI_STATE_MAP.get(state_name, "running")

    async def fetch(self, job_ref: str) -> list[BatchResult]:
        job = await self._client.aio.batches.get(name=job_ref)
        dest = job.dest
        responses = list(getattr(dest, "inlined_responses", None) or []) if dest else []
        out: list[BatchResult] = []
        for i, item in enumerate(responses):
            custom_id = ""
            meta = getattr(item, "metadata", None) or {}
            if isinstance(meta, dict):
                custom_id = meta.get("custom_id", "") or ""
            custom_id = custom_id or f"index-{i}"
            err = getattr(item, "error", None)
            if err is not None:
                out.append(BatchResult(custom_id=custom_id, error=str(err)))
                continue
            resp = getattr(item, "response", None)
            text = getattr(resp, "text", None) if resp is not None else None
            if text:
                out.append(BatchResult(custom_id=custom_id, text=text))
            else:
                out.append(BatchResult(custom_id=custom_id, error="empty batch response"))
        return out
