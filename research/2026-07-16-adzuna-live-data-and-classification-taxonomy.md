source: internal
date: 2026-07-16

The market-health feature currently runs entirely on mocked data (backend/src/mock_data.py,
no database) — a known v1 limitation already flagged in backend/specs/market-health/api.md,
which anticipates a real data source eventually replacing it. The product owner wants to move
off mocks: start pulling live job-market data, begin accumulating the product's own historical
dataset going forward, and separately figure out how to source genuine historical data for the
pre-launch period.

Research and decisions from this session:

- Adzuna Jobs API (UK) was signed up for and validated live (ADZUNA_APP_ID/ADZUNA_APP_KEY now
  in backend/.env, not yet used in code). Query shape `what_phrase=<role>&category=it-jobs`
  returns clean, accurate results for UX, Product Manager, and Developer/Engineering searches
  (spot-checked by hand: 30/30 and 29/30 relevant). `category=creative-design-jobs`, an earlier
  guess for where UX postings live, was tested and rejected — it undercounts UX postings by
  roughly 85% and skews mean salary about 40% low versus `category=it-jobs`.
- Adzuna's /search endpoint only ever returns currently-live postings. There is no absolute
  date-range parameter — `date_from`, `date_to`, and `created_from` all return 400 Bad Request,
  confirmed empirically. The only time lever is `max_days_old`, a rolling cutoff from "now," not
  a fixed calendar window. Adzuna cannot answer "what was live on a past date." This reframes all
  three of the original asks (live data / our own history / historical data) as one ingestion
  pipeline (snapshot + store, starting now) plus a separate, harder backfill problem that Adzuna
  alone cannot solve.
- Proposed ingestion design: daily pull per tracked role family with a rolling `max_days_old`
  safety margin (2-3 days, not exactly 1, to tolerate a late or missed cron run) and dedupe
  against already-stored postings by Adzuna's job `id` before any LLM classification runs, so no
  posting is ever classified twice.
- Proposed storage split: an immutable `raw_postings` table (the exact Adzuna response plus our
  own `fetched_at` timestamp — the only chance to ever capture a given posting, since expired
  listings disappear from Adzuna's index permanently) kept separate from a `classifications`
  table keyed to it, so classification logic can be revised later and re-run against everything
  already captured without re-fetching anything.
- Proposed classification taxonomy applied to every posting, decided as a design artifact (not a
  backend implementation detail) since it's the vocabulary users will actually see:
  - `type` (role_family): closed enum — UX/Design, Product Management, Engineering (each with
    sub-specializations) — starting narrow, widened later only once real data justifies it.
  - `seniority`: ordered enum — entry, junior, mid, senior, lead, principal, manager, director,
    vp, exec.
  - `track`: ic | management — kept separate from seniority because "Lead" is genuinely
    ambiguous (IC tech lead vs. first-line manager depending on company) and conflating the two
    would corrupt any "how many roles are management" trend.
  - Raw job title kept verbatim as its own free-text trend dimension, to surface emerging titles
    (e.g. "AI Product Manager," "Founding Engineer") before they're common enough to deserve a
    slot in the closed enum.
  - Classification is LLM-driven (via the existing `backend/src/llm/` provider abstraction),
    constrained to structured/JSON-schema output so it cannot invent categories, with an `other`
    escape hatch logged for human review and a `taxonomy_version` field so the taxonomy can
    evolve without losing track of which version labeled which historical row. Classification is
    batched per day per role family (not per posting) to control LLM cost.
- The existing experience spec (design/market-health/experience.md) already fixes the trend
  chart's categories to "Designer, Product Manager, Engineer" and carries an open, unresolved PM
  question: "Should role categories be fixed or user-configurable in v1?" This change is
  positioned to resolve that open question by formalizing the taxonomy, and the experience
  spec's existing category naming needs to be reconciled against the new `type` enum.

Proposed canonical location for the taxonomy: a new companion doc,
`design/market-health/job-classification.md`, alongside `experience.md` — the single source of
truth that both the backend spec (classification business logic) and the frontend spec (any
filter/legend vocabulary) reference, rather than each independently redefining it.

Related: research/2026-07-01-gemini-integration.md (existing LLM provider abstraction this
change will reuse for classification calls)
