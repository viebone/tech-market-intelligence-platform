source: internal
date: 2026-09-30

Flagged 2026-09-27 (`changes/2026-09-26-personio-adapter.md` Decision Log) and again in the
2026-09-28 roadmap discussion, never fixed until now:

> "a transient Postgres connection timeout hit mid-loop on `ashby`, right after `thought-machine`'s
> fetch succeeded — it wasn't caught by the per-company `SourceFetchError` isolation (that only
> wraps the *fetch*, not the DB write in `insert_new_postings`), so it aborted the rest of that
> adapter's company loop for this run. `thought-machine`'s possible new postings and a same-day
> refresh of `zego` (the last company in Ashby's list...) were skipped this run only... Worth a
> small follow-up (wrap the DB write in the same per-company isolation Greenhouse/Lever/Ashby/
> Workable/Personio fetches already have) — not fixed here, flagged for its own change request."

Root cause confirmed by reading `ingest.py`: `ingest_company()`'s own docstring promises
"Never raises" and cites the per-company fault-isolation rule, but only the fetch call
(`adapter.fetch_company(company)`) was wrapped in a try/except (`SourceFetchError`). The
`insert_new_postings(...)` call right after it was unguarded — any exception there (a DB
connection timeout, a constraint violation, anything) propagated straight out of
`ingest_company()`, was caught only by `run()`'s **adapter-level** try/except, and aborted every
remaining company in that adapter's `companies` list for the rest of the run, not just the one
company that hit the transient failure.

Confirmed safe to fix with a broad `except Exception`: both `existing_ids()` and the insert
itself open their own connection via `with get_connection()`, so a failure here can't leave a
partial write needing a rollback — the same reasoning that already justifies broad exception
handling on the fetch side.
