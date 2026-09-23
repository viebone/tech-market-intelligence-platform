"""
FastAPI router for User Feedback endpoints — anonymous, no auth, matching
this product's existing "no auth on /api/*" posture (backend/specs/
user-feedback/api.md). Registered in main.py alongside market_health_router,
same as every other /api/* feature router in this app.

Endpoints:
  POST /api/feedback/platform-rating
  POST /api/feedback/story-reaction
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import feedback_storage

router = APIRouter()


class PlatformRatingRequest(BaseModel):
    # rating bounds (1-5) enforced by the schema itself, not client-side
    # trust — backend/specs/user-feedback/api.md — Business Logic.
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class StoryReactionRequest(BaseModel):
    story_id: str
    reaction: Literal["up", "down"]
    comment: str | None = Field(default=None, max_length=2000)


def _created_response(result: dict) -> JSONResponse:
    return JSONResponse(
        content={"id": result["id"], "created_at": result["created_at"].isoformat()},
        status_code=201,
    )


@router.post("/api/feedback/platform-rating")
def post_platform_rating(body: PlatformRatingRequest) -> JSONResponse:
    """Capture a product-level satisfaction rating from the Feedback Panel.
    No dedup, no rate limiting, no one-per-user gate — every submission is
    its own independent record (Business Logic)."""
    result = feedback_storage.insert_platform_rating(body.rating, body.comment)
    return _created_response(result)


@router.post("/api/feedback/story-reaction")
def post_story_reaction(body: StoryReactionRequest) -> JSONResponse:
    """Capture a thumbs up/down reaction (and optional comment) for a
    specific Data Story. story_id is validated against the live catalogue
    (market_stories.list_stories()) at request time — a stale or typo'd id
    is refused here rather than silently stored (Business Logic)."""
    if body.story_id not in feedback_storage.valid_story_ids():
        raise HTTPException(
            status_code=422,
            detail=f"story_id {body.story_id!r} doesn't match any current Data Story.",
        )
    result = feedback_storage.insert_story_reaction(body.story_id, body.reaction, body.comment)
    return _created_response(result)
