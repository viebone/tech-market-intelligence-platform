"""
Tech Market Intelligence Platform — FastAPI application entry point.

Starts with:
  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi.middleware.cors import CORSMiddleware

from chat import router as chat_router
from db import init_schema
from market_health import router as market_health_router
from market_openings import router as market_openings_router

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Tech Market Intelligence Platform API",
    description="Market health signals, trend data, and AI-assisted market queries for tech professionals.",
    version="1.0.0",
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
# Startup — ensure raw_postings / classifications exist.
# Non-fatal if the DB is unreachable: only /api/market-health/openings depends
# on it, everything else (summary, chat, exceptions) still runs on mock data.
# ---------------------------------------------------------------------------

@app.on_event("startup")
def _ensure_schema() -> None:
    try:
        init_schema()
    except Exception as exc:
        logger.warning("Could not initialise market-health schema: %s", exc)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"])
def health() -> dict:
    """Lightweight liveness check."""
    return {"status": "ok"}
