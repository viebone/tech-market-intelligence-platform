---
id: bring-your-own-ai-agent-access
source: business
priority: high
status: proposed
created: 2026-09-13
---

# Outcome: A user can query this platform's market intelligence from whichever AI assistant they already use

## Signal
See: `research/2026-09-13-mcp-ai-agent-access.md`

The trigger is both a business call and a market fact arriving at the same time. The market
fact: Claude (Pro/Max/Team/Enterprise), ChatGPT (via OpenAI's Apps SDK), and Gemini CLI have
all independently converged on the same integration surface — remote MCP (Model Context
Protocol) connectors, OAuth-authenticated, callable from a consumer subscription the user
already pays for. That convergence didn't exist when this platform's chat feature was
designed. The business call: a consumer ChatGPT Plus / Claude Pro / Gemini subscription
cannot be spent as API credit inside this platform — subscription and API billing are
separate products — so every question this platform's own chat answers is a cost the
platform bears (`outcomes/llm-spend-is-bounded-and-isolated`). MCP inverts that: the
reasoning happens inside the user's own AI subscription, and this platform is paid nothing
for it and owes nothing for it.

## Context
Today the only way to get this platform's market intelligence is the platform's own UI and
its own chat feature, which the platform pays to run per-question. That caps how much
reasoning the product can afford to offer, and it locks every user into whichever single
model the platform has chosen — even a user who already pays for and prefers a different
AI assistant gets no benefit from that subscription here.

People don't want to run five different AI assistants for five different products; they
want to bring the one they already trust and already pay for, and point it at whatever data
they need that week. If this platform's intelligence is only reachable through its own
chat box, it competes with Claude/ChatGPT/Gemini on conversational quality — a contest
against labs spending orders of magnitude more on model quality. If instead this platform's
data is *reachable by* those assistants, it stops competing with them and starts being one
of the things they're good for. The durable asset stays what it already is — the
collection → classification → taxonomy → historical trend data — not which model answers
in natural language.

Left unaddressed, this platform's usefulness stays capped by its own LLM budget
(`outcomes/llm-spend-is-bounded-and-isolated`) and by one model's reasoning quality, while
the ecosystem moves toward users bringing their own agent to every data source that offers
one.

## Success looks like
- A user can connect Claude, ChatGPT, Gemini CLI, or any other MCP-compatible AI client to
  this platform and ask it market-intelligence questions — job demand, salary, skills,
  company hiring/layoffs, trends — without opening the platform's own UI
- The external AI client authenticates the user via OAuth against their platform account —
  never via a shared API key, a database credential, or anything the user could leak that
  isn't individually revocable
- A user can revoke an external AI client's access at any time from the platform, the same
  way they'd revoke any other connected app, without rotating a password or a shared secret
- Every capability the external AI client can call is a specific, named, parameterized
  operation over defined fields (role, seniority, geography, date range, metric, etc.) —
  never a raw or free-form query against the underlying database
- The platform's own taxonomy and classification stay authoritative: whatever term or
  category the external AI uses internally, the data it gets back reflects this platform's
  canonical definitions, not the AI's own interpretation
- A free-plan user and a premium-plan user asking the same external AI the same question get
  the access their plan actually entitles them to (data scope, rate/volume limits) — plan
  enforcement holds even though the request never touched the platform's own UI
- The platform's own UI and its own chat feature keep working exactly as they do today —
  this is an additional way in, not a replacement for either
- A user who already pays for Claude, ChatGPT, or Gemini gets real value from this platform
  without the platform spending anything on the reasoning that produced that value
- Someone can point three different AI assistants (their own choice of each) at this
  platform and get answers that agree with each other, because all three are reading the
  same canonical data through the same operations — not three independently-reasoned,
  potentially-conflicting takes

## Out of scope
- Raw SQL, or any unrestricted/free-form query access, for any external AI client — even
  read-only
- Automatic selection of which AI provider or model a user should use — which assistant a
  user brings is entirely their own choice, never suggested or chosen by the platform
  (same principle `ai-provider-flexibility` already sets for the platform's own internal
  routing: explicit, never magic)
- Bring-your-own-API-key (BYOK) inside the platform's own UI — a plausible later, separate
  outcome, not part of this one
- Any write access, mutation, or ability for an external AI client to change platform data —
  this is read/query access only
- Building a more sophisticated in-house conversational AI layer to out-compete
  Claude/ChatGPT/Gemini on reasoning quality — this outcome deliberately bets on the
  data/taxonomy/pipeline being the asset, not the platform's own chat experience
- Guaranteeing behavior for AI clients that don't yet support remote MCP connectors with
  OAuth — this outcome targets clients that do (Claude, ChatGPT, Gemini CLI today), not
  building bespoke integrations per assistant
