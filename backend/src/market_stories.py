"""Deterministic, live-data stories for the market-health conversation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from db import get_connection
from market_openings import PLOTTED_ROLE_CATEGORIES

# Year-on-year breakdowns (changes/2026-09-10-story-yoy-breakdowns.md): exactly
# two 12-month windows, one year back, windowed on raw_postings.fetched_at (the
# only date this platform can trust — same rule as the trend chart baseline).
_YEAR = timedelta(days=365)
# Classification dimensions the YoY sections break down. Whitelisted — the value
# goes straight into a GROUP BY column name, so it is never caller-supplied text.
_YOY_DIMENSIONS = ("role_category", "level", "track", "specialization")


STORY_CATALOGUE = (
    {
        "id": "market-data-briefing",
        "display_name": "What we know about the market",
        "question": "What do we currently know about the tech job market?",
        "example_phrasings": [
            "Give me an overview of the tech job market",
            "What does your job market data show?",
        ],
    },
    {
        "id": "employment-risk-overview",
        "display_name": "Employment risk across the market",
        "question": "What does layoff and hiring activity look like across the market right now?",
        "example_phrasings": [
            "Is the market seeing more layoffs or hiring?",
            "What's happening with layoffs right now?",
            "Show me employment risk",
        ],
    },
    {
        "id": "market-benchmark",
        "display_name": "Independent market benchmark",
        "question": "What does an independent market benchmark say about tech hiring demand and pay?",
        "example_phrasings": [
            "How does this compare to an outside source?",
            "What does IT Jobs Watch say?",
            "Show me an independent market benchmark",
        ],
    },
    {
        "id": "beyond-tracked-roles",
        "display_name": "Beyond Design, Product & Engineering",
        "question": "What roles exist beyond Design, Product, and Engineering?",
        "example_phrasings": [
            "What else are these companies hiring for?",
            "Show me the wider workforce breakdown",
            "What jobs aren't Design, Product, or Engineering?",
        ],
    },
)

# Employment risk story window — trailing 12 months, revised 2026-09-11 from
# an initial 90 days (changes/2026-09-11-employment-risk-12-month-window.md):
# a source's own event date can lag well behind when it actually appeared on
# a live feed (confirmed with real UK Companies House Streaming API data —
# a live-pushed case update can reference a case that itself started many
# months earlier), so a short window silently dropped real, freshly-surfaced
# events. Not the YoY 12-month *comparison* convention Story 1 uses (this is
# a single trailing window, not two windows compared) — same duration,
# different purpose. See design/market-health/data-stories.md — Story 2.
_EMPLOYMENT_RISK_WINDOW = timedelta(days=365)


def list_stories() -> dict[str, list[dict[str, Any]]]:
    """Return metadata only; story answers are always computed on demand."""
    return {"stories": [dict(story) for story in STORY_CATALOGUE]}


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _section(
    section_id: str,
    title: str,
    content: dict[str, Any],
    qualifier: str,
    *,
    ready: bool = True,
) -> dict[str, Any]:
    if ready:
        return {
            "id": section_id,
            "title": title,
            "status": "ready",
            "content": content,
            "qualifier": qualifier,
        }
    return {
        "id": section_id,
        "title": title,
        "status": "insufficient_data",
        "content": {},
        "qualifier": qualifier,
        "message": "Not enough data yet for this section.",
    }


def _rows_as_dicts(cursor) -> list[dict[str, Any]]:
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _windowed_counts(conn, dimension: str, start: datetime, end: datetime) -> dict[str, int]:
    """Distinct-posting count per value of `dimension`, for postings observed in
    [start, end). Same aggregate the admin overview uses
    (classification.get_classification_distribution), scoped to a fetched_at
    window. NULLs are excluded — a "not classified" state, not a value."""
    if dimension not in _YOY_DIMENSIONS:
        raise ValueError(f"unsupported YoY dimension: {dimension!r}")
    rows = conn.execute(
        f"""
        SELECT c.{dimension}, count(DISTINCT rp.id)
        FROM raw_postings rp
        JOIN classifications c ON c.posting_id = rp.id
        WHERE c.{dimension} IS NOT NULL
          AND rp.fetched_at >= %s AND rp.fetched_at < %s
        GROUP BY c.{dimension}
        """,
        (start, end),
    ).fetchall()
    return {value: count for value, count in rows}


def _window_dict(start: datetime, end: datetime) -> dict[str, str]:
    return {"start_date": start.date().isoformat(), "end_date": end.date().isoformat()}


def _yoy_rows(
    current: dict[str, int],
    prior: dict[str, int],
    comparison_available: bool,
    *,
    limit: int | None = None,
    exclude: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """One row per value, ordered by current-window count desc. Shares are each
    computed against their own window's total (the denominator). delta_pp is in
    percentage points, not a percent change. Prior fields are None (never
    estimated or zero-filled) when a full prior window doesn't exist yet."""
    current_total = sum(v for k, v in current.items() if k not in exclude)
    prior_total = sum(v for k, v in prior.items() if k not in exclude)
    ordered = sorted(
        (k for k in current if k not in exclude),
        key=lambda k: (-current[k], k),
    )
    if limit is not None:
        ordered = ordered[:limit]

    rows: list[dict[str, Any]] = []
    for value in ordered:
        cur_count = current[value]
        cur_share = cur_count / current_total if current_total else 0.0
        row: dict[str, Any] = {
            "value": value,
            "current_count": cur_count,
            "current_share": round(cur_share, 4),
            "prior_count": None,
            "prior_share": None,
            "delta_pp": None,
        }
        if comparison_available:
            prior_count = prior.get(value, 0)
            prior_share = prior_count / prior_total if prior_total else 0.0
            row["prior_count"] = prior_count
            row["prior_share"] = round(prior_share, 4)
            row["delta_pp"] = round((cur_share - prior_share) * 100, 1)
        rows.append(row)
    return rows


