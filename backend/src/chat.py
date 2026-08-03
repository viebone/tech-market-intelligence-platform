"""
FastAPI router for the conversational endpoint.

Endpoint:
  POST /api/chat

Answers by analysing the platform's own data for the specific question asked
(via the query_market_data tool), falling back to real, cited external
sources only when the platform's data genuinely can't answer — never a fixed
pre-computed context blob, never an unverified "general knowledge" claim. See
backend/specs/market-health/api.md — Business Logic — Conversational data
sourcing, and design/market-health/experience.md's sourcing rule.

Wire format: structured SSE data events (unchanged from before this change).
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
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from llm import providers
from pydantic import BaseModel

from ai_interaction_settings import (
    MAX_USER_MESSAGE_CHARS,
    SYNTHESIS_HISTORY_WINDOW_MESSAGES,
    TOOL_STAGE_HISTORY_MESSAGES,
)
from market_health import _resolve_signal, _filter_demand, _filter_compensation, _serialise
from market_query import query_market_data
from mock_data import LAYOFF_SIGNALS
from models import ReasoningStep, ReasoningTrace, SourceAccess

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
# Shared: bounded recent-history rendering
# See backend/AI_INTERACTION_SETTINGS.md for why these windows exist and why
# they're sized differently per stage.
# ---------------------------------------------------------------------------

def _recent(messages: list[ChatMessage], window: int) -> list[ChatMessage]:
    return messages[-window:]


def _render_transcript(messages: list[ChatMessage]) -> str:
    """Recent conversation as a readable mini-transcript, latest message last."""
    return "\n".join(f"{m.role}: {m.content}" for m in messages)


# ---------------------------------------------------------------------------
# Stage 1 — query the platform's own data
# ---------------------------------------------------------------------------

_DATA_STAGE_SYSTEM_TEMPLATE = """You are a market intelligence assistant for tech professionals. \
Today's date is {today}. Answer using the query_market_data tool to examine real, \
live-classified job posting data — call it as needed to answer the user's question with real \
numbers.

Below is the recent conversation. Answer the LAST message in it, using the earlier messages \
only to understand what a short reply like "yes please" or "what about X" is referring to.

Always check the tool's data_range and total_matching fields. If total_matching is 0 because \
the question falls outside data_range, or the question is about something the tool could \
never answer (general career advice, market history before data_range.earliest, industry \
context not derivable from job postings), do not guess or use your own general knowledge here. \
Instead, prefix your entire response with exactly "NEEDS_EXTERNAL: " followed by a one-sentence \
description of what's missing, then on a new line write anything you WERE able to determine \
from the data (write "(nothing)" if the data contributed nothing).

If you cannot tell what the last message is asking even with the conversation above — it's too \
ambiguous, or references something not present in the conversation shown — prefix your response \
with exactly "NEEDS_EXTERNAL: " followed by that explanation. Never invent an answer, a \
category, or a number that didn't come from an actual query_market_data call.

If the data can answer the question, respond directly and specifically: state the data's time \
window (from data_range) and the real numbers returned. Never state a number or claim the tool \
did not actually return."""


async def _query_platform_data(recent_messages: list[ChatMessage]):
    """
    Stage 1 (always tried first): let the model query real data for this
    specific question, not a fixed pre-computed blob. `recent_messages` is a
    bounded window (TOOL_STAGE_HISTORY_MESSAGES), not the full conversation —
    enough to resolve a short follow-up, not enough to grow cost with
    conversation length. Returns the model's text (possibly prefixed
    "NEEDS_EXTERNAL: ...") and the real tool calls made, for the reasoning trace.
    """
    provider = providers.gemini(_CHAT_MODEL)
    today = datetime.now(timezone.utc).date().isoformat()
    response = await provider.complete_with_tools(
        prompt=_render_transcript(recent_messages),
        system=_DATA_STAGE_SYSTEM_TEMPLATE.format(today=today),
        tools=[query_market_data],
    )
    return response.text, response.tool_calls


# ---------------------------------------------------------------------------
# Stage 2 — real external sources (only when stage 1 can't answer)
# ---------------------------------------------------------------------------

_SEARCH_STAGE_SYSTEM = """You are filling a gap in a job-market platform's own data using real \
web search. Search for real, citable sources (articles, reports, named studies) relevant to \
the question. If you cannot find a real source, say so plainly rather than answering from \
unverified memory. Never state a claim without a source you actually found via search."""


