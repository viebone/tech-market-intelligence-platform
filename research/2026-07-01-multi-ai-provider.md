source: internal
date: 2026-07-01

The system should not be locked to a single AI provider. Today it uses Gemini, but tomorrow
it could switch to another provider, or use multiple providers for different purposes (e.g.
one for chat, another for reasoning, another for a different feature). The architecture
should make swapping or adding providers possible without rewriting business logic each time.

Related: research/2026-07-01-gemini-integration.md
