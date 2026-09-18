---
id: itjobswatch-llm-extraction
date: 2026-09-18
trigger-type: user-feedback
change-type: api-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Replace IT Jobs Watch regex extraction with LLM-based extraction

## Signal
See: `research/2026-09-18-itjobswatch-llm-extraction.md`

## Outcome
See: `outcomes/job-data-source-flexibility.md` — this is a correctness fix inside an
already-delivered part of that outcome (the `scraped-data-sources` capability), not a new
capability. No success criteria change.

## Change Type
`api-change` — no endpoints exist yet for this data (deliberately, per the original spec), so
this is entirely Data Models + Business Logic + implementation inside `scraped-data-sources`.

## Triage Notes (Step 2)

Maps to the existing `job-data-source-flexibility` outcome and the `scraped-data-sources`
backend spec already delivered under it (2026-09-16). This is not a new area.

**AI-involvement check (Rule 9):** `design/foundations.md` (v1.3) has no literal "AI
Involvement" heading — it predates that field being added to the `new-design-foundations`
template. There is direct precedent already in this codebase for exactly this situation:
`classification.py` and `requirements.py` (the `job-sync` pipeline) both call the `llm/`
provider abstraction to turn messy real-world text into structured fields, and neither required
a dedicated experience spec — the call is internal, non-user-facing data processing, and is
documented via the relevant backend spec's Tech Decisions naming the provider/model explicitly.
This change is the same shape: extracting structured salary/demand/skill facts from scraped HTML
is invisible to any user (no query surface exists over this data yet — `mcp-access-review` on
the original spec recorded it as **deferred**, not exposed). Treating it as internal
data-processing, following the existing precedent, rather than requiring a new experience spec.
If/when this data is ever surfaced to a user or an external AI client, *that* step is the one
that needs an experience spec (and re-checks `design/foundations.md`'s Scope/Principle 9) — not
this one.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change (see AI-involvement note above) |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | none (deliberate, per original spec) | no-change |
| Frontend Spec | none | no-change |
| Backend Spec | `backend/specs/scraped-data-sources/api.md` | update |
| Frontend Implementation | `frontend/src/` | no-change |
| Backend Implementation | `backend/src/` | update |
| Plain-Language Overview | `OVERVIEW.md` | no-change — nothing a real user can see changes; the data still isn't surfaced anywhere |
| MCP Access Review | `ACCESS.md` + `backend/specs/mcp-access/api.md` | no-change — still deferred/not exposed, no new capability is being exposed by this change |
| Polite Scraping Review | `DATA_SOURCES.md` + `backend/specs/scraped-data-sources/api.md` | update — run `/polite-scraping-review` after the spec update, since this changes the new-only-fetching/dedupe layer for this source |

## Agreed Design (recorded here so `/new-backend-spec` has a fixed target, not a re-litigation)

**What's stored raw (unchanged):** `scrape_page_cache` keeps exactly what it does today — the
full fetched HTML body, `content_hash`, `etag`/`last_modified`, `fetched_at`. This is the
existing polite-scraping cache layer; nothing about fetching, robots.txt, or pacing changes.

**New: `scrape_extractions` table** (the cost-saving layer the user asked for — "so that we
don't go on every ingestion going through the same data once and again"):
- `url` (PK, references the page), `content_hash` (the hash of the raw HTML this extraction was
  run against), `extraction_json` (the LLM's structured output), `model` (e.g.
  `gemini-2.5-flash`), `extracted_at`.
- Before calling the LLM for any page, look up `scrape_extractions` by `url`; if a row exists
  and its `content_hash` matches the current page's `content_hash`, reuse the stored
  `extraction_json` and skip the LLM call entirely. Only an actually-changed page (new
  `content_hash` from a re-fetch) triggers a new extraction. This is the real dedupe mechanism —
  cheaper and simpler than the real async Gemini Batch API, and correctly sized: this source
  fetches 3 pages/week, so batching for throughput has no benefit; the saving that matters is
  never re-extracting a page whose content hasn't changed.

**What the LLM is asked to extract:** the BeautifulSoup-stripped plain text of the page (not
raw HTML — cheaper, and removes markup noise), asked to return the same structured shape the
adapter already produces today (`FetchedMarketObservation` / `FetchedSkillAssociation` fields:
rank, rank_yoy_change, vacancy_count, vacancy_share, salary percentiles p10/p25/median/p75/p90,
salary_yoy_change, salary_sample_size; and per-skill rank/job_count/percentage/name) — as
strict JSON, via the existing `llm/` provider abstraction, `providers.gemini("gemini-2.5-flash")`
(same model `classification.py` already uses for this kind of "extract structured facts from
messy real text" job — reusing it, not inventing a new consumer, given the tiny added volume:
3 pages/week).

**How it's stored:** the LLM's JSON output is parsed into the same `FetchedMarketObservation`/
`FetchedSkillAssociation` dataclasses the adapter already builds — downstream storage
(`scraping_storage.insert_market_observations`/`insert_skill_associations`, with their existing
id- and value-level dedupe) is unchanged. `scrape_extractions.extraction_json` is also kept
verbatim as the row's own provenance record — if an extraction ever looks wrong, this is what to
inspect first, without re-fetching the page.

**How it's used:** identically to today — ingested into `market_observations`/
`skill_associations`, no query surface yet (still deferred per the original spec's
`mcp-access-review`).

**Explicitly rejected:** the real async Gemini Batch API. Volume is 3 pages/week; batch APIs
exist to amortize overhead across many concurrent requests and typically add turnaround latency
(hours) in exchange for a lower per-call price — neither trade makes sense at this volume. The
`content_hash`-gated skip is the actual cost saving the user asked for.

**Cleanup required:** the 3 `market_observations` rows and 523 `skill_associations` rows
inserted by the real 2026-09-16 run contain confirmed-wrong values (see
`research/2026-09-18-itjobswatch-llm-extraction.md`) and must be deleted once the new extraction
path is built, then the affected pages re-ingested (their `scrape_page_cache` rows are already
fresh — cadence gate is keyed on last successful ingestion, verify this doesn't block a
re-ingestion of already-cached pages before relying on it).

## Execution Plan

- [x] Step 1: Signal captured — `research/2026-09-18-itjobswatch-llm-extraction.md`
- [x] Step 2: PM triage — mapped to `job-data-source-flexibility`, AI-involvement precedent recorded above
- [x] Step 3: `/new-backend-spec` — updated `backend/specs/scraped-data-sources/api.md` in place: replaced regex-based Business Logic with LLM extraction design, added `scrape_extractions`/`ExtractionCache` to Data Models, added `extraction_model` column to `market_observations`/`skill_associations`, named `gemini-2.5-flash` explicitly under Tech Decisions
- [x] Step 4: `/implement-backend` — built `scrape_extractions` table + `PostgresExtractionCacheStore` (`scraping_storage.py`), content-hash-gated extraction-skip logic (`scraping/itjobswatch.py::_extract_role_page`), the Gemini call (`_extract_via_llm`, `providers.gemini("gemini-2.5-flash")`), rewrote `scraping/itjobswatch.py`'s extraction end to end (regex → LLM), added `extraction_model` to both dataclasses/tables/inserts, updated `ingest_scraped_sources.py` to construct/pass the new store. Verified: 37/37 `backend/tests/test_scraping.py` + 4/4 `backend/tests/test_source_licences.py` pass; `admin_main.py`/`ingest_scraped_sources.py`/`scraping_storage.py`/`db.py` all import cleanly. **Not yet run against the real database or the real Gemini API** — same "verified by import, not yet run live" caveat every prior pass of this feature has carried honestly.
- [x] Step 5: Deleted the 3 `market_observations` + 523 `skill_associations` known-bad rows from production (confirmed by count before deleting) and reset `scrape_ingestion_runs` for `itjobswatch` so the cadence gate allowed an immediate re-run, per explicit user confirmation. Re-ran `ingest_scraped_sources.py` for real — 3 real, paced, robots.txt-respecting requests to itjobswatch.co.uk and 3 real Gemini extraction calls. Result: 3/3 new observations, 90/90 new skill associations (30 per role — matches the page's real "Top 30 Co-Occurring Skills" heading exactly, versus the old broken run's 523, which included false matches from page furniture). Salary percentiles now populated correctly (mojibake gone); a genuinely-absent value (UX Designer's `salary_p90`) came back `null` rather than guessed. `extraction_model = "gemini-2.5-flash"` recorded on every row; `scrape_extractions` now holds all 3 pages' cached extractions keyed by content hash, so the next weekly run skips the LLM for any unchanged page.
- [x] Step 6: `/polite-scraping-review` — re-checked all four constraints against the real current code: robots.txt/pacing and run cadence unchanged and still enforced; storage-level value dedupe unchanged; licence unchanged and still confirmed. The new `scrape_extractions` content-hash gate is an *additional*, independent dedupe layer on the extraction step itself, not a replacement for storage-level dedupe. `DATA_SOURCES.md` §3b updated accordingly.
- [x] Step 7: Extended `backend/tests/test_scraping.py` — 8 new tests covering `_parse_extraction_response`, `_validate_extraction` (currency/percent coercion, missing→None, bad-skill filtering), and `_extract_role_page`'s content-hash dedupe (LLM called on miss, skipped on matching hash, called again on a changed hash)

## Decision Log
- 2026-09-18: Chose LLM-based extraction over fixing the regex patterns — the real page
  structure keeps surprising (3-column historical table, mojibake currency symbol, reversed
  skill-list order); an LLM reading plain text is far less brittle than another round of regex
  guessing, and the user explicitly leaned this way for cost + accuracy.
- 2026-09-18: Rejected the real Gemini Batch API given 3 pages/week volume; the `content_hash`
  dedupe in `scrape_extractions` is the real cost-saving mechanism.
- 2026-09-18: Treated as internal data-processing (no experience spec) per the
  `classification.py`/`requirements.py` precedent, since `design/foundations.md` predates the
  "AI Involvement" field and no user/AI-facing surface exists over this data yet.
- 2026-09-18: User confirmed the estimated cost (a fraction of a cent for the one-time 3-page
  catch-up run, drawn from the existing prepaid classification/requirements Gemini project) and
  explicitly approved deleting the known-bad production rows and re-running ingestion. Executed
  and verified — see Step 5. Change request complete.
