---
id: market-health
experience: market-health
directive: low
status: draft
created: 2026-06-13
updated: 2026-08-09
---

# Market Health — Backend Architecture Spec

## Experience this implements
See: `design/market-health/experience.md`

## Taxonomy this uses
See: `design/market-health/job-classification.md` — canonical `Role Category`, `Seniority`,
and `Track` enums. This spec references that taxonomy rather than redefining it.

---

## Data Models

**Sourcing update (2026-08-03):** Adzuna is no longer used — its license does not permit
continued use, not merely a cost concern (see `changes/2026-07-28-multi-source-job-data-ingestion.md`).
Postings are now ingested from three ATS (applicant tracking system) platforms whose job
boards are public per-company JSON APIs, no authentication required: **Greenhouse, Lever,
and Ashby**. `RawPosting` changes from an Adzuna-shaped model to a source-agnostic one behind
a `SourceAdapter` abstraction (see Tech Decisions), so a fourth source can be added later as
one new adapter without another data-model change. Existing Adzuna-sourced rows already in
`raw_postings` are historical data and are never deleted or rewritten — see the migration
note under RawPosting below for how they're reconciled with the new columns.

`MarketHealthSignal` and `SearchImplication` below remain mocked in-memory in v1 — they
back `/api/market-health/summary`, which is not used by the current experience spec and is
unchanged by this update. `RawPosting` and `Classification` are new: the first models in
this product backed by a real database (PostgreSQL, per the project's tech stack) rather
than in-memory mock data. They replace the previous `DemandSignal`, `CompensationSignal`,
and `LayoffSignal` mock models, which only ever backed `/api/market-health/trends` and are
superseded by real ingestion.

### MarketHealthSignal
| Field | Type | Description |
|---|---|---|
| `verdict` | `"Healthy" \| "Cautious" \| "Contracting"` | The aggregate market verdict |
| `explanation` | `str` | One-sentence plain-language explanation of the verdict |
| `trend_direction` | `"improving" \| "stable" \| "worsening"` | Direction of change over the selected period |
| `as_of` | `date` | The date the signal was last computed |
| `source` | `str` | Description of the data source (for Data Freshness label) |

### SearchImplication
| Field | Type | Description |
|---|---|---|
| `text` | `str` | Plain-language statement of what the current signal means for the user's job search |
| `signal_verdict` | `str` | The verdict this implication corresponds to |

### RawPosting (`raw_postings` table)
Immutable. The exact source response for a posting is the only chance to ever capture it — a
posting can be edited or unpublished by the company at any time and there is no way to recover
its prior state, so nothing here is ever mutated after insert.

| Field | Type | Description |
|---|---|---|
| `id` | `str` (PK) | The dedupe key — a posting is fetched and stored at most once, regardless of how many daily ingestion runs re-surface it while still live. `id` is derived as `f"{source}:{source_ref}"` — e.g. `"greenhouse:acme-corp/123456"` — so uniqueness never depends on a source's native id being globally unique by itself. **Adzuna-era rows (which used a bare, undelimited id) were fully removed 2026-08-05** (`changes/2026-08-05-adzuna-data-removal.md`, a license-driven data deletion, not a schema change) — every current row uses this `source:source_ref` shape. **Load-bearing invariant, verified 2026-08-05**: "only new postings are ever stored" is enforced at the database level via this `PRIMARY KEY`, not just application logic — `raw_postings.insert_new_postings()`'s `existing_ids()` pre-check is an efficiency optimization (skip work we already know is redundant), but the constraint itself is what actually guarantees no duplicate row can ever exist, even if that pre-check were ever bypassed by a future bug. Confirmed directly against production data: zero duplicate ids, and zero cases of the same posting's full content or description text appearing under two different ids (checked by hash comparison, not just by id or title). |
| `source` | `str` | Which adapter produced this row: `"greenhouse"`, `"lever"`, `"ashby"` (closed set, validated in application code the same way `role_category` is — see Business Logic). `"adzuna"` for legacy rows (backfilled, no longer a live source). |
| `source_ref` | `str` | The posting's identifier within its source, scoped to be unique on its own within that source — `f"{company}/{native_id}"` for all three ATS adapters, since none of the three platforms guarantees its native id is unique *across* companies on that platform (only within one company's board), only that it's unique *within* one company's board. `NULL` for legacy Adzuna rows (backfilled to equal `id`; see migration note). |
| `company` | `str \| None` | The company whose job board produced this row — the Greenhouse `board_token`, Lever `site`, or Ashby job-board name used to fetch it. `NULL` for legacy Adzuna rows, which were never fetched per-company (see `role_family_query` below). |
| `role_family_query` | `str \| None` | **Legacy, Adzuna-era only.** Which tracked search term produced this row (Adzuna was queried by role-family search term, not by company). Always `NULL` for rows from Greenhouse/Lever/Ashby — those adapters fetch a company's entire board and rely on classification's `role_category: "other"` escape hatch to filter relevance, not a source-side search query (see Business Logic — Ingestion). Column kept, not dropped or renamed, since existing rows' values are historical data. |
| `title` | `str` | Raw job title, verbatim from the source. |
| `raw_response` | `JSON` | The full source API response object for this posting, stored verbatim — Adzuna's shape for legacy rows, the originating ATS's own job-object shape for everything since. Never normalised or projected down; each source's shape is whatever that source actually returned. |
| `fetched_at` | `datetime` | When our ingestion pipeline captured this posting. The only date this product can trust for "when did this posting first appear to us" — none of Adzuna, Greenhouse, Lever, or Ashby's public APIs support querying by historical date range; all four are live-snapshot-only. |
| `created_at` | `datetime` | Row insert timestamp (server clock). |
| `country` | `str \| None` | Normalized country, derived at ingestion time from the source's own location fields (see Business Logic — Location normalization). `NULL` when the source's location data couldn't be normalized — never guessed. |
| `city` | `str \| None` | Normalized city, same derivation and same honesty rule as `country`. Coverage is lower than `country` — see Business Logic — Location normalization for per-source rates. |
| `salary_min` | `int \| None` | Lower bound of disclosed/parsed compensation, in `salary_currency` units per year. `NULL` when the posting discloses no usable compensation (see Business Logic — Compensation extraction). |
| `salary_max` | `int \| None` | Upper bound, same rule as `salary_min`. |
| `salary_currency` | `str \| None` | ISO currency code (e.g. `"USD"`), `NULL` iff `salary_min`/`salary_max` are `NULL`. |
| `salary_confidence` | `"structured" \| "parsed" \| None` | **Load-bearing for the Compensation Signal's honesty rule** (`design/market-health/experience.md`, User Flow 7a): `"structured"` = read directly from a source-provided structured field (Ashby); `"parsed"` = extracted via regex from free text (Lever); `NULL` = no compensation data captured for this posting (includes all Greenhouse postings — see Business Logic). A compensation answer must never present a `"parsed"` figure with the same certainty as a `"structured"` one, and must never blend the two into one undifferentiated number. |
| `salary_extraction_method` | `str \| None` | e.g. `"ashby-structured"`, `"lever-regex"` — provenance/debugging detail, distinct from `classifications.model` (which is about role/seniority/track, not compensation). `NULL` iff `salary_confidence` is `NULL`. |
| `industry` | `str \| None` | The tracked company's industry (e.g. `"Fintech"`, `"AI"`, `"Social Media"`) — a static, curated lookup keyed by `company`, **not** an LLM inference (see Business Logic — Industry tagging). `NULL` for any company not yet tagged in the lookup; never guessed. |

