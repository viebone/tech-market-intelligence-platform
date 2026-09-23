---
id: feedback
outcome: user-feedback-is-heard-and-shapes-the-platform
directive: low
status: ready
created: 2026-09-23
---

# Give Feedback — Experience Spec

## Outcome this serves
See: `outcomes/user-feedback-is-heard-and-shapes-the-platform.md`

## A note on structure

This spec covers the **product-level** feedback mechanism only — the persistent "Give
Feedback" entry and its rating panel. The **feature-level** mechanism (thumbs up/down on each
Data Story) is a generic addition to every story's own rendering contract, not a separate
task or view, so it's specified in `design/market-health/data-stories.md` (new "Feedback
reaction" section) and referenced from `design/market-health/experience.md`'s Interactions and
Edge Cases tables, rather than duplicated here.

## Information Architecture

**Resolved 2026-09-23** via `/new-information-architecture` (`design/information-architecture.md`
v2.7). **Location:** Task Panel > **Footer** — a new,
persistent, non-task zone at the bottom of the Task Panel, below the story catalogue and
pinned feature tasks. Not itself a Task: selecting it does not change what the Working Space
or Output Panel show, unlike every existing Task Panel item.

| Zone | Priority | Contains |
|---|---|---|
| Task Panel Footer | Primary | **Give Feedback** — a single persistent entry, always visible, always in the same place regardless of which Task is active or how long the story catalogue grows |
| Feedback Panel | Primary (on open) | 1–5 satisfaction rating (mandatory) + optional free-text comment + Submit |
| Feedback Panel — confirmation | Primary (post-submit) | Brief thank-you acknowledgment, then auto-close |

## Opening Prompt

Not applicable. Per `design/foundations.md`'s Product Paradigm, the Agentic Conversational UI
model governs *views that show what the AI system is doing* — the Feedback Panel shows nothing
the system produced and generates no AI turn; it's a direct, static input form, the same class
of surface as `design/mcp-access/experience.md` Part 1 (Connections & Permissions), which
resolved the same way for the same reason. There is no opening AI message and no Reasoning
Panel on this surface.

## Why an overlay, not an inline expansion

