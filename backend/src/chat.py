"""
FastAPI router for the conversational endpoint.

Endpoint:
  POST /api/chat

Answers by analysing the platform's own data for the specific question asked
(via the query_* tools) — and ONLY that data. No web search, no model general
knowledge, no fixed pre-computed context blob. A question the data can't reach
gets a plain "we don't track that" plus a pointer to what it can answer, never
an outside answer (revised 2026-09-06 —
changes/2026-09-06-chat-answer-truncation-and-curated-match.md). See
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
import os
import time
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import curated_answers
from llm import providers
from llm.base import StreamOutcome
from llm.chat_fallback import ChatModelUnavailable, call_with_retry, stream_with_retry
from pydantic import BaseModel

from ai_interaction_settings import (
    CHAT_PAID_DAILY_REQUEST_CAP,
    CHAT_SYNTHESIS_MAX_OUTPUT_TOKENS,
    MAX_USER_MESSAGE_CHARS,
    SYNTHESIS_HISTORY_WINDOW_MESSAGES,
    TOOL_STAGE_HISTORY_MESSAGES,
)
from db import get_connection
from market_health import _resolve_signal, _filter_demand, _filter_compensation, _serialise
from market_query import query_compensation_data, query_market_data, query_requirements_data
from mock_data import LAYOFF_SIGNALS
from models import ReasoningStep, ReasoningTrace, SourceAccess

logger = logging.getLogger(__name__)

router = APIRouter()

# Provider and model — explicit at the call site per outcome ai-provider-flexibility.
# REVISED 2026-09-06 (changes/2026-09-03-chat-resilience-and-instant-answers.md): the free
# tier is removed from chat. Its gemini-3.6-flash quota is 20 requests/day (~6 chat turns)
# and it is slower and less predictable than paid; "free-first" also wasted ~8s/request
# retrying a spent tier. Chat now uses ONE model: gemini-3.6-flash on the dedicated,
# isolated, spend-capped paid project (GEMINI_API_KEY_CHAT_PAID). GEMINI_API_KEY (the old
# free key) is no longer read here.
_CHAT_MODEL = "gemini-3.6-flash"

_DEGRADED_MESSAGE = (
    "The assistant is briefly unavailable — please try again in a moment. "
    "Meanwhile, the suggested questions answer instantly, and “About this platform” "
    "and “What we know about the market” in the task panel never use AI."
)


def _chat_paid_requests_today() -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT requests FROM chat_paid_usage WHERE usage_date = (now() AT TIME ZONE 'UTC')::date"
        ).fetchone()
        return row[0] if row else 0


def _record_chat_paid_request() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_paid_usage (usage_date, requests)
            VALUES ((now() AT TIME ZONE 'UTC')::date, 1)
            ON CONFLICT (usage_date) DO UPDATE SET requests = chat_paid_usage.requests + 1
            """
        )


def _model_available() -> bool:
    """The paid model is usable only if its key is set AND today's request count is
    under the cap. Otherwise the model stages are skipped entirely — chat degrades to
    the curated instant-answer path / the 'briefly unavailable' message."""
    if not os.environ.get("GEMINI_API_KEY_CHAT_PAID"):
        return False
    return _chat_paid_requests_today() < CHAT_PAID_DAILY_REQUEST_CAP


def _chat_provider():
    """The single chat model tier — gemini-3.6-flash on the dedicated paid project."""
    return providers.gemini(_CHAT_MODEL, api_key=os.environ["GEMINI_API_KEY_CHAT_PAID"])


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
Today's date is {today}. You have three tools to examine real, live-classified job posting \
data — call whichever fit (or several) as needed to answer the user's question with real numbers:
- query_market_data: demand/volume questions — counts, trends, comparisons across role, \
specialization, level, track, or country.
- query_compensation_data: salary/pay questions. Never blend its structured_count and \
parsed_count figures into one number — lead with the structured (disclosed) figure when it \
exists, mention the parsed (estimated) one separately and label it as an estimate, and say \
plainly if neither exists rather than guessing.
- query_requirements_data: skills/technologies, education, years of experience, work \
arrangement (remote/hybrid/onsite), and language questions, and the data half of any \
synthesis question ("should I learn X", "what should I focus on"). For a question about a \
specific named technology ("is Rust in demand", "should I learn Kubernetes"), pass that name \
as the raw_skill filter — one direct query, rather than scanning every skill group. Its \
skills breakdown also has the specific raw_skill mentions behind each skill_group aggregate. \
Every extracted field is an interpretation of free text, not a verified fact — report \
findings as proportions of total_matching ("42% of postings mention X"), never as absolute \
claims. If total_matching is small, say so and be cautious about drawing a firm conclusion \
from it. This tool never returns compensation figures — use query_compensation_data for those.

