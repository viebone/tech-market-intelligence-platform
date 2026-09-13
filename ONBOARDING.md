# Onboarding — Tech Market Intelligence Platform

A guided reading path for someone new to this product — what to read, in what order, and why.
Total is roughly 90 minutes for a solid mental model. Tiers 1–4 are essential; 5 is code, read
once the specs make sense; 6 is a reference, not a read-through.

If a linked file mentions a decision you want the full story on, search `changes/` for it —
every change ever made lives there, in order, each with its trigger and reasoning.

---

## 1. Orientation (10 min)

- [`CLAUDE.md`](CLAUDE.md) — start here. What this product is, the tech stack, the spec-chain
  status table (what's built vs. pending), key constraints, and pointers to everything else.
- [`DATA_SOURCES.md`](DATA_SOURCES.md) — the master reference for every external data source
  this platform touches (job boards **and** employment-event registries): what's live, what
  isn't, and the control-lever index (env vars, keys, tunables) mapped to the file that owns
  each one. Open this whenever "where does X data come from" comes up.

## 2. Why it exists (15 min) — `outcomes/`

Each is one page, written from real user research. Read in this order:

1. [`outcomes/understand-market-health-before-searching.md`](outcomes/understand-market-health-before-searching.md)
   — the core outcome. Everything in Market Health traces back to this.
2. [`outcomes/job-data-source-flexibility.md`](outcomes/job-data-source-flexibility.md) — why
   the source-adapter architecture exists.
3. [`outcomes/pipeline-processing-visibility.md`](outcomes/pipeline-processing-visibility.md)
   — why the admin dashboard exists.
4. [`outcomes/ai-reasoning-transparency.md`](outcomes/ai-reasoning-transparency.md) — why
   there's a Reasoning Panel.
5. [`outcomes/ai-provider-flexibility.md`](outcomes/ai-provider-flexibility.md) and
   [`outcomes/llm-spend-is-bounded-and-isolated.md`](outcomes/llm-spend-is-bounded-and-isolated.md)
   — the AI provider/cost architecture.
6. [`outcomes/production-deploy-readiness.md`](outcomes/production-deploy-readiness.md) — the
   deployment/ops bar.

## 3. How it's meant to feel and be organized (15 min) — `design/`

- [`design/foundations.md`](design/foundations.md) — UX principles, and critically, **AI
  Involvement**: this product is AI-native, chat is the primary interface, not a bolt-on.
- [`design/information-architecture.md`](design/information-architecture.md) — the navigation
  model and the exact vocabulary every other spec uses (Task Panel, Working Space, Output
  Panel, Layoff Signal, and so on).
- [`design/visual-design.md`](design/visual-design.md) — colour, type, spacing, and Data
  Legibility (how every chart/metric/colour is required to explain itself).
- [`design/market-health/experience.md`](design/market-health/experience.md) — **the big
  one.** The main feature's full UX: opening chat, trend chart, Layoff Signal, all of it.
- [`design/market-health/data-stories.md`](design/market-health/data-stories.md) — the two
  deterministic "data stories" (What we know about the market / Employment risk across the
  market) — fixed-structure, no-LLM answers.
- [`design/pipeline-visibility/experience.md`](design/pipeline-visibility/experience.md) —
  the operator-only admin dashboard's UX.
- [`design/ai-reasoning-panel/experience.md`](design/ai-reasoning-panel/experience.md) — the
  "show your work" transparency panel.
- Skim only if curious: [`design/market-health/job-classification.md`](design/market-health/job-classification.md),
  [`design/market-health/conversation-turn.md`](design/market-health/conversation-turn.md),
  [`design/market-health/provenance-panel.md`](design/market-health/provenance-panel.md).

## 4. How it's actually built (20 min) — specs

- [`backend/specs/market-health/api.md`](backend/specs/market-health/api.md) — **the biggest,
  most important spec in the repo.** Data models (`RawPosting`, `EmploymentEvent`, etc.),
  every source adapter contract, all business logic, the chat tools. Read this one if you
  read nothing else in this tier.
- [`backend/EMPLOYMENT_EVENTS.md`](backend/EMPLOYMENT_EVENTS.md) — plain-language companion
  to the above, specifically for the employment-events table: schema, immutability, real
  per-source field coverage, and the history of every decision that shaped it.
- [`backend/specs/pipeline-visibility/api.md`](backend/specs/pipeline-visibility/api.md) —
  the admin dashboard's routes and business logic.
- [`backend/specs/ai-reasoning-panel/api.md`](backend/specs/ai-reasoning-panel/api.md) —
  reasoning-trace shape.
- [`frontend/specs/market-health/architecture.md`](frontend/specs/market-health/architecture.md)
  — component breakdown, state management.
- [`frontend/specs/ai-reasoning-panel/architecture.md`](frontend/specs/ai-reasoning-panel/architecture.md).
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — Railway topology: which service is which (`web`, `api`,
  `job-sync`, `employment-events`, `romantic-presence`, `Postgres`) and the operational
  gotchas found the hard way.

## 5. The code, once the specs make sense

Backend, in this order:

1. [`backend/src/db.py`](backend/src/db.py) — the whole schema in one place.
2. [`backend/src/main.py`](backend/src/main.py) — the consumer API app;
   [`backend/src/admin_main.py`](backend/src/admin_main.py) — the separate admin app.
3. [`backend/src/sources/`](backend/src/sources/) +
   [`backend/src/ingest.py`](backend/src/ingest.py) — the job-posting pipeline
   (Greenhouse/Lever/Ashby adapters).
4. [`backend/src/employment_events/`](backend/src/employment_events/) +
   [`backend/src/ingest_employment_events.py`](backend/src/ingest_employment_events.py) — the
   layoff/employment pipeline (Eurofound ERM, US WARN, UK Companies House, SEC EDGAR) — read
   `employment_events/__init__.py`'s own module docstring, it's a self-contained explainer.
5. [`backend/src/chat.py`](backend/src/chat.py),
   [`backend/src/market_query.py`](backend/src/market_query.py),
   [`backend/src/market_stories.py`](backend/src/market_stories.py) — where postings and
   events actually become chat answers and data stories.

Frontend: `frontend/src/features/market-health/` — start with `MarketHealthPage.tsx`, then
`DataStoryMessage.tsx` and its shared components (`StoryBlock`, `RankedBarList`, `Meter`,
`YearOnYearBars`).

## 6. Reference, not a read-through

`changes/` — every change ever made, in chronological order, each with its trigger, the specs
it touched, and a decision log. Don't read it top to bottom; when something in the code looks
odd, search it for the relevant date or feature name — the "why" is almost always there.
