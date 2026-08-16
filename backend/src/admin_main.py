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
from pathlib import Path
from urllib.parse import urlencode

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import Depends, FastAPI, Form, Query, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import classification
import ingestion_runs
import raw_postings
import requirements
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
            "classification_distribution": classification.get_classification_distribution(),
            "taxonomy_version_breakdown": classification.get_taxonomy_version_breakdown(),
            "skill_group_distribution": requirements.get_skill_group_distribution(),
            "latest_run": runs[0] if runs else None,
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
        "specialization": specialization, "classification_confidence": classification_confidence,
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
                "confidences": sorted(classification.CLASSIFICATION_CONFIDENCE_VALUES),
                "taxonomy_versions": [r["version"] for r in classification.get_taxonomy_version_breakdown()],
                "requirements_statuses": ["extracted", "pending", "failed", "not_eligible"],
                "sources": ["greenhouse", "lever", "ashby", "adzuna"],
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
    return templates.TemplateResponse(request, "run_detail.html", {"active_page": "runs", "run": run})


# ---------------------------------------------------------------------------
# Health check — same pattern as main.py
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"])
def health() -> dict:
    return {"status": "ok"}
