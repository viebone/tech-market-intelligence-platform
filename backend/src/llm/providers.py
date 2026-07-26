"""
Provider registry — factory functions for each supported AI provider.

Usage (provider and model always explicit at the call site):

    from llm import providers

    provider = providers.gemini("gemini-2.5-flash")
    async for chunk in provider.stream(messages, system):
        ...

    result = await providers.gemini("gemini-2.5-flash").complete(prompt)

A caller needing a non-default credential (e.g. a dedicated quota pool) names
it explicitly too:

    providers.gemini("gemini-2.5-flash", api_key=os.environ["GEMINI_API_KEY_CLASSIFICATION"])

To add a new provider: create llm/{provider}.py with a class implementing
llm.base.LLMProvider, then add a factory function here.
"""

from __future__ import annotations

from llm.gemini import GeminiAdapter


def gemini(model: str, api_key: str | None = None) -> GeminiAdapter:
    """Return a Gemini adapter for the given model, defaulting to GEMINI_API_KEY."""
    return GeminiAdapter(model, api_key=api_key)
