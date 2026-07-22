---
id: ai-reasoning-panel
outcome: ai-reasoning-transparency
directive: high
status: ready
created: 2026-06-25
---

# AI Reasoning Panel — Experience Spec

## Outcome this serves
See: `outcomes/ai-reasoning-transparency.md`

This is a **universal component**, not a standalone feature. It appears on every AI
turn in the Working Space, across every Task, without exception. It is the product's
primary trust mechanism and the direct expression of Principle 4 (Progressive Transparency
with Full Inspectability) from `design/foundations.md`.

---

## Information Architecture

**Location:** Working Space > AI Turn (embedded — not a separate zone or page)

This component has no dedicated navigation item. It lives within the AI turn structure
and is accessible from every AI response the system produces.

| Zone | Priority | Contains |
|---|---|---|
| Working Space | Primary | All AI turns, each containing the Reasoning Panel toggle in its header area |
| Reasoning Panel (when open) | Primary | Input received, data sources and tools accessed, reasoning steps taken |
| Answer content | Secondary | The AI's answer — always visible below the panel, never inside it |

The Reasoning Panel sits **between the AI turn header and the answer content**. It does
not replace the answer. It does not wrap the answer. The answer is always readable
whether the panel is open or closed.

---

## Opening Prompt

Not applicable. The Reasoning Panel is not a Task and does not fire a prompt on load.
It is triggered by user action — clicking "View thinking" — on any individual AI turn.
Each AI turn carries its own independent Reasoning Panel with the reasoning for that
specific response.

---

## User Flow

The flow below describes a user encountering an AI response they want to verify.
This flow repeats for every AI turn in every conversation.

1. The user receives an AI response in the Working Space. The answer is immediately
   visible. Below the AI name and subtitle, they see a quiet toggle: "⌄ View thinking · 2.3s"

2. The user reads the answer. Something prompts doubt — a number they didn't expect,
   a claim they can't verify, or simply curiosity about what the AI looked at.

3. The user clicks "View thinking." The Reasoning Panel expands inline, between the
   toggle and the answer. The answer shifts down. Nothing is hidden.

4. The user sees the full trail, structured into clear sections:
   - **Input** — what the AI received: the user's question, prior conversation context,
     any constraints or parameters in scope
   - **Sources & Tools** — what the AI accessed: named data sources, external tools used,
     and a brief note on why each was consulted
   - **Reasoning** — the steps the AI took: how it interpreted the input, what it evaluated,
     how it weighted sources, what it concluded at each step, and how it arrived at the answer

5. The user reads at the depth they need. They may scan the sources and stop. They may
   read every reasoning step. Both are valid — the panel supports both without forcing either.

6. The user is satisfied (or not). If satisfied: they click "↑ Hide thinking" and continue
   reading the answer, or ask a follow-up. If not satisfied: they ask a targeted follow-up
   question that challenges a specific step or source they've just seen.

7. The panel can be left open while reading the answer below. Open and closed states
   persist independently per AI turn for the duration of the session.

---

## Visual Design

Every visual decision here references `design/visual-design.md` exactly.

**AI turn structure (with Reasoning Panel):**

```
[Avatar]  AI Name                               ← gray-100, text-sm font-medium
          Subtitle (task name or context)       ← gray-400, text-xs
          ⌄ View thinking  ·  2.3s             ← tertiary link + muted time
          ─────────────────────────────────────
          Answer content...                     ← gray-300, text-sm, leading-relaxed
```

**Toggle line:**
- Arrow + label: `text-xs gray-500 hover:gray-300` — tertiary link, intentionally quiet
- Arrow: `↓` when collapsed · `↑` when expanded (swaps immediately on click, no transition)
- Label: "View thinking" collapsed · "Hide thinking" expanded
- Separator: ` · ` in `gray-600`
- Generation time: `text-xs gray-600` — muted, secondary to the label

**Reasoning Panel (expanded):**
```
background:    gray-800 (same as AI turn surface — seamless)
border-top:    1px solid gray-700  ← separates panel from toggle
border-bottom: 1px solid gray-700  ← separates panel from answer
padding:       16px 0 (py-4) — inherits AI turn horizontal padding
margin:        8px 0 (my-2) above and below the bordered area
```

**Panel internal structure:**

Three sections, always in this order, always present:

