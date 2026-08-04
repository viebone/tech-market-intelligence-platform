---
id: multi-source-job-data-ingestion
date: 2026-07-28
trigger-type: stakeholder-request
change-type: technical-refactor, api-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Source-agnostic job data model and multi-source ingestion architecture

## Signal
See: `research/2026-07-28-multi-source-job-data-ingestion.md`

## Outcome
See: `outcomes/job-data-source-flexibility.md` (new — created during this triage; see Decision Log)

## Change Type
`technical-refactor` — the current `RawPosting`/`Classification` model and `ingest.py` pipeline
are Adzuna-shaped by construction (`RawPosting.id` is documented as "Adzuna's own job id";
`raw_response` is "the full Adzuna API response object"). This restructures the model and
ingestion pipeline to be source-agnostic, mirroring the `llm/` provider-adapter pattern already
established for AI providers.
`api-change` — `RawPosting`'s schema changes (adds `source`, redefines the dedupe key), new
data model for non-posting enrichment content, and `query_market_data`'s output may gain a
source dimension.

**Update — 2026-08-03**: Adzuna is now fully unusable (no license), not merely costly at scale.
This change no longer migrates Adzuna as adapter #1 — it drops Adzuna entirely and builds three
concrete replacement adapters: **Greenhouse, Lever, and Ashby**, each an ATS platform whose
public job-board API covers many companies behind one shared shape. See the research file's
2026-08-03 update for the tradeoff (strong tech/startup coverage, not universal — large
enterprises on custom or legacy ATS aren't reachable this way). This change still builds the
`SourceAdapter` abstraction first — Greenhouse, Lever, and Ashby are simply its first three
adapters instead of a migrated Adzuna client. Onboarding any *further* source beyond these three
remains its own follow-on `new-feature` change request, per the outcome's scope boundary.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | created this session |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | update — the sourcing rule ("state the data's time window, never fabricate an external claim") and `source` language currently assume one provider; needs to describe multiple sources and how attribution reads when data is blended |
| Component Spec | `design/market-health/provenance-panel.md` | update — `signal.source` is currently a single string, and the "API calls" section hardcodes two endpoint names as literal display text; both assumptions break once postings carry a per-record source and enrichment content exists |
| Backend Spec | `backend/specs/market-health/api.md` | update — this is the core of the change: generalize `RawPosting`, define the source-adapter abstraction, document per-source fault isolation, add the enrichment-content model |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — API contract additions (`source` field, any new enrichment surface) flow through |
| Backend Implementation | `backend/src/ingest.py`, `backend/src/adzuna_client.py`, `backend/src/models.py`, `backend/src/raw_postings.py`, new `backend/src/sources/` | update |
| Frontend Implementation | `frontend/src/` (provenance panel, any source badges) | update |

## Execution Plan

- [x] Step 0: Verified Greenhouse, Lever, and Ashby's actual public job-board API shapes
      (endpoints, auth, rate limits/ToS, response fields) via WebSearch/WebFetch against each
      platform's own current docs. Findings: all three are public, unauthenticated GET endpoints
      (`boards-api.greenhouse.io/v1/boards/{board_token}/jobs`,
      `api.lever.co/v0/postings/{site}`, `api.ashbyhq.com/posting-api/job-board/{jobBoardName}`);
      none documents a hard rate limit on the GET job-listing endpoint (Lever documents one only
      for its POST application endpoint, which this product never calls).
- [x] Step 1: `/new-experience` — updated `design/market-health/experience.md`: Sources
      accordion bullet now describes naming multiple platforms in one string; new Edge Case
      makes the curated-company-list coverage limit explicit (not a full-market census);
      "Resolved 2026-08-03" note added.
- [x] Step 2: `/new-backend-spec` — updated `backend/specs/market-health/api.md`:
      - Generalize `RawPosting`: add `source` (adapter identifier) and `source_ref` (the
        source's own id), replace the current Adzuna-id-as-global-PK dedupe key with a
        composite `(source, source_ref)` key; keep `raw_response` as opaque per-source JSON
        (unchanged principle — store verbatim, never project down)
      - Define a `SourceAdapter` interface (`backend/src/sources/base.py`, mirroring
        `backend/src/llm/base.py`'s `LLMProvider` pattern): each adapter fetches and maps its
        source's native shape into `RawPosting` fields; adding a source means writing one
        adapter, never touching ingestion orchestration or classification
      - Remove `adzuna_client.py` and its ingestion wiring — Adzuna is dropped, not migrated
        (2026-08-03 update). Its fault-isolation, retry/backoff, and rate-limit pacing patterns
        are reused as a template for the three new adapters, not preserved as running code.
      - Build three concrete adapters: `sources/greenhouse.py`, `sources/lever.py`,
        `sources/ashby.py` — each driven by a curated list of company board tokens/slugs (same
        shape as today's `ROLE_SEARCH_TERMS`: reviewed periodically, not exhaustive). Exact
        endpoint/auth/rate-limit details confirmed against each platform's own docs before
        being written into the spec (Step 0 above), not assumed — matching how Adzuna's real
        quota was confirmed via their ToS in the 2026-07-27 change.
      - Ingestion orchestration (`ingest.py`) loops over configured adapters the same way it
        loops over search terms today: one adapter's failure is isolated and recorded, the run
        continues with the rest, `IngestionRun.terms_processed`-equivalent gains a `source`
        dimension
      - Define how non-posting enrichment (articles, reports) is modeled — a separate table/
        shape from `RawPosting`, since it isn't a job posting and shouldn't be forced through
        classification; document how (if at all) it feeds `/api/chat`'s data-sourcing decision
        order alongside `query_market_data` and Google Search grounding. Deferred to a follow-on
        change unless a concrete enrichment source is picked in this session.
      - Update `query_market_data`'s response shape and the trend-aggregation business logic
        if source-level filtering/attribution is needed downstream
- [x] Step 3: `/new-frontend-spec` — reviewed `frontend/specs/market-health/architecture.md`;
      confirmed and documented no frontend changes needed (response shapes unchanged, only the
      `source` string's content changes) — added a "Reviewed 2026-08-03" note, same pattern as
      the existing 2026-07-22 review entry.
- [x] Step 4: Updated `design/market-health/provenance-panel.md` — Sources section now documents
      that `signal.source` may name multiple platforms in one string (no shape change); also
      corrected the "API calls" section's stale `/api/market-health/trends` reference to the
      real `/api/market-health/openings` endpoint, found while this file was already open.
- [x] Step 5: `/implement-backend` —
      - `backend/src/sources/base.py`: `FetchedPosting`, `SourceAdapter` Protocol,
        `SourceFetchError`, and a shared `PacedFetcher` (per-adapter pacing clock + retry with
        backoff on 429/5xx/connection errors, mirroring `adzuna_client.py`'s pattern before its
        removal).
      - `backend/src/sources/greenhouse.py`, `lever.py`, `ashby.py`: one adapter class each,
        curated company lists validated live (2026-08-03) by confirming each token/slug/name
        resolves to a real board — 15 Greenhouse companies, 5 Lever (Lever's usage has shrunk
        considerably; this is genuinely the size of what resolved), 15 Ashby. Live end-to-end
        smoke test (fetch real data, not just compile) confirmed correct parsing for all three
        (stripe: 545 postings, palantir: 302, linear: 23).
      - `backend/src/sources/__init__.py`: `ALL_SOURCE_ADAPTERS` registry, mirroring
        `llm/providers.py`'s factory-module pattern.
      - Removed `backend/src/adzuna_client.py` (`git rm`).
      - `backend/src/ingest.py`: orchestration rewritten to loop over `ALL_SOURCE_ADAPTERS` ×
        each adapter's `companies`, with both per-company and per-adapter fault isolation.
      - `backend/src/raw_postings.py`: `insert_new_postings` takes `source` + `FetchedPosting`
        list, builds `id = f"{source}:{source_ref}"`.
      - `backend/src/db.py`: schema migration via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`
        (not just `CREATE TABLE IF NOT EXISTS`, since `raw_postings` already has live prod
        rows) — adds `source`/`source_ref`/`company`, drops `role_family_query`'s `NOT NULL`,
        backfills existing rows to `source='adzuna'`.
      - `backend/src/ingestion_runs.py`: `detect_anomalies` generalised from `term` to
        `(source, company)`; handles legacy pre-2026-08-03 run shape gracefully (no crash, no
        false-positive match).
      - Fixed two hardcoded Adzuna references in actual endpoint code that the spec update
        alone didn't touch: `market_openings.py`'s `/openings` response `source` string, and
        `chat.py`'s reasoning-trace `SourceAccess.name` label — found via a full `grep -i
        adzuna` sweep after the primary implementation, not anticipated in the plan.
      - `backend/.env.example`: removed `ADZUNA_APP_ID`/`ADZUNA_APP_KEY`.
      - `DEPLOYMENT.md`: updated env-var table, ingestion step description, and data-model
        sketch; flagged that `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` still need manual removal from
        the Railway dashboard (not in `railway.json`, so not fixable by a file edit).
      - Verified: `py_compile` clean on every new/changed file; `main.py` and `ingest.py`
        both import successfully at runtime (not just syntax-checked) via the project's WSL
        venv; a full `grep -i adzuna` across `backend/src` after all fixes shows only
        intentional historical/migration references.
      - **Not run**: the actual `python ingest.py` pipeline against the real database — that
        would write real rows and spend real Gemini classification quota, a consequential
        action left for the user to trigger deliberately rather than run unprompted.
- [x] Step 6: `/implement-frontend` — not needed; the reviewed-2026-08-03 note added to
      `frontend/specs/market-health/architecture.md` in Step 3 already established no frontend
      code changes are required (response shapes unchanged). Confirmed no frontend source files
      reference Adzuna.

## Decision Log
- 2026-07-28: Created `outcomes/job-data-source-flexibility.md` as a new business outcome
  rather than folding this into `outcomes/understand-market-health-before-searching.md` —
  confirmed with the user. The two are distinct: the existing outcome is about what a user sees
  and trusts when reading market trends; this one is about the platform not being load-bearing
  on a single paid vendor for the data behind those trends. Same split the codebase already
  makes between `ai-provider-flexibility` (business/infra) and `ai-reasoning-transparency`
  (user-facing), for the same underlying pattern applied to AI providers instead of job data.
  Priority set to `high` per user confirmation — Adzuna's paid tier is a near-term constraint,
  not a someday concern.
- 2026-07-28: Classified `technical-refactor` + `api-change`, not `new-feature` — this change
  is the abstraction and the migration of the one adapter that already exists (Adzuna), not new
  user-facing capability. Onboarding any specific new source (a named company portal, a named
  free aggregator) is explicitly out of this change's scope and will be its own `new-feature`
  change request against this same outcome once the adapter boundary exists to write into.
- 2026-07-28: Included the experience spec and provenance-panel component spec in the cascade,
  not just backend/frontend specs — `provenance-panel.md` currently hardcodes `source` as one
  string and the "API calls" section as two literal endpoint names, both of which are
  incompatible with genuinely multi-source data. Skipping this would let the backend model go
  multi-source while the UI still claims (or silently drops) single-source provenance, directly
  undermining `ai-reasoning-transparency`.
- 2026-07-28: Did not classify this as `bug-fix` despite following directly from the
  2026-07-27 Adzuna resilience work — that change fixed Adzuna's own failure handling and
  remains correct and reusable as the first adapter's internals; nothing about it is wrong,
  this change extends what it plugs into.
- 2026-07-28: Deferred cross-source deduplication (the same job appearing via two sources) and
  automatic source routing/selection to the outcome's "Out of scope" — both are real problems
  but only become concrete once a second source actually exists; solving them speculatively now
  risks designing against guesses instead of a real second adapter's actual shape.
- 2026-08-03: Adzuna confirmed fully unusable (no license) rather than merely costly — changes
  this change's shape from "build the abstraction, migrate Adzuna as adapter #1" to "build the
  abstraction, drop Adzuna, ship Greenhouse/Lever/Ashby as the first three adapters." Chose all
  three ATS platforms together (not one, sequentially) since the user's stated goal is genuinely
  multi-source flexibility, and three real adapters is a stronger proof that the abstraction
  holds than one — while still bounded (three named platforms, not "as many as possible").
  Real cross-source deduplication now becomes relevant sooner than originally assumed (three ATS
  sources launching together, not one added later) — still deferred per the outcome's scope, but
  flagged here since the "later" it was deferred to just moved closer.
