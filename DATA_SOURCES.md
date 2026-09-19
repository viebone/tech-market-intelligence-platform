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
| **Company career pages / ATS portals** | 🔲 planned | Same as job postings — a new *adapter*, not a new type | `raw_postings` | For companies not on a supported ATS (custom career sites, legacy ATS). Mechanism is scraping, not a public API — needs a per-site adapter or a generic HTML/JSON-LD adapter. Same `FetchedPosting` output. Can now build on the generic scraping infrastructure in §3b, once it exists. |
| **Employment events** (renamed from "Layoff events" 2026-09-11 — scope broadened to match) | 🟡 code shipped, 2/3 adapters not yet functional | An `employment_events` row (company, event date, event type, direction, jobs affected, source) — layoffs **and** closures, restructuring, bankruptcy, offshoring, expansion, hiring announcements | Table `employment_events` — *not* `raw_postings`, *not* classified | Feeds the broadened `Layoff Signal` (IA) and the trend chart's "Employment events strip". Data model, endpoint, chat tool, and three adapters implemented — see §3a below. `/change-request`: `changes/2026-09-11-employment-event-ingestion.md`. |
| **Market benchmark datasets (scraped, no API)** | 🟡 code shipped 2026-09-16, not yet run against real data | A `market_observations` row (entity, employment type, location, period, rank, vacancy count/share, salary percentiles) + a `skill_associations` row (role↔skill co-occurrence, weighted) — aggregate market intelligence, not a posting or an event, source-agnostic like `employment_events` (a future second benchmark source is a new `source` value, not a new table) | New tables `market_observations`, `skill_associations` — *not* `raw_postings`, *not* `employment_events` | First source: **IT Jobs Watch** (itjobswatch.co.uk) — declined API/paid access for this project, explicitly granted scraping permission instead (CC-licensed content, conditional on politeness — robots.txt, low rate, identification, caching, attribution). Deliberately modeled as a *category* of source ("market datasets"), parallel to job postings, not a member of them — see `research/2026-09-16-itjobswatch-data-model-analysis.md`. Ingestion only so far; nothing surfaces this data yet. See §3b below and `backend/specs/scraped-data-sources/api.md`. `/change-request`: `changes/2026-09-16-polite-scraping-adapters.md`. |
| **Research / reports / articles** | 🔲 planned | Enrichment text with market commentary | New table — explicitly *not* forced through the posting/classification shape (`job-data-source-flexibility.md` — Success looks like) | Feeds narrative + context, cited as an external source in provenance. Needs its own contract + CR. |

**Out of scope for now** (per the outcome): cross-source dedupe of the same posting; automatic
source routing by cost/quality; paid data licensing.

---

## 3. Job-posting adapters (active)

All four are **public, unauthenticated GET** endpoints — no credentials, no API keys. Each
adapter fetches a company's *entire* published board (none supports server-side filtering to
"tech roles only" consistently), and classification's `other` bucket does the relevance
filtering downstream.

