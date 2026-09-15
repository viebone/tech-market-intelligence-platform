"""
OAuth discovery metadata — RFC 8414 (Authorization Server Metadata) and
RFC 9728 (Protected Resource Metadata), both referenced by MCP's own
Authorization spec.

This was the actual cause of a real "Couldn't register with TMIP's sign-in
service" error from a live Claude connection attempt, not a hypothetical:
the OAuth endpoints themselves (register/authorize/token,
mcp_access/oauth.py) existed and worked, but nothing told a connecting
client *where* they live. A client doesn't guess — it fetches one of
these well-known documents first, then uses the URLs inside it. Without
them, "register" is the very first step that has nowhere to go.

This server is both the resource server (the /mcp endpoint) and its own
authorization server (issues its own tokens) — the common, simplest MCP
deployment shape. Both documents point at the same origin.
"""

from __future__ import annotations

import os

from fastapi import APIRouter

router = APIRouter(tags=["oauth-discovery"])

# The public base URL this server is actually reachable at. Local dev
# defaults to the local backend; set on the deployed api service to its
# real domain (https://api-production-df13.up.railway.app) — every URL
# below is built from this one value so it can't drift into inconsistency
# across the two documents.
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:8000")

# Where the consumer SPA lives — the single source of truth for this value
# (mcp_access/oauth.py imports it from here rather than reading its own copy
# of the env var, so the two can't drift apart the way PUBLIC_BASE_URL and
# this one briefly did in practice — see authorization_endpoint below).
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")

SUPPORTED_SCOPES = ["jobs.read", "companies.read", "compensation.read"]


@router.get("/.well-known/oauth-authorization-server")
def oauth_authorization_server_metadata():
    """RFC 8414. Tells a client where this server's authorize/token/
    register endpoints actually are — mcp_access/oauth.py's router, which
    a client has no way to find without this.

    authorization_endpoint deliberately points at FRONTEND_ORIGIN (`web`'s
    own domain, proxied server-side to this api service — see
    frontend/vite.config.ts), not PUBLIC_BASE_URL like the other two.
    Confirmed the hard way against a real Claude connection, 2026-09-15:
    the session cookie a user gets from logging in is scoped to whichever
    origin the browser believes it talked to. Login happens through `web`'s
    own domain (the SPA's relative fetches), so the cookie is scoped there.
    If a client is sent straight to `api`'s own domain for authorize — a
    different site, even though it's the same physical service — that
    cookie never arrives, the login appears to silently do nothing, and the
    user is bounced right back to the login page. token_endpoint and
    registration_endpoint have no such problem: both are called
    server-to-server by the connecting client's own backend, never by the
    user's browser, so no cookie is ever involved for them."""
    return {
        "issuer": PUBLIC_BASE_URL,
        "authorization_endpoint": f"{FRONTEND_ORIGIN}/mcp/oauth/authorize",
        "token_endpoint": f"{PUBLIC_BASE_URL}/mcp/oauth/token",
        "registration_endpoint": f"{PUBLIC_BASE_URL}/mcp/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        # Public clients only (Data Models — McpClient: "no client_secret" —
        # every MCP client is treated as public, using PKCE, never a secret).
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": SUPPORTED_SCOPES,
    }


@router.get("/.well-known/oauth-protected-resource")
@router.get("/.well-known/oauth-protected-resource/mcp")
def oauth_protected_resource_metadata():
    """RFC 9728. Tells a client that the /mcp endpoint is protected, and by
    which authorization server (this same origin, since this deployment
    doesn't separate the two roles). Registered at both the bare
    well-known path and the resource-path-appended variant — different
    clients probe different candidates first; serving both costs nothing
    and removes a guess."""
    return {
        "resource": f"{PUBLIC_BASE_URL}/mcp",
        "authorization_servers": [PUBLIC_BASE_URL],
        "scopes_supported": SUPPORTED_SCOPES,
    }
