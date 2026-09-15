---
id: mcp-access
experience: mcp-access
directive: low
status: implemented
created: 2026-09-15
updated: 2026-09-15
---

# AI Agent Access — Frontend Architecture Spec

## Experience this implements
See: `design/mcp-access/experience.md` (Part 1 — Connections & Permissions).
Part 2 (What a Good Answer Feels Like) has no frontend at all — it renders inside Claude,
ChatGPT, or Gemini's own interface, never this codebase. Nothing in this document implements it.

## Backend this calls
See: `backend/specs/mcp-access/api.md` — Account & Connections Endpoints (this frontend's own
calls) and OAuth Authorization Flow (the consent screen only; token exchange itself is between
the external AI client and the backend, never this frontend).

## Deployment note
Local only, same as the backend spec — no build/deploy step added here.

---

## Architecture Overview — where this fits, and where it doesn't

The user asked for every part of this app to be clearly differentiated and documented, so this
is stated explicitly rather than left implicit: this feature adds **two new, self-contained
areas** and touches **exactly one file** in the existing app. Everything else in
`frontend/specs/market-health/architecture.md` is unaffected.

| Area | New or existing? | Owns | Touches existing code? |
|---|---|---|---|
| **Market Health** (`features/market-health/`) | Existing, per `frontend/specs/market-health/architecture.md` | The three-column conversational product — Task Panel, Working Space, and the Output tab of the Output Panel | **One line of integration** — see "The one integration point," below |
| **Account** (`features/account/`, new) | New | Signup, login, session state | No |
| **MCP Access** (`features/mcp-access/`, new) | New | The Settings tab's content, the OAuth consent screen | No |

```
frontend/src/
├── features/
│   ├── market-health/       ← existing, untouched (TaskPanel, ConversationThread, OutputPanel, …)
│   ├── account/              ← new — SignupForm, LoginForm, session store
│   └── mcp-access/           ← new — SettingsTab, ConnectedAssistantCard, ConsentScreen
├── pages/
│   ├── MarketHealthPage.tsx  ← existing, untouched
│   ├── LoginPage.tsx         ← new
│   └── SignupPage.tsx        ← new
└── App.tsx                   ← changes from a single static render to a router (see Routing)

(No OAuthConsentPage — the consent screen is server-rendered by the backend. See Routing.)
```

**The one integration point.** `features/market-health/OutputPanel.tsx` (320px fixed, currently
a single-purpose "Output" reference list — real component, not this spec's earlier
approximation) gains a two-tab header (Output / Settings) and, when Settings is active, renders
`<SettingsTab />` from the new `mcp-access` feature instead of its existing reference list. That
one `if (activeTab === "settings") return <SettingsTab />` branch is the **entire** change to
existing code. `TaskPanel`, `ConversationThread`, every chart/story component, and the Output
tab's own existing behaviour are byte-for-byte unchanged.