| Section | Label style | Content style |
|---|---|---|
| Input | `text-xs font-medium gray-400 uppercase tracking-wide` | `text-sm gray-300 leading-relaxed` |
| Sources & Tools | Same | Named sources as a list; tool names with a one-line note on why each was used |
| Reasoning | Same | Numbered steps, each a single clear sentence or short paragraph |

If a section has no content (e.g. no external tools used), it is shown with a
muted placeholder: `text-xs gray-600 italic` — "No external tools used." Never hide
a section silently. Absence is information.

**Tone:**
The panel reads like a transparent colleague explaining their work — clear, direct,
non-technical in language. No jargon. No hedging. Reasoning steps are written in plain
language the user can evaluate without domain expertise in AI.

---

## Chart Specification

Not applicable. The Reasoning Panel contains no charts. Data visualisations belong
in the answer content below the panel, not inside it.

---

## Interactions

| User action | System response |
|---|---|
| Clicks "⌄ View thinking" | Panel expands inline between toggle and answer. Arrow becomes ↑. Label becomes "Hide thinking". Answer shifts down. Transition: `transition-all duration-200 ease-in-out` on panel height. |
| Clicks "↑ Hide thinking" | Panel collapses. Arrow becomes ↓. Label returns to "View thinking". Answer shifts back up. Same transition. |
| Clicks "View thinking" on a second AI turn while another is open | Both panels are open simultaneously. Each AI turn manages its own state independently. |
| Scrolls past the toggle while panel is closed | Toggle remains in place as part of the AI turn — it does not float or stick. User must scroll back to open it. |
| Scrolls while panel is open | Normal scroll. The open panel is part of the document flow. No sticky behaviour. |
| Asks a follow-up after reading the panel | The follow-up is added to the conversation thread as normal. The panel on the previous turn stays in whatever state the user left it. |

---

## Edge Cases

**Reasoning still generating (streaming response):**
If the AI response is still being generated, the toggle is not shown until generation
is complete. During streaming, a bouncing-dots indicator (per `visual-design.md`) appears
in place of the toggle. Once complete, the toggle fades in with `transition-opacity duration-150`.

**Very long reasoning (many steps or sources):**
The panel renders in full — no truncation by default. If the reasoning exceeds
approximately 600px in rendered height, a "Show less" link (`text-xs gray-500`)
appears at the bottom of the panel, collapsing it to the first 300px with a
fade gradient at the bottom. "Show less" is not the same as "Hide thinking" — it
trims the panel content, not the panel itself.

**Generation time unavailable:**
The ` · 2.3s` segment is omitted entirely. The toggle still shows. Never show "· —" or
a placeholder for the time.

**No external tools or sources used:**
The Sources & Tools section renders with a muted placeholder:
`text-xs gray-600 italic` — "No external tools or data sources were used for this response."
The section is never hidden.

**AI response produced an error:**
The toggle still appears. The panel shows whatever reasoning trace is available.
If the trace is empty, it shows: "Reasoning trace unavailable for this response."
in `text-xs gray-600 italic`.

**User is on a slow connection and panel content is loading:**
Section labels render immediately. Content within each section shows a skeleton pulse
(`animate-pulse gray-700`) until loaded. Never show a blank panel.

---

## Evaluation Metrics

| Metric | How measured | Target |
|---|---|---|
| Reasoning Panel open rate | Analytics: % of sessions with at least one panel expanded | > 40% within first 4 weeks |
| Reasoning Panel engagement depth | Analytics: % of users who scroll past the Sources section into Reasoning steps | > 25% of panel opens |
| Trust calibration lift | Post-session survey: "How confident are you in the AI's answer?" — compare users who opened panel vs. those who did not | Panel openers score ≥ 0.5pt higher (5-point scale) |
| Follow-up rate after panel open | Analytics: % of panel opens followed by a targeted follow-up question | Tracked for trend — no initial target |
| Time to verify | Usability test: time from "I'm not sure about this answer" to confident decision | < 60 seconds |
| Abandonment after panel open | Analytics: % of users who open the panel and then leave the product | Should decrease over time as users learn to use it |

---

## Open Questions

- Should the Sources & Tools section link out to external sources, or name them only?
  (Linking may distract; naming builds vocabulary without pulling users away.)
- Should reasoning panels from previous sessions be persisted, or reset on each load?
  (Session-only is simpler; persistence supports resumption — Principle 8.)
- If the user copies or shares an AI response, should the reasoning trail travel with it?
  (Supports Principle 8 — Collaborative Reasoning — but adds complexity to sharing.)
