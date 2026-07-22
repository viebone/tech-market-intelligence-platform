from __future__ import annotations

import os

from google import genai
from google.genai import types


class GeminiAdapter:
    """Adapter for the Google Gemini API (google-genai SDK)."""

    def __init__(self, model: str) -> None:
        self._model = model
        # http_options timeout: without this, a stalled network call has no
        # ceiling and can hang indefinitely — observed in practice during a
        # classification run (process alive, near-zero CPU, no progress, no
        # error, for many minutes past what retry/backoff should allow).
        self._client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
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
