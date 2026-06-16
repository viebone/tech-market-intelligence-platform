"""
Tech Market Intelligence Platform — FastAPI application entry point.

Starts with:
  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chat import router as chat_router
from market_health import router as market_health_router

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Tech Market Intelligence Platform API",
    description="Market health signals, trend data, and AI-assisted market queries for tech professionals.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow local dev origins
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # typical React/Next.js dev server
        "http://localhost:5173",   # Vite dev server
        "http://localhost:4173",   # Vite preview
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(market_health_router)
app.include_router(chat_router)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["ops"])
def health() -> dict:
    """Lightweight liveness check."""
    return {"status": "ok"}
