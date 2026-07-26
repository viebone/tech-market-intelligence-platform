---
id: market-health
experience: market-health
directive: low
status: draft
created: 2026-06-13
updated: 2026-07-25
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
| `status` | `"success" \| "partial" \| "failed"` | `"partial"` = completed but stopped early (e.g. hit an unresolvable rate limit) |
| `terms_processed` | `JSON` | `[{ "term": str, "fetched": int, "inserted": int }, ...]` — one entry per search term attempted |
| `total_fetched` | `int` | |
| `total_inserted` | `int` | New `raw_postings` rows this run |
| `total_classified` | `int` | Postings classified this run (cache hits + fresh LLM calls) |
| `cache_hits` | `int` | Titles resolved from the title cache — zero LLM calls |
| `llm_classified` | `int` | Titles that required a fresh LLM call |
| `other_count` | `int` | |
| `other_rate` | `float` | `other_count / total_classified` for this run, `0.0` if nothing was classified |
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

**Conversational data sourcing (replaces the old fixed-context-injection design)**
Per `design/market-health/experience.md`'s sourcing rule: analyse the platform's own data for
the specific question asked, state the data's time window, and never fabricate an external
claim. The old design — pre-fetch a fixed summary/trends blob and prepend it as static context
— could only ever answer questions that blob happened to cover, and had no way to distinguish
"our data" from "the model's memory," which is how the fabricated "LinkedIn job postings"
citation bug happened. The new design gives the model two tools and a fixed decision order:

1. **`query_market_data` tool (always tried first).** A read-only, parameterised query
   interface over `raw_postings` joined to `classifications` — not raw SQL execution, which
   would be unsafe to expose to a model. Parameters:
   - `group_by`: one or more of `role_category`, `sub_specialization`, `seniority`, `track`, `month`
   - `role_category`, `sub_specialization`, `seniority`, `track`: optional filters, each
     restricted to the closed sets in `design/market-health/job-classification.md`
   - `date_from`, `date_to`: optional ISO dates
   Always excludes `role_category: "other"` rows, matching the trend-aggregation rule.
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

2. **Google Search grounding (tried only when step 1 can't answer the question).** Triggered
   when `query_market_data` returns `total_matching: 0` for a request that should be inside its
   domain but isn't inside the data's time window, or when the question is categorically
   outside what the dataset could ever contain (general career advice, market history before
   this pipeline existed, industry context). Implemented as a **separate, second model call**
   with Google Search grounding enabled, not combined with `query_market_data` in the same
   call — current Gemini API versions don't support mixing a custom function-calling tool with
   the search-grounding tool in one request (reverify at implementation time; API capabilities
   change). The grounded response's citation metadata (search queries used, source
   titles/URLs) becomes the trace's external sources — never a source that wasn't actually
   returned by the grounded call.

3. **Never silently substitute one for the other.** If step 1 finds a partial answer and step
   2 is needed to fill a gap, the response says which parts came from which. If neither step
   can answer the question, the model says so rather than guessing — this is a prompt-level
   instruction, and was confirmed insufficient on its own through testing (see the
   anti-fabrication guard below); a code-level check backs it up.

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
data-query stage makes zero `query_market_data` calls AND doesn't emit the `NEEDS_EXTERNAL`
marker, its text is discarded outright before it can reach the synthesis stage — confirmed
by testing that a confused model will sometimes answer with fabricated content instead of
abstaining, regardless of what the system prompt says. The synthesis stage is also grounded
directly in the raw `query_market_data` return values (not just the data-query stage's prose
summary of them), so a hallucinated narrative can't reach the user even if it somehow slipped
past the first guard.

**Reasoning trace now reflects real tool calls, not pre-computed context.**
`backend/specs/ai-reasoning-panel/api.md` currently states trace assembly is "synchronous and
pre-LLM... input context and sources are known before the LLM call." That premise no longer
holds for `/api/chat`: `sources_and_tools` must now be built from the `query_market_data` calls
and any Google Search grounding call actually made during generation, in real order, not
assembled beforehand. This spec's behavior is authoritative for `/api/chat`; the other spec is
not updated here since reconciling it fully is out of this change's scope (flagged in
`design/market-health/experience.md`'s Open Questions).

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
- **Every run records an `IngestionRun` row, including failed ones.** Today, a crashed run
  produces nothing but console output — no record survives. The run's top level must be
  wrapped so that whatever totals were accumulated before a crash, plus the error, are still
  written as a `status: "failed"` row. A run that completes normally writes `status: "success"`;
  one that stops early after exhausting retries on a rate limit (rather than crashing outright)
  writes `status: "partial"` with whatever was actually classified.
- **Anomaly flagging** (appended to the run's `anomalies` list, does not block the run):
  - **Zero-result term**: a search term in `ingest.py`'s `ROLE_SEARCH_TERMS` returns 0 postings
    this run, and returned more than 0 in at least one of the last 5 recorded runs. (Not
    flagged before there's at least one prior run to compare against — a term legitimately
    returning 0 occasionally is normal, a term that's clearly stopped working is not.)
  - **Abnormal `other` rate**: this run's `other_rate` deviates from the trailing average of
    the last 5 completed runs' `other_rate` by more than 50% relative or 15 percentage points
    absolute, whichever is more lenient. No flagging until at least 5 completed runs exist to
    establish a baseline.
  - Anomalies are recorded, not acted on automatically — no run is blocked or retried because
    of a flag. They exist to be inspectable, per Principle 3 (Exceptions Define the
    Experience) — surfaced, not silently absorbed.
- **Explicitly out of scope**: analysing `other`-classified raw titles to propose new
  `ROLE_SEARCH_TERMS` entries or taxonomy changes. Valuable, deferred until there's enough real
  `IngestionRun` history to build sensible thresholds against — see this change's decision log.
  If ever built, it must propose changes for human review, never edit
  `job-classification.md` directly.

---

## External Dependencies

| Dependency | Purpose |
|---|---|
| Google Generative AI Python SDK (`google-genai`) | Streaming Gemini responses for `/api/chat`; `query_market_data` tool-calling; posting classification |
| Google Search grounding (via `google-genai`) | Real, citable external sources for `/api/chat` questions outside the platform's own data |
| Adzuna Jobs API (UK) | Source of live job postings for `raw_postings`. Credentials: `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` |
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
  process. Environment variables on that service: `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`,
  `GEMINI_API_KEY_CLASSIFICATION`, and `DATABASE_URL` — using Railway's **internal/private**
  network URL for Postgres, not the public proxy URL used for local dev, since the service is
  co-located with the database. Needs a `railway.json` (or equivalent) declaring the cron
  schedule and start command — a concrete deliverable of `/implement-backend`, not left
  open-ended. The job ingests every search term in `ROLE_SEARCH_TERMS` first, then runs
  classification once across everything newly ingested — not once per term — to maximize
  duplicate-title detection before spending any LLM call (see Business Logic — Classification).
- **The classification LLM call is the actual bottleneck, not Adzuna.** The provider's free
  tier caps `gemini-2.5-flash` at a low daily request count, lower in practice than documented.
  Now that classification uses its own dedicated key (Business Logic — Scheduled ingestion
  agent), it no longer competes with `/api/chat`'s live traffic for the same quota — but its
  own budget is still real. The title-based cache is the primary lever for staying under it as
  the dataset grows; if usage genuinely outgrows the free tier, upgrading that key's billing
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
