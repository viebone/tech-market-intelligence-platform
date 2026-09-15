"""
Data access for users, MCP clients/connections/tokens/auth-codes, and usage
counters. See backend/specs/mcp-access/api.md — Data Models.

Every read that gates access (revocation, scope, plan) is a live query
against the database — never cached, never checked only at issuance time.
That is the entire mechanism behind "revocation takes effect on the very
next call, no grace window" (Business Logic — Revocation): there is no
separate cache to invalidate, so there is nothing that can go stale.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from db import get_connection

ACCESS_TOKEN_TTL = timedelta(hours=1)
AUTH_CODE_TTL = timedelta(minutes=10)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _new_opaque_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(24)}"


def verify_pkce(code_verifier: str, code_challenge: str) -> bool:
    """PKCE S256 check (RFC 7636) — pulled out as its own pure function
    (no database access) specifically so it's unit-testable without a live
    connection standing in. Used by exchange_authorization_code, below."""
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return computed == code_challenge


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@dataclass
class User:
    id: int
    email: str
    password_hash: str
    plan: str


def create_user(email: str, password_hash: str) -> User:
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (%s, %s)
            RETURNING id, email, password_hash, plan
            """,
            (email, password_hash),
        ).fetchone()
    return User(*row)


def get_user_by_email(email: str) -> User | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash, plan FROM users WHERE email = %s",
            (email,),
        ).fetchone()
    return User(*row) if row else None


def get_user_by_id(user_id: int) -> User | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash, plan FROM users WHERE id = %s",
            (user_id,),
        ).fetchone()
    return User(*row) if row else None


# ---------------------------------------------------------------------------
# Dynamic Client Registration (RFC 7591)
# ---------------------------------------------------------------------------

def register_client(client_name: str, redirect_uris: list[str]) -> dict:
    client_id = _new_opaque_id("mcpc")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO mcp_clients (client_id, client_name, redirect_uris)
            VALUES (%s, %s, %s)
            """,
            (client_id, client_name, json.dumps(redirect_uris)),
        )
    return {"client_id": client_id, "client_name": client_name, "redirect_uris": redirect_uris}


def get_client(client_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT client_id, client_name, redirect_uris FROM mcp_clients WHERE client_id = %s",
            (client_id,),
        ).fetchone()
    if not row:
        return None
    return {"client_id": row[0], "client_name": row[1], "redirect_uris": row[2]}


# ---------------------------------------------------------------------------
# Authorization codes + connections (the consent step)
# ---------------------------------------------------------------------------

def create_authorization_code(
    user_id: int, client_id: str, scopes: list[str], redirect_uri: str, code_challenge: str
) -> str:
    """Issued on 'Allow'. Does NOT create the connection yet — that happens
    atomically with the code exchange (exchange_authorization_code, below),
    per the backend spec's 'a connection never exists without a
    corresponding grant event' rule and 'no partial grant is ever recorded'
    on Cancel."""
    code = _new_opaque_id("mcpac")
    expires_at = datetime.now(timezone.utc) + AUTH_CODE_TTL
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO mcp_auth_codes
                (code, user_id, client_id, scopes, redirect_uri, code_challenge, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (code, user_id, client_id, json.dumps(scopes), redirect_uri, code_challenge, expires_at),
        )
    return code


class InvalidGrant(Exception):
    """Code unknown, already used, expired, redirect_uri mismatch, or PKCE
    verifier mismatch — maps to a 400 at the router level."""


def exchange_authorization_code(
    code: str, redirect_uri: str, client_id: str, code_verifier: str
) -> tuple[str, str, list[str]]:
    """
    Redeems a code exactly once, creating the McpConnection in the same
    transaction — this is the one place a connection row is born. Returns
    (connection_id, user_id_as_str, scopes) for the caller to mint tokens
    from (issue_tokens, below) outside this transaction.
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT user_id, client_id, scopes, redirect_uri, code_challenge, expires_at, used_at
            FROM mcp_auth_codes WHERE code = %s
            """,
            (code,),
        ).fetchone()
        if row is None:
            raise InvalidGrant("unknown code")
        user_id, code_client_id, scopes, code_redirect_uri, code_challenge, expires_at, used_at = row
        if used_at is not None:
            raise InvalidGrant("code already used")
        if expires_at < datetime.now(timezone.utc):
            raise InvalidGrant("code expired")
        if code_client_id != client_id or code_redirect_uri != redirect_uri:
            raise InvalidGrant("client_id/redirect_uri mismatch")
        if not verify_pkce(code_verifier, code_challenge):
            raise InvalidGrant("code_verifier does not match code_challenge")

        conn.execute("UPDATE mcp_auth_codes SET used_at = now() WHERE code = %s", (code,))

        client_row = conn.execute(
            "SELECT client_name FROM mcp_clients WHERE client_id = %s", (client_id,)
        ).fetchone()
        client_name = client_row[0] if client_row else client_id

        connection_id = _new_opaque_id("conn")
        conn.execute(
            """
            INSERT INTO mcp_connections (id, user_id, client_id, client_name, scopes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (connection_id, user_id, client_id, client_name, json.dumps(scopes)),
        )
    return connection_id, user_id, scopes