def _yoy_section(
    section_id: str,
    title: str,
    dimension: str,
    conn,
    *,
    current_window: tuple[datetime, datetime],
    prior_window: tuple[datetime, datetime],
    comparison_available: bool,
    comparison_starts_at: datetime | None,
    meaning: str,
    limit: int | None = None,
    exclude: tuple[str, ...] = (),
) -> dict[str, Any]:
    cur = _windowed_counts(conn, dimension, *current_window)
    prior = _windowed_counts(conn, dimension, *prior_window) if comparison_available else {}
    rows = _yoy_rows(cur, prior, comparison_available, limit=limit, exclude=exclude)

    cur_range = f"{current_window[0].date().isoformat()} to {current_window[1].date().isoformat()}"
    if comparison_available:
        qualifier = (
            f"{meaning} Comparing {cur_range} with the 12 months before it. "
            "Shares use each window's own classified total; the two windows are never blended."
        )
    else:
        starts = comparison_starts_at.date().isoformat() if comparison_starts_at else "later"
        qualifier = (
            f"{meaning} Showing {cur_range} only — year-on-year comparison starts {starts}, "
            "once the platform has a full prior year to compare against."
        )

    return _section(
        section_id,
        title,
        {
            "dimension": dimension,
            "current_window": _window_dict(*current_window),
            "prior_window": _window_dict(*prior_window) if comparison_available else None,
            "comparison_available": comparison_available,
            "rows": rows,
        },
        qualifier,
        ready=bool(rows),
    )