Below is the recent conversation. Answer the LAST message in it, using the earlier messages \
only to understand what a short reply like "yes please" or "what about X" is referring to.

You answer ONLY from these tools' data. You have no web search and must not use your own \
general knowledge to state a fact, a number, a trend, or a recommendation. Always try the \
tools first — map the question onto the filters available (including raw_skill for a specific \
technology) before concluding the data can't help.

If the data genuinely can't answer — total_matching is 0 because the question falls outside \
data_range, or it's about something job-posting data could never contain (general life \
advice, market history before data_range.earliest, a company or place not in the dataset), \
or the last message is too ambiguous to act on even with the conversation above — prefix your \
entire response with exactly "NO_DATA: " followed by a one-sentence statement of what the \
platform doesn't have and the nearest thing it *could* speak to. Then on a new line write \
anything you WERE able to determine from the data (write "(nothing)" if the data contributed \
nothing). Do not answer the missing part from outside the data.

If the data can answer the question, respond directly and specifically: state the data's time \
window (from data_range) and the real numbers returned. Never state a number or claim the tool \
did not actually return."""


async def _query_platform_data(recent_messages: list[ChatMessage]):
    """
    Stage 1 (runs when the curated catalogue didn't match): let the model query
    real data for this specific question, not a fixed pre-computed blob.
    `recent_messages` is a bounded window (TOOL_STAGE_HISTORY_MESSAGES), not the
    full conversation — enough to resolve a short follow-up, not enough to grow
    cost with conversation length. Returns the model's text (possibly prefixed
    "NO_DATA: ...") and the real tool calls made (for the reasoning trace).
    Raises ChatModelUnavailable if the paid model can't be reached after retries.
    """
    today = datetime.now(timezone.utc).date().isoformat()

    async def _call(provider):
        return await provider.complete_with_tools(
            prompt=_render_transcript(recent_messages),
            system=_DATA_STAGE_SYSTEM_TEMPLATE.format(today=today),
            tools=[query_market_data, query_compensation_data, query_requirements_data],
        )

    response = await call_with_retry(_chat_provider(), _call)
    _record_chat_paid_request()
    return response.text, response.tool_calls


# There is no Stage 2. A "Stage 2 — real external sources" (Google Search
# grounding) lived here until 2026-09-06; chat is now DB-only
# (changes/2026-09-06-chat-answer-truncation-and-curated-match.md). The stage
# numbering is kept (Stage 1 → Stage 3) so existing references still resolve.

_NO_DATA_MARKER = "NO_DATA:"


def _has_no_data_marker(stage1_text: str) -> bool:
    """True when Stage 1 declared the platform's data can't answer the question.
    The synthesis stage then composes an honest "we don't track that" reply from
    whatever Stage 1 could determine — it never routes anywhere else."""
    return stage1_text.lstrip().startswith(_NO_DATA_MARKER)


# ---------------------------------------------------------------------------
# Stage 3 — final synthesis (this is what actually streams to the user)
# ---------------------------------------------------------------------------

def _build_synthesis_system(stage1_text: str, tool_calls: list) -> str:
    if tool_calls:
        raw_results = "\n".join(f"{c.name}({c.args}) -> {c.result}" for c in tool_calls)
    else:
        raw_results = "(no platform data was queried for this question)"

    no_data = _has_no_data_marker(stage1_text)

    sections = [
        "You are a market intelligence assistant for tech professionals. Write the final answer "
        "to the user's question using ONLY the platform's own data below — never the open web, "
        "never your own general knowledge, never an invented number, category, or statistic.",
        "",
        "RAW PLATFORM DATA (ground truth — the only real numbers, if any):",
        raw_results,
        "",
        "What the data-query stage concluded (context; if it conflicts with RAW PLATFORM DATA, "
        "the raw data wins):",
        stage1_text or "(none)",
        "",
        "Style: answer conversationally and concisely — a few sentences, or a short bullet list "
        "for several figures. Not a multi-section report, no headings. State the data's time "
        "window once. Proportions carry their denominator; never an absolute claim. Structured "
        "and parsed compensation are never blended into one number.",
    ]
    if no_data:
        sections += [
            "",
            "The data-query stage marked this NO_DATA — the platform doesn't track what was "
            "asked. Say that plainly and briefly, name the nearest thing the data *can* speak "
            "to, and suggest one or two questions the platform can actually answer. Do NOT "
            "answer the missing part from outside the platform's data.",
        ]
    else:
        sections += [
            "",
            "If RAW PLATFORM DATA is empty, say plainly you don't have that in the platform's "
            "data rather than guessing.",
            "",
            "If the question asks for a judgment or recommendation (\"should I learn X\", "
            "\"what should I focus on\") and query_requirements_data was called: two clearly "
            "separated parts — first the underlying data (real proportions/counts), then, on "
            "its own line, your judgment built on that data. Never blend them. The judgment "
            "reasons over these numbers only, not outside advice. If total_matching is too "
            "small for a confident conclusion, give the data alone and say the sample is too "
            "small — don't guess a recommendation anyway.",
        ]
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Reasoning trace — built from what was actually done, not pre-computed
# ---------------------------------------------------------------------------