**Migration note (2026-08-03).** `source`, `source_ref`, and `company` are new columns added to
the already-live `raw_postings` table via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` (not just
`CREATE TABLE IF NOT EXISTS`, which only affects table creation, not an existing table — see
Tech Decisions). Existing rows are backfilled once: `source = 'adzuna'`, `source_ref = id`,
`company = NULL`. `role_family_query`'s `NOT NULL` constraint is relaxed (`ALTER COLUMN ... DROP
NOT NULL`) since it's populated only for legacy rows going forward. No existing row's `id`,
`title`, `raw_response`, or `fetched_at` is touched — the immutability rule above still holds;
only new descriptive columns are added and backfilled.

**Migration note (2026-08-04).** `country`, `city`, `salary_min`, `salary_max`,
`salary_currency`, `salary_confidence`, `salary_extraction_method` are new nullable columns,
same `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` pattern. No backfill against existing rows in
this change — location/compensation extraction runs going forward, at ingestion time, per
Business Logic below; existing rows simply keep these columns `NULL` until (if ever) a
backfill pass is deliberately scoped as its own change. Still consistent with the
immutability rule: these are derived-once, source-agnostic-shape columns filled in at the
same moment a row is first inserted, not a later mutation of an existing row's captured data.

**Migration note (2026-08-09).** `industry` is a new nullable column, same pattern. No
backfill — populated going forward at ingestion time from the static lookup (Business
Logic — Industry tagging); existing rows keep it `NULL` until re-fetched (they won't be,
since postings aren't re-fetched once stored — see the `id` dedupe invariant above) or a
backfill is deliberately scoped separately.

### Classification (`classifications` table)
Keyed to `raw_postings`, one row per posting. Kept separate from `RawPosting` so
classification logic can be revised and re-run against everything already captured,
without re-fetching anything.

| Field | Type | Description |
|---|---|---|
| `id` | `int` (PK) | |
| `posting_id` | `str` (FK → `raw_postings.id`) | **Load-bearing invariant, verified 2026-08-05**: "a posting is classified at most once, ever" is enforced at the database level via a `UNIQUE` constraint on this column, not just application logic — `get_all_unclassified()`'s `LEFT JOIN ... WHERE c.posting_id IS NULL` filter is an efficiency optimization (never send an already-classified title to the LLM again), but the constraint is what actually prevents a duplicate classification row even if that filter were ever bypassed. Confirmed directly against production data: zero postings with more than one classification row. |
| `role_category` | `"Designer" \| "Product Manager" \| "Engineer" \| "other"` | Closed set from `job-classification.md`. `"other"` is the escape hatch for postings that don't genuinely fit. |
| `sub_specialization` | `str \| None` | e.g. `"UX Designer"`, `"Backend Engineer"`. `None` when `role_category` is `"other"`. |
| `seniority` | `"entry" \| "junior" \| "mid" \| "senior" \| "lead" \| "principal" \| "manager" \| "director" \| "vp" \| "exec" \| None` | `None` when `role_category` is `"other"`. |
| `track` | `"ic" \| "management" \| None` | `None` when `role_category` is `"other"`. Always captured alongside seniority, never inferred from it. |
| `taxonomy_version` | `str` | The version of `job-classification.md` active when this row was produced. Never rewritten retroactively when the taxonomy changes. |
| `model` | `str` | Provider/model that produced this classification, e.g. `"gemini/gemini-2.5-flash"` — or `"heuristic-keyword-filter"` when the posting was resolved by the pre-classification denylist filter (see Business Logic — Classification) rather than an LLM call. Kept as a free-text field specifically so provenance stays honest about which path produced a given `"other"`. |
| `classified_at` | `datetime` | |

### PostingRequirements (`posting_requirements` table) — added 2026-08-09
One row per posting, 1:1 with `raw_postings` — the singular (non-repeating) fields of
Requirements Signal (`design/information-architecture.md` Content Taxonomy;
`design/market-health/job-classification.md` — Requirements Taxonomy). Repeating fields
(skills, languages) live in their own tables below, not as arrays here, so they can be
aggregated with a plain `GROUP BY` rather than JSONB array manipulation.

| Field | Type | Description |
|---|---|---|
| `posting_id` | `str` (PK, FK → `raw_postings.id`) | One row per posting — a `PRIMARY KEY` here (not just `UNIQUE`, since there's no separate surrogate id needed) enforces "extracted at most once per posting" at the database level, same discipline as `classifications.posting_id`. |
| `education_level` | `"not_mentioned" \| "bootcamp_or_equivalent" \| "bachelors" \| "masters" \| "phd"` | Closed set from `job-classification.md` — Education level. `"not_mentioned"` is the default and is explicitly **not** evidence that no degree is required (see that section's honesty rule). |
| `responsibilities_summary` | `str \| None` | 2-4 sentence LLM-generated summary of the posting's core responsibilities. Deliberately not a closed taxonomy (`job-classification.md` — Responsibilities) — day-to-day duties are too varied to force into a fixed set. `NULL` only if extraction hasn't reached this posting yet. |
| `other_requirements` | `str \| None` | The freeform catch-all (`job-classification.md` — Other requirements) — captures both untracked skill mentions and any other notable requirement (certification, clearance, portfolio) that doesn't fit a standard field. Never forced into a standard field just to avoid using this one. |
| `model` | `str` | Provider/model that produced this extraction, same free-text provenance pattern as `classifications.model`. |
| `extracted_at` | `datetime` | |

### PostingSkill (`posting_skills` table) — added 2026-08-09
One row per posting **per tracked skill mention** — many rows per posting, zero rows if
none of that posting's Role Category's tracked skills were mentioned at all. Only ever
holds a closed-set `skill` value (`job-classification.md` — Skills) — an untracked mention
goes into `posting_requirements.other_requirements` instead, never forced in here.

| Field | Type | Description |
|---|---|---|
| `id` | `int` (PK) | |
| `posting_id` | `str` (FK → `raw_postings.id`) | |
| `skill` | `str` | One of the closed values for that posting's `role_category` (`job-classification.md` — Skills table). Validated against that closed set the same way `role_category` itself is. |
| `requirement_level` | `"must_have" \| "nice_to_have"` | |

`UNIQUE (posting_id, skill)` — the same tracked skill is never recorded twice for one
posting, even if mentioned in multiple places in the description.

### PostingLanguage (`posting_languages` table) — added 2026-08-09
One row per posting per language requirement mentioned — many rows per posting, zero if
none mentioned (the common case — most postings never state a spoken-language requirement).

| Field | Type | Description |
|---|---|---|
| `id` | `int` (PK) | |
| `posting_id` | `str` (FK → `raw_postings.id`) | |
| `language` | `str` | Free text (e.g. `"English"`, `"German"`) — `job-classification.md` explicitly notes no closed list is needed here, unlike skills, since language names are already a stable, unambiguous set. |
| `requirement_level` | `"required" \| "preferred"` | |

`UNIQUE (posting_id, language)`.

### IngestionRun (`ingestion_runs` table)
One row per execution of the scheduled ingestion agent (see Business Logic — Scheduled
ingestion agent). Makes a run's outcome inspectable after the fact instead of existing only
as ephemeral console output — today, a crashed run leaves no record at all beyond whatever a
human happened to be watching in a terminal.

| Field | Type | Description |
|---|---|---|
| `id` | `int` (PK) | |
| `started_at` | `datetime` | |
| `completed_at` | `datetime \| None` | `None` if the run crashed before finishing |
| `status` | `"success" \| "partial" \| "failed"` | **Redefined 2026-08-04.** `"success"` = completed with no errors — this now includes deliberately reaching the per-run classification budget (`budget_reached`, below); hitting a self-imposed cap on purpose is the run working as designed, not a degraded outcome. `"partial"` = completed but degraded by an actual error — one or more companies failed after exhausting retries (see Business Logic — Ingestion), or a classification batch failed after exhausting retries on a genuine, non-budget error (see Business Logic — Classification — Retry policy); whatever succeeded is still persisted. `"failed"` is reserved for a run that produced nothing usable at all (e.g. the database itself was unreachable) — a single bad company or classification batch is a `"partial"` run, not a `"failed"` one. |
| `terms_processed` | `JSON` | **Column name kept for migration simplicity; semantics generalised 2026-08-03.** `[{ "source": str, "company": str, "fetched": int, "inserted": int, "error": str \| None }, ...]` — one entry per (source, company) pair attempted, e.g. `{"source": "greenhouse", "company": "acme-corp", "fetched": 12, "inserted": 3, "error": null}`. `error` is set when that company's fetch failed after exhausting retries; `fetched`/`inserted` are `0` for it, and the run continues to the next company rather than aborting. Legacy rows (pre-2026-08-03) hold the old `{"term": str, ...}` shape — readers must handle both shapes when reading historical `ingestion_runs` rows. |
| `total_fetched` | `int` | |
| `total_inserted` | `int` | New `raw_postings` rows this run |
| `total_classified` | `int` | Postings classified this run (cache hits + heuristic-filtered + fresh LLM calls) |
| `cache_hits` | `int` | Titles resolved from the title cache — zero LLM calls |
| `heuristic_filtered` | `int` | **Added 2026-08-04.** Titles resolved straight to `other` by the pre-classification denylist filter — zero LLM calls (see Business Logic — Classification — Pre-classification filter) |
| `llm_classified` | `int` | Titles that required a fresh LLM call — excludes both cache hits and heuristic-filtered titles |
| `budget_reached` | `bool` | **Added 2026-08-04.** `true` if this run stopped because `MAX_BATCHES_PER_RUN` was reached with no errors (see Business Logic — Classification — Per-run classification budget), not because the backlog was exhausted. Distinguishes "still more backlog waiting for tomorrow" from "fully caught up today" without needing to infer it from counts. |
| `llm_requests_used` | `int` | **Added 2026-08-05.** The actual count of LLM requests made this run, including retries — deliberately distinct from `llm_classified`, which counts successfully-classified unique titles, not requests. A batch that needed 3 retries before succeeding consumes 3 requests against the real daily quota but produces only 1 batch's worth of classifications; `llm_classified` alone would undercount real usage. This is the field the cross-run daily budget (see Business Logic — Classification — Per-run classification budget) is actually computed from. |
| `other_count` | `int` | |
| `other_rate` | `float` | `other_count / total_classified` for this run, `0.0` if nothing was classified |
| `requirements_extracted` | `int` | **Added 2026-08-09.** Postings that got a `posting_requirements` row this run (see Business Logic — Requirements extraction). A separate phase from classification, so this is 0 on runs that only classified without reaching the requirements phase. |
| `requirements_requests_used` | `int` | **Added 2026-08-09.** Same discipline as `llm_requests_used`, tracked separately since requirements extraction uses its own dedicated key/budget (see Business Logic — Requirements extraction) — conflating the two would make either budget impossible to reason about independently. |
| `requirements_budget_reached` | `bool` | **Added 2026-08-09.** Same meaning as `budget_reached`, scoped to the requirements extraction phase's own daily budget. |
| `anomalies` | `JSON` | List of flagged issue strings (see Business Logic — Anomaly flagging); empty list if none |
| `error_message` | `str \| None` | Set only when `status` is `"failed"` |

---

## API Endpoints

### GET /api/market-health/summary

**Purpose**: Returns the current Market Health Signal and Search Implication, filtered by role and location if provided.

**Auth required**: no (v1)

**Query params**:
| Param | Type | Default |
|---|---|---|
| `role` | `str` | `"all"` |
| `seniority` | `str` | `"all"` |
| `location` | `str` | `"all"` |

**Response**:
```json
{
  "signal": {
    "verdict": "Cautious",
    "explanation": "Demand is stable but layoff activity has increased in large tech companies.",
    "trendDirection": "worsening",
    "asOf": "2026-06-01",
    "source": "Aggregated from job board postings and public layoff announcements"
  },
  "implication": {
    "text": "The market is soft but not closed. Targeting smaller companies and contract roles will increase your hit rate."
  }
}
```

**Errors**:
| Code | Reason |
|---|---|
| 400 | Invalid filter values |
| 503 | Data source unavailable (not applicable in v1 — mocked data always available) |

---

### GET /api/market-health/openings

**Purpose**: Returns monthly job-opening counts per Role Category (Designer, Product Manager,
Engineer) for the trend chart, plus a written trend summary, sourced from live-ingested,
LLM-classified postings.

> **Note**: this is the endpoint the shipped frontend actually calls. This spec previously
> described a `GET /api/market-health/trends` endpoint with a `series`/`roleCategory` shape —
> that endpoint was never implemented; the real frontend (`frontend/src/pages/MarketHealthPage.tsx`)
> was built independently against `/openings` with the wide row shape below, and neither spec
> was updated to match at the time. This spec is corrected here to document what's real. See
> the change request decision log (`changes/2026-07-16-adzuna-live-data-and-classification-taxonomy.md`)
> for how this was discovered and resolved.

**Auth required**: no (v1)

**Query params**:
| Param | Type | Default |
|---|---|---|
| `range` | `"this_year" \| "past_5_years" \| "all_time"` | `"this_year"` |

**Response**:
```json
{
  "range": "this_year",
  "data": [
    { "month": "2026-01", "designer": 34, "product_manager": 21, "engineer": 89 },
    { "month": "2026-02", "designer": 41, "product_manager": 19, "engineer": 96 }
  ],
  "summary": "Over this period, Designer openings are up 21%, Product Manager openings have stayed roughly flat, and Engineer openings are down 8%. Counts reflect postings first observed by live daily ingestion, not a backfilled historical series.",
  "as_of": "2026-07-19",
  "source": "Company job boards hosted on Greenhouse, Lever, and Ashby — live postings, LLM-classified"
}
```

`source` is a fixed descriptive string naming every adapter currently live, not a per-row
breakdown — matching this endpoint's existing behaviour of blending all sources into one
series. A user who wants to know which specific source contributed to a number uses the chat
endpoint's per-turn provenance (Business Logic — Conversational data sourcing), not this field.

One row per calendar month that has at least one non-`"other"` classified posting.
`range=all_time` returns every month since ingestion started — there is no earlier data,
since Adzuna's API cannot answer "what was live in the past" (see Business Logic below).

**Errors**:
| Code | Reason |
|---|---|
| 400 | Invalid `range` value |
| 503 | Database unavailable |

---

### GET /api/alerts/exceptions

**Purpose**: Returns unresolved Exceptions for the current user. Used to show the returning-user banner.

**Auth required**: no (v1 — returns empty array)

**Response**:
```json
{
  "exceptions": []
}
```

---

### POST /api/chat

**Purpose**: Accepts the user's conversation history and streams a Gemini response. Unlike
before, the model is not handed one fixed pre-computed data blob — it can query the platform's
real dataset directly for the specific question asked, and fall back to real, cited external
sources for anything the dataset doesn't cover. See Business Logic — Conversational data
sourcing. Wire format and streaming contract are unchanged — see
`backend/specs/ai-reasoning-panel/api.md` for the full stream event sequence
(`reasoning_trace` → tokens → `finish_message`). This spec changes what feeds that trace, not
its shape.

**Auth required**: no (v1)

**Request**:
```json
{
  "messages": [
    { "role": "user", "content": "Is now a good time to look for a senior UX role in London?" }
  ],
  "context": {
    "role": "UX Design",
    "seniority": "Senior",
    "location": "London"
  }
}
```

**Response**: Server-Sent Events stream (text/event-stream). Each event is a token chunk in Vercel AI SDK wire format.

**Errors**:
| Code | Reason |
|---|---|
| 400 | Malformed messages array |
| 502 | Gemini API unreachable |

---

## Business Logic

**Ingestion (daily) — multi-adapter, since 2026-08-03.** Three `SourceAdapter`s run each day —
Greenhouse, Lever, Ashby (see Tech Decisions for the adapter abstraction). Each adapter holds
its own curated list of company board tokens/site slugs/job-board names (the same curation
pattern as the retired `ROLE_SEARCH_TERMS`: a deliberately curated, periodically-reviewed list,
not an attempt at exhaustive coverage of every company on that platform — see Tech Decisions for
how that list is validated before being added). For each company in an adapter's list, fetch
that company's *entire* published job board — none of the three platforms' public APIs support
server-side filtering to "just tech roles" in a way that's consistent across all three (Ashby's
public endpoint supports no filtering at all; Greenhouse and Lever's filtering options don't map
onto this product's Role Category taxonomy) — and let classification's existing `role_category:
"other"` escape hatch do the relevance filtering downstream, the same mechanism already trusted
for Adzuna postings that didn't fit the taxonomy. This is a deliberate change from Adzuna's
search-term-based fetching (which pre-filtered by phrase before any posting reached
`raw_postings`) to fetch-everything-then-classify — expect a materially higher `other` rate
in the weeks after this ships, as a real, expected transition effect, not a pipeline defect (see
Anomaly flagging below, which needs a fresh baseline once the source mix changes).

**Fault isolation, per company, and per adapter.** Two nested levels, both non-aborting:
- **Per company** (within one adapter): a single company's board fetch failing — board token
  renamed or removed, network error, rate limited after exhausting retries — is recorded with
  its error in `terms_processed` (see Data Models — IngestionRun) and skipped; the adapter moves
  on to the next company. Mirrors the per-search-term isolation the 2026-07-27 Adzuna resilience
  change already established — same principle, applied one level differently (company instead of
  search term).
- **Per adapter** (within the whole run): an adapter-level failure outside any single company's
  fetch (e.g. an unexpected bug in that adapter's response parsing) is caught at the
  orchestration level and recorded, not allowed to abort the other two adapters — a bug in the
  Ashby adapter must never stop Greenhouse and Lever from running that day.

A company/adapter returning zero results is not a failure and is recorded exactly like any
successful one (`fetched: 0`, `error: null`) — a small company having no open roles on a given
day is expected, not exceptional.

**Pacing and retry policy — self-imposed, not source-mandated.** None of Greenhouse, Lever, or
Ashby documents a hard rate limit for their public GET job-board endpoints (confirmed against
each platform's own current API docs 2026-08-03 — Lever documents a rate limit only for its POST
application-submission endpoint, 2 requests/second, which this product never calls). The absence
of a documented limit is not treated as license to fetch unpaced: every adapter still applies a
conservative, fixed minimum interval between its own requests (company-to-company, and
pagination within a company where the platform paginates), and retries with exponential backoff
only on retryable failures — HTTP 429 and 5xx, plus connection errors/timeouts — never on a
non-429 4xx, which can't succeed on retry. This reuses the exact pattern (not the exact numbers)
already proven for Adzuna in the 2026-07-27 resilience change: pacing constant and retry count
are implementation details tuned per adapter, not spec'd exactly here, matching how Adzuna's
were left as code-level constants rather than spec'd numbers.

**Location normalization (at ingestion time, no LLM).** `country`/`city` (Data Models —
RawPosting) are derived synchronously while a posting is fetched and inserted — not a
separate pass, since nothing here needs an LLM or has an external rate limit. Each adapter
maps its own source's location shape:
- **Lever**: `country` comes directly from the source's own `country` field, already a clean
  ISO code — used as-is. `city` is a best-effort split of the `categories.location` free-text
  string (e.g. `"New York, NY"`); left `NULL` if it doesn't parse cleanly as `"City, ST"`.
- **Ashby**: `country` comes from `address.postalAddress.addressCountry`, populated for the
  large majority of postings but inconsistently formatted (e.g. `"United States"` and
  `"USA"` both appear for the same country) — passed through a small static normalization
  map, not an LLM. `city` comes from `address.postalAddress.addressLocality` when non-empty;
  left `NULL` otherwise (a meaningful minority of postings leave this blank).
- **Greenhouse**: weakest of the three. `offices[0].location` is a parseable `"City, State,
  Country"` string when present, but is absent for a large share of postings — when present,
  best-effort parsed; when absent, both fields are left `NULL` rather than attempting to
  parse the separate, messier `location.name` field, which frequently combines remote-status
  and multiple cities in one string (e.g. `"San Francisco, CA • New York, NY • United
  States"`) — genuinely ambiguous multi-location text, out of scope for this pass.

