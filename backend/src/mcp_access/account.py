"""
Account & Connections endpoints — called by this product's own frontend
(features/account/, features/mcp-access/), never by an external MCP client.
See backend/specs/mcp-access/api.md — Account & Connections Endpoints.
"""

from __future__ import annotations

import os
import re

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import auth
from mcp_access import db_helpers

router = APIRouter(prefix="/api/account", tags=["account"])

# Cookie must be Secure in production (same reasoning as admin_main.py's
# ADMIN_COOKIE_SECURE) — overridable for local dev over plain HTTP.
COOKIE_SECURE = os.environ.get("USER_COOKIE_SECURE", "true").lower() != "false"

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _set_session_cookie(response: Response, user_id: int) -> None:
    token = auth.create_session_token(user_id)
    response.set_cookie(
        auth.SESSION_COOKIE_NAME, token,
        httponly=True, secure=COOKIE_SECURE, samesite="strict",
        max_age=auth.SESSION_EXPIRY_HOURS * 3600,
    )


def _user_payload(user: db_helpers.User) -> dict:
    return {"id": user.id, "email": user.email, "plan": user.plan}


@router.post("/signup")
def signup(body: SignupRequest):
    email = body.email.strip().lower()
    if not _EMAIL_RE.match(email):
        return JSONResponse({"error": "invalid_email"}, status_code=400)
    if len(body.password) < 8:
        return JSONResponse({"error": "weak_password"}, status_code=400)
    if db_helpers.get_user_by_email(email) is not None:
        return JSONResponse({"error": "email_already_registered"}, status_code=409)

    user = db_helpers.create_user(email, auth.hash_password(body.password))
    response = JSONResponse(_user_payload(user))
    _set_session_cookie(response, user.id)
    return response


@router.post("/login")
def login(body: LoginRequest):
    email = body.email.strip().lower()
    user = db_helpers.get_user_by_email(email)
    # Deliberately the same error, and the same status code, whether the
    # email doesn't exist or the password is wrong — never reveal which one
    # was incorrect (backend spec — POST /api/account/login Errors).
    if user is None or not auth.verify_password(body.password, user.password_hash):
        return JSONResponse({"error": "invalid_credentials"}, status_code=401)

    response = JSONResponse(_user_payload(user))
    _set_session_cookie(response, user.id)
    return response


@router.post("/logout")
def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie(auth.SESSION_COOKIE_NAME)
    return response


@router.get("/me")
def me(user_id: int = Depends(auth.require_user_session)):
    user = db_helpers.get_user_by_id(user_id)
    if user is None:
        return JSONResponse({"error": "not_found"}, status_code=404)
    return _user_payload(user)


@router.get("/connections")
def list_connections(user_id: int = Depends(auth.require_user_session)):
    user = db_helpers.get_user_by_id(user_id)
    return {
        "connections": db_helpers.list_connections_for_user(user_id),
        "plan": user.plan if user else "free",
    }


@router.delete("/connections/{connection_id}")
def revoke_connection(connection_id: str, user_id: int = Depends(auth.require_user_session)):
    if not db_helpers.revoke_connection(connection_id, user_id):
        return JSONResponse({"error": "not_found"}, status_code=404)
    return Response(status_code=204)
