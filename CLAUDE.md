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

---

## What we're building
A market intelligence platform for UX and other tech professionals that automatically tracks hiring demand, skills, salaries, and layoffs — helping people understand how healthy the job market is and make better career decisions.

## Tech Stack
<!-- To be defined before first implementation. -->

### Frontend
- Framework: React
- Styling: Tailwind CSS
- State: Zustand
- HTTP: TanStack Query

### Backend
- Language/Framework: Python / Flask
- Database: PostgreSQL
- Auth: JWT

## Running Locally

Requires WSL (Ubuntu). Open two **Ubuntu** terminals in VS Code (click the `+` dropdown in the terminal panel and select **Ubuntu**).

**Backend**
```bash
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

**Frontend**
```bash
cd products/tech-market-intelligence-platform/frontend
npm install   # first time only
npm run dev
```

- Backend: http://127.0.0.1:8000 — API docs at http://127.0.0.1:8000/docs
- Frontend: http://localhost:5173

---

## Automation Level
See `.outcome/config.yaml` for current role automation settings.

## Active Outcomes
<!-- Keep this updated as outcomes are added/delivered. -->
See `outcomes/` — current active outcomes are marked `status: active`.

## Key Constraints
<!-- Anything the AI must know to avoid wrong decisions. -->
- 
