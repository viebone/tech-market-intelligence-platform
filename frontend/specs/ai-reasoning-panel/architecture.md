---
id: ai-reasoning-panel
experience: ai-reasoning-panel
directive: high
status: draft
created: 2026-06-26
---

# AI Reasoning Panel — Frontend Architecture Spec

## Experience this implements
See: `design/ai-reasoning-panel/experience.md`

Also reads: `frontend/specs/market-health/architecture.md` — `ReasoningPanel` integrates
into the existing `AIMessage` component. This spec extends that architecture; it does
not replace it.

Also reads: `backend/specs/ai-reasoning-panel/api.md` — the reasoning trace arrives as
the first `data` event in the `/api/chat` stream before any tokens.

---

## Component Breakdown

| Component | Responsibility | Location |
|---|---|---|
| `ReasoningPanel` | Self-contained panel component. Manages its own open/closed state. Renders the toggle line (arrow + label + time) and, when open, the three-section panel content (Input, Sources & Tools, Reasoning). | `frontend/src/components/ReasoningPanel.tsx` |
| `AIMessage` *(extended)* | Existing component. Receives two new props: `trace` and `generationTimeMs`. Renders `<ReasoningPanel>` between the message header and the answer content. No other changes. | `frontend/src/features/market-health/AIMessage.tsx` |
| `MarketHealthPage` *(extended)* | Existing component. Gains trace state management: captures `reasoning_trace` and `generation_time_ms` from the stream data events, stores them per message ID, and passes them down to each `AIMessage`. | `frontend/src/pages/MarketHealthPage.tsx` |

`ReasoningPanel` is the only new file. `AIMessage` and `MarketHealthPage` are surgical extensions.

---

## ReasoningPanel — detailed spec

### Props

```ts
interface ReasoningPanelProps {
  trace: ReasoningTrace | null        // null while still streaming or if capture failed
  generationTimeMs: number | null     // null until the done event arrives
  isStreaming?: boolean               // true while the parent message is still generating
}

interface ReasoningTrace {
  input_context: string
  sources_and_tools: SourceAccess[]
  reasoning_steps: ReasoningStep[]
  is_complete: boolean
}

interface SourceAccess {
  sequence: number
  source_type: 'data_source' | 'tool'
  name: string
  purpose: string
}

interface ReasoningStep {
  sequence: number
  content: string
}
```

### Internal state

`isOpen: boolean` — local, starts `false`. No prop controls it. Each instance is independent.

### Render structure

```
<div>                                         ← wrapper, mt-1 below subtitle/name
  <button onClick={toggle}>                   ← toggle line, full-width left-aligned
    {isOpen ? '↑' : '↓'}  {label}  ·  {time}
  </button>

  {isOpen && (
    <div className="panel">                   ← animated height, border-y gray-700, py-4
      <section>Input</section>
      <section>Sources & Tools</section>
      <section>Reasoning</section>
    </div>
  )}
</div>
```

### Toggle line — exact classes

```
button:  flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300
         cursor-pointer bg-transparent border-none p-0 mt-1
arrow:   inline — '↓' collapsed · '↑' expanded (character swap, no transition)
label:   'View thinking' collapsed · 'Hide thinking' expanded
sep:     <span className="text-gray-600"> · </span>
time:    {generationTimeMs ? `${(generationTimeMs / 1000).toFixed(1)}s` : null}
         — omit entirely if generationTimeMs is null; never render '—' or '0.0s'
```

### Panel sections — exact classes

Panel wrapper:
```
bg-gray-800 border-y border-gray-700 py-4 px-4 my-2 space-y-4
transition-all duration-200 ease-in-out
```

Section label:
```
text-xs font-medium text-gray-400 uppercase tracking-wide mb-2
```

Section content:
```
text-sm text-gray-300 leading-relaxed
```

**Input section** — renders `trace.input_context` as a paragraph.

**Sources & Tools section** — renders `trace.sources_and_tools` ordered by `sequence`:
```
<ol className="space-y-2">
  {sources.map(s => (
    <li key={s.sequence}>
      <span className="text-gray-300">{s.name}</span>
      <span className="text-gray-500 ml-1">— {s.purpose}</span>
    </li>
  ))}
</ol>
```
If `sources_and_tools` is empty: render placeholder `text-xs italic text-gray-600` —
"No external data sources or tools were used for this response."

**Reasoning section** — renders `trace.reasoning_steps` ordered by `sequence`:
```
<ol className="space-y-2 list-decimal list-inside">
  {steps.map(s => (
    <li key={s.sequence} className="text-sm text-gray-300 leading-relaxed">
      {s.content}
    </li>
  ))}
</ol>
```
If `reasoning_steps` is empty: render placeholder —
"Reasoning steps unavailable for this response."

**Incomplete trace warning** — if `trace.is_complete === false`, render below all
sections: `text-xs italic text-gray-500` — "Reasoning trace is incomplete."

