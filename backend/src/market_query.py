"""
query_market_data — the read-only tool /api/chat gives the model to analyse
the platform's own data per-question, instead of a fixed pre-computed blob.
See backend/specs/market-health/api.md — Business Logic — Conversational data
sourcing.

Not raw SQL execution: group-by fields and filter values are validated against
closed sets before ever reaching a query string, since this function is called
directly by the LLM via automatic function calling (see llm/gemini.py).

Field names renamed 2026-08-11 (sub_specialization -> specialization,
seniority -> level) per the classification taxonomy redesign — see
design/market-health/job-classification.md and
backend/specs/market-health/api.md — Data Models — Classification.
"""

import sampling_estimates
from db import get_connection
from employment_events import ALL_EMPLOYMENT_EVENT_ADAPTERS
from employment_events.base import SOURCE_DISPLAY_NAMES

_ALLOWED_GROUP_BY = {"role_category", "specialization", "level", "track", "country", "month"}
_ALLOWED_ROLE_CATEGORIES = {"Designer", "Product Manager", "Engineer", "other", "unknown"}
_ALLOWED_LEVEL = {
    "entry", "junior", "mid", "senior", "lead",
    "principal", "director", "vp", "executive", "unknown",
}
_ALLOWED_TRACK = {"ic", "management", "unknown"}
_ALLOWED_WORK_ARRANGEMENT = {"onsite", "hybrid", "remote", "not_mentioned"}
_ALLOWED_EDUCATION_REQUIRED = {"required", "preferred", "not_mentioned"}


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
    Country isn't a small closed set the way role/level are (Business
    Logic — Location normalization), so it's validated only as "non-empty,
    2-letter-ish" rather than against a fixed enum — still fully parameterised,
    never string-interpolated into SQL.
    """
    return [v.strip().upper() for v in _as_list(country) if v and v.strip()]


def query_market_data(
    group_by: list[str],
    role_category: list[str] | None = None,
    specialization: list[str] | None = None,
    level: list[str] | None = None,
    track: list[str] | None = None,
    country: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    Query real, live-classified job postings from the platform's own database.

    Use this to answer any question about tech job market demand — comparisons
    between role categories, specializations, levels, track, or location, and
    trends over time. Always try this before assuming a question can't be
    answered from the platform's data. For compensation/salary questions, use
    query_compensation_data instead — this tool only counts postings, it does
    not return salary figures.

    Args:
        group_by: One or more of "role_category", "specialization", "level",
            "track", "country", "month" — how to break the counts down.
        role_category: List of one or more of "Designer", "Product Manager",
            "Engineer" to filter to — pass a single-item list to filter to one.
            "unknown" (the title alone didn't give enough evidence to classify)
            is also a valid value here if a question specifically asks about it.
        specialization: List of one or more specific specializations to
            filter to, e.g. ["UX Designer"] or ["UX Designer", "Product Designer"]
            to compare two.
        level: List of one or more of "entry", "junior", "mid", "senior",
            "lead", "principal", "director", "vp", "executive" to filter to.
        track: List of one or more of "ic", "management" to filter to.
        country: List of one or more ISO-2 country codes (e.g. "US", "GB") to filter
            to. Postings whose location couldn't be normalized are always excluded
            when this filter or group_by dimension is used — never guessed in.
        date_from: ISO date (YYYY-MM-DD). Only postings first observed on or after this date.
        date_to: ISO date (YYYY-MM-DD). Only postings first observed on or before this date.

    Note on group_by=["month"] (trend questions): each tracked company's own first-observed
    day is excluded from the counted rows, so a company newly added to tracking never reads as
    a hiring spike in whichever month it joined. This means total_matching (always unfiltered)
    can legitimately be larger than the sum of the monthly rows -- that gap is coverage growth,
    not missing data, and is safe to mention as such if asked about it. No other group_by
    combination is affected by this exclusion.

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
    specializations = _as_list(specialization)
    levels = [v for v in _as_list(level) if v in _ALLOWED_LEVEL]
    tracks = [v for v in _as_list(track) if v in _ALLOWED_TRACK]
    countries = _country_filter(country)

    # "other" is always excluded (confidently not a tracked occupation).
    # "unknown" (2026-08-11) is NOT excluded by default — it's a real,
    # plausibly-tracked population, unlike "other" — a caller filters it out
    # explicitly via role_category if a question calls for that.
    where = ["c.role_category != 'other'"]
    params: list = []

    if role_categories:
        where.append(f"c.role_category = ANY(%s)")
        params.append(role_categories)
    if specializations:
        where.append("c.specialization = ANY(%s)")
        params.append(specializations)
    if levels:
        where.append("c.level = ANY(%s)")
        params.append(levels)
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

    # Grouping by month turns this into a time-trend view, not a stock
    # snapshot -- the same "a company's first crawl is a one-time bulk load,
    # not market activity" rule the dedicated trend chart already enforces
    # (market_openings.py / backend/specs/market-health/api.md -- Collection
    # baseline) must hold here too, or a newly onboarded company's entire
    # current board reads as a demand spike in whichever month it joined.
    # Scoped to the month grouping only -- a role_category/specialization/
    # etc. breakdown with no month dimension is a stock question ("how many
    # X are tracked right now"), where every currently-open posting
    # legitimately counts, bulk-loaded or not. total_matching (below) stays
    # unfiltered by this for the same reason -- see its own docstring.
    trend_by_month = "month" in valid_group_by
    baseline_cte = (
        "WITH company_baseline AS ("
        "SELECT company, min(fetched_at::date) AS day FROM raw_postings GROUP BY company"
        ")" if trend_by_month else ""
    )
    baseline_join = (
        "JOIN company_baseline cb ON cb.company IS NOT DISTINCT FROM rp.company"
        if trend_by_month else ""
    )
    baseline_where = "AND rp.fetched_at::date > cb.day" if trend_by_month else ""

    query = f"""
        {baseline_cte}
        SELECT {", ".join(select_columns)}, count(*) AS count
        FROM raw_postings rp
        JOIN classifications c ON c.posting_id = rp.id
        {baseline_join}
        WHERE {where_sql} {baseline_where}
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
    specialization: list[str] | None = None,
    level: list[str] | None = None,
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
    guess a figure from level or role alone.

    Args:
        role_category, specialization, level, track, country: same filters
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
    specializations = _as_list(specialization)
    levels = [v for v in _as_list(level) if v in _ALLOWED_LEVEL]
    tracks = [v for v in _as_list(track) if v in _ALLOWED_TRACK]
    countries = _country_filter(country)

    where = ["c.role_category != 'other'"]
    params: list = []
    if role_categories:
        where.append("c.role_category = ANY(%s)")
        params.append(role_categories)
    if specializations:
        where.append("c.specialization = ANY(%s)")
        params.append(specializations)
    if levels:
        where.append("c.level = ANY(%s)")
        params.append(levels)
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
    specialization: list[str] | None = None,
    level: list[str] | None = None,
    track: list[str] | None = None,
    country: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    skill_group: list[str] | None = None,
    work_arrangement: list[str] | None = None,
    education_required: list[str] | None = None,
    raw_skill: list[str] | None = None,
) -> dict:
    """
    Query real extracted requirements (skills, education, years of
    experience, work arrangement, language) from the platform's own
    database. Use this for any question about what a role's postings
    actually ask for — must-have vs. nice-to-have skills, specific
    technologies, education level, years of experience, remote/onsite/hybrid
    arrangement, language requirements — including "should I learn X" style
    synthesis questions, where this tool supplies the data half of the answer.

    Every extracted field is an LLM's interpretation of free text a company
    wrote, not a verified fact — state findings in proportional terms ("42%
    of postings mention X"), never as absolute claims ("all postings require
    X"), and always state the basis from `estimate` (see below). If the sample
    is small, say so explicitly rather than drawing a confident conclusion —
    for a synthesis question, give the data but decline to recommend if the
    sample is too small to support it. Never state a compensation/salary
    figure from this tool's results — it does not extract that; use
    query_compensation_data instead.

    Args:
        role_category, specialization, level, track, country: same filters
            as query_market_data — narrow to a specific slice of the market.
        date_from, date_to: ISO dates (YYYY-MM-DD), same meaning as query_market_data.
        skill_group: List of one or more tracked skill group names (see the
            skills breakdown this tool returns for real examples) to filter to.
        work_arrangement: List of one or more of "onsite", "hybrid", "remote" to filter to.
        education_required: List of one or more of "required", "preferred" to filter to.
        raw_skill: List of one or more specific technology/practice names, e.g.
            ["Rust"] or ["Kubernetes", "Terraform"]. Filters to postings that
            mention a matching skill (case-insensitive substring). Use this for
            "is X in demand" / "should I learn X" questions instead of scanning
            every skill group's raw_skills list. When set, every returned count
            and total_matching is scoped to postings mentioning a matching skill.

    Requirements are read from a fair SAMPLE of postings (up to a fixed number per role and
    specialization per month; every design role read in full), so every figure here is an
    ESTIMATE for all postings in the slice, returned as a % share. Always state the estimate and
    its basis in the same sentence as the number, using `estimate.qualifier` (e.g. "About 42% of
    Backend Engineer postings ask for Kubernetes (estimated from 50 of 712 postings we read in
    full, give or take 13 points)"). If two shares differ by less than `estimate.margin_pts`,
    call them "about level" — never say one is more in demand. If `estimate.confidence` is
    "small_sample", give the data but no recommendation; if "too_few", there are no shares —
    say plainly that too few postings have been read yet. Under "full_small" (a handful, every
    one read) the figures are plain counts, not shares.

    Returns:
        A dict with:
        - skills: [{skill_group, share_pct, must_have_pct, nice_to_have_pct,
          raw_skills: [{raw_skill, share_pct}, ...]}, ...] sorted by share_pct — the estimated %
          of postings in the slice mentioning that group (or that specific technology).
        - education_levels_pct, work_arrangement_pct: {value: estimated %}
        - equivalent_experience_accepted_pct: estimated % accepting equivalent experience —
          check this before stating an absolute education requirement claim.
        - years_experience_min: {min, median, max} of stated minimums (median weighted).
        - languages: [{language, required_pct, preferred_pct}, ...]
        - estimate: {is_estimate, sample_n, population_n, unread_n, margin_pts, confidence,
          qualifier} — the basis every number above stands on.
        - data_range; total_matching (= estimate.sample_n, postings read; kept for one release).
        Under confidence "full_small" the *_pct keys are *_count instead.
    """
    role_categories = [v for v in _as_list(role_category) if v in _ALLOWED_ROLE_CATEGORIES]
    specializations = _as_list(specialization)
    levels = [v for v in _as_list(level) if v in _ALLOWED_LEVEL]
    tracks = [v for v in _as_list(track) if v in _ALLOWED_TRACK]
    countries = _country_filter(country)
    skill_groups = _as_list(skill_group)
    work_arrangements = [v for v in _as_list(work_arrangement) if v in _ALLOWED_WORK_ARRANGEMENT]
    education_requireds = [v for v in _as_list(education_required) if v in _ALLOWED_EDUCATION_REQUIRED]
    # Substring patterns, case-insensitive, fully parameterised (never interpolated).
    raw_skill_patterns = [f"%{v.strip()}%" for v in _as_list(raw_skill) if v and v.strip()]

    # Sampling (2026-10-23 — Business Logic — Sampling — Estimates). Two kinds of filter:
    # posting filters (rp / c) define the population every share is estimated for; requirement
    # filters (pr fields, raw_skill) narrow which READ postings count. Every figure below is a
    # post-stratified estimate from sampling_estimates — never a raw count of sampled rows.
    pop_where = ["c.role_category NOT IN ('other', 'unknown')"]
    pop_params: list = []
    if role_categories:
        pop_where.append("c.role_category = ANY(%s)")
        pop_params.append(role_categories)
    if specializations:
        pop_where.append("c.specialization = ANY(%s)")
        pop_params.append(specializations)
    if levels:
        pop_where.append("c.level = ANY(%s)")
        pop_params.append(levels)
    if tracks:
        pop_where.append("c.track = ANY(%s)")
        pop_params.append(tracks)
    if countries:
        pop_where.append("rp.country = ANY(%s)")
        pop_params.append(countries)
    if date_from:
        pop_where.append("rp.fetched_at >= %s")
        pop_params.append(date_from)
    if date_to:
        pop_where.append("rp.fetched_at <= %s")
        pop_params.append(date_to)
    req_where: list[str] = []
    req_params: list = []
    if work_arrangements:
        req_where.append("pr.work_arrangement = ANY(%s)")
        req_params.append(work_arrangements)
    if education_requireds:
        req_where.append("pr.education_required = ANY(%s)")
        req_params.append(education_requireds)
    if raw_skill_patterns:
        req_where.append(
            "EXISTS (SELECT 1 FROM posting_skills psrs "
            "WHERE psrs.posting_id = rp.id AND psrs.raw_skill ILIKE ANY(%s))"
        )
        req_params.append(raw_skill_patterns)
    pop_sql = " AND ".join(pop_where)
    where_sql = " AND ".join(pop_where + req_where)
    params = pop_params + req_params
    key = sampling_estimates.GROUP_KEY_SQL
    read_from = """
        FROM posting_requirements pr
        JOIN raw_postings rp ON rp.id = pr.posting_id
        JOIN classifications c ON c.posting_id = rp.id
    """

    def by_group(rows, value_cols: int = 0) -> dict:
        """rows of (g1, g2, g3, *values, count) → {values: {group: count}} (or {group: count})."""
        out: dict = {}
        for r in rows:
            group, values, n = (r[0], r[1], r[2]), tuple(r[3:3 + value_cols]), r[3 + value_cols]
            if value_cols == 0:
                out[group] = n
            else:
                out.setdefault(values if value_cols > 1 else values[0], {})[group] = n
        return out

    with get_connection() as conn:
        groups = sampling_estimates.population(conn, pop_sql, pop_params)
        sample_by_group = by_group(conn.execute(
            f"SELECT {key}, count(*) {read_from} WHERE {where_sql} GROUP BY 1, 2, 3", params,
        ).fetchall())
        est = sampling_estimates.Estimator(groups, sample_by_group)

        skill_group_filter_sql = ""
        skill_params = list(params)
        if skill_groups:
            skill_group_filter_sql = " AND ps.skill_group = ANY(%s)"
            skill_params = skill_params + [skill_groups]
        skill_join = "JOIN posting_skills ps ON ps.posting_id = pr.posting_id"

        # Distinct postings, not skill mentions: one posting naming three Frontend skills counts
        # once for Frontend (the old row count could push a "% of postings" past 100).
        group_any = by_group(conn.execute(
            f"SELECT {key}, ps.skill_group, count(DISTINCT ps.posting_id) {read_from} {skill_join} "
            f"WHERE {where_sql}{skill_group_filter_sql} GROUP BY 1, 2, 3, 4", skill_params,
        ).fetchall(), 1)
        group_level = by_group(conn.execute(
            f"SELECT {key}, ps.skill_group, ps.requirement_level, count(DISTINCT ps.posting_id) {read_from} "
            f"{skill_join} WHERE {where_sql}{skill_group_filter_sql} GROUP BY 1, 2, 3, 4, 5", skill_params,
        ).fetchall(), 2)
        raw_skill_counts = by_group(conn.execute(
            f"SELECT {key}, ps.skill_group, ps.raw_skill, count(DISTINCT ps.posting_id) {read_from} "
            f"{skill_join} WHERE {where_sql}{skill_group_filter_sql} GROUP BY 1, 2, 3, 4, 5", skill_params,
        ).fetchall(), 2)
        education = by_group(conn.execute(
            f"SELECT {key}, pr.education_level, count(*) {read_from} WHERE {where_sql} GROUP BY 1, 2, 3, 4",
            params,
        ).fetchall(), 1)
        equivalent = by_group(conn.execute(
            f"SELECT {key}, count(*) {read_from} WHERE {where_sql} AND pr.equivalent_experience_accepted = true "
            "GROUP BY 1, 2, 3", params,
        ).fetchall())
        arrangement = by_group(conn.execute(
            f"SELECT {key}, pr.work_arrangement, count(*) {read_from} WHERE {where_sql} GROUP BY 1, 2, 3, 4",
            params,
        ).fetchall(), 1)
        language = by_group(conn.execute(
            f"SELECT {key}, pl.language, pl.requirement_level, count(DISTINCT pl.posting_id) {read_from} "
            f"JOIN posting_languages pl ON pl.posting_id = pr.posting_id WHERE {where_sql} "
            "GROUP BY 1, 2, 3, 4, 5", params,
        ).fetchall(), 2)
        years_rows = conn.execute(
            f"SELECT {key}, pr.years_experience_min {read_from} "
            f"WHERE {where_sql} AND pr.years_experience_min IS NOT NULL", params,
        ).fetchall()
        earliest, latest = conn.execute(
            "SELECT min(fetched_at), max(fetched_at) FROM raw_postings"
        ).fetchone()

    estimate = est.estimate()
    counts_mode = estimate["confidence"] == "full_small"   # a handful, every one read: plain counts
    no_shares = estimate["confidence"] == "too_few"

    def figure(counts_by_group: dict) -> dict:
        if counts_mode:
            return {"count": sum(counts_by_group.values())}
        return {"share_pct": est.share_pct(counts_by_group)}

    skills: list[dict] = []
    if not no_shares:
        for group_name, counts in group_any.items():
            entry = {"skill_group": group_name}
            entry.update({f"{k}" if counts_mode else k: v for k, v in figure(counts).items()})
            for level_ in ("must_have", "nice_to_have"):
                level_counts = group_level.get((group_name, level_), {})
                value = figure(level_counts)
                entry[f"{level_}_count" if counts_mode else f"{level_}_pct"] = (
                    value["count"] if counts_mode else value["share_pct"] or 0.0
                )
            raw = [
                {"raw_skill": raw_name, **figure(raw_counts)}
                for (g, raw_name), raw_counts in raw_skill_counts.items() if g == group_name
            ]
            entry["raw_skills"] = sorted(raw, key=lambda r: r.get("share_pct") or r.get("count") or 0, reverse=True)
            skills.append(entry)
        skills.sort(key=lambda s: s.get("share_pct") or s.get("count") or 0, reverse=True)

    def table(by_value: dict) -> dict:
        if no_shares:
            return {}
        return {v: (figure(c)["count"] if counts_mode else figure(c)["share_pct"]) for v, c in by_value.items()}

    languages: dict[str, dict] = {}
    if not no_shares:
        for (lang, level_), counts in language.items():
            entry = languages.setdefault(lang, {"language": lang})
            suffix = "_count" if counts_mode else "_pct"
            entry[f"{level_}{suffix}"] = figure(counts)["count" if counts_mode else "share_pct"]

    # Weighted median of the stated minimum years (each read posting counts w_g times).
    years_experience_min = None
    weighted_years = sorted(
        (years, est.weights[(g1, g2, g3)]) for g1, g2, g3, years in years_rows if (g1, g2, g3) in est.weights
    )
    if weighted_years and not no_shares:
        half, running, median = sum(w for _, w in weighted_years) / 2, 0.0, None
        for years, w in weighted_years:
            running += w
            if running >= half:
                median = years
                break
        years_experience_min = {"min": weighted_years[0][0], "median": median, "max": weighted_years[-1][0]}

    unit_suffix = "_count" if counts_mode else "_pct"
    return {
        "skills": skills,
        f"education_levels{unit_suffix}": table(education),
        f"equivalent_experience_accepted{unit_suffix}": (
            None if no_shares else figure(equivalent)["count" if counts_mode else "share_pct"]
        ),
        "years_experience_min": years_experience_min,
        f"work_arrangement{unit_suffix}": table(arrangement),
        "languages": list(languages.values()),
        "data_range": {
            "earliest": earliest.date().isoformat() if earliest else None,
            "latest": latest.date().isoformat() if latest else None,
        },
        "estimate": estimate,
        # Kept one release for callers that read it; it is the number of postings READ.
        "total_matching": estimate["sample_n"],
    }