`design/visual-design.md`'s "What this rules out" warns against forcing a surface into a modal
"when it fits an existing zone" — Connect Your AI avoided a modal because the Output Panel's
Settings tab already existed as a zone for it. Give Feedback has no equivalent existing zone:
the Task Panel is a fixed 240px column, too narrow to hold a 5-point rating control plus a
multi-line text area inline without either truncating other Task Panel items or growing the
column itself (ruled out — "Width never changes," Layout Model). A small centred overlay is
the only way to give the rating and comment fields enough room without disrupting the rest of
the layout — this is the exception the visual-design rule already anticipates ("when it fits
an existing zone"), not a violation of it.

## User Flow

1. The user sees **Give Feedback** at the bottom of the Task Panel, in the same place on every
   screen, regardless of which Task they're on.
2. They click it. The Feedback Panel opens as a small centred overlay above the current
   screen — nothing behind it changes; the active Task, its conversation, and the Output Panel
   are untouched underneath.
3. They see one question — "How satisfied are you with this platform?" — with a 1–5 rating
   control, unselected by default, and a short label under the scale ("Not satisfied" at 1,
   "Very satisfied" at 5).
4. Below it, an optional "Anything you'd like to tell us?" text area, empty by default.
5. They select a rating (required to submit) and, optionally, type a comment.
6. They click Submit. The panel shows a brief thank-you ("Thanks — that helps us improve the
   platform.") for a couple of seconds, then closes on its own.
7. Alternatively, at any point before submitting, they can dismiss the panel (close icon,
   backdrop click, or Escape) with no consequence — nothing is saved, and Give Feedback remains
   available to reopen at any time, including immediately again.

## Visual Design

References `design/visual-design.md` tokens — Surface (`bg-gray-800`, `border-gray-700`,
`rounded-lg`), Page background (`gray-900` backdrop scrim), existing type scale, and the
existing Primary button / Ghost-text action pair. No new accent colour: the rating control uses
the same neutral/emerald treatment as existing Status badges (unselected = gray, selected =
emerald, matching "Complete / success / current" semantics elsewhere in the product) — never a
new hue. The Task Panel Footer entry itself is visually quiet — an icon + short label at Body
scale, gray-400 at rest, brightening to gray-100 on hover, exactly like other Task Panel items,
but visually separated from the task list above it by a divider so it doesn't read as another
Task.

## Interactions

| User action | System response |
|---|---|
| Click "Give Feedback" | Feedback Panel opens as a centred overlay; rating unselected, comment empty. Focus moves to the rating control. |
| Click a rating value (1–5) | That value is selected (visibly highlighted); Submit becomes enabled. Selecting a different value replaces the prior selection — never additive. |
| Type in the comment field | No validation, no character-count pressure shown unless a hard limit is actually enforced (see Edge Cases). |
| Click Submit with no rating selected | Submit stays disabled — this state is unreachable, not an error message after the fact. |
| Click Submit with a rating selected | Feedback is captured immediately. Panel switches to the thank-you confirmation state. |
| Confirmation shown | Auto-closes after ~2–3 seconds, or immediately on any click/Escape — whichever comes first. |
| Dismiss before submitting (close icon, backdrop, Escape) | Panel closes; nothing is captured; no confirmation shown. |
| Reopen "Give Feedback" after a previous submission | Panel opens fresh (unselected rating, empty comment) — a user can submit as many times as they like; this is not a one-time gate. |
| Give Feedback while a Task's conversation is mid-stream (an AI answer is still generating) | Unaffected — the overlay sits above the Working Space without pausing, cancelling, or losing the in-progress answer underneath. |

## Edge Cases

- **Submission fails (network/server error):** The panel shows a plain inline message
  ("Couldn't send that — try again.") and stays open with the rating and comment intact, so the
  user doesn't have to redo their input. Never a silent failure that shows the thank-you state
  without actually capturing anything.
- **Comment field length:** A generous but real upper bound (enforced by the backend spec, not
  guessed here) — if reached, the field stops accepting further input rather than truncating
  silently or erroring on submit.
- **Rapid repeat submissions:** Each submission is its own independent record — there is no
  dedup or "already gave feedback today" gate. Nagging or frequency-capping the *prompt* itself
  is explicitly out of scope for v1 (Give Feedback is always available, never auto-triggered),
  so there's nothing to rate-limit on the capture side either.
- **Very small viewport / narrow window:** The overlay stays centred and never exceeds the
  viewport width; the comment text area may grow taller before it grows narrower.

## Evaluation Metrics

| Metric | How measured | Target |
|---|---|---|
| Feedback submission rate | Analytics — % of sessions with at least one Give Feedback submission | Track, no target yet |
| Time to submit | Analytics — time from panel open to Submit click | < 20 seconds |
| Comment attachment rate | Analytics — % of submissions that include a written comment | Track, no target yet |
| Average satisfaction rating | Computed from submitted ratings, surfaced in admin (see backend spec) | Track over time, no target yet |
| Abandonment rate | Analytics — % of panel opens that close without submitting | Track, no target yet |

## Open Questions
- Should "Give Feedback" ever be proactively suggested (e.g. after a particularly long or
  error-prone session), rather than purely user-initiated? Deliberately left purely
  user-initiated for v1, matching Principle 3 (Exceptions Define the Experience) and the
  outcome's own "never gates or nags" success criterion — revisit only if submission rate
  analytics show the entry point is being missed entirely.
- Should the Task Panel Footer host other future utility entries beyond Give Feedback (e.g.
  "What's new")? Not decided here — today it holds exactly one entry; the zone itself is
  designed to hold more without restructuring, per `/new-information-architecture`'s decision.