def build_market_data_briefing() -> dict[str, Any]:
    """Build the first story from the current owned-data database snapshot."""
    query_time = datetime.now().astimezone()

    with get_connection() as conn:
        coverage = conn.execute(
            """
            SELECT min(fetched_at), max(fetched_at), count(DISTINCT id)
            FROM raw_postings
            """
        ).fetchone()
        company_source = conn.execute(
            """
            SELECT count(DISTINCT company), count(DISTINCT source)
            FROM raw_postings
            """
        ).fetchone()
        sources = conn.execute(
            """
            SELECT source, count(DISTINCT id) AS posting_count
            FROM raw_postings
            WHERE source IS NOT NULL
            GROUP BY source
            ORDER BY posting_count DESC, source
            """
        ).fetchall()
        role_rows = _rows_as_dicts(conn.execute(
            """
            SELECT c.role_category, count(DISTINCT rp.id) AS posting_count
            FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            GROUP BY c.role_category
            ORDER BY posting_count DESC, c.role_category
            """
        ))
        title_rows = _rows_as_dicts(conn.execute(
            """
            SELECT c.role_category, rp.title, count(DISTINCT rp.id) AS posting_count
            FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            GROUP BY c.role_category, rp.title
            ORDER BY posting_count DESC, rp.title
            LIMIT 10
            """
        ))
        specialization_rows = _rows_as_dicts(conn.execute(
            """
            SELECT c.specialization, count(DISTINCT rp.id) AS posting_count
            FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            WHERE c.specialization IS NOT NULL
              AND c.specialization NOT IN ('unknown', '')
            GROUP BY c.specialization
            ORDER BY posting_count DESC, c.specialization
            LIMIT 10
            """
        ))
        skill_rows = _rows_as_dicts(conn.execute(
            """
            SELECT ps.skill_group, ps.requirement_level,
                   count(DISTINCT ps.posting_id) AS posting_count
            FROM posting_skills ps
            GROUP BY ps.skill_group, ps.requirement_level
            ORDER BY posting_count DESC, ps.skill_group
            LIMIT 20
            """
        ))
        requirements_coverage = conn.execute(
            """
            SELECT count(DISTINCT rp.id), count(DISTINCT pr.posting_id)
            FROM raw_postings rp
            LEFT JOIN posting_requirements pr ON pr.posting_id = rp.id
            """
        ).fetchone()
        compensation_rows = _rows_as_dicts(conn.execute(
            """
            SELECT COALESCE(salary_confidence, 'not_disclosed') AS confidence,
                   count(DISTINCT id) AS posting_count
            FROM raw_postings
            GROUP BY COALESCE(salary_confidence, 'not_disclosed')
            ORDER BY posting_count DESC, confidence
            """
        ))
        country_rows = _rows_as_dicts(conn.execute(
            """
            SELECT country, count(DISTINCT id) AS posting_count
            FROM raw_postings
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY posting_count DESC, country
            LIMIT 10
            """
        ))
        city_rows = _rows_as_dicts(conn.execute(
            """
            SELECT city, count(DISTINCT id) AS posting_count
            FROM raw_postings
            WHERE city IS NOT NULL
            GROUP BY city
            ORDER BY posting_count DESC, city
            LIMIT 10
            """
        ))

        # --- Year-on-year movement (changes/2026-09-10-story-yoy-breakdowns.md) ---
        current_window = (query_time - _YEAR, query_time)
        prior_window = (query_time - 2 * _YEAR, query_time - _YEAR)
        first_seen = coverage[0]
        comparison_available = first_seen is not None and first_seen <= current_window[0]
        comparison_starts_at = (first_seen + _YEAR) if first_seen is not None else None

        yoy_sections = [
            _yoy_section(
                "role-mix-shift", "How the role mix is shifting", "role_category", conn,
                current_window=current_window, prior_window=prior_window,
                comparison_available=comparison_available,
                comparison_starts_at=comparison_starts_at,
                meaning="Which of the tracked areas — Design, Product, Engineering — is taking a "
                        "bigger or smaller slice of new roles.",
                # Shares over the three tracked categories only, matching the trend
                # chart and the welcome's Category Share Bar. `other` / `unknown`
                # are coverage, not a market signal (see 2026-09-06 decision log).
                exclude=("unknown", "other"),
            ),
            _yoy_section(
                "seniority-shift", "How seniority is shifting", "level", conn,
                current_window=current_window, prior_window=prior_window,
                comparison_available=comparison_available,
                comparison_starts_at=comparison_starts_at,
                meaning="Whether the market is opening more junior or more senior roles than a "
                        "year ago.",
            ),
            _yoy_section(
                "track-shift", "IC vs. management", "track", conn,
                current_window=current_window, prior_window=prior_window,
                comparison_available=comparison_available,
                comparison_starts_at=comparison_starts_at,
                meaning="Whether more of the new roles are for people who lead teams or for people "
                        "who do the work directly.",
                exclude=("unknown",),
            ),
        ]

        spec_current = _windowed_counts(conn, "specialization", *current_window)
        spec_prior = _windowed_counts(conn, "specialization", *prior_window) if comparison_available else {}
        specialization_yoy_rows = _yoy_rows(
            spec_current, spec_prior, comparison_available,
            limit=10, exclude=("unknown", "other", ""),
        )

    earliest, latest, total_postings = coverage
    company_count, source_count = company_source
    classified_count = sum(row["posting_count"] for row in role_rows)
    requirements_total, requirements_extracted = requirements_coverage

    sections = [
        _section(
            "coverage-window",
            "Coverage window",
            {
                "first_captured_at": _iso(earliest),
                "latest_captured_at": _iso(latest),
            },
            "This is the platform's observation window, not the full history of the tech job market.",
            ready=earliest is not None,
        ),
        _section(
            "dataset-size",
            "Dataset size",
            {"unique_postings": total_postings},
            "Unique postings captured by the platform, not total jobs in the market.",
            ready=total_postings > 0,
        ),
        _section(
            "companies-and-sources",
            "Companies and sources",
            {
                "unique_companies": company_count,
                "source_count": source_count,
                "sources": [
                    {"source": source, "posting_count": count}
                    for source, count in sources
                ],
            },
            "Coverage reflects only tracked companies and source adapters that have contributed data.",
            ready=total_postings > 0,
        ),
        _section(
            "roles-offered",
            "What roles are being offered",
            {
                "classified_postings": classified_count,
                "role_categories": role_rows,
                "top_titles": title_rows,
                # All-time list kept for any consumer that still reads it; the
                # story now renders `top_specializations_yoy` (current 12-month
                # window, with per-item year-on-year deltas once a prior window
                # exists — changes/2026-09-10-story-yoy-breakdowns.md).
                "top_specializations": specialization_rows,
                "top_specializations_yoy": specialization_yoy_rows,
                "comparison_available": comparison_available,
            },
            "Role counts use classified postings. Unknown and other classifications remain part of the coverage picture.",
            ready=classified_count > 0,
        ),
        _section(
            "employer-mentioned-skills",
            "What employers mention",
            {
                "postings_with_extracted_requirements": requirements_extracted,
                "skills": skill_rows,
            },
            "Skill mentions are interpreted from posting text, not verified facts. Counts are distinct postings per skill and requirement level.",
            ready=bool(skill_rows),
        ),
        _section(
            "compensation-coverage",
            "Compensation coverage",
            {
                "coverage_by_confidence": compensation_rows,
                "postings_with_requirements_data": requirements_total,
            },
            "Structured and parsed compensation coverage is kept separate; this section does not estimate salary.",
            ready=bool(compensation_rows),
        ),
        _section(
            "geographic-coverage",
            "Geographic coverage",
            {"countries": country_rows, "cities": city_rows},
            "Only normalized locations are shown. Missing locations are not guessed.",
            ready=bool(country_rows or city_rows),
        ),
        *yoy_sections,
    ]

    return {
        "story_id": "market-data-briefing",
        "question": STORY_CATALOGUE[0]["question"],
        "as_of": query_time.isoformat(),
        "sections": sections,
        "provenance": {
            "sources": [
                "raw_postings",
                "classifications",
                "posting_skills",
                "posting_requirements",
            ],
            "model_used": False,
            "query_time": query_time.isoformat(),
        },
        "limitations": [
            "Coverage reflects tracked companies and source adapters only.",
            "The observation window begins when the platform first captured data.",
            "Fields not populated by the ingestion and extraction pipeline are shown as incomplete, not inferred.",
        ],
    }