# ---------------------------------------------------------------------------
# query_employment_events_data — added 2026-09-11, Layoff Signal
# ---------------------------------------------------------------------------

def query_employment_events_data(
    company: str | None = None,
    sector: str | None = None,
    country: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    Query reported employment events (layoffs, closures, restructuring,
    bankruptcy, offshoring, expansion, hiring announcements) from external
    registries — Eurofound European Restructuring Monitor, US state WARN
    notices, UK Companies House insolvency filings.

    Use this for any question about a company's or sector's layoffs,
    closures, restructuring, bankruptcy, offshoring, expansion, or hiring
    announcements, and for "is this a pattern or a one-off" questions. This
    tool is NOT restricted to the platform's own tracked companies — it can
    report on any company an ingested registry covers. **This data is fully
    independent of the platform's own job-posting/hiring data — never join,
    compare, or cross-reference it against anything from query_market_data,
    query_compensation_data, or query_requirements_data.** Whether a pattern
    judgment is warranted is YOUR call as the assistant, not this tool's:
    only offer one when `events` has at least two entries for the queried
    company/sector; with 0 or 1, say so plainly ("too early to call a
    pattern") rather than judging. A coincidence in timing between two
    events is not evidence either caused the other.

    Args:
        company: A company name to filter to (matched case-insensitively,
            substring match against the registry's own reported spelling —
            not a fuzzy match). Omit to search across all companies (e.g.
            for a sector-only question).
        sector: An industry/sector name to filter to, matched against
            whichever events report one (mainly Eurofound ERM records) — a
            sector query is honestly scoped to only the source(s) that
            report sector; state that if it materially affects the answer.
        country: List of one or more ISO-2 country codes (e.g. "US", "GB",
            "DE") to filter to.
        date_from, date_to: ISO dates (YYYY-MM-DD), same meaning as the
            other tools.

    Returns:
        A dict with:
        - events: [{company_raw, event_date, event_type, direction,
          jobs_affected, confidence, source}, ...], oldest first. confidence
          is "confirmed" (a statutory filing / official register) or
          "reported" (compiled by the registry from public announcements) —
          never state a "reported" event with the same certainty as a
          "confirmed" one.
        - sources_checked: every employment-event registry this platform
          currently ingests from, regardless of whether any returned a row —
          use this to say "we checked X, Y, Z; none report an event for
          this company" rather than staying silent.
        - total_matching: len(events).
    """
    where = ["superseded_by IS NULL"]
    params: list = []
    if company and company.strip():
        where.append("company_raw ILIKE %s")
        params.append(f"%{company.strip()}%")
    if sector and sector.strip():
        where.append("sector ILIKE %s")
        params.append(f"%{sector.strip()}%")
    countries = _country_filter(country)
    if countries:
        where.append("country = ANY(%s)")
        params.append(countries)
    if date_from:
        where.append("event_date >= %s")
        params.append(date_from)
    if date_to:
        where.append("event_date <= %s")
        params.append(date_to)
    where_sql = " AND ".join(where)

    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT company_raw, event_date, event_type, direction,
                   jobs_affected, confidence, source
            FROM employment_events
            WHERE {where_sql}
            ORDER BY event_date ASC
            """,
            params,
        ).fetchall()

    events = [
        {
            "company_raw": r[0],
            "event_date": r[1].isoformat(),
            "event_type": r[2],
            "direction": r[3],
            "jobs_affected": r[4],
            "confidence": r[5],
            "source": SOURCE_DISPLAY_NAMES.get(r[6], r[6]),
        }
        for r in rows
    ]

    return {
        "events": events,
        "sources_checked": [a.name for a in ALL_EMPLOYMENT_EVENT_ADAPTERS],
        "total_matching": len(events),
    }


def query_market_benchmark_data(entity_name: list[str] | None = None) -> dict:
    """
    Query the independent third-party market benchmark (IT Jobs Watch),
    filtered to source="itjobswatch" — added 2026-09-18
    (changes/2026-09-18-market-benchmark-mcp-tool.md), the first function to
    read market_observations/skill_associations back out of storage. Gated
    on source_licences.is_source_usable("itjobswatch") — see
    backend/specs/scraped-data-sources/api.md's Business Logic rule 10.

    Deliberately never joined to raw_postings/classifications — this is a
    separate benchmark, not this platform's own postings data, and the two
    are never blended or compared here (design/market-health/data-stories.md
    — Story 3; scraped-data-sources/api.md — "What this doesn't decide").

    Args:
        entity_name: optional list of tracked role names to filter to (e.g.
            ["Product Owner"]). Omit for every currently-observed role.

    Returns:
        A dict with:
        - roles: [{entity_name, vacancy_count, salary_median, salary_sample_size,
          salary_p10, salary_p25, salary_p75, salary_p90, salary_unit,
          employment_type, small_sample}], most recent observation per role.
          **Percentile/unit/employment_type/small_sample added 2026-09-27**
          (changes/2026-09-26-data-story-chart-variety.md) — additive, every
          existing field unchanged. small_sample = salary_sample_size < 30
          (see backend/specs/market-health/api.md's threshold decision), computed
          here so every caller (this story, chat, MCP) reads the same flag rather
          than each re-deriving it. A role with salary_median but no percentile
          figures on record carries salary_p10..salary_p90 as None — never
          estimated or interpolated.
        - skills: [{skill_name, job_count}], top 10 by job_count summed across
          the (filtered) roles' skill associations
        - tracked_role_count, observed_role_count: coverage — how many roles
          this platform tracks on IT Jobs Watch vs. how many currently have
          an observation
        - total_matching: observed_role_count (the real denominator)
        - definitions: {key: text} from data_definitions.py — always includes
          "benchmark.salary.percentiles" when at least one role has
          salary_median (added 2026-09-27), the shared wording a human reader
          and get_market_benchmark's meta.definitions both show. Empty dict
          when no role has salary data yet.
        - usable: False if this source is not currently cleared for use
          (source_licences.is_source_usable) — roles/skills are empty in
          that case, never a stale render of previously-fetched rows
    """
    from scraping.itjobswatch import ROLE_SLUGS
    from source_licences import is_source_usable

    tracked_role_count = len(ROLE_SLUGS)

    if not is_source_usable("itjobswatch"):
        return {
            "roles": [], "skills": [], "tracked_role_count": tracked_role_count,
            "observed_role_count": 0, "total_matching": 0, "usable": False,
            "definitions": {},
        }

    entity_names = _as_list(entity_name)
    where = ["source = %s"]
    params: list = ["itjobswatch"]
    if entity_names:
        where.append("entity_name = ANY(%s)")
        params.append(entity_names)
    where_sql = " AND ".join(where)

    with get_connection() as conn:
        observation_rows = conn.execute(
            f"""
            SELECT DISTINCT ON (entity_name)
                entity_name, vacancy_count, salary_median, salary_sample_size,
                salary_p10, salary_p25, salary_p75, salary_p90, salary_unit, employment_type
            FROM market_observations
            WHERE {where_sql}
            ORDER BY entity_name, period_end DESC
            """,
            params,
        ).fetchall()

        skill_where = ["source = %s"]
        skill_params: list = ["itjobswatch"]
        if entity_names:
            skill_where.append("role_name = ANY(%s)")
            skill_params.append(entity_names)
        skill_rows = conn.execute(
            f"""
            SELECT skill_name, sum(job_count) AS job_count
            FROM skill_associations
            WHERE {' AND '.join(skill_where)}
            GROUP BY skill_name
            ORDER BY job_count DESC
            LIMIT 10
            """,
            skill_params,
        ).fetchall()

    def _num(v):
        # NUMERIC -> Decimal from psycopg; cast to float so this is
        # JSON-serializable by the plain envelope path (same real bug
        # already found and fixed for the consumer web story, Story 3 —
        # backend/specs/market-health/api.md). None stays None — never
        # coerced to 0.0 (that would misrepresent "not reported" as a value).
        return float(v) if v is not None else None

    roles = [
        {
            "entity_name": r[0], "vacancy_count": r[1],
            "salary_median": _num(r[2]),
            "salary_sample_size": r[3],
            # Percentiles/unit/employment_type — added 2026-09-27
            # (changes/2026-09-26-data-story-chart-variety.md). A role with no
            # percentile figures on record carries these as None, never an
            # invented range (backend/specs/scraped-data-sources/api.md).
            "salary_p10": _num(r[4]),
            "salary_p25": _num(r[5]),
            "salary_p75": _num(r[6]),
            "salary_p90": _num(r[7]),
            "salary_unit": r[8],
            "employment_type": r[9],
            # The 30-sample floor decided in design/market-health/data-stories.md
            # — Story 3, "Small-sample threshold". A role with no sample size at
            # all (None) is not flagged small — it's a different honesty state
            # (no salary data reported at all), handled by "range not reported".
            "small_sample": r[3] is not None and r[3] < 30,
        }
        for r in observation_rows
    ]
    skills = [{"skill_name": r[0], "job_count": r[1]} for r in skill_rows]

    from data_definitions import DEFINITIONS
    definitions = (
        {"benchmark.salary.percentiles": DEFINITIONS["benchmark.salary.percentiles"]}
        if any(r["salary_median"] is not None for r in roles)
        else {}
    )

    return {
        "roles": roles,
        "skills": skills,
        "tracked_role_count": tracked_role_count,
        "observed_role_count": len(roles),
        "total_matching": len(roles),
        "usable": True,
        "definitions": definitions,
    }


def _job_function_tiles(function_rows: list, small_share_threshold: float = 3.0) -> list[dict]:
    """
    Shapes raw {job_function, posting_count} rows into treemap-ready tiles with a computed
    `share` and a `kind` ("named" | "aggregate" | "unknown") — added 2026-09-27
    (changes/2026-09-26-data-story-chart-variety.md), for Story 4's function breakdown
    (design/market-health/data-stories.md — Story 4's tail-handling decision:
    design/visual-design.md — Treemap). A function under small_share_threshold% of the total
    merges into one "aggregate" tile (naming which functions it holds); `unknown` NEVER merges
    into it — it is always its own real tile, per this catalogue's existing "never hidden or
    folded away" rule (job-classification.md's `unknown` discipline).
    """
    total = sum(r["posting_count"] for r in function_rows) or 1
    named: list[dict] = []
    small: list[dict] = []
    unknown: dict | None = None
    for r in function_rows:
        share = round(r["posting_count"] / total * 100, 1)
        if r["job_function"] == "unknown":
            unknown = {"job_function": "unknown", "posting_count": r["posting_count"], "share": share, "kind": "unknown"}
        elif share < small_share_threshold:
            small.append(r)
        else:
            named.append({"job_function": r["job_function"], "posting_count": r["posting_count"], "share": share, "kind": "named"})
    tiles = named
    if small:
        merged_count = sum(r["posting_count"] for r in small)
        tiles.append({
            "job_function": f"{len(small)} smaller function" + ("" if len(small) == 1 else "s"),
            "posting_count": merged_count,
            "share": round(merged_count / total * 100, 1),
            "kind": "aggregate",
            "merged": [r["job_function"] for r in small],
        })
    if unknown:
        tiles.append(unknown)
    return tiles


def query_job_function_data() -> dict:
    """
    Real breakdown of postings outside the 3 tracked Role Categories
    (Designer/Product Manager/Engineer), by Job Function — added 2026-09-21
    (changes/2026-09-21-job-function-story.md). Job Function is NEVER a
    fourth tracked Role Category; this reads classifications.job_function,
    populated only for role_category = "other" rows
    (design/market-health/job-classification.md — Job Function).

    Returns:
        A dict with:
        - functions: [{job_function, posting_count}], ordered by posting_count desc
        - other_count, total_count: how many classified postings are outside
          the 3 tracked categories vs. all classified postings
        - not_yet_reprocessed: other_count minus postings that already have a
          job_function assigned — a real, current reprocessing lag from the
          2026-09-21 taxonomy revision's backlog
          (changes/2026-09-21-fold-reprocessing-into-ingest.md), stated
          plainly rather than hidden, same discipline as Story 4's own
          honesty qualifier
        - total_matching: other_count (the real denominator for `functions`)
    """
    with get_connection() as conn:
        coverage_row = conn.execute(
            """
            SELECT
                count(*) FILTER (WHERE role_category = 'other') AS other_count,
                count(*) AS total_count,
                count(*) FILTER (WHERE role_category = 'other' AND job_function IS NOT NULL) AS other_with_job_function
            FROM classifications
            """
        ).fetchone()
        other_count, total_count, other_with_job_function = coverage_row

        function_rows = conn.execute(
            """
            SELECT job_function, count(*) AS posting_count
            FROM classifications
            WHERE role_category = 'other' AND job_function IS NOT NULL
            GROUP BY job_function
            ORDER BY posting_count DESC
            """
        ).fetchall()

    return {
        "functions": _job_function_tiles([{"job_function": r[0], "posting_count": r[1]} for r in function_rows]),
        "other_count": other_count,
        "total_count": total_count,
        "not_yet_reprocessed": other_count - other_with_job_function,
        "total_matching": other_count,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Trusted external statistics (added 2026-09-25 — changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md,
# backend/specs/trusted-statistics/api.md). The single read path shared by Story 5, the chat tool and
# the MCP tool `get_trusted_statistics` — nothing queries the statistic_* tables directly.
# ─────────────────────────────────────────────────────────────────────────────

_STATISTIC_DIMENSIONS = ("total", "industry", "size_band")
_STATISTIC_PERIODS = ("latest", "year_ago", "previous_quarter")
_REQUIRED_SOURCE_FIELDS = ("publisher", "programme", "dataset_code", "series_code", "source_url", "licence", "attribution_text")


def _add_months(d, months: int):
    """First-of-month arithmetic for statistic period starts (periods start on the 1st)."""
    from datetime import date
    total = d.year * 12 + (d.month - 1) + months
    return date(total // 12, total % 12 + 1, 1)


def named_source(series: dict) -> dict:
    """
    The non-optional `source` object every returned statistic carries (trusted-statistics spec, rule 4:
    a value never travels without its source). Raises if any required field is empty — a statistic that
    cannot name its publisher, dataset, URL, licence and attribution must never be returned at all.
    """
    src = {
        "publisher": series["publisher"], "programme": series["programme"], "dataset_code": series["dataset_code"],
        "series_code": series["series_code"], "source_url": series["source_page_url"],
        "methodology_url": series["methodology_url"], "designation": series["designation"],
        "licence": series["licence"], "licence_confirmed": bool(series["licence_confirmed"]),
        "attribution_text": series["attribution_text"],
    }
    empty = [f for f in _REQUIRED_SOURCE_FIELDS if not str(src.get(f) or "").strip()]
    if empty:
        raise ValueError(f"refusing to return a statistic with no named source (empty: {empty})")
    return src


def query_trusted_statistics_data(
    dimension: str = "total",
    publisher: str | None = None,
    industry_code: str | None = None,
    size_band: str | None = None,
    period: str = "latest",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    Official statistics from trusted institutions (today: the ONS Vacancy Survey — estimated UK job
    vacancies by industry and by size of business). These are ECONOMY-WIDE OFFICIAL ESTIMATES, not this
    platform's own postings: never present them as a check on, or correction of, the platform's own
    numbers unless the user asks for a comparison — and then say the two measure different populations.
    ALWAYS name the publisher when repeating a figure.

    Args:
        dimension: "total" (all vacancies), "industry" (by SIC 2007 industry) or "size_band" (by business size).
        publisher: optional registered source key (default: every registered publisher).
        industry_code: optional SIC 2007 section letter (e.g. "J") — with dimension "industry".
        size_band: optional ONS size band code ("1-9", "10-49", "50-249", "250-2499", "2500+").
        period: "latest" (newest period only); "year_ago" or "previous_quarter" (the newest period PLUS the
            comparison period, so a caller can see the change). Ignored when date_from/date_to is given.
        date_from / date_to: optional date range over period start/end, as an ISO date string
            ("YYYY-MM-DD") or a `date` object. A range with no natural start (e.g. "2000-01-01")
            returns every period actually stored — the whole published history, not an error.

    Returns:
        {
          "statistics": [{"series": {title, dimension, dimension_type, unit, unit_scale, seasonal_adjustment,
                                     period_type, coverage_note, definition_note, source: {publisher, programme,
                                     dataset_code, series_code, source_url, methodology_url, designation, licence,
                                     licence_confirmed, attribution_text}},
                          "observations": [{period_label, period_start, period_end, value, value_status, released_on}]}],
          "sources_checked": [...], "sources_unavailable": [...],   # unavailable = a human marked the source rejected for use
          "latest_period_label": str | None, "total_matching": number of series returned, "as_of": ISO time,
          "usable": False only if EVERY candidate source is unavailable,
          "definitions": {key: text}   # shared plain-language wording (data_definitions.py) for whichever
                                        # series are returned — e.g. the ONS Vacancy Survey's rounding note,
                                        # or the "information and communication is broader than tech" note
                                        # when the "J" industry series is part of the result. {} if none apply.
        }
        `value` is as published, in the series' `unit` (ONS levels: thousands of vacancies — see unit_scale).
        An empty `statistics` with a source in `sources_checked` means "checked, nothing collected yet" —
        never "does not exist". Nothing is estimated, interpolated or filled.
    """
    from datetime import date, datetime, timezone

    import statistics_storage
    from source_licences import is_source_usable
    from trusted_stats.registry import TRUSTED_PUBLISHERS

    def _normalize_date(value, field_name: str):
        if value is None or isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"{field_name} must be an ISO date (YYYY-MM-DD), got {value!r}") from exc
        raise ValueError(f"{field_name} must be a date or an ISO date string, got {value!r}")

    date_from = _normalize_date(date_from, "date_from")
    date_to = _normalize_date(date_to, "date_to")

    if dimension not in _STATISTIC_DIMENSIONS:
        raise ValueError(f"dimension must be one of {_STATISTIC_DIMENSIONS}, got {dimension!r}")
    if period not in _STATISTIC_PERIODS:
        raise ValueError(f"period must be one of {_STATISTIC_PERIODS}, got {period!r}")
    if publisher is not None and publisher not in TRUSTED_PUBLISHERS:
        raise ValueError(f"publisher must be one of {sorted(TRUSTED_PUBLISHERS)}, got {publisher!r}")

    candidates = [publisher] if publisher else sorted(TRUSTED_PUBLISHERS)
    usable = [s for s in candidates if is_source_usable(s)]
    unavailable = [s for s in candidates if s not in usable]
    base = {"sources_checked": candidates, "sources_unavailable": unavailable,
            "as_of": datetime.now(timezone.utc).isoformat()}
    if not usable:
        return {**base, "statistics": [], "latest_period_label": None, "total_matching": 0, "usable": False, "definitions": {}}

    if date_from or date_to:
        rows = statistics_storage.fetch_observations(sources=usable, dimension_type=dimension, industry_code=industry_code,
                                                     size_band=size_band, date_from=date_from, date_to=date_to)
    else:
        latest = statistics_storage.latest_period_start(sources=usable, dimension_type=dimension)
        if latest is None:
            return {**base, "statistics": [], "latest_period_label": None, "total_matching": 0, "usable": True, "definitions": {}}
        periods = [latest]
        if period == "year_ago":
            periods.append(_add_months(latest, -12))
        elif period == "previous_quarter":
            periods.append(_add_months(latest, -3))
        rows = statistics_storage.fetch_observations(sources=usable, dimension_type=dimension, industry_code=industry_code,
                                                     size_band=size_band, periods=periods)

    definitions: dict[str, str] = {}
    if rows:
        from data_definitions import DEFINITIONS
        keys: set[str] = set()
        for r in rows:
            s = r["series"]
            if s.get("source") == "ons_vacancy_survey":
                keys.add("ons.vacancies.rounding")
                if s["dimension_type"] == "industry" and s["dimensions"].get("industry", {}).get("code") == "J":
                    keys.add("ons.industry.J.breadth")
        definitions = {k: DEFINITIONS[k] for k in sorted(keys)}

    by_series: dict[str, dict] = {}
    for r in rows:
        s, o = r["series"], r["observation"]
        entry = by_series.setdefault(s["id"], {
            "series": {
                "title": s["title"], "dimension": s["dimensions"], "dimension_type": s["dimension_type"], "unit": s["unit"],
                "unit_scale": s["unit_scale"], "seasonal_adjustment": s["seasonal_adjustment"], "period_type": s["period_type"],
                "coverage_note": s["coverage_note"], "definition_note": s["definition_note"], "source": named_source(s),
            },
            "observations": [],
        })
        entry["observations"].append({
            "period_label": o["period_label"], "period_start": o["period_start"].isoformat(), "period_end": o["period_end"].isoformat(),
            "value": o["value"], "value_status": o["value_status"], "released_on": o["released_on"].isoformat(),
        })
    statistics = list(by_series.values())
    newest = max((o for e in statistics for o in e["observations"]), key=lambda o: o["period_start"], default=None)
    return {**base, "statistics": statistics, "latest_period_label": newest["period_label"] if newest else None,
            "total_matching": len(statistics), "usable": True, "definitions": definitions}
