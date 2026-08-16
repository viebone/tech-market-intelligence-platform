---
id: pipeline-visibility
experience: pipeline-visibility
directive: low
status: ready
created: 2026-08-16
---

# Pipeline Visibility — Backend Architecture Spec

## Experience this implements
See: `design/pipeline-visibility/experience.md`

## Deployment topology
See: `changes/2026-08-13-admin-pipeline-dashboard.md` Decision Log (2026-08-14) for the full
reasoning. Summary: a **new Railway service**, `admin`, rooted at the same `backend/`
directory as the existing `job-sync` and planned `api` services (`DEPLOYMENT.md`), with its
own start command and its own generated domain — genuine domain-level isolation from the
consumer-facing `web` app, on top of authentication (below). New entry point:
`backend/src/admin_main.py`. Server-renders its own HTML via Jinja2 templates — no separate
`frontend/` build, no JSON API consumed by client-side JS for the core views. This spec's
"API Endpoints" are therefore page routes returning HTML, not a JSON API — a deliberate
adaptation of this spec's usual JSON-endpoint format to match the decided architecture (see
Tech Decisions).

---

## Auth decision

**Decided: JWT-based login + httpOnly session cookie, not a bare shared-secret Basic Auth.**

Reasoning: this product's root `CLAUDE.md` already names JWT as the intended backend auth
mechanism, and `backend/specs/market-health/api.md` explicitly anticipated this moment —
*"No auth middleware in v1. Add it as a separate layer when needed."* Since this is a new,
standalone, domain-isolated service (not a quick patch on an existing one), it should follow
the product's already-stated direction rather than silently introducing a different pattern
(Basic Auth) with no stated reason. A real login screen + session cookie is also a better fit
for a server-rendered dashboard the operator keeps a browser tab open to, than re-sending
Basic Auth credentials on every request.

This stays deliberately minimal for a single operator — no user table, no registration flow,
no password reset flow, no refresh tokens:

- One operator identity, no user table. The password is a bcrypt hash stored in an env var
  (`ADMIN_PASSWORD_HASH`), not a database row.
- `POST /admin/login` verifies the submitted password against the hash and, on success,
  issues a JWT (signed with `ADMIN_JWT_SECRET`, a separate env var) with a fixed `sub` claim
  (e.g. `"operator"`) and a 24-hour expiry.
- The JWT is set as an `httpOnly`, `Secure`, `SameSite=Strict` cookie — never exposed to
  client-side JS, never sent as a bearer token from a script.
- Every route except `GET/POST /admin/login` requires a valid, unexpired JWT cookie; a
  missing/invalid/expired one redirects to `/admin/login`, never renders any dashboard content
  or data.
- Expiry after 24 hours requires re-entering the password — no silent refresh. Simple and
  sufficient for one operator; revisit only if this becomes actual friction in practice.

---

## Data Models

No new tables. This spec is entirely READ-only over tables already documented in
`backend/specs/market-health/api.md`: `raw_postings`, `classifications`,
`posting_requirements`, `posting_skills`, `posting_languages`, `ingestion_runs`. See that
spec for full field definitions — not repeated here.

**One additive column, needed to honestly answer the experience spec's "which ingestion run
touched it" requirement (`design/pipeline-visibility/experience.md`, User Flow step 5):**

### RawPosting — addition
| Field | Type | Description |
|---|---|---|
| `ingestion_run_id` | `int \| None` (FK → `ingestion_runs.id`) | **New.** The run that first fetched and inserted this posting. `NULL` for existing rows (backfilled `NULL`, same pattern as every prior migration in `backend/specs/market-health/api.md` — e.g. `source_ref`/`company` for legacy Adzuna rows) and honestly shown as "predates run tracking" in the Detail view, never guessed or approximated from `fetched_at` timestamps. Populated going forward in `raw_postings.insert_new_postings()` at insert time. |

Classification and successful requirements extraction already carry their own honest
provenance (`classified_at`/`model`/`taxonomy_version`, `extracted_at`/`model`) without
needing their own run-FK — a posting's Detail view composes "ingested by run #N" (new FK,
exact) with "classified at {classified_at} using {model}, taxonomy {taxonomy_version}" and
"requirements extracted at {extracted_at} using {model}" (existing fields, exact) rather than
needing every table to carry its own run reference.

