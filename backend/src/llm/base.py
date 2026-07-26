from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Protocol


@dataclass
class ToolCall:
    """A single function-tool invocation made during a complete_with_tools() call."""
    name: str
    args: dict
    result: Any


@dataclass
class ToolCallResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class GroundingSource:
    title: str
    url: str


@dataclass
class GroundedResponse:
    text: str
    search_queries: list[str] = field(default_factory=list)
    sources: list[GroundingSource] = field(default_factory=list)


class LLMProvider(Protocol):
    """
    Protocol all AI provider adapters must implement.

    Each adapter lives in llm/{provider}.py. To add a new provider,
    create a class implementing this protocol — nothing else changes.

    Provider and model are always named explicitly at the call site:

        provider = providers.gemini("gemini-2.5-flash")
        async for chunk in provider.stream(messages, system):
            yield chunk

        result = await providers.gemini("gemini-2.5-flash").complete(prompt)

    A single feature may call more than one provider:

        answer = providers.gemini("gemini-2.5-flash")
        judge  = providers.anthropic("claude-haiku-4-5")

    A caller that needs a non-default credential (e.g. a dedicated quota pool)
    names it explicitly too, same as provider and model:

        providers.gemini("gemini-2.5-flash", api_key=os.environ["GEMINI_API_KEY_CLASSIFICATION"])
    """

    def stream(self, messages: list[dict], system: str) -> AsyncIterator[str]:
        """
        Yield plain-text chunks from the model.

        messages: [{"role": "user" | "assistant", "content": str}, ...]
        system:   system instruction prepended to the conversation
        """
        ...

    async def complete(self, prompt: str, system: str = "") -> str:
        """Return a single complete (non-streaming) text response."""
        ...

    async def complete_with_tools(
        self, prompt: str, system: str, tools: list[Callable]
    ) -> ToolCallResponse:
        """
        Single call with custom function tools available (e.g. query_market_data).
        The model may call any of `tools` zero or more times before producing its
        final answer; the provider is responsible for executing those calls and
        feeding results back. `tool_calls` records what was actually invoked, in
        order, for building an honest reasoning trace — never reconstructed after
        the fact. Never combined with search grounding in the same call.
        """
        ...

    async def complete_with_search_grounding(
        self, prompt: str, system: str = ""
    ) -> GroundedResponse:
        """
        Single call with real web search grounding enabled — the model can
        search and cite real results. `search_queries` and `sources` reflect
        what was actually searched and found; never fabricated. Never combined
        with custom function tools in the same call.
        """
        ...
