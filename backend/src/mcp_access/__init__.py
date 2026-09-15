"""
Bring-your-own-AI access — MCP server + OAuth 2.1 authorization + account/
connections management. See backend/specs/mcp-access/api.md.

Package named `mcp_access`, not `mcp` (the spec's Tech Decisions section
names `backend/src/mcp/`) — deliberate deviation: `mcp` is also the name of
the official Model Context Protocol Python SDK this package depends on
(`pip install mcp`). Naming this package `mcp` would shadow that import
inside every module in `backend/src/` (which runs with `backend/src` itself
on `sys.path`, per how `main.py` is started) — `import mcp` from anywhere in
this codebase would resolve to this local package, not the installed
library. Noted here, and in the backend spec's implementation, rather than
silently renamed with no trace.
"""
