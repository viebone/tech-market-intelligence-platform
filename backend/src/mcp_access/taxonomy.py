"""
Backs the `get_taxonomy` tool. Reuses this platform's own already-enforced
closed sets rather than hand-typing a second copy that could drift from
what market_query.py actually validates — see
backend/specs/mcp-access/api.md — Principle 9 ("the platform's own taxonomy
stays authoritative").

Note: `market_query`'s allowed-set constants are underscore-prefixed
(module-private by convention) — there's no public re-export today. Imported
directly anyway rather than duplicating their contents, with this comment as
the honest flag: a small public re-export in market_query.py would be a
reasonable future cleanup, not done here since it's outside this feature's
scope.
"""

from __future__ import annotations

from employment_events.base import EVENT_TYPES
from market_query import (
    _ALLOWED_EDUCATION_REQUIRED,
    _ALLOWED_LEVEL,
    _ALLOWED_ROLE_CATEGORIES,
    _ALLOWED_TRACK,
    _ALLOWED_WORK_ARRANGEMENT,
)

# Human-readable labels for the closed sets that only exist as machine
# values today. Kept here, not invented per-value elsewhere, so a label
# change is a one-line edit.
# Display-only relabel (2026-09-22 — changes/2026-09-22-role-category-display-relabel.md):
# "Design" / "Product Management" / "Engineering" reads as the occupation family, matching
# job-classification.md's own internal "occupation family" reasoning. The machine values
# ("Designer" / "Product Manager" / "Engineer") stay exactly as stored — this is exactly the
# "label change is a one-line edit" this dict's own module docstring anticipated.
_ROLE_CATEGORY_LABELS = {
    "Designer": "Design",
    "Product Manager": "Product Management",
    "Engineer": "Engineering",
    "other": "Not a tracked occupation",
    "unknown": "Not enough signal to classify",
}
_LEVEL_LABELS = {v: v.replace("_", " ").title() for v in _ALLOWED_LEVEL}
_TRACK_LABELS = {"ic": "Individual contributor", "management": "Management", "unknown": "Unknown"}
_WORK_ARRANGEMENT_LABELS = {v: v.replace("_", " ").title() for v in _ALLOWED_WORK_ARRANGEMENT}
_EDUCATION_REQUIRED_LABELS = {v: v.replace("_", " ").title() for v in _ALLOWED_EDUCATION_REQUIRED}
_EVENT_TYPE_LABELS = {v: v.replace("_", " ").title() for v in EVENT_TYPES}
_CONFIDENCE_LABELS = {
    "confirmed": "A statutory filing or official register",
    "reported": "Compiled by the registry from public announcements",
}


def _pairs(values: set[str] | dict[str, str], labels: dict[str, str]) -> list[dict[str, str]]:
    keys = values if isinstance(values, (set, frozenset)) else values.keys()
    return [{"value": v, "label": labels.get(v, v)} for v in sorted(keys)]


def get_taxonomy() -> dict:
    """No scope required — reference metadata, not user data (same reasoning
    this platform's frontend can always read job-classification.md without
    auth). See backend/specs/mcp-access/api.md — MCP Tools."""
    return {
        "data": {
            "role_category": _pairs(_ROLE_CATEGORY_LABELS, _ROLE_CATEGORY_LABELS),
            "level": _pairs(_ALLOWED_LEVEL, _LEVEL_LABELS),
            "track": _pairs(_ALLOWED_TRACK, _TRACK_LABELS),
            "work_arrangement": _pairs(_ALLOWED_WORK_ARRANGEMENT, _WORK_ARRANGEMENT_LABELS),
            "education_required": _pairs(_ALLOWED_EDUCATION_REQUIRED, _EDUCATION_REQUIRED_LABELS),
            "employment_event_type": _pairs(EVENT_TYPES, _EVENT_TYPE_LABELS),
            "employment_event_direction": [
                {"value": "contraction", "label": "Contraction (layoff, closure, restructuring, bankruptcy, offshoring)"},
                {"value": "expansion", "label": "Expansion (expansion, hiring announcement)"},
            ],
            "employment_event_confidence": _pairs(_CONFIDENCE_LABELS, _CONFIDENCE_LABELS),
            "specialization": {
                "note": (
                    "Open-ended, curated per role_category — not a fixed enum this tool can "
                    "enumerate today. Pass any specific specialization string (e.g. "
                    "'UX Designer', 'Backend Engineer'); an unrecognised value simply matches "
                    "no postings rather than erroring."
                )
            },
            "skill_group": {
                "note": (
                    "Open-ended, curated per role_category/track/specialization — not a fixed "
                    "enum this tool can enumerate today. Use get_skill_demand without a "
                    "skill_group filter to discover which groups actually have data for a "
                    "given slice."
                )
            },
        },
        "meta": {
            "unit": "reference values, not measurements",
            "scope": {},
            "time_window": {"from": None, "to": None, "label": "not applicable"},
            "source": "This platform's own classification taxonomy",
        },
    }
