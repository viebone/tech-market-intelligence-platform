---
id: production-deploy-readiness
source: business
priority: high
status: active
created: 2026-08-16
---

# Outcome: A newly deployed service works for real users immediately, not just in local dev

## Signal
See: `research/2026-08-16-production-cors-config.md`

While preparing to deploy the consumer-facing app (`api` + `web`), found
`backend/src/main.py`'s CORS middleware hardcodes `allow_origins` to
`localhost`/`127.0.0.1` only — once `web` has a real domain, `api` would
reject every request from it. The deployed frontend would be completely
non-functional against the deployed backend, not just degraded.

## Context
Local dev environments are permissive in ways production environments are
not — same-origin dev servers, dev-only proxies that quietly paper over
cross-origin issues. Configuration that only matters once something is
actually deployed (CORS allow-lists, environment-scoped secrets, absolute
vs. relative URLs) has no local signal that it's wrong until a real deploy
exposes it — often as a silent, total failure (a frontend that loads but
can't reach its API at all) rather than a clear error anyone would notice
before a real user does.

This product is now deploying its first real user-facing services (`api` +
`web`, joining the already-deployed `job-sync` and `admin`). The CORS gap
is the first concrete instance, but not the last — any future service faces
the same class of gap unless it's checked for deliberately, the same way
`DEPLOYMENT.md` already accumulates real gotchas per service as each one is
actually deployed for the first time.

## Success looks like
- A service that works in local dev is verified against its real deployed
  environment before being called done — never assumed to "just work" the
  same way it does locally
- Environment-specific configuration (allowed origins, callback URLs,
  absolute vs. relative paths) is never hardcoded to localhost-only values
  in code that also runs in production
- When a new service is deployed, its ability to actually be reached and
  used by its real caller (a browser, another service) is confirmed —
  not just that the container started successfully
- A production-only failure mode (e.g. a rejected cross-origin request) is
  caught and fixed before real users hit it, not discovered via a bug report

## Out of scope
- General security hardening beyond what's needed for the app to function
  correctly (rate limiting, WAF rules, etc. are a separate concern)
- Building new deployment-testing infrastructure (a full CI/CD pipeline with
  staging environments) — this outcome is about catching known gap classes
  deliberately as each service deploys, not about new tooling
- Retroactively auditing every existing service for this class of issue in
  one pass — addressed as each service reaches its own real deploy, matching
  this product's existing "learn each service's real gotchas as it deploys"
  pattern already documented in `DEPLOYMENT.md`
