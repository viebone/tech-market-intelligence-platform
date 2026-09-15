"""
The MCP protocol server — mounted at /mcp on the existing api service
(main.py), per backend/specs/mcp-access/api.md's Tech Decisions ("not a new
Railway service"). Uses the official `mcp` Python SDK (External Dependencies)
for the JSON-RPC/Streamable-HTTP transport, so this codebase never hand-rolls
protocol framing that will keep evolving upstream.

Verified locally against a real installed SDK (`pip install mcp`), not left
as an untested assumption — two real findings from that verification, both
already fixed here:

  1. Version pin. `mcp`'s newest releases (2.x) pull in a `starlette`
     version that conflicts with this project's `fastapi==0.115.0` pin
     (`starlette<0.39.0`). `mcp==1.9.4` is the oldest line confirmed to
     both (a) satisfy that constraint (all `mcp` 1.x releases only require
     `starlette>=0.27`, no upper bound) and (b) actually expose
     `FastMCP.streamable_http_app()` — that method doesn't exist at all in
     earlier 1.x releases (confirmed empirically: present by 1.8.0, absent
     at 1.6.0/1.4.0). See requirements.txt for the exact pin and the
     `sse-starlette` companion pin `pip check` required alongside it.
  2. **`from __future__ import annotations` cannot be used in this file.**
     Every other module in this codebase opens with it (PEP 563 deferred
     evaluation, the project's default style) — this one deliberately
     doesn't. `mcp`'s `Tool.from_function` (`mcp/server/fastmcp/tools/base.py`)
     inspects each tool parameter's *runtime* annotation object directly
     (`get_origin(param.annotation)`, then `issubclass(param.annotation,
     Context)`) — it does not resolve stringified annotations. With the
     future import active, every annotation in this module becomes a
     plain string, `get_origin(...)` on a string returns `None` (so the
     union-type skip never fires), and `issubclass(<string>, Context)`
     raises `TypeError: issubclass() arg 1 must be a class` on the very
     first tool with more than zero parameters. Reproduced directly,
     confirmed the fix (dropping the future import) resolves it, and
     confirmed every tool registers and `main.py` imports cleanly end to
     end with it removed. If a future edit to this specific file
     reintroduces that import, tool registration will break exactly this
     way again.
"""

import contextvars
from typing import Any, Callable

from ai_interaction_settings import MCP_FREE_DAILY_REQUEST_CAP, MCP_PREMIUM_DAILY_REQUEST_CAP
from mcp_access import db_helpers, tools
from mcp_access.envelope import no_data, plan_required, rate_limited, revoked, scope_denied
from mcp_access.taxonomy import get_taxonomy

# Set by BearerTokenMiddleware (below) from the raw ASGI scope on every
# request, read by _authenticated_tool()'s wrapper at call time. A
# contextvar, not a global, so concurrent requests never see each other's
# token — each ASGI request gets its own context copy.
_current_bearer_token: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "_current_bearer_token", default=None
)