def build_employment_risk_overview() -> dict[str, Any]:
    """
    Story 2 — company-independent market employment risk, built entirely from
    `employment_events`. Deliberately no join to raw_postings/classifications
    and no matched_company filter — see design/market-health/data-stories.md
    — Story 2, and changes/2026-09-11-employment-events-independent-scope.md.
    """
    from employment_events.base import SOURCE_DISPLAY_NAMES, is_real_company_name

    query_time = datetime.now().astimezone()
    window_start = query_time - _EMPLOYMENT_RISK_WINDOW

    with get_connection() as conn:
        base_where = "superseded_by IS NULL AND event_date >= %s"
        params: tuple = (window_start.date(),)

        direction_rows = conn.execute(
            f"""
            SELECT direction, count(*) AS events, COALESCE(sum(jobs_affected), 0) AS affected
            FROM employment_events
            WHERE {base_where}
            GROUP BY direction
            """,
            params,
        ).fetchall()

        # Fetch a generous candidate set, then filter out placeholder ids in
        # Python (is_real_company_name — same check used everywhere else in
        # this pipeline, not duplicated as SQL) before truncating to the
        # top 10 — see changes/2026-09-11-employment-risk-hide-placeholder-names.md.
        # A source with no company name (UK Companies House's Streaming API,
        # so far) still counts toward every other aggregate below (direction,
        # country, sector) — only this company-name-specific ranking excludes it.
        company_candidates = _rows_as_dicts(conn.execute(
            f"""
            SELECT company_raw, sum(jobs_affected) AS affected, count(*) AS events
            FROM employment_events
            WHERE {base_where} AND jobs_affected IS NOT NULL
            GROUP BY company_raw
            ORDER BY affected DESC, company_raw
            LIMIT 30
            """,
            params,
        ))
        company_rows_excluded = sum(
            1 for row in company_candidates if not is_real_company_name(row["company_raw"])
        )
        company_rows = [
            row for row in company_candidates if is_real_company_name(row["company_raw"])
        ][:10]

        # By country, split by direction — revised 2026-09-13 (World risk
        # map, changes/2026-09-13-employment-risk-world-map.md) from a
        # single combined total per country to a per-direction split, so
        # the map can show net hiring vs. net layoff, not just total
        # activity. Still not by state — see the 2026-09-11 note this
        # replaces: COALESCE(region, country) conflated US state codes and
        # country codes in one ranking, which stops being meaningful the
        # moment a second country's data exists. `region` (state-level)
        # stays a stored column, deliberately not surfaced here — deferred,
        # not dropped. No LIMIT — the map plots every country with data,
        # not a top-N (unlike the ranked-list blocks below).
        country_direction_rows = _rows_as_dicts(conn.execute(
            f"""
            SELECT country, direction, count(*) AS events,
                   COALESCE(sum(jobs_affected), 0) AS affected
            FROM employment_events
            WHERE {base_where} AND country IS NOT NULL
            GROUP BY country, direction
            ORDER BY country
            """,
            params,
        ))

        sector_rows = _rows_as_dicts(conn.execute(
            f"""
            SELECT sector, count(*) AS events, COALESCE(sum(jobs_affected), 0) AS affected
            FROM employment_events
            WHERE {base_where} AND sector IS NOT NULL
            GROUP BY sector
            ORDER BY affected DESC, sector
            LIMIT 10
            """,
            params,
        ))

        total_events_row = conn.execute(
            f"SELECT count(*), count(jobs_affected) FROM employment_events WHERE {base_where}",
            params,
        ).fetchone()
        total_events, events_with_figure = total_events_row

        sources_row = conn.execute(
            f"SELECT DISTINCT source FROM employment_events WHERE {base_where}", params,
        ).fetchall()
        sources = sorted(SOURCE_DISPLAY_NAMES.get(s, s) for (s,) in sources_row)

    direction_counts = {d: (n, a) for d, n, a in direction_rows}
    contraction_events, contraction_affected = direction_counts.get("contraction", (0, 0))
    expansion_events, _expansion_affected = direction_counts.get("expansion", (0, 0))
    direction_total_events = contraction_events + expansion_events
    contraction_share = (
        (contraction_events / direction_total_events * 100) if direction_total_events else 0.0
    )

    has_data = total_events > 0

    # Pivot (country, direction) rows into one row per country carrying both
    # totals — World risk map, changes/2026-09-13-employment-risk-world-map.md.
    # `direction` is always 'contraction' or 'expansion' (a closed set,
    # enforced at insert time by direction_for() — employment_events/base.py),
    # so no third branch is needed.
    country_totals: dict[str, dict[str, Any]] = {}
    for row in country_direction_rows:
        entry = country_totals.setdefault(row["country"], {
            "country": row["country"],
            "contraction_events": 0, "contraction_affected": 0,
            "expansion_events": 0, "expansion_affected": 0,
        })
        entry[f"{row['direction']}_events"] = row["events"]
        entry[f"{row['direction']}_affected"] = row["affected"]
    country_rows = sorted(country_totals.values(), key=lambda r: r["country"])

    sections = [
        _section(
            "employment-risk-countries",
            "Where it's happening",
            {"countries": country_rows},
            "State-level detail isn't broken out here yet — every country's events are "
            "combined into one figure regardless of which state/region within it.",
            ready=bool(country_rows),
        ),
        _section(
            "contraction-vs-expansion",
            "Contraction vs. expansion",
            {
                "contraction_roles_affected": contraction_affected,
                "contraction_share_of_events": contraction_share,
                "contraction_events": contraction_events,
                "expansion_events": expansion_events,
                "events_missing_a_roles_figure": total_events - events_with_figure,
            },
            f"Based on {total_events} reported event(s) in the last 12 months. A roles-affected "
            "figure isn't reported by every source, so the roles total may understate the "
            "true count.",
            ready=has_data,
        ),
        _section(
            "employment-risk-companies",
            "Companies with the most reported impact",
            {"companies": company_rows},
            "Company names are exactly as the source registry reported them, not normalized "
            "against the platform's own tracked-company list."
            + (
                f" {company_rows_excluded} event(s) excluded — the source reports only a "
                "company id, not a name."
                if company_rows_excluded
                else ""
            ),
            ready=bool(company_rows),
        ),
        _section(
            "employment-risk-sectors",
            "By sector",
            {"sectors": sector_rows},
            f"Only {len(sector_rows)} sector value(s) are covered — not every source reports "
            "an industry/sector for its events.",
            ready=bool(sector_rows),
        ),
    ]

    return {
        "story_id": "employment-risk-overview",
        "question": STORY_CATALOGUE[1]["question"],
        "as_of": query_time.isoformat(),
        "sections": sections,
        "provenance": {
            "sources": sources,
            "model_used": False,
            "query_time": query_time.isoformat(),
        },
        "limitations": [
            "Independent of the platform's 35 tracked job-posting companies — this reflects "
            "whatever companies the ingested employment-event registries themselves report.",
            "Not every registry sizes an event's headcount impact or names a sector — those "
            "figures reflect only the events that report them.",
            "Coverage today is limited to whichever registries are currently ingesting — see "
            "the Reasoning Panel's Sources for this response, and DATA_SOURCES.md for the "
            "full, current adapter list.",
        ],
    }


