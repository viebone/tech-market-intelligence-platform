---
id: market-health
experience: market-health
directive: low
status: implemented
created: 2026-06-13
updated: 2026-07-19
---

# Market Health — Backend Architecture Spec

## Experience this implements
See: `design/market-health/experience.md`

## Taxonomy this uses
See: `design/market-health/job-classification.md` — canonical `Role Category`, `Seniority`,
and `Track` enums. This spec references that taxonomy rather than redefining it.

---

## Data Models

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
Immutable. The exact Adzuna response for a posting is the only chance to ever capture it —
expired listings disappear from Adzuna's index permanently, so nothing here is ever mutated
after insert.

| Field | Type | Description |
|---|---|---|
| `id` | `str` (PK) | Adzuna's own job id. The dedupe key — a posting is fetched and stored at most once, regardless of how many daily ingestion runs re-surface it while still live. |
| `role_family_query` | `str` | Which tracked search term produced this row (e.g. `"UX designer"`, `"product owner"`, `"backend engineer"` — the current full list is `ingest.py`'s `ROLE_SEARCH_TERMS`, reviewed periodically) — the specific query that surfaced it, not its eventual classification. |
| `title` | `str` | Raw job title, verbatim from Adzuna. |
| `raw_response` | `JSON` | The full Adzuna API response object for this posting, stored verbatim. |
| `fetched_at` | `datetime` | When our ingestion pipeline captured this posting. The only date this product can trust — Adzuna's `/search` endpoint has no reliable posting-date field and no historical date-range query. |
| `created_at` | `datetime` | Row insert timestamp (server clock). |

### Classification (`classifications` table)
Keyed to `raw_postings`, one row per posting. Kept separate from `RawPosting` so
classification logic can be revised and re-run against everything already captured,
without re-fetching anything.

| Field | Type | Description |
|---|---|---|
| `id` | `int` (PK) | |
| `posting_id` | `str` (FK → `raw_postings.id`) | |
| `role_category` | `"Designer" \| "Product Manager" \| "Engineer" \| "other"` | Closed set from `job-classification.md`. `"other"` is the escape hatch for postings that don't genuinely fit. |
| `sub_specialization` | `str \| None` | e.g. `"UX Designer"`, `"Backend Engineer"`. `None` when `role_category` is `"other"`. |
| `seniority` | `"entry" \| "junior" \| "mid" \| "senior" \| "lead" \| "principal" \| "manager" \| "director" \| "vp" \| "exec" \| None` | `None` when `role_category` is `"other"`. |
| `track` | `"ic" \| "management" \| None` | `None` when `role_category` is `"other"`. Always captured alongside seniority, never inferred from it. |
| `taxonomy_version` | `str` | The version of `job-classification.md` active when this row was produced. Never rewritten retroactively when the taxonomy changes. |
| `model` | `str` | Provider/model that produced this classification, e.g. `"gemini/gemini-2.5-flash"`. |
| `classified_at` | `datetime` | |

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
  "source": "Adzuna Jobs API (UK) — live postings, LLM-classified"
}
```

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

**Purpose**: Accepts the user's conversation history and streams a Claude response, with current market data injected as context.

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

**Ingestion (daily)**
For each curated, industry-standard job title tracked per Role Category — e.g. "UX designer",
"product owner", "backend engineer" (the current full list is `ingest.py`'s
`ROLE_SEARCH_TERMS`, one query per title) — query the Adzuna Jobs API:
`what_phrase=<term>&category=it-jobs&max_days_old=3`, paginating until exhausted.
`category=it-jobs` is the validated filter for all three role categories, but it is a coarse,
generic filter — Adzuna's own category taxonomy has no finer-grained bucket underneath it
(confirmed against Adzuna's `/categories` endpoint) — so precision comes entirely from the
search terms, not the category. Bare category-name terms (`"designer"`, `"engineer"`) were
tried first and rejected: too generic, pulling in a lot of irrelevant noise (e.g. "Cabling
Infrastructure Designer") that still costs a real classification call to reject as `"other"`.
`ROLE_SEARCH_TERMS` is deliberately curated, not exhaustive, and is expected to be reviewed
periodically — add a title once it recurs often enough in `raw_postings` to matter, retire
one that's gone stale. This is the same review process `job-classification.md` already
describes for Raw Title. `max_days_old=3` (not 1) is a deliberate rolling safety margin so a
late or missed daily run doesn't create a coverage gap; the 3-day overlap is safe because
postings are deduped by Adzuna's `id` before insert — an already-stored posting is skipped
entirely, never re-fetched or re-classified.

**Classification (daily, after ingestion)**
Classification runs once per ingestion run, across every newly-inserted posting from every
search term together — not once per search term — so the title-based cache below sees the
widest possible pool for catching duplicate titles before any LLM call is made. Postings are
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

**Title-based classification cache** — classification is a pure function of the posting's
title (the prompt sends nothing else). Before any LLM call, unclassified postings are deduped
by exact title in two layers: (1) a title already classified in a prior run is reused
straight from the `classifications` table, no LLM call; (2) among never-before-seen titles,
duplicates within the same run are classified once and fanned out to every posting sharing
that title. This is the main lever for staying under the LLM provider's request quota as the
dataset grows — job titles repeat heavily across postings, companies, and days — and it
doubles as a consistency improvement, since it removes run-to-run model variance for the
same exact title.

**Trend aggregation**
`GET /api/market-health/openings` counts distinct `raw_postings` — joined to their
`classifications` row, excluding `role_category: "other"` — grouped by `role_category` and
the calendar month of `fetched_at`, then pivots into one row per month with a column per
Role Category. This counts postings newly observed by the ingestion pipeline in that month,
not "total open positions" at any point in time: an inherent limit of Adzuna's live-only
search API (no historical date-range parameter, confirmed empirically). Because ingestion
runs daily with dedupe-by-id, each posting is counted exactly once, in the month it was
first captured.

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

**Conversational context injection**
Before calling the Gemini API, the server fetches the current summary and trends for the context filters and prepends them as a system instruction. The model is instructed to answer from this data and flag when a question cannot be answered from it.

**Insufficient data handling**
If filters produce an empty dataset, the summary endpoint returns `verdict: null` and an explanation stating that no data is available for that combination. The frontend must handle a null verdict without crashing.

---

## External Dependencies

| Dependency | Purpose |
|---|---|
| Google Generative AI Python SDK (`google-genai`) | Streaming Gemini responses for `/api/chat`; structured-output calls for posting classification |
| Adzuna Jobs API (UK) | Source of live job postings for `raw_postings`. Credentials: `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` (already in `backend/.env`, not yet used in code) |

PostgreSQL (already in the project's tech stack) backs `raw_postings` and `classifications` —
the first tables this product actually persists to. `MarketHealthSignal` / `SearchImplication`
remain mocked in-memory; no other queues or storage are introduced.

---

## Tech Decisions

- **FastAPI** with `StreamingResponse` for the `/api/chat` endpoint. Use `text/event-stream` content type to match Vercel AI SDK expectations on the frontend.
- `MarketHealthSignal` and `SearchImplication` remain in a single `backend/src/mock_data.py` module, unchanged by this update.
- Use Python dataclasses (not Pydantic for v1 simplicity, but Pydantic is fine if preferred). FastAPI will serialize them automatically.
- No auth middleware in v1. Add it as a separate layer when needed.
- **Ingestion + classification run as a daily scheduled job** (e.g. APScheduler or an external
  cron calling an internal endpoint — implementation detail, not prescribed further here).
  The job ingests every search term in `ROLE_SEARCH_TERMS` first, then runs classification
  once across everything newly ingested — not once per term — to maximize duplicate-title
  detection before spending any LLM call (see Business Logic — Classification).
- **The classification LLM call is the actual bottleneck, not Adzuna.** The provider's free
  tier caps `gemini-2.5-flash` at a low daily request count (confirmed in practice, not just
  documented) — shared with `/api/chat`'s live traffic, since both use the same model. The
  title-based cache (Business Logic) is the primary lever for staying under that budget as
  the dataset grows; if usage genuinely outgrows the free tier, upgrading the provider billing
  plan is the fix, not more aggressive caching or narrower ingestion.
- `raw_postings.raw_response` is stored as a JSON/JSONB column — store the Adzuna response
  verbatim, do not project it down to the fields we currently use, since it is the only
  chance to ever capture a given posting.

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
