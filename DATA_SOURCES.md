# Data Sources & Control Levers

**What this is:** the single index of every place the platform pulls data from — and every
knob that controls how it behaves. It is a *map*, not a config file: nothing here is loaded
at runtime. To change something, edit the file this points to.

**Why it exists:** the platform is built to draw from many sources of many kinds
(`outcomes/job-data-source-flexibility.md`) — job boards today, company career pages, layoff
feeds, research and articles later — all normalised into one internal model. This document
keeps that growing surface reviewable in one place.

Last reviewed: 2026-09-11.

---

## 1. The source model

Every source, whatever its kind, goes through **one adapter** and maps into **one internal
model**. No business logic (ingestion orchestration, classification, trend aggregation, the
API endpoints) knows or cares which source produced a given row — it only reads `source` for
provenance. This mirrors the `llm/` provider abstraction, applied to data.

```
source (API, scrape, feed, upload)
    │
    ▼
adapter  ──────────────  sources/{name}.py — implements SourceAdapter
    │                     (fetch → normalise → FetchedPosting)
    ▼
raw_postings          ──  one row per posting, id = "{source}:{source_ref}"
    │                     raw_response kept verbatim; source always recorded
    ▼
classification        ──  role_category / specialization / level / track
    │                     ("other" is the escape hatch for non-tracked roles)
    ▼
requirements + skills ──  extracted per posting (batch + interactive lanes)
    ▼
market-health API + chat + data stories
```

**Adding a source** = write one adapter class implementing `SourceAdapter`
(`backend/src/sources/base.py`), register it in `ALL_SOURCE_ADAPTERS`
(`backend/src/sources/__init__.py`). Nothing downstream changes. See
`backend/specs/market-health/api.md` — Tech Decisions — Source adapter abstraction.

---

## 2. Source types

| Type | Status | What it produces | Where it lands | Notes |
|---|---|---|---|---|
| **Job postings** | ✅ active | One `raw_postings` row per open role | `raw_postings` → classification → requirements | The only type live today. Three adapters (§3). |
| **Company career pages / ATS portals** | 🔲 planned | Same as job postings — a new *adapter*, not a new type | `raw_postings` | For companies not on a supported ATS (custom career sites, legacy ATS). Mechanism is scraping, not a public API — needs a per-site adapter or a generic HTML/JSON-LD adapter. Same `FetchedPosting` output. |
| **Employment events** (renamed from "Layoff events" 2026-09-11 — scope broadened to match) | 🟡 code shipped, 2/3 adapters not yet functional | An `employment_events` row (company, event date, event type, direction, jobs affected, source) — layoffs **and** closures, restructuring, bankruptcy, offshoring, expansion, hiring announcements | Table `employment_events` — *not* `raw_postings`, *not* classified | Feeds the broadened `Layoff Signal` (IA) and the trend chart's "Employment events strip". Data model, endpoint, chat tool, and three adapters implemented — see §3a below. `/change-request`: `changes/2026-09-11-employment-event-ingestion.md`. |
| **Research / reports / articles** | 🔲 planned | Enrichment text with market commentary | New table — explicitly *not* forced through the posting/classification shape (`job-data-source-flexibility.md` — Success looks like) | Feeds narrative + context, cited as an external source in provenance. Needs its own contract + CR. |

**Out of scope for now** (per the outcome): cross-source dedupe of the same posting; automatic
source routing by cost/quality; paid data licensing.

---

## 3. Job-posting adapters (active)

All three are **public, unauthenticated GET** endpoints — no credentials, no API keys. Each
adapter fetches a company's *entire* published board (none of the three supports server-side
filtering to "tech roles only" consistently), and classification's `other` bucket does the
relevance filtering downstream.

| Adapter | `name` | Endpoint (per company) | Fetches | File |
|---|---|---|---|---|
| Greenhouse | `greenhouse` | `boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true` | Every published job, one call, no pagination | `backend/src/sources/greenhouse.py` |
| Lever | `lever` | `api.lever.co/v0/postings/{site}?mode=json` | Every published job, paginated (`skip`/`limit=100`) | `backend/src/sources/lever.py` |
| Ashby | `ashby` | `api.ashbyhq.com/posting-api/job-board/{jobBoardName}?includeCompensation=true` | Every published job; `includeCompensation` on so pay lands in `raw_response` | `backend/src/sources/ashby.py` |

