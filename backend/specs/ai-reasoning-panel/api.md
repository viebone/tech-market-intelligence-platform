---
id: ai-reasoning-panel
experience: ai-reasoning-panel
directive: low
status: draft
created: 2026-06-25
---

# AI Reasoning Panel — Backend Architecture Spec

## Experience this implements
See: `design/ai-reasoning-panel/experience.md`

Also reads: `backend/specs/market-health/api.md` — the reasoning trace is emitted through
the existing `/api/chat` stream. This spec extends that contract; it does not replace it.

---

## Data Models

No database in v1. Models are Python dataclasses used within the request lifecycle —
generated per response, emitted in the stream, not persisted.

### ReasoningTrace
The full trace for a single AI response. Built server-side during response generation
and emitted as the first event in the stream.

| Field | Type | Description |
|---|---|---|
| `input_context` | `str` | Plain-language summary of what the AI received: the user's question, conversation history included, and any data injected as context |
| `sources_and_tools` | `list[SourceAccess]` | Ordered list of data sources and tools consulted, in access order |
| `reasoning_steps` | `list[ReasoningStep]` | Ordered list of reasoning steps in plain language |
| `is_complete` | `bool` | `True` if all sections captured successfully; `False` if partial |

### SourceAccess
A single data source or tool consulted during response generation.

| Field | Type | Description |
|---|---|---|
| `sequence` | `int` | Access order (1-based) |
| `source_type` | `"data_source" \| "tool"` | Whether this is a data source or an active tool call |
| `name` | `str` | Human-readable name, e.g. `"Job Openings Dataset"`, `"Market Health Calculator"` |
| `purpose` | `str` | One sentence: why this source was consulted for this response |

### ReasoningStep
A single step in the AI's reasoning process.

| Field | Type | Description |
|---|---|---|
| `sequence` | `int` | Step order (1-based) |
| `content` | `str` | Plain-language description of this reasoning step — no jargon, no model-internal language |

---

## API Endpoints

### POST /api/chat — updated stream contract

The existing `/api/chat` endpoint is extended. The request shape is unchanged.
The stream now emits a `reasoning_trace` data event as its **first event**, before
any answer tokens.

**Auth required**: no (v1 — unchanged from market-health spec)

**Request**: unchanged — see `backend/specs/market-health/api.md`

**Updated stream event sequence**:

```
1. reasoning_trace event  ← NEW: emitted first, before any tokens
2. token events           ← unchanged: Vercel AI SDK wire format
3. done event             ← updated: now includes generation_time_ms
```

**Event 1 — reasoning_trace** (new):
```
event: data
data: [{"type":"reasoning_trace","trace":{"input_context":"User asked: 'Is now a good time to search for a senior UX role?' Market data for Designer, PM, and Engineer roles was injected as context.","sources_and_tools":[{"sequence":1,"source_type":"data_source","name":"Job Openings Dataset","purpose":"Retrieve month-over-month opening counts by role category for the selected time range"},{"sequence":2,"source_type":"tool","name":"Market Health Calculator","purpose":"Derive trend direction and magnitude from the time-series data"}],"reasoning_steps":[{"sequence":1,"content":"Retrieved opening counts for Designer, PM, and Engineer roles across the past 12 months."},{"sequence":2,"content":"Identified a 12% month-over-month decline in Designer openings over the last quarter."},{"sequence":3,"content":"PM and Engineer openings remained stable, with less than 3% variance month-over-month."},{"sequence":4,"content":"Concluded the market is cautious for Designers specifically, stable for PM and Engineer roles."}],"is_complete":true}}]
```

**Event 2 — tokens** (unchanged from existing spec):
```
event: data
data: [{"type":"text","value":"The current tech market..."}]
```

**Event 3 — done** (updated to include generation time):
```
event: data
data: [{"type":"finish_message","finishReason":"stop","usage":{"promptTokens":340,"completionTokens":180},"generation_time_ms":2340}]
```

