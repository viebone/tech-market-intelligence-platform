"""
Storage and anomaly-flagging for ingestion_runs. Makes a run's outcome
inspectable after the fact instead of existing only as ephemeral console
output. See backend/specs/market-health/api.md — Data Models — IngestionRun,
Business Logic — Scheduled ingestion agent.
"""

from __future__ import annotations

import json
from datetime import datetime

from db import get_connection

# Thresholds and lookback window match backend/specs/market-health/api.md exactly.
ANOMALY_LOOKBACK = 5
OTHER_RATE_RELATIVE_THRESHOLD = 0.5
OTHER_RATE_ABSOLUTE_THRESHOLD = 0.15


def get_recent_runs(limit: int = ANOMALY_LOOKBACK) -> list[dict]:
    """Most recent completed (success or partial) runs, most recent first."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT terms_processed, other_rate
            FROM ingestion_runs
            WHERE status IN ('success', 'partial')
            ORDER BY started_at DESC
            LIMIT %s
            """,
            (limit,),
        ).fetchall()
    return [{"terms_processed": r[0], "other_rate": r[1]} for r in rows]


def detect_anomalies(terms_processed: list[dict], other_rate: float, total_classified: int) -> list[str]:
    """
    Compare this run against recent history. Never flags anything until there's
    enough history to have a baseline — a company legitimately returning 0 once,
    or the very first few runs' other_rate, aren't anomalies, they're just data.

    terms_processed entries are `{"source", "company", "fetched", "inserted",
    "error"}` since the 2026-08-03 multi-source change (previously `{"term",
    ...}`). Legacy pre-2026-08-03 runs in `recent` still carry the old shape —
    `.get("source")`/`.get("company")` simply return None for those, so they
    never match a current (source, company) pair and are silently excluded
    from the comparison rather than raising, per
    backend/specs/market-health/api.md — Data Models — IngestionRun.
    """
    anomalies: list[str] = []
    recent = get_recent_runs()
    if not recent:
        return anomalies

    for stat in terms_processed:
        source, company, fetched = stat.get("source"), stat.get("company"), stat.get("fetched", 0)
        if fetched > 0 or company is None:
            continue
        had_results_before = any(
            any(
                rt.get("source") == source and rt.get("company") == company and rt.get("fetched", 0) > 0
                for rt in run["terms_processed"]
            )
            for run in recent
        )
        if had_results_before:
            anomalies.append(
                f'"{source}/{company}" returned 0 postings this run, despite returning '
                f"results in at least one of the last {len(recent)} runs."
            )

    if len(recent) >= ANOMALY_LOOKBACK and total_classified > 0:
        trailing_avg = sum(r["other_rate"] for r in recent) / len(recent)
        absolute_dev = abs(other_rate - trailing_avg)
        relative_dev = (absolute_dev / trailing_avg) if trailing_avg > 0 else (1.0 if other_rate > 0 else 0.0)
        if relative_dev > OTHER_RATE_RELATIVE_THRESHOLD and absolute_dev > OTHER_RATE_ABSOLUTE_THRESHOLD:
            anomalies.append(
                f'"other" rate this run ({other_rate:.0%}) deviates significantly from the '
                f"trailing {len(recent)}-run average ({trailing_avg:.0%})."
            )

    return anomalies


def get_requests_used_today() -> int:
    """
    Sum of llm_requests_used across every run started today (UTC calendar
    day) — feeds classify_postings()'s already_used_today parameter so a
    second same-day run sees a reduced (or zero) remaining budget instead of
    a fresh MAX_BATCHES_PER_RUN allowance. UTC calendar day is a deliberately
    conservative proxy for Gemini's actual (undocumented) quota reset time —
    see backend/specs/market-health/api.md — Business Logic — Classification
    — Cross-run daily budget.
    """
    with get_connection() as conn:
        total = conn.execute(
            """
            SELECT COALESCE(SUM(llm_requests_used), 0)
            FROM ingestion_runs
            WHERE started_at::date = (now() AT TIME ZONE 'UTC')::date
            """
        ).fetchone()[0]
    return total


def get_requirements_requests_used_today() -> int:
    """
    Same purpose and mechanism as get_requests_used_today(), scoped to
    requirements_requests_used instead — this pipeline's own, separate daily
    budget (Business Logic — Requirements extraction). Deliberately not
    combined with the classification query: the two budgets must stay
    independently reasoned about, not summed together.
    """
    with get_connection() as conn:
        total = conn.execute(
            """
            SELECT COALESCE(SUM(requirements_requests_used), 0)
            FROM ingestion_runs
            WHERE started_at::date = (now() AT TIME ZONE 'UTC')::date
            """
        ).fetchone()[0]
    return total