A posting whose location can't be normalized keeps `country`/`city` as `NULL` and is simply
excluded from location-specific answers (`design/market-health/experience.md` — Edge Cases)
rather than guessed.

**Compensation extraction (at ingestion time) — three sources, three different confidence
levels, one deliberately excluded.** `salary_min`/`salary_max`/`salary_currency`/
`salary_confidence`/`salary_extraction_method` (Data Models — RawPosting) exist specifically
so a `"parsed"` estimate is never presented with the same certainty as a `"structured"`
figure (`design/market-health/experience.md`, User Flow 7a). Confirmed by querying the real
production database directly before writing this, not assumed:
- **Ashby — `salary_confidence: "structured"`.** Read directly from
  `raw_response.compensation.summaryComponents`, filtered to entries where
  `compensationType == "Salary"`, taking `minValue`/`maxValue`/`currencyCode`. Zero
  extraction risk — this is a source-provided structured field, not inferred. If
  `compensation` is absent or `shouldDisplayCompensationOnJobPostings` is false, the posting
  simply has no compensation data — not an error.
- **Lever — `salary_confidence: "parsed"`.** A majority of postings mention salary as free
  text inside `additionalPlain` (plain text, not the HTML `additional` field), in fairly
  consistent phrasing (e.g. "the estimated salary range for this position is estimated to be
  $93,000 - $160,000/year"). Extracted via regex for a `$X - $Y` pattern. If regex finds no
  confident match, the posting is treated as having no disclosed salary — **no LLM fallback**
  (see below for why).
- **Greenhouse — excluded from compensation extraction entirely, `salary_confidence: NULL`
  for every Greenhouse posting.** A majority of postings mention salary/compensation, but
  only inside one large unstructured HTML `content` blob mixed with the entire job
  description — nothing as cleanly patterned as Lever's phrasing, so reliable extraction
  would require an LLM call per posting, not per unique title. This is a deliberate scope
  boundary, not an oversight: an LLM fallback here (or for Lever's regex misses) would mean a
  **per-posting** LLM call — a fundamentally different, larger cost shape than classification's
  per-*title* LLM calls, and would reopen the exact daily-quota problem the 2026-08-04
  classification-budget change was built to solve, at a larger scale (thousands of
  Greenhouse postings vs. a few thousand unique *titles*). If this coverage gap ever becomes
  a real product priority, it deserves its own explicitly-budgeted change — not a quiet
  LLM call added here. **Note (2026-08-09): this is the exact same class of concern that
  Requirements extraction (below) revisits and finds now-viable** — the difference is real
  production volume turned out to be much smaller than assumed when this exclusion was
  written, not a change in the underlying cost logic.

**Industry tagging (at ingestion time, no LLM) — added 2026-08-09.** `industry` (Data
Models — RawPosting) is a static, curated lookup keyed by `company` — e.g.
`{"stripe": "Fintech", "openai": "AI", "reddit": "Social Media", ...}` — maintained with the
same discipline as each adapter's curated `COMPANIES` list (reviewed periodically, not
exhaustive, a company simply has `industry: NULL` until someone tags it). Deliberately not
LLM-inferred: with only 35 tracked companies, a one-time manual tag is both cheaper and more
reliable than asking a model to guess an industry from a company name. This directly
supports Requirements Signal-adjacent questions like "which industries are hiring the most
designers" without needing any new LLM cost.

**Classification (daily, after ingestion)**
Classification runs once per ingestion run, across every newly-inserted posting from every
adapter and company together — not once per company, and not scoped by source — so the
title-based cache below sees the widest possible pool for catching duplicate titles before any
LLM call is made. Postings are
classified in batched LLM calls (not per-posting, to control cost), constrained to the closed
`Role Category`, `Seniority`, and `Track` sets defined in `design/market-health/job-classification.md`;
the response is parsed and validated against those sets in application code (see `Tech
Decisions` — `LLMProvider` has no native schema-constrained output today, so validation is
the caller's job, not the provider's). A posting whose returned value doesn't validate, or
that doesn't genuinely fit any Role Category, is classified `role_category: "other"` and
logged for human review, per the `other` escape hatch defined in that spec, rather than
forced into the nearest match. Every classification row is stamped with the
`taxonomy_version` active in `job-classification.md` at classification time; if the taxonomy
is later revised, existing rows keep their original version rather than being silently
relabeled.

**Retry policy — transient provider errors, not just rate limits.** Each classification
batch call retries with backoff (up to 5 attempts, 60s between attempts) on any retryable
failure — HTTP 429/quota-exhausted **and** HTTP 5xx / transient provider unavailability
(e.g. a `503 UNAVAILABLE "model currently experiencing high demand"` response), plus
connection errors/timeouts. This mirrors the pattern already established for the
source-fetch step above (Business Logic — Ingestion — Pacing and retry policy): a
provider being briefly overloaded is not the same failure as quota exhaustion, and both
are equally worth retrying past before giving up on a batch. Only after retries are
exhausted does the run stop early and record `status: "partial"` (see Data Models —
IngestionRun) — whatever was classified before the failing batch is already persisted and
is not re-sent on the next run, since the title cache below only skips titles that were
actually written.

**Title-based classification cache** — classification is a pure function of the posting's
title (the prompt sends nothing else). Before any LLM call, unclassified postings are deduped
by exact title in two layers: (1) a title already classified in a prior run is reused
straight from the `classifications` table, no LLM call; (2) among never-before-seen titles,
duplicates within the same run are classified once and fanned out to every posting sharing
that title. This is the main lever for staying under the LLM provider's request quota as the
dataset grows — job titles repeat heavily across postings, companies, and days — and it
doubles as a consistency improvement, since it removes run-to-run model variance for the
same exact title.

**The real constraint — 20 requests/day, confirmed 2026-08-04.** Gemini's free tier for
`gemini-2.5-flash` is capped at exactly 20 requests/day/project/model (Google's own error
payload: `quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier, quotaValue: '20'`) —
not a per-minute limit, which earlier code comments assumed. At `BATCH_SIZE = 100`
titles/batch, that ceiling caps daily classification throughput at roughly 2,000 unique
titles. Real multi-source ingestion runs surface 3,000-4,700+ unique titles/day — demand
structurally exceeds throughput, not just occasionally but every day, since Greenhouse/
Lever/Ashby return each company's entire job board with no server-side tech-role filter (a
large share of any given board is sales, legal, finance, HR, and ops postings). The three
mechanisms below exist to make that gap survivable without the run always simply losing the
race against the quota.

