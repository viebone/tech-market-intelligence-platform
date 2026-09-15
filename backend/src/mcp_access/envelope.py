"""
The shared response envelope every MCP tool returns. See
backend/specs/mcp-access/api.md — Response envelope, and
design/mcp-access/experience.md Part 2's data-legibility contract: since an
external AI may quote a value verbatim with no added framing of its own,
every value's unit/scope/time-window/source has to travel inside the same
JSON payload, not in a separate document the AI would have to already know
to fetch.

One place builds this so all six tools stay consistent — never six
near-duplicate implementations.
"""

from __future__ import annotations

from typing import Any


def build_envelope(
    data: dict[str, Any],
    *,
    unit: str,
    scope: dict[str, Any],
    time_window: dict[str, str | None],
    source: str,
    taxonomy_version: str | None = None,
    total_matching: int | None = None,
    sources_checked: list[str] | None = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "unit": unit,
        "scope": scope,
        "time_window": time_window,
        "source": source,
    }
    if taxonomy_version is not None:
        meta["taxonomy_version"] = taxonomy_version
    if total_matching is not None:
        meta["total_matching"] = total_matching
    if sources_checked is not None:
        meta["sources_checked"] = sources_checked
    return {"data": data, "meta": meta}


def time_window_label(earliest: str | None, latest: str | None) -> dict[str, str | None]:
    """`from`/`to` plus a human `label` — never a bare ISO pair with no
    words-form (Response envelope, `time_window`)."""
    if earliest is None and latest is None:
        label = "no data in range"
    elif earliest == latest:
        label = earliest
    else:
        label = f"{earliest} to {latest}"
    return {"from": earliest, "to": latest, "label": label}


# --- Curated errors — backend/specs/mcp-access/api.md — Curated error responses ---

def error_envelope(error_type: str, message: str) -> dict[str, Any]:
    return {"error": {"type": error_type, "message": message}}


def scope_denied(missing_scope: str, label: str) -> dict[str, Any]:
    return error_envelope(
        "scope_denied",
        f"This connection doesn't have permission to {label}. "
        f"Reconnect and grant '{missing_scope}' to use this.",
    )


def plan_required(plan_name: str = "Premium") -> dict[str, Any]:
    return error_envelope(
        "plan_required",
        f"This requires a {plan_name} plan. This account is on the Free plan.",
    )


def rate_limited(reset_at_label: str) -> dict[str, Any]:
    return error_envelope(
        "rate_limited",
        f"This connection has reached its daily request limit. It resets at {reset_at_label}.",
    )


def revoked() -> dict[str, Any]:
    return error_envelope("revoked", "Access to this platform was revoked.")


def no_data(message: str) -> dict[str, Any]:
    """Deliberately NOT under the 'error' key at the transport level in the
    tool's own semantics — see the backend spec: a real, honest 'nothing
    found' is a successful answer, matching the in-app chat's own NO_DATA:
    convention. Callers return this as ordinary tool data, not as an
    exception."""
    return {"data": {"message": message}, "meta": {}}