def build_market_benchmark_story() -> dict[str, Any]:
    """
    Story 3 — an independent third-party market benchmark (IT Jobs Watch),
    built entirely from market_observations/skill_associations, filtered to
    source="itjobswatch". Deliberately never joined to or compared against
    raw_postings/classifications — a separate benchmark, not a reconciliation
    (design/market-health/data-stories.md — Story 3;
    backend/specs/scraped-data-sources/api.md — "What this doesn't decide").

    Gated on is_source_usable("itjobswatch") before any query runs — the
    first real consumer of this table's data, exercising the rule
    scraped-data-sources/api.md's Business Logic already specified.
    """
    from scraping.itjobswatch import ROLE_SLUGS
    from source_licences import get_licence, is_source_usable

    query_time = datetime.now().astimezone()
    licence = get_licence("itjobswatch")

    if not is_source_usable("itjobswatch"):
        return {
            "story_id": "market-benchmark",
            "question": STORY_CATALOGUE[2]["question"],
            "as_of": query_time.isoformat(),
            "sections": [
                _section(
                    "market-benchmark-unavailable", "Independent market benchmark", {},
                    "This data source isn't currently available.", ready=False,
                ),
            ],
            "provenance": {"sources": ["itjobswatch"], "model_used": False, "query_time": query_time.isoformat()},
            "limitations": ["This source is not currently cleared for use — see source_licences.py."],
        }

    with get_connection() as conn:
        # DISTINCT ON entity_name, most recent period_end first — one row per
        # currently-tracked role, its latest observation. Mirrors
        # scraping_storage.py's own "most recent per entity" read pattern.
        observation_rows = _rows_as_dicts(conn.execute(
            """
            SELECT DISTINCT ON (entity_name)
                entity_name, vacancy_count, salary_median, salary_sample_size
            FROM market_observations
            WHERE source = %s
            ORDER BY entity_name, period_end DESC
            """,
            ("itjobswatch",),
        ))
        skill_rows = _rows_as_dicts(conn.execute(
            """
            SELECT skill_name, sum(job_count) AS job_count
            FROM skill_associations
            WHERE source = %s
            GROUP BY skill_name
            ORDER BY job_count DESC
            LIMIT 10
            """,
            ("itjobswatch",),
        ))

    tracked_role_count = len(ROLE_SLUGS)
    observed_role_count = len(observation_rows)

    demand_rows = [
        {"entity_name": r["entity_name"], "vacancy_count": r["vacancy_count"]}
        for r in observation_rows if r["vacancy_count"] is not None
    ]
    pay_rows = [
        {
            # salary_median is NUMERIC -> Decimal from psycopg; JSONResponse's
            # plain json.dumps doesn't know how to serialize Decimal (confirmed
            # via a real TestClient call against production data, not assumed)
            # -- cast to float here, same as every other numeric fact in this
            # module already comes back as a plain int/float.
            "entity_name": r["entity_name"], "salary_median": float(r["salary_median"]),
            "salary_sample_size": r["salary_sample_size"],
        }
        for r in observation_rows if r["salary_median"] is not None
    ]
    total_vacancies_tracked = sum(
        r["vacancy_count"] for r in observation_rows if r["vacancy_count"] is not None
    )
    roles_with_salary_data = sum(1 for r in observation_rows if r["salary_median"] is not None)
    salary_coverage_share = (
        (roles_with_salary_data / observed_role_count * 100) if observed_role_count else 0.0
    )

    sections = [
        _section(
            "market-benchmark-demand",
            "Demand across tracked roles",
            {"roles": demand_rows, "tracked_role_count": tracked_role_count, "observed_role_count": observed_role_count},
            f"Covers {observed_role_count} of {tracked_role_count} hand-curated roles this "
            "platform tracks on IT Jobs Watch (DATA_SOURCES.md §3b) — not the full market. A "
            "tracked role with no bar yet simply hasn't been fetched on its latest scheduled run.",
            ready=bool(demand_rows),
        ),
        _section(
            "market-benchmark-coverage",
            "Coverage and pay data availability",
            {
                "total_vacancies_tracked": total_vacancies_tracked,
                "roles_with_salary_data": roles_with_salary_data,
                "observed_role_count": observed_role_count,
                "salary_coverage_share": salary_coverage_share,
            },
            f"Based on {observed_role_count} currently-observed role(s) out of "
            f"{tracked_role_count} tracked.",
            ready=observed_role_count > 0,
        ),
        _section(
            "market-benchmark-pay",
            "Typical pay by role",
            {"roles": pay_rows},
            "Median annual salary only — the real spread (10th-90th percentile) is wider than "
            "this single figure per role suggests.",
            ready=bool(pay_rows),
        ),
        _section(
            "market-benchmark-skills",
            "Skills most associated with these roles",
            {"skills": [{"skill_name": r["skill_name"], "job_count": r["job_count"]} for r in skill_rows]},
            "Summed across the hand-curated tracked-role set, not a market-wide skill ranking.",
            ready=bool(skill_rows),
        ),
    ]

    return {
        "story_id": "market-benchmark",
        "question": STORY_CATALOGUE[2]["question"],
        "as_of": query_time.isoformat(),
        "sections": sections,
        "provenance": {
            "sources": ["itjobswatch"],
            "model_used": False,
            "query_time": query_time.isoformat(),
        },
        "limitations": [
            "Independent of this platform's own postings data — never blended or compared "
            "against it.",
            "Covers only a hand-curated set of roles, not the full market — see "
            "DATA_SOURCES.md §3b.",
            f"Licence: {licence.licence}. {licence.attribution_text}.",
        ],
        # Rendered visibly on the page itself, not only in the Reasoning Panel — the CC
        # BY-NC-SA 4.0 licence's attribution condition requires credit wherever this data
        # is shown (scraped-data-sources/api.md — Business Logic rule 6).
        "attribution_text": licence.attribution_text,
    }


