"""
Postgres storage for trusted external statistics (statistic_series / statistic_releases /
statistic_observations / statistics_ingestion_runs, and the statistic_observations_latest view).

Spec: backend/specs/trusted-statistics/api.md. Implements trusted_stats.base.StatisticsStorage for the
ingestion orchestrator, plus the read functions the admin dashboard and query_trusted_statistics_data use.

Rules enforced here (each one a line in the spec):
- Observations are IMMUTABLE and VINTAGE-AWARE: a changed value is a new row under the new release; the
  latest vintage is what every reader sees (the view), the full history is admin-only.
- Nothing is stored twice: an unchanged value is skipped even under a new release; a release already
  ingested is never re-stored; a byte-identical file is never re-parsed (caller checks the hash).
- One transaction per release: a crash mid-release leaves nothing half-written.
- Every row carries licence / licence_confirmed (and the series its attribution text) so the source
  travels with the data, not only in a registry.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal

from db import get_connection
from trusted_stats.base import ParsedRelease, ReleaseRef, is_due_from_last_run

# admin list sort whitelist (never interpolate a caller-supplied column name)
_SORT_COLUMNS = {
    "period_end": "o.period_end",
    "series_code": "s.series_code",
    "value": "o.value",
    "released_on": "o.released_on",
}


# ONS releases monthly; the normal maximum gap in 129 releases is 35 days (two 63-day gaps exist). Past 45 days with nothing new
# ingested is worth a human look — it is how a broken schedule or a publisher problem would otherwise go unnoticed.
RELEASE_OVERDUE_AFTER_DAYS = 45


def days_since(latest_release_date: date | None, today: date) -> int | None:
    return None if latest_release_date is None else (today - latest_release_date).days


def is_overdue(latest_release_date: date | None, today: date, after_days: int = RELEASE_OVERDUE_AFTER_DAYS) -> bool:
    """Pure (no DB), unit-tested. Never true for a source with no release yet — that is the separate "never run" state."""
    d = days_since(latest_release_date, today)
    return d is not None and d > after_days


def series_id(source: str, series_code: str) -> str:
    return f"{source}:{series_code}"


def release_id(source: str, dataset_code: str, release_date: date) -> str:
    return f"{source}:{dataset_code}:{release_date.isoformat()}"


def _same_value(stored, new: float) -> bool:
    return round(float(stored), 6) == round(float(new), 6)


def decide_vintage(stored: tuple[Decimal | float, str] | None, new_value: float, new_status: str) -> tuple[str, str | None]:
    """
    Pure (no DB) — the vintage rule from the spec, unit-tested.
    Returns (action, status_to_store): action is 'new' | 'revised' | 'unchanged'.

    - nothing stored yet                                   -> new, the file's own status
    - same value                                           -> unchanged, EXCEPT a provisional value that is
                                                              now confirmed (status leaves 'provisional') -> stored, counted as revised
    - value changed                                        -> stored; 'provisional' stays provisional (ONS still
                                                              flags it), anything else is 'revised'
    A repeated '(r)' flag on an unchanged value never creates a new row (that would be a row a month of noise).
    """
    if stored is None:
        return "new", new_status
    stored_value, stored_status = stored
    if _same_value(stored_value, new_value):
        if stored_status == "provisional" and new_status != "provisional":
            return "revised", new_status
        return "unchanged", None
    return "revised", ("provisional" if new_status == "provisional" else "revised")


class PostgresStatisticsStorage:
    # ── cadence / new-only ────────────────────────────────────────────────
    def get_last_run_at(self, source: str) -> datetime | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT max(ran_at) FROM statistics_ingestion_runs WHERE source = %s AND outcome <> 'skipped_not_due'",
                (source,),
            ).fetchone()
        return row[0] if row else None

    def release_ingested(self, source: str, dataset_code: str, release_date: date) -> bool:
        with get_connection() as conn:
            return conn.execute(
                "SELECT 1 FROM statistic_releases WHERE id = %s AND status = 'ingested'",
                (release_id(source, dataset_code, release_date),),
            ).fetchone() is not None

    def release_hash_seen(self, source: str, dataset_code: str, content_hash: str) -> bool:
        with get_connection() as conn:
            return conn.execute(
                "SELECT 1 FROM statistic_releases WHERE source = %s AND dataset_code = %s AND content_hash = %s AND status = 'ingested' LIMIT 1",
                (source, dataset_code, content_hash),
            ).fetchone() is not None

    # ── writes ────────────────────────────────────────────────────────────
    def store_release(self, *, source: str, ref: ReleaseRef, content_hash: str, parsed: ParsedRelease,
                      licence: dict, fetched_at: datetime) -> dict:
        from trusted_stats.registry import TRUSTED_PUBLISHERS
        publisher = TRUSTED_PUBLISHERS[source]
        rid = release_id(source, ref.dataset_code, ref.release_date)
        now = datetime.now(timezone.utc)
        counts = {"new": 0, "revised": 0, "unchanged": 0}
        to_insert: list[tuple] = []

        with get_connection() as conn:                       # one transaction: commits on clean exit, rolls back on error
            with conn.cursor() as cur:
                for d in parsed.series:
                    cur.execute(
                        """
                        INSERT INTO statistic_series (
                            id, source, publisher, programme, dataset_code, series_code, title, measure, unit, unit_scale,
                            seasonal_adjustment, period_type, frequency, dimensions, dimension_type, definition_note,
                            coverage_note, designation, methodology_url, source_page_url, licence, licence_confirmed,
                            attribution_text, first_seen_at, updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (id) DO UPDATE SET
                            title = EXCLUDED.title, unit = EXCLUDED.unit, unit_scale = EXCLUDED.unit_scale,
                            seasonal_adjustment = EXCLUDED.seasonal_adjustment, dimensions = EXCLUDED.dimensions,
                            definition_note = EXCLUDED.definition_note, coverage_note = EXCLUDED.coverage_note,
                            designation = EXCLUDED.designation, methodology_url = EXCLUDED.methodology_url,
                            licence = EXCLUDED.licence, licence_confirmed = EXCLUDED.licence_confirmed,
                            attribution_text = EXCLUDED.attribution_text, updated_at = EXCLUDED.updated_at
                        """,
                        (series_id(source, d.series_code), source, publisher.publisher, publisher.programme, d.dataset_code,
                         d.series_code, d.title, d.measure, d.unit, d.unit_scale, d.seasonal_adjustment, d.period_type,
                         d.frequency, json.dumps(d.dimensions), d.dimension_type, d.definition_note, d.coverage_note,
                         d.designation, d.methodology_url, d.source_page_url, licence["licence"], licence["licence_confirmed"],
                         licence["attribution_text"], now, now),
                    )
                cur.execute(
                    """
                    INSERT INTO statistic_releases (id, source, dataset_code, release_date, release_uri, file_url, file_name,
                        content_hash, fetched_at, rows_parsed, status, validation_summary)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'ingested','')
                    ON CONFLICT (id) DO UPDATE SET content_hash = EXCLUDED.content_hash, fetched_at = EXCLUDED.fetched_at,
                        rows_parsed = EXCLUDED.rows_parsed, status = 'ingested', validation_summary = ''
                    """,
                    (rid, source, ref.dataset_code, ref.release_date, ref.release_uri, ref.file_url, ref.file_name,
                     content_hash, fetched_at, len(parsed.observations)),
                )
                sids = [series_id(source, d.series_code) for d in parsed.series]
                latest = {
                    (r[0], r[1]): (r[2], r[3])
                    for r in cur.execute(
                        "SELECT series_id, period_start, value, value_status FROM statistic_observations_latest WHERE series_id = ANY(%s)",
                        (sids,),
                    ).fetchall()
                }
                for o in parsed.observations:
                    sid = series_id(source, o.series_code)
                    action, status = decide_vintage(latest.get((sid, o.period_start)), o.value, o.value_status)
                    counts["new" if action == "new" else action] += 1
                    if action == "unchanged":
                        continue
                    to_insert.append((f"{sid}:{o.period_start.isoformat()}:{ref.release_date.isoformat()}", sid, rid,
                                      o.period_start, o.period_end, o.period_label, o.value, status, o.raw_cell,
                                      ref.release_date, licence["licence"], licence["licence_confirmed"], fetched_at))
                if to_insert:
                    cur.executemany(
                        """
                        INSERT INTO statistic_observations (id, series_id, release_id, period_start, period_end, period_label,
                            value, value_status, raw_cell, released_on, licence, licence_confirmed, fetched_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        to_insert,
                    )
                cur.execute(
                    "UPDATE statistic_releases SET observations_new = %s, observations_revised = %s, observations_unchanged = %s WHERE id = %s",
                    (counts["new"], counts["revised"], counts["unchanged"], rid),
                )
        return {"release_id": rid, "rows_parsed": len(parsed.observations), "observations_new": counts["new"],
                "observations_revised": counts["revised"], "observations_unchanged": counts["unchanged"]}

    def record_release_only(self, *, source: str, ref: ReleaseRef, content_hash: str | None, status: str,
                            summary: str, fetched_at: datetime) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO statistic_releases (id, source, dataset_code, release_date, release_uri, file_url, file_name,
                    content_hash, fetched_at, status, validation_summary)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE SET content_hash = EXCLUDED.content_hash, fetched_at = EXCLUDED.fetched_at,
                    status = EXCLUDED.status, validation_summary = EXCLUDED.validation_summary
                WHERE statistic_releases.status <> 'ingested'
                """,
                (release_id(source, ref.dataset_code, ref.release_date), source, ref.dataset_code, ref.release_date,
                 ref.release_uri, ref.file_url, ref.file_name, content_hash, fetched_at, status, summary),
            )

    def record_run(self, *, source: str, ran_at: datetime, outcome: str, release_id: str | None, message: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO statistics_ingestion_runs (source, ran_at, outcome, release_id, message) VALUES (%s,%s,%s,%s,%s)",
                (source, ran_at, outcome, release_id, message),
            )


# ─────────────────────────────────────────────────────────────────────────────
# Reads — admin dashboard and the shared query function. Every reader goes through the LATEST view.
# ─────────────────────────────────────────────────────────────────────────────

_SERIES_COLUMNS = (
    "s.id, s.source, s.publisher, s.programme, s.dataset_code, s.series_code, s.title, s.measure, s.unit, s.unit_scale, "
    "s.seasonal_adjustment, s.period_type, s.frequency, s.dimensions, s.dimension_type, s.definition_note, s.coverage_note, "
    "s.designation, s.methodology_url, s.source_page_url, s.licence, s.licence_confirmed, s.attribution_text"
)
_SERIES_KEYS = [c.split(".")[1] for c in _SERIES_COLUMNS.split(", ")]


def _series_dict(row) -> dict:
    return dict(zip(_SERIES_KEYS, row))


def _obs_dict(r) -> dict:
    return {"id": r[0], "series_id": r[1], "release_id": r[2], "period_start": r[3], "period_end": r[4],
            "period_label": r[5], "value": float(r[6]), "value_status": r[7], "raw_cell": r[8], "released_on": r[9],
            "licence": r[10], "licence_confirmed": r[11], "fetched_at": r[12]}


_OBS_COLUMNS = ("o.id, o.series_id, o.release_id, o.period_start, o.period_end, o.period_label, o.value, o.value_status, "
                "o.raw_cell, o.released_on, o.licence, o.licence_confirmed, o.fetched_at")


def fetch_observations(*, sources: list[str] | None = None, dimension_type: str | None = None,
                       industry_code: str | None = None, size_band: str | None = None,
                       periods: list[date] | None = None, date_from: date | None = None, date_to: date | None = None) -> list[dict]:
    """
    Latest-vintage observations joined to their series, for the query layer. `periods` is an exact list of
    period_start dates (used for latest / year-ago / previous-quarter); date_from/date_to a range.
    Returns [{"series": {...}, "observation": {...}}]. Licence gating is the CALLER's job (market_query).
    """
    where, params = ["1=1"], []
    if sources:
        where.append("s.source = ANY(%s)"); params.append(sources)
    if dimension_type:
        where.append("s.dimension_type = %s"); params.append(dimension_type)
    if industry_code:
        where.append("s.dimensions->'industry'->>'code' = %s"); params.append(industry_code)
    if size_band:
        where.append("s.dimensions->'size_band'->>'code' = %s"); params.append(size_band)
    if periods:
        where.append("o.period_start = ANY(%s)"); params.append(periods)
    if date_from:
        where.append("o.period_start >= %s"); params.append(date_from)
    if date_to:
        where.append("o.period_end <= %s"); params.append(date_to)
    sql = (f"SELECT {_SERIES_COLUMNS}, {_OBS_COLUMNS} FROM statistic_observations_latest o "
           f"JOIN statistic_series s ON s.id = o.series_id WHERE {' AND '.join(where)} "
           f"ORDER BY s.series_code, o.period_start")
    n = len(_SERIES_KEYS)
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [{"series": _series_dict(r[:n]), "observation": _obs_dict(r[n:])} for r in rows]


def latest_period_start(*, sources: list[str] | None = None, dimension_type: str | None = None) -> date | None:
    where, params = ["1=1"], []
    if sources:
        where.append("s.source = ANY(%s)"); params.append(sources)
    if dimension_type:
        where.append("s.dimension_type = %s"); params.append(dimension_type)
    with get_connection() as conn:
        row = conn.execute(
            f"SELECT max(o.period_start) FROM statistic_observations_latest o JOIN statistic_series s ON s.id = o.series_id WHERE {' AND '.join(where)}",
            params,
        ).fetchone()
    return row[0] if row else None


def sources_with_data() -> list[str]:
    with get_connection() as conn:
        return [r[0] for r in conn.execute("SELECT DISTINCT source FROM statistic_series ORDER BY 1").fetchall()]


def list_statistics(*, source=None, dataset_code=None, dimension_type=None, series_code=None, vintages="latest",
                    sort="period_end", direction="desc", page=1, page_size=50) -> tuple[list[dict], int]:
    """Admin list. `vintages='all'` reads every stored vintage; 'latest' the view."""
    table = "statistic_observations" if vintages == "all" else "statistic_observations_latest"
    order = _SORT_COLUMNS.get(sort, "o.period_end")
    dirn = "ASC" if direction == "asc" else "DESC"
    where, params = ["1=1"], []
    for col, val in (("s.source", source), ("s.dataset_code", dataset_code), ("s.dimension_type", dimension_type), ("s.series_code", series_code)):
        if val:
            where.append(f"{col} = %s"); params.append(val)
    clause = " AND ".join(where)
    with get_connection() as conn:
        total = conn.execute(f"SELECT count(*) FROM {table} o JOIN statistic_series s ON s.id = o.series_id WHERE {clause}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT {_SERIES_COLUMNS}, {_OBS_COLUMNS} FROM {table} o JOIN statistic_series s ON s.id = o.series_id "
            f"WHERE {clause} ORDER BY {order} {dirn}, o.id LIMIT %s OFFSET %s",
            params + [page_size, (max(page, 1) - 1) * page_size],
        ).fetchall()
    n = len(_SERIES_KEYS)
    return [{"series": _series_dict(r[:n]), "observation": _obs_dict(r[n:])} for r in rows], total


def get_statistic(observation_id: str) -> dict | None:
    """One observation with its series, its release, and the full vintage history for that (series, period)."""
    with get_connection() as conn:
        row = conn.execute(f"SELECT {_SERIES_COLUMNS}, {_OBS_COLUMNS} FROM statistic_observations o JOIN statistic_series s ON s.id = o.series_id WHERE o.id = %s", (observation_id,)).fetchone()
        if row is None:
            return None
        n = len(_SERIES_KEYS)
        series, obs = _series_dict(row[:n]), _obs_dict(row[n:])
        rel = conn.execute(
            "SELECT id, source, dataset_code, release_date, release_uri, file_url, file_name, content_hash, fetched_at, rows_parsed, "
            "observations_new, observations_revised, observations_unchanged, status, validation_summary FROM statistic_releases WHERE id = %s",
            (obs["release_id"],),
        ).fetchone()
        history = conn.execute(
            "SELECT id, value, value_status, released_on, release_id FROM statistic_observations WHERE series_id = %s AND period_start = %s ORDER BY released_on DESC, created_at DESC",
            (obs["series_id"], obs["period_start"]),
        ).fetchall()
    keys = ["id", "source", "dataset_code", "release_date", "release_uri", "file_url", "file_name", "content_hash", "fetched_at",
            "rows_parsed", "observations_new", "observations_revised", "observations_unchanged", "status", "validation_summary"]
    return {"observation": obs, "series": series, "release": dict(zip(keys, rel)) if rel else None,
            "history": [{"id": h[0], "value": float(h[1]), "value_status": h[2], "released_on": h[3], "release_id": h[4]} for h in history]}


def list_statistics_sources() -> list[dict]:
    """Every REGISTERED publisher — not only ones that have produced data — with cadence, licence and collection state."""
    from source_licences import get_licence, overall_status
    from trusted_stats.registry import TRUSTED_PUBLISHERS

    now = datetime.now(timezone.utc)
    out = []
    with get_connection() as conn:
        for key, p in TRUSTED_PUBLISHERS.items():
            lic = get_licence(key)
            last = conn.execute(
                "SELECT ran_at, outcome FROM statistics_ingestion_runs WHERE source = %s AND outcome <> 'skipped_not_due' ORDER BY ran_at DESC LIMIT 1", (key,)).fetchone()
            latest_rel = conn.execute(
                "SELECT release_date FROM statistic_releases WHERE source = %s AND status = 'ingested' ORDER BY release_date DESC LIMIT 1", (key,)).fetchone()
            latest_period = conn.execute(
                "SELECT o.period_label FROM statistic_observations_latest o JOIN statistic_series s ON s.id = o.series_id WHERE s.source = %s ORDER BY o.period_start DESC LIMIT 1", (key,)).fetchone()
            counts = conn.execute(
                "SELECT (SELECT count(*) FROM statistic_series WHERE source = %s), (SELECT count(*) FROM statistic_observations o JOIN statistic_series s ON s.id = o.series_id WHERE s.source = %s)",
                (key, key)).fetchone()
            rejected = conn.execute(
                "SELECT release_date, validation_summary FROM statistic_releases WHERE source = %s AND status <> 'ingested' ORDER BY fetched_at DESC LIMIT 1", (key,)).fetchone()
            out.append({
                "source": key, "publisher": p.publisher, "publisher_type": p.publisher_type, "programme": p.programme,
                "datasets": list(p.datasets), "licence": lic.licence, "licence_status": overall_status(key),
                "licence_confirmed": lic.confirmed, "permits_commercial_use": lic.permits_commercial_use,
                "attribution_text": lic.attribution_text, "licence_url": lic.licence_url,
                "trust_bar_reviewed_on": p.trust_bar_reviewed_on, "trust_bar_reviewed_by": p.trust_bar_reviewed_by,
                "min_check_interval_hours": p.min_check_interval_hours, "release_settle_days": p.release_settle_days,
                "days_since_latest_release": days_since(latest_rel[0] if latest_rel else None, now.date()),
                "overdue": is_overdue(latest_rel[0] if latest_rel else None, now.date()),
                "overdue_after_days": RELEASE_OVERDUE_AFTER_DAYS,
                "last_run_at": last[0] if last else None, "last_run_outcome": last[1] if last else None,
                "is_due": is_due_from_last_run(last[0] if last else None, p.min_check_interval_hours, now),
                "latest_release_date": latest_rel[0] if latest_rel else None,
                "latest_period_label": latest_period[0] if latest_period else None,
                "series_count": counts[0], "observation_count": counts[1],
                "last_rejected_release": ({"release_date": rejected[0], "validation_summary": rejected[1]} if rejected else None),
            })
    return out