class BearerTokenMiddleware:
    """
    Plain ASGI middleware — deliberately operating at the transport layer
    (raw `scope["headers"]`), not on any `mcp`-SDK-internal request/context
    object, so it stays correct regardless of which SDK version is
    installed (see the VERIFY-FIRST note above: this is the *stable* half
    of the auth story, the SDK method names are the unstable half).
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            token = None
            for name, value in scope.get("headers", []):
                if name == b"authorization":
                    raw = value.decode("latin-1")
                    if raw.lower().startswith("bearer "):
                        token = raw[7:].strip()
                    break
            reset_token = _current_bearer_token.set(token)
            try:
                await self.app(scope, receive, send)
            finally:
                _current_bearer_token.reset(reset_token)
        else:
            await self.app(scope, receive, send)


def _daily_cap_for(plan: str) -> int:
    return MCP_PREMIUM_DAILY_REQUEST_CAP if plan == "premium" else MCP_FREE_DAILY_REQUEST_CAP


def _authenticate() -> db_helpers.ConnectionContext | dict:
    """Returns a ConnectionContext on success, or a curated error envelope
    (dict) on failure — callers check `isinstance(result, dict)`."""
    token = _current_bearer_token.get()
    if not token:
        return revoked()  # no token presented reads the same as "not connected"
    ctx = db_helpers.resolve_access_token(token)
    if ctx is None:
        return revoked()
    return ctx


def _enforce_and_call(tool_name: str, fn: Callable[..., dict], kwargs: dict[str, Any]) -> dict:
    """
    The one place every scoped tool's checks happen, in the exact order the
    backend spec lists them: revocation (live, inside _authenticate) ->
    scope -> plan -> rate limit -> the actual query. See
    backend/specs/mcp-access/api.md — Business Logic.
    """
    ctx = _authenticate()
    if isinstance(ctx, dict):
        return ctx

    required_scope = tools.TOOL_SCOPES[tool_name]
    if required_scope not in ctx.scopes:
        return scope_denied(required_scope, tool_name.replace("_", " "))

    if tool_name in tools.PREMIUM_ONLY_TOOLS and ctx.user_plan != "premium":
        return plan_required()

    allowed, _ = db_helpers.increment_and_check_usage(ctx.connection_id, _daily_cap_for(ctx.user_plan))
    if not allowed:
        return rate_limited("the start of the next UTC day")

    return fn(**kwargs)


def create_mcp_server():
    """Builds the FastMCP instance and registers all six tools plus
    get_taxonomy. Called once, from asgi_app() below."""
    from mcp.server.fastmcp import FastMCP  # imported here, not at module top,

    # streamable_http_path="/" — FastMCP defaults this to "/mcp" internally, which
    # doubled up with the "/mcp" prefix this app is mounted under in main.py
    # (app.mount("/mcp", asgi_app())), producing an unreachable /mcp/mcp. Found by
    # actually curling the deployed endpoint, not caught by import-level checks —
    # see the module docstring's verification note.
    mcp_server = FastMCP("Tech Market Intelligence Platform", streamable_http_path="/")

    @mcp_server.tool()
    def get_taxonomy_tool() -> dict:
        """Canonical taxonomy values (role category, level, track, etc.) so you
        never have to guess a valid parameter for the other tools. No
        authentication required."""
        return get_taxonomy()

    @mcp_server.tool()
    def get_job_demand(
        group_by: list[str],
        role_category: list[str] | None = None,
        specialization: list[str] | None = None,
        level: list[str] | None = None,
        track: list[str] | None = None,
        country: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        """Job demand — live-classified posting counts by role_category /
        specialization / level / track / country / month. Requires the
        'jobs.read' scope."""
        return _enforce_and_call("get_job_demand", tools.get_job_demand, dict(
            group_by=group_by, role_category=role_category, specialization=specialization,
            level=level, track=track, country=country, date_from=date_from, date_to=date_to,
        ))

    @mcp_server.tool()
    def get_salary_stats(
        role_category: list[str] | None = None,
        specialization: list[str] | None = None,
        level: list[str] | None = None,
        track: list[str] | None = None,
        country: list[str] | None = None,
    ) -> dict:
        """Salary/compensation statistics for a market slice. Requires the
        'compensation.read' scope AND a Premium plan."""
        return _enforce_and_call("get_salary_stats", tools.get_salary_stats, dict(
            role_category=role_category, specialization=specialization, level=level,
            track=track, country=country,
        ))

    @mcp_server.tool()
    def get_skill_demand(
        role_category: list[str] | None = None,
        specialization: list[str] | None = None,
        level: list[str] | None = None,
        track: list[str] | None = None,
        country: list[str] | None = None,
        skill_group: list[str] | None = None,
        raw_skill: list[str] | None = None,
        work_arrangement: list[str] | None = None,
        education_required: list[str] | None = None,
    ) -> dict:
        """Skills, education, work-arrangement, and language requirements
        from job postings. Requires the 'jobs.read' scope."""
        return _enforce_and_call("get_skill_demand", tools.get_skill_demand, dict(
            role_category=role_category, specialization=specialization, level=level, track=track,
            country=country, skill_group=skill_group, raw_skill=raw_skill,
            work_arrangement=work_arrangement, education_required=education_required,
        ))

    @mcp_server.tool()
    def get_employment_risk(
        company: str | None = None,
        sector: str | None = None,
        country: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        """Reported employment events (layoffs, closures, restructuring,
        bankruptcy, offshoring, expansion, hiring announcements) for any
        company or sector. Requires the 'companies.read' scope."""
        return _enforce_and_call("get_employment_risk", tools.get_employment_risk, dict(
            company=company, sector=sector, country=country, date_from=date_from, date_to=date_to,
        ))

    @mcp_server.tool()
    def list_tracked_companies() -> dict:
        """The companies this platform tracks job postings for, with
        industry where tagged. Requires the 'companies.read' scope."""
        return _enforce_and_call("list_tracked_companies", tools.list_tracked_companies, {})

    return mcp_server


def asgi_app():
    """Returns the mountable ASGI app for main.py: app.mount('/mcp', asgi_app())."""
    mcp_server = create_mcp_server()
    inner_app = mcp_server.streamable_http_app()  # see VERIFY-FIRST note, top of file
    return BearerTokenMiddleware(inner_app)
