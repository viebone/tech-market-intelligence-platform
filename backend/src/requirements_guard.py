"""
Repeat-work guardrails for paid requirements extraction — see
backend/specs/market-health/api.md — Business Logic — Repeat-work guardrails, and
changes/2026-10-10-requirements-re-extraction-loop.md (CLAUDE.md Rule 15).

Why this exists: from 2026-09-21 to 2026-10-10 a daily step deleted every extracted
requirements row, and a correctly rate-capped batch lane paid to re-read the same 500 postings
every day. The request budgets and MAX_BATCH_USD bound how fast money is spent; nothing noticed
the money buying nothing. These checks do, whatever the cause.

The thresholds are code constants on purpose, not env vars: a tripwire shouldn't be one config
flip away from off. Raising them is a change request.
"""

from __future__ import annotations

from db import get_connection

# A lane refuses to spend when more than this many of the postings it is about to pay for were
# already paid for before, with no deliberate reprocess request explaining it...
REPEAT_WORK_MAX_COUNT = 50
# ...or when they are more than this share of the selection.
REPEAT_WORK_MAX_SHARE = 0.10
# A daily run may delete at most this many postings' requirements. Larger reprocessing goes
# through a manual script with allow_bulk=True and a change_ref.
DAILY_REPROCESS_DELETE_CAP = 200
# guard_detail.unexplained_ids is capped so a pathological day can't bloat a run row.
MAX_IDS_IN_DETAIL = 200

# Most severe first. "ok" is the absence of any.
GUARD_SEVERITY = [
    "repeat_work_blocked_batch",
    "repeat_work_blocked_interactive",
    "delete_cap_blocked",
    "batch_submit_incomplete",
]


class RequirementsDeleteCapExceeded(Exception):
    """A daily-path delete asked for more than DAILY_REPROCESS_DELETE_CAP postings. Raised
    before any SQL runs — nothing was deleted."""

    def __init__(self, attempted: int, cap: int = DAILY_REPROCESS_DELETE_CAP):
        super().__init__(f"refused to delete requirements for {attempted} postings (daily cap {cap})")
        self.attempted = attempted
        self.cap = cap


def is_blocked(selected: int, unexplained: int) -> bool:
    """The breaker's rule, kept pure so it is testable without a database."""
    if unexplained < 1 or selected <= 0:
        return False
    return unexplained > REPEAT_WORK_MAX_COUNT or unexplained > REPEAT_WORK_MAX_SHARE * selected


def prior_extractions(posting_ids: list[str]) -> dict[str, bool]:
    """For each of `posting_ids` that has ever been extracted (a ledger row), whether that repeat
    is *explained*: a reprocess request newer than its latest ledger row. Postings never
    extracted are absent from the result."""
    if not posting_ids:
        return {}
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT l.posting_id,
                   MAX(l.extracted_at) AS last_extracted,
                   (SELECT MAX(r.requested_at) FROM requirements_reprocess_requests r
                     WHERE r.posting_id = l.posting_id) AS last_requested
            FROM requirements_extraction_ledger l
            WHERE l.posting_id = ANY(%s)
            GROUP BY l.posting_id
            """,
            (list(posting_ids),),
        ).fetchall()
    return {pid: (requested is not None and requested > extracted) for pid, extracted, requested in rows}


def check_repeat_work(posting_ids: list[str], lookup=prior_extractions) -> dict:
    """Run the breaker on the exact set a lane is about to pay for. `lookup` is injectable for
    tests. Returns counts, the unexplained ids (capped), and `blocked`."""
    ids = list(dict.fromkeys(posting_ids))
    prior = lookup(ids)
    unexplained = [pid for pid in ids if pid in prior and not prior[pid]]
    explained = sum(1 for pid in ids if prior.get(pid))
    return {
        "selected": len(ids),
        "repeats": len(unexplained) + explained,
        "explained": explained,
        "unexplained": len(unexplained),
        "unexplained_ids": unexplained[:MAX_IDS_IN_DETAIL],
        "repeat_ids": {pid for pid in ids if pid in prior},
        "blocked": is_blocked(len(ids), len(unexplained)),
        "thresholds": {"count": REPEAT_WORK_MAX_COUNT, "share": REPEAT_WORK_MAX_SHARE},
    }


def severest(guards: list[str]) -> str:
    fired = [g for g in guards if g and g != "ok"]
    if not fired:
        return "ok"
    return min(fired, key=lambda g: GUARD_SEVERITY.index(g) if g in GUARD_SEVERITY else len(GUARD_SEVERITY))
