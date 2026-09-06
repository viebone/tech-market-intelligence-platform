from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Literal, Protocol


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


# Note: GroundingSource / GroundedResponse (for web-search grounding) lived here
# until 2026-09-06. Removed with the chat web-search stage
# (changes/2026-09-06-chat-answer-truncation-and-curated-match.md) — the product
# answers only from its own data.


# Provider-neutral streaming stop reason. Every adapter maps its provider's own
# finish enum (Gemini's finish_reason, etc.) onto exactly these four — the caller
# never sees a raw provider value. Sibling of BatchState below; same contract.
# See backend/specs/market-health/api.md — "Provider-neutral streaming contract"
# and outcomes/ai-provider-flexibility.md (amended 2026-09-06).
#   complete  — generation ended on its own
#   truncated — hit the output-length limit before finishing
#   filtered  — stopped by a safety / content filter
#   error     — ended abnormally, or the finish reason was unknown/unreported
StreamStop = Literal["complete", "truncated", "filtered", "error"]


@dataclass
class StreamOutcome:
    """Mutable holder a caller passes to stream() to learn how generation ended,
    without any provider's raw finish enum crossing the boundary. The adapter
    sets `stop` as the stream completes; the caller reads it after the iterator
    drains. Defaults to "complete" so a caller that doesn't pass one, or a
    provider that can't report, degrades to today's behaviour."""
    stop: StreamStop = "complete"


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

    def stream(
        self,
        messages: list[dict],
        system: str,
        *,
        max_output_tokens: int | None = None,
        outcome: "StreamOutcome | None" = None,
    ) -> AsyncIterator[str]:
        """
        Yield plain-text chunks from the model.

        messages: [{"role": "user" | "assistant", "content": str}, ...]
        system:   system instruction prepended to the conversation
        max_output_tokens: provider-neutral cap on the visible answer length. The
            caller passes an application-layer value; the adapter maps it to its
            SDK's own parameter. None means the adapter's own sensible default.
        outcome: if given, the adapter sets `outcome.stop` (a StreamStop) as the
            stream ends, so the caller can tell a clean finish from a truncated /
            filtered / errored one without touching a provider enum.
        """
        ...

    async def complete(
        self, prompt: str, system: str = "", *, max_output_tokens: int | None = None
    ) -> str:
        """Return a single complete (non-streaming) text response.
        `max_output_tokens`: provider-neutral length cap; None uses the adapter default."""
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
        the fact.
        """
        ...


# ---------------------------------------------------------------------------
# Batch processing — a distinct capability from interactive LLMProvider calls.
# An asynchronous job lifecycle (submit -> poll -> fetch), not request/response,
# so it is its own Protocol. Not every provider implements it. See
# backend/specs/market-health/api.md — Tech Decisions — BatchProvider, and
# changes/2026-09-01-requirements-backlog-batch-catchup.md.
# ---------------------------------------------------------------------------

# Provider-neutral job state. Every adapter maps its provider's own state names
# onto exactly these four — the pipeline never sees a provider's raw enum.
BatchState = Literal["submitted", "running", "succeeded", "failed"]


@dataclass
class BatchRequest:
    """One unit of work in a batch job. The same three things
    LLMProvider.complete() takes, plus a caller-chosen id to map the result
    back (here: a synthetic per-prompt id; the posting ids are inside `prompt`
    and echoed back by the model, same as the interactive path)."""
    custom_id: str
    prompt: str
    system: str = ""


@dataclass
class BatchResult:
    """One response from a finished batch job. Exactly one of `text` / `error`
    is set. `text` is the raw model output — the caller parses/validates it
    with the same code path it uses for interactive responses."""
    custom_id: str
    text: str | None = None
    error: str | None = None


class BatchProvider(Protocol):
    """
    Protocol for a provider's batch API. Adapters live in the same
    llm/{provider}.py file as that provider's LLMProvider adapter.

    Provider and model are named explicitly at the call site, same as
    LLMProvider:

        batch = providers.batch("gemini", "gemini-3.6-flash",
                                api_key=os.environ["GEMINI_API_KEY_REQUIREMENTS"])
        job_ref = await batch.submit(requests)
        ...
        if await batch.poll(job_ref) == "succeeded":
            results = await batch.fetch(job_ref)

    No provider SDK type ever crosses this boundary — `BatchRequest`,
    `BatchResult`, and `BatchState` are all defined here.
    """

    async def submit(self, requests: list[BatchRequest]) -> str:
        """Create the batch job. Returns the provider's own job identifier —
        persist it immediately (the batch API is not idempotent)."""
        ...

    async def poll(self, job_ref: str) -> BatchState:
        """Current state of the job. `succeeded` / `failed` are terminal."""
        ...

    async def fetch(self, job_ref: str) -> list[BatchResult]:
        """Results, one per submitted request. Only valid once poll() returned
        `succeeded`. A provider that partially succeeded returns `error`-bearing
        `BatchResult`s for the failed units rather than omitting them."""
        ...