def record_run(
    started_at: datetime,
    completed_at: datetime | None,
    status: str,
    terms_processed: list[dict],
    total_fetched: int = 0,
    total_inserted: int = 0,
    total_classified: int = 0,
    cache_hits: int = 0,
    heuristic_filtered: int = 0,
    llm_classified: int = 0,
    other_count: int = 0,
    budget_reached: bool = False,
    llm_requests_used: int = 0,
    requirements_extracted: int = 0,
    requirements_requests_used: int = 0,
    requirements_budget_reached: bool = False,
    error_message: str | None = None,
) -> int:
    """Insert one IngestionRun row. Called exactly once per run, always —
    including when the run failed, so a crash still leaves a record.

    Returns the new row's id (added 2026-08-16 for the pipeline-visibility
    admin dashboard — backend/specs/pipeline-visibility/api.md). This run's
    ingestion_runs row is only written here, at the *end* of the run, well
    after raw_postings.insert_new_postings() already ran during the fetch
    phase — so raw_postings.ingestion_run_id can't be set at insert time, it
    has to be backfilled afterward. See raw_postings.attach_ingestion_run(),
    called by ingest.py's run() right after this returns."""
    other_rate = other_count / total_classified if total_classified else 0.0
    anomalies = detect_anomalies(terms_processed, other_rate, total_classified)

    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO ingestion_runs
                (started_at, completed_at, status, terms_processed, total_fetched,
                 total_inserted, total_classified, cache_hits, heuristic_filtered,
                 llm_classified, other_count, other_rate, budget_reached,
                 llm_requests_used, requirements_extracted, requirements_requests_used,
                 requirements_budget_reached, anomalies, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                started_at, completed_at, status, json.dumps(terms_processed), total_fetched,
                total_inserted, total_classified, cache_hits, heuristic_filtered,
                llm_classified, other_count, other_rate, budget_reached,
                llm_requests_used, requirements_extracted, requirements_requests_used,
                requirements_budget_reached, json.dumps(anomalies), error_message,
            ),
        ).fetchone()
    return row[0]


def list_runs(page: int = 1, page_size: int = 25) -> dict:
    """Paginated run history, most recent first — backend/specs/pipeline-visibility/api.md
    GET /admin/runs. Read-only; page/page_size are trusted ints from admin_main.py's
    own query-param coercion, not raw user SQL."""
    offset = (page - 1) * page_size
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM ingestion_runs").fetchone()[0]
        rows = conn.execute(
            """
            SELECT id, started_at, completed_at, status, total_fetched, total_inserted,
                   total_classified, requirements_extracted, budget_reached, other_rate
            FROM ingestion_runs
            ORDER BY started_at DESC
            LIMIT %s OFFSET %s
            """,
            (page_size, offset),
        ).fetchall()
    runs = [
        {
            "id": r[0], "started_at": r[1], "completed_at": r[2], "status": r[3],
            "total_fetched": r[4], "total_inserted": r[5], "total_classified": r[6],
            "requirements_extracted": r[7], "budget_reached": r[8], "other_rate": r[9],
        }
        for r in rows
    ]
    return {"runs": runs, "total": total, "page": page, "page_size": page_size}


def get_run(run_id: int) -> dict | None:
    """Full detail for one run, including terms_processed — backend/specs/
    pipeline-visibility/api.md GET /admin/runs/{run_id}. None if no such run."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, started_at, completed_at, status, terms_processed, total_fetched,
                   total_inserted, total_classified, cache_hits, heuristic_filtered,
                   llm_classified, other_count, other_rate, budget_reached,
                   llm_requests_used, requirements_extracted, requirements_requests_used,
                   requirements_budget_reached, anomalies, error_message
            FROM ingestion_runs WHERE id = %s
            """,
            (run_id,),
        ).fetchone()
    if row is None:
        return None
    return {
        "id": row[0], "started_at": row[1], "completed_at": row[2], "status": row[3],
        "terms_processed": row[4], "total_fetched": row[5], "total_inserted": row[6],
        "total_classified": row[7], "cache_hits": row[8], "heuristic_filtered": row[9],
        "llm_classified": row[10], "other_count": row[11], "other_rate": row[12],
        "budget_reached": row[13], "llm_requests_used": row[14],
        "requirements_extracted": row[15], "requirements_requests_used": row[16],
        "requirements_budget_reached": row[17], "anomalies": row[18], "error_message": row[19],
    }
