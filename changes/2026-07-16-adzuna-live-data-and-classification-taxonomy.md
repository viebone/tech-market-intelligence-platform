---
id: adzuna-live-data-and-classification-taxonomy
date: 2026-07-16
trigger-type: internal
change-type: api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Live Adzuna data + job classification taxonomy for Market Health

## Signal
See: `research/2026-07-16-adzuna-live-data-and-classification-taxonomy.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md`

This directly serves the outcome's success criteria — "identify which roles and skills are in
demand vs. declining" and "see the trends clearly, how the hiring market numbers evolve through
time" — which today are satisfied only by static mock data. No change to the outcome's scope or
success criteria; this is how the outcome gets served with real data instead of mocks.

## Change Type
`api-change` — new data models, new external dependency (Adzuna Jobs API), new backend business
logic (ingestion + LLM classification pipeline). Also touches the experience spec, because the
classification taxonomy is user-facing vocabulary (chart categories, potential filter values),
not a pure implementation detail — per the api-change cascade rule, the experience spec is
reviewed first.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | update — reconcile fixed chart categories ("Designer, Product Manager, Engineer") against the new `type` taxonomy; resolve the open question "Should role categories be fixed or user-configurable in v1?"; reference the new taxonomy doc |
| Design Reference (new) | `design/market-health/job-classification.md` | create — canonical taxonomy: `type` (role_family enum), `seniority` (ordered ladder), `track` (ic/management), raw-title trend dimension, taxonomy versioning rule |
| Backend Spec | `backend/specs/market-health/api.md` | update — replace mocked data plan with: Adzuna ingestion (query shape, dedupe-by-id, `max_days_old` safety margin), `raw_postings` + `classifications` data models, LLM classification business logic (structured output, batching, `other` escape hatch) referencing `job-classification.md`, new external dependency (Adzuna Jobs API) |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — align any filter/legend component data contract to the new taxonomy enum and the updated backend API contract |
| Backend Implementation | `backend/src/` | update — after backend spec is finalized |
| Frontend Implementation | `frontend/src/` | update — only if the frontend spec's contract changes require it |

## Execution Plan

- [x] Step 1: `/new-experience` — update `design/market-health/experience.md` (reconcile category naming, resolve open question) and create `design/market-health/job-classification.md` (the taxonomy)
- [x] Step 2: `/new-backend-spec` — update `backend/specs/market-health/api.md` (Adzuna ingestion, data models, classification business logic)
- [x] Step 3: `/new-frontend-spec` — update `frontend/specs/market-health/architecture.md` to match the updated backend contract and taxonomy
- [x] Step 4: `/implement-backend`
- [x] Step 5: `/implement-frontend` — not needed. The real `/api/market-health/openings`
  response shape was preserved exactly (see decision log), so no frontend code changes
  are required.

## Decision Log
- 2026-07-16: Mapped to existing outcome `understand-market-health-before-searching` — no new
  outcome needed, this is how the existing outcome gets served with real data. Classified as
  `api-change` rather than `new-feature` since market-health already exists; the experience spec
  is in the cascade because the taxonomy is user-visible vocabulary, not backend-only.
- 2026-07-16: Taxonomy placed in `design/market-health/` (Designer-owned) rather than in the
  backend spec, so backend and frontend specs both reference one canonical source instead of
  each defining their own version and drifting apart over time.
- 2026-07-16: Historical backfill (pre-existing market data, before this ingestion pipeline
  starts) is explicitly out of scope for this change — Adzuna's `/search` endpoint cannot answer
  "what was live in the past," confirmed empirically. Backfill remains a separate, later problem
  (candidate sources already scouted: BLS series, H-1B LCA disclosure data, layoffs.fyi archive)
  and should get its own change request once this live-ingestion pipeline is working.
- 2026-07-19: Backend spec (`backend/specs/market-health/api.md`) updated. `GET
  /api/market-health/trends` rewritten to return monthly counts per Role Category, sourced from
  new `raw_postings` + `classifications` tables (PostgreSQL — the product's first real database
  usage), replacing the old unused `DemandSignal`/`CompensationSignal`/`LayoffSignal` mock
  models. `/api/market-health/summary` and `/api/alerts/exceptions` left untouched — not
  referenced by the current experience or frontend specs, out of scope for this change.
  Classification calls reuse `LLMProvider.complete()` with manual JSON parsing/validation
  against the taxonomy's closed sets, since the provider abstraction has no native
  schema-constrained output method today — noted as a caller-side responsibility rather than
  inventing a new protocol method mid-spec.
- 2026-07-19: Frontend spec (`frontend/specs/market-health/architecture.md`) updated —
  `TrendChart` maps `roleCategory` to its fixed accent colour by exact string match (never
  array index), and the `/trends` API contract row now matches the finalized backend response
  shape (`series: [{ roleCategory, points }]`). No component additions were needed — the
  existing chart already consumed a per-category line shape; only the field names and response
  envelope changed.
