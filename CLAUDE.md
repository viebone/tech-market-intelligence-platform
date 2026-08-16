# Tech Market Intelligence Platform — Project Instructions

This project follows the **User Outcome Based Product Development (UOBPD)** framework.
See `CLAUDE.md` at the workspace root for the full framework rules. This file adds project-specific context.

---

## Workspace Setup

This project lives inside the UOBPD framework repo, which acts as the VS Code workspace root:

```
user-outcome-based-product-development/   ← open this as your VS Code workspace
├── CLAUDE.md                             ← framework rules (workspace root)
├── .claude/skills/                       ← skills available to all products (spec formats embedded)
├── roles/                                ← role definitions
└── products/
    └── [this project]/                   ← you are here (its own git repo)
```

**Skills** live in `.claude/skills/` at the workspace root and are available in every
product session automatically. To update a skill, edit it there — no copying needed.

**MCPs** are configured globally in `~/.claude/settings.json` and available in every
product session. Project-specific MCP overrides go in this project's `.claude/settings.json`.

**Framework rules** live in `CLAUDE.md` at the workspace root.
Always read that file before making decisions about spec hierarchy, roles, or directive levels.

**Change management**: all changes — new features, bug fixes, user feedback, visual updates —
must start with `/change-request`. Change requests are saved in `changes/` at this product root.
Nothing moves to specs or implementation without one.

---

## What we're building
A market intelligence platform for UX and other tech professionals that automatically tracks hiring demand, skills, salaries, and layoffs — helping people understand how healthy the job market is and make better career decisions.

## Tech Stack

### Frontend
- Framework: React
- Styling: Tailwind CSS
- State: Zustand
- HTTP: TanStack Query

### Backend
- Language/Framework: Python / **FastAPI** (corrected 2026-08-16 — this said
  Flask from the original scaffold, but every backend module actually built
  (`main.py`, `admin_main.py`, and everything under `backend/src/`) is FastAPI;
  Flask was never used)
- Database: PostgreSQL
- Auth: JWT — used by the pipeline-visibility admin dashboard
  (`backend/src/admin_auth.py`); the consumer-facing `/api/*` routes have no
  auth yet (`backend/specs/market-health/api.md` — Tech Decisions)

## Running Locally

**Backend runs in WSL (Ubuntu); frontend runs in a normal Windows terminal (PowerShell or
Git Bash) — not WSL.** This isn't a preference, it's a hard requirement discovered empirically:
`frontend/node_modules` was installed on Windows and contains Windows-only native rollup
binaries (`@rollup/rollup-win32-x64-*`). Running `npm run dev` under WSL's Linux Node fails
with `Cannot find module @rollup/rollup-linux-x64-gnu` — npm's optional-dependency resolution
picks binaries for the OS it was installed on, and reinstalling under WSL would just flip the
problem (Linux binaries, then failing on Windows). Keep frontend on Windows, backend in WSL.

Open one **Ubuntu** terminal in VS Code (click the `+` dropdown in the terminal panel and select **Ubuntu**) for the backend, and use a regular Windows terminal for the frontend.

**Backend**
```bash

**Use Ubunto WSL as a terminal**
cd products/tech-market-intelligence-platform/backend/src
source venv_linux/bin/activate
uvicorn main:app --reload --port 8000
```
First time only — create the Linux venv and install deps:
```bash
python3 -m venv venv_linux
source venv_linux/bin/activate
pip install -r ../requirements.txt
```

Market Health's job-opening trends are backed by a real PostgreSQL database
(`raw_postings` + `classifications` — see `backend/specs/market-health/api.md`).
Set `DATABASE_URL` in `backend/.env` before starting the server; the schema is
created automatically on startup if missing. An externally hosted Postgres
(e.g. Railway) is the simplest option — it avoids WSL↔Windows localhost
networking friction entirely. To populate real data, run the ingestion
pipeline (fetches live postings from Greenhouse/Lever/Ashby — Adzuna was
retired 2026-08-03, see `changes/2026-07-28-multi-source-job-data-ingestion.md`
— then classifies them via Gemini):
```bash
cd products/tech-market-intelligence-platform/backend/src
source venv_linux/bin/activate
python ingest.py
```
Run it daily (cron or manual) to keep the dataset current. Until it's run at
least once, `/api/market-health/openings` returns empty series with a
"no data yet" summary — this is expected, not an error.

