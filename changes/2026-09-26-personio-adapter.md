---
id: personio-adapter
date: 2026-09-26
trigger-type: stakeholder-request
change-type: new-feature
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Build a Personio source adapter (easiest of the parked candidates)

## Signal
See: `research/2026-09-26-easiest-parked-source-adapter.md`

User asked to start with the easiest of the sources parked by
`changes/2026-09-23-us-eu-employer-panel-expansion.md`. Live probing on 2026-09-26 ranked
**Personio** easiest: a keyless, per-company public XML feed that Personio's own docs describe
as credential-free, same shape as the Workable adapter. Recruitee (undocumented unauthenticated
endpoint, docs say a token is required), Arbeitnow (aggregator, no published terms), Jobicy
(attribution + apply-redirect duties), France Travail and USAJOBS (registration/credentials)
are each a later, separate change request.

## Outcome
See: `outcomes/job-data-source-flexibility.md` — a new adapter mechanism, the 5th ATS adapter.
Also directly serves the continental-EU stratification goal of the US + EU panel CR (Personio is
DACH-heavy; Personio itself was one of the 67 "no resolvable board" candidates).

## Change Type
`new-feature` — a genuinely new ATS mechanism, not a company-list edit. Same recipe and same
"data acquisition only, no experience spec" precedent as `changes/2026-09-19-workable-adapter.md`
(`DATA_SOURCES.md` §1: new class in `backend/src/sources/`, register in `ALL_SOURCE_ADAPTERS`).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | no-change |
| Design Foundations / IA / Visual Design | — | no-change |
| Experience Spec | none (deliberate, per every prior adapter's precedent) | no-change |
| Frontend Spec / Implementation | — | no-change |
| Backend Spec | `backend/specs/market-health/api.md` | update — `source` closed set, Protocol snippet |
| Backend Implementation | `backend/src/sources/personio.py` (new), `sources/__init__.py`, `source_licences.py`, `industries.py`, `admin_main.py` (filter list), tests | update |
| Docs | `DATA_SOURCES.md` (§3 row, §4 count, §7), `LICENSING.md` (new row), `EMPLOYER_PANEL.md` (backlog), product `CLAUDE.md` count if it lists adapters | update |
| Plain-Language Overview | `OVERVIEW.md` | no-change — more of the same existing "job demand" capability; checked states no adapter or company count |
| MCP Access Review | `ACCESS.md` | no-change — existing tools already cover any `raw_postings` source; no new capability |
| Polite Scraping Review | `DATA_SOURCES.md` | not-applicable in the Rule 13 sense — a documented, credential-free published feed, not a scraped page (no HTML parsing) — **but** see Decision Log: the same pacing/identification discipline applies, and the licence record is still mandatory |
| Data Surface Review | — | no-change — more rows of the existing `raw_postings` shape; flows through existing stories/admin/query path |

## Execution Plan

- [x] ✅ Step 1: Close the open terms question — Personio's developer docs state no restriction on reading the feed, but the support FAQ (403 to the fetch tool) was not read. Read it directly (browser or `curl`) and record the finding; if it prohibits third-party use, stop and mark Blocked like Workday/Taleo — **Done 2026-09-26**: the FAQ was readable via curl; it states "you don't need credentials", the feed may be used on multiple websites, and recommends syncing at most hourly. The API Use Policy covers the authenticated partner API only. No restriction on third-party reads found, no grant either — recorded as "no formal licence, nothing restricting" (same as Greenhouse/Workable)
- [x] ✅ Step 2: Real-data shape research — fetch 3–5 real Personio boards (incl. `?language=en`); confirm multi-office handling (`office` + `additionalOffices`), `jobDescriptions` (empty on `personio`'s own board — check whether it is populated elsewhere), `createdAt`, and whether any salary field exists; note that the XML is not JSON, so `raw_response` needs a defined verbatim form (position XML → dict) — **Done**: 4 boards read (personio 1, stark 131, capmo 8, moss 0, bounti 3, choco 2 stale 2017 roles); findings in the adapter docstring
- [x] ✅ Step 3: Build `backend/src/sources/personio.py` — `PacedFetcher`, XML parse (stdlib `xml.etree` with safe defaults), one `FetchedPosting` per `<position>` id, `source_ref = "{company}/{id}"`, country from office via `normalize_country()` where derivable, never guessed; language handled explicitly (English feed where available, native otherwise)
- [x] ✅ Step 4: Register in `ALL_SOURCE_ADAPTERS`, `source_licences.py` (real entry, attribution text, `licence_url`, `confirmed` set honestly from Step 1), `industries.py`, `admin_main.py` filter list
- [x] ✅ Step 5: Seed `COMPANIES` with a small verified set (Personio's own board + a few real DACH/EU employers, each content-inspected, no false positives) — **local, small; expansion stays a separate gated operation** per the LLM budget constraint
- [x] ✅ Step 6: Tests (fixture XML incl. multi-office, empty descriptions, 404 board, malformed XML → `SourceFetchError`) + `test_source_licences.py` still passes
- [x] ✅ Step 7: Update `backend/specs/market-health/api.md`, `DATA_SOURCES.md`, `LICENSING.md`, `EMPLOYER_PANEL.md`
- [x] ✅ Step 8: Verify end-to-end against real boards (adapter returns real postings, unique `source_ref`s, `main.py`/`ingest.py` import cleanly). Check classification copes with German-language postings on a sample **before** the first production ingest (carries over the open Step 5 of the US + EU panel CR) — **Done**: live fetch of all three seed boards through the real adapter (1 / 131 / 8 postings, unique refs, JSON-storable), a nonexistent slug -> `SourceFetchError`, `ingest` imports, `test_personio` 8/8, `test_source_licences`, `test_employer_headcount`, `test_trusted_stats` (55), `test_periodic_sources`, `test_mcp_access` all pass. **German classification sample-check — done 2026-09-26, 2 LLM requests, nothing written to the DB** (see Decision Log). `main.py` does not import locally because the `mcp` package is missing from the local venv — pre-existing (fails identically with these changes stashed)
- [x] ✅ Step 9: Committed (`969a130`), pushed, and a real production run executed 2026-09-27 (ingestion_run id 77) — see Decision Log

## Decision Log
- 2026-09-26: Chose Personio as easiest — the only candidate that is keyless, per-company (fits the existing adapter model with no aggregator dedupe), *and* documented by its vendor as credential-free. Recruitee's official docs say its Careers Site API needs a token, so its unauthenticated endpoint is a permission grey area; Arbeitnow/Jobicy/France Travail/USAJOBS each carry a licence, attribution or credential problem.
- 2026-09-26: Treated as a public-feed adapter, not a scraped source (Rule 13 not triggered), but reuses `PacedFetcher` pacing and an identified User-Agent regardless, and does not skip the licence registry entry (`test_source_licences.py` enforces one per adapter).
- 2026-09-26: Small seed list only. The $5/month LLM cap and the classification backlog gate company-list growth, exactly as for the US + EU panel.
- 2026-09-26: **Three things the original plan missed, found while building — each would have been a silent gap.** (1) `requirements._extract_description()` has a per-source branch; without a `personio` branch every Personio posting would have had an empty description and no requirements extraction. Added. (2) `test_trusted_stats` requires every industry tag to have an explicit ONS-crosswalk decision; "Construction Tech" and "Defence Tech" were added as `None` (each spans software and non-software activity), crosswalk version bumped to `2026-09-26.1`. (3) `test_employer_headcount` requires every tracked company to have a headcount or a stated reason; the three are in `UNKNOWN_HEADCOUNT` ("not yet researched") rather than guessed.
- 2026-09-26: Language: fetched without a `?language=` parameter (the account's default feed) so a job published in two languages is not returned twice. Kept `country=None` (the feed has only city strings); the employer's HQ country is in `COMPANY_REGION`.
- 2026-09-26: Seed list is `personio`, `stark`, `capmo` (140 postings in total). `choco` (stale 2017 roles), `bounti` (employer not verifiable) and `moss` (0 roles) were deliberately not added.
- 2026-09-26: **Noticed, not changed (out of scope):** `_extract_description()` has no `workable` branch either, so Workable postings likely get no requirements extraction. Worth a separate look.
- 2026-09-26: Adapter sets a static, non-personal User-Agent (`tmip-job-ingest/1.0 ...`); the other ATS adapters use the httpx default. Deliberately no contact email in it.
- 2026-09-26: **German classification sample (2 requests to `classify_batch`, title-only, no DB writes).** (a) Real titles, 20 (8 Capmo + 12 Stark): every engineering role landed as `Engineer`/`senior`/`ic`; Customer Success, Account Executive, BDR, Assembly Technician, truck driver, buyer etc. correctly `other`. Only 2 of Capmo's 8 titles were tech roles, so this alone was inconclusive for German titles. (b) 13 constructed standard German titles (not from a real board): 13/13 sensible, all `high` confidence — Softwareentwickler → Engineer, Leiter Softwareentwicklung → lead/management, Produktmanager/Product Owner → Product Manager, Produktdesigner/UX-Designer → Designer, Werkstudent → entry, Vertrieb/Buchhalter → other. **Conclusion: German titles classify correctly; no taxonomy or prompt change needed.** One data-quality note: Capmo lists "Nichts passendes dabei? Initiativbewerbung!" ("nothing fitting? open application") as a position — a placeholder, not a job; it classifies `other`, so it is harmless to role stories but does add one non-job row to raw postings. Not filtered (the adapter keeps the feed verbatim); revisit if it becomes a pattern.
- 2026-09-27: **Real production run, confirmed end to end** (ingestion_run id 77, triggered manually after the daily cron had already fired earlier without this code — see `changes/2026-09-27-llm-budget-raised-to-10.md`'s context). `personio/personio`: 1 fetched, 1 inserted. `personio/stark`: 132 fetched, 132 inserted. `personio/capmo`: 8 fetched, 8 inserted. All 141 classified cleanly (2 LLM requests total for the whole run, `other_rate` 0.6%). Confirms the adapter works against live production, not just the local venv.
- 2026-09-27: **Found in the same run, unrelated to Personio**: a transient Postgres connection timeout hit mid-loop on `ashby`, right after `thought-machine`'s fetch succeeded — it wasn't caught by the per-company `SourceFetchError` isolation (that only wraps the *fetch*, not the DB write in `insert_new_postings`), so it aborted the rest of that adapter's company loop for this run. `thought-machine`'s possible new postings and a same-day refresh of `zego` (the last company in Ashby's list, already has 47 rows from an earlier run) were skipped this run only — both self-heal on the next run since inserts are id-deduped and idempotent. Overall run status recorded as `partial` for this reason alone; every other adapter, including all of Personio, completed with zero errors. Worth a small follow-up (wrap the DB write in the same per-company isolation Greenhouse/Lever/Ashby/Workable/Personio fetches already have) — not fixed here, flagged for its own change request.
- 2026-09-27: Railway's `redeploy` MCP action rebuilds `job-sync`'s image but does **not** execute its cron start command out of schedule (confirmed: empty deploy logs, no new rows). Ran `ingest.py` directly from a local shell against the same production `DATABASE_URL` and Gemini keys instead — functionally identical to what the Railway cron does, just triggered from here since no "run cron now" action is exposed via the available Railway tools.
