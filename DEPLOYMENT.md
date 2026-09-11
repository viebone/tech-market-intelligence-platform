# Deployment Architecture

How this product is actually deployed and run in production (Railway), and how the
pieces connect. Written so anyone — human or AI — can pick this up cold and understand
the full picture without spelunking through service configs.

---

## The mental model

**One Railway project holds every piece of infrastructure for this product. Each
piece is a separate Railway *service*, even though most of them build from the same
GitHub repo.** Railway doesn't infer that a repo has multiple deployable parts — every
service explicitly declares its own root directory, build, and start command, even
when several services share one repo.

```
Railway project: "feisty-grace"
│
├── Postgres              — managed database (Railway template image)
│
├── job-sync              — the daily ingestion + classification pipeline (see below)
│
├── romantic-presence     — the pipeline-visibility admin dashboard (see "Service: `admin`" below —
│                           named `admin` in code/specs, `romantic-presence` is just this
│                           particular service's Railway-assigned name)
│
├── api                   — the consumer-facing FastAPI backend (see "Service: `api`" below)
│
└── web                   — the React frontend (see "Service: `web`" below)
```

All five pieces exist and are live today (deployed 2026-08-16). The consumer-facing
product is fully reachable in production for the first time — `web`'s public domain is
the real, share-able entry point to the whole product now, not just `localhost:5173`.

---

## Gemini projects & LLM billing

Set up 2026-08-29 — see `outcomes/llm-spend-is-bounded-and-isolated.md` and
`changes/2026-08-29-chat-free-tier-key-isolation.md`. **Revised 2026-09-06** —
chat moved to a dedicated paid project, free tier dropped
(`changes/2026-09-03-chat-resilience-and-instant-answers.md`). **Google Cloud
billing is per project, not per API key.** Four Gemini keys across three projects,
by billing tier and workload:

| Env var | Google Cloud project | Billing tier | Used by (Railway service) | Model |
|---|---|---|---|---|
| `GEMINI_API_KEY_CHAT_PAID` | _dedicated chat project — operator to record id_ | **Prepay** — its own balance | `api` (`/api/chat`, reasoning trace) | `gemini-3.6-flash` |
| `GEMINI_API_KEY` | `gen-lang-client-0003173949` | **Free** | _nothing_ — removed from `/api/chat` 2026-09-06; left in the env, unread | `gemini-3.6-flash` |
| `GEMINI_API_KEY_CLASSIFICATION` | `gen-lang-client-0963554051` | **Tier 1 · Prepay** | `job-sync` (classification) | `gemini-2.5-flash` |
| `GEMINI_API_KEY_REQUIREMENTS` | `gen-lang-client-0963554051` | **Tier 1 · Prepay** | `job-sync` (requirements extraction) | `gemini-3.6-flash` (pinned 2026-08-30, commit `ddb68b3`) |

Rationale:

- **Chat runs on its own dedicated paid project** (revised 2026-09-06). The free
  tier was dropped because it could not be fast: `gemini-3.6-flash` free quota is
  20 requests/day (~6 chat turns), with higher, less predictable latency and ~8s
  wasted per request retrying it once spent. Chat is now bounded instead by
  `CHAT_PAID_DAILY_REQUEST_CAP` (`ai_interaction_settings.py`, 100/day, tracked in
  `chat_paid_usage`); past the cap it degrades to the curated instant-answer path
  (`curated_answers.py`, no model call) / a calm "briefly unavailable" message.
  The dedicated project keeps a chat spike from draining the pipeline balance and
  vice versa.
- **Both jobs-pipeline workloads share one prepaid project** so total pipeline
  spend draws down a single balance.
- `gen-lang-client-0963554051` is grandfathered for `gemini-2.5-flash`;
  `gen-lang-client-0003173949` (created 2026-08-10) is not.

**Operator responsibilities on `gen-lang-client-0963554051` (pipeline) and the
dedicated chat project:**

- **Auto-recharge must stay OFF on both** — this is what makes each prepaid
  balance a hard ceiling. If it's on, the "can't overspend" guarantee is void.