def _needs_external(stage1_text: str) -> tuple[bool, str]:
    """Parse stage 1's NEEDS_EXTERNAL marker. Returns (needed, gap_description)."""
    marker = "NEEDS_EXTERNAL:"
    if not stage1_text.startswith(marker):
        return False, ""
    first_line, _, _ = stage1_text[len(marker):].partition("\n")
    return True, first_line.strip()


async def _search_external_sources(recent_messages: list[ChatMessage], gap_description: str):
    """Stage 2: real, cited external sources for what stage 1 couldn't answer."""
    provider = providers.gemini(_CHAT_MODEL)
    prompt = (
        f'The platform\'s own job market data could not answer this: "{gap_description}"\n'
        f"Recent conversation:\n{_render_transcript(recent_messages)}\n\n"
        "Find real, citable external sources to help answer the last message."
    )
    return await provider.complete_with_search_grounding(prompt=prompt, system=_SEARCH_STAGE_SYSTEM)


# ---------------------------------------------------------------------------
# Stage 3 — final synthesis (this is what actually streams to the user)
# ---------------------------------------------------------------------------

def _build_synthesis_system(
    stage1_text: str,
    tool_calls: list,
    grounded_text: str | None,
    grounded_sources: list,
) -> str:
    if tool_calls:
        raw_results = "\n".join(f"query_market_data({c.args}) -> {c.result}" for c in tool_calls)
    else:
        raw_results = "(no platform data was queried for this question)"

    sections = [
        "You are a market intelligence assistant for tech professionals. Write the final answer "
        "to the user's question using ONLY the findings below — do not add facts beyond them, "
        "and never invent a number, category, or statistic that isn't in RAW PLATFORM DATA.",
        "",
        "RAW PLATFORM DATA (ground truth — the only real numbers, if any):",
        raw_results,
        "",
        "Summary of what the data-query stage concluded (for context; if this ever conflicts "
        "with RAW PLATFORM DATA above, the raw data wins):",
        stage1_text or "(none)",
    ]
    if grounded_text is not None:
        sources_list = "\n".join(f"- {s.title} ({s.url})" for s in grounded_sources) or "(no sources found)"
        sections += [
            "",
            "EXTERNAL SOURCE FINDINGS:",
            grounded_text,
            "",
            "External sources found:",
            sources_list,
        ]
    sections += [
        "",
        "Rules: state plainly which parts of your answer come from the platform's own data and "
        "which come from an external source — never blend the two without saying which is which. "
        "If RAW PLATFORM DATA is empty and no external search was done, say plainly that you "
        "don't have enough information rather than guessing. Never cite a source that isn't "
        "listed above.",
    ]
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Reasoning trace — built from what was actually done, not pre-computed
# ---------------------------------------------------------------------------

