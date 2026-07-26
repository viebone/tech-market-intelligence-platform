"""
query_market_data — the read-only tool /api/chat gives the model to analyse
the platform's own data per-question, instead of a fixed pre-computed blob.
See backend/specs/market-health/api.md — Business Logic — Conversational data
sourcing.

Not raw SQL execution: group-by fields and filter values are validated against
closed sets before ever reaching a query string, since this function is called
directly by the LLM via automatic function calling (see llm/gemini.py).
"""

from db import get_connection

_ALLOWED_GROUP_BY = {"role_category", "sub_specialization", "seniority", "track", "month"}
_ALLOWED_ROLE_CATEGORIES = {"Designer", "Product Manager", "Engineer"}
_ALLOWED_SENIORITY = {
    "entry", "junior", "mid", "senior", "lead",
    "principal", "manager", "director", "vp", "exec",
}
_ALLOWED_TRACK = {"ic", "management"}


def _as_list(value) -> list:
    """
    Normalise a filter argument to a list. The model sometimes sends a single
    string ("UX Designer") and sometimes a list (["UX Designer", "Product
    Designer"]) for the same parameter, e.g. when comparing two specializations
    in one call — observed empirically, not hypothetical. Accepting both
    avoids a schema/type mismatch failing the whole tool call.
    """
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def query_market_data(
    group_by: list[str],
    role_category: list[str] | None = None,
    sub_specialization: list[str] | None = None,
    seniority: list[str] | None = None,
    track: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    Query real, live-classified job postings from the platform's own database.

    Use this to answer any question about tech job market demand — comparisons
    between role categories, specializations, seniority levels, or track, and
    trends over time. Always try this before assuming a question can't be
    answered from the platform's data.

    Args:
        group_by: One or more of "role_category", "sub_specialization",
            "seniority", "track", "month" — how to break the counts down.
        role_category: List of one or more of "Designer", "Product Manager",
            "Engineer" to filter to — pass a single-item list to filter to one.
        sub_specialization: List of one or more specific specializations to
            filter to, e.g. ["UX Designer"] or ["UX Designer", "Product Designer"]
            to compare two.
        seniority: List of one or more of "entry", "junior", "mid", "senior",
            "lead", "principal", "manager", "director", "vp", "exec" to filter to.
        track: List of one or more of "ic", "management" to filter to.
        date_from: ISO date (YYYY-MM-DD). Only postings first observed on or after this date.
        date_to: ISO date (YYYY-MM-DD). Only postings first observed on or before this date.

    Returns:
        A dict with:
        - rows: one row per unique combination of the group_by fields, each with a "count"
        - data_range: {earliest, latest} — the actual date range of data that exists in
          the database at all, regardless of filters. ALWAYS check this before concluding
          "zero postings" — if date_from/date_to falls outside data_range, the platform
          simply has no data for that period; that's a different answer than "the count is
          zero because nothing happened."
        - total_matching: total postings matching every filter (independent of group_by)
    """
    valid_group_by = [g for g in (group_by or []) if g in _ALLOWED_GROUP_BY]
    if not valid_group_by:
        valid_group_by = ["role_category"]

    role_categories = [v for v in _as_list(role_category) if v in _ALLOWED_ROLE_CATEGORIES]
    sub_specializations = _as_list(sub_specialization)
    seniorities = [v for v in _as_list(seniority) if v in _ALLOWED_SENIORITY]
    tracks = [v for v in _as_list(track) if v in _ALLOWED_TRACK]

    where = ["c.role_category != 'other'"]
    params: list = []

    if role_categories:
        where.append(f"c.role_category = ANY(%s)")
        params.append(role_categories)
    if sub_specializations:
        where.append("c.sub_specialization = ANY(%s)")
        params.append(sub_specializations)
    if seniorities:
        where.append("c.seniority = ANY(%s)")
        params.append(seniorities)
    if tracks:
        where.append("c.track = ANY(%s)")
        params.append(tracks)
    if date_from:
        where.append("rp.fetched_at >= %s")
        params.append(date_from)
    if date_to:
        where.append("rp.fetched_at <= %s")
        params.append(date_to)
    where_sql = " AND ".join(where)

    select_columns = [
        "to_char(date_trunc('month', rp.fetched_at), 'YYYY-MM') AS month" if g == "month" else f"c.{g} AS {g}"
        for g in valid_group_by
    ]
    group_by_sql = ", ".join("month" if g == "month" else g for g in valid_group_by)

    query = f"""
        SELECT {", ".join(select_columns)}, count(*) AS count
        FROM raw_postings rp
        JOIN classifications c ON c.posting_id = rp.id
        WHERE {where_sql}
        GROUP BY {group_by_sql}
        ORDER BY count DESC
    """

    with get_connection() as conn:
        cur = conn.execute(query, params)
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]

        total_matching = conn.execute(
            f"""
            SELECT count(*) FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            WHERE {where_sql}
            """,
            params,
        ).fetchone()[0]

        earliest, latest = conn.execute(
            "SELECT min(fetched_at), max(fetched_at) FROM raw_postings"
        ).fetchone()

    return {
        "rows": rows,
        "data_range": {
            "earliest": earliest.date().isoformat() if earliest else None,
            "latest": latest.date().isoformat() if latest else None,
        },
        "total_matching": total_matching,
    }
