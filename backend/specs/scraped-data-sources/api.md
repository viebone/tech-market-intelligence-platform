---
id: scraped-data-sources
outcome: job-data-source-flexibility
directive: low
status: implemented
created: 2026-09-16
updated: 2026-09-18
---

**Implementation note (2026-09-16)**: built per `/implement-backend`, verified by import-level
and mocked-transport tests only (`backend/tests/test_scraping.py`, 29 passing; a full
`ItJobsWatchAdapter.fetch()` round-trip against a fake HTTP transport) — same "verified by
import, not yet run against a live X" caveat this product's `mcp-access` spec carried before its
own real-connection verification. **Still not yet run against the real database. Partially
verified against the real itjobswatch.co.uk site** (same day, later — see
`research/2026-09-16-itjobswatch-real-page-verification.md`): the real URL pattern and real page
phrasing were confirmed via one approved WebFetch request, and `scraping/itjobswatch.py`'s URL
template and parsing regexes were rewritten against them. Not a full verification — that fetch
was an LLM-summarized reading, not raw HTML, and the actual `PoliteScraper` path has still never
made a real request. Before trusting this with real data: run `ingest_scraped_sources.py`
against a real Postgres to confirm the schema migrates cleanly, and confirm the actual
`PoliteScraper` path (robots.txt check, real `SCRAPER_CONTACT`, pacing) against the live site at
least once.

**Revision note (2026-09-18)** — `changes/2026-09-18-itjobswatch-llm-extraction.md`: the real
first production run (2026-09-16, 3 pages, real `PoliteScraper` requests, robots.txt respected)
confirmed the regex-based extraction above was wrong, not just unverified — the real page is a
3-column historical comparison table (`"{label} {current} {2025} {2024}"`, not
`"{number} {label}"`), the currency symbol wasn't decoding correctly, and the skill list is
`"{rank} {job_count} ({pct}%) {name}"`, not `"{name} ({pct}%)"`. Regex extraction is **replaced
by LLM-based extraction** (Gemini, via the existing `llm/` provider abstraction) — see the
rewritten "IT Jobs Watch adapter" Business Logic subsection and the new `scrape_extractions`
table below. The 3 `market_observations` + 523 `skill_associations` rows that first run inserted
are known-wrong and are deleted once this revision is live (see that change request's Execution
Plan, Step 5).

# Scraped Data Sources — Backend Architecture Spec

## Outcome this implements
See: `outcomes/job-data-source-flexibility.md` (amended 2026-09-16 — scraping named as a
legitimate adapter mechanism alongside API-calling, per this same change).

**No experience spec upstream — deliberately.** Per `changes/2026-09-16-polite-scraping-adapters.md`'s
explicit scope, this change is data acquisition only: nothing user-facing is decided here, no
IA/visual-design layer is touched, no chart or story reads this data yet. Whether and how any of
this data is ever surfaced to a user (a comparison, a data story, a chat/MCP tool) is its own
future change, once real data exists to look at — flagged, not solved, in "What this doesn't
decide," below. This mirrors how `sources/{greenhouse,lever,ashby}.py` and the
employment-event adapters were both speced directly against `DATA_SOURCES.md`'s conventions,
without an experience spec of their own.

---

## Data Models

Two concerns, kept separate: **Part 1** is generic scraping infrastructure (reusable by any
future no-API source); **Part 2** is IT Jobs Watch's own data, the first thing built on it.

### Part 1 — Generic scraping infrastructure

#### RobotsCache (`scrape_robots_cache` table)
One row per host. Holds the parsed permission state so every fetch checks it in-memory rather
than re-fetching `robots.txt` per request.

| Field | Type | Description |
|---|---|---|
| `host` | `str` (PK) | e.g. `"www.itjobswatch.co.uk"` |
| `raw_body` | `text \| None` | The fetched `robots.txt` verbatim. `NULL` if the host has none (a 404 on `/robots.txt` means "no restrictions stated," not an error). |
| `fetched_at` | `datetime` | When this was last fetched — governs re-fetch via `ROBOTS_CACHE_TTL_HOURS` (Tech Decisions). |
| `http_status` | `int` | The status `/robots.txt` itself returned, for debugging. |

