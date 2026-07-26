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
├── Postgres          — managed database (Railway template image)
│
├── job-sync           — the daily ingestion + classification pipeline (see below)
│
├── api   (planned)    — the FastAPI backend (backend/src/main.py)
│
└── web   (planned)    — the React frontend
```

Only **Postgres** and **job-sync** exist today. `api` and `web` are not yet deployed —
the app currently only runs locally (see this product's `CLAUDE.md` — "Running
Locally"). The rest of this doc documents what exists, and sketches what deploying the
remaining two would look like when that becomes the next step.

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
| Env vars | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `GEMINI_API_KEY_CLASSIFICATION`, `DATABASE_URL` |

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

1. **Fetch** — for each of 12 curated job titles across 3 role categories (Designer,
   Product Manager, Engineer — see `ROLE_SEARCH_TERMS` in `ingest.py`), pull live UK
   postings from the Adzuna Jobs API (`backend/src/adzuna_client.py`), last 3 days.
2. **Dedupe & store** — insert only postings not already seen, keyed on Adzuna's own
   `id` (`backend/src/raw_postings.py`). `raw_postings` is append-only: a posting is
   never updated after first sight, since expired listings vanish from Adzuna's index
   permanently and this is the only chance to capture them.
3. **Classify** — every newly-ingested posting is classified into a closed taxonomy
   (role category / sub-specialization / seniority / track) by Gemini
   (`backend/src/classification.py`), batched and rate-limited to survive the free
   tier. Titles already classified in a past run, or duplicated within this run, are
   never sent to the LLM twice — classification depends only on title text.
4. **Record** — exactly one row is written to `ingestion_runs`
   (`backend/src/ingestion_runs.py`) per run, success or failure, with counts and any
   anomalies detected (a search term that suddenly returns 0 results, an "other"-rate
   that jumps relative to the last 5 runs). This is what makes a run's outcome
   inspectable from the database — see "How to verify it actually ran," below.

### Data model (Postgres, created by `backend/src/db.py`)

```
raw_postings     — id (Adzuna's own), role_family_query, title, raw_response (JSONB), fetched_at
classifications  — posting_id → raw_postings, role_category, sub_specialization,
                    seniority, track, taxonomy_version, model, classified_at
ingestion_runs   — started_at / completed_at, status, terms_processed (JSONB),
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