def issue_tokens(connection_id: str) -> tuple[str, str]:
    """Mints a fresh (access_token, refresh_token) pair for a connection.
    Called after exchange_authorization_code, and again on every refresh
    grant. Raw tokens are returned once here and never stored — only their
    SHA-256 hash is persisted (Data Models — OAuthToken)."""
    access_token = _new_opaque_id("mat")
    refresh_token = _new_opaque_id("mrt")
    now = datetime.now(timezone.utc)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO mcp_tokens (token_hash, connection_id, kind, expires_at)
            VALUES (%s, %s, 'access', %s)
            """,
            (_hash_token(access_token), connection_id, now + ACCESS_TOKEN_TTL),
        )
        conn.execute(
            """
            INSERT INTO mcp_tokens (token_hash, connection_id, kind, expires_at)
            VALUES (%s, %s, 'refresh', %s)
            """,
            # Refresh tokens don't expire on a timer (Business Logic — Token
            # lifetimes) — a far-future sentinel keeps the NOT NULL column
            # honest without giving refresh a real expiry to reason about.
            (_hash_token(refresh_token), connection_id, now.replace(year=now.year + 50)),
        )
    return access_token, refresh_token


def refresh_tokens(refresh_token: str) -> tuple[str, str, list[str]] | None:
    """Returns (new_access_token, new_refresh_token, scopes) or None if the
    refresh token is unknown OR its connection is revoked — checked live,
    same discipline as every other revocation check in this module. The old
    refresh token is deleted (rotation) so a leaked, already-used refresh
    token can't be replayed."""
    token_hash = _hash_token(refresh_token)
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT mt.connection_id, mc.revoked_at, mc.scopes
            FROM mcp_tokens mt
            JOIN mcp_connections mc ON mc.id = mt.connection_id
            WHERE mt.token_hash = %s AND mt.kind = 'refresh'
            """,
            (token_hash,),
        ).fetchone()
        if row is None:
            return None
        connection_id, revoked_at, scopes = row
        if revoked_at is not None:
            return None
        conn.execute("DELETE FROM mcp_tokens WHERE token_hash = %s", (token_hash,))
    return (*issue_tokens(connection_id), scopes)


# ---------------------------------------------------------------------------
# Resolving a bearer access token at MCP tool-call time
# ---------------------------------------------------------------------------

@dataclass
class ConnectionContext:
    connection_id: str
    user_id: int
    user_plan: str
    scopes: list[str]


def resolve_access_token(access_token: str) -> ConnectionContext | None:
    """The live check every tool call makes. None means: unknown token,
    expired token, or — the important case — a revoked connection. There is
    deliberately no separate 'is this connection revoked' cache; this query
    IS the revocation check, run fresh every time."""
    token_hash = _hash_token(access_token)
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT mc.id, mc.user_id, u.plan, mc.scopes
            FROM mcp_tokens mt
            JOIN mcp_connections mc ON mc.id = mt.connection_id
            JOIN users u ON u.id = mc.user_id
            WHERE mt.token_hash = %s
              AND mt.kind = 'access'
              AND mt.expires_at > now()
              AND mc.revoked_at IS NULL
            """,
            (token_hash,),
        ).fetchone()
    if row is None:
        return None
    connection_id, user_id, plan, scopes = row
    return ConnectionContext(connection_id=connection_id, user_id=user_id, user_plan=plan, scopes=scopes)


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def increment_and_check_usage(connection_id: str, daily_cap: int) -> tuple[bool, int]:
    """
    Increments today's counter BEFORE the tool runs (Business Logic —
    Rate limiting: 'enforced before each call, not reconciled after'), then
    reports whether the connection is now over its cap. Returns
    (allowed, requests_used_today).
    """
    today = date.today()
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO mcp_usage (connection_id, usage_date, request_count)
            VALUES (%s, %s, 1)
            ON CONFLICT (connection_id, usage_date)
            DO UPDATE SET request_count = mcp_usage.request_count + 1
            RETURNING request_count
            """,
            (connection_id, today),
        ).fetchone()
    request_count = row[0]
    return request_count <= daily_cap, request_count


# ---------------------------------------------------------------------------
# Connections list / revoke (Settings tab)
# ---------------------------------------------------------------------------

def list_connections_for_user(user_id: int) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, client_name, scopes, created_at, revoked_at
            FROM mcp_connections
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [
        {
            "id": r[0],
            "client_name": r[1],
            "scopes": r[2],
            "created_at": r[3].isoformat(),
            "revoked_at": r[4].isoformat() if r[4] else None,
        }
        for r in rows
    ]


def revoke_connection(connection_id: str, user_id: int) -> bool:
    """Sets revoked_at, and deletes every token row outright — belt and
    braces (Business Logic — Revocation: the live revoked_at check alone
    already guarantees immediate effect; deleting tokens too means nothing
    is left to leak even in a bug). Returns False if the connection doesn't
    exist or isn't this user's — the router turns that into a 404."""
    with get_connection() as conn:
        result = conn.execute(
            """
            UPDATE mcp_connections SET revoked_at = now()
            WHERE id = %s AND user_id = %s AND revoked_at IS NULL
            """,
            (connection_id, user_id),
        )
        if result.rowcount == 0:
            return False
        conn.execute("DELETE FROM mcp_tokens WHERE connection_id = %s", (connection_id,))
    return True