| Adapter | `name` | Endpoint (per company) | Fetches | File |
|---|---|---|---|---|
| Greenhouse | `greenhouse` | `boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true` | Every published job, one call, no pagination | `backend/src/sources/greenhouse.py` |
| Lever | `lever` | `api.lever.co/v0/postings/{site}?mode=json` | Every published job, paginated (`skip`/`limit=100`) | `backend/src/sources/lever.py` |
| Ashby | `ashby` | `api.ashbyhq.com/posting-api/job-board/{jobBoardName}?includeCompensation=true` | Every published job; `includeCompensation` on so pay lands in `raw_response` | `backend/src/sources/ashby.py` |
| Workable | `workable` | `apply.workable.com/api/v1/widget/accounts/{account}` | Every published job, one call, no pagination. **Multi-location jobs are duplicated per location in the raw response** — deduped to one row per distinct `shortcode` (first location kept), same "one row per distinct job" semantics Ashby already applies to its own `secondaryLocations`. Added 2026-09-19 (`EMPLOYER_PANEL.md`) — the first ATS adapter built since the original three, unlocking Starling and any future Workable-hosted employer. No structured salary field on this endpoint. | `backend/src/sources/workable.py` |

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
| Eurofound European Restructuring Monitor | `eurofound_erm` | Keyless CSV export (`apps.eurofound.europa.eu/restructuring-events/factsheetscsv`) — no query params returns the full dataset; access mechanism found by reading Eurofound's own client-side JS, no manual browser step needed after all (`changes/2026-09-11-eurofound-erm-live.md`) | **None — fully keyless and free.** | ✅ **Live — 31,786 real rows ingested 2026-09-11** (EU 27 + Norway), re-run confirmed idempotent (0 new). Full-file refetch every run, not a trailing window (unlike WARN Firehose/SEC EDGAR, this endpoint has no observed rate limit) — `insert_new_events()`'s id-based dedupe handles the overlap. 5 of 9 real restructuring types map onto the closed `event_type` set (94.9% of rows); the other 4 (Merger/Acquisition, Relocation, Reshoring, Outsourcing) are skipped, not guessed — see `research/2026-09-11-eurofound-erm-access-confirmed.md`. Extended the shared `COUNTRY_NAME_TO_ISO2` with 19 real EU/Norway country names found in this data. |
| US state WARN notices | `us_warn` | **WARN Firehose** (warnfirehose.com) — one aggregated API, all 50 states, replaces the original per-state scraping design (found via live research 2026-09-11, same day) | API key, free tier (25 calls/day) — env var `WARN_FIREHOSE_API_KEY` (set, local `backend/.env` only, gitignored) | ✅ **Live — first real data ingested 2026-09-11.** Field mapping verified against a real authenticated response (`company_name`, `industry`→`sector`, real `source_url` per record — see `backend/src/employment_events/us_warn.py`). 25 real rows inserted on first run; re-run confirmed idempotent (0 new). **Real finding**: the feed lags ~9 days behind the actual date (an unfiltered call's `latest_notice` was 9 days stale) — the trailing window was widened from 4 to 30 days after the first run returned 0 (too narrow), same "confirm empirically" correction pattern as everywhere else in this pipeline. |
| UK Companies House — insolvency | `companies_house_insolvency` | **Streaming API** (`stream.companieshouse.gov.uk/insolvency-cases`) — real-time, all UK companies, no company targeting (revised 2026-09-11, replacing a tracked-company candidate-list design — `changes/2026-09-11-employment-events-no-company-matching.md`) | Streaming-type API key (free registration, Companies House Developer Hub) — env var `COMPANIES_HOUSE_API_KEY`, **set 2026-09-11** | ✅ **Live — first real data ingested 2026-09-11.** Field mapping corrected against a real authenticated response (`resource_id` for company number, `data.cases[0].dates[0].date` for the case date — three fields differed from the initial guess). **Known limitation**: the stream carries no company name, only a company number (`company_raw` = the bare id, e.g. `"12028607"` — never fabricated as `"Company N"`, revised 2026-09-11) — resolving names needs a separate REST-type key, not pursued yet. Such events are excluded from the Employment Risk story's company ranking (`is_real_company_name()`) but still count toward direction/country/sector totals — `changes/2026-09-11-employment-risk-hide-placeholder-names.md`. |
| SEC EDGAR (8-K Item 2.05) | `sec_edgar_8k` | Full-text search (`efts.sec.gov/LATEST/search-index`), filtered to structured Item 2.05 ("Costs Associated with Exit or Disposal Activities") — added 2026-09-11 | **None — no key at all, keyless and free.** Requires only a descriptive `User-Agent` (`SEC_EDGAR_CONTACT` env var; falls back to a placeholder that should be replaced with a real contact before relying on this in production) | ✅ **Live — first real data ingested 2026-09-11**, 9 real filings on first run (Veritone, TScan Therapeutics, TELA Bio, PDS Biotechnology, CVD Equipment, and others). The only source so far with a genuine company name straight from the record — see `backend/src/employment_events/sec_edgar.py`. `jobs_affected` and `sector` are `NULL` (not in this index's metadata; sizing/SIC-to-sector mapping not attempted rather than guessed). |
| ~~UK ONS HR1~~ | — | — | — | ❌ **Deliberately not integrated** — macro/aggregate only, no company names; doesn't fit `EmploymentEvent`. See the backend spec's "UK ONS HR1 (descoped)" note. |

**Licensing audit (added 2026-09-16 — `research/2026-09-16-existing-source-licensing-audit.md`),
extending the "always name the source per its licence" principle from `scraped-data-sources`
back across every external source, not only scraped ones.** None of these four is literally
"Creative Commons" — per the operator's own explicit decision, "no CC licence" is read as "no
*confirmed, legitimate* reuse right," of which CC is one kind among several, not the only one
that counts:
- **Eurofound ERM**: the EU's own bespoke reuse policy (attribution required, no distortion) —
  confirmed to a medium level (eurofound.europa.eu's own copyright page rate-limited on direct
  fetch; this reflects the EU's general reuse framework rather than eurofound's own page
  verbatim — worth a direct re-check if this ever becomes higher-stakes).
- **UK Companies House**: Open Government Licence v3.0 — confirmed, high confidence.
- **SEC EDGAR**: public domain, no copyright restriction, per sec.gov's own reuse statement —
  confirmed, high confidence.
- **US WARN notices (via WARN Firehose)**: the underlying government WARN data itself is public
  record with no copyright — but **WARN Firehose's own Terms of Service separately prohibit
  reselling/redistributing raw API access, bulk downloads, or data exports without a commercial
  licence agreement.** ⚠️ **Not resolved** — whether this product's actual use (storing derived
  structured facts, never reselling raw exports) falls inside or outside that restriction is a
  judgement call about the operator's own agreed account terms, not something a public page can
  settle. Needs the operator to either re-read what they actually agreed to at signup, or ask
  WARN Firehose directly — the same move that got IT Jobs Watch's permission in the first place.
  Not disabled pending that — flagged, per the same "always flag, never silently block" rule
  this whole audit is built on — but this is the one open item here.

**No company matching (added 2026-09-11, removed the same day —
`changes/2026-09-11-employment-events-no-company-matching.md`).** A `matched_company` field
and its alias map (`employment_events/company_aliases.py`) briefly linked events to the 35
tracked job-posting companies. Removed entirely, per explicit, repeated user direction:
employment events are an **independent dataset, matched or compared against tracked companies
nowhere in this pipeline** — not the data model, not any query, not any surface. Every
`employment_events` row carries only `company_raw`, exactly as its source reported it.

**Net effect today**: `python ingest_employment_events.py` is live and verified for **all four
registered adapters** — 31,865 real rows in `employment_events` as of 2026-09-11 (31,786
Eurofound ERM, 45 UK Companies House, 25 US WARN, 9 SEC EDGAR), every source's re-run confirmed
idempotent. See `backend/EMPLOYMENT_EVENTS.md` for the always-current per-source breakdown
(query it directly rather than trusting this static count for long). All real employment-event
data surfaces through the **"Employment risk across the market"** data story
(`design/market-health/data-stories.md` — Story 2) and follow-up Layoff Signal conversation —
both fully independent of the platform's 35 tracked companies, by design, at every layer.

**Add a new employment-event source**: a 4-step recipe, documented in full in
`backend/src/employment_events/__init__.py`'s module docstring (write one adapter file
implementing `EmploymentEventAdapter`, register its display name, add it to
`ALL_EMPLOYMENT_EVENT_ADAPTERS`, update this doc) — `ingest_employment_events.py`, the DB
schema, the API endpoint, and the chat tool all already handle "however many adapters are
registered," none of them name a specific source. Same "one adapter, one internal model"
principle as §1's job-posting model.