**Errors**: unchanged — see `backend/specs/market-health/api.md`

---

## Business Logic

**Trace is assembled before the LLM call.**
The input context summary and sources_and_tools list are built during context assembly
(before the Anthropic API call), since the data sources and injected context are known
at that point. Reasoning steps come from the LLM's extended thinking output (see below).

**Thinking mode for reasoning steps.**
Use Gemini's thinking capability (`thinking_config` with dynamic budget) to capture the
model's reasoning as structured output. The Gemini response includes a `thought` part
before the answer part — parse this into `reasoning_steps`, splitting on sentence
boundaries or numbered points to produce individual steps. If thinking output is
unavailable or empty, generate a 3–5 step summary from the response content after
generation, using a second lightweight prompt. Never send empty `reasoning_steps` —
if neither method works, set `is_complete: false` and include a single step:
`"Reasoning steps unavailable for this response."`

**Reasoning steps must be in plain language.**
Before adding a reasoning step to the trace, check that it contains no model-internal
language (e.g. "token probability", "temperature", "embedding"). If raw thinking output
contains such terms, rephrase or summarise at the server before emitting. The frontend
receives only human-readable steps.

**Generation time is wall-clock, server-side.**
Record `time.time()` at the start of the `/api/chat` handler. Emit `generation_time_ms`
in the `done` event calculated as `(time.time() - start) * 1000`. Never infer from token
counts or estimate.

**`is_complete` flag.**
Set to `True` only if all three sections populated: `input_context` is non-empty,
`sources_and_tools` has at least one entry, and `reasoning_steps` has at least one entry.
If any section is empty, set `is_complete: False`. The frontend handles partial traces
without crashing — it shows what's available.

**Source ordering reflects real access order.**
`sequence` on each `SourceAccess` must reflect the order sources were actually consulted
during context assembly — not alphabetical, not by type. This is what makes the trace
honest rather than reconstructed.

---

## External Dependencies

| Dependency | Purpose |
|---|---|
| Google Generative AI Python SDK (`google-genai`) | LLM call + thinking mode for reasoning steps |
| `backend/src/mock_data.py` | Source of all market data injected as context (v1) |

No database, no queues, no additional storage beyond what already exists.

---

## Tech Decisions

- **Reasoning trace as the first stream event**, not a separate endpoint. This keeps the
  frontend's data model simple (one stream = one complete response + its trace) and avoids
  the need for response IDs, session storage, or a second HTTP request.

- **Vercel AI SDK `data` event type** for the trace. Using `event: data` with a typed
  payload (`"type":"reasoning_trace"`) means the frontend can distinguish it from token
  events using the same stream listener. No new event type needed.

- **Trace assembly is synchronous and pre-LLM** for everything except reasoning steps.
  Input context and sources are known before the LLM call. Only reasoning steps come from
  the model's thinking output. When using `thinking_config`, Gemini returns a `thought` part
  followed by a `text` part in the response — the `thought` part is parsed for reasoning
  steps before the `text` part is streamed as tokens.

**Provider abstraction layer**
The reasoning trace feature calls the LLM through the same `LLMProvider` protocol as all
other AI features (`backend/src/llm/base.py`). The provider and model are named explicitly
at the call site. A single feature may call more than one provider — for example, one model
could generate the answer while a second evaluates it — and each call names its provider
independently:

```python
answer = await providers.gemini("gemini-2.5-flash").stream(messages, system)
eval   = await providers.anthropic("claude-haiku-4-5").complete(eval_prompt)
```

Each provider adapter in `backend/src/llm/{provider}.py` is responsible for its own
message format, streaming contract, and error mapping. The reasoning trace handler imports
no provider SDK directly. See `backend/specs/market-health/api.md` for the protocol definition.

- **No trace caching in v1.** Each request generates a fresh trace. If the user refreshes,
  the trace is regenerated. This is acceptable for v1; persistence can be added when a
  database is introduced.
