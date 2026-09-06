"""Deterministic, live-data stories for the market-health conversation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from db import get_connection
from market_openings import PLOTTED_ROLE_CATEGORIES


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
)


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
                "top_specializations": specialization_rows,
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


def get_story(story_id: str) -> dict[str, Any]:
    if story_id != "market-data-briefing":
        raise KeyError(story_id)
    return build_market_data_briefing()


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