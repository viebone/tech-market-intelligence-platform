from __future__ import annotations

import os
from typing import Callable

from google import genai
from google.genai import types

from llm.base import GroundedResponse, GroundingSource, ToolCall, ToolCallResponse


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

    async def stream(self, messages: list[dict], system: str):
        """Yield plain-text chunks from the Gemini model."""
        contents = [
            types.Content(
                role="model" if m["role"] == "assistant" else "user",
                parts=[types.Part(text=m["content"])],
            )
            for m in messages
        ]
        async for chunk in await self._client.aio.models.generate_content_stream(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=1024,
            ),
        ):
            if chunk.text:
                yield chunk.text

    async def complete(self, prompt: str, system: str = "") -> str:
        """Return a single complete response from the Gemini model."""
        # thinking_budget=0: complete() is for simple, single-shot completions
        # (e.g. structured extraction), not open-ended reasoning. Without this,
        # gemini-2.5-flash spends its output budget on invisible "thinking"
        # tokens before ever producing visible text — observed truncating a
        # classification response to a few tokens, well before the output
        # budget's worth of real text. Left enabled for stream(), which is
        # used for higher-quality conversational answers.
        config_kwargs: dict = {
            "max_output_tokens": 8192,
            "thinking_config": types.ThinkingConfig(thinking_budget=0),
        }
        if system:
            config_kwargs["system_instruction"] = system
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

    async def complete_with_search_grounding(
        self, prompt: str, system: str = ""
    ) -> GroundedResponse:
        """
        Single call with Google Search grounding enabled — the model can
        search and cite real results. Never combined with complete_with_tools
        in the same call; Gemini doesn't support mixing custom function tools
        with the search-grounding tool in one request.
        """
        config_kwargs: dict = {
            "max_output_tokens": 8192,
            "tools": [types.Tool(google_search=types.GoogleSearch())],
        }
        if system:
            config_kwargs["system_instruction"] = system
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        search_queries: list[str] = []
        sources: list[GroundingSource] = []
        candidates = response.candidates or []
        if candidates:
            grounding_metadata = getattr(candidates[0], "grounding_metadata", None)
            if grounding_metadata is not None:
                search_queries = list(getattr(grounding_metadata, "web_search_queries", None) or [])
                for chunk in getattr(grounding_metadata, "grounding_chunks", None) or []:
                    web = getattr(chunk, "web", None)
                    if web is not None:
                        sources.append(GroundingSource(title=web.title or web.uri, url=web.uri))

        return GroundedResponse(text=response.text or "", search_queries=search_queries, sources=sources)
