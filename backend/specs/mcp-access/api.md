---
id: mcp-access
experience: mcp-access
directive: low
status: implemented
created: 2026-09-15
updated: 2026-09-15
---

# AI Agent Access — Backend Architecture Spec

## Experience this implements
See: `design/mcp-access/experience.md` (Part 1 — Connections & Permissions; Part 2 — What a
Good Answer Feels Like).

## Taxonomy this uses
See `design/market-health/job-classification.md` (`role_category`, `specialization`, `level`,
`track`, `skill_group`) and `backend/EMPLOYMENT_EVENTS.md` (`event_type`, `direction`,
`confidence`). This spec **reuses these enums verbatim** — it never redefines or parallels
them. Every MCP tool parameter that names a taxonomy dimension uses exactly the values those
two documents already define.

## Deployment note
**Deployed 2026-09-15**, at the user's explicit request (local Postgres wasn't running, and
"maybe better to deploy and test in remote then"). Mounted on the existing `api` service, no
new Railway service — see `DEPLOYMENT.md`'s "Bring-your-own-AI access" section for the live
URL, env vars (`USER_JWT_SECRET`, `FRONTEND_ORIGIN`, `PUBLIC_BASE_URL`), and the three
production-only bugs a real Claude connection attempt surfaced (none of which any local or
import-level check could have caught): a `/mcp` routing collision, the MCP SDK's session-manager
lifespan not being wired into `main.py`'s startup, and missing OAuth discovery metadata
(RFC 8414/9728). All fixed same day; see `changes/2026-09-13-mcp-ai-agent-access.md`'s Decision
Log for the full sequence.

---

## Why this reuses `market_query.py`, not new query logic

`backend/specs/market-health/api.md` (Business Logic — Conversational data sourcing) already
built four read-only, parameterized query functions for the *in-app* chat feature —
`query_market_data`, `query_compensation_data`, `query_requirements_data`,
`query_employment_events_data` in `backend/src/market_query.py`. These are already exactly what
`design/foundations.md` Principle 9 (Curated Access, Never Raw) demands: named, parameterized,
taxonomy-validated operations, not raw SQL. **This spec's MCP tools are thin wrappers around
these same four functions**, not a second, parallel query layer — the same discipline
`outcomes/job-data-source-flexibility.md` and `outcomes/ai-provider-flexibility.md` already
established ("one adapter, no parallel implementation"). A tool that needs a capability
`market_query.py` doesn't have today (see "What's deliberately not a tool," below) is not
invented here — that would mean trusting new, untested query logic on a public-facing surface
before it's ever been proven against the in-app chat feature.

---

## Data Models

### User (`users` table) — new, first consumer-facing account model in this product

Per the user's direction: a minimal account system, not a full identity platform. The
consumer product (`/api/*`) has had no auth at all until now (`CLAUDE.md`) — only the admin
dashboard has login. This is the first.

| Field | Type | Description |
|---|---|---|
| `id` | `int` (PK) | |
| `email` | `str`, unique | |
| `password_hash` | `str` | Same hashing technique as `admin_auth.py`'s `hash_password()` (bcrypt) — reused for consistency, in a new module (`backend/src/auth.py`), not by importing the admin module, which stays operator-only and conceptually separate. |
| `plan` | `"free" \| "premium"` | Default `"free"`. **How a user becomes `"premium"` is out of scope for this spec** — this platform has no billing/payment integration at all yet (see Out of scope). For now, upgrading is an operator action (a direct DB update), the same honest placeholder `outcomes/llm-spend-is-bounded-and-isolated.md` already uses for "provisioning the cloud billing account itself." |
| `created_at` | `datetime` | |