**Frontend** — run this in a **Windows terminal** (PowerShell or Git Bash), not the WSL Ubuntu terminal used for the backend:
```bash
cd products/tech-market-intelligence-platform/frontend
npm install   # first time only
npm run dev
```

- Backend: http://127.0.0.1:8000 — API docs at http://127.0.0.1:8000/docs
- Frontend: http://localhost:5173

**Live in production** (deployed 2026-08-16 — see `DEPLOYMENT.md`, "Service: `api`" /
"Service: `web`"): the product's real public entry point is
`https://web-production-03c43.up.railway.app`, backed by
`https://api-production-df13.up.railway.app`.

**Admin dashboard** (operator-only pipeline visibility — see
`backend/specs/pipeline-visibility/api.md`) — a separate FastAPI app, run the
same way as the main backend (`backend/src/`, same venv), just a different
entry point and port so it can run alongside `main.py` if you want both:
```bash
cd products/tech-market-intelligence-platform/backend/src
source venv_linux/bin/activate   # or the Windows venv, same as above
uvicorn admin_main:app --reload --port 8001
```
Needs `ADMIN_PASSWORD_HASH` and `ADMIN_JWT_SECRET` in `backend/.env` first —
generate a hash with `python -c "from admin_auth import hash_password; print(hash_password('your-password'))"`
(run from `backend/src/`). Set `ADMIN_COOKIE_SECURE=false` in `.env` for local
`http://` testing — the session cookie is `Secure` (HTTPS-only) by default,
which is correct in production but silently blocks login over plain local
HTTP. Then open http://127.0.0.1:8001/admin/login. Deployed in production as
its own Railway service — see `DEPLOYMENT.md`, "Service: `admin`".

---

## Automation Level
See `.outcome/config.yaml` for current role automation settings.

## Active Outcomes
<!-- Keep this updated as outcomes are added/delivered. -->
See `outcomes/` — current active outcomes are marked `status: active`.

## Spec Chain Status
Current state of the spec chain for this product (corrected 2026-08-16 — this
table said "Not started" for every layer despite all of it being built; kept
in sync with reality now, update it whenever a spec's status changes):

| Layer | Status |
|---|---|
| Design Foundations | ✅ Active (`design/foundations.md`, v1.1) |
| Information Architecture | ✅ Active (`design/information-architecture.md`, v2.2) |
| Visual Design | ✅ Active (`design/visual-design.md`, v1.1) |
| Experience Specs | ✅ `market-health` (ready), `ai-reasoning-panel` (ready), `pipeline-visibility` (ready) |
| Backend Specs | ✅ `pipeline-visibility`, `market-health` (both `ready`, implemented — `market-health`'s corrected 2026-08-16, see `changes/2026-08-16-production-cors-config.md`). ⚠️ `ai-reasoning-panel` (`status: draft` in the spec file itself — implemented and live regardless; stale, worth correcting next time it's touched) |
| Frontend Specs | ✅ `market-health`, `ai-reasoning-panel` (both implemented). `pipeline-visibility` has none by design — folded into its backend spec, server-rendered, no separate frontend build (see `changes/2026-08-13-admin-pipeline-dashboard.md`) |

## Change Log
See `changes/` — every change request is saved here with its signal, outcome reference,
impact map, and skill execution plan. Check here before starting any new change to avoid
duplicating work in progress.

## Key Constraints
<!-- Anything the AI must know to avoid wrong decisions. -->
- **Before touching `/api/chat` or anything conversation-history related**, read
  `backend/AI_INTERACTION_SETTINGS.md` — it explains why LLM conversation context is
  intentionally bounded (sliding windows, message-length caps), not just handed through in
  full. The actual enforced numbers live in `backend/src/ai_interaction_settings.py`, not in
  that doc, so they can't drift apart.
- **Before touching Railway deployment config or adding new services**, read
  `DEPLOYMENT.md` — the full product is live now (`Postgres`, `job-sync`, `admin`,
  `api`, `web` — all five services deployed as of 2026-08-16, `web`'s public domain
  is the product's real entry point), and the doc has eleven operational gotchas found
  the hard way across three real deploys — not just `railway.json` overriding
  dashboard config and auto-deploy being off, but also that API-set service config
  doesn't reliably persist, GitHub source needs the dashboard's real "Connect Repo"
  flow, config-as-code file paths aren't auto-discovered from root directory, a plain
  "redeploy" won't pick up a source/branch change, and Vite 5.4+'s host-checking
  needs disabling for `web`'s preview server. Read the full gotcha list before
  assuming any of this works the way it "should."
