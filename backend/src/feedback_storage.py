"""
User Feedback storage — platform_feedback / story_reactions. Both tables are
anonymous and append-only (no update/delete path — see backend/specs/
user-feedback/api.md — Data Models). Storage module owns the SQL, the route
handlers (feedback.py, admin_main.py) own HTTP concerns — same split as
scraping_storage.py/employment_events_storage.py.
"""

from __future__ import annotations

from typing import Any

from db import get_connection
from market_stories import list_stories

RATING_VALUES = (1, 2, 3, 4, 5)

_RESPONSE_SORT_COLUMNS = {"created_at"}  # the only sortable column — see
# backend/specs/pipeline-visibility/api.md, GET /admin/feedback/responses:
# "there's no other shared, comparable field across both row types."


def valid_story_ids() -> set[str]:
    """The live Data Story catalogue's ids, for POST /api/feedback/story-
    reaction's validation. Reuses market_stories.list_stories() — the same
    function GET /api/market-health/stories already uses — never a fixed
    enum baked into this table (Business Logic — story_id validation)."""
    return {story["id"] for story in list_stories()["stories"]}


def _normalize_comment(comment: str | None) -> str | None:
    """An empty-string or whitespace-only comment is stored as NULL, never as
    "" (Business Logic — Comment normalization) — keeps "has a written
    comment" a simple IS NOT NULL check for the admin aggregate."""
    if comment is None:
        return None
    comment = comment.strip()
    return comment or None


def insert_platform_rating(rating: int, comment: str | None) -> dict[str, Any]:
    """Insert one PlatformFeedback row. `rating` bounds (1-5) are enforced at
    the API layer (Pydantic Field(ge=1, le=5) in feedback.py), not here —
    this function trusts its caller, same as every other insert_* function
    in this codebase."""
    comment = _normalize_comment(comment)
    with get_connection() as conn:
        row = conn.execute(
            "INSERT INTO platform_feedback (rating, comment) VALUES (%s, %s) "
            "RETURNING id, created_at",
            (rating, comment),
        ).fetchone()
    return {"id": row[0], "created_at": row[1]}


def insert_story_reaction(story_id: str, reaction: str, comment: str | None) -> dict[str, Any]:
    """Insert one StoryReaction row. `story_id` membership in the live
    catalogue and `reaction` in {"up", "down"} are validated by the caller
    (feedback.py) before this is called — this function trusts its caller."""
    comment = _normalize_comment(comment)
    with get_connection() as conn:
        row = conn.execute(
            "INSERT INTO story_reactions (story_id, reaction, comment) VALUES (%s, %s, %s) "
            "RETURNING id, created_at",
            (story_id, reaction, comment),
        ).fetchone()
    return {"id": row[0], "created_at": row[1]}


# ---------------------------------------------------------------------------
# Admin read functions — added 2026-09-23
# (changes/2026-09-23-user-feedback-mechanism.md), for the pipeline-
# visibility admin dashboard. See backend/specs/pipeline-visibility/api.md
# for the routes these serve.
# ---------------------------------------------------------------------------

def get_feedback_summary() -> dict[str, Any]:
    """Overall platform rating aggregate + per-story reaction aggregate, for
    GET /admin/feedback. `by_story` left-joins the live Data Story catalogue
    against a GROUP BY over story_reactions, so every current story appears
    even with zero reactions — the catalogue drives the list, the reaction
    table only fills in counts (same "every registered X, run or not"
    precedent as scraping_storage.list_scrape_runs())."""
    with get_connection() as conn:
        rating_rows = conn.execute(
            "SELECT rating, count(*) FROM platform_feedback GROUP BY rating"
        ).fetchall()
        reaction_rows = conn.execute(
            "SELECT story_id, reaction, count(*) FROM story_reactions GROUP BY story_id, reaction"
        ).fetchall()

    distribution = {str(value): 0 for value in RATING_VALUES}
    total = 0
    weighted_sum = 0
    for rating, count in rating_rows:
        distribution[str(rating)] = count
        total += count
        weighted_sum += rating * count
    average_rating = round(weighted_sum / total, 2) if total else None

    reactions_by_story: dict[str, dict[str, int]] = {}
    for story_id, reaction, count in reaction_rows:
        reactions_by_story.setdefault(story_id, {"up": 0, "down": 0})[reaction] = count

    by_story = []
    for story in list_stories()["stories"]:
        counts = reactions_by_story.get(story["id"], {"up": 0, "down": 0})
        up, down = counts["up"], counts["down"]
        total_reactions = up + down
        by_story.append({
            "story_id": story["id"],
            "display_name": story["display_name"],
            "up": up,
            "down": down,
            "positive_share": round(up / total_reactions, 4) if total_reactions else None,
        })

    return {
        "platform": {
            "average_rating": average_rating,
            "count": total,
            "distribution": distribution,
        },
        "by_story": by_story,
    }


def list_feedback_responses(
    type: str | None = None,
    story_id: str | None = None,
    has_comment: bool | None = None,
    sort: str = "created_at",
    dir: str = "desc",
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """Filtered/sorted/paginated union of platform_feedback and
    story_reactions, for GET /admin/feedback/responses. The two tables are
    combined at query time only (UNION ALL), never merged at rest (Business
    Logic — Feedback responses list). `story_id` only ever matches
    story_reaction rows — applying it when `type` isn't "story_reaction"
    simply has no effect on the (story_id-less) platform_rating branch,
    matching the spec's "ignored otherwise" rule."""
    if sort not in _RESPONSE_SORT_COLUMNS:
        sort = "created_at"
    order_dir = "ASC" if dir == "asc" else "DESC"

    include_ratings = type in (None, "platform_rating")
    include_reactions = type in (None, "story_reaction")

    parts: list[str] = []
    params: list = []

    if include_ratings:
        conditions = []
        rating_params: list = []
        if has_comment is not None:
            conditions.append("comment IS NOT NULL" if has_comment else "comment IS NULL")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        parts.append(f"""
            SELECT id, 'platform_rating' AS type, NULL::TEXT AS story_id,
                   rating, NULL::TEXT AS reaction, comment, created_at
            FROM platform_feedback
            {where}
        """)
        params.extend(rating_params)

    if include_reactions:
        conditions = []
        reaction_params: list = []
        if story_id:
            conditions.append("story_id = %s")
            reaction_params.append(story_id)
        if has_comment is not None:
            conditions.append("comment IS NOT NULL" if has_comment else "comment IS NULL")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        parts.append(f"""
            SELECT id, 'story_reaction' AS type, story_id,
                   NULL::INTEGER AS rating, reaction, comment, created_at
            FROM story_reactions
            {where}
        """)
        params.extend(reaction_params)

    if not parts:
        return {"responses": [], "total": 0}

    union_sql = " UNION ALL ".join(parts)
    columns = ["id", "type", "story_id", "rating", "reaction", "comment", "created_at"]

    with get_connection() as conn:
        total = conn.execute(f"SELECT count(*) FROM ({union_sql}) t", params).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT * FROM ({union_sql}) t
            ORDER BY {sort} {order_dir}
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, (page - 1) * page_size],
        ).fetchall()
        responses = [dict(zip(columns, row)) for row in rows]

    return {"responses": responses, "total": total}
