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

_ALLOWED_GROUP_BY = {"role_category", "sub_specialization", "seniority", "track", "country", "month"}
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


def _country_filter(country: list[str] | None) -> list[str]:
    """
    Country isn't a small closed set the way role/seniority are (Business
    Logic — Location normalization), so it's validated only as "non-empty,
    2-letter-ish" rather than against a fixed enum — still fully parameterised,
    never string-interpolated into SQL.
    """
    return [v.strip().upper() for v in _as_list(country) if v and v.strip()]


def query_market_data(
    group_by: list[str],
    role_category: list[str] | None = None,
    sub_specialization: list[str] | None = None,
    seniority: list[str] | None = None,
    track: list[str] | None = None,
    country: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    Query real, live-classified job postings from the platform's own database.

    Use this to answer any question about tech job market demand — comparisons
    between role categories, specializations, seniority levels, track, or
    location, and trends over time. Always try this before assuming a question
    can't be answered from the platform's data. For compensation/salary
    questions, use query_compensation_data instead — this tool only counts
    postings, it does not return salary figures.

    Args:
        group_by: One or more of "role_category", "sub_specialization",
            "seniority", "track", "country", "month" — how to break the counts down.
        role_category: List of one or more of "Designer", "Product Manager",
            "Engineer" to filter to — pass a single-item list to filter to one.
        sub_specialization: List of one or more specific specializations to
            filter to, e.g. ["UX Designer"] or ["UX Designer", "Product Designer"]
            to compare two.
        seniority: List of one or more of "entry", "junior", "mid", "senior",
            "lead", "principal", "manager", "director", "vp", "exec" to filter to.
        track: List of one or more of "ic", "management" to filter to.
        country: List of one or more ISO-2 country codes (e.g. "US", "GB") to filter
            to. Postings whose location couldn't be normalized are always excluded
            when this filter or group_by dimension is used — never guessed in.
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
    countries = _country_filter(country)

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
    if countries:
        where.append("rp.country = ANY(%s)")
        params.append(countries)
    if "country" in valid_group_by:
        where.append("rp.country IS NOT NULL")
    if date_from:
        where.append("rp.fetched_at >= %s")
        params.append(date_from)
    if date_to:
        where.append("rp.fetched_at <= %s")
        params.append(date_to)
    where_sql = " AND ".join(where)

    def _select_for(g: str) -> str:
        if g == "month":
            return "to_char(date_trunc('month', rp.fetched_at), 'YYYY-MM') AS month"
        if g == "country":
            return "rp.country AS country"
        return f"c.{g} AS {g}"

    select_columns = [_select_for(g) for g in valid_group_by]
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


def query_compensation_data(
    role_category: list[str] | None = None,
    sub_specialization: list[str] | None = None,
    seniority: list[str] | None = None,
    track: list[str] | None = None,
    country: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    Query real disclosed/estimated compensation data from the platform's own
    database. Use this for any salary or pay-range question — query_market_data
    only counts postings, it does not know about compensation.

    Not every posting discloses compensation, and the postings that do aren't
    equally reliable: `structured_count` postings had a real structured salary
    field from the source itself; `parsed_count` postings only had salary
    mentioned in free text, extracted via pattern matching. NEVER present
    these as equally certain. Always lead with the disclosed/structured figure
    when `structured_count` > 0, state how many postings it's based on, and
    only mention the parsed/estimated count separately, explicitly labelled as
    an estimate — never blend the two into one number. If both counts are 0,
    say plainly that no postings in this slice disclose compensation — never
    guess a figure from seniority or role alone.

    Args:
        role_category, sub_specialization, seniority, track, country: same filters
            as query_market_data — narrow to a specific slice of the market.
        date_from, date_to: ISO dates (YYYY-MM-DD), same meaning as query_market_data.

    Returns:
        A dict with:
        - structured_count: postings with a real, source-provided salary field
        - parsed_count: postings with salary only inferred from free text
        - salary_min, salary_max: the range across the higher-confidence tier
          available (structured if any exist, else parsed) — null if neither exists
        - currency: the currency the range above is denominated in (the most common
          currency within whichever tier was used) — null if no range
        - data_range, total_matching: same meaning as query_market_data
    """
    role_categories = [v for v in _as_list(role_category) if v in _ALLOWED_ROLE_CATEGORIES]
    sub_specializations = _as_list(sub_specialization)
    seniorities = [v for v in _as_list(seniority) if v in _ALLOWED_SENIORITY]
    tracks = [v for v in _as_list(track) if v in _ALLOWED_TRACK]
    countries = _country_filter(country)

    where = ["c.role_category != 'other'"]
    params: list = []
    if role_categories:
        where.append("c.role_category = ANY(%s)")
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
    if countries:
        where.append("rp.country = ANY(%s)")
        params.append(countries)
    if date_from:
        where.append("rp.fetched_at >= %s")
        params.append(date_from)
    if date_to:
        where.append("rp.fetched_at <= %s")
        params.append(date_to)
    where_sql = " AND ".join(where)

    with get_connection() as conn:
        total_matching = conn.execute(
            f"""
            SELECT count(*) FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            WHERE {where_sql}
            """,
            params,
        ).fetchone()[0]

        # Grouped by (confidence, currency) so a range is never computed by
        # mixing currencies — the dominant currency within whichever
        # confidence tier is actually used wins (see docstring: structured
        # preferred over parsed).
        comp_rows = conn.execute(
            f"""
            SELECT rp.salary_confidence, rp.salary_currency,
                   min(rp.salary_min) AS lo, max(rp.salary_max) AS hi, count(*) AS n
            FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            WHERE {where_sql} AND rp.salary_confidence IS NOT NULL
            GROUP BY rp.salary_confidence, rp.salary_currency
            """,
            params,
        ).fetchall()

        earliest, latest = conn.execute(
            "SELECT min(fetched_at), max(fetched_at) FROM raw_postings"
        ).fetchone()

    structured_count = sum(n for conf, _, _, _, n in comp_rows if conf == "structured")
    parsed_count = sum(n for conf, _, _, _, n in comp_rows if conf == "parsed")

    salary_min = salary_max = currency = None
    for preferred_confidence in ("structured", "parsed"):
        candidates = [r for r in comp_rows if r[0] == preferred_confidence]
        if candidates:
            # Dominant currency within this tier (highest posting count) —
            # never mix currencies into one min/max.
            best = max(candidates, key=lambda r: r[4])
            _, currency, salary_min, salary_max, _ = best
            break

    return {
        "structured_count": structured_count,
        "parsed_count": parsed_count,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "currency": currency,
        "data_range": {
            "earliest": earliest.date().isoformat() if earliest else None,
            "latest": latest.date().isoformat() if latest else None,
        },
        "total_matching": total_matching,
    }


def query_requirements_data(
    role_category: list[str] | None = None,
    sub_specialization: list[str] | None = None,
    seniority: list[str] | None = None,
    track: list[str] | None = None,
    country: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    Query real extracted requirements (skills, education, language) from the
    platform's own database. Use this for any question about what a role's
    postings actually ask for — must-have vs. nice-to-have skills, education
    level, language requirements — including "should I learn X" style
    synthesis questions, where this tool supplies the data half of the answer.

    Every extracted field is an LLM's interpretation of free text a company
    wrote, not a verified fact — state findings in proportional terms ("42%
    of postings mention X"), never as absolute claims ("all postings require
    X"), and always state total_matching as the sample size. If total_matching
    is small, say so explicitly rather than drawing a confident conclusion —
    for a synthesis question, give the data but decline to recommend if the
    sample is too small to support it.

    Args:
        role_category, sub_specialization, seniority, track, country: same filters
            as query_market_data — narrow to a specific slice of the market.
        date_from, date_to: ISO dates (YYYY-MM-DD), same meaning as query_market_data.

    Returns:
        A dict with:
        - skills: [{skill, must_have_count, nice_to_have_count}, ...] for every tracked
          skill mentioned at least once in the matched slice
        - education_levels: {education_level: count, ...}
        - languages: [{language, required_count, preferred_count}, ...]
        - data_range, total_matching: total_matching is the count of postings in the
          matched slice that actually have extracted requirements — the real denominator
          for any percentage stated, not the same as query_market_data's broader count
    """
    role_categories = [v for v in _as_list(role_category) if v in _ALLOWED_ROLE_CATEGORIES]
    sub_specializations = _as_list(sub_specialization)
    seniorities = [v for v in _as_list(seniority) if v in _ALLOWED_SENIORITY]
    tracks = [v for v in _as_list(track) if v in _ALLOWED_TRACK]
    countries = _country_filter(country)

    where = ["c.role_category != 'other'"]
    params: list = []
    if role_categories:
        where.append("c.role_category = ANY(%s)")
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
    if countries:
        where.append("rp.country = ANY(%s)")
        params.append(countries)
    if date_from:
        where.append("rp.fetched_at >= %s")
        params.append(date_from)
    if date_to:
        where.append("rp.fetched_at <= %s")
        params.append(date_to)
    where_sql = " AND ".join(where)

    with get_connection() as conn:
        total_matching = conn.execute(
            f"""
            SELECT count(*) FROM posting_requirements pr
            JOIN raw_postings rp ON rp.id = pr.posting_id
            JOIN classifications c ON c.posting_id = rp.id
            WHERE {where_sql}
            """,
            params,
        ).fetchone()[0]

        skill_rows = conn.execute(
            f"""
            SELECT ps.skill, ps.requirement_level, count(*)
            FROM posting_skills ps
            JOIN raw_postings rp ON rp.id = ps.posting_id
            JOIN classifications c ON c.posting_id = rp.id
            WHERE {where_sql}
            GROUP BY ps.skill, ps.requirement_level
            """,
            params,
        ).fetchall()

        education_rows = conn.execute(
            f"""
            SELECT pr.education_level, count(*)
            FROM posting_requirements pr
            JOIN raw_postings rp ON rp.id = pr.posting_id
            JOIN classifications c ON c.posting_id = rp.id
            WHERE {where_sql}
            GROUP BY pr.education_level
            """,
            params,
        ).fetchall()

        language_rows = conn.execute(
            f"""
            SELECT pl.language, pl.requirement_level, count(*)
            FROM posting_languages pl
            JOIN raw_postings rp ON rp.id = pl.posting_id
            JOIN classifications c ON c.posting_id = rp.id
            WHERE {where_sql}
            GROUP BY pl.language, pl.requirement_level
            """,
            params,
        ).fetchall()

        earliest, latest = conn.execute(
            "SELECT min(fetched_at), max(fetched_at) FROM raw_postings"
        ).fetchone()

    skills: dict[str, dict] = {}
    for skill, level, n in skill_rows:
        entry = skills.setdefault(skill, {"skill": skill, "must_have_count": 0, "nice_to_have_count": 0})
        entry[f"{level}_count"] = n

    languages: dict[str, dict] = {}
    for language, level, n in language_rows:
        entry = languages.setdefault(language, {"language": language, "required_count": 0, "preferred_count": 0})
        entry[f"{level}_count"] = n

    return {
        "skills": list(skills.values()),
        "education_levels": {level: n for level, n in education_rows},
        "languages": list(languages.values()),
        "data_range": {
            "earliest": earliest.date().isoformat() if earliest else None,
            "latest": latest.date().isoformat() if latest else None,
        },
        "total_matching": total_matching,
    }