Shared machinery (`backend/src/sources/base.py`):
- `SourceAdapter` protocol — `name`, `companies`, `fetch_company(company) -> list[FetchedPosting]`
- `FetchedPosting` — the normalised output (source_ref, company, title, raw_response, + optional country/city/salary)
- `PacedFetcher` — self-imposed ~1 req/s pacing + retry-with-backoff on 429/5xx (no source documents a hard rate limit)
- `normalize_country()` / `COUNTRY_NAME_TO_ISO2` — free-text country → ISO-2 (curated from observed data)
- `SourceFetchError` — one company failing never aborts the run or the rest of the list (fault isolation, per company)

---

## 3a. Employment-event adapters (spec'd 2026-09-11; code shipped 2026-09-11 — Step 7)

**How the data is stored, field by field, verified against the real production schema:
`backend/EMPLOYMENT_EVENTS.md`** — read that first if the question is "what does a stored
employment-event row actually look like." Source evaluation:
`research/2026-09-11-employment-event-data-sources.md`. Full data model and adapter contracts:
`backend/specs/market-health/api.md` — Data Models (`EmploymentEvent`), Business Logic —
Employment event ingestion, Tech Decisions — `EmploymentEventAdapter`. Priority order below is
implementation order, not a ranking of importance.

| Adapter | `name` | Access | Auth | Status |
|---|---|---|---|---|
| Eurofound European Restructuring Monitor | `eurofound_erm` | CSV data-access request (exact mechanism TBC) | None confirmed | ⚠️ **Scaffolded, not functional.** `fetch()` logs a notice and returns `[]` — `ACCESS_CONFIRMED = False`. See `backend/src/employment_events/eurofound_erm.py`'s module-docstring TODO for the exact next step. |
| US state WARN notices | `us_warn` | **WARN Firehose** (warnfirehose.com) — one aggregated API, all 50 states, replaces the original per-state scraping design (found via live research 2026-09-11, same day) | API key, free tier (25 calls/day) — env var `WARN_FIREHOSE_API_KEY` (set, local `backend/.env` only, gitignored) | ✅ **Live — first real data ingested 2026-09-11.** Field mapping verified against a real authenticated response (`company_name`, `industry`→`sector`, real `source_url` per record — see `backend/src/employment_events/us_warn.py`). 25 real rows inserted on first run; re-run confirmed idempotent (0 new). **Real finding**: the feed lags ~9 days behind the actual date (an unfiltered call's `latest_notice` was 9 days stale) — the trailing window was widened from 4 to 30 days after the first run returned 0 (too narrow), same "confirm empirically" correction pattern as everywhere else in this pipeline. |
| UK Companies House — insolvency | `companies_house_insolvency` | **Streaming API** (`stream.companieshouse.gov.uk/insolvency-cases`) — real-time, all UK companies, no company targeting (revised 2026-09-11, replacing a tracked-company candidate-list design — `changes/2026-09-11-employment-events-no-company-matching.md`) | Streaming-type API key (free registration, Companies House Developer Hub) — env var `COMPANIES_HOUSE_API_KEY`, **set 2026-09-11** | ✅ **Live — first real data ingested 2026-09-11.** Field mapping corrected against a real authenticated response (`resource_id` for company number, `data.cases[0].dates[0].date` for the case date — three fields differed from the initial guess). **Known limitation**: the stream carries no company name, only a company number (`company_raw` = the bare id, e.g. `"12028607"` — never fabricated as `"Company N"`, revised 2026-09-11) — resolving names needs a separate REST-type key, not pursued yet. Such events are excluded from the Employment Risk story's company ranking (`is_real_company_name()`) but still count toward direction/country/sector totals — `changes/2026-09-11-employment-risk-hide-placeholder-names.md`. |
| SEC EDGAR (8-K Item 2.05) | `sec_edgar_8k` | Full-text search (`efts.sec.gov/LATEST/search-index`), filtered to structured Item 2.05 ("Costs Associated with Exit or Disposal Activities") — added 2026-09-11 | **None — no key at all, keyless and free.** Requires only a descriptive `User-Agent` (`SEC_EDGAR_CONTACT` env var; falls back to a placeholder that should be replaced with a real contact before relying on this in production) | ✅ **Live — first real data ingested 2026-09-11**, 9 real filings on first run (Veritone, TScan Therapeutics, TELA Bio, PDS Biotechnology, CVD Equipment, and others). The only source so far with a genuine company name straight from the record — see `backend/src/employment_events/sec_edgar.py`. `jobs_affected` and `sector` are `NULL` (not in this index's metadata; sizing/SIC-to-sector mapping not attempted rather than guessed). |
| ~~UK ONS HR1~~ | — | — | — | ❌ **Deliberately not integrated** — macro/aggregate only, no company names; doesn't fit `EmploymentEvent`. See the backend spec's "UK ONS HR1 (descoped)" note. |

**No company matching (added 2026-09-11, removed the same day —
`changes/2026-09-11-employment-events-no-company-matching.md`).** A `matched_company` field
and its alias map (`employment_events/company_aliases.py`) briefly linked events to the 35
tracked job-posting companies. Removed entirely, per explicit, repeated user direction:
employment events are an **independent dataset, matched or compared against tracked companies
nowhere in this pipeline** — not the data model, not any query, not any surface. Every
`employment_events` row carries only `company_raw`, exactly as its source reported it.

**Net effect today**: `python ingest_employment_events.py` is live and verified for **US
WARN** — 25 real rows in `employment_events` as of 2026-09-11, re-run confirmed idempotent.
Eurofound ERM (access unconfirmed) and Companies House (no key set yet) still insert nothing,
safely. All real employment-event data surfaces through the **"Employment risk across the
market"** data story (`design/market-health/data-stories.md` — Story 2) and follow-up Layoff
Signal conversation — both fully independent of the platform's 35 tracked companies, by
design, at every layer.

**Add a new employment-event source**: a 4-step recipe, documented in full in
`backend/src/employment_events/__init__.py`'s module docstring (write one adapter file
implementing `EmploymentEventAdapter`, register its display name, add it to
`ALL_EMPLOYMENT_EVENT_ADAPTERS`, update this doc) — `ingest_employment_events.py`, the DB
schema, the API endpoint, and the chat tool all already handle "however many adapters are
registered," none of them name a specific source. Same "one adapter, one internal model"
principle as §1's job-posting model.

---

## 4. Tracked companies

**35 companies**, hand-curated per adapter — a deliberately curated, periodically-reviewed
list, *not* an attempt at exhaustive coverage. Every board token is verified against a live
HTTP 200 before being added (`backend/specs/market-health/api.md` — Tech Decisions —
Company-list curation). A wrong token 404s loudly the same day, not a silent gap.

Two files must stay in sync (until §6 lands):
- `backend/src/sources/{greenhouse,lever,ashby}.py` — `COMPANIES` list (drives ingestion)
- `backend/src/industries.py` — `COMPANY_INDUSTRY` dict (static tag, one row per company; `NULL` if untagged, never guessed)

| Company | Source | Industry | Status |
|---|---|---|---|
| stripe | greenhouse | Fintech | ✅ |
| airbnb | greenhouse | Travel/Marketplace | ✅ |
| pinterest | greenhouse | Social Media | ✅ |
| asana | greenhouse | Productivity Software | ✅ |
| reddit | greenhouse | Social Media | ✅ |
| robinhood | greenhouse | Fintech | ✅ |
| coinbase | greenhouse | Fintech | ✅ |
| affirm | greenhouse | Fintech | ✅ |
| webflow | greenhouse | Web/Dev Tools | ✅ |
| figma | greenhouse | Design Tools | ✅ |
| airtable | greenhouse | Productivity Software | ✅ |
| cloudflare | greenhouse | Cloud/Infrastructure | ✅ |
| twilio | greenhouse | Developer Platform | ✅ |
| discord | greenhouse | Social/Communications | ✅ |
| gitlab | greenhouse | Developer Platform | ✅ |
| palantir | lever | Enterprise Software/Data | ✅ |
| plaid | lever | Fintech | ⚠️ board token 404s (seen every run since ~2026-09-06) — fix the token or retire |
| clari | lever | Enterprise Software | ✅ (returns 0 — board may be empty or moved) |
| restream | lever | Media/Streaming Tools | ✅ (returns 0) |
| lever | lever | HR Tech | ✅ (returns 0) |
| ramp | ashby | Fintech | ✅ |
| linear | ashby | Productivity Software | ✅ |
| openai | ashby | AI | ✅ |
| notion | ashby | Productivity Software | ✅ |
| modal | ashby | Developer Platform | ✅ |
| replit | ashby | Developer Platform | ✅ |
| mercury | ashby | Fintech | ✅ (returns 0) |
| deel | ashby | HR Tech | ✅ (returns 0) |
| loom | ashby | Productivity Software | ✅ (returns 0) |
| vercel | ashby | Developer Platform | ✅ (returns 0) |
| supabase | ashby | Developer Platform | ✅ |
| perplexity | ashby | AI | ✅ |
| elevenlabs | ashby | AI | ✅ |
| ashby | ashby | HR Tech | ✅ |
| watershed | ashby | Climate Tech | ✅ |

> "returns 0" = the board resolves (HTTP 200) but currently lists no roles matching what the
> adapter reads. Not an error; worth a periodic look to confirm the slug is still right.

---

## 5. How to change coverage

**Add a company** (on a supported ATS):
1. Find its board token / Lever site / Ashby job-board name (it's the slug in that ATS's
   public board URL).
2. Verify: `curl` the endpoint from §3 — expect HTTP 200 with a jobs array.
3. Add the slug to `COMPANIES` in the right `backend/src/sources/*.py`.
4. Add a `"{slug}": "Industry"` line to `COMPANY_INDUSTRY` in `backend/src/industries.py`.
5. Push — `job-sync`'s image rebuilds; the next daily run (06:00 UTC) picks it up.

**Retire a company:** remove it from both files. Existing `raw_postings` rows stay as
historical data.

**Add a new ATS or a career-page adapter:** new class in `backend/src/sources/`, register in
`ALL_SOURCE_ADAPTERS`. If it's a genuinely new *mechanism* (scraping), start with
`/change-request` — the ingestion spec's fault-isolation and pacing rules need a review.

**Add a new source *type*** (layoffs, articles): `/change-request` first — it needs a new
data model and its own adapter contract, not just a `COMPANIES` edit.

---

## 6. Planned: `config/companies.yaml`

Folding §4's two lists into one reviewable YAML file (companies + industries + status +
per-source), loaded at startup, with a `scripts/check_companies.py` that pings every board
and flags dead tokens. Makes coverage a one-file diff a non-engineer can review. Not built
yet — its own `technical-refactor` CR. Until then, §4 is the source of truth and this doc
must be updated by hand alongside the two code files.