def _build_reasoning_trace(
    question: str,
    tool_calls: list,
    *,
    truncated: bool = False,
) -> ReasoningTrace:
    """Trace for a model-composed chat turn. Chat is DB-only — every source is
    one of the platform's own owned-data queries; there is never an external
    entry. `truncated=True` marks a Stage 3 answer that was cut short."""
    sources: list[SourceAccess] = []
    steps: list[ReasoningStep] = []
    seq = 1
    step_seq = 1

    for call in tool_calls:
        sources.append(SourceAccess(
            sequence=seq,
            source_type="data_source",
            name="Job Market Database (Greenhouse/Lever/Ashby-sourced, LLM-classified)",
            purpose=f"{call.name}({call.args})",
        ))
        seq += 1
        result = call.result if isinstance(call.result, dict) else {}
        data_range = result.get("data_range", {})
        steps.append(ReasoningStep(
            sequence=step_seq,
            content=(
                f"Queried the platform's data via {call.name}({call.args}). Found "
                f"{result.get('total_matching', 0)} matching postings, data available from "
                f"{data_range.get('earliest')} to {data_range.get('latest')}."
            ),
        ))
        step_seq += 1

    if not tool_calls:
        steps.append(ReasoningStep(
            sequence=step_seq,
            content="Determined the platform's dataset was not relevant to this question.",
        ))
        step_seq += 1

    steps.append(ReasoningStep(
        sequence=step_seq,
        content=(
            "The answer was cut short before it finished — it is incomplete, not a "
            "completed response."
            if truncated
            else "Synthesised the final answer from the platform's own data."
        ),
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

# Vercel AI SDK finishReason values, keyed by our provider-neutral StreamStop.
_SDK_FINISH_REASON = {
    "complete": "stop",
    "truncated": "length",
    "filtered": "content-filter",
    "error": "error",
}


def _curated_trace(question: str, tool_calls: list) -> ReasoningTrace:
    """Trace for a curated instant answer — the real query it ran, and an explicit
    'no model' step (Principle 4, full inspectability)."""
    trace = _build_reasoning_trace(question, tool_calls)
    # _build_reasoning_trace always ends with a "Synthesised the final answer…"
    # step — no synthesis happens on the curated path, so replace it.
    if trace.reasoning_steps:
        trace.reasoning_steps.pop()
    trace.reasoning_steps.append(ReasoningStep(
        sequence=len(trace.reasoning_steps) + 1,
        content="Filled a pre-built answer template from that query's results. No language model was used.",
    ))
    return trace


async def _stream_response(
    messages: list[ChatMessage],
) -> AsyncIterator[str]:
    """
    Streams the AI response in Vercel AI SDK data-stream format.

    Event order: reasoning_trace data part → text parts → finish_message → finish delta.

    Path selection:
      1. Curated instant answer (curated_answers.match) — no model call, sub-second.
      2. Otherwise the model stages (Stage 1 owned-data tools → Stage 3 synthesis
         stream) on the single paid tier (_chat_provider). DB-only — no web search.
      3. If the paid model is unavailable / its daily cap is spent — the calm
         degraded message. Never a hang or a bare error.
    See changes/2026-09-03-chat-resilience-and-instant-answers.md and
    changes/2026-09-06-chat-answer-truncation-and-curated-match.md.
    """
    start_time = time.time()
    question = next((m.content for m in reversed(messages) if m.role == "user"), "")

    def _finish(finish_reason: str = "stop") -> str:
        ms = int((time.time() - start_time) * 1000)
        return _sdk_data({
            "type": "finish_message",
            "finishReason": finish_reason,
            "generation_time_ms": ms,
        })

    # ── Path 1: curated instant answer (no model call) ────────────────────────
    curated = curated_answers.match(question)
    if curated is not None:
        try:
            answer_text, tool_calls = curated.builder()
            yield _sdk_data({
                "type": "reasoning_trace",
                "trace": dataclasses.asdict(_curated_trace(question, tool_calls)),
            })
            yield _sdk_text(answer_text)
            yield _finish()
            yield _sdk_finish()
            return
        except Exception as exc:
            # A curated builder failing (e.g. a DB blip) is not fatal — fall
            # through to the model path rather than erroring the whole request.
            logger.warning("Curated answer '%s' failed, falling through to the model: %s", curated.id, exc)

    # ── Path 3 (pre-check): the model isn't available at all ──────────────────
    if not _model_available():
        logger.warning("Chat model unavailable (key missing or daily cap reached) and no curated match.")
        yield _sdk_data({
            "type": "reasoning_trace",
            "trace": dataclasses.asdict(_build_reasoning_trace(question, [])),
        })
        yield _sdk_text(_DEGRADED_MESSAGE)
        yield _finish()
        yield _sdk_finish()
        return

    # ── Path 2: the model stages ─────────────────────────────────────────────
    # Bounded windows, not full history — see backend/AI_INTERACTION_SETTINGS.md.
    tool_stage_messages = _recent(messages, TOOL_STAGE_HISTORY_MESSAGES)
    synthesis_messages = _recent(messages, SYNTHESIS_HISTORY_WINDOW_MESSAGES)

    try:
        stage1_text, tool_calls = await _query_platform_data(tool_stage_messages)
    except ChatModelUnavailable as exc:
        logger.error("Stage 1 unavailable after retries: %s", exc)
        yield _sdk_data({
            "type": "reasoning_trace",
            "trace": dataclasses.asdict(_build_reasoning_trace(question, [])),
        })
        yield _sdk_text(_DEGRADED_MESSAGE)
        yield _finish()
        yield _sdk_finish()
        return
    except Exception as exc:
        logger.error("Stage 1 (query_market_data) failed: %s", exc)
        stage1_text, tool_calls = "(platform data query failed)", []

    no_data = _has_no_data_marker(stage1_text)

    # Anti-fabrication guard: if the model neither called a data tool nor marked
    # the question NO_DATA, its text is untrusted — a confused model will sometimes
    # answer with fabricated numbers instead of abstaining. Never let that reach synthesis.
    if not tool_calls and not no_data:
        logger.warning("Stage 1 produced ungrounded text with no tool call and no NO_DATA marker; discarding it.")
        stage1_text = "(no real platform data was retrieved for this question)"

    trace = _build_reasoning_trace(question, tool_calls)
    yield _sdk_data({"type": "reasoning_trace", "trace": dataclasses.asdict(trace)})

    # Stage 3 — stream the final synthesis (DB-only, concise, bounded length)
    synthesis_system = _build_synthesis_system(stage1_text, tool_calls)
    synthesis_payload = [{"role": m.role, "content": m.content} for m in synthesis_messages]
    outcome = StreamOutcome()

    def _stream_call(provider):
        return provider.stream(
            messages=synthesis_payload,
            system=synthesis_system,
            max_output_tokens=CHAT_SYNTHESIS_MAX_OUTPUT_TOKENS,
            outcome=outcome,
        )

    recorded_synthesis = False
    stream_errored = False
    try:
        async for chunk in stream_with_retry(_chat_provider(), _stream_call):
            if not recorded_synthesis:
                recorded_synthesis = True
                _record_chat_paid_request()
            yield _sdk_text(chunk)
    except ChatModelUnavailable as exc:
        stream_errored = True
        logger.error("Synthesis stage unavailable after retries: %s", exc)
        yield _sdk_text("\n\n" + _DEGRADED_MESSAGE)
    except Exception as exc:
        stream_errored = True
        logger.error("LLM provider error (%s): %s", _CHAT_MODEL, exc)
        yield _sdk_text("\n\n" + _DEGRADED_MESSAGE)

    # Provider-neutral stop reason (llm.base.StreamStop) — never Gemini's raw enum.
    # An answer cut short is never presented as if it were complete.
    finish_reason = "stop"
    if not stream_errored and outcome.stop != "complete":
        if outcome.stop == "truncated":
            yield _sdk_text(
                "\n\n_(This answer was cut off before it finished. Ask me to continue "
                "and I'll pick up where it stopped.)_"
            )
        elif outcome.stop == "filtered":
            yield _sdk_text(
                "\n\n_(The rest of this answer was withheld by a safety filter.)_"
            )
        else:  # "error"
            yield _sdk_text("\n\n" + _DEGRADED_MESSAGE)
        finish_reason = _SDK_FINISH_REASON.get(outcome.stop, "error")
        # Re-emit the trace with the truncation marked — a partial answer's
        # provenance must say it was cut short (ai-reasoning-panel spec).
        yield _sdk_data({
            "type": "reasoning_trace",
            "trace": dataclasses.asdict(
                _build_reasoning_trace(question, tool_calls, truncated=True)
            ),
        })
    elif stream_errored:
        finish_reason = "error"

    yield _finish(finish_reason)

    # 4. Finish delta — signals stream end to useChat
    yield _sdk_finish(finish_reason)


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
