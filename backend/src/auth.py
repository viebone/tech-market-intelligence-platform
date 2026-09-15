"""
Consumer account session — this product's first user-facing auth.

Deliberately separate from admin_auth.py: different secret (USER_JWT_SECRET,
never ADMIN_JWT_SECRET), different cookie, different audience (any signed-up
user, not a single operator identity). Same technique (bcrypt + PyJWT +
httpOnly cookie) reused for consistency, not shared code, since the two
concerns should never be able to forge each other's session even if one
secret leaks — see backend/specs/mcp-access/api.md — Business Logic —
Session auth, and outcomes/bring-your-own-ai-agent-access.md.

This is intentionally minimal — email + password only. No verification, no
password reset, no social login. See that spec's Out of scope.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Cookie

SESSION_COOKIE_NAME = "user_session"
SESSION_EXPIRY_HOURS = 24 * 14  # two weeks — a consumer session, not an
                                # operator one; re-logging in every 24h would
                                # be real friction for a returning job seeker.
JWT_ALGORITHM = "HS256"


class NotAuthenticated(Exception):
    """Raised by require_user_session() when the cookie is missing, invalid,
    or expired. Callers turn this into a 401 (API routes) or a redirect to
    /login (the one server-rendered page that needs a signed-in user, the
    OAuth consent screen) — never a raw stack trace."""


def hash_password(plain_password: str) -> str:
    """Same technique as admin_auth.hash_password (direct bcrypt, not
    passlib[bcrypt] — passlib is unmaintained and breaks against bcrypt>=4.0,
    confirmed the hard way when admin auth was built). Not the same function,
    on purpose — this module owns consumer password hashing independently."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def create_session_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(hours=SESSION_EXPIRY_HOURS),
    }
    return jwt.encode(payload, os.environ["USER_JWT_SECRET"], algorithm=JWT_ALGORITHM)


def _decode_session_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, os.environ["USER_JWT_SECRET"], algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    if sub is None:
        return None
    try:
        return int(sub)
    except (TypeError, ValueError):
        return None


def current_user_id(user_session: str | None = Cookie(default=None)) -> int | None:
    """Non-raising variant — returns None instead of erroring, for routes
    (like the OAuth consent screen) that need to branch on "signed in or
    not" rather than always requiring it."""
    if not user_session:
        return None
    return _decode_session_token(user_session)


def require_user_session(user_session: str | None = Cookie(default=None)) -> int:
    """FastAPI dependency guarding /api/account/* routes that need a real
    user (connections list, revoke, /me). Raises NotAuthenticated — an
    exception handler in main.py turns this into a plain 401 JSON body, per
    backend/specs/mcp-access/api.md's Account endpoints (never a redirect —
    unlike the consent screen, these are called by fetch(), not navigated
    to)."""
    user_id = current_user_id(user_session)
    if user_id is None:
        raise NotAuthenticated()
    return user_id