### PostingRequirementsFailure (`posting_requirements_failures` table) — new, additive
One row per posting **currently** in a failed state — deleted the moment that posting's
`posting_requirements` row is finally written. Never coexists with a `posting_requirements`
row for the same `posting_id`; the two tables together fully determine Requirements Status
(see "Requirements Status" section above).

| Field | Type | Description |
|---|---|---|
| `posting_id` | `str` (PK, FK → `raw_postings.id`) | Same "at most one row per posting" discipline as `posting_requirements.posting_id`, but here `PRIMARY KEY` means "currently failing," not "extracted at most once" — the row is deleted and can be recreated if the posting fails again after a transient earlier success attempt was itself never recorded (it wasn't a failure). |
| `error` | `str` | The error message from the most recent failed attempt. Overwritten on each new failure — only the latest matters for debugging, not a full history. |
| `attempt_count` | `int` | How many consecutive failed attempts, for visibility ("failed 3 times") — informational only, does not itself stop or throttle retries; the existing retry/backoff policy in `requirements.py` is unchanged by this table's existence. |
| `last_attempted_at` | `datetime` | |
| `model` | `str` | Provider/model that produced the failing attempt, same provenance pattern as every other table's `model` field. |

---

## Requirements Status — including per-posting failure tracking

`design/pipeline-visibility/experience.md`'s Edge Cases section calls for a per-posting
**"Failed"** Requirements Status, distinct from "Pending," with "the recorded error visible
in that posting's Detail view."

Checked against the actual pipeline (`backend/specs/market-health/api.md` — Business Logic,
requirements extraction): **no per-posting extraction failure was recorded before this
spec.** `posting_requirements` gets a row only on success; a posting whose extraction failed
simply had no row and was picked up again by `get_all_needing_requirements()` on the next
run, indistinguishable from a posting merely waiting its turn. Only run-level failures were
recorded (`ingestion_runs.error_message`, per-source/company entries in `terms_processed`) —
never attributed to a specific posting.

**Decided (2026-08-16, stakeholder request): add real per-posting failure tracking now**,
via one small additive table — see `PostingRequirementsFailure` under Data Models. This is a
genuine addition to the existing ingestion pipeline's write path
(`backend/src/requirements.py`), not just a new read surface for this dashboard — flagged
explicitly since it means `/implement-backend` for this spec touches the real extraction
pipeline, not only new `/admin/*` routes.

Four states now genuinely exist:

| Requirements Status | Meaning | Derived from |
|---|---|---|
| `Extracted` | Has a `posting_requirements` row | `posting_requirements.posting_id` exists |
| `Failed` | Extraction attempted and failed at least once, not yet extracted | `posting_requirements_failures.posting_id` exists |
| `Not eligible` | `role_category` is `other`/`unknown` — excluded from the pipeline entirely | `classifications.role_category` |
| `Pending` | Eligible, no attempt recorded yet | Everything else |

A posting can move `Pending → Failed → Pending → ... → Extracted` — failure does **not**
remove a posting from the retry backlog (`get_all_needing_requirements()`'s selection logic
is unchanged); it only makes past failures visible instead of silent. The failure row is
deleted the moment extraction finally succeeds — `Extracted` and `Failed` are mutually
exclusive, never shown as both.

---

## API Endpoints

All routes below are server-rendered HTML pages (Jinja2), not a JSON API — see Deployment
topology. "Response" describes the template and the data passed into it, not a JSON body.
All routes except login require the auth cookie (see Auth decision) — an invalid/missing
cookie redirects (`303`) to `/admin/login` before any data is queried.

### GET /admin/login
**Purpose**: Render the login form.
**Auth required**: no
**Response**: `login.html` — a single password field and submit button. No dashboard chrome.

### POST /admin/login
**Purpose**: Verify the submitted password, issue the session cookie, redirect to Overview.
**Auth required**: no
**Request** (form-encoded): `{ "password": str }`
**Response**: `303` redirect to `/admin/` with `Set-Cookie` on success; `login.html`
re-rendered with an inline error on failure. No distinction in the error message between
"wrong password" and any other failure mode — nothing about the operator identity is ever
disclosed.
**Errors**:
| Code | Reason |
|---|---|
| 401 | Wrong password (rendered inline, not a raw HTTP error page) |

### POST /admin/logout
**Purpose**: Clear the session cookie.
**Auth required**: yes
**Response**: `303` redirect to `/admin/login`, cookie cleared.

### GET /admin/
**Purpose**: Overview — summary counts, classification distributions, taxonomy version
breakdown, requirements coverage, and the most recent ingestion run, per
`design/pipeline-visibility/experience.md` User Flow step 2.
**Auth required**: yes
**Response**: `overview.html`, rendered with:
```json
{
  "totals": { "total_postings": 5105, "fully_indexed": 2143, "requirements_pending": 2760, "requirements_failed": 91, "requirements_not_eligible": 111 },
  "classification_distribution": {
    "role_category": [{ "value": "Engineer", "count": 2201 }, "..."],
    "level": [{ "value": "senior", "count": 251 }, { "value": "unknown", "count": 270 }, "..."],
    "track": ["..."],
    "specialization": ["..."],
    "classification_confidence": [{ "value": "high", "count": 1890 }, "..."]
  },
  "taxonomy_version_breakdown": [
    { "version": "2026-08-11", "count": 2143, "is_current": true },
    { "version": "2026-06-13", "count": 2962, "is_current": false }
  ],
  "requirements_coverage": { "extracted": 82, "eligible": 4994, "pct": 1.6 },
  "skill_group_distribution": [{ "value": "Frontend", "count": 340 }, "..."],
  "latest_run": { "id": 412, "started_at": "2026-08-15T06:00:00Z", "status": "success", "total_fetched": 340, "total_inserted": 12, "total_classified": 1314, "budget_reached": true }
}
```

### GET /admin/postings
**Purpose**: Filterable, sortable, paginated postings table, per
`design/pipeline-visibility/experience.md` User Flow steps 3–4 and Interactions.
**Auth required**: yes
**Query params**:
| Param | Type | Default | Notes |
|---|---|---|---|
| `role_category` | `str` | none | Exact match against closed set |
| `level` | `str` | none | Exact match |
| `track` | `str` | none | Exact match |
| `specialization` | `str` | none | Exact match |
| `classification_confidence` | `str` | none | Exact match |
| `taxonomy_version` | `str` | none | Exact match |
| `requirements_status` | `"extracted" \| "pending" \| "failed" \| "not_eligible"` | none | See "Requirements Status" above |
| `source` | `str` | none | `"greenhouse" \| "lever" \| "ashby" \| "adzuna"` |
| `search` | `str` | none | `ILIKE` against `raw_postings.title` and `company`, debounced client-side before the GET fires |
| `sort` | `str` | `"fetched_at"` | Whitelisted closed set: `fetched_at`, `company`, `role_category`, `level`, `classification_confidence`, `taxonomy_version` — same "validate against a closed set" discipline as `role_category` itself, to keep the column name out of raw SQL construction |
| `dir` | `"asc" \| "desc"` | `"desc"` | |
| `page` | `int` | `1` | |
| `page_size` | `int` | `50` | |
**Response**: `postings.html`, rendered with the filtered/sorted/paginated row list, the
active filter chips, total match count, and pagination controls. Each row links to
`/admin/postings/{posting_id}`.

### GET /admin/postings/{posting_id}
**Purpose**: Full detail for a single posting, per
`design/pipeline-visibility/experience.md` User Flow step 5.
**Auth required**: yes
**Response**: `posting_detail.html`, rendered with:
```json
{
  "posting": { "id": "greenhouse:acme-corp/123456", "source": "greenhouse", "company": "acme-corp", "title": "Senior Product Designer", "fetched_at": "2026-08-14T06:03:11Z", "country": "US", "city": "San Francisco", "salary_min": 140000, "salary_max": 180000, "salary_confidence": "structured", "raw_response": { "...": "verbatim source JSON" } },
  "ingested_by_run": { "id": 409, "started_at": "2026-08-14T06:00:00Z" },
  "classification": { "role_category": "Designer", "specialization": "Product Designer", "level": "senior", "track": "ic", "classification_confidence": "high", "taxonomy_version": "2026-08-11", "model": "gemini/gemini-2.5-flash", "classified_at": "2026-08-14T06:12:03Z" },
  "requirements": { "status": "extracted", "education_level": "bachelors", "education_required": "preferred", "equivalent_experience_accepted": true, "years_experience_min": 5, "work_arrangement": "hybrid", "responsibilities_summary": "...", "other_requirements": "...", "extracted_at": "2026-08-14T06:14:00Z", "model": "gemini/gemini-2.5-flash" },
  "skills": [{ "raw_skill": "Figma", "skill_group": "Design tooling", "requirement_level": "must_have" }, "..."],
  "languages": [{ "language": "English", "requirement_level": "required" }]
}
```
`ingested_by_run` is `null` for rows predating `ingestion_run_id` (see Data Models addition)
— rendered as "predates run tracking," never approximated. `requirements` is `null` when
`status` is `"pending"` or `"not_eligible"`; when `status` is `"failed"` it instead carries
`{ "status": "failed", "error": "...", "attempt_count": 3, "last_attempted_at": "..." }` from
`posting_requirements_failures`, with no other requirements fields populated.
**Errors**:
| Code | Reason |
|---|---|
| 404 | No posting with that id |

### GET /admin/runs
**Purpose**: Ingestion run history, per `design/pipeline-visibility/experience.md` User Flow
step 6.
**Auth required**: yes
**Query params**: `page` (`int`, default `1`), `page_size` (`int`, default `25`)
**Response**: `runs.html` — one row per run: `started_at`, `status`, `total_fetched`,
`total_inserted`, `total_classified`, `requirements_extracted`, `budget_reached`,
`other_rate`. Each row links to `/admin/runs/{run_id}`.

### GET /admin/runs/{run_id}
**Purpose**: Per-source/per-company breakdown for a single run, per
`design/pipeline-visibility/experience.md` Edge Cases ("partially failed run").
**Auth required**: yes
**Response**: `run_detail.html`, rendered with the full `ingestion_runs` row plus
`terms_processed` rendered as a table (`source`, `company`, `fetched`, `inserted`, `error`) —
directly, since that JSON shape is already exactly what the run-detail view needs, no
reshaping required. Legacy pre-2026-08-03 rows (old `{"term": ...}` shape) are rendered with
a "legacy run format" note rather than forced into the current shape.
**Errors**:
| Code | Reason |
|---|---|
| 404 | No run with that id |

---

## Business Logic

**Auth** — see Auth decision above. `verify_password(plain, hash)` via `passlib[bcrypt]`;
`create_session_token()` / `verify_session_token()` via `PyJWT`. A FastAPI dependency
(`require_admin_session`) wraps every route below `/admin/` except `/admin/login`.

**Requirements Status derivation** (used by both Overview aggregates and the Postings
filter):
```
if posting_requirements row exists for posting_id → "extracted"
elif classifications.role_category in ("other", "unknown") → "not_eligible"
elif posting_requirements_failures row exists for posting_id → "failed"
else → "pending"
```
The `not_eligible` check stays ahead of the `failed` check — eligibility is a hard exclusion,
independent of whatever `posting_requirements_failures` happens to hold (a posting that
failed while still classified as `other`/`unknown` shouldn't happen given the extraction
pipeline only ever attempts eligible postings, but the precedence keeps the derivation
correct even if that invariant were ever violated). "Eligible" here must always mean the same
thing it means to the ingestion pipeline itself (`get_all_needing_requirements()`'s existing
exclusion rule, `backend/specs/market-health/api.md`), not a redefinition.

**Recording a failure** (in `backend/src/requirements.py`, the real extraction pipeline, not
just this dashboard's read path): when a posting's extraction attempt exhausts its retry
budget (the same "Retry policy" already documented for classification/ingestion), UPSERT a
row into `posting_requirements_failures` — insert if none exists, otherwise overwrite `error`
and `last_attempted_at` and increment `attempt_count`. When extraction later succeeds for a
`posting_id` that has a failure row, the insert into `posting_requirements` and the delete
from `posting_requirements_failures` happen in the same transaction — the two tables must
never simultaneously hold a row for the same posting.

**Taxonomy "current version"** — read from the same `TAXONOMY_VERSION` constant
`backend/src/classification.py` already defines (`backend/specs/market-health/api.md`'s
Classification table), not duplicated as a separate constant. A row's `taxonomy_version` is
`"current"` iff it equals that constant at request time.

**Requirements coverage %** — `extracted / eligible`, where `eligible` = count of
`classifications` rows with `role_category NOT IN ('other', 'unknown')` — same eligibility
rule as Requirements Status above, not a separate calculation.

**Postings query construction** — filters build a `WHERE` clause from a fixed, named set of
optional exact-match params (never raw user-supplied SQL fragments); `sort` is validated
against the closed whitelist above before being interpolated into `ORDER BY` — the same
"validate against a closed set" discipline `role_category`/`skill_group` already use
elsewhere in this product, applied here to protect against SQL injection via a column name
rather than to validate business data.

**Pagination** — plain `LIMIT`/`OFFSET`. At today's real scale (~5,105 postings,
`backend/specs/market-health/api.md`), this needs no cursor-based pagination or
virtualization; revisit only if that changes materially.

---

## External Dependencies

| Dependency | Purpose |
|---|---|
| PyJWT | Signs/verifies the admin session cookie |
| passlib[bcrypt] | Hashes/verifies the admin password |
| Jinja2 (bundled with FastAPI) | Server-rendered HTML templates for every `/admin/*` route |
| PostgreSQL (already in the project's tech stack) | Same database as the rest of the product — reads only, via the same `DATABASE_URL` internal reference `job-sync`/`api` already use |
| Railway (new `admin` service) | Hosts this service on its own generated domain, same Railway project as `job-sync`/Postgres/`api` |

No new third-party APIs. No LLM calls — this is a pure read/aggregate surface over data
already produced by the existing pipeline.

---

## Tech Decisions

- **New Railway service `admin`**, `rootDirectory: backend/` (same directory as `job-sync`
  and the planned `api` service — see `DEPLOYMENT.md`), start command
  `uvicorn admin_main:app --host 0.0.0.0 --port $PORT`, restart policy `ALWAYS` (long-running,
  unlike `job-sync`'s one-shot cron). New env vars on this service only:
  `ADMIN_PASSWORD_HASH`, `ADMIN_JWT_SECRET`, plus the existing `DATABASE_URL` internal
  reference. Needs its own generated domain (`generate-domain`), never linked from the `web`
  service's public bundle.
- **`backend/src/admin_main.py`** is a separate FastAPI app from `backend/src/main.py` — not
  a router mounted on the consumer-facing API. Keeps the two services' failure domains,
  dependencies, and auth entirely independent; a bug in one can't take down the other.
- **New read/aggregate query functions**, added to the existing DB access modules rather than
  a new module per table (consistent with the existing one-module-per-table pattern in
  `backend/src/`): `raw_postings.py` gains `list_postings(filters, sort, dir, page,
  page_size)`, `get_posting(posting_id)`; `classification.py` gains
  `get_classification_distribution()`, `get_taxonomy_version_breakdown()`;
  `requirements.py` gains `get_requirements_coverage()`, `get_skill_group_distribution()`;
  `ingestion_runs.py` gains `list_runs(page, page_size)`, `get_run(run_id)`.
- **Migrations** (both in `db.py`'s `init_schema()`, same idempotent-guarded pattern as every
  existing migration there):
  `ALTER TABLE raw_postings ADD COLUMN IF NOT EXISTS ingestion_run_id INTEGER REFERENCES
  ingestion_runs(id)` — `raw_postings.insert_new_postings()` updated to accept and set the
  current run's id going forward; existing rows keep it `NULL`.
  `CREATE TABLE IF NOT EXISTS posting_requirements_failures (posting_id TEXT PRIMARY KEY
  REFERENCES raw_postings(id), error TEXT, attempt_count INTEGER, last_attempted_at
  TIMESTAMP, model TEXT)`.
- **`backend/src/requirements.py` (existing ingestion pipeline module, not new code for this
  dashboard) gains**: `record_extraction_failure(posting_id, error, model)` — called from the
  existing retry-exhaustion path; `clear_extraction_failure(posting_id)` — called
  transactionally alongside the existing success-path insert into `posting_requirements`;
  `get_extraction_failure(posting_id)` and `get_failure_count()` for the admin read side.
  This is the one place this spec's implementation touches the real, already-running
  extraction pipeline rather than only adding new `/admin/*` read routes — called out
  explicitly since it changes production ingestion behavior (adds a write), not just this
  dashboard.
- **No client-side JS framework.** Filtering/sorting/pagination on `/admin/postings` are
  plain `<form method="get">` submissions and `<a href="?sort=...">` links — a full page
  reload per interaction, deliberately, matching the "plain traditional dashboard" decision
  from Step 1 of `changes/2026-08-13-admin-pipeline-dashboard.md`. No fetch/XHR, no SPA state.
