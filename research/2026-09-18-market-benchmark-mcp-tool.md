source: internal
date: 2026-09-18

> "do we have an skill which make sure that when we build a pipe line to access new data it
> will be also accessible from external agents"

## Context
Answered directly: yes — Rule 12 (framework `CLAUDE.md`) + the `/mcp-access-review` skill,
which fires automatically inside `/new-backend-spec` and is called out explicitly in
`/change-request`'s own execution-plan generator. It doesn't force every capability to be
exposed — it forces an explicit, recorded decision (exposed / not exposed / deferred) every
time, in `ACCESS.md`.

Self-auditing against that answer surfaced a real gap: `changes/2026-09-18-market-benchmark-story.md`
had asserted "still deferred" for MCP exposure of `market_observations`/`skill_associations`
from memory, without actually re-running the skill now that a real consumer surface existed
(the prior "deferred" reasoning — "nothing concrete to expose yet" — was no longer true).
Re-ran it for real; see `changes/2026-09-18-market-benchmark-mcp-tool.md` for the resulting
decision (a real tension, put to the user, resolved as "expose now, Free-plan only").
