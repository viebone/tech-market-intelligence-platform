"""
The six MCP tools' actual data shaping — thin wrappers around market_query.py's
already-shipped, already-trusted functions. See backend/specs/mcp-access/api.md
— MCP Tools and "Why this reuses market_query.py, not new query logic".

Deliberately pure / auth-free: these functions take only the parameters a
calling AI would supply and return an envelope dict. Authentication, scope
enforcement, plan enforcement, and rate limiting all happen one layer up, in
server.py — kept separate so these functions are directly unit-testable
without a fake token or database connection standing in for auth machinery.

Each function's own docstring is written for the calling AI (this is what
an MCP tool's description actually is) — mirrors the style market_query.py's
functions already use for /api/chat's function-calling, since that's the
same audience (a model deciding whether and how to call this).
"""

from __future__ import annotations

import industries
from employment_events.base import SOURCE_DISPLAY_NAMES
from mcp_access.envelope import build_envelope, time_window_label
from market_query import (
    query_compensation_data,
    query_employment_events_data,
    query_market_data,
    query_requirements_data,
)

# Which scope each tool requires. get_taxonomy needs none (see taxonomy.py)
# and isn't listed here.
TOOL_SCOPES: dict[str, str] = {
    "get_job_demand": "jobs.read",
    "get_skill_demand": "jobs.read",
    "get_salary_stats": "compensation.read",
    "get_employment_risk": "companies.read",
    "list_tracked_companies": "companies.read",
}

# Tools that additionally require the Premium plan, regardless of scope.
PREMIUM_ONLY_TOOLS: frozenset[str] = frozenset({"get_salary_stats"})


def _scope_description(scope: dict) -> dict:
    """Drop None-valued filters from the envelope's `scope` field — but keep
    every key present (Response envelope: 'including ones the caller left
    as no filter, stated as null, not omitted') rather than actually
    omitting them. This just documents that intent at the call site."""
    return scope


def get_job_demand(
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
    Job demand — live-classified job posting counts, broken down by any of
    role_category / specialization / level / track / country / month. Use
    this for demand comparisons and trends. For salary, use get_salary_stats.
    For skills/education/languages, use get_skill_demand.
    """
    result = query_market_data(
        group_by=group_by, role_category=role_category, specialization=specialization,
        level=level, track=track, country=country, date_from=date_from, date_to=date_to,
    )
    return build_envelope(
        {"rows": result["rows"]},
        unit="count of live job postings first observed by this platform's ingestion",
        scope=_scope_description({
            "group_by": group_by, "role_category": role_category, "specialization": specialization,
            "level": level, "track": track, "country": country,
        }),
        time_window=time_window_label(result["data_range"]["earliest"], result["data_range"]["latest"]),
        source="Company job boards on Greenhouse, Lever, and Ashby — classified by this platform",
        total_matching=result["total_matching"],
    )


def get_salary_stats(
    role_category: list[str] | None = None,
    specialization: list[str] | None = None,
    level: list[str] | None = None,
    track: list[str] | None = None,
    country: list[str] | None = None,
) -> dict:
    """
    Salary/compensation statistics for a slice of the market. Premium plan
    only. structured_count/parsed_count tell you how reliable the range is —
    always caveat a parsed-only figure as an estimate, never present it with
    the same confidence as a structured one.
    """
    result = query_compensation_data(
        role_category=role_category, specialization=specialization, level=level,
        track=track, country=country,
    )
    currency = result["currency"] or "unknown currency"
    return build_envelope(
        {
            "structured_count": result["structured_count"],
            "parsed_count": result["parsed_count"],
            "salary_min": result["salary_min"],
            "salary_max": result["salary_max"],
            "currency": result["currency"],
        },
        unit=f"annual salary in {currency}",
        scope=_scope_description({
            "role_category": role_category, "specialization": specialization,
            "level": level, "track": track, "country": country,
        }),
        time_window=time_window_label(result["data_range"]["earliest"], result["data_range"]["latest"]),
        source="Structured or free-text-parsed compensation fields from live job postings",
        total_matching=result["total_matching"],
    )


def get_skill_demand(
    role_category: list[str] | None = None,
    specialization: list[str] | None = None,
    level: list[str] | None = None,
    track: list[str] | None = None,
    country: list[str] | None = None,
    skill_group: list[str] | None = None,
    raw_skill: list[str] | None = None,
    work_arrangement: list[str] | None = None,
    education_required: list[str] | None = None,
) -> dict:
    """
    Skills, education, work-arrangement, and language requirements
    extracted from job postings. total_matching is the real denominator for
    any percentage you state — it's postings with extraction completed, not
    every matching posting from get_job_demand.
    """
    result = query_requirements_data(
        role_category=role_category, specialization=specialization, level=level, track=track,
        country=country, skill_group=skill_group, raw_skill=raw_skill,
        work_arrangement=work_arrangement, education_required=education_required,
    )
    return build_envelope(
        {
            "skills": result["skills"],
            "education_levels": result["education_levels"],
            "equivalent_experience_accepted_count": result["equivalent_experience_accepted_count"],
            "years_experience_min": result["years_experience_min"],
            "work_arrangement": result["work_arrangement"],
            "languages": result["languages"],
        },
        unit="% and count of postings with requirements extracted (see total_matching for the real denominator)",
        scope=_scope_description({
            "role_category": role_category, "specialization": specialization, "level": level,
            "track": track, "country": country, "skill_group": skill_group, "raw_skill": raw_skill,
        }),
        time_window=time_window_label(result["data_range"]["earliest"], result["data_range"]["latest"]),
        source="Skills, education, and language requirements extracted from live job postings",
        total_matching=result["total_matching"],
    )


def get_employment_risk(
    company: str | None = None,
    sector: str | None = None,
    country: list[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """
    Reported employment events (layoffs, closures, restructuring,
    bankruptcy, offshoring, expansion, hiring announcements) for any company
    or sector the ingested registries cover — NOT restricted to this
    platform's own tracked job-posting companies, and never joinable against
    get_job_demand/get_salary_stats/get_skill_demand (a fully independent
    dataset). Only judge a pattern (vs. an isolated event) when `events` has
    at least two entries for the queried company/sector.
    """
    result = query_employment_events_data(
        company=company, sector=sector, country=country, date_from=date_from, date_to=date_to,
    )
    sources_checked = [SOURCE_DISPLAY_NAMES.get(s, s) for s in result["sources_checked"]]
    return build_envelope(
        {"events": result["events"]},
        unit="reported employment events, oldest first",
        scope=_scope_description({"company": company, "sector": sector, "country": country}),
        time_window=time_window_label(date_from, date_to),
        source="External employment-event registries (see sources_checked in this response's meta)",
        total_matching=result["total_matching"],
        sources_checked=sources_checked,
    )


def list_tracked_companies() -> dict:
    """
    The companies this platform tracks job postings for, with industry
    where tagged. Metadata only — does NOT gate or filter get_employment_risk,
    which answers for any company the registries cover, tracked or not. Use
    this to check whether a company is one this platform has job-posting-
    side context on before asking a job-demand question about it.
    """
    companies = [
        {"company": key, "display_name": key.replace("-", " ").title(), "industry": industry}
        for key, industry in sorted(industries.COMPANY_INDUSTRY.items())
    ]
    return build_envelope(
        {"companies": companies},
        unit="tracked companies with their curated industry tag",
        scope={},
        time_window={"from": None, "to": None, "label": "not applicable — a static, curated list"},
        source="This platform's curated company list (reviewed periodically, not exhaustive)",
        total_matching=len(companies),
    )
