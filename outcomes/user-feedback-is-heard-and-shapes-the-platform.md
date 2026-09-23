---
id: user-feedback-is-heard-and-shapes-the-platform
source: stakeholder-request
priority: medium
status: active
created: 2026-09-23
---

# Outcome: As a user, I feel listened to — my feedback helps make this platform more useful

## Signal
See: `research/2026-09-23-user-feedback-mechanism.md`

"I want to build a mechanism that allows users to provide feedback, at product level and
feature level." Followed up, when asked how to frame the goal: "as a user I feel listened to
and my feedback helps making this platform more useful."

## Context
Today the platform has no way for a user to tell the team how satisfied they are, or to react
to any specific thing it shows them. The team has no signal on overall satisfaction and no
per-feature read on what's landing and what isn't, beyond usage data. Closing that loop —
letting a user say something and trusting it's actually captured — is what "feels listened to"
means here.

This is a distinct audience and need from `pipeline-processing-visibility`: that outcome is the
operator watching what the pipeline did; this one is the end user's voice about the product
itself, surfaced to whoever's watching admin.

Two feedback mechanisms, at two different altitudes:
- **Product-level** — a persistent, always-available way to say how satisfied the user is with
  the platform overall (not tied to any one moment or feature).
- **Feature-level** — a lightweight, in-the-moment reaction to a specific Data Story, so the
  team knows which individual things are working and which aren't.

Feedback is anonymous — no login required, matching how the rest of the consumer app works
today (`CLAUDE.md`: "the consumer-facing `/api/*` routes have no auth yet"). The separate
MCP/Connect-Your-AI account system is out of scope for this outcome; feedback is not tied to it.

## Success looks like
- A user can rate overall platform satisfaction (1–5, mandatory) with optional written comment,
  at any time, without it interrupting whatever they were doing
- A user can react to a specific Data Story with a thumbs up or thumbs down; thumbs down also
  invites an optional written comment
- Giving feedback takes seconds, never requires an account, and never blocks or gates any part
  of the product
- The team can see, without querying the database: the platform's average satisfaction rating,
  and an average/aggregate reaction per ratable Data Story
- The team can read every individual response — its rating or reaction, its written comment if
  any, and when it was given
- A user who gives feedback has some visible acknowledgment that it was received (even
  something as simple as a thank-you) — this is what makes "listened to" real, not just captured

## Out of scope
- Responding to individual feedback / closing the loop back to the specific user (anonymous —
  there's no one to respond to; a future account-based version could change this)
- Any AI-generated analysis, summarization, or sentiment scoring of feedback text
- Gating features or nagging users into giving feedback (frequency capping / re-prompting logic
  is an experience-spec decision, but the default is: never forced, always dismissible)
- Feedback tied to the MCP/Connect-Your-AI account system