---

## 3b. Scraped sources (spec'd 2026-09-16, code shipped same day; real production data since 2026-09-18)

**Why this section exists, separate from §3/§3a.** Every source so far (job postings,
employment events) is a public **API** — no HTML parsing, no `robots.txt`, no page cache, no
attribution requirement. Scraping a site with no API is a different mechanism with its own
rules, triggered here for the first time by a real, named, conditional permission grant — see
`research/2026-09-16-itjobswatch-scraping-permission.md`. Full design:
`backend/specs/scraped-data-sources/api.md`.

**The generic mechanism** (`backend/src/scraping/base.py`, once implemented) — a
`PoliteScraper` any future no-API source's adapter can build on, not just IT Jobs Watch's own:
- `robots.txt` fetched, cached, and checked before every request — a disallowed path is skipped
  and logged, never overridden.
- A page already fetched within the cache window (default 24h) is never re-requested at all;
  once that window passes, a conditional request (`If-None-Match`/`If-Modified-Since`) is tried
  before a full re-fetch.
- Pacing floor higher than the API-source `PacedFetcher` default (3s vs 1s) — scraping a whole
  site is a different load profile than one JSON call.
- A required, real contact identifier (`SCRAPER_CONTACT`) on every request's User-Agent — unlike
  the API sources' optional `SEC_EDGAR_CONTACT` courtesy, this one **refuses to run** if unset,
  since the entire adapter's right to exist rests on the permission it was granted under.