**Why two new features, not one.** `account` (signup/login/session) is not specific to
connecting an AI — a future account-level surface (the outcome's own "in the future we will
offer other functionalities") reuses the same session, not a new one per feature. `mcp-access`
is specific to this outcome. Keeping them separate means a future account feature doesn't have
to import anything MCP-specific, and this feature's own code doesn't have to know how sessions
are implemented, only that `useSession()` exists.

---

## Routing (new — first client-side routing in this app)

`MarketHealthPage` has always been the entire app — `App.tsx` renders it directly, no router,
no URL ever changes (`frontend/specs/market-health/architecture.md` confirms: task switching is
local React state, never reflected in the URL). That stops being sufficient here: an OAuth
redirect from Claude/ChatGPT/Gemini is a real browser navigation to a real URL
(`backend/specs/mcp-access/api.md` — `GET /mcp/oauth/authorize`), and login/signup need
linkable, bookmarkable, browser-back-button-correct pages — none of which a single
always-rendered component can provide.

**Adds `react-router-dom`** (not previously a dependency — confirmed in `package.json`). Three
routes, `App.tsx` becomes a `<BrowserRouter>`:

| Path | Page | Auth required |
|---|---|---|
| `/` | `MarketHealthPage` (unchanged) | No — anonymous browsing of Market Health still works exactly as today |
| `/login` | `LoginPage` | No — supports a `?next=` param it redirects to on success, so the OAuth consent hand-off (below) round-trips correctly |
| `/signup` | `SignupPage` | No |

**Deliberately not a route: the OAuth consent screen.** Resolved (this spec's own Open Question,
now closed) in `backend/specs/mcp-access/api.md` — `GET /mcp/oauth/authorize` is server-rendered
Jinja2 HTML on the **backend**, the same pattern `admin_main.py`'s `/admin/login` already uses.
There is no `OAuthConsentPage` in this codebase; when that endpoint finds no session, it
redirects here to `/login?next=...`, and `LoginForm`'s success handler redirects the browser
back to whatever `next` carries — plain top-level navigation (`window.location`), not a router
`navigate()`, since the destination is a different service/origin in production.

**Deliberately not a route: the Settings tab.** It's a tab inside `/`'s Output Panel, not its
own URL — matching the IA's own decision (`design/information-architecture.md` v2.6) that
Settings is a panel state, not a page. A user can't deep-link straight to "Settings" today, and
that's fine — it's one click away from `/` in every case.

---

## Component Breakdown

### `account` (new)

| Component | Responsibility | Location |
|---|---|---|
| `SignupForm` | Email + password fields, client-side format validation (real email shape, non-trivial password length) mirroring — never replacing — the backend's own validation. Submits to `POST /api/account/signup`. | `frontend/src/features/account/SignupForm.tsx` |
| `LoginForm` | Email + password fields. Submits to `POST /api/account/login`. Shows one generic "incorrect email or password" message on `401` — never reveals which field was wrong (matches the backend's own deliberate ambiguity). | `frontend/src/features/account/LoginForm.tsx` |
| `useSession` (hook) | Reads the session store (below). The one thing the rest of the app should ever import from this feature — `mcp-access` never reaches into `SignupForm`/`LoginForm` directly. | `frontend/src/features/account/useSession.ts` |

### `mcp-access` (new)

| Component | Responsibility | Location |
|---|---|---|
| `SettingsTab` | Top-level content for the Output Panel's Settings tab (`design/visual-design.md` — "Output Panel — Settings tab"). Composes the header (title, explanation, MCP endpoint, per-client instructions) + `ConnectionsList`. | `frontend/src/features/mcp-access/SettingsTab.tsx` |
| `McpEndpointField` | The copyable endpoint field + per-client collapsed instructions. Pure presentation — the endpoint value itself is a static constant (below), not fetched. | `frontend/src/features/mcp-access/McpEndpointField.tsx` |
| `ConnectionsList` | Fetches `GET /api/account/connections`, renders one `ConnectedAssistantCard` per row or the `EmptyState`. | `frontend/src/features/mcp-access/ConnectionsList.tsx` |
| `ConnectedAssistantCard` | One connection: client name/icon, relative time, scope chips (translated from raw scope identifiers — see Data Requirements), plan badge, inline Revoke confirm. Calls `DELETE /api/account/connections/{id}` on confirm. | `frontend/src/features/mcp-access/ConnectedAssistantCard.tsx` |
| `EmptyState` | Rendered by `ConnectionsList` when the list is empty. Explains the value of connecting, per the experience spec's edge case. | `frontend/src/features/mcp-access/EmptyState.tsx` |

**No `OAuthConsentPage` component** — the consent screen is server-rendered by the backend
(Routing, above), not built here.

### `TabSwitcher` — shared, not owned by either new feature

The Output/Settings tab control reuses `design/visual-design.md`'s existing "Tab / range
selector" pattern. Since `market-health` doesn't currently have this as an extracted component
(its own tab-like controls — granularity, time range — are each hand-rolled inline in
`JobOpeningsChart.tsx`), this is the first time it's pulled out generically:

| Component | Responsibility | Location |
|---|---|---|
| `TabSwitcher` | Generic two-or-more-option pill switcher, styled per the existing Tab/range-selector tokens. Takes `options` + `active` + `onChange` — no knowledge of Output/Settings specifically, so `JobOpeningsChart`'s own controls could migrate to it later without this feature depending on that happening. | `frontend/src/components/TabSwitcher.tsx` |

---

## State Management

**Session** — the first Zustand store this app actually uses (`CLAUDE.md`'s tech stack has
named Zustand since the start; `frontend/specs/market-health/architecture.md` explicitly needed
none). A small store, not a kitchen sink:
```ts
{ user: { id, email, plan } | null, setUser, clearUser }
```
Populated by `GET /api/account/me` on app load (once, in `App.tsx`, before rendering routes —
so a page can synchronously know "signed in or not" instead of flashing an unauthenticated
state). `LoginForm`/`SignupForm` call `setUser` on success; a logout action (surfaced from
`SettingsTab` — the only place a signed-in user currently has any account-level UI at all)
calls `POST /api/account/logout` then `clearUser`.

**Why Zustand and not React Context here**: session state is read from `OutputPanel` (deep in
the market-health tree) and from `LoginPage`/`SignupPage` (separate route trees entirely) — three
places with no shared parent short of the app root. A store avoids threading a prop or a
context provider through `MarketHealthPage`'s entire existing tree just for this.

**Connections list state** — plain TanStack Query, same pattern as every existing market-health
query: `['account', 'connections']` → `GET /api/account/connections`. Invalidated on a
successful revoke (`ConnectedAssistantCard`'s `DELETE` mutation invalidates the query on
success — the row disappears/updates because the list refetches, not because of local
optimistic-removal logic that could drift from the server's real state).

**Settings/Output tab state** — local to `OutputPanel`, `useState<"output" | "settings">`. Not
global, not persisted across a page reload (reopens on "Output" every time, matching the
existing Output tab's own non-persisted behaviour — neither tab remembers its scroll position
or selection across a reload today).

**No consent-screen state in this codebase** — it's server-rendered (Routing, above); its form
state lives in the Jinja2 template's own plain HTML form, not in any frontend store.

**No new state for Market Health itself.** Confirmed against `OutputPanel.tsx`'s real code —
its existing `messages`-derived `refs` list logic is completely unchanged; it only gains a
sibling render path, not a rewrite.

---

## Data Requirements

| Data | Source | When fetched |
|---|---|---|
| Current session | `GET /api/account/me` | Once, on app load, before routes render |
| Connections list | `GET /api/account/connections` | On mount of `ConnectionsList` (i.e. whenever the Settings tab is opened) |
| MCP endpoint value | A build-time/env constant (`VITE_MCP_ENDPOINT_URL`, e.g. `http://127.0.0.1:8000/mcp` locally) | Not fetched — it's this deployment's own known address, same as how the frontend already knows its own API base path |
| Scope plain-language labels | A small static map in `mcp-access`, keyed by the backend's scope identifiers (`jobs.read` → "Can read job demand and skill trends", etc. — exact three from `backend/specs/mcp-access/api.md` — Scope model) | Bundled, not fetched — these three labels change only when the backend's own scope model changes, at which point this map is updated in the same change |

---

## API Contract

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/account/signup` | `SignupForm` |
| POST | `/api/account/login` | `LoginForm` |
| POST | `/api/account/logout` | Logout action in `SettingsTab` |
| GET | `/api/account/me` | Session bootstrap on app load |
| GET | `/api/account/connections` | `ConnectionsList` |
| DELETE | `/api/account/connections/{id}` | `ConnectedAssistantCard`'s Revoke |

`GET /mcp/oauth/authorize` is **not** called by this frontend — it's a server-rendered page the
backend serves directly (Routing, above). This frontend's only relationship to it is
`LoginForm`'s `?next=` redirect target, which may point there.

All account/connections calls need `credentials: "include"` on `fetch` — the **first** time
this codebase has needed to send cookies cross-request. Every existing market-health `fetch`
call is unauthenticated and doesn't set this; this feature's calls must, or the session cookie
(`backend/specs/mcp-access/api.md` — Business Logic — Session auth) never reaches the backend.

---

## Tech Decisions

- **`react-router-dom`** — new dependency, justified above (Routing). Not used for anything
  inside `MarketHealthPage`'s own three-column app, which keeps its existing state-based task
  switching unchanged; routing exists only to give login/signup/consent real URLs.
- **Zustand** — first real use in this codebase, scoped to session state only (User Model
  above). Not a general app-wide store; `market-health`'s own state stays exactly as
  `frontend/specs/market-health/architecture.md` already describes it (TanStack Query +
  component-local state, no store).
- **TanStack Query** for the connections list, same key convention as every existing
  market-health query (`['area', 'resource', ...params]`).
- **Tailwind CSS only** — no new component library, consistent with the rest of the app.
- Password fields use native `<input type="password">`, no third-party form library — this
  product has never used one, and two short forms don't justify introducing one now.
- **Added `src/vite-env.d.ts`** (`/// <reference types="vite/client" />`) — this project never
  needed `import.meta.env` before (`McpEndpointField`'s `VITE_MCP_ENDPOINT_URL` is the first
  use), and TypeScript doesn't know that type exists without this reference. Found by actually
  running `tsc --noEmit`, not assumed to be unnecessary.

---

## Out of scope

- Anything Part 2 of the experience spec describes — no frontend renders it, ever (Experience
  this implements, above).
- Email verification, password reset, "remember me," social login — per
  `backend/specs/mcp-access/api.md`'s own Out of scope, there is nothing here for the frontend
  to build against yet.
- Any UI for upgrading from Free to Premium — no billing integration exists (backend spec, Open
  Questions resolved). A `plan_required` error surfaces as plain text; no upgrade button, no
  pricing page.
- Migrating `market-health`'s own hand-rolled tab-like controls (granularity, time range) onto
  the new `TabSwitcher` — it's built generically so that becomes possible later, but doing it is
  not part of this change.
- Any route guard beyond the one `/mcp/oauth/authorize` needs — `/` stays anonymous-accessible,
  matching Market Health's existing no-auth-required behaviour exactly.

## Open Questions

None outstanding. The one real ambiguity this spec surfaced — whether the OAuth consent screen
is server-rendered or part of this frontend — is resolved in both this document (Routing,
Component Breakdown) and `backend/specs/mcp-access/api.md` (`GET /mcp/oauth/authorize`): it's
server-rendered Jinja2, matching the existing `/admin/login` precedent. Nothing here waits on a
future decision.
