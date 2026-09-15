"""
Tech Market Intelligence Platform — FastAPI application entry point.

Starts with:
  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request

load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import auth
from chat import router as chat_router
from db import init_schema
from market_health import router as market_health_router
from market_openings import router as market_openings_router
from mcp_access.account import router as mcp_account_router
from mcp_access.oauth import router as mcp_oauth_router
from mcp_access.server import get_mcp_asgi_app, mcp_lifespan
from mcp_access.well_known import router as mcp_well_known_router

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan — schema init (unchanged, just moved off the legacy @app.on_event
# style) plus mcp_access's session-manager context, which the MCP SDK
# requires entered for the lifetime of the process (see
# mcp_access/server.py's mcp_lifespan() docstring for why — a real 500
# found by curling the deployed /mcp endpoint, not by any import-level
# check, since nothing about registering tools or mounting the app touches
# this path).
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(app: FastAPI):
    try:
        init_schema()
    except Exception as exc:
        logger.warning("Could not initialise market-health schema: %s", exc)
    async with mcp_lifespan():
        yield

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Tech Market Intelligence Platform API",
    description="Market health signals, trend data, and AI-assisted market queries for tech professionals.",
    version="1.0.0",
    lifespan=_lifespan,
)

# ---------------------------------------------------------------------------
# CORS — local dev origins, always allowed, plus real deployed origin(s) from
# CORS_ALLOWED_ORIGINS (comma-separated) once `web` is deployed. Added
# 2026-08-16 — see backend/specs/market-health/api.md — Tech Decisions and
# changes/2026-08-16-production-cors-config.md. The env var is appended to,
# never replaces, the local-dev list, so local dev is unaffected whether or
# not it's set. A wildcard origin isn't used: it can't be combined with
# allow_credentials=True per the CORS spec, and this service already sets
# allow_credentials=True.
# ---------------------------------------------------------------------------

_LOCAL_DEV_ORIGINS = [
    "http://localhost:3000",   # typical React/Next.js dev server
    "http://localhost:5173",   # Vite dev server
    "http://localhost:4173",   # Vite preview
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
_production_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_LOCAL_DEV_ORIGINS + _production_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(market_health_router)
app.include_router(market_openings_router)
app.include_router(chat_router)

# ---------------------------------------------------------------------------
# Bring-your-own-AI access (added 2026-09-15, deployed same day at the
# user's request — see changes/2026-09-13-mcp-ai-agent-access.md's Decision
# Log) — see backend/specs/mcp-access/api.md, for
# outcomes/bring-your-own-ai-agent-access.md. Mounted on this same api
# service, not a new Railway service, per that spec's Tech Decisions.
# ---------------------------------------------------------------------------

app.include_router(mcp_account_router)
app.include_router(mcp_oauth_router)
app.include_router(mcp_well_known_router)
app.mount("/mcp", get_mcp_asgi_app())


@app.exception_handler(auth.NotAuthenticated)
def _account_not_authenticated(request: Request, exc: auth.NotAuthenticated) -> JSONResponse:
    """Every /api/account/* route guarded by auth.require_user_session lands
    here on a missing/invalid/expired cookie — a plain 401 JSON body, never a
    redirect (these are called by fetch(), not navigated to; contrast with
    the OAuth consent screen's own not-signed-in redirect, which is a real
    page navigation and handles that itself in mcp_access/oauth.py)."""
    return JSONResponse({"error": "not_authenticated"}, status_code=401)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"])
def health() -> dict:
    """Lightweight liveness check."""
    return {"status": "ok"}
