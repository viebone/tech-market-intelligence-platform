---
id: ai-reasoning-transparency
source: user_research
priority: high
status: active
created: 2026-06-25
---

# Outcome: Users can inspect and verify how the AI reached any answer

## Signal
Users want to see how the AI got to its answer — what inputs it used, what data sources
and tools it accessed, and why. Without this, users either blindly trust the output or
spend time re-researching it themselves, slowing down decisions and eroding confidence
in the platform over time.

See: `research/2026-06-25-ai-reasoning-transparency.md`

## Context
The platform makes consequential recommendations — whether to search now, what salary to
target, which skills are in demand. Users need to be able to evaluate whether they trust
a specific answer before acting on it.

This outcome is the concrete expression of Principle 4 in `design/foundations.md`:
*"Progressive Transparency with Full Inspectability — users can always see what the system
is doing, why it is doing it, and what data and rules were involved."*

Transparency is not a feature to add later. It is a default behaviour that must be present
in every AI response from the first release. AI products that show reasoning report higher
user trust and longer retention. Products that hide it accumulate suspicion over time.

The design direction is full inspectability without overwhelm — progressive disclosure,
not raw dumps. The reference pattern is Claude AI and ChatGPT thinking panels: collapsed
by default, expandable on demand, unobtrusive when not needed.

## Success looks like
- Every AI response includes an accessible reasoning trail — users never have to wonder
  how an answer was reached
- Users can expand and collapse reasoning detail without losing their place in the main content
- Users can see which data sources and external tools the AI consulted for any given response
- Users can see the reasoning steps that led to a conclusion, in plain language
- A user who doubts an answer can verify or dismiss it without leaving the platform
- Inspecting reasoning at least once measurably increases a user's confidence in subsequent answers
- Drill-down rate, satisfaction with explanations, and time-to-trust improve over the first
  four weeks of use (see Transparency Without Overload metric in `design/foundations.md`)

## Out of scope
- Modifying or correcting AI reasoning after the fact
- Exposing raw model internals, token probabilities, or prompt engineering details
- Developer-level debugging tools
- Showing reasoning for non-AI content (static charts, raw data tables)
- Per-session configuration of transparency level — it is always available, never hidden
