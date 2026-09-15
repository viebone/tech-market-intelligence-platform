"""
OAuth 2.1 + PKCE + Dynamic Client Registration — see
backend/specs/mcp-access/api.md — OAuth 2.1 Authorization Flow.

GET/POST /mcp/oauth/authorize is server-rendered Jinja2, mounted on this
same api service (main.py) — not a frontend route. Matches the existing
/admin/login precedent (admin_main.py) rather than inventing a second way
this codebase serves an HTML page. See that spec section's own note on why
this was resolved this way, and frontend/specs/mcp-access/architecture.md's
Routing section, which has no route for this at all.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import auth
from mcp_access import db_helpers

router = APIRouter(prefix="/mcp/oauth", tags=["mcp-oauth"])

_BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(_BASE_DIR / "templates"))

# Where the consumer SPA's login page lives — this backend redirects a
# not-yet-signed-in visitor there and back, per the Routing decision in
# frontend/specs/mcp-access/architecture.md. Local dev default matches the
# Vite dev server; override via env once this is ever deployed (not now).
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")

# Plain-language scope descriptions — the consent screen's checklist wording.
# The frontend keeps its own copy of this same map for the Connected
# Assistant card's chips (frontend/specs/mcp-access/architecture.md — Data
# Requirements); duplicated deliberately, not imported, since one is Python
# rendered server-side and the other is bundled into the SPA — see that
# spec's Data Requirements note on why this pair only changes together.
SCOPE_DESCRIPTIONS = {
    "jobs.read": "Read job demand and skill trends",
    "companies.read": "Read company employment risk (layoffs, expansion)",
    "compensation.read": "Read salary data",
}


class RegisterRequest(BaseModel):
    client_name: str
    redirect_uris: list[str]


@router.post("/register")
def register_client(body: RegisterRequest):
    """Dynamic Client Registration (RFC 7591). No auth — any MCP client can
    register itself before its first user connects."""
    client = db_helpers.register_client(body.client_name, body.redirect_uris)
    return JSONResponse(client)


@router.get("/authorize")
def authorize_form(
    request: Request,
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query(...),
    scope: str = Query(""),
    state: str = Query(""),
    code_challenge: str = Query(...),
    code_challenge_method: str = Query(...),
):
    user_id = auth.current_user_id(request.cookies.get(auth.SESSION_COOKIE_NAME))
    if user_id is None:
        next_url = str(request.url)
        login_url = f"{FRONTEND_ORIGIN}/login?{urlencode({'next': next_url})}"
        return RedirectResponse(login_url, status_code=303)

    client = db_helpers.get_client(client_id)
    if client is None or redirect_uri not in client["redirect_uris"]:
        return JSONResponse({"error": "invalid_client_or_redirect_uri"}, status_code=400)
    if response_type != "code" or code_challenge_method != "S256":
        return JSONResponse({"error": "unsupported_response_type"}, status_code=400)

    requested_scopes = [s for s in scope.split() if s in SCOPE_DESCRIPTIONS]
    return templates.TemplateResponse(
        request,
        "consent.html",
        {
            "client_name": client["client_name"],
            "scopes": [{"id": s, "label": SCOPE_DESCRIPTIONS[s]} for s in requested_scopes],
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "requested_scope": scope,
        },
    )


@router.post("/authorize")
def authorize_submit(
    request: Request,
    action: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    state: str = Form(""),
    code_challenge: str = Form(...),
    requested_scope: str = Form(""),
):
    # Re-validate redirect_uri against the registered client on every POST,
    # not only when the GET form was rendered — the hidden form field is
    # client-controlled input at this point and must not be trusted blindly
    # (an unvalidated redirect_uri here would be an open redirect, even on
    # the "cancel" path).
    client = db_helpers.get_client(client_id)
    if client is None or redirect_uri not in client["redirect_uris"]:
        return JSONResponse({"error": "invalid_client_or_redirect_uri"}, status_code=400)

    if action != "allow":
        return RedirectResponse(
            f"{redirect_uri}?{urlencode({'error': 'access_denied', 'state': state})}",
            status_code=303,
        )

    user_id = auth.current_user_id(request.cookies.get(auth.SESSION_COOKIE_NAME))
    if user_id is None:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    granted_scopes = [s for s in requested_scope.split() if s in SCOPE_DESCRIPTIONS]
    code = db_helpers.create_authorization_code(
        user_id=user_id, client_id=client_id, scopes=granted_scopes,
        redirect_uri=redirect_uri, code_challenge=code_challenge,
    )
    return RedirectResponse(
        f"{redirect_uri}?{urlencode({'code': code, 'state': state})}", status_code=303,
    )


@router.post("/token")
def token(
    grant_type: str = Form(...),
    code: str | None = Form(default=None),
    redirect_uri: str | None = Form(default=None),
    client_id: str | None = Form(default=None),
    code_verifier: str | None = Form(default=None),
    refresh_token: str | None = Form(default=None),
):
    if grant_type == "authorization_code":
        if not (code and redirect_uri and client_id and code_verifier):
            return JSONResponse({"error": "invalid_request"}, status_code=400)
        try:
            connection_id, _user_id, scopes = db_helpers.exchange_authorization_code(
                code=code, redirect_uri=redirect_uri, client_id=client_id, code_verifier=code_verifier,
            )
        except db_helpers.InvalidGrant as exc:
            return JSONResponse({"error": "invalid_grant", "error_description": str(exc)}, status_code=400)
        access_token, refresh_token_out = db_helpers.issue_tokens(connection_id)
        return JSONResponse({
            "access_token": access_token,
            "refresh_token": refresh_token_out,
            "token_type": "Bearer",
            "expires_in": int(db_helpers.ACCESS_TOKEN_TTL.total_seconds()),
            "scope": " ".join(scopes),
        })

    if grant_type == "refresh_token":
        if not refresh_token:
            return JSONResponse({"error": "invalid_request"}, status_code=400)
        result = db_helpers.refresh_tokens(refresh_token)
        if result is None:
            # Unknown refresh token, or its connection is revoked — checked
            # live inside refresh_tokens(). Either way: 401, never a silent
            # "here's a token anyway".
            return JSONResponse({"error": "invalid_grant"}, status_code=401)
        new_access, new_refresh, scopes = result
        return JSONResponse({
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "Bearer",
            "expires_in": int(db_helpers.ACCESS_TOKEN_TTL.total_seconds()),
            "scope": " ".join(scopes),
        })

    return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)