---

## 7. Control-lever index

Everything tunable, and where it lives. Grouped by area.

### Ingestion & sources
| Lever | Value | File |
|---|---|---|
| Tracked companies | 35, per adapter | `backend/src/sources/{greenhouse,lever,ashby}.py` — `COMPANIES` |
| Company → industry | static dict | `backend/src/industries.py` — `COMPANY_INDUSTRY` |
| Registered source adapters | Greenhouse, Lever, Ashby | `backend/src/sources/__init__.py` — `ALL_SOURCE_ADAPTERS` |
| Fetch pacing / retry | 1 req/s, 3 retries, 2s backoff base | `backend/src/sources/base.py` — `PacedFetcher` defaults |
| Country name → ISO-2 | curated map | `backend/src/sources/base.py` — `COUNTRY_NAME_TO_ISO2` |
| Daily ingestion schedule | `0 6 * * *` (06:00 UTC) | `backend/railway.json` — `cronSchedule` |
| "Other rate" anomaly thresholds | 0.5 relative / 0.15 absolute | `backend/src/ingestion_runs.py` |

### Classification
| Lever | Value | File |
|---|---|---|
| Model | `gemini-2.5-flash` | `backend/src/classification.py` — `CLASSIFICATION_MODEL` |
| Description-recovery model | `gemini-3.6-flash+description` | `backend/src/classification.py` — `RECOVERY_MODEL` |
| Daily request budget / retry headroom | 20 / 8 | `backend/src/classification.py` — `DAILY_REQUEST_BUDGET`, `RETRY_HEADROOM` |
| Batches per run / batch size / pacing | 12 / 100 / 13s | `backend/src/classification.py` |
| Heuristic denylist keywords | frozenset | `backend/src/classification.py` — `DENYLIST_KEYWORDS` |
| Role taxonomy (categories, specializations, levels, tracks, skills) | — | `design/market-health/job-classification.md` (spec) + closed sets in `backend/src/market_query.py` |