**Pre-classification filter (denylist, not allowlist).** Before any title reaches the
LLM-batching step (i.e. before it's even counted against the title cache above's
"never-before-seen" pool for LLM purposes), it's checked against a curated denylist of
unambiguous non-tech keywords (e.g. "account executive," "payroll," "legal counsel,"
"recruiter," "warehouse associate" — full list is an implementation detail, see Tech
Decisions). A match is classified `role_category: "other"` immediately, no model call spent,
stamped with `model: "heuristic-keyword-filter"` (Data Models — Classification) so it stays
distinguishable from an LLM-produced `"other"`. Deliberately a denylist rather than an
allowlist: an allowlist (only send recognized tech keywords to the LLM) would silently
starve exactly the unusual-but-real titles `job-classification.md`'s "Raw Title" section
exists to catch (e.g. "Founding Engineer," "AI Product Manager") — a denylist only ever
skips titles that are unambiguous regardless of phrasing, so novel tech titles still reach
the LLM. This is a cost optimization, not a taxonomy change (see
`design/market-health/job-classification.md` — Classification Method): the end result for a
denylisted title is the same `"other"` an LLM call would have produced anyway.

**Backlog processing order — oldest-first.** `raw_postings.get_all_unclassified()` returns
unclassified postings ordered by `fetched_at` ascending. Under a bounded daily budget (below),
order of processing directly determines what actually gets classified promptly versus what
waits — without an explicit order, this was previously arbitrary (whatever Postgres's default
scan happened to produce). Oldest-first was chosen over newest-first despite newest-first
giving fresher data sooner, because the outcome this pipeline serves
(`understand-market-health-before-searching`) depends on reliable historical continuity
("how the hiring market numbers evolve through time") — newest-first would let the backlog
accumulated from any single large ingestion event get perpetually deprioritized behind each
day's new arrivals, leaving a permanent gap instead of one that closes over the following
days.

