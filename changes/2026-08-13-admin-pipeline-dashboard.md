---
id: admin-pipeline-dashboard
date: 2026-08-13
trigger-type: stakeholder-request
change-type: new-feature, api-change
outcome: pipeline-processing-visibility
status: complete
---

# Change Request: Admin Pipeline Visibility Dashboard

## Signal
See: `research/2026-08-13-admin-pipeline-dashboard.md`

## Outcome
See: `outcomes/pipeline-processing-visibility.md`

New outcome, created as part of this change request's triage — no existing outcome covered
operator-facing pipeline visibility (all four prior outcomes are either end-user-facing or
engineering-flexibility concerns, not observability).

## Change Type
`new-feature` — an admin-only view of pipeline processing status doesn't exist anywhere in
the product today.
`api-change` — requires new read-only endpoints over existing tables (`ingestion_runs`,
`classifications`, `posting_requirements`, `posting_skills`) and, since the product currently
has no auth middleware at all (`backend/specs/market-health/api.md`: "No auth middleware in
v1. Add it as a separate layer when needed"), a new auth layer to gate access to the
operator alone.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/pipeline-processing-visibility.md` | create — done |
| Design Foundations | `design/foundations.md` | review — confirm it doesn't assume a single (consumer-only) audience or a no-auth product; update only if it does |
| Experience Spec | `design/pipeline-visibility/experience.md` | create |
| Information Architecture | `design/information-architecture.md` | review — decide whether/how an operator-only surface is noted, even though it won't share navigation with the consumer app |
| Visual Design | `design/visual-design.md` | review — likely reuse existing tokens/components; confirm no gap (e.g. data-table/detail-drilldown patterns) |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | create — new endpoints, and the auth-mechanism decision (left open by the stakeholder; backend spec's existing "add a separate auth layer when needed" note and this product's `CLAUDE.md` naming JWT as the intended mechanism are both relevant inputs, not decisions) |
| Frontend Spec | `frontend/specs/pipeline-visibility/architecture.md` | **no-change — folded into backend spec.** The backend spec locked in server-rendered Jinja2 templates living inside `backend/`, not a separate `frontend/` build; there is no frontend-spec-shaped work left (no component breakdown, no client state, no API contract for a SPA to consume). Confirmed with the stakeholder at Step 5. |
| Backend Implementation | `backend/src/` | update — includes the admin dashboard's templates, since they live in `backend/` |
| Frontend Implementation | `frontend/src/` | no-change — nothing in this change touches `frontend/` |

## Execution Plan

- [x] Step 1: `/new-design-foundations` — reviewed `design/foundations.md` in full. Found a
      real conflict, not a no-op: the existing Product Paradigm (Agentic Conversational UI,
      mandatory for "every experience spec") and Principle 5 (Direct Manipulation of
      Outcomes, requiring every system output be user-editable) would have forced the new
      admin dashboard into a conversational, editable interface — directly contradicting
      `outcomes/pipeline-processing-visibility.md`'s explicit scope (read-only, no editing,
      no real-time/alerting). Confirmed with the user: the admin dashboard should be a plain
      traditional dashboard, not conversational. Added a new "Scope" section to
      `design/foundations.md` (v1.0 → v1.1) carving out internal/operational tooling from the
      Agentic Conversational UI paradigm and from Principle 5, as a default exemption
      individual internal-tooling outcomes can still opt back into.
- [x] Step 2: `/new-experience` — created `design/pipeline-visibility/experience.md` (status:
      ready). Traditional sidebar + main-content dashboard (Overview → Postings → Posting
      Detail, plus Ingestion Runs), explicitly outside the consumer product's three-column
      conversational IA — flagged as an open question for Step 3. Reuses all existing
      `design/visual-design.md` tokens rather than inventing new ones. Specifies classification
      distribution / taxonomy-version-progress / requirements-coverage charts, an
      Interactions table, and edge cases (no data yet, Pending vs. Failed requirements status,
      mixed taxonomy versions mid-reprocessing, `unknown` values as honest signal not error,
      table pagination, partial run failures). Auth mechanism and IA/visual-design gap checks
      left as open questions for Steps 3–5, per the change request's Decision Log.
- [x] Step 3: `/new-information-architecture` — reviewed `design/information-architecture.md`
      in full (v2.1). Not a no-op: added a new "Scope" section (v2.1 → v2.2) clarifying the
      document governs the consumer-facing product only, explicitly naming the admin
      pipeline-visibility dashboard as an out-of-model example — its Sidebar Nav / Main
      Content terms are deliberately absent from the Content Taxonomy and must not be
      confused with the consumer product's vocabulary. Mirrors `design/foundations.md`
      v1.1's own Scope carve-out. No new consumer-facing navigation terms invented.
- [x] Step 4: `/new-visual-design` — reviewed `design/visual-design.md` in full (v1.0). Found
      a real, small gap, not a no-op: colour/type/spacing tokens already fully cover the
      admin dashboard's needs (confirmed — the existing Semantic colours table maps exactly
      onto Extracted/Pending/Failed/`unknown` with zero new colours needed), but three
      component patterns didn't exist yet — data tables, filter chips, and status
      badges/pills — plus a layout entry for the sidebar+main-content shape (distinct from
      the three-column model, per the Scope carve-outs already in foundations v1.1 and IA
      v2.2). Added all four as new subsections (v1.0 → v1.1), each built entirely from
      existing tokens.
- [x] Step 5: `/new-backend-spec` — created `backend/specs/pipeline-visibility/api.md`
      (status: ready). **Deployment**: new `admin` Railway service rooted at `backend/`
      (`backend/src/admin_main.py`), own domain, own start command, server-rendered Jinja2 —
      no separate frontend build. **Auth, decided**: JWT login + httpOnly session cookie
      (not bare shared-secret Basic Auth) — matches this product's `CLAUDE.md`-stated intended
      mechanism rather than silently diverging; single bcrypt-hashed operator password in an
      env var, no user table, 24h expiry, no refresh flow. **Real finding, not a silent
      scope-cut**: the pipeline never recorded per-posting extraction failures before this
      spec — confirmed with the stakeholder, who asked for it to be built now rather than
      deferred. Added one small additive table (`posting_requirements_failures`) plus
      `raw_postings.ingestion_run_id` (both idempotent `ALTER`/`CREATE ... IF NOT EXISTS`
      migrations, same pattern as every prior migration in `backend/specs/market-health/api.md`).
      This means `/implement-backend` for this spec also touches the real, already-running
      extraction pipeline (`backend/src/requirements.py` gains failure-recording on the
      write path), not only new `/admin/*` read routes — called out explicitly in the spec.
      Requirements Status is now a genuine four-state model: Extracted / Failed / Not
      eligible / Pending.
- [x] Step 6: `/new-frontend-spec` — **skipped, confirmed with the stakeholder.** No separate
      frontend-spec work exists: the backend spec's server-rendered Jinja2 templates
      (`overview.html`, `postings.html`, `posting_detail.html`, `runs.html`, `run_detail.html`,
      `login.html`) are already fully specified as part of `backend/specs/pipeline-visibility/api.md`'s
      API Endpoints section. Frontend Spec row in Specs Affected updated to `no-change`.
- [x] Step 7: `/implement-backend` — built and verified against the real production
      database (Railway Postgres, `backend/.env`'s `DATABASE_URL`), not just compile-checked:
      **New files**: `backend/src/admin_main.py` (separate FastAPI app, all 8 routes from the
      spec), `backend/src/admin_auth.py` (JWT + bcrypt auth), `backend/src/admin_templates/*.html`
      (7 Jinja2 templates), `backend/src/admin_static/admin.css` (hand-written, matching
      `design/visual-design.md` v1.1's tokens exactly — no Tailwind CDN, since that needs
      client-side JS and this spec ruled that out).
      **Migrations**: `raw_postings.ingestion_run_id` + `posting_requirements_failures` table
      added to `db.py`, ran successfully against the real database — confirmed via direct
      schema query (`information_schema`) that both landed correctly.
      **Real design refinement found during implementation**: the backend spec said
      `insert_new_postings()` would "accept and set the current run's id" — checking the real
      code, that's impossible as written, since `ingestion_runs.record_run()` only inserts its
      row at the *end* of `ingest.py`'s `run()`, well after postings are already inserted
      during the fetch phase. Fixed with a more accurate design: `record_run()` now returns
      the new row's id (`RETURNING id`), and a new `raw_postings.attach_ingestion_run()`
      backfills `ingestion_run_id` in one UPDATE right after — wired into both of `ingest.py`'s
      `record_run()` call sites (success and failure paths).
      **`requirements.py` failure-tracking**: `record_extraction_failure()` wired into the
      real retry-exhaustion path in `extract_requirements()`. Caught a real correctness gap
      while writing this report, not just during coding: my first pass called a separate
      `clear_extraction_failure()` right after `insert_requirements()`, each opening its own
      connection — which is *not* the same transaction the backend spec calls for, and leaves
      a real (if narrow) crash window where a posting could end up with rows in both
      `posting_requirements` and `posting_requirements_failures` at once. Fixed by folding the
      failure-clear `DELETE` directly into `insert_requirements()`'s own connection/cursor, and
      removed the now-dead standalone `clear_extraction_failure()` function rather than leaving
      unused code. Re-verified `admin_main.py` and `requirements.py` still import cleanly and
      all 14 routes register after the fix. Verified: `get_all_needing_requirements()` is
      untouched, so failed postings stay in the real retry backlog — only visibility changed.
      **Real dependency bug caught by testing, not assumed away**: `passlib[bcrypt]` (spec'd
      originally) is unmaintained and breaks against `bcrypt>=4.0`
      (`AttributeError: module 'bcrypt' has no attribute '__about__'`, then a bogus
      72-byte-truncation `ValueError`) — hit this for real while verifying `verify_password()`.
      Switched to calling `bcrypt` directly (`admin_auth.hash_password`/`verify_password`),
      removed `passlib` from `requirements.txt`, documented the reasoning inline.
      **End-to-end verification against real data** (temporary local server, real Postgres,
      test credentials never committed): `count_postings()` → 5,451; classification
      distribution, taxonomy version breakdown (100% now on `2026-08-11` — the reprocessing
      backlog from `changes/2026-08-11-classification-taxonomy-redesign.md` has fully drained
      since it was last checked), requirements coverage (1,427/2,778 = 51.4%), skill group
      distribution, `list_postings()` with real filters/sort, `get_posting()` full detail
      (including a genuine `level: "unknown"` posting rendering the correct amber badge),
      `list_runs()`/`get_run()` — all returned correct real results. Full HTTP flow tested with
      curl against a real running instance: wrong password → 401 inline error; correct
      password → session cookie set, 303 redirect; unauthenticated access to any `/admin/*`
      route → 303 to `/admin/login`, zero data leaked; authenticated Overview/Postings/Posting
      Detail/Runs/Run Detail all → 200 with correct real content; missing posting/run → 404;
      logout → cookie cleared, subsequent access redirects again. Static CSS mount verified
      serving. Test server and all background processes cleanly stopped after verification.
      **One deliberate simplification, noted not hidden**: 404s render as FastAPI's default
      JSON error rather than a styled HTML error page — acceptable for an internal single-operator
      tool, not built out further given scope.
      **Docs**: `DEPLOYMENT.md` updated with the new `admin` service (mirrors the existing
      `api`/`web` "Planned" section's format), including an explicitly flagged open question
      it shares with `api` — multiple services rooted at `backend/` all needing their own
      Railway config-as-code file, not yet resolved for any of them.
      **`backend/requirements.txt`/`backend/.env.example`** updated with the new dependencies
      and env vars (`ADMIN_PASSWORD_HASH`, `ADMIN_JWT_SECRET`, `ADMIN_COOKIE_SECURE`).

## Decision Log
- 2026-08-13: No existing outcome covered this — created `pipeline-processing-visibility`
  during triage rather than forcing this under `understand-market-health-before-searching`
  (different audience: operator vs. job seeker) or the two flexibility outcomes (different
  concern: observability vs. swappability).
- 2026-08-13: Priority set to `medium` — real internal-tooling need, not blocking the
  user-facing product (same tier as `ai-provider-flexibility`).
- 2026-08-13: Auth mechanism deliberately left undecided at triage — stakeholder asked for it
  to be raised as an open question for the backend spec rather than settled here. Relevant
  inputs for that spec: `backend/specs/market-health/api.md` already anticipates "add a
  separate auth layer when needed," and this product's `CLAUDE.md` tech stack section names
  JWT as the intended mechanism, though nothing using it exists yet.
- 2026-08-13: Classified as `new-feature` + `api-change`, not `technical-refactor` — this adds
  a genuinely new, if operator-only, user-facing (to an audience of one) capability, not just
  internal restructuring.
- 2026-08-14: Deployment/access topology decided (to be formalized in Step 5's backend spec
  and eventually `DEPLOYMENT.md`): the admin dashboard is a **new backend-rooted Railway
  service**, not a new git repo and not part of `frontend/`. Same repo
  (`products/tech-market-intelligence-platform`), same `backend/` directory — a new entry
  point (e.g. `backend/src/admin_main.py`) reusing existing DB access code, exposing only
  read-only admin routes, server-rendering its own HTML (no separate Vite/React build).
  Deployed as its own Railway service with its own start command and its own generated
  domain, mirroring the existing precedent of `job-sync` and the planned `api` both being
  separate services rooted at the same `backend/` directory. This gives two layers of
  access protection: domain separation (the admin UI's code never ships in `web`'s public JS
  bundle, and lives at a different origin entirely) plus authentication (mechanism still
  open, to be decided in Step 5) — domain separation is defense-in-depth, not a substitute
  for auth.
- 2026-08-16: Auth mechanism resolved at Step 5 — JWT login + session cookie, confirmed with
  the stakeholder. Requirements Status expanded from the three-state model the backend spec
  initially proposed (Extracted/Pending/Not eligible, omitting per-posting failures as not
  currently trackable) to a real four-state model including `Failed` — the stakeholder chose
  to add the small tracking mechanism now rather than defer it. Frontend-spec step (Step 6)
  confirmed skippable given the server-rendered architecture decided in Step 5 — no
  component/state/API-contract work exists for a spec to describe.
- 2026-08-16 (post-completion): deployed to Railway — service `romantic-presence` in the
  `feisty-grace` project, live at `https://romantic-presence-production.up.railway.app`.
  This happened after this change request was already marked `complete` (deployment was
  explicitly left open as future operational work, not spec/implementation work); recorded
  here only as a pointer, not reopening the checklist. Initially deployed from a temporary
  branch (`admin-pipeline-dashboard`) while being debugged; once working, merged into `main`
  and the service repointed there, and the now-fully-merged branch deleted (both locally and
  on GitHub) — `main` is the only branch this work lives on now, matching `job-sync`'s
  existing convention and avoiding two long-lived branches silently diverging on the
  `backend/src/` modules the two services share. Full deployment record — service config
  and nine gotchas found across both this and `job-sync`'s original deploy — lives in
  `DEPLOYMENT.md` under "Service: `admin`", the same place `job-sync`'s own deployment story
  already lives.
