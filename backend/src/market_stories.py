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

        # By country only, not state — revised 2026-09-11
        # (changes/2026-09-11-employment-risk-country-dimension.md). The
        # original COALESCE(region, country) conflated US state codes and
        # country codes in one ranking, which stops being a meaningful
        # comparison the moment a second country's data exists. `region`
        # (state-level) stays a stored column, deliberately not surfaced
        # here — deferred, not dropped.
        country_rows = _rows_as_dicts(conn.execute(
            f"""
            SELECT country, count(*) AS events, COALESCE(sum(jobs_affected), 0) AS affected
            FROM employment_events
            WHERE {base_where} AND country IS NOT NULL
            GROUP BY country
            ORDER BY affected DESC, country
            LIMIT 10
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

    sections = [
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
            "employment-risk-countries",
            "By country",
            {"countries": country_rows},
            "State-level detail isn't broken out here yet — every country's events are "
            "combined into one figure regardless of which state/region within it.",
            ready=bool(country_rows),
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


def get_story(story_id: str) -> dict[str, Any]:
    if story_id == "market-data-briefing":
        return build_market_data_briefing()
    if story_id == "employment-risk-overview":
        return build_employment_risk_overview()
    raise KeyError(story_id)


def build_welcome() -> dict[str, Any]:
    """
    Platform inventory + one shortcut per current story-catalogue entry, for the pinned
    "About this platform" welcome. The welcome is not itself a catalogue entry — it reads
    STORY_CATALOGUE at request time, same as list_stories(), so a new story appears here
    with no change to this function. See design/market-health/data-stories.md — Relationship
    to the Welcome.
    """
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

    collection_started_at, total_postings, company_count = coverage
    role_breakdown = [
        {"role_category": role_category, "postings": posting_count}
        for role_category, posting_count in breakdown_rows
    ]

    return {
        "inventory": {
            "total_postings": total_postings,
            "companies": company_count,
            "collection_started_at": _iso(collection_started_at),
            "role_categories": list(PLOTTED_ROLE_CATEGORIES),
            "role_breakdown": role_breakdown,
            "signals_available": ["skills", "compensation", "location"],
        },
        "story_shortcuts": [
            {"id": s["id"], "display_name": s["display_name"], "question": s["question"]}
            for s in STORY_CATALOGUE
        ],
        "provenance": {
            "sources": ["raw_postings", "classifications"],
            "model_used": False,
            "query_time": query_time.isoformat(),
        },
        "as_of": query_time.isoformat(),
    }