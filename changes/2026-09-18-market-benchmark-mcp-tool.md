---
id: market-benchmark-mcp-tool
date: 2026-09-18
trigger-type: internal
change-type: api-change
outcome: bring-your-own-ai-agent-access
status: complete
---

# Change Request: Expose the market-benchmark data as an MCP tool (`get_market_benchmark`)

## Signal
See: `research/2026-09-18-market-benchmark-mcp-tool.md` — triggered by the user's own process
question ("do we have a skill which make sure that when we build a pipeline to access new data
it will be also accessible from external agents") prompting a real re-run of `/mcp-access-review`
against `changes/2026-09-18-market-benchmark-story.md`, rather than trusting the "still deferred"
note asserted from memory in that change's own impact table.

## Outcome
See: `outcomes/bring-your-own-ai-agent-access.md` — a new tool over an existing outcome, not a
new area.

## Change Type
`api-change` — a new MCP tool + its backing query function. No new data model (reads
`market_observations`/`skill_associations`, already owned by `scraped-data-sources/api.md`).

## Triage Notes (Step 2) — the `/mcp-access-review` re-run

The prior "Deferred, not decided against" call on this data (`ACCESS.md`, 2026-09-16) was
reasoned specifically as "no query/comparison surface exists anywhere in this product yet, so
there's nothing concrete to expose or withhold." `changes/2026-09-18-market-benchmark-story.md`
made that no longer true — a real consumer surface exists. Re-running the skill surfaced a
genuine tension rather than an obvious call, so it was put to the user directly (per the skill's
own "only ask when genuinely ambiguous" rule):

- **For exposing**: `bring-your-own-ai-agent-access.md`'s whole point is giving external AI the
  same helpful primitives a human gets; the web story is now a ready template.
- **Against exposing as-is**: MCP connections have a real Free/Premium tier system (unlike the
  plain web app) — so the NC-licence question the web story sidestepped ("no tiers to gate
  against") comes back for MCP. And an external AI holding both this tool and `get_job_demand`
  could freely do the cross-source comparison this platform's own spec has never built even
  for itself.

User's answer: **"Expose now, Free-plan only"** — the same "free tier sidesteps the NC
question" logic already applied to the web story, extended to MCP by simply not adding this
tool to `PREMIUM_ONLY_TOOLS`.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/bring-your-own-ai-agent-access.md` | no-change — already covers "give external AI curated access to platform data" broadly |
| Design Foundations | `design/foundations.md` | no-change — Principle 9 ("Curated Access, Never Raw") already governs this; no new principle needed |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change — no UI surface, this is a backend/MCP-only capability |
| Experience Spec | `design/mcp-access/experience.md` | no-change — Part 2's existing binding contract (self-describing values, curated not raw) already covers this tool; no new experience-level decision needed |
| Backend Spec | `backend/specs/mcp-access/api.md` | update — new tool section, scope-reuse decision, resolved the "deferred" bullet |
| Frontend Spec | none | no-change |
| Backend Implementation | `backend/src/market_query.py`, `backend/src/mcp_access/tools.py`, `backend/src/mcp_access/server.py` | update |
| Frontend Implementation | `frontend/src/` | no-change |
| Plain-Language Overview | `OVERVIEW.md` | no-change — the existing "Bring your own AI" paragraph already reads generically enough ("the same kinds of questions") to cover this without naming every tool |
| MCP Access Review | `ACCESS.md` + `backend/specs/mcp-access/api.md` | update — the actual point of this change |
| Polite Scraping Review | `DATA_SOURCES.md` + affected backend spec | no-change — doesn't touch scraping mechanics, only adds a read path over already-stored data |

## Execution Plan

- [x] Step 1: Signal captured — `research/2026-09-18-market-benchmark-mcp-tool.md`
- [x] Step 2: Re-ran `/mcp-access-review` for real (not from memory) against the market-benchmark-story change; surfaced the Free/Premium-tier tension; asked the user; got "Expose now, Free-plan only"
- [x] Step 3: Updated `backend/specs/mcp-access/api.md` — new `get_market_benchmark` tool section (scope reuse decision, licence gate, no-Premium-gating rationale, explicit "never compare against job-postings tools" instruction, and the honest named limitation that nothing server-side stops an AI holding both tools from comparing anyway); resolved the old "deferred" bullet in "What's deliberately not a tool," replacing it with the cross-source-comparison caveat
- [x] Step 4: `/implement-backend` — `market_query.py` gains `query_market_benchmark_data()` (licence-gated, filters by `entity_name`, casts `salary_median` to `float` up front this time — learned from the Decimal bug in the web-story change); `mcp_access/tools.py` gains `get_market_benchmark()` (`jobs.read` scope, not in `PREMIUM_ONLY_TOOLS`); `mcp_access/server.py` registers it as a real `@mcp_server.tool()`
- [x] Step 5: Updated `ACCESS.md` — row changed from Deferred to Exposed, with the real reasoning and the named comparison-risk limitation
- [x] Step 6: Extended `backend/tests/test_mcp_access.py` — `get_market_benchmark` covered by `test_tool_scopes_cover_every_scoped_tool` (scope + not-Premium assertions)
- [x] Step 7: Verified against real production data (not fixtures): `tools.get_market_benchmark()` called directly returns real roles/skills/attribution; `entity_name` filtering works; `create_mcp_server()` builds cleanly with the new tool registered; `main.py` imports cleanly; 9/9 `test_mcp_access.py` passing

## Decision Log
- 2026-09-18: Reused the `jobs.read` scope rather than inventing a fourth scope — same
  conceptual grant, avoids touching the OAuth consent screen's scope-chip UI for a small
  addition. Noted as a deliberate call, not an oversight — a dedicated scope is a real option
  later if separate consent granularity ever matters.
- 2026-09-18: Did not add `get_market_benchmark` to `PREMIUM_ONLY_TOOLS` — the user's explicit
  choice, mirroring the same "no consumer tier to gate against" logic already used for the web
  story.
- 2026-09-18: Named a real, unsolved limitation rather than papering over it: the tool's
  docstring instructs against comparing this data to the job-postings tools, but nothing
  server-side actually prevents a calling AI from doing so once it holds both tools' outputs.
  Recorded honestly in `backend/specs/mcp-access/api.md` rather than implied as solved.