**Per-run classification budget — stopping on purpose is success, not degradation.** A
single run attempts at most `MAX_BATCHES_PER_RUN` batches, not "every unclassified title
that exists." Reaching that budget with zero errors sets `budget_reached: true` (Data
Models — IngestionRun) and `status: "success"` — the run did exactly what it was designed
to do. This is a deliberate redefinition: previously, running out of anything (backlog or
quota) short of "classified everything" had no vocabulary except the failure-flavored
`"partial"`. Under a real daily ceiling, "classified everything" is no longer an achievable
definition of success, so conflating a by-design stopping point with a degraded one would
make every future run look broken when it's actually working as intended. `status:
"partial"` remains reserved strictly for a batch that fails after exhausting retries on a
genuine, non-budget error (see Retry policy, above) — the distinction that matters
operationally is "we chose to stop" versus "something is actually wrong."

**Cross-run daily budget — corrected 2026-08-05, a real gap, not a hypothetical one.**
`MAX_BATCHES_PER_RUN` was originally sized "with headroom under the 20-request/day
ceiling" — true only if exactly one run happens per calendar day. It does not: manual "Run
now" testing repeatedly triggered multiple runs on the same day, and each run independently
got its own fresh batch allowance, meaning two runs in one day could together attempt
nearly double the real daily ceiling. This directly contradicted the budget's own stated
purpose and was narrowly avoided by luck during testing, not by design. Fixed via two
explicit, configurable constants (see Tech Decisions for exact values):
- `DAILY_REQUEST_BUDGET` — the confirmed Gemini free-tier ceiling (20). Raise this if the
  classification key's billing plan is ever upgraded.
- `RETRY_HEADROOM` — reserved across **all** of today's runs combined, not per run, for
  transient-error retries (Retry policy, above).

A given run's actual ceiling is now dynamic: `min(MAX_BATCHES_PER_RUN, DAILY_REQUEST_BUDGET
- RETRY_HEADROOM - already_used_today)`, where `already_used_today` is the sum of
`llm_requests_used` (Data Models — IngestionRun) across every run since the daily boundary.
UTC calendar day is used as that boundary — Gemini's exact quota reset time isn't
documented/confirmed, so this is a deliberately conservative proxy (a safety margin, not a
precision claim), consistent with this pipeline's existing bias toward under-using the
budget rather than assuming the most generous interpretation of an unconfirmed external
constraint. A second same-day run now correctly sees a reduced (or zero) remaining budget
rather than a fresh 12-batch allowance.

**Requirements extraction (daily, after classification) — added 2026-08-09, per-posting not
per-title.** Populates `PostingRequirements`/`PostingSkill`/`PostingLanguage` (Data Models)
per `design/market-health/job-classification.md`'s Requirements Taxonomy. Structurally
different from classification above: there is no title-cache shortcut, because two postings
sharing a title can have entirely different actual requirements — extraction reads a
posting's full *description*, not its title (`job-classification.md` — Requirements
Extraction Method). This is the exact class of per-posting cost concern that excluded
Greenhouse from Compensation extraction; it's revisited here because real production volume
has since been confirmed much smaller than assumed at that time (~43-115 new postings/day
steady-state, not thousands — see the Business Logic — Classification's cost analysis,
which was based on a one-time migration burst, not ongoing load).

- **Scope**: only postings with a real classification (`role_category != "other"`) and no
  existing `posting_requirements` row. No point extracting requirements for postings
  already known to be irrelevant, and — same invariant as classification — never
  re-extract a posting already processed (`posting_requirements.posting_id` is a
  `PRIMARY KEY`, DB-enforced, same discipline as `classifications.posting_id`).
- **Ordering**: oldest-first by `fetched_at`, same reasoning and same mechanism as
  classification's backlog processing order.
- **Dedicated key**: a separate credential (e.g. `GEMINI_API_KEY_REQUIREMENTS`), same
  "dedicated key per concern" discipline as classification's own key versus `/api/chat`'s.
  Honesty caveat, same one already on record for the classification key: this only grants a
  truly independent quota if it's a different Google Cloud project than the other keys —
  unconfirmed either way. If it turns out to share a project, real recent usage
  (classification now uses only ~1 request/day at steady state, backlog long cleared)
  suggests there's likely ample shared headroom regardless.
- **Own daily budget, same pattern as classification** — its own
  `REQUIREMENTS_DAILY_REQUEST_BUDGET`/`REQUIREMENTS_RETRY_HEADROOM` constants, its own
  cross-run tracking via `IngestionRun.requirements_requests_used` (Data Models), its own
  `requirements_budget_reached` flag. Reaching this budget is success, not degradation —
  identical reasoning to classification's redefinition, above. Kept as a **separate** budget
  from classification's, not a shared pool, so a heavy classification day and a heavy
  requirements-extraction day can't silently starve each other — same principle that
  justified separating `/api/chat`'s key from classification's in the first place.
- **Batching**: multiple postings' full descriptions per call, not one-per-call, same
  cost-control principle as classification — but a materially smaller batch size than
  classification's 100-titles/batch, since each item now needs a full description as input
  and a richer structured output (skills, education, language, a responsibilities summary,
  and the catch-all) rather than four short classification fields. Exact batch size is an
  implementation constant, not spec'd here — same "tuned as real data comes in" precedent
  already used for `BATCH_SIZE` and the denylist keyword list.
- **One call produces all of it.** A single extraction call for a posting yields its
  `PostingRequirements` row (education level, responsibilities summary, catch-all) and its
  `PostingSkill`/`PostingLanguage` rows together — not separate calls per field. Skill and
  language values are validated against `job-classification.md`'s closed sets the same way
  `role_category` is; anything that doesn't validate is folded into
  `other_requirements` rather than discarded or forced into the nearest match.

**Trend aggregation**
`GET /api/market-health/openings` counts distinct `raw_postings` — joined to their
`classifications` row, excluding `role_category: "other"` — grouped by `role_category` and
the calendar month of `fetched_at`, then pivots into one row per month with a column per
Role Category. This counts postings newly observed by the ingestion pipeline in that month,
not "total open positions" at any point in time: an inherent limit shared by all three source
platforms' public APIs (none support a historical date-range query — each only ever returns
what's currently live — confirmed empirically for Adzuna and, separately, for Greenhouse,
Lever, and Ashby). Because ingestion runs daily with dedupe-by-id, each posting is counted
exactly once, in the month it was first captured.

**Written summary generation**
The `summary` string is generated deterministically (percentage change from the first to
last month in the requested range, per Role Category), not by an LLM call — matching the
pattern already used by this endpoint before this change (no `/api/chat` call was ever wired
into the opening summary). Extending it to an LLM-generated summary is out of scope here.

**Market Health Signal verdict (v1 mock rule)**
The verdict is pre-set in the mock data. When a real data source is connected, the rule is:
- `Healthy`: demand trend is rising AND layoff activity is low
- `Cautious`: demand is stable OR layoff activity is moderate
- `Contracting`: demand is declining OR layoff activity is high

**Search Implication generation**
In v1, implications are static strings keyed to verdict + filter combination, stored in the mock data layer. When real data is connected, implications may be generated by Claude with the signal as input.

**Conversational data sourcing (replaces the old fixed-context-injection design)**
Per `design/market-health/experience.md`'s sourcing rule: analyse the platform's own data for
the specific question asked, state the data's time window, and never fabricate an external
claim. The old design — pre-fetch a fixed summary/trends blob and prepend it as static context
— could only ever answer questions that blob happened to cover, and had no way to distinguish
"our data" from "the model's memory," which is how the fabricated "LinkedIn job postings"
citation bug happened. The new design gives the model two tools and a fixed decision order:

1. **`query_market_data` tool (always tried first).** A read-only, parameterised query
   interface over `raw_postings` joined to `classifications` — not raw SQL execution, which
   would be unsafe to expose to a model. **Note (2026-08-04): sub-specialization, seniority,
   and track drill-down — the "Demand Signal, enriched" part of
   `design/market-health/experience.md` — already work through this exact tool, unchanged.
   No backend change was needed for those three dimensions; only `country` (below) is new.**
   Parameters:
   - `group_by`: one or more of `role_category`, `sub_specialization`, `seniority`, `track`,
     `country` (new 2026-08-04), `month`
   - `role_category`, `sub_specialization`, `seniority`, `track`: optional filters, each
     restricted to the closed sets in `design/market-health/job-classification.md`
   - `country` (new 2026-08-04): optional filter — a non-empty string, parameterised the same
     safe way as the closed-set filters, but validated only as "non-empty" rather than against
     a fixed set, since normalized country values aren't a small enum the way role/seniority
     are (Business Logic — Location normalization)
   - `date_from`, `date_to`: optional ISO dates
   Always excludes `role_category: "other"` rows, matching the trend-aggregation rule. Rows
   with `country IS NULL` are excluded whenever `country` is used as a filter or `group_by`
   dimension — never guessed in to pad a count.
   Returns:
   ```json
   {
     "rows": [{ "role_category": "Designer", "sub_specialization": "Product Designer", "count": 33 }],
     "data_range": { "earliest": "2026-07-20", "latest": "2026-07-22" },
     "total_matching": 297
   }
   ```
   `data_range` is always included, even on a zero-row result — this is how the model knows
   whether a question falls outside the data's actual window (e.g. `date_to` before
   `data_range.earliest` means "we don't have that," not "the answer is zero").

1a. **`query_compensation_data` tool (added 2026-08-04, tried alongside `query_market_data`,
   same stage).** A second read-only, parameterised tool, added because compensation
   questions need a different aggregation shape than demand questions — `AVG`/`MIN`/`MAX`
   over a numeric range plus a disclosed-vs-estimated breakdown, not a `GROUP BY` count.
   Accepts the same filter dimensions as `query_market_data` (`role_category`,
   `sub_specialization`, `seniority`, `track`, `country` — see Location normalization,
   above, for how `country` is derived) so a compensation question can be scoped exactly
   like a demand question. Returns:
   ```json
   {
     "structured_count": 14,
     "parsed_count": 6,
     "salary_min": 130000,
     "salary_max": 165000,
     "currency": "USD",
     "data_range": { "earliest": "2026-07-20", "latest": "2026-08-04" },
     "total_matching": 41
   }
   ```
   `salary_min`/`salary_max` are computed **only from `salary_confidence: "structured"` rows**
   — `structured_count`/`parsed_count` are surfaced separately precisely so the model can lead
   with the reliable figure and mention (never blend in) the parsed count, per
   `design/market-health/experience.md`'s confidence rule. If `structured_count` is 0 but
   `parsed_count` > 0, the range is computed from the parsed rows instead, and the model must
   label it as an estimate — never presented as if structured. If both are 0, the range
   fields are `null` and the model states plainly that no postings in that slice disclose
   compensation (Edge Cases — no fallback guess from seniority/role alone).

1b. **`query_requirements_data` tool (added 2026-08-09, tried alongside the other two, same
   stage).** A third read-only, parameterised tool for skills/education/language questions —
   yet another different aggregation shape (frequency counts per closed taxonomy value, not
   a numeric range or a role/seniority `GROUP BY`). Accepts the same filter dimensions as the
   other two tools. Returns:
   ```json
   {
     "skills": [
       { "skill": "Front-end coding (HTML/CSS/JS)", "must_have_count": 3, "nice_to_have_count": 7 },
       { "skill": "Design systems", "must_have_count": 19, "nice_to_have_count": 4 }
     ],
     "education_levels": { "not_mentioned": 29, "bachelors": 8, "masters": 1 },
     "languages": [{ "language": "English", "required_count": 2, "preferred_count": 0 }],
     "data_range": { "earliest": "2026-07-20", "latest": "2026-08-09" },
     "total_matching": 38
   }
   ```
   `total_matching` is the count of postings in the matched slice that actually have a
   `PostingRequirements` row — i.e. the real denominator for any percentage the model states
   (e.g. "27% of postings" must be computed against this number, not against
   `query_market_data`'s broader count, which includes postings requirements extraction
   hasn't reached yet). This is also the field a synthesis question's "sample too small"
   check (`design/market-health/experience.md` — Edge Cases) is computed from.

2. **Google Search grounding (tried only when steps 1/1a/1b can't answer the question).**
   Triggered when none of the data tools return anything usable for a request that should be
   inside their domain but isn't inside the data's time window, or when the question is
   categorically outside what the dataset could ever contain (general career advice, market
   history before this pipeline existed, industry context). Implemented as a **separate,
   second model call** with Google Search grounding enabled, not combined with the data tools
   in the same call — current Gemini API versions don't support mixing custom function-calling
   tools with the search-grounding tool in one request (reverify at implementation time; API
   capabilities change). The grounded response's citation metadata (search queries used,
   source titles/URLs) becomes the trace's external sources — never a source that wasn't
   actually returned by the grounded call.

3. **Never silently substitute one for the other.** If steps 1/1a/1b find a partial answer
   and step 2 is needed to fill a gap, the response says which parts came from which. If
   nothing can answer the question, the model says so rather than guessing — this is a
   prompt-level instruction, and was confirmed insufficient on its own through testing (see
   the anti-fabrication guard below); a code-level check backs it up.
   **Synthesis questions (added 2026-08-09) get an additional rule**: when the data supports
   a judgment, not just a lookup (`design/market-health/experience.md` — User Flow 7b), the
   final answer must present the data and the judgment as two clearly separated parts, never
   blended into one statement — and must decline to judge (data only) if `total_matching`
   from `query_requirements_data` is too small to support a confident conclusion (exact
   threshold is an implementation/prompt-tuning detail, not spec'd as a precise number here).

**Bounded conversation history, not the full transcript.** Each stage gets only as much
recent conversation as it actually needs, not everything since the conversation began — see
`backend/AI_INTERACTION_SETTINGS.md` for the full reasoning (cost grows with conversation
length on a stateless API; the fix is sliding windows, sized differently per stage) and
`backend/src/ai_interaction_settings.py` for the current window sizes. This was also a real
correctness bug, not just a cost concern, confirmed through testing: without any history, a
short follow-up like "yes please" is meaningless to the data-query stage, and rather than
admitting that, the model fabricated a plausible-sounding category breakdown using category
names that don't exist anywhere in `job-classification.md` — worse than the original
fabricated-source bug, because it fabricated the data itself, then invented a justification
when the user questioned it. Giving the tool stages a small bounded window of recent messages
(not the full history a longer conversation would otherwise need) fixed this directly.

**Anti-fabrication guard — a code-level check, not just a prompt instruction.** If the
data-query stage makes zero calls to *any* of the three data tools (`query_market_data`,
`query_compensation_data`, `query_requirements_data`) AND doesn't emit the `NEEDS_EXTERNAL`
marker, its text is
discarded outright before it can reach the synthesis stage — confirmed by testing that a
confused model will sometimes answer with fabricated content instead of abstaining,
regardless of what the system prompt says. The synthesis stage is also grounded directly in
the raw tool-call return values (not just the data-query stage's prose summary of them), so a
hallucinated narrative can't reach the user even if it somehow slipped
past the first guard.

**Reasoning trace now reflects real tool calls, not pre-computed context.**
`backend/specs/ai-reasoning-panel/api.md` currently states trace assembly is "synchronous and
pre-LLM... input context and sources are known before the LLM call." That premise no longer
holds for `/api/chat`: `sources_and_tools` must now be built from whichever data tool(s) were
actually called (`query_market_data`; `query_compensation_data`, added 2026-08-04;
`query_requirements_data`, added 2026-08-09 — any combination)
and any Google Search grounding call actually made during generation, in real order, not
assembled beforehand. The trace-building code must not hardcode a single tool name/purpose
string the way it could when only one data tool existed — it now needs to reflect whichever
tool(s) the model actually invoked. This spec's behavior is authoritative for `/api/chat`; the
other spec is not updated here since reconciling it fully is out of this change's scope
(flagged in `design/market-health/experience.md`'s Open Questions).

**Insufficient data handling**
If filters produce an empty dataset, the summary endpoint returns `verdict: null` and an explanation stating that no data is available for that combination. The frontend must handle a null verdict without crashing.

**Scheduled ingestion agent**
Ingestion and classification (Business Logic, above) move from manually-triggered-locally to a
daily scheduled process, decoupled from `/api/chat`'s live traffic — not just in code (already
true — `ingest.py` has never been called from any request path) but in deployment and in quota.

- **Dedicated classification API key.** `classification.py`'s Gemini calls use
  `GEMINI_API_KEY_CLASSIFICATION` (a separate key from `/api/chat`'s `GEMINI_API_KEY`), so a
  heavy classification day never competes with live chat sessions for the same quota, and vice
  versa. Requires the provider abstraction to accept an explicit API key per call (see Tech
  Decisions), defaulting to `GEMINI_API_KEY` when not given so `/api/chat` and the reasoning
  trace feature are unaffected.
- **Every run records an `IngestionRun` row, including degraded ones.** The run's top level is
  wrapped so that whatever totals were accumulated are always written, never lost to an
  unhandled crash. **Redefined 2026-08-04**: a run that completes with every company (across
  all three adapters) succeeding, and classification either clearing the entire backlog or
  deliberately stopping at `MAX_BATCHES_PER_RUN` with zero errors (`budget_reached: true` —
  see Business Logic — Classification — Per-run classification budget), writes
  `status: "success"`. Reaching the budget on purpose is not degradation — under the
  confirmed 20-request/day quota, "classified everything" is no longer an achievable bar for
  success, so a clean, by-design stop must not read the same as a failure. A run where one or
  more companies failed after exhausting retries (see Business Logic — Ingestion — Fault
  isolation), or a classification batch failed after exhausting retries on a genuine,
  non-budget error (see Business Logic — Classification — Retry policy), writes
  `status: "partial"` — whatever was fetched, inserted, or classified before the degradation is
  still persisted and still counts. `status: "failed"` is reserved for a run that couldn't
  produce anything usable at all (e.g. the database itself is unreachable at startup, or every
  adapter failed) — deliberately rare now that per-company and per-adapter failures degrade to
  `"partial"` instead of aborting the whole run.
- **Anomaly flagging** (appended to the run's `anomalies` list, does not block the run):
  - **Zero-result company**: a company in any adapter's curated list returns 0 postings this
    run, and returned more than 0 in at least one of the last 5 recorded runs. (Not flagged
    before there's at least one prior run to compare against — a company legitimately having no
    open roles occasionally is normal, a company whose board integration has clearly broken is
    not.) Generalises the same rule previously scoped to `ROLE_SEARCH_TERMS` entries.
  - **Abnormal `other` rate**: this run's `other_rate` deviates from the trailing average of
    the last 5 completed runs' `other_rate` by more than 50% relative or 15 percentage points
    absolute, whichever is more lenient. No flagging until at least 5 completed runs exist to
    establish a baseline. **Note**: this baseline resets in effect once the source mix changes
    (2026-08-03) — the first ~5 runs on the new fetch-everything-then-classify pattern will read
    as "no baseline yet," and a materially higher `other_rate` than the old Adzuna-era baseline
    is expected during that window, not a signal something's broken (see Business Logic —
    Ingestion).
  - Anomalies are recorded, not acted on automatically — no run is blocked or retried because
    of a flag. They exist to be inspectable, per Principle 3 (Exceptions Define the
    Experience) — surfaced, not silently absorbed.
- **Explicitly out of scope**: analysing `other`-classified raw titles to propose new companies
  to track, or taxonomy changes. Valuable, deferred until there's enough real `IngestionRun`
  history to build sensible thresholds against — see this change's decision log. If ever built,
  it must propose changes for human review, never edit `job-classification.md` or an adapter's
  company list directly.

---

## External Dependencies

| Dependency | Purpose |
|---|---|
| Google Generative AI Python SDK (`google-genai`) | Streaming Gemini responses for `/api/chat`; `query_market_data` tool-calling; posting classification |
| Google Search grounding (via `google-genai`) | Real, citable external sources for `/api/chat` questions outside the platform's own data |
| Greenhouse Job Board API (`boards-api.greenhouse.io/v1/boards/{board_token}/jobs`) | Source of live job postings for `raw_postings` (`source: "greenhouse"`). Public, unauthenticated GET, no credentials. No documented rate limit for this endpoint (confirmed against Greenhouse's own API docs, 2026-08-03) — paced conservatively regardless (Business Logic — Ingestion). |
| Lever Postings API (`api.lever.co/v0/postings/{site}`) | Source of live job postings for `raw_postings` (`source: "lever"`). Public, unauthenticated GET, no credentials. Documents a rate limit only for its POST application-submission endpoint (2 req/sec) — this product never calls that endpoint; the GET postings endpoint has no documented limit, paced conservatively regardless. |
| Ashby Job Board API (`api.ashbyhq.com/posting-api/job-board/{jobBoardName}`) | Source of live job postings for `raw_postings` (`source: "ashby"`). Public, unauthenticated GET, no credentials. No documented rate limit (confirmed against Ashby's own API docs, 2026-08-03); paced conservatively regardless. No filtering support at all on this endpoint — every company's full board is fetched. |
| ~~Adzuna Jobs API (UK)~~ | **Retired 2026-08-03** — license no longer permits use. No longer called; existing `raw_postings` rows sourced from it are kept as historical data (`source: "adzuna"`, backfilled). See `changes/2026-07-28-multi-source-job-data-ingestion.md`. |
| Railway (cron-scheduled service) | Runs the daily ingestion agent independently of local dev — see Tech Decisions |

PostgreSQL (already in the project's tech stack) backs `raw_postings`, `classifications`, and
now `ingestion_runs`. `MarketHealthSignal` / `SearchImplication` remain mocked in-memory; no
queues are introduced.

Two distinct Gemini API keys are now in use: `GEMINI_API_KEY` (`/api/chat`, reasoning trace)
and `GEMINI_API_KEY_CLASSIFICATION` (ingestion agent only) — see Business Logic — Scheduled
ingestion agent for why these are kept separate.

---

## Tech Decisions

- **FastAPI** with `StreamingResponse` for the `/api/chat` endpoint. Use `text/event-stream` content type to match Vercel AI SDK expectations on the frontend.
- `MarketHealthSignal` and `SearchImplication` remain in a single `backend/src/mock_data.py` module, unchanged by this update.
- Use Python dataclasses (not Pydantic for v1 simplicity, but Pydantic is fine if preferred). FastAPI will serialize them automatically.
- No auth middleware in v1. Add it as a separate layer when needed.
- **Ingestion + classification run as a daily cron-scheduled service on Railway**, in the same
  Railway project as the Postgres database. `python ingest.py` is the service's start command;
  Railway's native cron scheduling runs it to completion once a day, not as a long-running
  process. Environment variables on that service: `GEMINI_API_KEY_CLASSIFICATION` and
  `DATABASE_URL` — using Railway's **internal/private** network URL for Postgres, not the public
  proxy URL used for local dev, since the service is co-located with the database. **No
  `ADZUNA_APP_ID`/`ADZUNA_APP_KEY` needed going forward** — a real operational simplification,
  since all three replacement sources are public and unauthenticated; those two variables should
  be removed from the Railway service config and `backend/.env.example` as part of this change's
  implementation, not just left unused. Needs `railway.json` (or equivalent) updated if it
  referenced Adzuna credentials — a concrete deliverable of `/implement-backend`. The job runs
  every adapter's every company first, then runs classification once across everything newly
  ingested — not once per company — to maximize duplicate-title detection before spending any
  LLM call (see Business Logic — Classification).
- **The classification LLM call is the actual bottleneck, not fetching — confirmed 2026-08-04,
  superseding the free-tier assumption below.** The provider's free tier caps
  `gemini-2.5-flash` at exactly 20 requests/day/project/model (Google's own error payload:
  `quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier`) — a hard daily ceiling, not a
  per-minute limit as originally assumed here. At `BATCH_SIZE = 100`, that's ~2,000
  titles/day of throughput against a real 3,000-4,700+ titles/day of demand (Business Logic —
  Classification). **Decision: stay on the free tier and reduce call volume, rather than
  upgrade billing** — reverses this bullet's original stance ("upgrading is the fix, not more
  aggressive caching or narrower ingestion"). Three mechanisms now do that: a
  pre-classification denylist filter (skips obviously non-tech titles with zero LLM calls), a
  deliberate per-run batch budget (`MAX_BATCHES_PER_RUN`, stops on purpose instead of racing
  the quota to a `429`), and oldest-first backlog ordering (all three documented in Business
  Logic — Classification). Revisit the upgrade-billing option only if these three together
  still can't keep the backlog from permanently growing.
- **Denylist keywords and `MAX_BATCHES_PER_RUN` are implementation constants, not spec'd
  exactly here** — same precedent as the retry pacing/backoff numbers (Business Logic —
  Ingestion — Pacing and retry policy): the *policy* (denylist not allowlist; a fixed budget
  with headroom under the daily quota) is spec'd, the exact keyword list and batch count are
  code-level and expected to be tuned as real `other`-rate and quota-usage data comes in.
  `MAX_BATCHES_PER_RUN` should leave enough headroom under 20 requests/day to absorb this-run
  retries on transient errors (Business Logic — Classification — Retry policy) without itself
  causing a `429` — sizing it at the full 20 would leave zero margin for a single retry.
- **`DAILY_REQUEST_BUDGET = 20` and `RETRY_HEADROOM = 8` (added 2026-08-05)** — named,
  configurable constants backing the cross-run daily budget (Business Logic —
  Classification — Cross-run daily budget). Named explicitly (not left as inline numbers)
  specifically so raising the quota later — e.g. upgrading the classification key's billing
  plan — is a one-line change, not a re-derivation. `RETRY_HEADROOM = 8` mirrors
  `MAX_BATCHES_PER_RUN = 12`'s existing 20/12/8 split (12 usable, 8 reserved) — same ratio,
  now applied across a day's runs instead of assumed for a single one.
- **Requirements extraction gets its own dedicated key, budget constants, and batch size —
  added 2026-08-09, not spec'd exactly here.** `GEMINI_API_KEY_REQUIREMENTS` (or equivalent),
  `REQUIREMENTS_DAILY_REQUEST_BUDGET`/`REQUIREMENTS_RETRY_HEADROOM`, and the requirements
  batch size are all implementation constants, same "policy is spec'd, exact numbers are
  tuned as real data comes in" precedent as classification's constants above. Kept
  deliberately separate from classification's constants (Business Logic — Requirements
  extraction) rather than reused, so the two extraction types can't silently starve each
  other's budget.
- **Industry lookup is a static Python dict, not a database table** — 35 entries, reviewed
  the same way the curated `COMPANIES` lists are, not a new schema concept. Simplicity is
  deliberate: a real company→industry mapping table would be over-engineering for 35
  hand-maintained values, and would blur the line this change explicitly draws around not
  building company-level infrastructure speculatively (Decision Log,
  `changes/2026-08-09-skills-and-industry-signal.md`).
- `raw_postings.raw_response` is stored as a JSON/JSONB column — store each source's response
  verbatim, do not project it down to the fields we currently use, since it is the only
  chance to ever capture a given posting.
- **Schema migration is `ALTER TABLE`, not just `CREATE TABLE IF NOT EXISTS`.** `db.py`'s
  `init_schema()` today only creates tables that don't exist yet — it never alters a table that's
  already live. `raw_postings` already has real production rows, so the new `source`,
  `source_ref`, and `company` columns (Data Models — RawPosting) need explicit `ALTER TABLE
  raw_postings ADD COLUMN IF NOT EXISTS ...` statements plus the one-time backfill UPDATE and the
  `role_family_query` `DROP NOT NULL`, run as part of `init_schema()` (idempotent — safe to run
  on every startup, same as the existing `CREATE TABLE IF NOT EXISTS` calls) rather than a
  separate manual migration step.

**Source adapter abstraction**
Mirrors the `LLMProvider` pattern (below) for job-data sources instead of AI providers — the
same shape solving the same problem: no business logic anywhere (ingestion orchestration,
classification, trend aggregation) should need to know or care which source produced a given
row. Defined in `backend/src/sources/base.py`:

```python
@dataclass
class FetchedPosting:
    source_ref: str   # unique within this source, e.g. "acme-corp/123456"
    company: str       # the board token / site / job-board name fetched
    title: str
    raw_response: dict  # the source's own job-object shape, verbatim
    # Added 2026-08-04 — all optional, populated per-adapter on a best-effort
    # basis (Business Logic — Location normalization, Compensation extraction).
    # None means "couldn't be normalized," never a guess.
    country: str | None = None
    city: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    salary_confidence: str | None = None       # "structured" | "parsed" | None
    salary_extraction_method: str | None = None  # e.g. "ashby-structured", "lever-regex"

