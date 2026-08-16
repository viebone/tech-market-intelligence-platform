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
├── api   (planned)       — the FastAPI backend (backend/src/main.py)
│
└── web   (planned)       — the React frontend
```

**Postgres**, **job-sync**, and **`admin`** (Railway service name `romantic-presence`)
exist today. `api` and `web` are not yet deployed — the consumer-facing app currently
only runs locally (see this product's `CLAUDE.md` — "Running Locally"). The rest of
this doc documents what exists, and sketches what deploying the remaining two would
look like when that becomes the next step.

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
| Env vars | `GEMINI_API_KEY_CLASSIFICATION`, `DATABASE_URL` — `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` were removed 2026-08-03 (Adzuna retired, no license to keep using it); the three replacement sources (Greenhouse, Lever, Ashby) are public and need no credentials. **Action needed**: remove these two variables from the `job-sync` service in the Railway dashboard — they're stale now, not read by any code, but should be cleaned up rather than left dangling. |

`DATABASE_URL` is set to the Railway variable reference `${{Postgres.DATABASE_URL}}` —
Postgres's *internal* private-network address, not its public proxy URL. Services in
the same Railway project reach each other over the internal network, which is faster
and doesn't expose the database's credentials over the public internet. (The public
proxy URL — the one in local `backend/.env` — exists specifically so tools *outside*
Railway, like your own machine, can connect. Never put the public URL into a
service's own env vars; use the internal reference instead.)

`GEMINI_API_KEY_CLASSIFICATION` is deliberately a separate key from `/api/chat`'s
`GEMINI_API_KEY` — classification and live chat traffic must never compete for the
same request quota. See `AI_INTERACTION_SETTINGS.md` for the chat side of that
boundary.

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

## Gotchas learned the hard way (2026-07-26 deploy)

These cost real time to figure out and will bite again if forgotten:

1. **`backend/railway.json` always wins over dashboard/API config changes.** Setting
   `cronSchedule`, `startCommand`, etc. via the Railway dashboard or API on a service
   that has a `railway.json` gets silently overwritten back to the file's values on
   the next deploy. **To change deploy config permanently, edit the file and push —
   don't change it in the dashboard and expect it to stick.**

2. **Auto-deploy is off for this repo** (`viebone/tech-market-intelligence-platform`
   has no Railway GitHub App installation). Pushing to `main` does **not**
   automatically redeploy `job-sync`. A plain "redeploy" action in Railway re-runs the
   *last deployed commit*, not the latest one on the branch — a new deploy must be
   explicitly triggered against the specific commit SHA you want. Confirm the deployed
   `commitHash` matches what you expect after any deploy.

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

## Planned: deploying `api` and `web`

Not yet done — sketched here so the next step is a checklist, not a design exercise.

```
api   — rootDirectory: backend/, no cron, restart policy ALWAYS
        start command: uvicorn main:app --host 0.0.0.0 --port $PORT
        needs: DATABASE_URL (internal ref), GEMINI_API_KEY, ANTHROPIC_API_KEY, etc.
        needs a public domain (Railway `generate-domain`) so `web` can reach it

web   — rootDirectory: frontend/
        build: npm run build
        needs api's public URL baked in at build time (e.g. a VITE_API_URL env var)
        needs its own way to serve the built static files in production —
        Vite's dev server (`npm run dev`) is not meant for production use
```

Open question, not yet decided: whether `web` belongs on Railway at all, versus a
static-first host (Vercel, Netlify) that's more purpose-built for a Vite/React
frontend. Railway can do it, but that's a real trade-off worth making deliberately
rather than defaulting into.

---

## Service: `admin` (deployed 2026-08-16, real Railway service name `romantic-presence`)

Live at `https://romantic-presence-production.up.railway.app` (public Railway
domain — not a custom domain). Deliberately named `romantic-presence` (Railway's
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
| Auto-deploy | **On** for this service (unlike `job-sync`'s `main`, which has it off) — any push to `main` now deploys `admin` automatically. Since `job-sync` and `admin` both build from `main`, a push that only touches, say, `ingest.py` still triggers a rebuild of `admin` too (harmless — same image either way, just an extra build cycle). |
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