def _build_reasoning_trace(
    question: str,
    tool_calls: list,
    used_external: bool,
    grounded_queries: list[str],
    grounded_sources: list,
) -> ReasoningTrace:
    sources: list[SourceAccess] = []
    steps: list[ReasoningStep] = []
    seq = 1
    step_seq = 1

    for call in tool_calls:
        sources.append(SourceAccess(
            sequence=seq,
            source_type="data_source",
            name="Job Market Database (Greenhouse/Lever/Ashby-sourced, LLM-classified)",
            purpose=f"query_market_data({call.args})",
        ))
        seq += 1
        result = call.result if isinstance(call.result, dict) else {}
        data_range = result.get("data_range", {})
        steps.append(ReasoningStep(
            sequence=step_seq,
            content=(
                f"Queried the platform's data ({call.args}). Found {result.get('total_matching', 0)} "
                f"matching postings, data available from {data_range.get('earliest')} to "
                f"{data_range.get('latest')}."
            ),
        ))
        step_seq += 1

    if not tool_calls:
        steps.append(ReasoningStep(
            sequence=step_seq,
            content="Determined the platform's dataset was not relevant to this question.",
        ))
        step_seq += 1

    if used_external:
        for q in grounded_queries:
            sources.append(SourceAccess(
                sequence=seq,
                source_type="tool",
                name="Google Search",
                purpose=q,
            ))
            seq += 1
        steps.append(ReasoningStep(
            sequence=step_seq,
            content=(
                f"Platform data didn't fully answer the question, so searched real external "
                f"sources and found {len(grounded_sources)} source(s)."
            ),
        ))
        step_seq += 1

    steps.append(ReasoningStep(
        sequence=step_seq,
        content="Synthesised the final answer, attributing platform data and external sources separately.",
    ))

    return ReasoningTrace(
        input_context=f'User question: "{question}".',
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
) -> AsyncIterator[str]:
    """
    Streams the AI response in Vercel AI SDK data-stream format.

    Event order:
      1. reasoning_trace data part  — first, before any tokens
      2. text parts                 — one per chunk, from the stage 3 synthesis call
      3. finish_message data part   — includes generation_time_ms
      4. finish delta               — tells useChat the stream is done

    Provider and model are declared via _CHAT_MODEL above.
    """
    start_time = time.time()
    question = next((m.content for m in reversed(messages) if m.role == "user"), "")
    # Bounded windows, not full history — see backend/AI_INTERACTION_SETTINGS.md.
    tool_stage_messages = _recent(messages, TOOL_STAGE_HISTORY_MESSAGES)
    synthesis_messages = _recent(messages, SYNTHESIS_HISTORY_WINDOW_MESSAGES)

    try:
        stage1_text, tool_calls = await _query_platform_data(tool_stage_messages)
    except Exception as exc:
        logger.error("Stage 1 (query_market_data) failed: %s", exc)
        stage1_text, tool_calls = "(platform data query failed)", []

    used_external, gap = _needs_external(stage1_text)

    # Anti-fabrication guard: if the model neither called the tool nor
    # admitted it needed external help, its text is untrusted — found in
    # testing that a confused model (e.g. a context-dependent follow-up with
    # no history) will sometimes answer with fabricated numbers instead of
    # abstaining, despite the system prompt instructing it not to. Never let
    # that text reach the synthesis stage as if it were real.
    if not tool_calls and not used_external:
        logger.warning("Stage 1 produced ungrounded text with no tool call and no NEEDS_EXTERNAL marker; discarding it.")
        stage1_text = "(no real platform data was retrieved for this question)"

    grounded_text: str | None = None
    grounded_queries: list[str] = []
    grounded_sources: list = []

    if used_external:
        try:
            grounded = await _search_external_sources(tool_stage_messages, gap)
            grounded_text = grounded.text
            grounded_queries = grounded.search_queries
            grounded_sources = grounded.sources
        except Exception as exc:
            logger.error("Stage 2 (search grounding) failed: %s", exc)
            grounded_text = "(external search failed)"

    trace = _build_reasoning_trace(question, tool_calls, used_external, grounded_queries, grounded_sources)

    # 1. Reasoning trace — emitted before the final synthesis call starts
    yield _sdk_data({
        "type": "reasoning_trace",
        "trace": dataclasses.asdict(trace),
    })

    # 2. Stream the final synthesis through the provider abstraction
    synthesis_system = _build_synthesis_system(stage1_text, tool_calls, grounded_text, grounded_sources)
    provider = providers.gemini(_CHAT_MODEL)
    try:
        async for chunk in provider.stream(
            messages=[{"role": m.role, "content": m.content} for m in synthesis_messages],
            system=synthesis_system,
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
    Debug endpoint for /api/market-health/summary's mock context (unchanged
    by this update — the market health signal/implication mock data this
    reads is separate from /api/chat's own data sourcing, see market_query.py).
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

    The first event is always a reasoning_trace built from the real
    query_market_data (and, if needed, search grounding) calls made for this
    specific question — not pre-computed context. Token events follow, from
    a final synthesis call. The last event is finish_message with wall-clock
    generation_time_ms.
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
        if len(msg.content) > MAX_USER_MESSAGE_CHARS:
            # Rejected with a clear reason, not silently truncated — truncation
            # risks cutting off exactly the part that mattered and producing a
            # confusing partial-context answer. See AI_INTERACTION_SETTINGS.md.
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Message is too long ({len(msg.content)} characters, max "
                    f"{MAX_USER_MESSAGE_CHARS}). Please shorten it and try again."
                ),
            )

    if request.messages[0].role != "user":
        raise HTTPException(
            status_code=400,
            detail="The first message must have role 'user'.",
        )

    return StreamingResponse(
        _stream_response(request.messages),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
