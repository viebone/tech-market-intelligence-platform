from __future__ import annotations

import os

from google import genai
from google.genai import types


class GeminiAdapter:
    """Adapter for the Google Gemini API (google-genai SDK)."""

    def __init__(self, model: str) -> None:
        self._model = model
        self._client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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
        config_kwargs: dict = {"max_output_tokens": 512}
        if system:
            config_kwargs["system_instruction"] = system
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        return response.text or ""
