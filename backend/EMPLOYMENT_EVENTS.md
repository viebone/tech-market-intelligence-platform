# Employment Events — Data Model & Storage

Plain-language explanation of how layoff/employment-event data is stored in this
product — for anyone (human or AI) working on this codebase who doesn't already
know why it's built the way it is. Full spec detail lives in
`backend/specs/market-health/api.md` (Data Models — `EmploymentEvent`, Business
Logic — Employment event ingestion) and `design/market-health/data-stories.md`
(Story 2); this doc is the map, not a duplicate of either.

Verified against the **real, live production schema** on 2026-09-11 (queried
directly, not assumed from the spec — see "How to verify this yourself," below).

---

## The core fact this all follows from

Employment events are **not job postings, and not related to job postings in
any way.** There is exactly one table, `employment_events`, and it has:

- no foreign key to `raw_postings`
- no join to `raw_postings` in any query, anywhere in the codebase
- no field that identifies a "tracked company" — a `matched_company` field
  existed for a few hours on 2026-09-11 and was deliberately deleted (see
  "History," below)

This is a deliberate, repeated, explicit product decision — layoffs/closures/
restructuring/bankruptcy/expansion/hiring-announcement data is independent
market intelligence, not an overlay on the 35 companies this product happens
to track job postings for. If you're adding a feature and find yourself
wanting to join `employment_events` to `raw_postings`, stop — that's almost
certainly the wrong design for this product.

---

## The table: `employment_events`

One row per reported event, one adapter per source. Schema (`backend/src/db.py`):

| Column | Type | Nullable | Meaning |
|---|---|---|---|
| `id` | `text` | **PK, not null** | `f"{source}:{source_ref}"` — the dedupe key. Never generated any other way. |
| `source` | `text` | not null | Which adapter produced this row — a closed set: `eurofound_erm`, `us_warn`, `companies_house_insolvency`, `sec_edgar_8k`. |
| `source_ref` | `text` | not null | The event's id *within* its source — a real native id when the source has one, otherwise a deterministic composite the adapter builds (never random, so re-fetching the same event always produces the same `id`). |
| `source_url` | `text` | nullable | Direct link back to the source record, when the source has a stable per-record URL. |
| `company_raw` | `text` | not null | The company name **exactly as the source reported it** — or, when a source genuinely has no name (only an id), the bare id, stored honestly rather than dressed up as a fabricated name. Never normalized, never matched against anything else in this product. |
| `sector` | `text` | nullable | The source's own reported sector, verbatim, when it has one. Not the platform's own industry taxonomy — different vocabulary, not reconciled. |
| `country` | `text` | nullable | Normalized via the same `normalize_country()` job postings use — one shared normalization path. |
| `region` | `text` | nullable | Sub-national detail when the source provides it (a US state code, so far). |
| `event_date` | `date` | not null | The date **the source itself** attaches to the event — never the date this platform happened to observe it (`ingested_at`, below, is that). |
| `event_type` | `text` | not null | Closed set: `layoff`, `closure`, `restructuring`, `bankruptcy`, `offshoring`, `expansion`, `hiring_announcement`. |
| `direction` | `text` | not null | `contraction` or `expansion` — **derived, never independently input.** Computed once from `event_type` at insert time (`direction_for()`, `employment_events/base.py`), so it can never disagree with `event_type`. |
| `jobs_affected` | `integer` | nullable | Headcount, when the source reports one. Never estimated when absent. |
| `confidence` | `text` | not null | `confirmed` (a statutory filing or official register) or `reported` (compiled by the registry from public announcements). Never blended or presented with the same certainty. |
| `source_type` | `text` | not null, default `'registry'` | Reserved for a future non-registry source shape; every source today is `registry`. |
| `superseded_by` | `text` | nullable, FK → `employment_events.id` | Set when a later ingestion pass finds the source corrected/retracted this record. The old row is **kept**, never edited — see Immutability, below. |
| `raw_response` | `jsonb` | not null | The source's own record, stored verbatim. Never projected down — it's the only chance to ever capture exactly what the source said. |
| `ingested_at` | `timestamptz` | not null | When *this platform's* ingestion captured the record. |
| `created_at` | `timestamptz` | not null, default `now()` | Row insert timestamp. |