Loaded into a stdlib `urllib.robotparser.RobotFileParser` in memory on read — this table stores
the raw text, not a bespoke parsed-rules format, so parsing logic lives in exactly one place
(Python's own robots-parsing library) rather than being reinvented.

#### PageCache (`scrape_page_cache` table)
One row per fetched URL. This is what makes "cache rather than re-fetch unchanged pages" real,
not just a comment in the code.

| Field | Type | Description |
|---|---|---|
| `url` | `str` (PK) | The exact URL fetched. |
| `source` | `str` | Which adapter owns this cache row (`"itjobswatch"`, closed set as more scraped sources are added) — namespacing only, no cross-source logic reads across it. |
| `raw_body` | `text` | The fetched page body, stored so a cache hit never needs the network at all. |
| `content_hash` | `str` | SHA-256 of `raw_body` — lets a fetch that *did* go to the network (no ETag/Last-Modified support) detect "byte-identical to what I already have" and skip re-parsing, not just skip re-fetching. |
| `etag` | `str \| None` | From the response header, when the source sends one — enables a conditional GET (`If-None-Match`) on the next fetch. |
| `last_modified` | `str \| None` | Same idea, `If-Modified-Since`. |
| `fetched_at` | `datetime` | Governs `min_refetch_interval` — a page fetched within that window is served from this row with **no network call at all**, conditional or otherwise (Business Logic, below). |
| `http_status` | `int` | The status the last real fetch returned. |

#### ExtractionCache (`scrape_extractions` table) — added 2026-09-18, LLM extraction dedupe
The cost-saving layer for LLM-based extraction (`changes/2026-09-18-itjobswatch-llm-extraction.md`)
— mirrors what `PageCache.content_hash` already does for the fetch layer, one level up: don't
pay for an LLM call over a page whose content hasn't changed since it was last extracted.

| Field | Type | Description |
|---|---|---|
| `url` | `str` (PK) | The page this extraction was run against — same key as `PageCache.url`. |
| `content_hash` | `str` | The `PageCache.content_hash` this extraction was run against. An adapter checks this against the *current* page's `content_hash` before calling the LLM at all — a match means the page is byte-identical to last time, so the stored `extraction_json` is reused with **zero LLM calls**, not just zero network calls. |
| `extraction_json` | `jsonb` | The LLM's structured output, verbatim — kept as its own provenance record: if an extraction ever looks wrong, this is what to inspect first, without re-fetching or re-calling the LLM. |
| `model` | `str` | Which model produced this extraction (e.g. `"gemini-2.5-flash"`) — travels onto every row built from it via `extraction_model` (Part 2, below), the same "provenance travels with the data" discipline as `licence`/`fetched_at`. |
| `extracted_at` | `datetime` | When the LLM call happened (or, on a cache hit, when the reused extraction was *originally* made — not bumped on a hit, since nothing new was extracted). |

**This is the real answer to "how do we not go through the same data once and again":** the
adapter's flow per page is fetch (already deduped by `PageCache`, Business Logic rule 4) →
compare `content_hash` against `ExtractionCache` → LLM call only on a miss or a changed hash →
store/update `ExtractionCache` → build `FetchedMarketObservation`/`FetchedSkillAssociation` from
`extraction_json` (cache hit or miss, same code path either way) → hand off to the existing
value-level dedupe at insert time (Business Logic rule 9, unchanged). Three independent dedupe
layers, each answering a different question: page fetch (did the network need to be touched?),
extraction (did the LLM need to be touched?), storage insert (did the database need a new row?).

**Deliberately not the real async Gemini Batch API** (`llm/gemini.py`'s `GeminiBatchAdapter`,
already used by `requirements.py` for its own workload). Batch APIs trade higher latency
(often hours) for lower per-call cost by amortizing overhead across many concurrent requests —
neither side of that trade helps here: this source fetches 3 pages/week, so there's no volume to
amortize across, and the `content_hash` gate above already eliminates the redundant calls that
would otherwise be the cost problem. Revisit only if the number of tracked pages grows by an
order of magnitude.

#### FetchedScrapedFact (in-memory dataclass, not a table — the scraping-side counterpart to `FetchedPosting`)
What a scraping adapter hands back to its ingestion script, before storage. Unlike
`FetchedPosting` (whose attribution-shaped fields are optional, best-effort), the fields below
are **mandatory** — a scraped fact with no attribution can't be stored at all, because the
entire reason scraping is permitted here is the licence condition attached to it.

| Field | Type | Description |
|---|---|---|
| `source_ref` | `str` | Unique within this source — the deterministic key the adapter derives from what it scraped (e.g. `"salary:ux-designer:2026-Q3"`). |
| `value` | dict | The adapter's own extracted shape — deliberately generic here, not fixed, since Part 1 must serve sources other than IT Jobs Watch too. |
| `source_url` | `str` | **Mandatory** — the exact page this fact was scraped from. |
| `licence` | `str` | **Mandatory** — the specific licence variant (Tech Decisions flags this needs empirical confirmation for IT Jobs Watch specifically — "Creative Commons" alone isn't a citable licence string). |
| `fetched_at` | `datetime` | **Mandatory** — when this was scraped, so a consumer can judge staleness. |
| `raw_response` | dict/text | The scraped fragment, verbatim — same "never project down, it's the only chance to capture it" discipline as `raw_postings.raw_response`. |

#### SourceLicence (in-memory registry, `source_licences.py` — not a table)
Added 2026-09-16 (`research/2026-09-16-scraping-good-practices-refinement.md`), replacing a
per-adapter hardcoded placeholder string. Every scraped source, current or future, must be
registered here before its adapter can produce a single row — there is no path to a stored
fact's `licence` field that doesn't go through this registry. This is what makes "always name
the source aligned with its own licence" an enforced fact, not a convention someone has to
remember per adapter.

| Field | Type | Description |
|---|---|---|
| `source` | `str` | Matches the adapter's own `name` — the registry key. |
| `licence` | `str` | The confirmed licence variant (e.g. `"CC BY 4.0"`) — or, until confirmed, an explicitly-labelled placeholder that a lookup can distinguish from a real value (never a bare `"Creative Commons"` presented as if it were specific). |
| `attribution_text` | `str` | The exact text to show wherever this data is displayed or republished, satisfying that licence's own attribution requirement — not just the licence name, the actual citation string. |
| `licence_url` | `str` | Link to the licence deed/source's own licence statement, for anyone who needs to verify terms later. |
| `confirmed` | `bool` | `False` until a human has actually read the source's own licence statement and confirmed the variant — never set `True` by inference or guess. A registry entry existing at all is not the same as it being confirmed. |
| `permits_commercial_use` | `bool` | Added 2026-09-16 — **informational only**, revised same day: does this source's licence itself say commercial use is OK? IT Jobs Watch's CC BY-NC-SA 4.0 sets this `False` (the "NC" clause). Feeds a human's decision on `rejected`, below; does not by itself block anything. |
| `rejected` | `bool` | Added 2026-09-16, default `False` — the **only** field that actually gates use. Set `True` only by a human deliberately editing this file after reviewing a source's terms — never inferred from `confirmed`, `permits_commercial_use`, or commercial mode. See "Per-source switch," below. |
| `data_summary` | `str` | Added 2026-09-16 (`research/2026-09-16-job-posting-source-licensing.md`) — plain-language "what do we actually take from this source," shown next to the licence itself in the admin view so nobody has to cross-reference `DATA_SOURCES.md` to answer "is this specific data covered." |

**This registry now covers every adapter in the codebase, not only scraped ones** — job-posting
sources (`greenhouse`/`lever`/`ashby`) and employment-event sources
(`sec_edgar_8k`/`companies_house_insolvency`/`eurofound_erm`/`us_warn`) are registered here too,
alongside `itjobswatch`. `backend/tests/test_source_licences.py` enforces full coverage: every
adapter registered in `ALL_SOURCE_ADAPTERS`, `ALL_EMPLOYMENT_EVENT_ADAPTERS`, or
`ALL_SCRAPED_SOURCE_ADAPTERS` must have a matching entry here, and vice versa (no stale
entries either) — this is what makes "every bit of data can be tracked against a licence" an
enforced fact rather than a hope.

Looking up an unregistered source is a hard error (`LicenceNotRegisteredError`, or equivalent) —
an adapter can't silently ship with no licence answer, the same "refuses rather than proceeds
with a placeholder" discipline `PoliteScraper`'s `SCRAPER_CONTACT` check already applies to
identification.

**Always flag if unconfirmed — never block, never bury.** Added 2026-09-16
(`research/2026-09-16-scraping-good-practices-refinement.md`). An unconfirmed licence is not a
reason to refuse storing data (unlike a missing `SCRAPER_CONTACT`, which *is* refused — the
difference: identification is entirely within this platform's control to get right before
running at all, while confirming a third party's exact licence wording sometimes takes a real
human reading a real page). Two things make "always flag" real rather than aspirational:
1. `licence_confirmed: bool` is copied onto every `FetchedMarketObservation`/
   `FetchedSkillAssociation` at construction time (mandatory field, mirrors `licence` itself) —
   so the caveat travels with the row into storage, not just the code registry. A future
   consumer reads it off the row directly, with no second lookup.
2. Storing any row from a `confirmed=False` source logs a `WARNING` (not `INFO`) at ingestion
   time, naming the source and the unconfirmed licence string — see
   `scraping_storage._warn_if_licence_unconfirmed()`.

This is the ingestion-time half of a framework-wide principle (`data-legibility`'s Provenance
section, extended 2026-09-16): wherever this platform ever builds a "show your thinking" /
reasoning surface for data derived from this table, an unconfirmed-licence row's caveat must
render there too — not dropped once it leaves storage. Binding on whichever future change
eventually builds that surface, not on this one (nothing surfaces this data yet).

**Per-source switch — gates USE, never gates COLLECTION.** Added 2026-09-16
(`research/2026-09-16-commercial-mode-kill-switch.md`), revised twice same day. First revision:
*"we want to keep all sources in the ingestion runs... we would exclude the data later if we
don't get a license"* — collection is never gated. Second revision, replacing an earlier
automatic-inference design: *"we can switch on/off by sources. Just make sure that ingestions
always work and that insights and other functionality always work unless we say license
rejected. but in any case the ingestions can work until we say the opposite."*

`SourceLicence.rejected` (Data Models, above) is now the **only** thing that gates use — a
plain boolean, defaulting to `False`, flipped only by a human deliberately editing
`source_licences.py`. `source_licences.is_source_usable(source)` is exactly
`not get_licence(source).rejected` — nothing else. `confirmed` and `permits_commercial_use`
remain in the registry as context a human reads *before* deciding whether to set `rejected`;
neither computes a block by itself anymore. `TMIP_COMMERCIAL_MODE`/`is_commercial_mode()` is
kept as a purely informational signal (surfaced in the admin view — "you're monetized now, go
review sources") — it does not, by itself, change any source's usability. This is a deliberate
simplification over the first design (which auto-inferred a block from
`confirmed`/`permits_commercial_use`/commercial mode): a single, explicit, git-tracked human
decision is both simpler and more honest than encoding every real-world nuance (e.g. WARN
Firehose's redistribution-only restriction, which was never cleanly a "commercial use" question)
into automated boolean logic.

**What actually calls it today**: `ingest_scraped_sources.py` calls it once per adapter, purely
to log a visible, non-blocking note when a source is explicitly `rejected` — ingestion proceeds
regardless, always. **Forward-binding on any future query/display function**: per the same
discipline as `licence_confirmed`'s propagation requirement above, any future code that reads
`market_observations`/`skill_associations` back out to actually *use* it (a chart, a chat
answer, an MCP tool, anything shown to or acted on by a person or another system) **must** call
`is_source_usable(row.source)` and exclude what it returns `False` for — this is the real
enforcement point, specified now for whichever later change builds that reader. Collection and
use are, and remain, two different gates — ingestion has no gate at all.

#### IngestionRun (`scrape_ingestion_runs` table) — added 2026-09-16, enforced weekly cadence
Tracks the last completed run per source, so "run once a week" is an enforced guard in code —
same "don't just comment it, enforce it" discipline `PoliteScraper`'s pacing already follows —
not a cron-schedule comment nobody checks if a run happens to trigger twice.

| Field | Type | Description |
|---|---|---|
| `source` | `str` (PK) | The adapter's `name`. |
| `last_run_at` | `datetime` | When that source's ingestion last completed (successfully or not — even a failed run counts, so a broken adapter can't be hammered by repeated immediate retries either). |

`ingest_scraped_sources.py` checks this before calling an adapter's `fetch()` at all: if
`last_run_at` is within `MIN_RUN_INTERVAL_DAYS` (7, Tech Decisions) of now, the adapter is
skipped entirely for this invocation — logged plainly, not silently — regardless of how often
the script itself is invoked (manually, or by a misconfigured scheduler later). This is what
makes "should not overwhelm the server" true even if a human runs the script by hand more often
than intended.

### Part 2 — Market benchmark observations (revised 2026-09-16 —
`research/2026-09-16-itjobswatch-data-model-analysis.md`)

**Reframed from an IT-Jobs-Watch-specific table to its own source-agnostic model**, on the same
principle `employment_events` already established: a *category* of source (here, "aggregate
market benchmark data," alongside "job postings" and "employment events" in `DATA_SOURCES.md`
§2), not a per-adapter table. IT Jobs Watch is the first adapter; a future benchmark source
(e.g. ONS) would be a second `source` value in the same two tables below, not a third table —
same "one adapter, one shared model" discipline §1 of `DATA_SOURCES.md` states for every source
category. This shape is *not* a job posting and *not* a discrete event; it's a periodic,
dimensional aggregate — a genuinely third shape.

#### MarketObservation (`market_observations` table)
One row per (source, entity, employment type, location, period) — the demand/salary/geography
side of the analysis.

| Field | Type | Description |
|---|---|---|
| `id` | `str` (PK) | `f"{source}:{entity_type}:{entity_name}:{employment_type}:{location}:{period_start}"` — same deterministic-composite-key dedupe pattern as `raw_postings.id` / `employment_events.id`. |
| `source` | `str` | Which adapter produced this row — `"itjobswatch"` today, closed set as more benchmark sources are added (same pattern as `employment_events.source`). |
| `entity_type` | `"role" \| "skill" \| "technology" \| "capability"` | Closed set, chosen to line up with this platform's own taxonomy categories where possible (Business Logic — taxonomy reconciliation, below). |
| `entity_name` | `str` | The source's own label for the entity (e.g. `"Product Owner"`). |
| `taxonomy_match` | `str \| None` | This platform's own canonical taxonomy term, when a confident match exists (Business Logic, below). `NULL` when no confident match was made — the source's raw `entity_name` is never silently treated as a taxonomy term it doesn't actually match. |
| `employment_type` | `"permanent" \| "contract"` | Closed set — kept as genuinely separate markets per the analysis, never blended in a query without the caller explicitly asking for both. |
| `location` | `str` | The source's own regional label verbatim (e.g. `"London"`, `"UK excluding London"`, `"Work from Home"`, `"Scotland"`) — **not** run through `normalize_country()` (that's country-level ISO-2 normalization; this is sub-national UK regions, a different vocabulary). `"UK"` when the source reports no regional breakdown for this row. |
| `period_start` / `period_end` | `date` | The exact window this observation covers — IT Jobs Watch's own rolling window (its own Product Owner example is six months), not assumed to be a calendar month or quarter. |
| `rank` | `int \| None` | Demand rank at time of fetch. |
| `rank_yoy_change` | `int \| None` | Signed position change vs. the same period a year prior. |
| `vacancy_count` | `int \| None` | Absolute count over `period_start`–`period_end`. |
| `vacancy_share` | `numeric \| None` | This entity's share of all vacancies in its `employment_type`, as a percentage — the number that can move independently of, and sometimes opposite to, `vacancy_count` (the analysis's own example: count up, share down). |
| `live_jobs` | `int \| None` | Current live count — a different, narrower figure from `vacancy_count`'s rolling-window total; never conflated with it. |
| `salary_sample_size` | `int \| None` | How many of the vacancies in this window quoted a salary — the real denominator behind the percentiles below, always carried alongside them (never presented without it, per this platform's own data-legibility rule for any statistic). |
| `salary_p10` / `salary_p25` / `salary_median` / `salary_p75` / `salary_p90` | `numeric \| None` | The full percentile spread, not just a median — captured because the analysis is explicit that the spread itself is part of the value ("how wide is the distribution"). |
| `salary_unit` | `"GBP/year" \| "GBP/day" \| None` | States explicitly whether the percentiles above are annual salary (`employment_type = "permanent"`) or day rate (`"contract"`) — the two are never comparable without this being explicit, and this field is what makes that self-describing wherever the row is read, not something a caller has to infer from `employment_type`. |
| `salary_yoy_change` | `numeric \| None` | Percentage change vs. the same period a year prior. |
| `source_url` | `str` | Mandatory (Part 1). |
| `licence` | `str` | Mandatory (Part 1) — the confirmed specific CC variant. |
| `licence_confirmed` | `bool` | Mandatory (Part 1, added 2026-09-16) — copied from `SourceLicence.confirmed` at scrape time, so the "always flag if unconfirmed" caveat travels with the row itself, not just the code registry. |
| `fetched_at` | `datetime` | Mandatory (Part 1). |
| `extraction_model` | `str \| None` | Added 2026-09-18 — which model turned the raw page into these field values (e.g. `"gemini-2.5-flash"`), copied from `ExtractionCache.model`. `NULL` only for rows that predate this revision (none should remain once the cleanup step in `changes/2026-09-18-itjobswatch-llm-extraction.md` runs). |
| `raw_response` | `text` | The scraped fragment, verbatim. |
| `created_at` | `datetime` | Row insert timestamp. |

#### SkillAssociation (`skill_associations` table)
One row per (source, role, skill, period) — the market-derived, *weighted* role→skill graph the
analysis flags as possibly the most valuable single dataset here, since it ties directly into
this platform's own existing skill extraction from job descriptions.

| Field | Type | Description |
|---|---|---|
| `id` | `str` (PK) | `f"{source}:{role_name}:{skill_name}:{period_start}"`. |
| `source` | `str` | Same closed set as `MarketObservation.source`. |
| `role_name` | `str` | The source's own role label this association is under. |
| `role_taxonomy_match` | `str \| None` | Same reconciliation concept as `MarketObservation.taxonomy_match`, applied to the role side. |
| `skill_name` | `str` | The associated skill, as the source labels it. |
| `skill_taxonomy_match` | `str \| None` | Same reconciliation concept, applied against this platform's existing skill vocabulary (`posting_skills` — the same skill taxonomy this platform's own requirements-extraction pipeline already populates, so a match here is directly comparable to what's already extracted from real job descriptions). |
| `period_start` / `period_end` | `date` | Same shape as `MarketObservation`. |
| `job_count` | `int \| None` | How many vacancies for this role also mention this skill. |
| `percentage` | `numeric \| None` | `job_count` as a share of all vacancies for this role (e.g. `45.92`). |
| `rank` | `int \| None` | This skill's rank among all skills associated with this role. |
| `source_url` / `licence` / `licence_confirmed` / `fetched_at` | mandatory (Part 1) | Same as `MarketObservation`. |
| `extraction_model` | `str \| None` | Added 2026-09-18 — same as `MarketObservation.extraction_model`. |
| `raw_response` | `text` | Verbatim. |
| `created_at` | `datetime` | Row insert timestamp. |

No relationship (FK or otherwise) to `raw_postings` or `employment_events` — same independence
precedent `employment_events` already set for a differently-shaped source; nothing here assumes
or requires a join to either. `SkillAssociation.skill_taxonomy_match` is a *label-level* echo of
this platform's own skill vocabulary, not a join to `posting_skills` rows.

---

## API Endpoints

**None.** Ingestion here is a script, the same pattern as `ingest.py` / `ingest_employment_events.py`
— not a REST surface. No endpoint reads `market_observations` or `skill_associations` back out
yet either: nothing in this
product (not the frontend, not chat, not MCP) has a decided reason to query it yet, per "What
this doesn't decide," below. Recording that plainly here, in an otherwise-empty section, rather
than skipping the section — an empty section states a fact; a missing one looks like an
oversight.

---

## Business Logic

### Polite scraping — the mechanical rules, generic to any future scraped source

1. **`robots.txt` first, always.** Before an adapter's first request to a host in a given run,
   fetch/refresh `RobotsCache` (respecting its TTL — Tech Decisions) and load it into a
   `RobotFileParser`. Every URL is checked against it before the request is made.
2. **A disallowed path is skipped, logged, and never overridden.** No adapter option or config
   flag can bypass this — matches this codebase's existing fault-isolation discipline
   (`PacedFetcher`'s per-company isolation, `SecEdgarAdapter`'s per-hit skip-and-continue): one
   page being off-limits degrades that page's data, never the whole run, and never becomes a
   reason to fetch it anyway.
3. **Pacing** — a configurable `min_interval_seconds` per adapter, same shape as
   `PacedFetcher._pace()`, but with a different default (Tech Decisions — 3.0s, not 1.0s).
4. **Cache before network, every time.** Before any GET: check `PageCache` for that URL. If
   `fetched_at` is within `min_refetch_interval` (default 24h — Tech Decisions), return the
   cached `raw_body` with **zero network calls** — not even a conditional request. Only once
   that window has elapsed does a real request happen, and even then it's conditional
   (`If-None-Match` / `If-Modified-Since`) whenever the cached row has an `etag` or
   `last_modified` to offer. A `304 Not Modified` response updates only `fetched_at`, never
   `raw_body` — the page is confirmed unchanged, not re-stored.
5. **Identification is load-bearing, not a courtesy.** Every request carries a User-Agent built
   from `SCRAPER_CONTACT` (Tech Decisions) — e.g.
   `"TechMarketIntelligencePlatform-Scraper/1.0 (+{contact})"`. Unlike this codebase's existing
   `SEC_EDGAR_CONTACT` precedent (which falls back to a placeholder locally, with a comment to
   fix it before production), **this adapter refuses to run at all** if `SCRAPER_CONTACT` is
   unset or looks like a placeholder — see Tech Decisions for why this is deliberately stricter.
6. **Attribution travels with the data, not just in a comment.** Every `FetchedScrapedFact` (and
   therefore every stored row) carries `source_url`, `licence`, and `fetched_at` as mandatory
   fields — there is no code path that stores a scraped fact without them. This is what makes
   the licence's attribution condition satisfiable later, whenever/if this data is ever shown
   anywhere — the provenance isn't reconstructed after the fact, it's captured once, at scrape
   time, same "the only chance to capture it" discipline as `raw_response` everywhere else in
   this codebase.
7. **Fault isolation** — one page or dimension failing (network error, unexpected markup) is
   logged and skipped; it never aborts the rest of that adapter's run or any other adapter's run,
   matching every existing source in this codebase.
8. **Run cadence is enforced, not just scheduled.** Added 2026-09-16
   (`research/2026-09-16-scraping-good-practices-refinement.md`) — "it has to run once a week"
   is a real guard checked against `IngestionRun.last_run_at` (Data Models, above) before an
   adapter's `fetch()` is even called, not a hope that whatever eventually triggers this script
   only does so weekly. An adapter run within `MIN_RUN_INTERVAL_DAYS` (7, Tech Decisions) of its
   last completed run is skipped for this invocation, logged plainly. This holds even if the
   script itself is invoked more often — by a human testing, or a future misconfigured
   scheduler — the same "don't trust the caller to behave, enforce it here" reasoning already
   behind rule 5's refusal-to-construct.
9. **Store only what actually changed — "focus on new things, not old."** Added 2026-09-16, same
   signal as rule 8. Before inserting a new `market_observations` row, its comparable fields
   (everything except `id`/`period_start`/`period_end`/`fetched_at`/`raw_response`) are compared
   against the most recently stored observation for the same
   `(source, entity_type, entity_name, employment_type, location)`. Identical values are **not**
   re-inserted — logged as "unchanged since last observation," not silently dropped. This
   matters specifically because a weekly rolling-window source can report the exact same
   figures two weeks running (nothing in the underlying market changed) while `period_start`/
   `period_end` still shift forward — without this check, `market_observations` would
   accumulate one near-duplicate row per week per entity forever, none of them carrying any new
   information. `skill_associations` gets the same treatment, compared on `job_count`/
   `percentage`/`rank`.
10. **The per-source `rejected` switch gates use, never collection.** Added 2026-09-16, revised
    twice same day (Data Models — `SourceLicence.rejected`, above). Nothing in this file ever
    stops an adapter from running — ingestion collects every registered source regardless,
    always. `rejected` defaults to `False`; the only thing that flips it is a human deliberately
    editing `source_licences.py`. When a source is rejected, ingestion only logs (non-blocking)
    that it isn't cleared for use; the actual exclusion is required of any future function that
    reads this data back out to use it. `TMIP_COMMERCIAL_MODE` is informational only — it never
    flips `rejected` on its own.
11. **Extraction is deduped independently of the fetch, via content hash.** Added 2026-09-18
    (`ExtractionCache`, Data Models, above). Before turning a fetched page into structured
    fields, an adapter checks `scrape_extractions` for that `url`; if a row exists and its
    `content_hash` matches the page's current `content_hash`, the stored `extraction_json` is
    reused and no LLM call is made. Only a page whose content actually changed since the last
    extraction triggers a new LLM call. This is on top of, not instead of, rule 4's page-fetch
    cache — a page can be a fetch-cache hit (served from `PageCache`, no network call) and still
    correctly skip extraction too (served from `ExtractionCache`, no LLM call), or a page can be
    freshly fetched (network call happened) but still be an extraction-cache hit if its content
    turned out byte-identical to what was already stored.

### IT Jobs Watch adapter — LLM-based extraction (revised 2026-09-18, replacing regex)

**Why regex extraction was replaced.** The first real production run (2026-09-16 — real
`PoliteScraper` requests, robots.txt respected, 3 pages fetched) surfaced confirmed-wrong
extracted values once checked against the real cached HTML: the historical comparison table is
3 columns (`"{label} {current} {same-period-2025} {same-period-2024}"`), not the assumed
`"{number} {label}"`; the currency symbol wasn't decoding as `£`; and the skills list is
`"{rank} {job_count} ({pct}%) {name}"`, not the assumed `"{name} ({pct}%)"`. Concretely: `rank`/
`vacancy_count` picked up numbers from adjacent table cells, all 5 salary percentiles landed
`NULL`, and every `skill_name` was garbled (e.g. `"Roadmaps 2 162"` instead of `"Roadmaps"`).
Real page structure kept surprising a hand-written regex; an LLM reading the page's plain text is
materially less brittle to exactly this kind of surprise, and was the direction the outcome owner
explicitly leaned toward given it also solves the cost/dedupe question below.

**What's extracted, and how:**
1. The already-fetched, already-cached page (`PageCache.raw_body`, HTML — unchanged, still
   governed by rules 1-7 above) is reduced to plain text via BeautifulSoup's `get_text()` — same
   library already a dependency here, now used for text extraction instead of feeding regexes
   directly. This also resolves the currency-mojibake issue: BeautifulSoup decodes HTML entities
   (`&pound;` → `£`) itself, so the LLM sees a correctly-decoded `£` in the text it reads, not a
   raw encoding bug.
2. The plain text (not raw HTML — cheaper, and removes markup noise that isn't informative to
   the extraction) is sent to `providers.gemini("gemini-2.5-flash")` (Tech Decisions) with a
   system instruction asking for the same structured shape `FetchedMarketObservation`/
   `FetchedSkillAssociation` already need: `rank`, `rank_yoy_change`, `vacancy_count`,
   `vacancy_share`, `salary_p10`/`p25`/`median`/`p75`/`p90`, `salary_sample_size`,
   `salary_yoy_change`, and a `skills` array of `{rank, job_count, percentage, name}` — strict
   JSON, no prose, matching this codebase's existing `classification.py` prompt/parse idiom
   (`_build_prompt` / `_parse_response`: strip markdown fences, `json.loads`, fields the model
   omits or that fail validation come back `None` — never guessed or coerced, same "unmatched
   means NULL, not a made-up value" discipline the regex version already followed).
3. Before step 2 runs at all, `ExtractionCache` is checked by `(url, content_hash)` (Business
   Logic rule 11) — a hit skips the LLM call entirely and reuses the stored `extraction_json`.
4. The LLM's validated JSON is what builds `FetchedMarketObservation`/`FetchedSkillAssociation`
   — the same dataclasses, same downstream storage/dedupe (rule 9), same mandatory attribution
   fields (rule 6) as before. Only the step that turns page text into field values changed.

**Explicitly not the real Gemini Batch API** — see `ExtractionCache`'s own note in Data Models
for why (3 pages/week has no volume to batch; the `content_hash` gate is the actual saving).

**Priority order for the first implementation cut** (per
`research/2026-09-16-itjobswatch-data-model-analysis.md`'s own explicit ranking — don't build
every dimension the site offers at once):
1. Historical role/skill demand — `vacancy_count`, `vacancy_share`, `rank`, `rank_yoy_change`.
2. Salary distributions — the full `salary_p10`...`salary_p90` spread + `salary_sample_size`.
3. Geography — the `location`-broken-down rows.
4. Role↔skill co-occurrence — `SkillAssociation`.

Contractor day-rate benchmarking, `live_jobs`, and role-taxonomy-variant reconciliation
(`taxonomy_match` / `role_taxonomy_match` / `skill_taxonomy_match`, below) are real fields in the
model above but lower priority — the adapter can leave them `NULL` in a first pass without that
being a gap worth blocking on.

**Confirmed 2026-09-16/18, against real cached HTML (`scrape_page_cache.raw_body`), not a
paraphrase**: the real URL pattern (`/jobs/uk/{title}.do`, spaces as `%20`), the real 3-column
historical table structure, the real `"{rank} {job_count} ({pct}%) {name}"` skills format, and
that the page lists exactly 30 co-occurring skills ("Top 30 Co-Occurring Skills & Capabilities").
**Still not confirmed**: how much historical depth beyond the current 6-month rolling window is
actually reachable on this same page shape — the source claims data back to 2004, but what's
shown here is only a 3-period (current/2025/2024) comparison, not a full series.

**A process note on how the 2026-09-16 check was done, for the record**: that verification pass
included an uncontrolled `curl` request outside the compliant `PoliteScraper` path (no prior
`robots.txt` check, a placeholder identifier) — disclosed in full in
`research/2026-09-16-itjobswatch-real-page-verification.md`. Not repeated since; the actual
scraper (`PoliteScraper`) was never used to make either check and remains untouched by it.
- ~~The specific CC licence variant~~ — **confirmed 2026-09-16**, read directly off
  itjobswatch.co.uk's own copyright page: **CC BY-NC-SA 4.0**, attribution wording "Source: IT
  Jobs Watch," with vacancy listings and third-party material explicitly excluded (not relevant
  here — this adapter never touches vacancy listings). Recorded in `source_licences.py`,
  `confirmed=True`. **One real, unresolved flag this confirmation surfaced**: the "NC"
  (NonCommercial) clause. TMIP has a Premium paid tier — nothing today violates this (this data
  isn't surfaced anywhere yet), but *before* this data is ever exposed through anything
  monetized, that needs its own explicit resolution (Free-tier-only, or confirming with IT Jobs
  Watch that this product's specific use qualifies as non-commercial) — not something to
  discover after the fact once a paid feature already depends on it.

### Taxonomy reconciliation — a hook, not a commitment

`taxonomy_match` / `role_taxonomy_match` / `skill_taxonomy_match` are reserved fields, populated
only where a confident match against this platform's existing taxonomy vocabulary (role
categories, specializations, and — for skills — the same vocabulary `posting_skills` already
uses) is straightforward, e.g. an exact or near-exact string match. Building a real reconciliation
pass (fuzzy matching, handling the source's own role variants like "Product Owner" vs. "Technical
Product Owner" vs. "Digital Product Owner") is explicitly **deferred** — per the analysis, this
is a genuine future opportunity to validate/enrich this platform's taxonomy against a real
external market vocabulary, not something to build blind before any real scraped entity names
exist to match against. Leaving a row's `*_match` field `NULL` is the correct, expected state for
anything not confidently matched — never a coerced guess.

### Permanent vs. contract — never silently blended

A `MarketObservation` row's `salary_p10`...`salary_p90` mean different things depending on
`employment_type` — annual salary for `"permanent"`, day rate for `"contract"` — and `salary_unit`
states which explicitly on every row. No business logic anywhere may average, rank, or compare
these two `employment_type` values against each other without a caller having explicitly asked
for that comparison; the two are kept as genuinely separate markets, per the analysis's own
framing (`employment_market: permanent | contract`).

### What this doesn't decide

- **Whether/where this data ever surfaces to a user.** No chart, story, chat tool, or MCP tool
  reads `market_observations` or `skill_associations` as of this spec. That's a real product
  decision (what does "our number vs. their number" mean to a job-seeker, and is it even a fair
  comparison given the two platforms measure different populations?) deserving its own
  outcome/experience pass once real data exists to look at — not something to decide implicitly
  by writing a query function here. Worth flagging plainly, though not deciding: the analysis's
  own use-case list (market share vs. count, regional comparison, weighted skill graph) lines up
  closely with `outcomes/understand-market-health-before-searching.md` — a strong future
  candidate, once this exists as real data, not before.
- **Any comparison logic between this data and the platform's own `raw_postings`-derived
  numbers.** Not attempted, not implied by these two tables merely coexisting.
- **Reconciling IT Jobs Watch's role-variant taxonomy against this platform's own** (e.g.
  "Technical Product Owner" vs. this platform's `role_category`/`specialization` set) beyond the
  reserved-but-unpopulated `*_match` fields above.
- **When/whether `TMIP_COMMERCIAL_MODE` actually gets flipped to `true`.** That's a business
  decision (when this product starts charging for something), not a technical one — this spec
  only guarantees that *when* it happens, the switch already works.

---

## External Dependencies

- **IT Jobs Watch** (itjobswatch.co.uk) — public website, no API, no credentials. Scraped under
  the explicit permission described in `research/2026-09-16-itjobswatch-scraping-permission.md`,
  bound by the five rules above.
- `httpx` — already a dependency; reused for fetching (same client library `PacedFetcher` uses).
- `beautifulsoup4` + `lxml` — already a dependency (added 2026-09-16). Used for plain-text
  extraction (`get_text()`) since the 2026-09-18 revision, not just as a stepping-stone to regex.
- **Gemini, `gemini-2.5-flash`, via the existing `backend/src/llm/` provider abstraction**
  (`providers.gemini("gemini-2.5-flash")`) — added 2026-09-18. Same model
  `classification.py` already uses for the same kind of job (turn messy real-world text into
  validated structured fields); reused rather than a new consumer/key, given the tiny added
  volume (3 pages/week). Uses the classification project's existing key
  (`GEMINI_API_KEY_CLASSIFICATION`) — no new Gemini project or key needed at this volume; revisit
  if this source's page count grows enough to meaningfully compete with the classification
  pipeline's own quota.
- Python stdlib `urllib.robotparser` — `robots.txt` parsing, no new dependency.

---

## Tech Decisions

**Where this lives — `backend/src/scraping/`, a new sibling to `sources/` and `employment_events/`.**
- `scraping/base.py` — `PoliteScraper` (robots-aware, cache-aware, paced `get()`),
  `ScrapedSourceAdapter` protocol, `FetchedScrapedFact`.
- `scraping/itjobswatch.py` — the first concrete adapter.
- `scraping/__init__.py` — `ALL_SCRAPED_SOURCE_ADAPTERS`, same registration pattern as
  `ALL_SOURCE_ADAPTERS` / `ALL_EMPLOYMENT_EVENT_ADAPTERS`.
- `ingest_scraped_sources.py` (product root, sibling to `ingest.py` /
  `ingest_employment_events.py`) — run manually or via cron later, iterates registered adapters,
  same per-source fault isolation as the other two ingestion scripts.

**Why a sibling module, not extending `sources/base.py` in place.** `SourceAdapter`/`PacedFetcher`
are API-shaped: one GET-with-retry primitive, no `robots.txt` concept, no page cache, no mandatory
attribution. Bolting those onto the existing protocol would either force unused fields onto
Greenhouse/Lever/Ashby or make critical scraping fields optional (defeating the point — mandatory
attribution is the whole reason this is safe to build). A sibling module keeps the existing three
adapters untouched while sharing the same *spirit* (one adapter per source; nothing downstream
cares which produced a row) — the same precedent `employment_events/` already set sitting next to
`sources/` rather than inside it.

**Contact/identification — stricter than the `SEC_EDGAR_CONTACT` precedent, deliberately.**
`sec_edgar.py` falls back to a placeholder locally with a comment to fix it before production —
acceptable there because SEC's policy is a general fair-access courtesy to an anonymous public
API. This is different: a named person at IT Jobs Watch granted a specific, conditional
permission to this specific project. Running this adapter with a placeholder contact would
itself be a small violation of what was actually granted. `SCRAPER_CONTACT` is checked at
`PoliteScraper` construction time — missing, empty, or containing a placeholder marker (e.g.
`"example.com"`, `"set SCRAPER_CONTACT"`) raises immediately rather than proceeding with a
fallback. If this feels too strict once implemented, that's a conversation to have explicitly —
not something to quietly loosen.

**Caching store — Postgres, not the filesystem.** Matches this product's existing convention of
keeping all ingestion state in the one database (`ingestion_runs`, `employment_event_cursors`) —
nothing to lose on a redeploy, one place to inspect.

**Default pacing — `min_interval_seconds=3.0`, not `PacedFetcher`'s `1.0`.** Scraping a full site
(many pages) is a different request-volume profile than one JSON call per company, and the
permission's own language ("low request rate... sensible pauses") reads as asking for slower
than the existing API-adapter bar, not the same. Configurable per adapter if a specific source
later needs a different value — this is IT Jobs Watch's starting default, not a hard product-wide
constant.

**Default cache freshness — `min_refetch_interval=24h`.** A page fetched within the last 24 hours
is never re-requested at all, matching "cache rather than re-fetch unchanged pages" plainly. This
product's other ingestion already runs roughly daily (`job-sync` 06:00 UTC, employment-events
07:00 UTC), so a 24h cache window costs nothing the rest of the pipeline doesn't already accept.
This is deliberately a *page*-level cache window, independent of the *run*-level cadence below —
even at a weekly run cadence, 24h just means "never accidentally double-fetch within the same
day," it isn't what makes the run weekly.

**Run cadence — `MIN_RUN_INTERVAL_DAYS=7`, enforced via `IngestionRun`, not left to the
scheduler.** Added 2026-09-16 (Business Logic rule 8). A source's adapter is skipped for a given
invocation of `ingest_scraped_sources.py` if `IngestionRun.last_run_at` for that source is less
than 7 days old — checked in code, before any request is made, regardless of how often the
script itself is invoked. This is *this* source's floor, not necessarily every future scraped
source's — a different source with a different granted permission could reasonably need a
different value; `MIN_RUN_INTERVAL_DAYS` is a per-adapter-overridable constant, defaulting to 7.

**Value-level dedupe on insert, not just id-level.** Added 2026-09-16 (Business Logic rule 9).
`market_observations`/`skill_associations` already dedupe by `id` (which embeds `period_start`,
so a shifting rolling window alone would produce a "new" id every run). That's not enough on its
own to satisfy "focus on new things, not old" — a genuinely unchanged observation would still
insert as a new row under a new id. `scraping_storage.py`'s insert functions additionally check
the most recently stored row for the same entity key and skip the insert if nothing comparable
changed, logging it as a no-op rather than a write.

**Licence registry — `source_licences.py`, a hard dependency, not an adapter-local constant.**
Added 2026-09-16 (Data Models — `SourceLicence`). Every adapter looks up its own `licence`/
`attribution_text` from this registry; there is no code path to construct a
`FetchedMarketObservation`/`FetchedSkillAssociation` with a licence string an adapter invented
locally. An unregistered source is a hard error at adapter-construction or first-use time — same
"refuse rather than proceed with a guess" discipline `SCRAPER_CONTACT`'s check already
established for identification, now applied to licensing too.

**Migration** — six tables via the existing `CREATE TABLE IF NOT EXISTS` schema-on-startup
pattern already used for every other table in `db.py`: `scrape_robots_cache`,
`scrape_page_cache`, `market_observations`, `skill_associations`, `scrape_ingestion_runs`, and
(added 2026-09-18) `scrape_extractions`. `extraction_model` is added to `market_observations`
and `skill_associations` via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, same pattern already
used elsewhere in `db.py` for a column added after a table's first creation.

**LLM extraction — reuse `classification.py`'s prompt/parse idiom, don't invent a new one.**
Added 2026-09-18. `SYSTEM_INSTRUCTION`/`_build_prompt`/`_parse_response` in `classification.py`
already establish this codebase's pattern for "ask Gemini for strict JSON, strip markdown
fences, `json.loads`, treat anything that fails validation as `None` rather than guessing" — the
new `scraping/itjobswatch.py` extraction step follows the same shape (its own system instruction
and prompt builder, scoped to this adapter's fields) rather than a different JSON-extraction
convention. No retry/backoff loop is added to match `classification.py`'s
`_complete_with_retry` — at 3 pages/week, a page that fails extraction this run is simply
skipped (rule 7, fault isolation) and picked up cleanly next week; the retry complexity
`classification.py` needs to protect a daily batch budget doesn't apply here.

**Known follow-up, not blocking this revision**: the 3 `market_observations` + 523
`skill_associations` rows the 2026-09-16 run inserted under the regex extraction are confirmed
wrong and must be deleted once this revision is implemented and verified, then the same 3 pages
re-ingested through the new path — see `changes/2026-09-18-itjobswatch-llm-extraction.md`,
Execution Plan Step 5. `IngestionRun.last_run_at`/`MIN_RUN_INTERVAL_DAYS` (rule 8) is keyed on
successful runs regardless of what got extracted, so re-ingesting immediately after a code fix
needs either waiting out the 7-day window or a deliberate one-time manual reset of that row —
call this out explicitly when actually running the cleanup, don't silently bypass the cadence
guard in code to do it.