- 2026-07-19: **Discovered mid-implementation**: the shipped frontend (`MarketHealthPage.tsx`)
  never actually called the `/api/market-health/trends` endpoint both specs described — it was
  built independently, in a later session, against `GET /api/market-health/openings` with a
  wide per-month row shape (`{ month, designer, product_manager, engineer }`), and neither spec
  was updated to match at the time. The real frontend is also structurally richer than the
  frontend spec describes (`TaskPanel`, `OutputPanel`, `ReasoningTrace` from the
  ai-reasoning-transparency and provenance-panel change requests). Building against the
  originally-drafted `/trends` spec would have created a second, dead endpoint nobody calls.
  Corrected course: kept the real `/openings` endpoint and its existing response shape (zero
  frontend code changes required), wired real Adzuna/classification data underneath it, and
  corrected both specs' endpoint name/shape/component-name references to document that reality.
  Did not attempt a full reconciliation of the frontend spec against everything the later
  reasoning-panel work added — that's out of scope for this change and is flagged in the
  frontend spec as a candidate for its own future change request.
- 2026-07-19: Implemented backend — first real database usage in this product. Added
  `backend/src/db.py` (psycopg3 connection pool, schema init), `adzuna_client.py` (Adzuna
  search with pagination), `raw_postings.py` (dedupe-by-id insert), `classification.py`
  (batched LLM classification via `providers.gemini("gemini-2.5-flash").complete()`, chunked
  to 10 postings per call to stay under the adapter's 512-token output cap, parsed/validated
  against the closed taxonomy sets), and `ingest.py` (manual/cron entry point: `python
  ingest.py`). Rewrote `market_openings.py` to aggregate real data instead of the synthetic
  2019–2026 mock series in `mock_data.py`, which was deleted along with the now-unused
  `OPENING_TRENDS`/`OPENING_SUMMARIES`. Added `DATABASE_URL` to `backend/.env.example` and
  `psycopg[binary,pool]` + `httpx` to `requirements.txt`. User confirmed they'll provide a
  `DATABASE_URL` themselves rather than needing Docker Compose scaffolding.
- 2026-07-19: Real-world verification uncovered several bugs and one hard constraint, fixed in
  sequence:
  - `psycopg_pool.ConnectionPool` hung indefinitely in local Windows dev even though a direct
    `psycopg.connect()` succeeded instantly. Dropped pooling entirely (`db.py` now opens a
    plain per-call connection with `connect_timeout=10`) — this feature's query volume doesn't
    need a pool, and it sidesteps the issue. User switched from a local Postgres to a
    Railway-hosted instance to avoid WSL↔Windows networking friction generally.
  - `localhost` in `DATABASE_URL` hung on DNS/IPv6 resolution with no timeout; fixed by the
    `connect_timeout` above and documented preferring `127.0.0.1`/an external host.
  - **Real bug**: `gemini-2.5-flash`'s default "thinking" mode silently consumed the entire
    output token budget on invisible reasoning before producing visible text, truncating every
    classification response — this is why an early real run classified everything as `"other"`
    (a parse failure on truncated JSON, not genuine model judgment). Fixed in the shared
    `backend/src/llm/gemini.py` adapter: `complete()` now sets `thinking_budget=0` (only
    `classification.py` calls `complete()`; `chat.py` uses `stream()`, left untouched and still
    benefits from thinking). Output budget raised 512 → 4096 tokens now that it isn't being
    silently eaten.
  - **Hard constraint, not a bug**: the Gemini API key is on the free tier, capped at 20
    requests/day for `gemini-2.5-flash` — shared with live `/api/chat` traffic. User chose to
    stay on the free tier rather than upgrade billing, so minimizing LLM call volume became a
    real product constraint, not just a cost nicety.
  - Added retry-with-backoff for 429 responses and inter-batch pacing in `classification.py`
    (`SECONDS_BETWEEN_BATCHES`, `MAX_RETRIES`) to survive the per-minute limit; the daily limit
    can only be addressed by fewer total requests or a billing upgrade.
  - **Title-based classification cache** added (`_get_title_cache` in `classification.py`):
    classification depends only on posting title (see `_build_prompt`), so identical titles
    always classify identically. Before any LLM call, postings are deduped by exact title
    against both prior runs (DB lookup) and the current batch (in-memory) — a title is
    classified at most once, ever, then fanned out to every posting sharing it. This is now the
    primary lever for staying under the daily request quota as the dataset grows, and doubles
    as a determinism improvement (no run-to-run variance for the same title).
  - Adzuna's own `category` field confirmed generic via its `/categories` endpoint (~30 broad
    industry buckets, nothing finer under `it-jobs`) — precision has to come from `what_phrase`,
    not `category`. Bare category-word search terms (`"designer"`, `"engineer"`) were replaced
    with `ingest.py`'s `ROLE_SEARCH_TERMS`: a curated list of specific, industry-standard job
    titles per Role Category (e.g. "UX designer", "product owner", "backend engineer"), per
    user direction — reduces noise (fewer irrelevant postings burning a classification call to
    reject as `"other"`) and is explicitly meant to be reviewed periodically (titles added once
    they recur often enough in `raw_postings`, retired once stale), mirroring the review process
    `job-classification.md` already describes for Raw Title. "Product Owner" added to that
    spec's Product Manager sub-specialization examples since it's now an explicitly tracked
    title. Ingestion now iterates every search term across all three categories, then runs
    classification once across everything newly ingested together (not once per term), so the
    title cache sees the widest possible pool for catching cross-term duplicates before any LLM
    call.
  - Backend spec (`api.md`) updated throughout to match: `role_family_query` field description,
    Business Logic (Ingestion, Classification, Title-based classification cache), and Tech
    Decisions (free-tier constraint called out explicitly, pointing to a billing upgrade — not
    more caching — as the fix if usage outgrows it).
