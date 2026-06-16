"""
FastAPI router for the conversational endpoint.

Endpoint:
  POST /api/chat

Fetches the current market summary and trends for the given context,
prepends them as a system message to Claude, then streams the response
as Server-Sent Events using text/event-stream.

Wire format: Vercel AI SDK data-stream protocol.
  data: {"type":"text","value":"<chunk>"}\n\n
  data: [DONE]\n\n
"""

from __future__ import annotations

import dataclasses
import json
import logging
from datetime import date
from typing import AsyncIterator

import anthropic
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from market_health import _resolve_signal, _filter_demand, _filter_compensation, _serialise
from mock_data import LAYOFF_SIGNALS, slice_posting_trend

logger = logging.getLogger(__name__)

router = APIRouter()

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 1024

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
    system message for Claude.
    """
    role, seniority, location = context.role, context.seniority, context.location

    signal, implication = _resolve_signal(role, seniority, location)
    demand_signals = _filter_demand(role, seniority, location)
    comp_signals = _filter_compensation(role, seniority, location)
    # Slice posting trends to 6m for context (default)
    sliced_demand = [
        dataclasses.replace(d, posting_trend=slice_posting_trend(d.posting_trend, "6m"))
        for d in demand_signals
    ]

    # Serialise to JSON-compatible dicts
    signal_data = _serialise(signal) if signal else None
    implication_data = _serialise(implication) if implication else None
    demand_data = _serialise(sliced_demand)
    comp_data = _serialise(comp_signals)
    layoff_data = _serialise(LAYOFF_SIGNALS)

    context_block = json.dumps(
        {
            "filters_applied": {
                "role": role,
                "seniority": seniority,
                "location": location,
            },
            "market_health_signal": signal_data,
            "search_implication": implication_data,
            "demand_signals": demand_data,
            "compensation_signals": comp_data,
            "layoff_signals": layoff_data,
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
# SSE helpers — Vercel AI SDK data-stream wire format
# ---------------------------------------------------------------------------

def _sse_text_chunk(chunk: str) -> str:
    payload = json.dumps({"type": "text", "value": chunk})
    return f"data: {payload}\n\n"


def _sse_done() -> str:
    return "data: [DONE]\n\n"


def _sse_error(message: str) -> str:
    payload = json.dumps({"type": "error", "value": message})
    return f"data: {payload}\n\n"


# ---------------------------------------------------------------------------
# Streaming generator
# ---------------------------------------------------------------------------

async def _stream_claude(
    messages: list[ChatMessage],
    system_prompt: str,
) -> AsyncIterator[str]:
    """
    Calls the Anthropic API with streaming and yields plain text chunks.
    The frontend uses streamProtocol: "text" which reads the raw body stream.
    """
    client = anthropic.AsyncAnthropic()

    anthropic_messages = [
        {"role": m.role, "content": m.content} for m in messages
    ]

    try:
        async with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            messages=anthropic_messages,
        ) as stream:
            async for text_chunk in stream.text_stream:
                yield text_chunk

    except anthropic.APIConnectionError as exc:
        logger.error("Anthropic API connection error: %s", exc)
        yield "\n\n[The AI service is currently unreachable. Please try again shortly.]"
    except anthropic.APIStatusError as exc:
        logger.error("Anthropic API status error %s: %s", exc.status_code, exc.message)
        yield f"\n\n[The AI service returned an error (status {exc.status_code}).]"
    except Exception as exc:
        logger.exception("Unexpected error during Claude streaming: %s", exc)
        yield "\n\n[An unexpected error occurred. Please try again.]"


# ---------------------------------------------------------------------------
# POST /api/chat
# ---------------------------------------------------------------------------

@router.post("/api/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """
    Accepts the user's conversation history and streams a Claude response
    as Server-Sent Events (text/event-stream).

    Returns 400 for malformed input, 502 if the Anthropic API is unreachable.
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

    # Anthropic requires messages to start with role=user
    if request.messages[0].role != "user":
        raise HTTPException(
            status_code=400,
            detail="The first message must have role 'user'.",
        )

    try:
        system_prompt = _build_system_prompt(request.context)
    except Exception as exc:
        logger.exception("Failed to build system prompt: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch market data for context injection.",
        )

    return StreamingResponse(
        _stream_claude(request.messages, system_prompt),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