**Deliberately excluded from v1**: email verification, password reset, magic-link login, OAuth
login via Google/GitHub. Each is a real feature with its own edge cases (email verification
needs an email-sending capability this platform doesn't have at all today); adding any of them
now would be designing for a hypothetical, not what this feature needs to be testable. Plain
email + password is the smallest thing that makes "sign in to your platform account" real.

### McpClient (`mcp_clients` table) — Dynamic Client Registration record

MCP's authorization spec expects a client (Claude, ChatGPT, Gemini CLI, or any other) to
register itself before first use ([RFC 7591](https://www.rfc-editor.org/rfc/rfc7591) Dynamic
Client Registration) rather than this platform pre-configuring every possible client by hand —
the whole point of "any MCP-compatible client," per the outcome.

| Field | Type | Description |
|---|---|---|
| `client_id` | `str` (PK) | Generated on registration, opaque. |
| `client_name` | `str` | Self-reported by the registering client (e.g. `"Claude"`, `"ChatGPT"`) — shown as the "client name + icon" the experience spec's Connected Assistant card needs. Never trusted for anything security-relevant, only display. |
| `redirect_uris` | `JSON` (`str[]`) | Registered callback URLs — validated against on every authorization request, standard OAuth redirect-confirmation. |
| `created_at` | `datetime` | |

No `client_secret` — every MCP client is treated as a **public client** using PKCE (below),
not a confidential one holding a secret. This is deliberate, not an oversight: a desktop/CLI/
browser-embedded AI client can't keep a secret safe, and PKCE is the standard answer to exactly
that ([RFC 7636](https://www.rfc-editor.org/rfc/rfc7636)).

### McpConnection (`mcp_connections` table) — the "Connected Assistant"

The IA's **Connected Assistant** (`design/information-architecture.md` v2.6) is this row.

| Field | Type | Description |
|---|---|---|
| `id` | `str` (PK) | Opaque connection id. |
| `user_id` | `int` (FK → `users.id`) | Whose connection this is. |
| `client_id` | `str` (FK → `mcp_clients.client_id`) | Which registered client this connection is for. |
| `client_name` | `str` | Denormalized copy of `mcp_clients.client_name` **at grant time** — so a Connected Assistant card's label never changes retroactively if the same client re-registers under a different name later. |
| `scopes` | `JSON` (`str[]`) | The scopes actually granted at consent — see Scope model, below. Never re-derived from the client's request; it's what the user actually clicked "Allow" on. |
| `created_at` | `datetime` | Backs the card's "Connected {relative time}." |
| `revoked_at` | `datetime \| None` | `NULL` = active. Set the instant the user clicks "Revoke" — see Business Logic — Revocation, below, for why this column alone (not a cache, not a queue) is what every tool call checks. |

**No `plan_tier` column here.** Plan tier is a property of the *user*, not the connection — a
user has exactly one plan, and every one of their connections reflects it identically. The
Connected Assistant card's plan badge reads `users.plan` live, joined through `user_id`, not a
stored snapshot that could drift from reality.

**On the experience spec's "connection disconnected by the client's own side" edge case**: this
turns out not to be something this platform can observe. OAuth's authorization server (this
platform) is the sole source of truth for whether a grant is active — an external client has no
mechanism to tell this platform "the user disconnected me over there," and this platform has no
way to detect it either. This edge case is **not implemented as its own state**; a connection is
either active or revoked-by-this-platform, full stop. Noted back to the experience spec as a
correction, not a gap — the underlying assumption didn't hold up against how OAuth actually works.

### OAuthToken (`mcp_tokens` table)

| Field | Type | Description |
|---|---|---|
| `token_hash` | `str` (PK) | SHA-256 of the actual bearer token — the raw token is returned to the client once, at issuance, and never stored or logged in the clear, same discipline this platform already applies to nothing-comparable-existing-today but consistent with not storing secrets in the clear anywhere else in this codebase. |
| `connection_id` | `str` (FK → `mcp_connections.id`) | |
| `kind` | `"access" \| "refresh"` | |
| `expires_at` | `datetime` | Access tokens: 1 hour from issuance. Refresh tokens: no expiry — see Business Logic — Token lifetimes, below, for why the *connection*, not the refresh token, is the thing that actually gates access. |
| `created_at` | `datetime` | |

### OAuthAuthorizationCode (`mcp_auth_codes` table)

Short-lived, single-use, per standard OAuth authorization-code flow.

| Field | Type | Description |
|---|---|---|
| `code` | `str` (PK) | Opaque, random. |
| `user_id` | `int` (FK → `users.id`) | Set once the user grants, at the consent step. |
| `client_id` | `str` (FK → `mcp_clients.client_id`) | |
| `scopes` | `JSON` (`str[]`) | What was actually granted. |
| `redirect_uri` | `str` | Must match on exchange, standard OAuth check. |
| `code_challenge` | `str` | PKCE (`S256` only — plain is not accepted). |
| `expires_at` | `datetime` | 10 minutes from issuance. |
| `used_at` | `datetime \| None` | Set on exchange; a code can be exchanged exactly once. |

### McpUsage (`mcp_usage` table) — rate limiting

Same shape and purpose as the existing `chat_paid_usage` table (`AI_INTERACTION_SETTINGS.md`) —
a per-day counter, not an in-memory one, so it survives a restart and is auditable.

| Field | Type | Description |
|---|---|---|
| `connection_id` | `str` (FK → `mcp_connections.id`) | |
| `date` | `date` | |
| `request_count` | `int` | |

`PRIMARY KEY (connection_id, date)` — one row per connection per day, incremented per tool call.

---

## Scope model

Three scopes, matching the plain-language chips the experience spec and `design/visual-design.md`
already designed the frontend for (this spec defines the identifiers those chips translate):

| Scope | Plain-language label (frontend) | Gates |
|---|---|---|
| `jobs.read` | "Can read job demand and skill trends" | `get_job_demand`, `get_skill_demand` |
| `companies.read` | "Can read company employment risk (layoffs, expansion)" | `get_employment_risk`, `list_tracked_companies` |
| `compensation.read` | "Can read salary data" | `get_salary_stats` — **Premium plan only**, see Business Logic — Plan enforcement |

`get_taxonomy` (below) requires no scope — it returns reference metadata (valid parameter
values), not user data, the same way this product's own frontend can always read
`job-classification.md`'s enums without any auth.

A client requests a subset of these three at connection time (Flow B, step 4 of the experience
spec); the user can grant fewer than requested but never more.

---

## OAuth Discovery Metadata

**Added post-deployment, 2026-09-15** — found missing when a real Claude connection attempt
failed at the very first step ("Couldn't register with TMIP's sign-in service"), because
nothing published *where* the endpoints below actually live. A connecting client doesn't guess
these paths — it fetches a well-known discovery document first. Two, per the two RFCs MCP's own
Authorization spec references:

### GET /.well-known/oauth-authorization-server
RFC 8414. Returns `issuer`, `authorization_endpoint`, `token_endpoint`, `registration_endpoint`
(pointing at the three endpoints below), `code_challenge_methods_supported: ["S256"]`,
`token_endpoint_auth_methods_supported: ["none"]` (public clients only), and
`scopes_supported`.

### GET /.well-known/oauth-protected-resource (and the `/mcp`-suffixed variant)
RFC 9728. Tells a client that `/mcp` is protected and names this same origin as its
authorization server (this deployment doesn't separate the two roles). Served at both the bare
well-known path and the resource-path-appended one — different clients probe different
candidates first.

Both are built from a single `PUBLIC_BASE_URL` env var (`mcp_access/well_known.py`) so the two
documents can't drift apart — see `backend/.env.example`. **Exception**: `authorization_endpoint`
deliberately points at `FRONTEND_ORIGIN` (the `web` service's own domain), not `PUBLIC_BASE_URL`
— see "Why the consent step is reached through `web`'s domain, not `api`'s," below. This was
found and fixed post-deployment, against a real Claude connection: the session cookie a user
gets from logging in is scoped to whichever domain the browser believes it talked to, and login
happens through `web`'s domain, so sending the browser straight to `api`'s separate domain for
consent meant the cookie never arrived — login appeared to silently do nothing.

### Why the consent step is reached through `web`'s domain, not `api`'s

`GET/POST /mcp/oauth/authorize` and its unauthenticated redirect to `/login` all have to share
one origin with wherever the login POST itself lands, or the session cookie set by one is
invisible to the other — cookies are scoped by the domain the browser believes it's talking to,
not by which physical service ends up handling the request server-side. Since login
(`POST /api/account/login`) is called via the SPA's own relative fetch (landing on `web`'s
domain), the consent step must be reached the same way: `frontend/vite.config.ts` proxies
`/mcp/*` through to `api`, exactly like it already does for `/api/*`
(`DEPLOYMENT.md`'s "How `web` actually reaches `api`"). `token_endpoint` and
`registration_endpoint` have no such requirement — both are called server-to-server by the
connecting client's own backend, never by the user's browser, so no cookie and no origin
constraint applies to them; they stay on `PUBLIC_BASE_URL` (`api`'s own domain) directly.

## OAuth 2.1 Authorization Flow

Follows [MCP's own authorization spec](https://modelcontextprotocol.io) — OAuth 2.1, PKCE
mandatory, public clients only (no client secret), Dynamic Client Registration. This is a
standards-compliance choice, not a custom scheme: it's what makes "any MCP-compatible client"
in the outcome actually true, since Claude/ChatGPT/Gemini CLI already speak this exact flow.

### POST /mcp/oauth/register

**Purpose**: Dynamic Client Registration (RFC 7591). A client self-registers before its first
user ever connects.

**Auth required**: no

**Request**:
```json
{ "client_name": "Claude", "redirect_uris": ["https://claude.ai/api/mcp/callback"] }
```

**Response**:
```json
{ "client_id": "mcpc_9f2a...", "client_name": "Claude", "redirect_uris": ["https://claude.ai/api/mcp/callback"] }
```

### GET /mcp/oauth/authorize

**Purpose**: The consent step (experience spec Flow B, steps 2-4). Standard OAuth authorization
endpoint.

**Server-rendered, not a JSON endpoint the frontend calls** — resolved here rather than left as
an open question between this spec and `frontend/specs/mcp-access/architecture.md`. This
endpoint returns HTML directly, the same way `backend/specs/pipeline-visibility/api.md`'s
`/admin/*` routes already do (Jinja2, bundled with FastAPI, already a dependency — see External
Dependencies). The consent screen has no client-side interactivity beyond two buttons; giving it
a Vite/React bundle, a second deploy artifact, and a cross-service redirect for a page this
simple would be the "settings surface forced into ceremony it doesn't need" anti-pattern
`design/visual-design.md`'s "What this rules out" already warns against for a different surface
— the same judgement applies here. `frontend/specs/mcp-access/architecture.md` has **no route
for this** — there is no `OAuthConsentPage` in the frontend at all.

**Auth required**: requires a signed-in platform session. If none: redirects to the
**frontend's** `/login?next={this URL's own path+query}` (the consumer login page is a real SPA
page, unlike this endpoint) — the frontend's `LoginForm`, on success, redirects the browser back
to the `next` URL, landing here again, now authenticated.

**Query params**: `client_id`, `redirect_uri`, `response_type=code`, `scope` (space-separated
subset of the three above), `state`, `code_challenge`, `code_challenge_method=S256`.

**Response**: Renders the consent screen (`design/visual-design.md` — "OAuth consent screen") as
a Jinja2 template, resolving `client_id` to `mcp_clients.client_name` server-side (no separate
lookup call needed — this is the same request that already has the id). On **Allow** (a plain
HTML form `POST` to this same path): creates an `OAuthAuthorizationCode` row and the
`McpConnection` row together (in one transaction — a connection never exists without a
corresponding grant event), redirects to `redirect_uri` with `code` and `state`. On **Cancel**:
redirects with `error=access_denied&state=...`; no rows are written — "no partial grant is ever
recorded" (experience spec, Interactions).

### POST /mcp/oauth/token

**Purpose**: Exchanges an authorization code for tokens, or a refresh token for a new access
token.

**Auth required**: no (the code/refresh token itself is the credential; PKCE's
`code_verifier` proves possession)

**Request** (`grant_type=authorization_code`):
```json
{ "grant_type": "authorization_code", "code": "...", "redirect_uri": "...", "client_id": "...", "code_verifier": "..." }
```

**Request** (`grant_type=refresh_token`):
```json
{ "grant_type": "refresh_token", "refresh_token": "...", "client_id": "..." }
```

**Response**:
```json
{ "access_token": "...", "refresh_token": "...", "token_type": "Bearer", "expires_in": 3600, "scope": "jobs.read companies.read" }
```

A `refresh_token` grant checks the parent `McpConnection.revoked_at` **before** issuing a new
access token — a revoked connection can never mint a fresh token, closing the one path that
would otherwise let a revoked client silently keep working past its last access token's expiry.

**Errors**:
| Code | Reason |
|---|---|
| 400 | Malformed request, expired/already-used code, `code_verifier` mismatch |
| 401 | Refresh token unknown, or its connection is revoked |

---

## MCP Tools

Exposed over the MCP protocol at a single endpoint, **`POST /mcp`** — and, deliberately, also
`POST /mcp/`; both work identically, with no redirect between them either way. This needed two
attempts to get right, against two separate real Claude connection failures:

1. First fix: always *publish* the URL with a trailing slash (`mcp_access/well_known.py`'s
   `MCP_ENDPOINT_URL`), since Starlette's `Mount` can only match `/mcp/` or deeper — a bare
   `/mcp` only "worked" via a 307 redirect that curl follows silently but a real client does
   not. This fixed tool calls (which had been retrying the bare form and giving up), but not
   the *next* failure: the literal URL a user pastes when adding a connector in Claude is
   `/mcp` — no client normalizes that against published metadata, a human just types the
   URL that looks complete without a slash — and the very first "is this a valid MCP server"
   probe failed outright, no retry.
2. Real fix: `mcp_access/server.py`'s `NormalizeMcpPathMiddleware`, applied to the whole app in
   `main.py`, rewrites a bare `/mcp` to `/mcp/` **before Starlette's own routing runs at all** —
   so both forms match on the first request, no redirect ever generated, and no assumption
   about client behavior (follows redirects? retries?) is needed at all. The "publish with a
   trailing slash" habit stays as harmless extra care, not the thing actually holding this up.

This is per the MCP spec's own transport — JSON-RPC over HTTP; this platform does not invent a
second, REST-shaped tool API alongside it. Every tool call carries a Bearer access token; every
tool implementation runs the same three checks before touching data — see Business Logic, below.

Six tools. Each is a genuine data primitive already proven inside this platform's own chat
feature (`backend/specs/market-health/api.md`) — nothing here is new, untested query logic.

### `get_taxonomy`
**Scope**: none. **Purpose**: returns the canonical enum values so a calling AI never has to
guess a valid parameter (Principle 9 — "the platform's own taxonomy stays authoritative").
Returns `role_category`, `specialization`, `level`, `track`, `skill_group` (from
`job-classification.md`) and `event_type`, `direction`, `confidence` (from
`EMPLOYMENT_EVENTS.md`), each as `{ "value": ..., "label": ... }` pairs — machine value plus the
plain-language label this platform already uses for it.

### `get_job_demand`
**Scope**: `jobs.read`. **Wraps**: `query_market_data`.
**Parameters**: `group_by` (one or more of `role_category`, `specialization`, `level`, `track`,
`country`, `month`), `role_category`, `specialization`, `level`, `track`, `country`,
`date_from`, `date_to` — identical to the existing tool's own parameters, same closed-set
validation.
**Response** (self-describing, per Part 2's binding contract — see "Response envelope," below):
```json
{
  "data": { "rows": [{ "role_category": "Designer", "specialization": "Product Designer", "count": 33 }] },
  "meta": {
    "unit": "count of live job postings first observed by this platform's ingestion",
    "scope": { "role_category": "Designer", "specialization": "Product Designer", "country": null },
    "time_window": { "from": "2026-07-20", "to": "2026-07-22", "label": "Jul 20–22, 2026" },
    "source": "Company job boards on Greenhouse, Lever, and Ashby — classified by this platform",
    "taxonomy_version": "2026-08-11",
    "total_matching": 297
  }
}
```

### `get_salary_stats`
**Scope**: `compensation.read` (**Premium only**). **Wraps**: `query_compensation_data`.
**Parameters**: `role_category`, `specialization`, `level`, `track`, `country`.
**Response**: same envelope shape; `meta.unit` states currency and period explicitly (e.g.
`"annual salary in USD"`) and `data` carries `structured_count`/`parsed_count` split exactly as
the wrapped function does, so the calling AI can honestly caveat a `"parsed"`-only figure rather
than presenting every number with equal confidence.

### `get_skill_demand`
**Scope**: `jobs.read`. **Wraps**: `query_requirements_data`.
**Parameters**: `role_category`, `specialization`, `level`, `track`, `country`, `skill_group`,
`raw_skill`, `work_arrangement`, `education_required`.
**Response**: same envelope; `meta.unit` states `"% and count of matching postings"` and names
`total_matching` as the real denominator, carrying forward the wrapped function's own "the
denominator is postings-with-extraction, not all postings" honesty rule into `meta` explicitly,
so the calling AI can't accidentally compute a percentage against the wrong base.

### `get_employment_risk`
**Scope**: `companies.read`. **Wraps**: `query_employment_events_data`.
**Parameters**: `company`, `sector`, `country`, `date_from`, `date_to`.
**Response**: same envelope; `data.events` carries `confidence` (`confirmed`/`reported`)
per-event, unchanged from the wrapped function — the calling AI is expected to relay that
distinction (per Part 2, "never present with equal certainty"), and `meta` states
`sources_checked` explicitly (already returned by the wrapped function) so a zero-result answer
reads as "checked and found nothing," never as "didn't look."

### `list_tracked_companies`
**Scope**: `companies.read`. **New, thin, no LLM, no existing wrapper** — reads the same static
curated company→industry lookup `backend/specs/market-health/api.md`'s Business Logic —
Industry tagging already maintains. Lets a calling AI answer "does this cover Company X" before
spending a call on `get_employment_risk` for a company this platform was never going to have
job-posting-side context on anyway. **Note**: this does **not** gate or filter
`get_employment_risk` — that tool answers for any company the registries cover, tracked or not
(`EMPLOYMENT_EVENTS.md` — "no relationship to `raw_postings`"). This tool is metadata only.

### What's deliberately not a tool

- **Company-level job-demand** (e.g. "how many roles is Company X hiring for") — `query_market_data`
  has no `company` filter today (`raw_postings.company` exists in the database but was never
  exposed to the *in-app* chat tool either). Adding it here would mean trusting new,
  never-before-shipped filter logic on a public surface first — backwards from how every other
  capability in this platform has been proven. **Open question for a future change**, not solved
  here.
- **`get_market_snapshot` / any pre-composed report** — the outcome and its research signal are
  explicit: *"expose data primitives, not pre-written reports."* A calling AI builds its own
  snapshot by calling `get_job_demand` grouped by `month` and reading the most recent bucket,
  exactly as `design/mcp-access/experience.md` Part 2 describes ("the user is doing the
  comparing by asking, not this platform pre-building a comparison feature").
- **Any "compare X vs Y" tool** — same reasoning; the calling AI calls `get_job_demand` (or any
  tool) once per thing being compared and composes the comparison itself.

---

## Response envelope (binding on every tool above)

Every tool response is `{ "data": {...tool-specific...}, "meta": {...} }`. `meta` is what makes
`design/mcp-access/experience.md` Part 2's data-legibility contract real — it travels inside the
same JSON payload the calling AI reads, so nothing depends on the AI fetching a second reference
document or remembering context from an earlier call:

| `meta` field | Always present? | Purpose |
|---|---|---|
| `unit` | always | States what a bare number in `data` actually counts, in words |
| `scope` | always | Every filter that was actually applied, by name — including ones the caller left as "no filter," stated as `null`, not omitted |
| `time_window` | always | `from`/`to` plus a `label` in words — never a bare ISO pair with no human-readable form |
| `source` | always | Plain-language provenance, equivalent to what the Reasoning Panel gives a human, for an AI that gets asked "how do you know that?" |
| `taxonomy_version` | when the tool returns taxonomy-classified data | Lets a caller (or a human debugging a discrepancy) know which taxonomy revision produced these labels |
| `total_matching` / `sources_checked` | tool-specific | Carried straight through from the wrapped function — never dropped, since it's what lets an AI state a real denominator or a real "we checked and found nothing" |

Category/role/skill/event-type **values** inside `data` are always this platform's own
plain-language taxonomy strings (`"Designer"`, not `"DESIGNER"` or `0`) — never an internal code
the calling AI would have to look up. This is what `get_taxonomy` documents and every other tool
is bound to use consistently.

### Curated error responses

Never a raw HTTP 403/404/429 with no body the calling AI has to interpret. Every error is:
```json
{ "error": { "type": "scope_denied" | "plan_required" | "rate_limited" | "revoked" | "no_data", "message": "..." } }
```

| `type` | HTTP status | `message` example |
|---|---|---|
| `scope_denied` | 403 | "This connection doesn't have permission to read salary data. Reconnect and grant 'Can read salary data' to use this." |
| `plan_required` | 403 | "Salary data requires a Premium plan. This account is on the Free plan." |
| `rate_limited` | 429 | "This connection has reached its daily limit of {N} requests. It resets at {time}." |
| `revoked` | 401 | "Access to this platform was revoked." |
| `no_data` | 200 (not an error status — a real, honest answer) | "No employment events found for this company across the sources we check (Eurofound ERM, US WARN, UK Companies House, SEC EDGAR)." |

`no_data` is intentionally a `200`, not an error — matching the in-app chat's own
`NO_DATA:`-marker convention (`backend/specs/market-health/api.md` — Business Logic, step 2): a
real, honest "nothing found" is a successful answer, not a failure.

---

## Account & Connections Endpoints (this product's own frontend, not the MCP protocol)

These back the Settings tab (`design/mcp-access/experience.md` Part 1) and are called by
`frontend/specs/mcp-access/architecture.md`, not by an external MCP client.

### POST /api/account/signup
**Request**: `{ "email": "...", "password": "..." }` · **Response**: sets the session cookie
(see Business Logic — Session auth), `{ "id": 1, "email": "...", "plan": "free" }`.
**Errors**: `400` invalid email/weak password, `409` email already registered.

### POST /api/account/login
**Request**: `{ "email": "...", "password": "..." }` · **Response**: same shape as signup.
**Errors**: `401` wrong email/password (deliberately the same message for "no such email" and
"wrong password" — never reveal which one was wrong).

### POST /api/account/logout
Clears the session cookie. No body.

### GET /api/account/me
**Auth required**: yes. Returns the signed-in user's `id`, `email`, `plan`.

### GET /api/account/connections
**Auth required**: yes. **Purpose**: the Connections List (experience spec Part 1, Flow C).
**Response**:
```json
{
  "connections": [
    { "id": "conn_a1", "client_name": "Claude", "scopes": ["jobs.read", "companies.read"], "created_at": "2026-09-10T14:00:00Z", "revoked_at": null }
  ],
  "plan": "free"
}
```
`plan` is returned once, alongside the list, not per-connection — see Data Models note above.

### DELETE /api/account/connections/{id}
**Auth required**: yes, and the connection must belong to the signed-in user.
**Purpose**: Revoke (experience spec Flow C, steps 2-4). Sets `revoked_at = now()`. Also deletes
every `mcp_tokens` row for that connection outright (not merely marking them — belt-and-braces;
the live `revoked_at` check alone is what actually guarantees immediate effect, per Business
Logic below, but deleting the tokens too means there's nothing left to leak even in a bug).
**Response**: `204`. **Errors**: `404` if the connection doesn't exist or isn't this user's.

---

## Business Logic

**Revocation — immediate, no grace window (Principle 9 / "Curated Access Integrity" metric,
`design/foundations.md`).** Every `/mcp` tool call, and the token endpoint's refresh grant,
performs a **live** `SELECT revoked_at FROM mcp_connections WHERE id = ...` — never a cached or
in-memory check, never a check only at token-issuance time. This is the entire mechanism: there
is no separate revocation list, no queue, no eventual-consistency window to reason about. The
very next call after a revoke sees `revoked_at IS NOT NULL` and returns the curated `revoked`
error. This is intentionally the simplest possible design that satisfies "immediate" exactly —
a cache would only ever reintroduce the grace window the outcome explicitly rules out.

**Scope enforcement.** Each tool declares the one scope it requires (`get_taxonomy` requires
none). Before running the wrapped query function, the handler checks the requesting
connection's `scopes` array. A mismatch returns `scope_denied`, not a filtered/partial result —
never silently omitting data the connection isn't allowed to see while returning `200` as if the
request had simply matched nothing.

**Plan enforcement.** `get_salary_stats` additionally checks `users.plan == "premium"` for the
connection's `user_id`, live (joined through `mcp_connections.user_id`, never cached) — a
free-plan user who upgrades to premium sees every existing connection gain access on its very
next call, with no separate step to "refresh" a connection's entitlement.

**Rate limiting.** Before running any tool, increment (or insert) today's `mcp_usage` row for
the connection; if the resulting count exceeds the plan's daily cap
(`MCP_FREE_DAILY_REQUEST_CAP`, `MCP_PREMIUM_DAILY_REQUEST_CAP` — new settings in
`ai_interaction_settings.py`, same module and naming convention as the existing
`CHAT_PAID_DAILY_REQUEST_CAP`), return `rate_limited` with the exact reset time (start of the
next UTC day). The increment happens **before** the tool runs, not after — the same
"enforced before each call, not reconciled after" discipline
`outcomes/llm-spend-is-bounded-and-isolated.md` already requires of every paid workload, applied
here even though this feature spends no LLM money itself (protecting database/compute load, not
a dollar budget).

**Session auth (this platform's own UI, not MCP).** A signed-in user gets an `httpOnly`,
`Secure`, `SameSite=Strict` JWT cookie, signed with a new `USER_JWT_SECRET` — **a separate
secret from `ADMIN_JWT_SECRET`**, matching this product's established discipline of one
credential per concern (the same reasoning behind separate Gemini keys per workload,
`outcomes/llm-spend-is-bounded-and-isolated.md`). A bug or leak in the admin JWT secret must
never be able to forge a consumer session, or vice versa.

**Taxonomy validation.** Every tool parameter that names a taxonomy value (`role_category`,
`level`, `track`, `specialization`, `skill_group`, `event_type`, etc.) is validated against the
exact closed sets `job-classification.md` / `EMPLOYMENT_EVENTS.md` already define — the same
validation `market_query.py`'s existing functions already perform for the in-app chat tool. An
invalid value is a `400`, not a best-effort guess.

**No LLM calls anywhere in this feature.** Every tool above is a direct database read via
`market_query.py`'s existing functions (or, for `get_taxonomy`/`list_tracked_companies`, a
static lookup). This is deliberate and load-bearing for the outcome's core premise — the
external AI does its own reasoning, on the caller's own subscription; this platform's part of
the round-trip spends no model tokens and touches `backend/src/llm/` not at all.

---

## External Dependencies

| Dependency | Purpose |
|---|---|
| `mcp==1.9.4` (official Python SDK, [github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)), `sse-starlette==3.0.3` | Protocol-compliant JSON-RPC transport, tool/resource registration — avoids hand-rolling a spec that will keep evolving upstream. **Version verified locally, not assumed**: `mcp`'s 2.x line requires `starlette>=1.x`, which conflicts with this project's existing `fastapi==0.115.0` pin (`starlette<0.39.0`); 1.9.4 is the oldest 1.x release confirmed to still expose `FastMCP.streamable_http_app()` (absent in 1.x releases checked below 1.8.0) while satisfying that constraint (every 1.x release only requires `starlette>=0.27`). See `requirements.txt`'s own comment for the full finding. |
| `PyJWT` | Already a dependency (admin auth) — reused for the new consumer session cookie |
| `bcrypt` (or whatever `admin_auth.py` already uses — reuse, don't add a second hashing library) | Password hashing for `users.password_hash` |
| Jinja2 | Already a dependency (bundled with FastAPI, used by `admin_main.py`) — reused for the one server-rendered page this feature needs, the OAuth consent screen |

No new external service, no new Gemini/LLM credential, no new Railway service (Deployment
note, above).

---

## Tech Decisions

- New module tree **`backend/src/mcp_access/`** (corrected during implementation — this section
  originally said `backend/src/mcp/`; renamed because `mcp` is also the name of the official
  Model Context Protocol Python SDK this package imports, and `backend/src` sits on `sys.path`,
  so a same-named local package would shadow the real library for every module in this codebase)
  — mirrors the adapter-abstraction spirit already established for `llm/` and the source
  adapters, without touching either: `mcp_access/server.py` (protocol handler + tool
  registration), `mcp_access/tools.py` (the six tools, each a thin wrapper calling into
  `market_query.py`), `mcp_access/oauth.py` (the three OAuth endpoints), `mcp_access/envelope.py`
  (the shared `meta`-building helper so every tool builds its envelope the same way instead of
  six near-duplicate implementations), `mcp_access/db_helpers.py` (users/connections/tokens/
  usage — the new tables' only data-access layer).
- New module `backend/src/auth.py` — consumer session + password hashing, separate from
  `admin_auth.py` (different secret, different cookie, different audience), same technique.
- `mcp_clients`, `mcp_connections`, `mcp_tokens`, `mcp_auth_codes`, `mcp_usage`, `users` — six
  new tables, `CREATE TABLE IF NOT EXISTS` in the existing schema-on-startup pattern
  (`backend/src/db.py`), additive only, no change to any existing table.
- The MCP endpoint is mounted at `/mcp` on the **existing** `api` service (`main.py`) — not a
  new Railway service — so it shares the same `DATABASE_URL` and deploys alongside the rest of
  the consumer API when this is eventually deployed (Deployment note, above; not now).
- **`mcp_access/server.py` must never use `from __future__ import annotations`**, unlike every
  other module in this codebase. Confirmed the hard way during implementation: `mcp`'s
  `Tool.from_function` inspects each tool parameter's *runtime* annotation object directly
  (`get_origin(...)`, then `issubclass(...)`) rather than resolving stringified ones — with the
  future import active, every annotation becomes a string, the union-type skip never fires, and
  `issubclass(<string>, Context)` raises `TypeError: issubclass() arg 1 must be a class` on the
  first tool with any parameters. Reproduced, fixed by omitting the import in that one file, and
  verified end-to-end (`main.py` imports cleanly, all six tools plus `get_taxonomy` register).

## Open Questions resolved here (carried from the experience spec)

- **Self-serve upgrade path inside the external AI's own interface, or point back to this
  product?** → **Point back to this product only, for v1.** This platform has no
  billing/payment integration of any kind yet (see `users.plan`, above) — there is nothing to
  self-serve into. `plan_required`'s `message` states the plan requirement plainly; it does not
  link anywhere, since there's no upgrade flow yet to link to. Revisit once a real billing flow
  exists.
- **Should a connection ever expire on its own?** → **No, not the grant itself.** Access tokens
  expire in 1 hour (forcing routine refresh, standard OAuth hygiene); refresh tokens don't
  expire on a timer. The connection (the grant a user sees on the Settings tab) persists until
  the user explicitly revokes it — matching the outcome's success criteria, which specify
  explicit revoke and say nothing about auto-expiry.

## Sequencing check (carried from `changes/2026-09-13-mcp-ai-agent-access.md`)

Checked `changes/2026-09-01-requirements-backlog-batch-catchup.md`: it touches `ingest.py`, the
new `batch_jobs` table, and the requirements-extraction *write* path. This spec's
`get_skill_demand` tool only calls `query_requirements_data` — an existing, already-shipped
*read* function in `market_query.py` that the batch catch-up work does not modify. **No file-level
overlap.** Safe to implement in parallel, as `changes/2026-09-13-mcp-ai-agent-access.md`
anticipated.

## Out of scope

- Billing/payment integration, or any mechanism for a user to actually become `"premium"` other
  than an operator manually updating the `users.plan` column — a future change, once this
  platform has any billing at all.
- Email verification, password reset, and any login method besides email + password (magic
  link, OAuth-login via a third party) — the smallest account system that makes OAuth consent
  real, not a full identity platform.
- Adding a `company` filter to `query_market_data` (see "What's deliberately not a tool") — a
  separate, future change to the *shared* query layer both this feature and the in-app chat
  would benefit from, not something to bolt on only for MCP callers.
- Any tool that pre-composes a report, summary, or comparison — per Principle 9 and the
  outcome's explicit "data primitives, not pre-written reports" direction.
- ~~Deploying this feature anywhere~~ — done 2026-09-15, see Deployment note, above.