**Constraints** (real, from `pg_constraint`): `PRIMARY KEY (id)`, a `NOT NULL`
on every required column above, and `FOREIGN KEY (superseded_by) REFERENCES
employment_events(id)` — the only foreign key this table has, and it points
to itself, not to any other table.

**Indexes**: `event_date`, `company_raw`, `source` — one per column this
product actually filters/groups by today (the Employment Risk story's
window, its company ranking, and the chat tool's `sources_checked`).

---

## Immutability

Same discipline as `raw_postings`: **a row is inserted once and never
mutated.** A registry's published record is the only chance to ever capture
it as reported at that moment — if the registry later corrects or retracts
it, that arrives as a *new* ingestion pass, and the old row stays exactly as
it was, with `superseded_by` pointing at the row that replaces it. Nothing in
this codebase ever runs an `UPDATE` against an existing `employment_events`
row's own fields.

This is also why the *display-time* fix for placeholder company names
(below) had to be a display-time fix, not a data rewrite — the two already-
inserted UK Companies House rows that predate that fix keep their original
`company_raw` value forever; a query-time check (`is_real_company_name()`)
is what keeps them from being shown as if they were real names, not a
correction to the stored row itself.

---

## Deduplication

`id = f"{source}:{source_ref}"` is a `PRIMARY KEY`, so uniqueness is enforced
by Postgres itself, not just application logic — `insert_new_events()`
(`employment_events_storage.py`) pre-checks against the DB as an efficiency
optimization, but the constraint is what actually guarantees no duplicate
row can exist even if that pre-check were ever bypassed.

One real wrinkle, found and fixed while verifying the UK Companies House
adapter: a **change-stream** source can hand back several updates to the
*same* underlying record in one fetch (e.g. a practitioner's address
changing on an insolvency case that's otherwise unchanged) — all mapping to
the same `id`. `insert_new_events()` now dedupes *within one fetch batch*
too, not only against what's already in the DB, so the "N new" figure every
adapter logs reflects real distinct new rows.

---

## What a source can and can't give you — real, current data

Not every source reports every field. This is the actual breakdown from
production right now (`GROUP BY source`), not a claim:

| Source | Events | Has `jobs_affected` | Has `sector` | Has `region` | Date range seen |
|---|---|---|---|---|---|
| `companies_house_insolvency` | 45 | 0 (never — this endpoint doesn't size headcount) | 0 (not in this stream's payload) | 0 (UK only, no sub-national field) | 2021-04-30 → 2026-09-03 |
| `us_warn` | 25 | 25 (always — a WARN notice states it) | 16 (sparsely populated by the source) | 25 (always — a US state code) | 2026-08-28 → 2026-09-02 |
| `sec_edgar_8k` | 9 | 0 (not in this index's metadata) | 0 (a SIC code is present in the raw payload but not honestly mappable to a sector name without a real ~1,000-entry lookup table, so it's left `NULL` rather than guessed) | 9 (a US state, from the filer's business address) | 2026-08-13 → 2026-09-10 |

Every row currently in the table is `direction: contraction` — 45
`bankruptcy`, 21 `layoff`, 9 `restructuring`, 4 `closure`. No `expansion` or
`hiring_announcement` events exist yet (none of the three live sources
report growth — Eurofound ERM, the only source that would, isn't live yet).

**A `NULL` in any of these columns is not a bug and not a gap to silently
fill** — it means that source genuinely doesn't report that fact for that
event. Every query and every display in this product treats an absent value
as more honest than a guessed one, the same rule this product already
applies to job-posting location/compensation/requirements.

---

## Per-source id shape

`source_ref` (and therefore `id`) looks different per source, because each
source gives us a different kind of identifier:

- **`us_warn`** — the source's own native id (e.g. `TN-2026-f990fc74`), or a
  composite of `state:company:notice_date` when one isn't available.
- **`companies_house_insolvency`** — `{company_number}:{case_number}`, built
  from the stream's own structured fields.
- **`sec_edgar_8k`** — the SEC's own accession number (`adsh`), one per
  filing (deduped across multiple exhibit files belonging to the same
  filing before it ever reaches storage).
- **`eurofound_erm`** — not live yet; will be the registry's own case
  reference once built.

---

## The cursor table: `employment_event_cursors`

```
source      TEXT PRIMARY KEY
cursor      TEXT
updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
```

A small, generic table any **streaming-style** source can use to resume from
its last position between scheduled runs — added for UK Companies House's
Streaming API (a live, unbounded feed; without a saved position, every run
would either replay from the very beginning or miss everything that arrived
since the last run went idle). A polling/full-refetch source (WARN Firehose,
SEC EDGAR) doesn't need this — those adapters just re-request a trailing
date window every run and rely on the `id`-based dedupe above to make the
overlap free.

Real current state: one row, `companies_house_insolvency` → a Companies
House `timepoint` integer (stored as text) — the position the stream had
reached at the end of the last successful run.

---

## Where the numbers actually live

This doc explains the *why*; the numbers themselves stay in code, so they
can't drift apart from what's actually running:

| What | Where |
|---|---|
| The schema itself (source of truth) | `backend/src/db.py` — `SCHEMA` |
| Field derivation logic (`direction_for`, `is_real_company_name`) | `backend/src/employment_events/base.py` |
| Insert/dedupe logic | `backend/src/employment_events_storage.py` |
| One adapter per source | `backend/src/employment_events/{name}.py` |
| Registered adapters | `backend/src/employment_events/__init__.py` — `ALL_EMPLOYMENT_EVENT_ADAPTERS` |
| How to add a new source | `employment_events/__init__.py`'s own module docstring — a 4-step recipe |
| Scheduled ingestion entry point | `backend/src/ingest_employment_events.py` |
| Every source's access method, auth, and live status | `DATA_SOURCES.md` §3a |
| The two consumers (story + chat tool) | `backend/src/market_stories.py` — `build_employment_risk_overview()`; `backend/src/market_query.py` — `query_employment_events_data()` |

---

## History — decisions that shaped this table, in order

Everything below is a real, dated decision, not a hypothetical design
discussion — each links to its full change record in `changes/`.

1. **2026-09-11 — `employment-event-ingestion`**: the table created, scoped
   to the platform's 35 tracked job-posting companies via a `matched_company`
   field, a chart overlay on the hiring trend chart.
2. **2026-09-11, same day — `employment-events-independent-scope`**: added a
   *second*, independent data story alongside the tracked-company chart
   overlay, once real data showed most events don't match any tracked
   company.
3. **2026-09-11, hours later — `employment-events-no-company-matching`**:
   the user directed, firmly and repeatedly, that employment events must be
   independent of tracked companies **everywhere**, not scoped anywhere.
   `matched_company` dropped from the schema (a real, non-additive
   migration against the live production table); the chart overlay deleted
   entirely, not just descoped. This is the decision that gives this table
   its current shape.
4. **2026-09-11, same day — `employment-risk-country-dimension`**: the
   "where it's happening" view changed from a state/country-mixed ranking to
   country-only, once a second country's data made the mixed ranking
   meaningless.
5. **2026-09-11, same day — `employment-risk-12-month-window`**: the
   Employment Risk story's window widened from 90 days to 12 months, once
   real Companies House data showed a source's own event date can lag well
   behind when it's actually observed on a live feed.
6. **2026-09-11, same day — `employment-risk-hide-placeholder-names`**: UK
   Companies House's Streaming API turned out to carry no company name, only
   a bare id — fixed at the source (store the bare id honestly, never a
   fabricated `"Company N"` string) and at display time
   (`is_real_company_name()` keeps a bare id from ever being shown as if it
   were a company).

---

## How to verify this yourself

Nothing above is a claim to trust blindly — run it:

```bash
cd backend/src
python -c "
from db import get_connection
with get_connection() as conn:
    for r in conn.execute('SELECT source, count(*) FROM employment_events GROUP BY source'):
        print(r)
"
```

or query `information_schema.columns` / `pg_constraint` / `pg_indexes` for
`employment_events` directly against `DATABASE_URL` — this doc was written
by doing exactly that against the real production database, not by copying
the spec.
