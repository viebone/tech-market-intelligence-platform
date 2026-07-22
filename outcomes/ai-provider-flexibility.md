---
id: ai-provider-flexibility
source: business
priority: medium
status: active
created: 2026-07-01
---

# Outcome: The platform can use multiple AI providers simultaneously, with each feature's provider choice explicit in code

## Signal
See: `research/2026-07-01-multi-ai-provider.md`

The decision to use Gemini today shouldn't lock the platform in permanently. Different providers
may be better suited for different tasks, and even a single feature may benefit from using more
than one provider at once. Engineering needs to be able to declare which AI handles what —
and change that declaration — without touching business logic.

## Context
Every AI provider has a different SDK, auth model, message format, and streaming contract.
If provider calls are scattered through business logic, adding a second provider or reassigning
a feature to a different model means hunting across multiple files and risking regressions.

A provider abstraction layer turns model selection into an explicit, visible configuration at
the point of use — not a buried SDK call. This is especially important as the platform adds
more AI-powered features that may each have different latency, cost, and capability requirements.
When a reader looks at any feature's code, they should immediately see which AI is doing what.

## Success looks like
- Every AI call in the codebase names the provider and model at the call site — no reader has to search to find out which AI a feature uses
- A feature can call more than one AI provider in a single request (e.g. one model generates the answer, another evaluates it)
- Adding a new provider requires creating one adapter, not modifying existing feature code
- Swapping the provider for a specific feature is a one-line change at the call site
- The frontend contract (stream format, response shape) is unchanged regardless of which provider is active
- Two features can use different providers simultaneously without either being aware of the other's choice

## Out of scope
- Exposing provider selection to end users (this is an internal engineering concern)
- Automatic provider selection based on cost, latency, or load (routing is always explicit, never magic)
- Provider fallback / retry logic across providers (if a provider fails, it fails — no silent rerouting)
- Cost comparison tooling
