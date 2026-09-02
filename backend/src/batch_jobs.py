"""
`batch_jobs` table — persistence and reconciliation for the requirements
Batch catch-up lane.

This module is state only: it writes and reads `batch_jobs` rows and decides
which rows are stale. It never calls an LLM and never touches
`posting_requirements` — the orchestration in `ingest.py` wires this together
with `requirements.py`'s extraction path. See backend/specs/market-health/
api.md — Data Models — BatchJob and Business Logic — Requirements extraction —
Batch catch-up lane; backend/BATCH_PROCESSING.md.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from db import get_connection

logger = logging.getLogger(__name__)

ACTIVE_STATES = ["submitted", "running"]

_COLUMNS = (
    "id, provider, model, provider_job_ref, purpose, state, item_count, "
    "posting_ids, est_cost_usd, actual_cost_usd, submitted_at, completed_at, error"
)


def _row(r) -> dict:
    return {
        "id": r[0], "provider": r[1], "model": r[2], "provider_job_ref": r[3],
        "purpose": r[4], "state": r[5], "item_count": r[6],
        "posting_ids": r[7] or [], "est_cost_usd": r[8], "actual_cost_usd": r[9],
        "submitted_at": r[10], "completed_at": r[11], "error": r[12],
    }


def get_active_job() -> dict | None:
    """The one job currently in flight (`submitted` or `running`), if any.
    The lane submits at most one at a time, so this is the in-flight guard."""
    with get_connection() as conn:
        r = conn.execute(
            f"SELECT {_COLUMNS} FROM batch_jobs WHERE state = ANY(%s) ORDER BY submitted_at DESC LIMIT 1",
            (ACTIVE_STATES,),
        ).fetchone()
    return _row(r) if r else None


def get_latest_job() -> dict | None:
    """Most recent job by submission, any state — for the dashboard's
    'Last batch: ...' line."""
    with get_connection() as conn:
        r = conn.execute(
            f"SELECT {_COLUMNS} FROM batch_jobs ORDER BY submitted_at DESC LIMIT 1"
        ).fetchone()
    return _row(r) if r else None


def get_job(job_id: int) -> dict | None:
    with get_connection() as conn:
        r = conn.execute(f"SELECT {_COLUMNS} FROM batch_jobs WHERE id = %s", (job_id,)).fetchone()
    return _row(r) if r else None


def create_job(provider: str, model: str, posting_ids: list[str], est_cost_usd: float,
               purpose: str = "requirements") -> int:
    """Write the row BEFORE the provider submit call (the batch API is not
    idempotent — a crash after submit but before persist must be reconcilable,
    not a silent double charge). `provider_job_ref` stays NULL until
    set_provider_ref() is called with what submit() returned."""
    with get_connection() as conn:
        r = conn.execute(
            """
            INSERT INTO batch_jobs (provider, model, purpose, state, item_count, posting_ids, est_cost_usd, submitted_at)
            VALUES (%s, %s, %s, 'submitted', %s, %s, %s, %s)
            RETURNING id
            """,
            (provider, model, purpose, len(posting_ids), json.dumps(posting_ids),
             est_cost_usd, datetime.now(timezone.utc)),
        ).fetchone()
    return r[0]


def set_provider_ref(job_id: int, provider_job_ref: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE batch_jobs SET provider_job_ref = %s WHERE id = %s",
            (provider_job_ref, job_id),
        )


def mark_running(job_id: int) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE batch_jobs SET state = 'running' WHERE id = %s AND state = 'submitted'", (job_id,))


def mark_collected(job_id: int, actual_cost_usd: float | None = None) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE batch_jobs SET state = 'collected', completed_at = %s, actual_cost_usd = %s WHERE id = %s",
            (datetime.now(timezone.utc), actual_cost_usd, job_id),
        )


def mark_failed(job_id: int, error: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE batch_jobs SET state = 'failed', completed_at = %s, error = %s WHERE id = %s",
            (datetime.now(timezone.utc), error[:2000], job_id),
        )


def reconcile(stuck_after_hours: int) -> list[dict]:
    """Fail rows that can never make progress. Runs at the start of every
    requirements phase, before deciding whether to submit.

    - `submitted` with `provider_job_ref` still NULL (and not brand new): the
      submit() call never returned — treat as a failed submit. No provider job
      exists, so nothing was charged and the postings are still in the backlog.
    - active for longer than `stuck_after_hours`: the provider is not moving.
      Mark failed so it surfaces on the dashboard and its postings get retried.

    Returns the job rows it just failed (with `posting_ids`, `model`, `error`)
    so the caller can record per-posting failures — reconcile() only touches
    `batch_jobs`.
    """
    now = datetime.now(timezone.utc)
    failed: list[dict] = []
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT {_COLUMNS} FROM batch_jobs
            WHERE (state = 'submitted' AND provider_job_ref IS NULL AND submitted_at < %s)
               OR (state = ANY(%s) AND submitted_at < %s)
            """,
            (now - timedelta(minutes=30), ACTIVE_STATES, now - timedelta(hours=stuck_after_hours)),
        ).fetchall()
        for r in rows:
            job = _row(r)
            reason = ("submit did not complete" if job["provider_job_ref"] is None
                      else f"stuck in an active state for over {stuck_after_hours}h")
            conn.execute(
                "UPDATE batch_jobs SET state = 'failed', completed_at = %s, error = %s WHERE id = %s",
                (now, reason, job["id"]),
            )
            job["state"], job["error"] = "failed", reason
            failed.append(job)
            logger.warning("batch reconcile: job %d -> failed (%s)", job["id"], reason)
    return failed
