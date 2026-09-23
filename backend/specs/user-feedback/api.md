---
id: user-feedback
experience: feedback
directive: low
status: ready
created: 2026-09-23
---

# User Feedback — Backend Architecture Spec

## Experience this implements
See: `design/feedback/experience.md` (product-level rating) and
`design/market-health/data-stories.md` — "Feedback reaction" (feature-level thumbs).

## Data Models

Two new tables. Both anonymous — no user/session identity, no IP address, no user-agent —
matching the outcome's explicit scope decision
(`outcomes/user-feedback-is-heard-and-shapes-the-platform.md`: "not tied to any account
system"). Added to the same startup schema-creation path every other table uses
(`CLAUDE.md`: "the schema is created automatically on startup if missing").

### PlatformFeedback
| Field | Type | Description |
|---|---|---|
| `id` | `int` (PK, autoincrement) | |
| `rating` | `int` | 1–5. Required — enforced at the API layer (Business Logic), not nullable. |
| `comment` | `str \| None` | Optional free text. `NULL` when not provided, never an empty string (Business Logic — normalization). |
| `created_at` | `datetime` (UTC) | Set server-side at insert time — never client-supplied. |

### StoryReaction
| Field | Type | Description |
|---|---|---|
| `id` | `int` (PK, autoincrement) | |
| `story_id` | `str` | The Data Story catalogue `id` this reaction is about (e.g. `market-data-briefing`) — same identifiers `market_data_stories.list_stories()` already returns for routing (`backend/specs/market-health/api.md`). Validated against the live catalogue at request time (Business Logic) — never a fixed enum baked into this table, so a new story added to the catalogue needs no migration here. |
| `reaction` | `str` | `"up" \| "down"`. Required. |
| `comment` | `str \| None` | Optional free text. Meaningful mainly on `"down"` (the experience spec only reveals the field there), but the column accepts either — the frontend, not this table, decides when to show the input. `NULL` when not provided. |
| `created_at` | `datetime` (UTC) | Set server-side, same as `PlatformFeedback`. |

**No update/delete endpoints.** Every submission — including a changed-mind reaction
(clicking the other thumb, or the same thumb twice to clear it) — is its own new row, never an
in-place edit. This keeps the write path trivial (append-only) and preserves a full history for
admin; "current" reaction per story-view is a read-time aggregation question (Business Logic),
not a write-time overwrite.

## API Endpoints

Both endpoints live in the existing consumer-facing app (`backend/src/main.py`), alongside
`/api/market-health/*` — same "no auth on `/api/*`" posture already documented in this
product's root `CLAUDE.md`.

### POST /api/feedback/platform-rating
**Purpose**: Capture a product-level satisfaction rating from the Feedback Panel.
**Auth required**: no
**Request**:
```json
{
  "rating": 4,
  "comment": "Would love a way to save a custom company list."
}
```
`comment` is optional — omit or send `null`.
**Response**: `201 Created`
```json
{ "id": 118, "created_at": "2026-09-23T14:02:11Z" }
```
**Errors**:
| Code | Reason |
|---|---|
| 422 | `rating` missing, non-integer, or outside 1–5 |
| 422 | `comment` exceeds the max length (Business Logic) |

### POST /api/feedback/story-reaction
**Purpose**: Capture a thumbs up/down reaction (and optional comment) for a specific Data
Story.
**Auth required**: no
**Request**:
```json
{
  "story_id": "employment-risk-overview",
  "reaction": "down",
  "comment": "The world map is hard to read on a laptop screen."
}
```
`comment` is optional — omit or send `null`.
**Response**: `201 Created`
```json
{ "id": 245, "created_at": "2026-09-23T14:05:47Z" }
```
**Errors**:
| Code | Reason |
|---|---|
| 422 | `reaction` missing or not one of `"up"` / `"down"` |
| 422 | `story_id` missing |
| 422 | `story_id` doesn't match any entry currently returned by `market_data_stories.list_stories()` |
| 422 | `comment` exceeds the max length (Business Logic) |

## Business Logic

- **Rating bounds**: `rating` must be an integer 1–5 inclusive. Enforced by the request schema
  (Pydantic `Field(ge=1, le=5)`), not by client-side trust — the Feedback Panel already
  disables Submit until a rating is picked, but the server is the real gate.
- **`story_id` validation against the live catalogue**: `POST /api/feedback/story-reaction`
  calls `market_data_stories.list_stories()` (the same function `GET /api/market-health/stories`
  already uses) and rejects any `story_id` not present in that result. This is what keeps the
  table honest as the catalogue grows or a story is ever renamed/removed — a stale or typo'd id
  is refused at write time rather than silently stored and surfacing as a confusing admin row
  later.
- **Comment normalization**: an empty-string or whitespace-only comment is stored as `NULL`,
  not as `""` — keeps "has a written comment" a simple `IS NOT NULL` check for the admin
  aggregate (below).
- **Comment length cap**: 2,000 characters (generous for feedback, real enough to bound storage
  and admin-page rendering — Edge Cases in `design/feedback/experience.md` and
  `design/market-health/data-stories.md` both call for "a generous but real upper bound," this
  is that number). Enforced server-side; the frontend spec may also soft-cap in the UI, but this
  is the source of truth.
- **No dedup, no rate limiting, no one-per-user gate** — matches the experience specs'
  explicit "each submission is its own independent record" edge case. Nothing here reads or
  writes any per-visitor identity, so there is nothing to key a limit on even if one were
  wanted later.
- **"Current" reaction aggregation (read-time, for admin)**: since every reaction is its own
  row (append-only), an admin aggregate that wants "net" sentiment per story computes it from
  all rows in the window being viewed, not from a single "latest" row per some notion of
  visitor identity that doesn't exist here. Concretely: per `story_id`, count of `reaction =
  'up'` rows and count of `reaction = 'down'` rows, over all time (or a future date-range filter
  — not required for v1). This is a straightforward `GROUP BY`, not a dedup step.

## Admin Visibility

Extends the existing operator-only pipeline-visibility admin dashboard
(`backend/specs/pipeline-visibility/api.md`, `backend/src/admin_main.py`) — same JWT-protected,
server-rendered pattern as every other admin view, not a new app or a new auth mechanism.
**This is a spec update to `backend/specs/pipeline-visibility/api.md`, made alongside this one**
(same precedent as `changes/2026-09-18-admin-market-benchmark-visibility.md`, where the scraped-
data-sources spec owned the new tables and pipeline-visibility owned the new admin routes
reading them). See that file for the two new routes: `GET /admin/feedback` (summary — overall
average rating, per-story aggregate) and `GET /admin/feedback/responses` (filterable, paginated,
individual response list). No new outcome needed for this — pipeline-visibility's own outcome
(`outcomes/pipeline-processing-visibility.md`) already covers "the operator can see X without
querying the database" for whatever this product ingests or collects, and user feedback is
exactly that.

## External Dependencies
None. No LLM call, no third-party service — this is a plain CRUD-shaped write path plus a
read-only aggregate, entirely within the existing Postgres database and FastAPI apps.

## Tech Decisions
- New module `backend/src/feedback_storage.py` — `insert_platform_rating()`,
  `insert_story_reaction()`, `list_stories_lookup()` (thin wrapper reusing
  `market_data_stories.list_stories()` for the `story_id` validation, not a duplicate list),
  `get_feedback_summary()`, `list_feedback_responses()` (filter/sort/paginate, same shape as
  `scraping_storage.py`'s existing list functions). Mirrors the existing
  `scraping_storage.py`/`classification.py` separation of "storage module owns the SQL, route
  handler owns HTTP concerns" already used throughout this backend.
- Both new tables are created in the same startup schema-creation function every other table
  goes through (`main.py`'s existing "create schema if missing" path) — no separate migration
  tool in this codebase, consistent with how `market_observations`/`skill_associations` were
  added.
- `story_id` is stored as plain `str`, not a foreign key into a `data_stories` table — there is
  no such table; the catalogue lives in code
  (`design/market-health/data-stories.md` → `market_data_stories.py`), not the database. This
  matches how `market-health/api.md` already treats the catalogue as code-owned, not
  data-owned.

---

## MCP Access Review

Run per Rule 12 (`CLAUDE.md`) / this skill's Step 6 — this product has an MCP layer
(`backend/specs/mcp-access/api.md`). Both new capabilities from this spec get an explicit
decision:

| Capability | Decision | Reason |
|---|---|---|
| `POST /api/feedback/platform-rating` | **Not exposed** | A write action a human performs about their own experience of *this UI* — an external AI agent acting on a user's behalf over MCP has no "satisfaction with the platform" of its own to report, and letting an agent submit ratings on a human's behalf would corrupt the signal this feature exists to collect (Principle 9, Curated Access, Never Raw, is about reads; this is a write-integrity concern specific to feedback data). |
| `POST /api/feedback/story-reaction` | **Not exposed** | Same reasoning — a reaction is a human's opinion of a Data Story's presentation, not a fact an agent could meaningfully report. |
| Feedback summary/aggregate (admin) | **Not exposed** | Operator-only data, same posture as every other pipeline-visibility admin view (`backend/specs/pipeline-visibility/api.md`'s MCP tool layer, `mcp_access/server.py`, wraps `market_query.py`'s consumer-facing read functions only — never admin data). No change to that boundary. |

Recorded here per Rule 12; no change to `ACCESS.md`'s reachability matrix is needed beyond
adding these three rows as "not exposed" with the reasons above (Frontend: yes for the two POST
endpoints via the consumer UI, no for the admin views; Backend API: yes for the two POST
endpoints, no for admin; MCP: no for all three).

## Data Surface Review — completed 2026-09-23

Run via `/data-surface-review` against this spec (`changes/2026-09-23-user-feedback-mechanism.md`,
Step 7). One new data category: user feedback/sentiment (`PlatformFeedback`, `StoryReaction`),
distinct from postings, employment events, and market-benchmark observations.

- **(a) Story / narrative-surface coverage — no surface needed.** This data is meta-data about
  the platform's own reception, not market/job data — it doesn't answer a "what does the job
  market look like" question the way every entry in
  `design/market-health/data-stories.md` does, and forcing it into that catalogue (a "Story 5 —
  What do users think of this platform?") would mix an operator-facing concern into a job-seeker-
  facing surface. No existing story is extended; no new one is added.
- **(b) Admin / operator visibility — updated.** `backend/specs/pipeline-visibility/api.md` gained
  `GET /admin/feedback` (summary) and `GET /admin/feedback/responses` (individual list) as part
  of this same change. This is the data's actual explaining surface.
- **(c) MCP exposure — confirmed via `/mcp-access-review`, recorded in `ACCESS.md`.** All three
  capabilities (both write endpoints + the admin summary) are **not exposed** — see this spec's
  own MCP Access Review section, above, and `ACCESS.md`'s "Market data capabilities" /
  "Operator-only capabilities" tables (rows added 2026-09-23).
- **(d) Ad-hoc query path — deliberately unreachable.** The market-health chat's tool layer
  (`query_market_data`, `query_compensation_data`, etc.) answers questions about the tech job
  market from platform-owned market data (`backend/AI_INTERACTION_SETTINGS.md` — DB-only,
  curated). Feedback data is operator-only meta-data about the tool itself, not market data a
  job seeker would ask the chat assistant about — no query function is registered for it, and
  none should be. This is a deliberate scope boundary, not a gap.
- **Lag:** not applicable — both admin views are live queries (`get_feedback_summary()`,
  `list_feedback_responses()`), no caching or snapshotting involved, so there's no freshness lag
  to state.
