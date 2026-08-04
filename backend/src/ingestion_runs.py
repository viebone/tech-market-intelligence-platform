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
    error_message: str | None = None,
) -> None:
    """Insert one IngestionRun row. Called exactly once per run, always —
    including when the run failed, so a crash still leaves a record."""
    other_rate = other_count / total_classified if total_classified else 0.0
    anomalies = detect_anomalies(terms_processed, other_rate, total_classified)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ingestion_runs
                (started_at, completed_at, status, terms_processed, total_fetched,
                 total_inserted, total_classified, cache_hits, heuristic_filtered,
                 llm_classified, other_count, other_rate, budget_reached, anomalies,
                 error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                started_at, completed_at, status, json.dumps(terms_processed), total_fetched,
                total_inserted, total_classified, cache_hits, heuristic_filtered,
                llm_classified, other_count, other_rate, budget_reached, json.dumps(anomalies),
                error_message,
            ),
        )