### Requirements extraction
| Lever | Value | File |
|---|---|---|
| Model | `gemini-3.6-flash` | `backend/src/requirements.py` — `EXTRACTION_MODEL` |
| Daily budget / retry headroom | 20 / 8 | `backend/src/requirements.py` — `REQUIREMENTS_DAILY_REQUEST_BUDGET`, `REQUIREMENTS_RETRY_HEADROOM` |
| Interactive batch size / pacing / retries | 15 / 13s / 5 | `backend/src/requirements.py` |
| Batch lane: min backlog / max postings / max $ | 100 / 500 / $1.00 | `backend/src/requirements.py` — `REQUIREMENTS_BATCH_MIN_BACKLOG`, `MAX_BATCH_POSTINGS`, `MAX_BATCH_USD` |
| Batch stuck timeout | 72h | `backend/src/requirements.py` — `BATCH_STUCK_AFTER_HOURS` |
| Description truncation | 3000 chars | `backend/src/requirements.py` — `MAX_DESCRIPTION_CHARS` |
| Full explanation | — | `backend/BATCH_PROCESSING.md` |

### Chat / LLM
| Lever | Value | File |
|---|---|---|
| Model | `gemini-3.6-flash` (paid project) | `backend/src/chat.py` — `_CHAT_MODEL` |
| Daily paid request cap | 100/day | `backend/src/ai_interaction_settings.py` — `CHAT_PAID_DAILY_REQUEST_CAP` |
| Synthesis answer length | 2048 tokens | `backend/src/ai_interaction_settings.py` — `CHAT_SYNTHESIS_MAX_OUTPUT_TOKENS` |
| History windows | 15 (synthesis) / 6 (tool stage) | `backend/src/ai_interaction_settings.py` |
| Max user message | 4000 chars | `backend/src/ai_interaction_settings.py` — `MAX_USER_MESSAGE_CHARS` |
| Retry policy | 2 attempts, 1s/2s | `backend/src/llm/chat_fallback.py` |
| Curated instant answers | 6 entries + matcher thresholds | `backend/src/curated_answers.py` — `CURATED_CATALOGUE` |
| Full explanation | — | `backend/AI_INTERACTION_SETTINGS.md` |

