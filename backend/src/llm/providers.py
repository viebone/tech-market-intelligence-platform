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

from llm.gemini import GeminiAdapter, GeminiBatchAdapter


def gemini(model: str, api_key: str | None = None) -> GeminiAdapter:
    """Return a Gemini adapter for the given model, defaulting to GEMINI_API_KEY."""
    return GeminiAdapter(model, api_key=api_key)


# Batch API adapters — see llm.base.BatchProvider. To switch the batch provider
# for a workload, this dispatch is the one line that changes (plus a new adapter
# file). See backend/specs/market-health/api.md — Tech Decisions — BatchProvider.
_BATCH_ADAPTERS = {
    "gemini": GeminiBatchAdapter,
}


def batch(provider: str, model: str, api_key: str | None = None):
    """Return a BatchProvider adapter for the named provider + model.

        providers.batch("gemini", "gemini-3.6-flash",
                        api_key=os.environ["GEMINI_API_KEY_REQUIREMENTS"])
    """
    try:
        adapter_cls = _BATCH_ADAPTERS[provider]
    except KeyError:
        raise ValueError(
            f"no batch adapter for provider {provider!r} — implement one in "
            f"llm/{provider}.py and register it here"
        ) from None
    return adapter_cls(model, api_key=api_key)