**Loading state** (when `isStreaming` is true and panel is open):
Show section labels with skeleton pulse content instead of real data:
```
<div className="animate-pulse bg-gray-700 rounded h-3 w-3/4 mb-1" />
<div className="animate-pulse bg-gray-700 rounded h-3 w-1/2" />
```

**Null trace + not streaming** (trace capture failed entirely):
Panel opens but shows only: `text-xs italic text-gray-600` —
"Reasoning trace unavailable for this response."

---

## State Management

All trace state lives in `MarketHealthPage`. No Zustand store.

### Trace storage

```ts
// In MarketHealthPage:
const [traces, setTraces] = useState<
  Map<string, { trace: ReasoningTrace | null; generationTimeMs: number | null }>
>(new Map())

const [openingTrace, setOpeningTrace] = useState<{
  trace: ReasoningTrace | null
  generationTimeMs: number | null
} | null>(null)

// Refs — captured from stream events, consumed on message completion
const pendingTrace = useRef<ReasoningTrace | null>(null)
const pendingGenerationTime = useRef<number | null>(null)
```

### Capturing trace from the stream

The `/api/chat` stream emits two relevant data event types (from the backend spec):
- `{ type: 'reasoning_trace', trace: ReasoningTrace }` — first event, before tokens
- `{ type: 'finish_message', generation_time_ms: number }` — last event

Use Vercel AI SDK's `data` array from `useChat` and process new entries on each render.
When a `reasoning_trace` event arrives → store in `pendingTrace.current`.
When a `finish_message` event arrives → store `generation_time_ms` in `pendingGenerationTime.current`.
When `useChat`'s `onFinish(message)` fires → write pending values into `traces`:

```ts
onFinish: (message) => {
  setTraces(prev => new Map(prev).set(message.id, {
    trace: pendingTrace.current,
    generationTimeMs: pendingGenerationTime.current,
  }))
  pendingTrace.current = null
  pendingGenerationTime.current = null
}
```

The opening message (pre-rendered, not from `useChat`) captures its trace the same way —
directly from the opening stream fetch, stored in `openingTrace`.

### Passing trace to AIMessage

```tsx
// Opening message
<AIMessage
  trace={openingTrace?.trace ?? null}
  generationTimeMs={openingTrace?.generationTimeMs ?? null}
  isStreaming={openingIsStreaming}
  ...
/>

// Follow-up messages
{messages.map(msg => msg.role === 'assistant' && (
  <AIMessage
    key={msg.id}
    trace={traces.get(msg.id)?.trace ?? null}
    generationTimeMs={traces.get(msg.id)?.generationTimeMs ?? null}
    isStreaming={isLoading && msg.id === messages[messages.length - 1]?.id}
    ...
  />
))}
```

---

## Data Requirements

| Data | Source | When fetched |
|---|---|---|
| Reasoning trace | `POST /api/chat` stream — `reasoning_trace` data event | Arrives as first event in every `/api/chat` stream response |
| Generation time | `POST /api/chat` stream — `finish_message` data event | Arrives as last event in every `/api/chat` stream response |

No new endpoints. No new fetches. All data arrives through the existing `/api/chat` stream.

---

## API Contract

| Method | Endpoint | New data consumed |
|---|---|---|
| POST | `/api/chat` | `data` events of type `reasoning_trace` and `finish_message` — see `backend/specs/ai-reasoning-panel/api.md` for exact shape |

---

## Tech Decisions

- **`ReasoningPanel` owns its open/closed state.** It is not controlled by the parent.
  Each panel instance is independent — opening one does not close others.

- **No animation library.** Use Tailwind's `transition-all duration-200 ease-in-out`
  on the panel container. Mount/unmount with a conditional render (`isOpen && ...`).
  For a smooth height transition, apply `overflow-hidden` and animate `max-height`
  from `0` to a large value (e.g. `max-h-0` → `max-h-[2000px]`) rather than
  animating height directly, which requires JavaScript measurement.

- **Arrow is a character swap, not an animation.** `↓` and `↑` render instantly on
  click. No transition on the arrow or label.

- **Generation time display.** Convert `generationTimeMs` to seconds with one decimal
  place: `(ms / 1000).toFixed(1) + 's'`. Display only when the value is available —
  omit the separator and time entirely if null.

- **`ReasoningPanel` is in `src/components/`**, not `src/features/market-health/`, because
  it will be used by every AI message across all Tasks — not just market health.

- **Refs for pending trace and time**, not state. Storing in refs avoids a re-render on
  every stream event. The single `setTraces` call in `onFinish` is the only state update.

---

## Out of scope

- Persisting reasoning panel open/closed state across page reloads
- Persisting reasoning traces across sessions (no database in v1)
- Sharing or copying a reasoning trace
- Deep-linking to a specific reasoning panel
- Per-section collapse within the panel (the "Show less" behaviour for very long panels
  described in the experience spec — deferred to v2)