- Keep only a small balance loaded on each (target: ~$5/month of headroom) until
  the follow-on spend-ledger change adds an in-app monthly cap.
- Optional: cloud-console budget alerts at $2 / $3 / $4.
- **Record the dedicated chat project's GCP id and balance** in the table above
  and in product `CLAUDE.md` (both carry a placeholder) — outstanding as of
  2026-09-06.

Until that follow-on change lands, the code's existing per-workload request-count
budgets (`DAILY_REQUEST_BUDGET`, `REQUIREMENTS_DAILY_REQUEST_BUDGET`) are the
operative spend cap — conservative (pennies/day) and **must not be raised** yet.

**Chat resilience (revised 2026-09-06).** `/api/chat` now runs on the dedicated
paid project, so the old free-tier `429`-on-burst problem is gone. Each model call
retries a transient `503`/`429`/timeout twice (1s then 2s) before giving up
(`llm/chat_fallback.py`). Common questions are answered by the curated engine with
**no model call** in ~0.3s (`curated_answers.py`); only free-form misses hit the
model, at 10–30s (inherent to `gemini-3.6-flash` doing live-data tool-calling).
When the daily cap is spent or the model is unavailable after retries, chat streams
a calm "briefly unavailable — here's what I can answer instantly" message, never a
dead-end error string.

---

## Service: `job-sync`

The one piece of this product currently running unattended in production.

| | |
|---|---|
| Source | `viebone/tech-market-intelligence-platform`, branch `main` |
| Root directory | `backend/` |
| Config file | `backend/railway.json` — **this file is the source of truth**, see "Gotchas" below |
| Build | Nixpacks, auto-detected from `requirements.txt` |
| Start command | `python src/ingest.py` |
| Schedule | Cron `0 6 * * *` (06:00 UTC, daily) |
| Restart policy | `NEVER` — it's a one-shot job, not a long-running service |
| Env vars | `GEMINI_API_KEY_CLASSIFICATION`, `GEMINI_API_KEY_REQUIREMENTS` (both keys of the **prepaid** Gemini project — see "Gemini projects & LLM billing" above), `DATABASE_URL` — `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` were removed 2026-08-03 (Adzuna retired, no license to keep using it); the three replacement sources (Greenhouse, Lever, Ashby) are public and need no credentials. **Action needed**: remove these two variables from the `job-sync` service in the Railway dashboard — they're stale now, not read by any code, but should be cleaned up rather than left dangling. |

