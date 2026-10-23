"""
Sampling settings — backend/specs/market-health/api.md — Business Logic — Sampling;
changes/2026-10-10-requirements-extraction-sampling.md (scope widened to storage 2026-10-23).

One sampling decision per posting decides both whether its full job details are kept and, for
tracked roles, whether it is read for requirements. The limits are settings, not taxonomy: they
can be changed with an environment variable and no code change (owner's decision), and every
surface that explains the method (method_text.py) renders the live values.

Env overrides:
    SAMPLING_LIMIT_DEFAULT=50              # Engineer, Product Manager, other
    SAMPLING_LIMIT_DESIGNER=none           # "none" = no limit (keep and read every one)
    SAMPLING_LIMIT_ENGINEER=50 / SAMPLING_LIMIT_PRODUCT_MANAGER=50 / SAMPLING_LIMIT_OTHER=50
    SAMPLING_GO_LIVE=2026-10-24T00:00:00+00:00
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

# Postings first stored at or after this moment are sampled; everything before keeps its full
# details (owner: "going forward only"). Set to the first cron after the sampling deploy.
SAMPLING_GO_LIVE = datetime.fromisoformat(os.environ.get("SAMPLING_GO_LIVE", "2026-10-24T00:00:00+00:00"))
if SAMPLING_GO_LIVE.tzinfo is None:
    SAMPLING_GO_LIVE = SAMPLING_GO_LIVE.replace(tzinfo=timezone.utc)

_DEFAULT_LIMIT = 50
# Roles with no limit unless overridden. Designer: the product's core audience and a small volume.
_UNLIMITED_BY_DEFAULT = {"Designer"}
# Always kept in full whatever the settings say: the description-assisted recovery pass reads the
# description, so dropping it would leave the posting `unknown` for good.
ALWAYS_KEEP_ROLES = {"unknown"}

# A posting still undecided after this many days, and no longer on its board, is recorded as
# not kept ("unavailable") — its payload is gone.
SAMPLING_PENDING_MAX_DAYS = 14
# From this day of the month the rate is re-checked against the month's projected size, and can
# only go down — so a new source can't fill a group in its first week.
RECALIBRATE_FROM_DAY = 7
# Surge backstop: a group never keeps more than this multiple of its limit in one month.
CEILING_MULTIPLIER = 2
# Admin flags a group as "over the limit" above this multiple (normal Poisson spread is ±2.5 sd).
OVER_LIMIT_TOLERANCE = 1.5

# Roles whose kept postings are read for requirements (the others are kept, never read).
TRACKED_ROLES = ("Designer", "Product Manager", "Engineer")


def _env_key(role: str) -> str:
    return "SAMPLING_LIMIT_" + role.upper().replace(" ", "_")


def _parse(value: str) -> int | None:
    value = value.strip().lower()
    return None if value in ("none", "all", "") else int(value)


def default_limit() -> int:
    return int(os.environ.get("SAMPLING_LIMIT_DEFAULT", _DEFAULT_LIMIT))


def limit_for(role_category: str | None) -> int | None:
    """Monthly limit of postings kept in full per (role, specialization) group, or None for no
    limit. `unknown` is always unlimited (see ALWAYS_KEEP_ROLES)."""
    if role_category in ALWAYS_KEEP_ROLES:
        return None
    override = os.environ.get(_env_key(role_category or "other"))
    if override is not None:
        return _parse(override)
    if role_category in _UNLIMITED_BY_DEFAULT:
        return None
    return default_limit()
