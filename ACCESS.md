# What's Accessible From Where

For every capability this product offers: can you reach it from the product's own UI, from its
backend API directly, and/or from an external AI client over MCP? Kept current as a mandatory
step whenever a capability is added or changed — see the `mcp-access-review` skill (framework
level, `.claude/skills/mcp-access-review/`).

Every ❌ in the MCP column carries a real reason, not a blank — a capability that simply hasn't
been decided on yet is exactly the gap this file exists to make visible.

## Market data capabilities

| Capability | Frontend (UI) | Backend API | MCP Tool | Notes |
|---|---|---|---|---|
| Job demand / openings trend (by role, specialization, level, track, country, month) | ✅ "Tech market hiring status" chart + chat | ✅ `GET /api/market-health/openings`; `query_market_data` (chat tool) | ✅ `get_job_demand` | |
| Salary / compensation stats | ✅ via chat only, no dedicated chart | ✅ `query_compensation_data` (chat tool only) | ✅ `get_salary_stats` — **Premium plan only** | |
| Skills / education / language / work-arrangement demand | ✅ via chat only | ✅ `query_requirements_data` (chat tool only) | ✅ `get_skill_demand` | |
| Employment risk (layoffs, closures, restructuring, expansion) — "Layoff Signal" | ✅ "Employment risk across the market" story + chat | ✅ `POST /api/market-health/stories/employment-risk-overview`; `query_employment_events_data` (chat tool) | ✅ `get_employment_risk` | |
| Tracked companies + industry | ❌ not its own view (used internally for industry tagging) | ❌ no dedicated endpoint (internal lookup only) | ✅ `list_tracked_companies` | MCP-only today — a real gap in the other two surfaces, not a decision; low priority since it's metadata, not market data |
| Market benchmark datasets (third-party — demand rank, salary percentiles, geography, weighted role↔skill associations; IT Jobs Watch first) | ❌ none | ❌ none — ingested and stored (`market_observations`, `skill_associations`), not queryable by anything yet, not even internally | ❌ Deferred | **Deferred, not decided against** — `backend/specs/scraped-data-sources/api.md` (2026-09-16, revised same day) ships ingestion only; no query/comparison surface exists anywhere in this product yet, so there's nothing concrete to expose or withhold. Revisit once a real decision is made on whether/how this data is ever surfaced (a comparison, a story, a chat tool) — see that spec's "What this doesn't decide." |
| Canonical taxonomy reference (role categories, levels, tracks, skill groups, event types) | ❌ implicit only (used internally for labels/filters) | ❌ documented in `design/market-health/job-classification.md`, not served as an API | ✅ `get_taxonomy` | MCP-only today, deliberately — lets an external AI use this platform's exact vocabulary without guessing; no scope required |
| Data stories (pre-composed narrative reports — "What we know about the market," etc.) | ✅ Task Panel story catalogue | ✅ `GET /api/market-health/stories`, `POST /api/market-health/stories/{id}` | ❌ Not exposed | Deliberate — outcome direction is "data primitives, not pre-written reports" (`outcomes/bring-your-own-ai-agent-access.md`); an external AI composes its own equivalent from the primitive tools above instead |
| Platform welcome / data inventory ("About this platform") | ✅ default landing task | ✅ `GET /api/market-health/welcome` | ❌ Not exposed | Orientation for a human visiting this product's own UI, not market data an external AI's user would ask for |
| Curated instant-answer chips | ✅ `SuggestedQuestions` chips | ✅ `GET /api/market-health/chat-suggestions` | ❌ Not exposed | A convenience for this product's own chat input UI, not a data capability |
| Conversational chat | ✅ every task's chat input | ✅ `POST /api/chat` | ❌ Not applicable | This platform's *own* AI feature — MCP exists specifically so an external AI does this same reasoning on the user's own subscription instead of this one; not a gap, the whole point |
| AI reasoning transparency (how an answer was derived) | ✅ Reasoning Panel toggle on every AI message | ✅ part of `/api/chat`'s SSE stream | N/A as a standalone capability | Its *values* (provenance, freshness) are carried inside every MCP tool's own `meta` envelope instead — the MCP-native equivalent, not a missing feature |

## Operator-only capabilities

| Capability | Frontend (UI) | Backend API | MCP Tool | Notes |
|---|---|---|---|---|
| Pipeline processing visibility (postings, classifications, ingestion runs) | ✅ admin dashboard | ✅ `admin_main.py` routes (JWT-protected) | ❌ Not exposed | Operator-only, no end-user data — `outcomes/pipeline-processing-visibility.md` scopes this to the person running the platform, never end users or an AI acting for them |
| Employment-events admin visibility | ✅ admin dashboard | ✅ `admin_main.py` routes | ❌ Not exposed | Same reasoning as above |
| Data source licensing status (added 2026-09-16) | ✅ admin dashboard (`/admin/licensing`) | ✅ `admin_main.py` routes | ❌ Not exposed | Same reasoning as above — also, licence/attribution data isn't market data an external AI's user would ask for |

## The access-control layer itself (not a data capability — not in scope for this table's MCP column)

Account signup/login, connections management (view/revoke a Connected Assistant), and the OAuth
flow itself are what makes MCP access possible — they aren't capabilities *reachable through*
MCP, and asking "why isn't login an MCP tool" doesn't apply the way it does for the rows above.
One boundary worth stating explicitly: a connected AI **cannot** view or revoke its own (or any)
connection through MCP — that's deliberately human-only, from the Settings tab, so an external AI
can never manage its own access. See `backend/specs/mcp-access/api.md` for the full account/OAuth
surface.
