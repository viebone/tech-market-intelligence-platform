"""
Auth for the pipeline-visibility admin dashboard.

JWT login + httpOnly session cookie, single operator, no user table — see
backend/specs/pipeline-visibility/api.md — Auth decision for the full
reasoning (this product's CLAUDE.md already names JWT as the intended
backend auth mechanism; a bare shared-secret Basic Auth would have silently
diverged from that with no stated reason).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Cookie

SESSION_COOKIE_NAME = "admin_session"
SESSION_EXPIRY_HOURS = 24
JWT_ALGORITHM = "HS256"
JWT_SUBJECT = "operator"  # single fixed identity — no user table


class NotAuthenticated(Exception):
    """Raised by require_admin_session() when the cookie is missing, invalid,
    or expired. Caught by an exception handler in admin_main.py that redirects
    to /admin/login — never rendered as a raw error page, and never leaks
    which specific check failed."""


def verify_password(plain_password: str) -> bool:
    """
    Compares against ADMIN_PASSWORD_HASH (bcrypt) — never a plaintext
    comparison, and the submitted password is never logged.

    Uses the `bcrypt` package directly, not passlib[bcrypt] — passlib is
    unmaintained (last release 2020) and its backend self-test raises
    (`AttributeError: module 'bcrypt' has no attribute '__about__'`, then a
    ValueError from a bogus 72-byte-truncation check) against bcrypt>=4.0,
    confirmed the hard way while verifying this implementation against real
    dependencies. bcrypt's own API needs no such compatibility shim.
    """
    password_hash = os.environ["ADMIN_PASSWORD_HASH"]
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def hash_password(plain_password: str) -> str:
    """Generates an ADMIN_PASSWORD_HASH value — see backend/.env.example for
    the one-line command that calls this to set up a real password."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_session_token() -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": JWT_SUBJECT,
        "iat": now,
        "exp": now + timedelta(hours=SESSION_EXPIRY_HOURS),
    }
    return jwt.encode(payload, os.environ["ADMIN_JWT_SECRET"], algorithm=JWT_ALGORITHM)


def _verify_session_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, os.environ["ADMIN_JWT_SECRET"], algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return False
    return payload.get("sub") == JWT_SUBJECT


def require_admin_session(admin_session: str | None = Cookie(default=None)) -> None:
    """
    FastAPI dependency guarding every /admin/* route except /admin/login and
    /admin/logout. No expiry refresh — after SESSION_EXPIRY_HOURS the
    operator re-enters the password; deliberately simple for a single
    operator (backend/specs/pipeline-visibility/api.md — Auth decision).
    """
    if not admin_session or not _verify_session_token(admin_session):
        raise NotAuthenticated()
