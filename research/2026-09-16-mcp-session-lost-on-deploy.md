source: bug
date: 2026-09-16

> "just found out that claude couldn't connect. it was working fine and now suddenly stop
> working. now it cannot connect"

## Root cause, confirmed empirically against production

Not a code bug — a structural gap. MCP sessions (the `mcp` Python SDK's `StreamableHTTP` session
manager) are held **in memory** inside the `api` service's own process, never persisted to
Postgres. Every deploy to `api` restarts that process and silently drops every active session.
A client (Claude) holding a session ID from before the restart gets rejected on its very next
call — confirmed directly against production:

```
$ curl -X POST .../mcp -H "Mcp-Session-Id: <a session id from before the restart>" ...
HTTP/1.1 400 Bad Request
Bad Request: No valid session ID provided
```

A fresh `initialize` call (no session ID yet) works perfectly at any time — confirmed the same
way. So the server itself was never actually broken; the specific session Claude was holding
had simply stopped existing.

**Trigger, this time**: five deploys to `api` in one evening (today's scraping/licensing work),
each one silently invalidating whatever MCP session existed at that moment.

## Immediate fix (given to the operator)

Disconnect and reconnect the connector in Claude — this re-runs OAuth + `initialize` and gets a
new, valid session. Confirmed this is sufficient; no code change was needed to restore the
connection.

## What's flagged for later, not fixed now

Sessions don't survive a restart of `api`. This will keep happening — for anyone with an active
MCP session — every time `api` redeploys, which is often during active development. Fixing it
for real means persisting session state (Postgres, matching this product's existing
"nothing stateful lives only in memory" convention for everything else — `ingestion_runs`,
`mcp_connections`, `scrape_ingestion_runs`, etc.) instead of relying on the SDK's default
in-memory session manager. Not attempted here — flagged as a known limitation in
`backend/specs/mcp-access/api.md`, not solved, per explicit direction to note it and move on for
now.