`DATABASE_URL` is set to the Railway variable reference `${{Postgres.DATABASE_URL}}` —
Postgres's *internal* private-network address, not its public proxy URL. Services in
the same Railway project reach each other over the internal network, which is faster
and doesn't expose the database's credentials over the public internet. (The public
proxy URL — the one in local `backend/.env` — exists specifically so tools *outside*
Railway, like your own machine, can connect. Never put the public URL into a
service's own env vars; use the internal reference instead.)

`GEMINI_API_KEY_CLASSIFICATION` is deliberately a separate key from `/api/chat`'s
`GEMINI_API_KEY` — classification and live chat traffic must never compete for the
same request quota. Since 2026-08-29 they are also in **different Google Cloud
projects on different billing tiers** (see "Gemini projects & LLM billing"
above). See `AI_INTERACTION_SETTINGS.md` for the chat side of that boundary.

### What it does, end to end

`ingest.py` runs four steps every time it fires:

1. **Fetch** — for each company in each source adapter's curated list
   (`backend/src/sources/greenhouse.py`, `lever.py`, `ashby.py` — 15, 5, and 15
   companies respectively as of 2026-08-03), pull that company's full published job
   board. **Adzuna was retired 2026-08-03** (license no longer permits use) — see
   `changes/2026-07-28-multi-source-job-data-ingestion.md`. Unlike Adzuna's
   search-term-based fetch, these three ATS platforms return a company's entire board
   with no server-side "tech roles only" filter, so classification's `"other"`
   escape hatch does that filtering downstream instead.
2. **Dedupe & store** — insert only postings not already seen, keyed on
   `id = f"{source}:{source_ref}"` (`backend/src/raw_postings.py`). `raw_postings` is
   append-only: a posting is never updated after first sight, since a company can
   edit or remove a listing at any time with no way to recover its prior state.
3. **Classify** — every newly-ingested posting is classified into a closed taxonomy
   (role category / sub-specialization / seniority / track) by Gemini
   (`backend/src/classification.py`), batched and rate-limited to survive the free
   tier. Titles already classified in a past run, or duplicated within this run, are
   never sent to the LLM twice — classification depends only on title text. Expect a
   materially higher volume through this step (and a higher `other` rate) than under
   Adzuna, since the new sources aren't pre-filtered by search term.
4. **Record** — exactly one row is written to `ingestion_runs`
   (`backend/src/ingestion_runs.py`) per run, success or failure, with counts and any
   anomalies detected (a company that suddenly returns 0 results, an "other"-rate
   that jumps relative to the last 5 runs). This is what makes a run's outcome
   inspectable from the database — see "How to verify it actually ran," below.

### Data model (Postgres, created by `backend/src/db.py`)

```
raw_postings     — id (f"{source}:{source_ref}"), source, source_ref, company,
                    role_family_query (legacy Adzuna-era, NULL for new rows), title,
                    raw_response (JSONB), fetched_at
classifications  — posting_id → raw_postings, role_category, sub_specialization,
                    seniority, track, taxonomy_version, model, classified_at
ingestion_runs   — started_at / completed_at, status, terms_processed (JSONB — now
                    {source, company, fetched, inserted, error} per entry),
                    fetch/insert/classify counts, other_rate, anomalies (JSONB), error_message
```

### Who reads this data

`job-sync` is the *only* thing that writes to `raw_postings` / `classifications`.
Everything else only reads:

- `backend/src/market_health.py` / `market_openings.py` aggregate both tables into the
  Market Health trend charts.
- `backend/src/market_query.py`'s `query_market_data` tool is called by `/api/chat` so
  chat answers from this real data instead of a mock dataset.

### How to verify it actually ran

Don't rely on Railway's log stream for this service — in practice (see incident below)
it has repeatedly returned empty logs and zero metrics for real, successful runs.
The reliable signal is the database itself, since `record_run()` writes a row on every
single run, including failures:

```sql
SELECT id, started_at, completed_at, status, total_fetched, total_inserted,
       total_classified, error_message
FROM ingestion_runs
ORDER BY started_at DESC
LIMIT 10;
```

Run this via the Railway dashboard → Postgres service → **Data** tab (no local setup
needed), or a local GUI/`psql` client using the *public* `DATABASE_URL` from
`backend/.env`.

---

## Service: `employment-events` (code ready 2026-09-11 — **not yet deployed**)

Employment-event ingestion (`changes/2026-09-11-employment-event-ingestion.md`) — layoffs,
closures, restructuring, bankruptcy, offshoring, expansion, hiring announcements. Same
cron-service shape as `job-sync`, deliberately a **separate** Railway service (not folded into
`job-sync`) — see `backend/specs/market-health/api.md` — Tech Decisions — Scheduling.

| | |
|---|---|
| Source | Same repo/branch as `job-sync` |
| Root directory | `backend/` |
| Config file | `backend/railway.employment-events.json` (committed; not yet connected to a live Railway service) |
| Start command | `python src/ingest_employment_events.py` |
| Schedule | Cron `0 7 * * *` (07:00 UTC, daily — offset 1h from `job-sync`'s 06:00 UTC) |
| Restart policy | `NEVER` |
| Env vars needed | `DATABASE_URL` (internal reference, same as `job-sync`), `COMPANIES_HOUSE_API_KEY` (free registration — see `backend/.env.example`) |

**Not yet a real Railway service** — committing `railway.employment-events.json` is only the
config-as-code half; per Gotcha 6 below, a new service still needs the dashboard's real
"Connect Repo" flow and its config-file path set explicitly under Settings → Config-as-code
before it will build or run anything. Deliberately left as a manual step here rather than
created via this session's Railway MCP access — creating a new production service is exactly
the kind of outward-facing, hard-to-reverse action that should be a deliberate choice, not a
side effect of a spec-chain implementation pass. Running it is also low-value until at least
one adapter is functional (`DATA_SOURCES.md` §3a) — connect the service once that's true, not
before.

---

## Gotchas learned the hard way (2026-07-26 deploy)

These cost real time to figure out and will bite again if forgotten:

1. **`backend/railway.json` always wins over dashboard/API config changes.** Setting
   `cronSchedule`, `startCommand`, etc. via the Railway dashboard or API on a service
   that has a `railway.json` gets silently overwritten back to the file's values on
   the next deploy. **To change deploy config permanently, edit the file and push —
   don't change it in the dashboard and expect it to stick.**

2. **Auto-deploy history (resolved 2026-09-02).** `job-sync` originally had no
   automatic deployments — the Railway GitHub App was connected for `api`/`admin`
   during the 2026-08-16 deploy but `job-sync` was left on manual. This bit
   `changes/2026-08-29-chat-free-tier-key-isolation.md`: a `requirements.py` pin
   (commit `ddb68b3`) deployed to `api` automatically but `job-sync` kept running
   the older commit for days. **Fixed 2026-09-02 — `job-sync` → Settings → Source
   now has automatic deployments on for `main`**, matching `api` and `admin`.
   Note that enabling the toggle does *not* retroactively deploy the current HEAD
   — it triggers on the *next* push. A plain "redeploy" in Railway re-runs the
   *last deployed commit*, not the latest branch commit; always confirm the
   deployed `commitHash` after a deploy.

3. **A cron-scheduled service does not run on deploy.** Once `cronSchedule` is set,
   the container builds and sits idle until the next scheduled tick — it does not
   execute once immediately, the way a plain (non-cron) one-off deployment does. To
   force an immediate test run, the schedule has to be temporarily removed from
   `railway.json`, committed, deployed, verified, then restored, committed, and
   deployed again. There is no "run now" button for an already-scheduled cron service.

4. **Railway's log/metrics API can be unreliable for very short-lived containers.**
   Multiple real, successful (`status: SUCCESS`) deploys of this service returned
   completely empty deploy logs and zero CPU/memory samples through the API — even
   though a crash would have surfaced as `FAILED`/`CRASHED` instead. Don't treat empty
   logs as proof nothing happened; check `ingestion_runs` instead.

---

## Service: `api` (deployed 2026-08-16)

The consumer-facing FastAPI backend (`backend/src/main.py`) — `/api/market-health/*`,
`/api/chat`. Live at `https://api-production-df13.up.railway.app`.

| | |
|---|---|
| Source | `viebone/tech-market-intelligence-platform`, branch `main` |
| Root directory | `/backend` — same directory `job-sync` and `admin` also use |
| Config file | `backend/railway.api.json` — its own file, separate from `job-sync`'s and `admin`'s |
| Start command | `cd src && uvicorn main:app --host 0.0.0.0 --port $PORT` (from `railway.api.json`) |
| Restart policy | `ALWAYS` — long-running web service |
| Auto-deploy | On — a push to `main` deploys `api` (and `admin`, and rebuilds `job-sync`'s image, though `job-sync` itself only *runs* on its cron schedule) |
| Env vars | `DATABASE_URL` (`${{Postgres.DATABASE_URL}}`, internal reference), `GEMINI_API_KEY_CHAT_PAID` (the **dedicated paid** chat Gemini project — the only key `/api/chat` reads since 2026-09-06; set + verified live that date), `GEMINI_API_KEY` (the old **free-tier** project `gen-lang-client-0003173949` — no longer read by any code, left set, safe to remove), `CORS_ALLOWED_ORIGINS` (`https://web-production-03c43.up.railway.app` — see below; not actually load-bearing given how `web` reaches it, kept set anyway as defense-in-depth and to match what any *other* future direct caller would need). See "Gemini projects & LLM billing" above and `AI_INTERACTION_SETTINGS.md`. |
| Domain | Railway-generated (`generate-domain`) |

Deployed cleanly on the **first attempt** — every gotcha below had already been learned
deploying `admin` a few hours earlier in the same session.

## Service: `web` (deployed 2026-08-16)

The React/Vite consumer frontend. Live at
`https://web-production-03c43.up.railway.app` — **this is the product's real public
entry point.**

| | |
|---|---|
| Source | `viebone/tech-market-intelligence-platform`, branch `main` |
| Root directory | `/frontend` |
| Config file | `frontend/railway.json` |
| Build command | `npm run build` (`tsc && vite build`) |
| Start command | `npm run preview -- --port $PORT` (from `frontend/railway.json`) — **not** a purpose-built production static server; `vite preview` is pragmatic here (zero new dependencies, already verified working) but is explicitly not designed by Vite for heavy production traffic. Revisit if `web` ever needs more than light/personal traffic. |
| Restart policy | `ALWAYS` |
| Env vars | `API_PROXY_TARGET` (`https://api-production-df13.up.railway.app`) — server-side only, deliberately **not** `VITE_`-prefixed, so it's never bundled into client JS |
| Domain | Railway-generated (`generate-domain`) |

### How `web` actually reaches `api` — no frontend code change, no CORS dependency

The frontend's React components only ever call **relative** paths
(`/api/market-health/openings`, `/api/chat`) — true in dev and unchanged in production.
`vite.config.ts` gained a `preview.proxy` block (mirroring the pre-existing
`server.proxy` used for local dev) that forwards `/api/*` to `API_PROXY_TARGET` —
**server-side**, inside the `web` container, using Vite's own built-in proxy feature.
No new dependency, no frontend component change.

**This means the browser only ever talks to `web`'s own origin** — same-origin from
the browser's point of view, since the page and the (proxied) API calls both appear to
come from `web-production-03c43.up.railway.app`. Confirmed by testing the real deployed
URLs directly: `curl https://web-production-03c43.up.railway.app/api/market-health/openings`
returns real production data, end to end, through the proxy. Browser-enforced CORS
simply never triggers for this path — `api`'s `CORS_ALLOWED_ORIGINS` is set anyway
(matches the backend spec's documented mechanism, and covers any future caller that
hits `api` directly, bypassing the proxy) but isn't actually load-bearing for `web`
itself to work.

### Gotchas learned the hard way (2026-08-16, `api`+`web` deploy)

Continuing the numbering from `admin`'s deploy above:

10. **Vite 5.4+'s `allowedHosts` check applies to `preview` too, not just `server`.**
    Railway's domain isn't known until after the first deploy, so `preview.allowedHosts`
    is set to `true` (disable the check) rather than trying to pre-guess the domain.
    Low-risk for a public static site regardless.
11. **The service-settings-not-persisting issue from `admin`'s deploy (gotcha #5)
    recurred for `web`** — Root Directory and Config File path were entered correctly
    in the dashboard but the first deploy still failed with the config file "not found."
    Re-entering/re-confirming the same values fixed it — genuinely a UI/persistence
    flake on Railway's side, not a path-resolution rule (a same-structure
    `/frontend/railway.json` + root directory `/frontend` combination that failed once
    then worked immediately after re-confirming, no other change). **If a config file
    "not found" error appears despite the path being visibly correct in Settings, try
    re-entering the same value before assuming the path syntax itself is wrong.**

---

## Service: `admin` (deployed 2026-08-16, real Railway service name `romantic-presence`)

Live at `https://romantic-presence-production.up.railway.app` (public Railway
domain — not a custom domain). **Entry point:
`https://romantic-presence-production.up.railway.app/admin/login`** — the app
defines no route at `/`, so the bare domain returns `{"detail":"Not Found"}`.
Every page lives under `/admin/` (see `backend/specs/pipeline-visibility/api.md`
— "API Endpoints"); a successful login redirects to `/admin/`. Deliberately
named `romantic-presence` (Railway's
default random service name, kept as-is — the name itself carries no meaning and
is never referenced in code) rather than `admin`, unlike the tidy
`job-sync`/`api`/`web` naming above.

| | |
|---|---|
| Source | `viebone/tech-market-intelligence-platform`, branch `main` — originally deployed from a feature branch (`admin-pipeline-dashboard`) while this was being built, repointed to `main` 2026-08-16 once merged, specifically because this service shares `backend/src/` modules with `job-sync` and two long-lived branches for shared code risked silent drift (see `changes/2026-08-13-admin-pipeline-dashboard.md`'s Decision Log) |
| Root directory | `/backend` — same directory `job-sync` and the planned `api` also use |
| Config file | `backend/railway.admin.json` — its own file, separate from `job-sync`'s `backend/railway.json` (see Gotchas below) |
| Start command | `cd src && uvicorn admin_main:app --host 0.0.0.0 --port $PORT` (from `railway.admin.json`) |
| Restart policy | `ALWAYS` — long-running web service, not a one-shot job like `job-sync` |
| Auto-deploy | **On** — any push to `main` deploys `admin` automatically. `job-sync` was the last hold-out on manual deploys; it was switched to auto 2026-09-02 (see Gotchas #2), so all three code services (`api`, `admin`, `job-sync`) now auto-deploy from `main`. |
| Env vars | `DATABASE_URL` (`${{Postgres.DATABASE_URL}}`, internal reference), `ADMIN_PASSWORD_HASH`, `ADMIN_JWT_SECRET`. `ADMIN_COOKIE_SECURE` intentionally omitted (defaults `true` — correct in production) |
| Domain | Railway-generated (`generate-domain`), no custom domain attached |

Server-renders its own HTML (Jinja2 templates in `backend/src/admin_templates/`)
— no separate frontend build, unlike `web`. Auth is a single bcrypt-hashed
operator password + JWT session cookie, no user table — see
`backend/specs/pipeline-visibility/api.md` — Auth decision.

### Gotchas learned the hard way (2026-08-16 deploy)

Added to the existing job-sync gotcha list above, not a separate story:

5. **Build/deploy settings (root directory, start command, restart policy,
   config file path) set through the Railway API/MCP did not reliably persist**
   for a freshly-created empty service — the dashboard kept showing those
   fields empty even after the API reported success, and a build ran against
   the whole repo root instead of `backend/` as a result. **Fix: set root
   directory and the config-as-code file path directly in the dashboard UI**,
   not via API calls.
6. **Attaching a GitHub source via the API doesn't create a working
   connection** — it records the repo name, but not the GitHub App
   installation link the dashboard's real "Connect Repo" flow creates.
   Deploys failed with "git repo not found" until the repo was disconnected
   and manually reconnected through **Settings → Source → Connect Repo**.
7. **The config-as-code file is not auto-discovered from root directory** —
   correcting what this doc previously assumed from watching `job-sync` work.
   Each service needs its config file path set explicitly under **Settings →
   Config-as-code → Railway Config File** (e.g. `/backend/railway.admin.json`).
   Two services can share a root directory and use two different config files
   — `job-sync` and `admin` now do — but only because each is told explicitly
   which file to read; leaving this blank (or pointed at the wrong file)
   silently pulled in `job-sync`'s file/settings during setup.
8. **`rootDirectory` scopes the build context, not the app's internal
   layout** — `uvicorn admin_main:app` failed with `Could not import module
   "admin_main"` even with root directory correctly set to `/backend`, because
   the module actually lives at `backend/src/admin_main.py`. Unlike `python
   src/ingest.py` (Python adds the *script's own* directory to `sys.path`
   regardless of working directory), `uvicorn`'s `module:app` string only
   resolves against the working directory itself. Fixed with
   `cd src && uvicorn admin_main:app ...` — matches how `backend/src/` is
   `cd`'ed into for local dev too (`CLAUDE.md` — "Running Locally").
9. **Changing a service's source branch doesn't take effect via a plain
   "redeploy"** — same underlying gotcha as #2 above (a `job-sync` redeploy
   re-running the last-*deployed* commit, not the branch's latest), but hit
   again here for a *branch change* specifically: after repointing `admin`
   from `admin-pipeline-dashboard` to `main`, triggering `redeploy` rebuilt
   the old branch's last commit again — the branch change stayed "staged,"
   never applied. What actually applied it: committing the environment's
   staged changes (Railway's "Deploy" action for pending config changes, not
   its "Redeploy" action for re-running history) — after that, the next
   deployment correctly showed `branch: "main"` at the new merge commit.