def build_job_function_story() -> dict[str, Any]:
    """
    Story 4 — what real hiring looks like beyond the 3 tracked Role Categories
    (design/market-health/data-stories.md — Story 4). Built entirely from
    `classifications.job_function`, populated only for `role_category = "other"`
    rows (job-classification.md — Job Function, 2026-09-21) — never a fourth
    tracked category, never blended into the trend chart's own 3-line split.

    Real, current honesty state, not hidden: the 2026-09-21 taxonomy revision's
    reclassification backlog is still draining (changes/2026-09-21-fold-
    reprocessing-into-ingest.md) — a real share of `other` postings genuinely
    have `job_function IS NULL` right now because they haven't been reprocessed
    onto the new taxonomy version yet. Every section states this plainly as a
    coverage qualifier, per this catalogue's own "real lag, stated plainly,
    never faked as fresh" discipline.
    """
    query_time = datetime.now().astimezone()

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

        function_rows = _rows_as_dicts(conn.execute(
            """
            SELECT c.job_function, count(DISTINCT rp.id) AS posting_count
            FROM classifications c
            JOIN raw_postings rp ON rp.id = c.posting_id
            WHERE c.role_category = 'other' AND c.job_function IS NOT NULL
            GROUP BY c.job_function
            ORDER BY posting_count DESC
            """
        ))

        top_titles: list[dict[str, Any]] = []
        largest_function = function_rows[0]["job_function"] if function_rows else None
        if largest_function:
            top_titles = _rows_as_dicts(conn.execute(
                """
                SELECT rp.title, count(*) AS posting_count
                FROM classifications c
                JOIN raw_postings rp ON rp.id = c.posting_id
                WHERE c.job_function = %s
                GROUP BY rp.title
                ORDER BY posting_count DESC, rp.title
                LIMIT 10
                """,
                (largest_function,),
            ))

    not_yet_reprocessed = other_count - other_with_job_function
    reprocessing_note = (
        f" {not_yet_reprocessed} more \"other\" posting(s) haven't been reprocessed onto the "
        "current taxonomy version yet and aren't reflected below — not a gap, a real backlog "
        "still draining (see the platform's own ingestion run history)."
        if not_yet_reprocessed > 0 else ""
    )
    other_share = (other_count / total_count * 100) if total_count else 0.0

    sections = [
        _section(
            "beyond-tracked-roles-breakdown",
            "What the wider hiring picture looks like",
            {"functions": function_rows},
            f"Based on {other_with_job_function} of {other_count} postings outside Design, "
            f"Product, and Engineering that have a function assigned so far." + reprocessing_note,
            ready=bool(function_rows),
        ),
        _section(
            "beyond-tracked-roles-scale",
            "How much of all hiring this actually is",
            {
                "other_count": other_count,
                "total_count": total_count,
                "other_share": other_share,
            },
            f"{other_count} of {total_count} classified postings ({other_share:.1f}%) are "
            "outside the 3 tracked categories — the trend chart and Story 1 only ever show the "
            "tracked slice, not the full picture.",
            ready=total_count > 0,
        ),
        _section(
            "beyond-tracked-roles-top-titles",
            f"Most common titles in {largest_function or 'the largest function'}",
            {"job_function": largest_function, "titles": top_titles},
            "Real job titles, not normalized — the single largest function's own most-repeated "
            "titles, to show what it actually contains rather than just its name.",
            ready=bool(top_titles),
        ),
    ]

    return {
        "story_id": "beyond-tracked-roles",
        "question": STORY_CATALOGUE[3]["question"],
        "as_of": query_time.isoformat(),
        "sections": sections,
        "provenance": {
            "sources": ["raw_postings", "classifications"],
            "model_used": False,
            "query_time": query_time.isoformat(),
        },
        "limitations": [
            "Job Function is never a fourth tracked Role Category — it exists only to describe "
            "what's genuinely outside Design, Product, and Engineering, and never appears in "
            "the trend chart's own 3-line split.",
            "A posting's Job Function reflects the same title-only classification pass as "
            "everything else in this taxonomy — an interpretation, not a verified fact.",
            reprocessing_note.strip() or "All \"other\" postings currently have a Job Function assigned.",
        ],
    }


