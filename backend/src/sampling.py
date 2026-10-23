"""
The sampling decision — backend/specs/market-health/api.md — Business Logic — Sampling;
changes/2026-10-10-requirements-extraction-sampling.md; outcomes/storage-stays-bounded-as-sources-grow.md.

Every posting is still fetched, deduped, stored as a short record (every raw_postings column
except raw_response) and classified, so counts, trends, pay and coverage stay full counts. Once a
posting stored after SAMPLING_GO_LIVE is classified, ONE decision is made and never revisited:
keep its full details (posting_details) or not. For tracked roles the kept postings are exactly
the requirements sample.

Selection is rate-based (Poisson) on a fixed per-posting number `u` derived from the id:
    keep  iff  u < r,   r = min(1, K / previous month's group size)
with two monthly safeguards: from day RECALIBRATE_FROM_DAY the rate can only fall towards
K / projected size, and a hard ceiling of CEILING_MULTIPLIER × K kept per group per month.
Nothing about a posting's content or arrival order affects `u`, so inclusion is fair and
repeatable, and post-stratified estimates (sampling_estimates.py) stay unbiased.

Rule 15 steady state: on a day with nothing new this selects nothing, pays for nothing (no model
call anywhere in this module) and deletes or overwrites nothing — posting_samples and
posting_details are insert-only and raw_postings is never updated. See
backend/tests/test_sampling.py.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import logging
import re
from datetime import date, datetime, timedelta, timezone

import sampling_settings as settings
from db import get_connection

logger = logging.getLogger(__name__)

_HASH_SALT = "tmip-sample-v1:"


# ---------------------------------------------------------------------------
# Pure parts (no database) — tested directly
# ---------------------------------------------------------------------------

def hash_u(posting_id: str) -> float:
    """The posting's fixed sampling number, uniform in [0, 1). Same on every run."""
    digest = hashlib.sha256((_HASH_SALT + posting_id).encode("utf-8")).hexdigest()
    return int(digest[:16], 16) / 2**64


def month_start(moment: datetime) -> date:
    return date(moment.year, moment.month, 1)


def previous_month(month: date) -> date:
    return (month - timedelta(days=1)).replace(day=1)


def rate_for(limit: int | None, n_prev: int, n_so_far: int, day_of_month: int, days_in_month: int) -> float:
    """Inclusion rate for a group this month. 1.0 when there is no limit or the group is
    expected to stay under it. From RECALIBRATE_FROM_DAY the rate can only fall towards
    K / projected size — never rise."""
    if limit is None:
        return 1.0
    rate = 1.0 if n_prev <= limit else limit / n_prev
    if day_of_month >= settings.RECALIBRATE_FROM_DAY and n_so_far > 0:
        projected = n_so_far * days_in_month / day_of_month
        if projected > limit:
            rate = min(rate, limit / projected)
    return rate


def decide(role_category: str, u: float, rate: float, limit: int | None, kept_so_far: int) -> tuple[str, str]:
    """(decision, reason) for one classified posting."""
    if role_category in settings.ALWAYS_KEEP_ROLES:
        return "kept", "unknown_role"
    if limit is None:
        return "kept", "all_kept_role"
    if kept_so_far >= settings.CEILING_MULTIPLIER * limit:
        return "not_kept", "ceiling"
    if u < rate:
        return "kept", ("under_limit" if rate >= 1.0 else "selected")
    return "not_kept", "not_selected"


_WS_RE = re.compile(r"\s+")


def description_hash(company: str | None, title: str | None, source: str, raw_response: dict) -> str:
    """Duplicate-reuse key: exact (company, normalised title, cleaned description). Uses the
    same description extraction the requirements extractor reads, so "same hash" means "the
    model would have been sent the same text"."""
    from requirements import _extract_description  # local import: requirements is heavy

    normalised_title = _WS_RE.sub(" ", (title or "").strip().lower())
    description = _extract_description(source, raw_response or {})
    key = f"{company or ''}|{normalised_title}|{description}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Database phase
# ---------------------------------------------------------------------------

def is_sampling_live(now: datetime | None = None) -> bool:
    return (now or datetime.now(timezone.utc)) >= settings.SAMPLING_GO_LIVE