- Every stored fact carries mandatory attribution (`source_url`, `licence`, `fetched_at`) — never
  optional, since satisfying the licence's attribution condition later depends on capturing it
  now. The `licence` value itself always comes from `source_licences.py`'s registry, never an
  adapter-local guess — an unregistered source is a hard error.
- **Run cadence is enforced, not scheduled** (added 2026-09-16) — 7 days per source by default,
  checked before any request is made, regardless of how often the ingestion script itself is
  invoked. "Should not overwhelm the server" holds even against a human running the script by
  hand more often than intended.
- **Value-level dedupe on top of id-level dedupe** (added 2026-09-16) — an observation/
  association identical to the last one stored for the same entity is skipped even under a new
  id, so a shifting rolling window doesn't pile up near-duplicate rows carrying no new
  information ("focus on new things, not old").

**Market benchmark datasets are their own source *category*** (revised 2026-09-16 —
`research/2026-09-16-itjobswatch-data-model-analysis.md`), stored source-agnostically in
`market_observations` + `skill_associations` — parallel to job postings and employment events,
not a member of either. IT Jobs Watch is the first adapter; a future benchmark source (e.g. ONS)
is a new `source` value in the same two tables, not a new table.

**Good-practice review (`polite-scraping-review` skill, run 2026-09-16, licence updated same day
after real research against the live site; re-run 2026-09-18 after replacing regex extraction
with LLM-based extraction — `changes/2026-09-18-itjobswatch-llm-extraction.md`) — checked against
the real code, not assumed:**

| Source | Run cadence (enforced how) | `robots.txt`/pacing | New-only fetching | Licence (confirmed?) |
|---|---|---|---|---|
| `itjobswatch` | 7 days — checked in `ingest_scraped_sources.ingest_adapter()` via `scraping_storage.is_due()` against `scrape_ingestion_runs`, *before* the adapter is even constructed; survives the script being invoked more often than intended | ✅ `scraping/base.py`'s `PoliteScraper._check_robots()` + `_pace()`, called on every `get()` — **unchanged by the 2026-09-18 revision** | ✅ `scraping_storage.insert_market_observations()` / `insert_skill_associations()` compare against the most recently stored row per entity and skip an unchanged one, even under a new id — **unchanged by the 2026-09-18 revision**. Plus a new, independent second dedupe layer above storage: `scrape_extractions` (`scraping/itjobswatch.py::_extract_role_page`) skips the LLM call itself when a page's `content_hash` matches what it was last extracted against — this is a cost/re-work guard on the *extraction* step, not a substitute for the storage-level value dedupe, which still runs unchanged after it | **CC BY-NC-SA 4.0 — ✅ confirmed** 2026-09-16 (read directly off itjobswatch.co.uk's own copyright page — `source_licences.py`'s `SOURCE_LICENCES["itjobswatch"].confirmed = True`) — **unchanged by the 2026-09-18 revision** |

