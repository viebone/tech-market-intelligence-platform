"""
FastAPI router for the conversational endpoint.

Endpoint:
  POST /api/chat

Fetches the current market summary and trends for the given context,
prepends them as a system instruction to Gemini, then streams the response
as Server-Sent Events (text/event-stream).

Wire format: structured SSE data events.
  event: data
  data: [{"type":"reasoning_trace","trace":{...}}]   ← first event, before any tokens

  event: data
  data: [{"type":"text","value":"<chunk>"}]           ← one per token

  event: data
  data: [{"type":"finish_message","generation_time_ms":2340}]  ← last event

  d:{...}                                             ← Vercel AI SDK finish delta
"""

from __future__ import annotations

import dataclasses
import json
import logging
import time
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from llm import providers
from pydantic import BaseModel

from market_health import _resolve_signal, _filter_demand, _filter_compensation, _serialise
from mock_data import LAYOFF_SIGNALS, slice_posting_trend
from models import (
    MarketHealthSignal, DemandSignal, CompensationSignal,
    SourceAccess, ReasoningStep, ReasoningTrace,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Provider and model are declared here — explicit at the call site per outcome ai-provider-flexibility.
_CHAT_MODEL = "gemini-2.5-flash"


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str    # "user" | "assistant"
    content: str


class ChatContext(BaseModel):
    role: str = "all"
    seniority: str = "all"
    location: str = "all"


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    context: ChatContext = ChatContext()


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------

def _build_system_prompt(context: ChatContext) -> str:
    """
    Fetches market data for the given context and formats it as a structured
    system instruction for Gemini.
    """
    role, seniority, location = context.role, context.seniority, context.location

    signal, implication = _resolve_signal(role, seniority, location)
    demand_signals = _filter_demand(role, seniority, location)
    comp_signals = _filter_compensation(role, seniority, location)
    sliced_demand = [
        dataclasses.replace(d, posting_trend=slice_posting_trend(d.posting_trend, "6m"))
        for d in demand_signals
    ]

    context_block = json.dumps(
        {
            "filters_applied": {
                "role": role,
                "seniority": seniority,
                "location": location,
            },
            "market_health_signal": _serialise(signal) if signal else None,
            "search_implication": _serialise(implication) if implication else None,
            "demand_signals": _serialise(sliced_demand),
            "compensation_signals": _serialise(comp_signals),
            "layoff_signals": _serialise(LAYOFF_SIGNALS),
        },
        indent=2,
        default=str,
    )

    return f"""You are a market intelligence assistant for tech professionals exploring the job market.

You have access to the following real-time market data, fetched specifically for the user's context:

<market_data>
{context_block}
</market_data>

Instructions:
- Answer the user's question using ONLY the data provided above.
- Be direct and specific. Quote numbers, trends, and verdicts from the data when relevant.
- If the user asks about something not covered by the data above (e.g. a role, location, or time period not in the dataset), say clearly that you don't have data for that and suggest what you can answer.
- Do not speculate beyond what the data supports. Explicitly flag uncertainty when confidence is low.
- Keep responses concise and evidence-backed. Avoid generic career advice not grounded in the signals above.
- When referencing salary figures, note that the currency depends on location (GBP for London, USD for New York and Remote).
"""


# ---------------------------------------------------------------------------
# Reasoning trace builder
# ---------------------------------------------------------------------------

def _build_reasoning_trace(
    user_messages: list[ChatMessage],
    context: ChatContext,
    signal: MarketHealthSignal | None,
    demand_signals: list[DemandSignal],
    comp_signals: list[CompensationSignal],
) -> ReasoningTrace:
    """
    Builds the reasoning trace from what was assembled before the LLM call.
    All fields are deterministic — derived from the context and data actually fetched.
    """
    role, seniority, location = context.role, context.seniority, context.location

    last_user_msg = next(
        (m.content for m in reversed(user_messages) if m.role == "user"), ""
    )
    active_filters = [f for f in [
        role if role != "all" else None,
        seniority if seniority != "all" else None,
        location if location != "all" else None,
    ] if f]
    filter_desc = " · ".join(active_filters) if active_filters else "none (all roles, seniority levels, and locations)"

    input_context = (
        f'User question: "{last_user_msg}". '
        f"Context filters: {filter_desc}. "
        f"Model: {_CHAT_MODEL}."
    )

    sources: list[SourceAccess] = []
    seq = 1

    sources.append(SourceAccess(
        sequence=seq,
        source_type="data_source",
        name="Market Health Dataset",
        purpose=(
            f"Retrieve overall market health verdict and trend direction"
            f"{' for ' + ', '.join(active_filters) if active_filters else ''}"
        ),
    ))
    seq += 1

    if demand_signals:
        n = len(demand_signals)
        sources.append(SourceAccess(
            sequence=seq,
            source_type="data_source",
            name="Job Openings Dataset",
            purpose=(
                f"Retrieve month-over-month job opening counts for "
                f"{n} role/location combination{'s' if n != 1 else ''}"
            ),
        ))
        seq += 1

    if comp_signals:
        n = len(comp_signals)
        sources.append(SourceAccess(
            sequence=seq,
            source_type="data_source",
            name="Compensation Dataset",
            purpose=(
                f"Retrieve salary ranges and trend direction for "
                f"{n} role/location combination{'s' if n != 1 else ''}"
            ),
        ))
        seq += 1

    n_layoffs = len(LAYOFF_SIGNALS)
    sources.append(SourceAccess(
        sequence=seq,
        source_type="data_source",
        name="Layoff Events Dataset",
        purpose=f"Retrieve recent tech layoff events ({n_layoffs} event{'s' if n_layoffs != 1 else ''} in dataset)",
    ))
    seq += 1

    sources.append(SourceAccess(
        sequence=seq,
        source_type="tool",
        name="Context Injector",
        purpose=(
            f"Assemble all market signals into a structured system instruction "
            f"and pass them to {_CHAT_MODEL} as grounding context"
        ),
    ))

    steps: list[ReasoningStep] = []
    step_seq = 1

    if signal:
        steps.append(ReasoningStep(
            sequence=step_seq,
            content=(
                f"Retrieved market health signal: verdict is '{signal.verdict}', "
                f"trend is {signal.trend_direction}. "
                f"Source: {signal.source}."
            ),
        ))
        step_seq += 1

    if demand_signals:
        n = len(demand_signals)
        steps.append(ReasoningStep(
            sequence=step_seq,
            content=(
                f"Retrieved job opening trends for {n} "
                f"role/seniority/location combination{'s' if n != 1 else ''}. "
                f"Last 6 months of data included for each."
            ),
        ))
        step_seq += 1

    if comp_signals:
        n = len(comp_signals)
        steps.append(ReasoningStep(
            sequence=step_seq,
            content=(
                f"Retrieved salary data for {n} "
                f"role/seniority/location combination{'s' if n != 1 else ''}, "
                f"including minimum, maximum, and median annual figures."
            ),
        ))
        step_seq += 1

    steps.append(ReasoningStep(
        sequence=step_seq,
        content=(
            f"Retrieved {n_layoffs} recent tech layoff event{'s' if n_layoffs != 1 else ''} "
            f"from the dataset, including company, sector, date, and headcount affected."
        ),
    ))
    step_seq += 1

    steps.append(ReasoningStep(
        sequence=step_seq,
        content=(
            f"Assembled all market signals into a structured context block and passed them "
            f"to {_CHAT_MODEL}. The model was instructed to answer using only the provided "
            f"data and to flag uncertainty when data is insufficient."
        ),
    ))

    return ReasoningTrace(
        input_context=input_context,
        sources_and_tools=sources,
        reasoning_steps=steps,
        is_complete=True,
    )


# ---------------------------------------------------------------------------
# Vercel AI SDK data-stream helpers
# Wire format used by useChat({ streamProtocol: "data" })
#   2:[json_array]\n   — data part (goes into useChat's `data` array)
#   0:json_string\n    — text part (accumulated into message.content)
#   d:{json}\n         — finish delta (triggers onFinish)
# ---------------------------------------------------------------------------

def _sdk_data(payload: dict) -> str:
    """Vercel AI SDK data part: items from the JSON array land in useChat's `data` prop."""
    return f"2:{json.dumps([payload], default=str)}\n"


def _sdk_text(text: str) -> str:
    """Vercel AI SDK text part: accumulated into the current assistant message content."""
    return f"0:{json.dumps(text)}\n"


def _sdk_finish(finish_reason: str = "stop") -> str:
    """Vercel AI SDK finish delta: signals stream end and triggers onFinish."""
    return f"d:{json.dumps({'finishReason': finish_reason, 'usage': {'promptTokens': 0, 'completionTokens': 0}})}\n"


# ---------------------------------------------------------------------------
# Streaming generator
# ---------------------------------------------------------------------------

async def _stream_response(
    messages: list[ChatMessage],
    system_prompt: str,
    trace: ReasoningTrace,
) -> AsyncIterator[str]:
    """
    Streams the AI response in Vercel AI SDK data-stream format.

    Event order:
      1. reasoning_trace data part  — first, before any tokens
      2. text parts                 — one per chunk
      3. finish_message data part   — includes generation_time_ms
      4. finish delta               — tells useChat the stream is done

    Provider and model are declared via _CHAT_MODEL above.
    To switch providers, change the providers.* call below — nothing else changes.
    """
    start_time = time.time()

    # 1. Reasoning trace — emitted before the LLM call starts
    yield _sdk_data({
        "type": "reasoning_trace",
        "trace": dataclasses.asdict(trace),
    })

    # 2. Stream response through the provider abstraction
    provider = providers.gemini(_CHAT_MODEL)
    try:
        async for chunk in provider.stream(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            system=system_prompt,
        ):
            yield _sdk_text(chunk)

    except Exception as exc:
        logger.error("LLM provider error (%s): %s", _CHAT_MODEL, exc)
        msg = str(exc).lower()
        if any(w in msg for w in ("connection", "network", "timeout", "unreachable")):
            yield _sdk_text("\n\n[The AI service is currently unreachable. Please try again shortly.]")
        else:
            yield _sdk_text("\n\n[The AI service returned an error. Please try again.]")

    # 3. Finish data event with wall-clock generation time
    generation_time_ms = int((time.time() - start_time) * 1000)
    yield _sdk_data({
        "type": "finish_message",
        "finishReason": "stop",
        "generation_time_ms": generation_time_ms,
    })

    # 4. Finish delta — signals stream end to useChat
    yield _sdk_finish()


# ---------------------------------------------------------------------------
# GET /api/chat/context
# ---------------------------------------------------------------------------

@router.get("/api/chat/context")
async def get_chat_context(
    role: str = "all",
    seniority: str = "all",
    location: str = "all",
):
    """
    Returns the market context injected into Gemini's system instruction for the
    given filter combination. Useful for debugging context injection.
    """
    try:
        signal, _ = _resolve_signal(role, seniority, location)
        demand_signals = _filter_demand(role, seniority, location)
        comp_signals = _filter_compensation(role, seniority, location)
    except Exception as exc:
        logger.exception("Failed to resolve chat context: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to load market context.")

    return {
        "signal": _serialise(signal) if signal else None,
        "demand_count": len(demand_signals),
        "comp_count": len(comp_signals),
        "layoff_count": len(LAYOFF_SIGNALS),
        "model": _CHAT_MODEL,
    }


# ---------------------------------------------------------------------------
# POST /api/chat
# ---------------------------------------------------------------------------

@router.post("/api/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """
    Accepts the user's conversation history and streams a Gemini response
    as structured Server-Sent Events (text/event-stream).

    The first event is always a reasoning_trace containing the full context
    and data sources used to generate the response. Token events follow.
    The last event is finish_message with wall-clock generation_time_ms.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages array must not be empty.")

    for msg in request.messages:
        if msg.role not in {"user", "assistant"}:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid message role '{msg.role}'. Must be 'user' or 'assistant'.",
            )
        if not msg.content or not msg.content.strip():
            raise HTTPException(
                status_code=400,
                detail="Each message must have non-empty content.",
            )

    if request.messages[0].role != "user":
        raise HTTPException(
            status_code=400,
            detail="The first message must have role 'user'.",
        )

    context = request.context
    try:
        signal, _ = _resolve_signal(context.role, context.seniority, context.location)
        demand_signals = _filter_demand(context.role, context.seniority, context.location)
        comp_signals = _filter_compensation(context.role, context.seniority, context.location)
        system_prompt = _build_system_prompt(context)
    except Exception as exc:
        logger.exception("Failed to build system prompt: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch market data for context injection.",
        )

    trace = _build_reasoning_trace(
        user_messages=request.messages,
        context=context,
        signal=signal,
        demand_signals=demand_signals,
        comp_signals=comp_signals,
    )

    return StreamingResponse(
        _stream_response(request.messages, system_prompt, trace),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