def pending_ids() -> set[str]:
    """Postings stored at or after go-live with no decision yet. Loaded once at run start so
    ingest_company() keeps their payloads in memory when they reappear on their board."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT rp.id FROM raw_postings rp
            LEFT JOIN posting_samples ps ON ps.posting_id = rp.id
            WHERE ps.posting_id IS NULL AND rp.created_at >= %s
            """,
            (settings.SAMPLING_GO_LIVE,),
        ).fetchall()
    return {r[0] for r in rows}


def _group_sizes(conn, month: date) -> dict[tuple[str, str], int]:
    """Classified postings per (role, specialization) first stored in `month`."""
    nxt = (month + timedelta(days=32)).replace(day=1)
    rows = conn.execute(
        """
        SELECT c.role_category, COALESCE(c.specialization, ''), count(*)
        FROM raw_postings rp JOIN classifications c ON c.posting_id = rp.id
        WHERE rp.created_at >= %s AND rp.created_at < %s
        GROUP BY 1, 2
        """,
        (month, nxt),
    ).fetchall()
    return {(r, s): n for r, s, n in rows}


def _kept_so_far(conn, month: date) -> dict[tuple[str, str], int]:
    rows = conn.execute(
        """
        SELECT group_role, COALESCE(group_specialization, ''), count(*)
        FROM posting_samples
        WHERE group_month = %s AND decision = 'kept' AND reason <> 'unknown_role'
        GROUP BY 1, 2
        """,
        (month,),
    ).fetchall()
    return {(r, s): n for r, s, n in rows}


def run_decision_phase(payloads: dict[str, dict], now: datetime | None = None) -> dict:
    """Decide every pending, classified posting whose payload this run holds. Returns
    {postings_kept, postings_not_kept, postings_pending} for the IngestionRun record."""
    stats = {"postings_kept": 0, "postings_not_kept": 0, "postings_pending": 0}
    now = now or datetime.now(timezone.utc)
    if not is_sampling_live(now):
        return stats

    with get_connection() as conn:
        pending = conn.execute(
            """
            SELECT rp.id, rp.created_at, rp.company, rp.title, rp.source,
                   c.role_category, c.specialization
            FROM raw_postings rp
            LEFT JOIN classifications c ON c.posting_id = rp.id
            LEFT JOIN posting_samples ps ON ps.posting_id = rp.id
            WHERE ps.posting_id IS NULL AND rp.created_at >= %s
            ORDER BY rp.created_at, rp.id
            """,
            (settings.SAMPLING_GO_LIVE,),
        ).fetchall()
        if not pending:
            return stats

        months = {month_start(row[1]) for row in pending}
        sizes = {m: _group_sizes(conn, m) for m in months}
        prev_sizes = {m: _group_sizes(conn, previous_month(m)) for m in months}
        kept = {m: _kept_so_far(conn, m) for m in months}

        sample_rows: list[tuple] = []
        detail_rows: list[tuple] = []
        stale_before = now - timedelta(days=settings.SAMPLING_PENDING_MAX_DAYS)
        for pid, created_at, company, title, source, role, specialization in pending:
            if role is None:  # not classified yet (e.g. classification budget reached) — wait
                stats["postings_pending"] += 1
                continue
            month = month_start(created_at)
            key = (role, specialization or "")
            limit = settings.limit_for(role)
            payload = payloads.get(pid)
            u = hash_u(pid)
            if payload is None:
                if created_at < stale_before:
                    sample_rows.append((pid, "not_kept", "unavailable", role, specialization, month,
                                        limit, 1.0, u, now))
                    stats["postings_not_kept"] += 1
                else:
                    stats["postings_pending"] += 1
                continue
            days_in_month = calendar.monthrange(month.year, month.month)[1]
            day_of_month = now.day if month_start(now) == month else days_in_month
            rate = rate_for(limit, prev_sizes[month].get(key, 0), sizes[month].get(key, 0),
                            day_of_month, days_in_month)
            decision, reason = decide(role, u, rate, limit, kept[month].get(key, 0))
            recorded_rate = rate if reason in ("selected", "not_selected") else 1.0
            sample_rows.append((pid, decision, reason, role, specialization, month, limit,
                                recorded_rate, u, now))
            if decision == "kept":
                if reason != "unknown_role":
                    kept[month][key] = kept[month].get(key, 0) + 1
                detail_rows.append((pid, json.dumps(payload),
                                    description_hash(company, title, source, payload), now))
                stats["postings_kept"] += 1
            else:
                stats["postings_not_kept"] += 1

        # One transaction: a posting's sample row and its kept details land together or not at all.
        with conn.cursor() as cur:
            if sample_rows:
                cur.executemany(
                    """
                    INSERT INTO posting_samples
                        (posting_id, decision, reason, group_role, group_specialization, group_month,
                         limit_at_decision, rate, hash_u, decided_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (posting_id) DO NOTHING
                    """,
                    sample_rows,
                )
            if detail_rows:
                cur.executemany(
                    """
                    INSERT INTO posting_details (posting_id, raw_response, description_hash, kept_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (posting_id) DO NOTHING
                    """,
                    detail_rows,
                )
    logger.info("sampling: kept %d, not kept %d, still pending %d",
                stats["postings_kept"], stats["postings_not_kept"], stats["postings_pending"])
    return stats