- 2026-07-20: Re-verification (new day, quota expected to reset) surfaced two more real issues:
  - The `google-genai` client had no request timeout, so a stalled network call could hang
    indefinitely — observed in practice (process alive, near-zero CPU, zero progress, for many
    minutes past what the retry/backoff logic should allow, no crash). Fixed by passing
    `http_options=types.HttpOptions(timeout=60_000)` to the `genai.Client` constructor in
    `llm/gemini.py`, applying to both `stream()` and `complete()`.
  - **Regression, now fixed**: the title-cache refactor had moved `insert_classifications()` to
    run once at the very end of `classify_postings()`, after the full batch loop — meaning a
    later batch failing (routine on the free tier) discarded every earlier batch's successful,
    quota-costing classifications instead of persisting them. Confirmed happening in practice: a
    run that completed 3 successful batches before hitting a 429 wall left `classifications` at
    0 rows. Fixed by inserting per-title-group as each batch (and the cached-title group)
    completes, so partial progress always survives a later failure and doesn't need
    re-classifying (or re-paying for) on the next run.
  - Quota behavior in practice is less generous than the "20 requests/day" label suggests — this
    run got only 3 successful requests before hitting a sustained block despite the API's own
    "retry in ~11s" hints never actually clearing after 4+ minutes of real waiting across 5
    retries. Free-tier completion of the full backfill will take multiple partial runs over
    several days, not one or two attempts; each run now safely banks its progress rather than
    risking losing it to the bug above.
  - Raised `BATCH_SIZE` 50 → 100 titles/request and the adapter's output budget 4096 → 8192
    tokens (`llm/gemini.py`), since the binding limit is on request *count*
    (`generate_content_free_tier_requests`), not tokens — fewer, larger batches buy more real
    progress per usable window than many small ones.
  - Fresh empirical tally across this whole day's testing: only ~1-2 successful classification
    requests actually went through despite the "20/day" label, before a sustained multi-minute
    block that repeated retries couldn't clear. Real-world throughput on this free-tier key is
    far below the documented figure. User re-confirmed keeping the free tier regardless — plan
    going forward is to re-run classification periodically (manually or scheduled) and let the
    remaining ~889 unique titles accumulate over roughly 1-2+ weeks, not days. 100/1454 postings
    classified so far, distribution healthy (~10% `"other"`, well down from ~22% with the old
    generic search terms).
- 2026-07-21: Quota opened back up substantially — a further re-run completed classification of
  all 1454/1454 postings in one pass (the 100-title batching change likely helped: fewer total
  requests needed meant more real progress fit inside whatever window was available). Final
  distribution: Engineer 1008, Product Manager 162, Designer 49, `other` 235 (~16%). Full
  end-to-end verification performed: started the backend (WSL/uvicorn) and frontend (Windows
  native — the existing `node_modules` had Windows-only native rollup binaries, so the frontend
  runs on Windows even though the backend runs in WSL, confirmed via `vite.config.ts`'s proxy to
  `localhost:8000`), then drove the app with a one-off Playwright script (`chromium-cli` wasn't
  available in this environment) and confirmed: `/api/market-health/openings` returns real
  aggregated data, the Market Health page renders correctly (chart legend colours match
  `visual-design.md`, written summary reflects real numbers), and zero browser console errors.
  One expected, non-bug observation: the chart itself shows no visible line yet, since all data
  currently falls in a single calendar month ("2026-07") — a line needs ≥2 points to draw a
  stroke — and will resolve naturally once ingestion spans into August. This is the
  "no backfill" limitation already documented and accepted as out of scope for this change.
  Also fixed in passing: `genai.Client` had no request timeout, letting a stalled network call
  hang indefinitely (`http_options=types.HttpOptions(timeout=60_000)` added in `llm/gemini.py`).
