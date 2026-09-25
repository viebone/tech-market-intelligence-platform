"""
Pipeline Visibility — admin dashboard FastAPI app.

A separate FastAPI app from main.py — not a router mounted on the
consumer-facing API — deployed as its own Railway service, its own domain,
server-rendering its own Jinja2 templates. See backend/specs/
pipeline-visibility/api.md — Deployment topology, and
changes/2026-08-13-admin-pipeline-dashboard.md's Decision Log for the full
reasoning (domain isolation from `web`, plus auth, not either alone).

Starts with:
    uvicorn admin_main:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import batch_jobs
import classification
import employment_events_storage
import feedback_storage
import ingestion_runs
import market_stories
import raw_postings
import requirements
import scraping_storage
import statistics_storage
from employment_events.base import EVENT_TYPES, SOURCE_DISPLAY_NAMES
from source_licences import SOURCE_LICENCES, is_commercial_mode, overall_status
from requirements import BATCH_STUCK_AFTER_HOURS, REQUIREMENTS_BATCH_MIN_BACKLOG
from admin_auth import (
    SESSION_COOKIE_NAME,
    SESSION_EXPIRY_HOURS,
    NotAuthenticated,
    create_session_token,
    require_admin_session,
    verify_password,
)
from db import init_schema

logger = logging.getLogger(__name__)

app = FastAPI(title="Pipeline Visibility — Admin Dashboard")

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "admin_templates"))
app.mount("/admin/static", StaticFiles(directory=str(BASE_DIR / "admin_static")), name="admin_static")

# Cookie must be Secure in production (Railway serves this service over
# HTTPS). Overridable for local dev, where plain HTTP means a Secure cookie
# would never actually be sent back by the browser — see backend/.env.example.
COOKIE_SECURE = os.environ.get("ADMIN_COOKIE_SECURE", "true").lower() != "false"


@app.on_event("startup")
def _ensure_schema() -> None:
    try:
        init_schema()
    except Exception as exc:
        logger.warning("Could not initialise schema: %s", exc)


@app.exception_handler(NotAuthenticated)
def _redirect_to_login(request: Request, exc: NotAuthenticated) -> RedirectResponse:
    """Every /admin/* route (except login) that fails require_admin_session()
    lands here — never a raw error page, never any dashboard content or data
    rendered. See backend/specs/pipeline-visibility/api.md — API Endpoints."""
    return RedirectResponse("/admin/login", status_code=303)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@app.get("/admin/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/admin/login")
def login_submit(request: Request, password: str = Form(...)):
    if not verify_password(password):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Incorrect password."}, status_code=401
        )
    token = create_session_token()
    response = RedirectResponse("/admin/", status_code=303)
    response.set_cookie(
        SESSION_COOKIE_NAME, token,
        httponly=True, secure=COOKIE_SECURE, samesite="strict",
        max_age=SESSION_EXPIRY_HOURS * 3600,
    )
    return response


@app.post("/admin/logout", dependencies=[Depends(require_admin_session)])
def logout():
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

def _requirements_backlog_status() -> dict:
    """Overview's backlog & batch-status line — backend/specs/pipeline-visibility/
    api.md — Business Logic — Requirements backlog & batch status. Reuses the
    pipeline's own backlog count so the dashboard and the pipeline never
    disagree; reads batch_jobs, never writes it."""
    count = raw_postings.count_needing_requirements()
    job = batch_jobs.get_latest_job()
    batch: dict | None = None
    if job is not None:
        batch = {
            "state": job["state"],
            "item_count": job["item_count"],
            "est_cost_usd": job["est_cost_usd"],
            "actual_cost_usd": job["actual_cost_usd"],
            "submitted_at": job["submitted_at"],
            "completed_at": job["completed_at"],
            "error": job["error"],
        }
        if job["state"] in batch_jobs.ACTIVE_STATES and job["submitted_at"] is not None:
            batch["expected_by"] = job["submitted_at"] + timedelta(hours=BATCH_STUCK_AFTER_HOURS)
    no_batch_needed = job is None and count < REQUIREMENTS_BATCH_MIN_BACKLOG
    return {"count": count, "batch": batch, "no_batch_needed": no_batch_needed}


@app.get("/admin/", dependencies=[Depends(require_admin_session)])
def overview(request: Request):
    coverage = requirements.get_requirements_coverage()
    runs = ingestion_runs.list_runs(page=1, page_size=1)["runs"]
    return templates.TemplateResponse(
        request, "overview.html",
        {
            "active_page": "overview",
            "totals": {"total_postings": raw_postings.count_postings()},
            "requirements_coverage": coverage,
            "requirements_backlog": _requirements_backlog_status(),
            "classification_distribution": classification.get_classification_distribution(),
            "taxonomy_version_breakdown": classification.get_taxonomy_version_breakdown(),
            "skill_group_distribution": requirements.get_skill_group_distribution(),
            "latest_run": runs[0] if runs else None,
            "employment_events_summary": employment_events_storage.get_summary(),
        },
    )


# ---------------------------------------------------------------------------
# Postings
# ---------------------------------------------------------------------------

def _clean_query(params: dict) -> dict:
    """Drop empty/None values so they never end up in a rebuilt query string
    (an empty `role_category=` filter chip would be confusing and pointless)."""
    return {k: v for k, v in params.items() if v not in (None, "")}


@app.get("/admin/postings", dependencies=[Depends(require_admin_session)])
def postings_list(
    request: Request,
    role_category: str | None = None,
    level: str | None = None,
    track: str | None = None,
    specialization: str | None = None,
    job_function: str | None = None,
    classification_confidence: str | None = None,
    taxonomy_version: str | None = None,
    requirements_status: str | None = None,
    source: str | None = None,
    search: str | None = None,
    sort: str = "fetched_at",
    dir: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    filters = {
        "role_category": role_category, "level": level, "track": track,
        "specialization": specialization, "job_function": job_function,
        "classification_confidence": classification_confidence,
        "taxonomy_version": taxonomy_version, "requirements_status": requirements_status,
        "source": source, "search": search,
    }
    result = raw_postings.list_postings(
        **filters, sort=sort, dir=dir, page=page, page_size=page_size,
    )

    active_filters = _clean_query(filters)
    base_query = urlencode(active_filters)
    page_base_query = urlencode({**active_filters, "sort": sort, "dir": dir})

    active_filter_chips = [
        {
            "label": f"{key.replace('_', ' ')}: {value}",
            "remove_href": "/admin/postings?" + urlencode({k: v for k, v in active_filters.items() if k != key}),
        }
        for key, value in active_filters.items()
    ]

    sort_links = {}
    for column in ("fetched_at", "company", "role_category", "level", "classification_confidence", "taxonomy_version"):
        # Clicking the already-active column toggles direction; clicking any
        # other column starts it fresh at desc.
        next_dir = ("asc" if dir == "desc" else "desc") if sort == column else "desc"
        sort_links[column] = "/admin/postings?" + urlencode({**active_filters, "sort": column, "dir": next_dir})

    total_pages = max(1, math.ceil(result["total"] / page_size))

    return templates.TemplateResponse(
        request, "postings.html",
        {
            "active_page": "postings",
            "postings": result["postings"],
            "total": result["total"],
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "sort": sort,
            "dir": dir,
            "filters": filters,
            "active_filter_chips": active_filter_chips,
            "base_query": base_query,
            "page_base_query": page_base_query,
            "sort_links": sort_links,
            "filter_options": {
                "role_categories": sorted(classification.ROLE_CATEGORIES),
                "levels": sorted(classification.LEVEL_LADDER) + ["unknown"],
                "tracks": sorted(classification.TRACKS) + ["unknown"],
                "specializations": classification.get_distinct_specializations(),
                "job_functions": sorted(classification.JOB_FUNCTIONS) + ["unknown"],
                "confidences": sorted(classification.CLASSIFICATION_CONFIDENCE_VALUES),
                "taxonomy_versions": [r["version"] for r in classification.get_taxonomy_version_breakdown()],
                "requirements_statuses": ["extracted", "pending", "failed", "not_eligible"],
                "sources": ["greenhouse", "lever", "ashby", "workable", "adzuna"],
            },
        },
    )


@app.get("/admin/postings/{posting_id:path}", dependencies=[Depends(require_admin_session)])
def posting_detail(request: Request, posting_id: str):
    data = raw_postings.get_posting(posting_id)
    if data is None:
        raise HTTPException(status_code=404, detail="No posting with that id")
    data["posting"]["raw_response_json"] = json.dumps(data["posting"]["raw_response"], indent=2, default=str)
    return templates.TemplateResponse(request, "posting_detail.html", {"active_page": "postings", "data": data})


# ---------------------------------------------------------------------------
# Ingestion runs
# ---------------------------------------------------------------------------

@app.get("/admin/runs", dependencies=[Depends(require_admin_session)])
def runs_list(request: Request, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200)):
    result = ingestion_runs.list_runs(page=page, page_size=page_size)
    total_pages = max(1, math.ceil(result["total"] / page_size))
    return templates.TemplateResponse(
        request, "runs.html",
        {
            "active_page": "runs",
            "runs": result["runs"],
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    )


@app.get("/admin/runs/{run_id}", dependencies=[Depends(require_admin_session)])
def run_detail(request: Request, run_id: int):
    run = ingestion_runs.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="No run with that id")
    terms = run["terms_processed"] or []
    run["is_legacy_format"] = bool(terms) and "source" not in terms[0]
    # Batch job this run submitted (if any), for the batch-activity section —
    # backend/specs/pipeline-visibility/api.md — Batch activity.
    submitted_batch = (
        batch_jobs.get_job(run["batch_submitted_id"]) if run["batch_submitted_id"] else None
    )
    return templates.TemplateResponse(
        request, "run_detail.html",
        {"active_page": "runs", "run": run, "submitted_batch": submitted_batch},
    )


# ---------------------------------------------------------------------------
# Employment events — added 2026-09-11, changes/2026-09-11-employment-events-
# admin-visibility.md. Read-only over employment_events/employment_event_cursors;
# never joined to raw_postings or any other job-postings table — see
# backend/EMPLOYMENT_EVENTS.md and backend/specs/pipeline-visibility/api.md.
# ---------------------------------------------------------------------------

@app.get("/admin/employment-events", dependencies=[Depends(require_admin_session)])
def employment_events_list(
    request: Request,
    source: str | None = None,
    event_type: str | None = None,
    direction: str | None = None,
    confidence: str | None = None,
    country: str | None = None,
    sort: str = "event_date",
    dir: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    filters = {
        "source": source, "event_type": event_type, "direction": direction,
        "confidence": confidence, "country": country,
    }
    result = employment_events_storage.list_events(**filters, sort=sort, dir=dir, page=page, page_size=page_size)

    active_filters = _clean_query(filters)
    page_base_query = urlencode({**active_filters, "sort": sort, "dir": dir})

    active_filter_chips = [
        {
            "label": f"{key.replace('_', ' ')}: {value}",
            "remove_href": "/admin/employment-events?" + urlencode({k: v for k, v in active_filters.items() if k != key}),
        }
        for key, value in active_filters.items()
    ]

    sort_links = {}
    for column in ("event_date", "company_raw", "source", "event_type", "jobs_affected"):
        next_dir = ("asc" if dir == "desc" else "desc") if sort == column else "desc"
        sort_links[column] = "/admin/employment-events?" + urlencode({**active_filters, "sort": column, "dir": next_dir})

    total_pages = max(1, math.ceil(result["total"] / page_size))

    return templates.TemplateResponse(
        request, "employment_events.html",
        {
            "active_page": "employment_events",
            "events": result["events"],
            "total": result["total"],
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "sort": sort,
            "dir": dir,
            "filters": filters,
            "active_filter_chips": active_filter_chips,
            "page_base_query": page_base_query,
            "sort_links": sort_links,
            "filter_options": {
                "sources": sorted(SOURCE_DISPLAY_NAMES.keys()),
                "source_display_names": SOURCE_DISPLAY_NAMES,
                "event_types": sorted(EVENT_TYPES),
                "directions": ["contraction", "expansion"],
                "confidences": ["confirmed", "reported"],
                "countries": employment_events_storage.get_distinct_countries(),
            },
        },
    )


@app.get("/admin/employment-events/{event_id:path}", dependencies=[Depends(require_admin_session)])
def employment_event_detail(request: Request, event_id: str):
    event = employment_events_storage.get_event(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="No employment event with that id")
    event["raw_response_json"] = json.dumps(event["raw_response"], indent=2, default=str)
    event["source_display_name"] = SOURCE_DISPLAY_NAMES.get(event["source"], event["source"])
    return templates.TemplateResponse(
        request, "employment_event_detail.html",
        {"active_page": "employment_events", "event": event},
    )


# ---------------------------------------------------------------------------
# Sources & Licensing — added 2026-09-16,
# changes/2026-09-16-admin-licensing-visibility.md. A flat list, not List ->
# Detail (unlike every route above) — SOURCE_LICENCES is a small in-memory
# registry, not a database table (see backend/specs/pipeline-visibility/
# api.md — Tech Decisions for why this is a deliberate exception).
# ---------------------------------------------------------------------------

@app.get("/admin/licensing", dependencies=[Depends(require_admin_session)])
def licensing(request: Request):
    sources = [
        {
            "source": licence.source,
            "licence": licence.licence,
            "status": overall_status(licence.source),  # "pending" | "licensed" | "rejected"
            "confirmed": licence.confirmed,
            "permits_commercial_use": licence.permits_commercial_use,
            "rejected": licence.rejected,
            "attribution_text": licence.attribution_text,
            "licence_url": licence.licence_url,
            "data_summary": licence.data_summary,
        }
        for licence in sorted(SOURCE_LICENCES.values(), key=lambda l: l.source)
    ]
    return templates.TemplateResponse(
        request, "licensing.html",
        {
            "active_page": "licensing",
            "sources": sources,
            "commercial_mode": is_commercial_mode(),
        },
    )


# ---------------------------------------------------------------------------
# Market Observations / Skill Associations / Scraped Source Runs — added
# 2026-09-18, changes/2026-09-18-admin-market-benchmark-visibility.md.
# Read-only over market_observations/skill_associations/scrape_ingestion_runs
# (backend/specs/scraped-data-sources/api.md owns and writes all of it).
# ---------------------------------------------------------------------------

@app.get("/admin/market-observations", dependencies=[Depends(require_admin_session)])
def market_observations_list(
    request: Request,
    source: str | None = None,
    entity_type: str | None = None,
    entity_name: str | None = None,
    employment_type: str | None = None,
    sort: str = "period_end",
    dir: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    filters = {
        "source": source, "entity_type": entity_type,
        "entity_name": entity_name, "employment_type": employment_type,
    }
    result = scraping_storage.list_market_observations(**filters, sort=sort, dir=dir, page=page, page_size=page_size)

    active_filters = _clean_query(filters)
    page_base_query = urlencode({**active_filters, "sort": sort, "dir": dir})

    active_filter_chips = [
        {
            "label": f"{key.replace('_', ' ')}: {value}",
            "remove_href": "/admin/market-observations?" + urlencode({k: v for k, v in active_filters.items() if k != key}),
        }
        for key, value in active_filters.items()
    ]

    sort_links = {}
    for column in ("period_end", "entity_name", "rank", "vacancy_count"):
        next_dir = ("asc" if dir == "desc" else "desc") if sort == column else "desc"
        sort_links[column] = "/admin/market-observations?" + urlencode({**active_filters, "sort": column, "dir": next_dir})

    total_pages = max(1, math.ceil(result["total"] / page_size))

    return templates.TemplateResponse(
        request, "market_observations.html",
        {
            "active_page": "market_observations",
            "observations": result["observations"],
            "total": result["total"],
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "sort": sort,
            "dir": dir,
            "filters": filters,
            "active_filter_chips": active_filter_chips,
            "page_base_query": page_base_query,
            "sort_links": sort_links,
            "filter_options": {
                "sources": scraping_storage.get_distinct_observation_sources(),
                "entity_types": ["role", "skill", "technology", "capability"],
                "entity_names": scraping_storage.get_distinct_observation_entity_names(),
                "employment_types": ["permanent", "contract"],
            },
        },
    )


@app.get("/admin/market-observations/{observation_id:path}", dependencies=[Depends(require_admin_session)])
def market_observation_detail(request: Request, observation_id: str):
    observation = scraping_storage.get_market_observation(observation_id)
    if observation is None:
        raise HTTPException(status_code=404, detail="No observation with that id")
    observation["raw_response_json"] = json.dumps(observation["raw_response"], indent=2, default=str)

    extraction = scraping_storage.get_extraction_for_url(observation["source_url"])
    if extraction is not None:
        # "Fresh this run" vs "reused from cache" — backend/specs/pipeline-visibility/
        # api.md — Business Logic — Extraction provenance "fresh vs. reused".
        delta = abs((extraction["extracted_at"] - observation["fetched_at"]).total_seconds())
        extraction["is_fresh"] = delta < 300  # a few minutes' tolerance for the LLM call's own latency

    return templates.TemplateResponse(
        request, "market_observation_detail.html",
        {"active_page": "market_observations", "observation": observation, "extraction": extraction},
    )


@app.get("/admin/skill-associations", dependencies=[Depends(require_admin_session)])
def skill_associations_list(
    request: Request,
    source: str | None = None,
    role_name: str | None = None,
    sort: str = "rank",
    dir: str = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    filters = {"source": source, "role_name": role_name}
    result = scraping_storage.list_skill_associations(**filters, sort=sort, dir=dir, page=page, page_size=page_size)

    active_filters = _clean_query(filters)
    page_base_query = urlencode({**active_filters, "sort": sort, "dir": dir})

    active_filter_chips = [
        {
            "label": f"{key.replace('_', ' ')}: {value}",
            "remove_href": "/admin/skill-associations?" + urlencode({k: v for k, v in active_filters.items() if k != key}),
        }
        for key, value in active_filters.items()
    ]

    sort_links = {}
    for column in ("rank", "percentage", "job_count"):
        next_dir = ("asc" if dir == "desc" else "desc") if sort == column else "desc"
        sort_links[column] = "/admin/skill-associations?" + urlencode({**active_filters, "sort": column, "dir": next_dir})

    total_pages = max(1, math.ceil(result["total"] / page_size))

    return templates.TemplateResponse(
        request, "skill_associations.html",
        {
            "active_page": "skill_associations",
            "associations": result["associations"],
            "total": result["total"],
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "sort": sort,
            "dir": dir,
            "filters": filters,
            "active_filter_chips": active_filter_chips,
            "page_base_query": page_base_query,
            "sort_links": sort_links,
            "filter_options": {
                "sources": scraping_storage.get_distinct_association_sources(),
                "roles": scraping_storage.get_distinct_association_roles(),
            },
        },
    )


@app.get("/admin/skill-associations/{association_id:path}", dependencies=[Depends(require_admin_session)])
def skill_association_detail(request: Request, association_id: str):
    association = scraping_storage.get_skill_association(association_id)
    if association is None:
        raise HTTPException(status_code=404, detail="No skill association with that id")
    association["raw_response_json"] = json.dumps(association["raw_response"], indent=2, default=str)
    return templates.TemplateResponse(
        request, "skill_association_detail.html",
        {"active_page": "skill_associations", "association": association},
    )


@app.get("/admin/scrape-runs", dependencies=[Depends(require_admin_session)])
def scrape_runs(request: Request):
    return templates.TemplateResponse(
        request, "scrape_runs.html",
        {"active_page": "scrape_runs", "runs": scraping_storage.list_scrape_runs()},
    )


# ---------------------------------------------------------------------------
# Trusted Statistics + Statistics Sources — added 2026-09-25,
# changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md, backend/specs/
# pipeline-visibility/api.md. Read-only over statistic_series / statistic_releases /
# statistic_observations (backend/specs/trusted-statistics/api.md owns and writes all of it).
# Every row names its publisher and unit — the operator view names the source exactly as any
# user-facing surface must.
# ---------------------------------------------------------------------------

@app.get("/admin/statistics", dependencies=[Depends(require_admin_session)])
def statistics_list(
    request: Request,
    source: str | None = None,
    dataset_code: str | None = None,
    dimension_type: str | None = None,
    series_code: str | None = None,
    vintages: str = "latest",
    sort: str = "period_end",
    dir: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    from trusted_stats.registry import TRUSTED_PUBLISHERS

    vintages = "all" if vintages == "all" else "latest"
    filters = {"source": source, "dataset_code": dataset_code, "dimension_type": dimension_type, "series_code": series_code}
    rows, total = statistics_storage.list_statistics(**filters, vintages=vintages, sort=sort, direction=dir, page=page, page_size=page_size)

    active_filters = _clean_query({**filters, **({"vintages": "all"} if vintages == "all" else {})})
    page_base_query = urlencode({**active_filters, "sort": sort, "dir": dir})
    active_filter_chips = [
        {"label": f"{key.replace('_', ' ')}: {value}",
         "remove_href": "/admin/statistics?" + urlencode({k: v for k, v in active_filters.items() if k != key})}
        for key, value in active_filters.items()
    ]
    sort_links = {}
    for column in ("period_end", "series_code", "value", "released_on"):
        next_dir = ("asc" if dir == "desc" else "desc") if sort == column else "desc"
        sort_links[column] = "/admin/statistics?" + urlencode({**active_filters, "sort": column, "dir": next_dir})

    return templates.TemplateResponse(
        request, "statistics.html",
        {
            "active_page": "statistics", "rows": rows, "total": total, "page": page, "page_size": page_size,
            "total_pages": max(1, math.ceil(total / page_size)), "sort": sort, "dir": dir, "filters": filters,
            "vintages": vintages, "active_filter_chips": active_filter_chips, "page_base_query": page_base_query,
            "sort_links": sort_links,
            "filter_options": {
                "sources": sorted(set(TRUSTED_PUBLISHERS) | set(statistics_storage.sources_with_data())),
                "datasets": sorted({d for p in TRUSTED_PUBLISHERS.values() for d in p.datasets}),
                "dimension_types": ["total", "industry", "size_band"],
            },
        },
    )


@app.get("/admin/statistics-sources", dependencies=[Depends(require_admin_session)])
def statistics_sources(request: Request):
    return templates.TemplateResponse(
        request, "statistics_sources.html",
        {"active_page": "statistics_sources", "sources": statistics_storage.list_statistics_sources()},
    )


@app.get("/admin/statistics/{observation_id:path}", dependencies=[Depends(require_admin_session)])
def statistic_detail(request: Request, observation_id: str):
    detail = statistics_storage.get_statistic(observation_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="No statistic with that id")
    return templates.TemplateResponse(
        request, "statistic_detail.html",
        {"active_page": "statistics", **detail, "dimensions_json": json.dumps(detail["series"]["dimensions"], ensure_ascii=False)},
    )


# ---------------------------------------------------------------------------
# Taxonomy Health — added 2026-09-21, changes/2026-09-21-emerging-role-
# detection.md. Deliberately a live, on-demand query (get_emerging_taxonomy_
# candidates() reruns fresh every page load) rather than a stored monthly
# snapshot — there's no separate "monthly job" to trigger since nothing here
# is generated or mutated by running it; "monthly cadence" describes the
# operator's own habit of checking this page, not a backend automation. See
# that change's Decision Log for why a cron was deliberately not built.
# ---------------------------------------------------------------------------

@app.get("/admin/taxonomy-health", dependencies=[Depends(require_admin_session)])
def taxonomy_health(request: Request):
    return templates.TemplateResponse(
        request, "taxonomy_health.html",
        {
            "active_page": "taxonomy_health",
            "candidates": classification.get_emerging_taxonomy_candidates(),
        },
    )


# ---------------------------------------------------------------------------
# Feedback — added 2026-09-23, changes/2026-09-23-user-feedback-mechanism.md.
# Read-only over platform_feedback/story_reactions, owned and written by the
# two anonymous consumer endpoints in feedback.py — see backend/specs/
# user-feedback/api.md and backend/specs/pipeline-visibility/api.md.
# ---------------------------------------------------------------------------

@app.get("/admin/feedback", dependencies=[Depends(require_admin_session)])
def feedback_summary(request: Request):
    return templates.TemplateResponse(
        request, "feedback_summary.html",
        {"active_page": "feedback", "summary": feedback_storage.get_feedback_summary()},
    )


@app.get("/admin/feedback/responses", dependencies=[Depends(require_admin_session)])
def feedback_responses(
    request: Request,
    type: str | None = None,
    story_id: str | None = None,
    has_comment: bool | None = None,
    sort: str = "created_at",
    dir: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    filters = {"type": type, "story_id": story_id, "has_comment": has_comment}
    result = feedback_storage.list_feedback_responses(
        **filters, sort=sort, dir=dir, page=page, page_size=page_size,
    )

    active_filters = _clean_query(filters)
    page_base_query = urlencode({**active_filters, "sort": sort, "dir": dir})

    active_filter_chips = [
        {
            "label": f"{key.replace('_', ' ')}: {value}",
            "remove_href": "/admin/feedback/responses?" + urlencode({k: v for k, v in active_filters.items() if k != key}),
        }
        for key, value in active_filters.items()
    ]

    # created_at is the only sortable column (backend/specs/pipeline-
    # visibility/api.md — no other field is shared/comparable across both
    # row types), so this is a single toggle link, not a per-column dict.
    next_dir = "asc" if dir == "desc" else "desc"
    sort_link = "/admin/feedback/responses?" + urlencode({**active_filters, "sort": "created_at", "dir": next_dir})

    total_pages = max(1, math.ceil(result["total"] / page_size))

    return templates.TemplateResponse(
        request, "feedback_responses.html",
        {
            "active_page": "feedback_responses",
            "responses": result["responses"],
            "total": result["total"],
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "sort": sort,
            "dir": dir,
            "filters": filters,
            "active_filter_chips": active_filter_chips,
            "page_base_query": page_base_query,
            "sort_link": sort_link,
            "filter_options": {
                "story_ids": [s["id"] for s in market_stories.list_stories()["stories"]],
            },
        },
    )


# ---------------------------------------------------------------------------
# Health check — same pattern as main.py
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"])
def health() -> dict:
    return {"status": "ok"}
