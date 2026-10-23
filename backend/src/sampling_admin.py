"""
Admin read side for sampling — backend/specs/pipeline-visibility/api.md — GET /admin/sampling;
design/pipeline-visibility/experience.md — User Flow 14, Sampling panel / Sampling by group.

One function backs both the Overview panel and the per-group page, so they can't disagree.
Read-only. Postings stored before SAMPLING_GO_LIVE with no decision row read as kept in full
("kept_before_sampling"), the same rule the requirements pipeline uses.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import method_text
import sampling_settings as settings
from db import get_connection

_DECISION_SQL = f"""
    COALESCE(ps.decision, CASE WHEN rp.created_at < '{settings.SAMPLING_GO_LIVE.isoformat()}'
                               THEN 'kept_before_sampling' ELSE 'pending' END)
"""


def _month_bounds(month: str | None) -> tuple[date, date]:
    if month:
        year, mon = (int(x) for x in month.split("-"))
        start = date(year, mon, 1)
    else:
        now = datetime.now(timezone.utc)
        start = date(now.year, now.month, 1)
    end = (start + timedelta(days=32)).replace(day=1)
    return start, end


def month_summary(month: str | None = None) -> dict:
    start, end = _month_bounds(month)
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT COALESCE(c.role_category, 'unclassified') AS role,
                   COALESCE(c.specialization, '') AS spec,
                   {_DECISION_SQL} AS decision,
                   ps.reason,
                   (pr.posting_id IS NOT NULL) AS read,
                   count(*)
            FROM raw_postings rp
            LEFT JOIN classifications c ON c.posting_id = rp.id
            LEFT JOIN posting_samples ps ON ps.posting_id = rp.id
            LEFT JOIN posting_requirements pr ON pr.posting_id = rp.id
            WHERE rp.created_at >= %s AND rp.created_at < %s
            GROUP BY 1, 2, 3, 4, 5
            """,
            (start, end),
        ).fetchall()

    panel = {"seen": 0, "kept": 0, "read": 0, "not_kept": 0, "pending": 0}
    groups: dict[tuple[str, str], dict] = {}
    for role, spec, decision, reason, read, n in rows:
        panel["seen"] += n
        g = groups.setdefault((role, spec), {"role": role, "specialization": spec or None, "seen": 0,
                                             "kept": 0, "kept_unknown_role": 0, "not_kept": 0, "pending": 0,
                                             "sampled_any": False})
        g["seen"] += n
        if decision in ("kept", "kept_before_sampling"):
            panel["kept"] += n
            g["kept"] += n
            if reason == "unknown_role":
                g["kept_unknown_role"] += n
            if read:
                panel["read"] += n
            if reason == "selected":
                g["sampled_any"] = True
        elif decision == "not_kept":
            panel["not_kept"] += n
            g["not_kept"] += n
            g["sampled_any"] = True
        else:
            panel["pending"] += n
            g["pending"] += n

    out_groups = []
    for g in groups.values():
        limit = settings.limit_for(g["role"]) if g["role"] != "unclassified" else None
        counted = g["kept"] - (g["kept_unknown_role"] if g["role"] != "unknown" else 0)
        if limit is not None and counted > settings.OVER_LIMIT_TOLERANCE * limit:
            status = "over_limit"
        elif g["sampled_any"]:
            status = "sampled"
        else:
            status = "under_limit"
        out_groups.append({"role": g["role"], "specialization": g["specialization"], "seen": g["seen"],
                           "kept": g["kept"], "not_kept": g["not_kept"], "pending": g["pending"],
                           "limit": limit, "status": status})
    out_groups.sort(key=lambda g: g["seen"], reverse=True)
    return {"month": start.strftime("%Y-%m"), "month_label": start.strftime("%B %Y"),
            "rule_line": method_text.rule_line(), "panel": panel, "groups": out_groups}


def storage_split() -> dict:
    """Technical data footprint: postings kept in full vs. short record only."""
    with get_connection() as conn:
        row = conn.execute(
            f"""
            SELECT count(*) FILTER (WHERE {_DECISION_SQL} IN ('kept', 'kept_before_sampling')),
                   count(*) FILTER (WHERE {_DECISION_SQL} = 'not_kept'),
                   count(*) FILTER (WHERE {_DECISION_SQL} = 'pending')
            FROM raw_postings rp LEFT JOIN posting_samples ps ON ps.posting_id = rp.id
            """
        ).fetchone()
    return {"kept_in_full": row[0], "short_record_only": row[1], "pending": row[2]}
