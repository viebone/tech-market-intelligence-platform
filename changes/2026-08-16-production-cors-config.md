---
id: production-cors-config
date: 2026-08-16
trigger-type: stakeholder-request
change-type: api-change, technical-refactor
outcome: production-deploy-readiness
status: complete
---

# Change Request: Production-Ready CORS Configuration

## Signal
See: `research/2026-08-16-production-cors-config.md`

## Outcome
See: `outcomes/production-deploy-readiness.md`

New outcome, created as part of this change request's triage — no existing outcome covered
"a deployed service actually works for real users, not just locally"; the closest candidates
(`understand-market-health-before-searching`, `ai-provider-flexibility`,
`job-data-source-flexibility`) are about experience quality once reached or engineering
flexibility, not reachability itself.

## Change Type
`api-change` — `backend/src/main.py`'s CORS middleware configuration changes from a hardcoded
localhost-only allow-list to an environment-driven one.
`technical-refactor` — no new user-facing capability; existing, already-implemented code made
production-ready. Nothing changes for anyone already reaching the app locally.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/production-deploy-readiness.md` | create — done |
| Design Foundations | `design/foundations.md` | no-change — doesn't affect UX principles |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | review — confirm no-change; CORS is invisible to the user by design (it either silently blocks everything or gets out of the way, never a visible UX difference) |
| Backend Spec | `backend/specs/market-health/api.md` | update — add a Tech Decision documenting the production CORS approach, same precedent as its existing "No auth middleware in v1. Add it as a separate layer when needed" entry |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | no-change — API contract (paths, request/response shapes) is unchanged; only which origins are allowed to call it changes |
| Backend Implementation | `backend/src/main.py` | update — the actual fix |
| Frontend Implementation | `frontend/src/` | no-change |

**Explicitly out of scope for this change** (per the stakeholder's own framing, still an open
decision): how `web` will actually reach `api` in production (host-level reverse proxy vs. a
frontend code change to call an absolute URL) — that's `web`'s hosting decision, not yet made,
and doesn't block fixing `api`'s CORS gap on its own.

## Execution Plan

- [x] Step 1: `/new-experience` — reviewed `design/market-health/experience.md` in full,
      including its entire Edge Cases section. Confirmed no-change: every edge case there
      (insufficient data, no data, unanswerable questions, coverage limits, compensation
      confidence) assumes the API is reachable and describes data-quality gaps, not
      connectivity failure — exactly matching this change's premise that CORS is invisible
      when working. **Real, separate finding, not part of this change's scope**: the spec
      has no edge case at all for "the request to the backend itself failed" (network error,
      5xx, or a CORS rejection) — yet `frontend/src/pages/MarketHealthPage.tsx` already wires
      an `onRetry={() => openingsQuery.refetch()}` handler, meaning *some* failure-state UI
      was already built without ever being speced or reviewed against Designer intent. Not
      fixed here (scope creep beyond this CORS change) — worth a future `/change-request` if
      this gap should be closed properly.
- [x] Step 2: `/new-backend-spec` — updated `backend/specs/market-health/api.md`'s Tech
      Decisions with the production CORS approach: a new `CORS_ALLOWED_ORIGINS` env var
      (comma-separated), appended to — never replacing — the existing hardcoded local-dev
      origin list, so local dev is unaffected whether or not it's set. Chose a wildcard-free,
      append-only, multi-origin-capable design: wildcard ruled out (incompatible with the
      already-set `allow_credentials=True`), single-origin env var ruled out (more than one
      real origin is plausible over time — custom domain + host-generated preview domain).
      Also corrected this spec's own stale `status: draft` → `ready` while touching it
      (flagged as stale in `CLAUDE.md`'s Spec Chain Status table during the pipeline-visibility
      work) — it's been implemented and live the whole time, `updated` bumped to 2026-08-16.
- [x] Step 3: `/new-frontend-spec` — reviewed `frontend/specs/market-health/architecture.md`
      in full. Confirmed no-change: no endpoint, request/response shape, or SSE contract
      changes; this spec's fetch calls are relative paths, unaffected by the backend's
      allowed-origins list, which is enforced entirely server-side. Added a "Reviewed
      2026-08-16" entry following this file's own established review-log convention (6th
      consecutive no-op, but confirmed by reading, not assumed).
- [x] Step 4: `/implement-backend` — updated `main.py`: local-dev origins now live in a
      named `_LOCAL_DEV_ORIGINS` constant (unchanged values), a new `_production_origins`
      list is parsed from `CORS_ALLOWED_ORIGINS` (comma-separated, `.strip()`ped, empty
      values dropped), and `allow_origins` is the concatenation of both — never a
      replacement. `backend/.env.example` documents the new var. **Verified against real
      HTTP behavior, not just code review**: restarted the local server three ways —
      (1) unset, confirmed local dev origins still work and production list is empty;
      (2) `CORS_ALLOWED_ORIGINS="https://app.example.com, https://staging-app.example.com"`
      (deliberately with a stray space), confirmed both parsed correctly; (3) live CORS
      preflight requests against the running server with three different `Origin` headers —
      `http://localhost:5173` → allowed, `https://app.example.com` (the configured one) →
      allowed, `https://evil-random-site.com` (unlisted) → correctly rejected, no
      `Access-Control-Allow-Origin` header returned. Test server stopped, normal local
      backend (no `CORS_ALLOWED_ORIGINS` set, matching real local `.env`) restarted
      afterward. Also updated `DEPLOYMENT.md`'s "Planned: deploying `api`" env-var list to
      include `CORS_ALLOWED_ORIGINS`, so it isn't rediscovered as a surprise at that
      deploy — same discipline as documenting `admin`'s real gotchas after its deploy.

## Decision Log
- 2026-08-16: Tracked against new outcome `production-deploy-readiness` — created during
  triage since nothing existing covered production reachability as its own concern.
  Priority `high` — actively blocking the `api`+`web` deployment currently being planned.
- 2026-08-16: Classified as `api-change` + `technical-refactor`, not `bug-fix` — the current
  localhost-only CORS list isn't wrong for what's shipped so far (nothing has ever been
  deployed to a real domain yet), it's just not yet extended to cover the production case
  about to exist.
- 2026-08-16: `web`'s hosting/proxy decision deliberately excluded from this change's scope —
  it's a separate, still-open decision (reverse proxy vs. frontend code change) that doesn't
  block fixing `api`'s CORS gap on its own terms.