def get_story(story_id: str) -> dict[str, Any]:
    if story_id == "market-data-briefing":
        return build_market_data_briefing()
    if story_id == "employment-risk-overview":
        return build_employment_risk_overview()
    if story_id == "market-benchmark":
        return build_market_benchmark_story()
    if story_id == "beyond-tracked-roles":
        return build_job_function_story()
    raise KeyError(story_id)


def build_welcome() -> dict[str, Any]:
    """
    Platform inventory + one shortcut per current story-catalogue entry, for the pinned
    "About this platform" welcome. The welcome is not itself a catalogue entry — it reads
    STORY_CATALOGUE at request time, same as list_stories(), so a new story appears here
    with no change to this function. See design/market-health/data-stories.md — Relationship
    to the Welcome.
    """
    from employment_events.base import SOURCE_DISPLAY_NAMES

    query_time = datetime.now().astimezone()
    role_categories_sql = ", ".join(f"'{c}'" for c in PLOTTED_ROLE_CATEGORIES)

    with get_connection() as conn:
        coverage = conn.execute(
            """
            SELECT min(fetched_at), count(DISTINCT id), count(DISTINCT company)
            FROM raw_postings
            """
        ).fetchone()
        breakdown_rows = conn.execute(
            f"""
            SELECT c.role_category, count(DISTINCT rp.id) AS posting_count
            FROM raw_postings rp
            JOIN classifications c ON c.posting_id = rp.id
            WHERE c.role_category IN ({role_categories_sql})
            GROUP BY c.role_category
            ORDER BY posting_count DESC, c.role_category
            """
        ).fetchall()

        # Employment-risk proof — added 2026-09-13
        # (changes/2026-09-13-welcome-employment-risk-proof.md), so the
        # Hero's "layoffs... from official registries" claim is backed by a
        # real number, same discipline as the job-openings proof above.
        # superseded_by IS NULL excludes corrected/retracted records — same
        # rule the Employment Risk story itself already follows.
        employment_risk_row = conn.execute(
            """
            SELECT count(*), count(DISTINCT source), count(DISTINCT country)
            FROM employment_events
            WHERE superseded_by IS NULL
            """
        ).fetchone()
        employment_risk_sources_row = conn.execute(
            "SELECT DISTINCT source FROM employment_events WHERE superseded_by IS NULL",
        ).fetchall()

    collection_started_at, total_postings, company_count = coverage
    role_breakdown = [
        {"role_category": role_category, "postings": posting_count}
        for role_category, posting_count in breakdown_rows
    ]
    employment_events_count, employment_source_count, employment_country_count = employment_risk_row
    employment_source_names = sorted(
        SOURCE_DISPLAY_NAMES.get(s, s) for (s,) in employment_risk_sources_row
    )

    return {
        "inventory": {
            "total_postings": total_postings,
            "companies": company_count,
            "collection_started_at": _iso(collection_started_at),
            "role_categories": list(PLOTTED_ROLE_CATEGORIES),
            "role_breakdown": role_breakdown,
            "signals_available": ["skills", "compensation", "location"],
            "employment_risk": {
                "events": employment_events_count,
                "sources": employment_source_count,
                "source_names": employment_source_names,
                "countries": employment_country_count,
            },
        },
        "story_shortcuts": [
            {"id": s["id"], "display_name": s["display_name"], "question": s["question"]}
            for s in STORY_CATALOGUE
        ],
        "provenance": {
            "sources": ["raw_postings", "classifications", "employment_events"],
            "model_used": False,
            "query_time": query_time.isoformat(),
        },
        "as_of": query_time.isoformat(),
    }