class SourceAdapter(Protocol):
    name: str  # "greenhouse" | "lever" | "ashby"
    def fetch(self) -> list[FetchedPosting]:
        """
        Fetch every company in this adapter's curated list. Never raises for a
        single company's failure — that's caught and recorded internally (Business
        Logic — Ingestion — Fault isolation, per company); only an adapter-level
        failure outside any single company's fetch propagates, for orchestration
        to catch at the per-adapter level.
        """
        ...
```

`backend/src/sources/greenhouse.py`, `lever.py`, and `ashby.py` each implement this protocol:
own curated company list (module-level constant, same review discipline as the retired
`ROLE_SEARCH_TERMS` — periodically reviewed, not exhaustive), own pacing/retry logic (reusing
the pattern, not the code, from `adzuna_client.py`'s `_pace()`/`_get_with_retry()` before its
removal), own mapping from that platform's job-object shape into `FetchedPosting`. Adding a
fourth source later means writing one new adapter file implementing this protocol — no change to
`ingest.py`'s orchestration, `raw_postings.py`, or classification.

`ingest.py`'s orchestration loops over a fixed list of adapter instances (`ALL_SOURCE_ADAPTERS`
in `backend/src/sources/__init__.py`, mirroring `llm/providers.py`'s factory-module pattern),
catches an adapter-level exception without aborting the others (Business Logic — Ingestion —
Fault isolation, per adapter), and passes each adapter's `FetchedPosting`s to
`raw_postings.insert_new_postings()`, updated to accept `source` and build `id =
f"{source}:{p.source_ref}"` before the existing dedupe-by-`id` insert logic.

**Company-list curation — verified, not invented.** Each adapter's initial company list is a
deliverable of `/implement-backend`, not fixed by this spec: candidate companies are validated
by actually confirming their board token/site/job-board name resolves (a live HTTP 200 from that
company's public job-board URL) before being added to the list — the same "confirm empirically,
don't assume" discipline this spec already applies to Adzuna's quota and these three platforms'
rate-limit documentation. A guessed-but-wrong board token fails loudly and immediately (a
same-day 404, not a silent gap), so this is a cheap check worth doing before shipping, not an
excuse to skip it.

**Not in this change.** Non-posting enrichment content (articles, market reports) — named as a
future source category in `outcomes/job-data-source-flexibility.md` — is not modeled here. This
change is scoped to job-posting sources only (Greenhouse, Lever, Ashby); enrichment content has
a genuinely different shape (not a job posting, shouldn't be forced through classification) and
is deferred to its own follow-on change once a concrete enrichment source is chosen, per the
outcome's scope boundary.

**Provider abstraction layer**
All AI calls go through a shared `LLMProvider` protocol defined in `backend/src/llm/base.py`.
The `/api/chat` handler does not import any provider SDK directly — it calls the provider
through the protocol and names the provider and model explicitly at the call site:

```python
response = await providers.gemini("gemini-2.5-flash").stream(messages, system)
```

Posting classification reuses the same abstraction and the same model via `complete()`
(the non-streaming call already defined on `LLMProvider`), not `stream()`:

```python
response_text = await providers.gemini("gemini-2.5-flash").complete(
    prompt=classification_batch_prompt, system=classification_system_instruction
)
```

The prompt instructs the model to return one JSON object per posting, constrained to the
closed `Role Category` / `Seniority` / `Track` sets in `job-classification.md`. The response
is parsed and validated against those sets in application code before insert; a posting whose
returned value doesn't validate is classified `"other"` rather than trusting an invalid value.
`LLMProvider` currently exposes only `stream()` and `complete()` — no schema-constrained
structured-output method — so validation is the caller's responsibility, not the provider's.

Each provider is implemented as a separate adapter in `backend/src/llm/{provider}.py`.
Adding a new provider means creating one new adapter file — no changes to endpoints or
business logic. The adapter is responsible for message format conversion, streaming, and
mapping provider-specific errors to the common error surface. See `backend/specs/ai-reasoning-panel/api.md`
for the same pattern applied to the reasoning trace feature.

**Two protocol extensions needed for this change** (both to `backend/src/llm/base.py` and the
Gemini adapter — implementation detail of the exact method signature is left to
`/implement-backend`, but the capability is not optional):

1. **Explicit API key per call.** `GeminiAdapter` currently reads `GEMINI_API_KEY` from the
   environment unconditionally. It needs an optional `api_key` parameter (falling back to
   `GEMINI_API_KEY` when not given), so `classification.py` can pass `GEMINI_API_KEY_CLASSIFICATION`
   explicitly while every existing caller (`chat.py`, the reasoning trace feature) is
   unaffected. Same pattern as naming provider and model explicitly at the call site — the
   credential is now also explicit when a caller needs a non-default one.
2. **Tool-enabled calls.** Nothing in `LLMProvider` today lets a caller pass function
   declarations (for `query_market_data`) or enable Google Search grounding. `/api/chat` needs
   both, as two distinct call modes (Business Logic — Conversational data sourcing): one call
   with the `query_market_data` function tool, a separate call with search grounding enabled —
   never both tools in the same call. This is new surface on the protocol, not a change to
   `stream()`/`complete()`'s existing behavior for callers that don't need it.