# ---------------------------------------------------------------------------
# Duplicate reuse — copy an identical posting's extraction instead of paying for it
# ---------------------------------------------------------------------------

def reuse_duplicate_extractions() -> int:
    """For kept, tracked-role postings with no requirements yet whose description_hash matches
    an already-extracted kept posting, copy that extraction (no model call). Recorded with
    reused_from and a ledger row of lane 'reused'. Returns how many postings were filled.
    Only postings with posting_details take part (both sides): legacy rows carry no stored hash.
    """
    with get_connection() as conn:
        pairs = conn.execute(
            """
            SELECT DISTINCT ON (t.posting_id) t.posting_id, s.posting_id
            FROM posting_details t
            JOIN classifications c ON c.posting_id = t.posting_id
            JOIN posting_details s ON s.description_hash = t.description_hash AND s.posting_id <> t.posting_id
            JOIN posting_requirements spr ON spr.posting_id = s.posting_id
            LEFT JOIN posting_requirements tpr ON tpr.posting_id = t.posting_id
            WHERE tpr.posting_id IS NULL AND c.role_category = ANY(%s)
            ORDER BY t.posting_id, spr.extracted_at
            """,
            (list(settings.TRACKED_ROLES),),
        ).fetchall()
        if not pairs:
            return 0
        now = datetime.now(timezone.utc)
        with conn.cursor() as cur:
            for target, source in pairs:
                cur.execute(
                    """
                    INSERT INTO posting_requirements
                        (posting_id, education_level, education_required, equivalent_experience_accepted,
                         years_experience_min, work_arrangement, responsibilities_summary,
                         other_requirements, model, extracted_at, reused_from)
                    SELECT %s, education_level, education_required, equivalent_experience_accepted,
                           years_experience_min, work_arrangement, responsibilities_summary,
                           other_requirements, model, %s, posting_id
                    FROM posting_requirements WHERE posting_id = %s
                    ON CONFLICT (posting_id) DO NOTHING
                    """,
                    (target, now, source),
                )
                cur.execute(
                    """
                    INSERT INTO posting_skills (posting_id, raw_skill, skill_group, requirement_level)
                    SELECT %s, raw_skill, skill_group, requirement_level FROM posting_skills WHERE posting_id = %s
                    ON CONFLICT (posting_id, raw_skill) DO NOTHING
                    """,
                    (target, source),
                )
                cur.execute(
                    """
                    INSERT INTO posting_languages (posting_id, language, requirement_level)
                    SELECT %s, language, requirement_level FROM posting_languages WHERE posting_id = %s
                    ON CONFLICT (posting_id, language) DO NOTHING
                    """,
                    (target, source),
                )
                cur.execute(
                    """
                    INSERT INTO requirements_extraction_ledger (posting_id, lane, model, extracted_at)
                    SELECT %s, 'reused', model, %s FROM posting_requirements WHERE posting_id = %s
                    """,
                    (target, now, source),
                )
    logger.info("sampling: reused %d identical extractions (no model call)", len(pairs))
    return len(pairs)