**Not a clean sweep, though — the confirmation itself surfaced a real, separate flag**: the "NC"
(NonCommercial) clause. This product has a Premium paid tier. Nothing today violates this
(this data isn't surfaced anywhere yet, on the Free tier or the Premium one) — but before this
data is ever exposed through anything monetized, that clause needs its own explicit resolution
first.

**2026-09-18 revision — why extraction changed, and what's still open.** The first real
production run (2026-09-16) surfaced confirmed-wrong extracted values once checked against the
real cached HTML — not just unverified ones (the historical table is 3 columns, the currency
symbol wasn't decoding, the skills list order was reversed). Regex extraction is replaced by
LLM-based extraction (Gemini `gemini-2.5-flash`, via the existing `llm/` provider abstraction) —
see `backend/specs/scraped-data-sources/api.md`'s "IT Jobs Watch adapter" Business Logic
subsection. Verified by 37 passing unit tests (`backend/tests/test_scraping.py`, up from 29,
covering the new extraction validation and the `scrape_extractions` content-hash dedupe) — **not
yet run against a live Postgres or the real Gemini API**. The 3 `market_observations` + 523
`skill_associations` rows the 2026-09-16 run stored under the old regex extraction are
confirmed wrong and are deleted once this revision is verified live (pending explicit
confirmation before deleting real production rows — see the change request's Execution Plan).

**All four scraped rows now also carry `licence_confirmed: bool`** (added 2026-09-16, mandatory
field, mirrors `licence` itself) — so an unconfirmed source's caveat travels with the data into
storage and any future consumer inherits it with no second lookup. Storing data from any
`confirmed=False` source logs a `WARNING` at ingestion time (`scraping_storage.py`) — always
flagged, never silently blocked. See `data-legibility`'s Provenance section (extended
2026-09-16) for the framework-wide version of this rule: wherever this platform ever builds a
"show your thinking" surface for this data, an unconfirmed-licence caveat must render there too.

| Adapter | `name` | Target | Status |
|---|---|---|---|
| IT Jobs Watch | `itjobswatch` | itjobswatch.co.uk — UK IT demand rank, vacancy share, salary percentiles, regional breakdowns, weighted role↔skill associations, no API, scraping explicitly permitted (CC-licensed content) | 🟡 Code shipped 2026-09-16, **extraction rewritten 2026-09-18** (`scraping/itjobswatch.py`) after the real 2026-09-16 production run (real `PoliteScraper` requests, robots.txt respected, 3 pages) showed the regex extraction it originally shipped with was confirmed wrong against the real page structure (3-column historical table, currency mojibake, reversed skill-list order) — replaced with LLM-based extraction (Gemini `gemini-2.5-flash`), gated by a new `scrape_extractions` content-hash cache so an unchanged page is never re-extracted. Verified by 37 passing unit tests (up from 29). **Still not run against a live Postgres or the real Gemini API.** The 3 observation + 523 skill-association rows the 2026-09-16 run stored are confirmed wrong and are deleted once this revision is verified live. Historical depth beyond the current 3-period comparison is still unchecked. Licence is separately confirmed (CC BY-NC-SA 4.0). First cut prioritizes demand trend, salary distributions, geography, and skill co-occurrence over contractor rates and live-job counts, per the analysis's own ranking. See `changes/2026-09-18-itjobswatch-llm-extraction.md`. |

**Tracked roles (added 2026-09-18 — `changes/2026-09-18-itjobswatch-expanded-role-coverage.md`).**
Same "hand-curated, not exhaustive" discipline as §4's tracked companies, applied here for the
first time to a scraped source: `scraping/itjobswatch.py`'s `ROLE_SLUGS` is a deliberately
curated seed list, not an attempt to cover every role IT Jobs Watch tracks. Every slug is
verified against the real live site (URL resolves, real rank/vacancy figures returned) before
being trusted — same "confirm empirically, never guess" discipline as §4's board-token
verification, just via a single approved `WebFetch` check rather than `curl`, since this is a
read-only confirmation outside the compliant `PoliteScraper` path (same caveat already
documented for the original 3-role check, `research/2026-09-16-itjobswatch-real-page-verification.md`).

Chosen to give real coverage across all three of this platform's own job-posting taxonomy
categories (`classification.py`'s `ROLE_CATEGORIES`) — the original 3 slugs skewed toward
Product Manager (2 of 3) and Designer (1 of 3), with **zero** Engineer coverage despite it
being a core tracked category for job postings.

| Slug | Maps to `role_category` | Verified (rank / vacancy count, 2026-09-18) |
|---|---|---|
| `product-owner` | Product Manager | 468 / 358 |
| `product-manager` | Product Manager | 366 / 536 |
| `ux-designer` | Designer | 562 / 235 |
| `product-designer` | Designer | 718 / 86 |
| `software-developer` | Engineer | 147 / 1,486 |
| `devops-engineer` | Engineer | 169 / 1,339 |
| `data-engineer` | Engineer | 102 / 2,064 |
| `full-stack-developer` | Engineer | 213 / 1,027 |

**How to add a tracked role** (mirrors §5's "add a company" recipe):
1. Confirm the role's real slug and that its page resolves — one approved `WebFetch` (or,
   preferably, a real `PoliteScraper` fetch once this is folded into a verification script) —
   quote the real rank/vacancy figures shown, never guess or invent them.
2. Add the slug to `ROLE_SLUGS` in `scraping/itjobswatch.py`.
3. Add a row to the table above (slug, `role_category` it maps to, the verified figures).
4. Push. The next due ingestion run (`scrape_ingestion_runs.last_run_at` + 7 days) picks it up —
   run cadence is enforced (Business Logic rule 8), so a new slug does **not** trigger an
   immediate re-fetch of the whole source; it's simply included the next time `itjobswatch` is
   actually due.

**Retire a tracked role:** remove it from `ROLE_SLUGS` and the table above. Existing
`market_observations`/`skill_associations` rows stay as historical data, same as retiring a
tracked company (§5).

**Add a new scraped source**: same shape as any other adapter — write a class implementing
`ScrapedSourceAdapter`, register it in `ALL_SCRAPED_SOURCE_ADAPTERS`, get the target's own
scraping-permission terms in writing first (this mechanism exists *because* a permission was
explicitly granted, not as a default right to scrape anything with no API).

---

## 4. Tracked companies

**55 companies**, hand-curated per adapter — a deliberately curated, periodically-reviewed
list, *not* an attempt at exhaustive coverage. Every board token is verified against a live
HTTP 200 before being added (`backend/specs/market-health/api.md` — Tech Decisions —
Company-list curation). A wrong token 404s loudly the same day, not a silent gap.

**16 UK employers added 2026-09-18** (`EMPLOYER_PANEL.md`, `changes/2026-09-18-uk-employer-panel-v1.md`)
— the first slice of a deliberately-designed panel correcting this list's prior skew toward
venture-backed US tech, adding variation in geography (UK) and industry (fintech, marketplace,
insurtech, AI, EdTech, travel, food delivery) — see `EMPLOYER_PANEL.md` for the full 36-employer
candidate list this was drawn from, and its own tracked verification status for the remaining
entries. All 16 use an ATS this codebase already has an adapter for — zero new adapter work.

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
| monzo | greenhouse | Fintech | ✅ |
| deliveroo | greenhouse | Food Delivery/Marketplace | ✅ (Greenhouse board only — also resolves on Ashby, but that's a separate operational/warehouse board, deliberately not tracked, see `EMPLOYER_PANEL.md`) |
| wise | greenhouse | Fintech | ✅ |
| autotrader | greenhouse | Automotive Marketplace | ✅ |
| cleo | greenhouse | Fintech/AI | ✅ |
| zopa | lever | Fintech | ✅ |
| trainline | ashby | Travel/Tech | ✅ |
| quantexa | ashby | AI/Data | ✅ |
| faculty | ashby | AI | ✅ |
| motorway | ashby | Marketplace | ✅ |
| marshmallow | ashby | Insurtech | ✅ |
| multiverse | ashby | EdTech | ✅ |
| attio | ashby | SaaS/CRM | ✅ |
| griffin | ashby | Fintech (Banking-as-a-Service) | ✅ |
| sylvera | ashby | Climate/Data | ✅ |
| beamery | ashby | HR Tech | ✅ |
| rightmovecareers | greenhouse | Property Marketplace/Tech | ✅ (real board token, not "rightmove") |
| ocadogroup | greenhouse | Retail/Tech (Grocery/Robotics) | ✅ (real board token, not "ocado"; board includes non-UK roles — Ocado licenses its robotics internationally) |
| incident | ashby | SaaS (Incident Management) | ✅ (real board token, not "incidentio" — confirmed by "incident.io" appearing in job descriptions) |
| starling-bank | workable | Fintech | ✅ (first company on the new Workable adapter — confirmed real, 55 real jobs) |

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

**Candidate employers not yet added** (added 2026-09-18 —
`research/2026-09-18-uk-employer-panel-plan.md`): see `EMPLOYER_PANEL.md` at the product root —
a deliberately-designed, stratified panel proposal (~36 UK employers, size/sector/geography
variation, correcting this table's current skew toward venture-backed tech) to work through
one entry at a time. Nothing there is verified or added yet; each candidate still needs the
same real verification this section already requires before it becomes a real row above.

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
| Eurofound ERM export endpoint | Keyless, no env var needed | `backend/src/employment_events/eurofound_erm.py` — `EXPORT_URL` |
| Companies House source | Streaming API, all UK companies (revised 2026-09-11) | `backend/src/employment_events/companies_house.py` |
| Companies House API key | env var, free registration | `COMPANIES_HOUSE_API_KEY` — `backend/.env.example` |
| Source-event cursors | resumable stream position, per source | `employment_event_cursors` table (Postgres) |
| Ingestion schedule | `0 7 * * *` (07:00 UTC — offset 1h from job-sync's 06:00 UTC, own service) | `backend/railway.employment-events.json` — `cronSchedule` |

### Scraped sources (spec'd 2026-09-16)
| Lever | Value | File |
|---|---|---|
| Registered scraped-source adapters | IT Jobs Watch (real production data since 2026-09-18) | `backend/src/scraping/__init__.py` — `ALL_SCRAPED_SOURCE_ADAPTERS` |
| **Tracked roles (added 2026-09-18)** | 8 hand-curated role slugs, spanning all 3 job-posting taxonomy categories — see §3b's table for the full list and how to add/retire one | `backend/src/scraping/itjobswatch.py` — `ROLE_SLUGS` |
| **Extraction model (added 2026-09-18)** | `gemini-2.5-flash`, via the `llm/` provider abstraction — reuses the classification pipeline's key, gated by a `content_hash` cache (`scrape_extractions`) so an unchanged page is never re-extracted | `backend/src/scraping/itjobswatch.py` — `EXTRACTION_MODEL` |
| Scraper contact (required — refuses to run if unset) | env var, no fallback placeholder | `SCRAPER_CONTACT` — `backend/.env.example` |
| Pacing floor | 3.0s min interval (vs. API sources' 1.0s) | `backend/src/scraping/base.py` — `PoliteScraper` default |
| Page cache freshness | 24h — no re-fetch within this window | `backend/src/scraping/base.py` — `min_refetch_interval` default |
| `robots.txt` cache TTL | 24h | `backend/src/scraping/base.py` — `ROBOTS_CACHE_TTL_HOURS` |
| **Run cadence (added 2026-09-16)** | 7 days, per source, **enforced** via `scrape_ingestion_runs` — a source not due yet is skipped before any request is made, no matter how often the script is invoked | `backend/src/scraping/__init__.py` — `MIN_RUN_INTERVAL_DAYS` / `DEFAULT_MIN_RUN_INTERVAL_DAYS`; enforcement in `scraping_storage.is_due()` |
| **Value-level dedupe (added 2026-09-16)** | An observation/association identical to the last one stored for the same entity is never re-inserted, even under a new id ("focus on new things, not old") | `backend/src/scraping_storage.py` — `insert_market_observations()` / `insert_skill_associations()` |
| **Per-source CC licence registry (added 2026-09-16)** | One entry per source — confirmed variant, attribution text, licence URL, `confirmed: bool`, `permits_commercial_use: bool`. Unregistered source = hard error, never a guessed placeholder | `backend/src/source_licences.py` — `SOURCE_LICENCES` / `get_licence()` |
| **Per-source use switch (added 2026-09-16, revised twice same day)** | `SourceLicence.rejected` — `False` by default on every source (usable). The *only* thing that blocks use — a deliberate, git-tracked, human decision, never inferred from `confirmed`/`permits_commercial_use`/commercial mode. `TMIP_COMMERCIAL_MODE` stays purely informational (a review reminder, not a gate). Ingestion is never gated by any of this, regardless | `backend/src/source_licences.py` — `SOURCE_LICENCES[...].rejected` / `is_source_usable()`; `backend/.env.example` for the informational `TMIP_COMMERCIAL_MODE`; logged (non-blocking) in `ingest_scraped_sources.ingest_adapter()` |
| **Full-coverage traceability check (added 2026-09-16)** | Every adapter registered anywhere (job postings, employment events, scraped) must have a `source_licences.py` entry, and vice versa — enforced by a test, not a hope | `backend/tests/test_source_licences.py` |

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
- `backend/specs/scraped-data-sources/api.md` — the generic scraping-adapter mechanism and IT
  Jobs Watch's own data model (§2, §3b above); `changes/2026-09-16-polite-scraping-adapters.md`;
  permission grant in `research/2026-09-16-itjobswatch-scraping-permission.md`
