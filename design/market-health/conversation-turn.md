---
id: conversation-turn
feature: market-health
directive: low
status: active
created: 2026-06-15
---

# Conversation Turn — Component Spec

## What this spec is

Documents the two turn components that form the visual pattern for the conversation thread:
`UserTurn` and `AITurn`. Every message in the thread — the implicit opening briefing and
every user follow-up — is rendered using one of these two components.

This spec lives under `design/market-health/` because both components were first built for
Market Health. If the turn pattern appears in other features, extract to `design/components/`.

Reference: `design/market-health/experience.md` — the Visual Design section defines the
overall three-zone layout these components live inside.

---

## UserTurn

Represents a user-authored message.

**Visual pattern**

- Right-aligned in the thread
- Dark rounded bubble (`bg-gray-800 text-gray-100`)
- Small circular avatar to the right of the bubble, containing the user initial ("Y" as placeholder)
- Label above the bubble: "You" — small, muted

**Truncation**

If the prompt text is longer than 120 characters, show only the first 120 characters followed
by an ellipsis. A chevron-down icon button below the truncated text lets the user expand to read
the full prompt. The same button (now chevron-up) collapses it. Expand state is local to
the component.

| State | What renders |
|---|---|
| Short prompt (≤ 120 chars) | Full text, no expand control |
| Long prompt, collapsed | `prompt.slice(0, 120).trimEnd() + "…"` + chevron-down button |
| Long prompt, expanded | Full text + chevron-up button |

**Props**

| Prop | Type | Description |
|---|---|---|
| `prompt` | `string` | The full text of the user's message |

---

## AITurn

Represents an AI-generated message. Used for both the implicit opening briefing and all
follow-up chat responses.

**Visual pattern**

- Left-aligned in the thread
- Dark circular avatar on the left containing a small SVG icon (info/circuit style)
- Header row to the right of the avatar: "Assistant" label (muted) + generation time
- If provenance data is provided, render `ProvenancePanel` between the header and content
- Content renders as children below the provenance panel

**Timing format**

```
< 1000ms → "{n}ms"    e.g. "742ms"
≥ 1000ms → "{n.n}s"   e.g. "1.4s"
```

Timing is omitted when `timeMs` is undefined (e.g. while the response is still loading).

**Loading state**

When `children` is a loading indicator (AI is still streaming), render three bouncing dots:
`bg-gray-300`, staggered `animationDelay` at 0ms / 150ms / 300ms. Wrap with
`role="status"` and `aria-label="Loading response"` for accessibility.

**Props**

| Prop | Type | Description |
|---|---|---|
| `children` | `ReactNode` | The AI-generated content, or a loading indicator |
| `provenance` | `ProvenanceData \| undefined` | If provided, renders the ProvenancePanel |
| `timeMs` | `number \| undefined` | Generation time in milliseconds |

| State | What renders |
|---|---|
| Loading | Avatar + "Assistant" header + animated dots |
| Loaded, with provenance | Avatar + "Assistant" + timing + ProvenancePanel (collapsed) + content |
| Loaded, no provenance | Avatar + "Assistant" + timing + content |

---

## Composition

`ConversationThread` composes these two components. The opening briefing always renders
as one implicit `UserTurn` (using the `OPENING_PROMPT` constant from `MarketBriefingMessage`)
followed by one `AITurn` wrapping `MarketBriefingMessage`. Every follow-up exchange adds
a `UserTurn` (user message content) then an `AITurn` (streamed text or received text).

---

## What this rules out

- Inline editing of either turn (thread is read-only)
- Showing provenance on `UserTurn` (provenance is AI-only)
- Showing timing on `UserTurn`
- A shared wrapper container around both turns in a pair (they are independent siblings)
