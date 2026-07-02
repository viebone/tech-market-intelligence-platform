"""
Provider registry — factory functions for each supported AI provider.

Usage (provider and model always explicit at the call site):

    from llm import providers

    provider = providers.gemini("gemini-2.5-flash")
    async for chunk in provider.stream(messages, system):
        ...

    result = await providers.gemini("gemini-2.5-flash").complete(prompt)

To add a new provider: create llm/{provider}.py with a class implementing
llm.base.LLMProvider, then add a factory function here.
"""

from __future__ import annotations

from llm.gemini import GeminiAdapter


def gemini(model: str) -> GeminiAdapter:
    """Return a Gemini adapter for the given model."""
    return GeminiAdapter(model)
