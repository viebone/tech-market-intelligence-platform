---
source: stakeholder-request
date: 2026-08-16
---

While preparing to deploy the consumer-facing app (`api` + `web` services on
Railway/Vercel, alongside the already-deployed `job-sync` and `admin` services),
found that `backend/src/main.py`'s CORS middleware hardcodes `allow_origins` to
`localhost`/`127.0.0.1` only (ports 3000/5173/4173):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:5173", "http://localhost:4173",
        "http://127.0.0.1:3000", "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Once `web` is deployed to a real domain, `api` will reject every cross-origin
request from it — the deployed frontend would be completely non-functional
against the deployed backend, not just degraded. This blocks the `api`+`web`
deployment currently being planned.

No user-facing behavior changes for anyone who already reaches the app locally
— this only fixes what is currently a hard block on the app being reachable in
production at all. Existing, already-implemented backend code (`main.py`, part
of the market-health backend) needs its CORS configuration made
production-ready — e.g. an env-var-driven allowed-origins list, so the actual
`web` domain(s) can be configured per-environment rather than hardcoded to
localhost.