### Employment events (added 2026-09-11)
| Lever | Value | File |
|---|---|---|
| Registered adapters | Eurofound ERM, US WARN, UK Companies House, SEC EDGAR | `backend/src/employment_events/__init__.py` — `ALL_EMPLOYMENT_EVENT_ADAPTERS` |
| SEC EDGAR contact | env var (required by SEC's fair-access policy, not a secret) | `SEC_EDGAR_CONTACT` — `backend/.env.example` |
| US WARN source | WARN Firehose, all 50 states in one API | `backend/src/employment_events/us_warn.py` |
| WARN Firehose API key | env var, free tier (25 calls/day) | `WARN_FIREHOSE_API_KEY` — `backend/.env.example` |
| Eurofound ERM access flag | `False` | `backend/src/employment_events/eurofound_erm.py` — `ACCESS_CONFIRMED` |
| Companies House source | Streaming API, all UK companies (revised 2026-09-11) | `backend/src/employment_events/companies_house.py` |
| Companies House API key | env var, free registration | `COMPANIES_HOUSE_API_KEY` — `backend/.env.example` |
| Source-event cursors | resumable stream position, per source | `employment_event_cursors` table (Postgres) |
| Ingestion schedule | `0 7 * * *` (07:00 UTC — offset 1h from job-sync's 06:00 UTC, own service) | `backend/railway.employment-events.json` — `cronSchedule` |

### Gemini projects / keys / billing
| Lever | File / location |
|---|---|
| Which key each workload uses, project isolation, spend caps | `DEPLOYMENT.md` — "Gemini projects & LLM billing" |
| Env vars (`GEMINI_API_KEY_CHAT_PAID`, `_CLASSIFICATION`, `_REQUIREMENTS`) | Railway service settings (`api`, `job-sync`) + local `backend/.env` |

### Deployment
| Lever | File |
|---|---|
| Railway services, roots, start commands, auto-deploy, gotchas | `DEPLOYMENT.md` |
| Per-service config (source of truth) | `backend/railway.{api,admin,json}` |
| CORS allowed origins | `CORS_ALLOWED_ORIGINS` env var on `api` |

---

## 8. Related specs

- `outcomes/job-data-source-flexibility.md` — the outcome this whole model serves
- `backend/specs/market-health/api.md` — Business Logic — Ingestion; Tech Decisions — Source adapter abstraction, Company-list curation
- `design/market-health/job-classification.md` — the role/skill taxonomy
- `changes/2026-07-28-multi-source-job-data-ingestion.md` — the change that replaced Adzuna with the three ATS adapters
- `changes/2026-09-11-employment-event-ingestion.md` — the change that added employment events
  (§2, §3a above); source evaluation in `research/2026-09-11-employment-event-data-sources.md`
