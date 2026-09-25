# Trusted External Statistics — Data Model, Standard & "Add a Source" Recipe

Plain-language map for anyone (human or AI) about to touch this category. Full detail lives in
`backend/specs/trusted-statistics/api.md`; the user-facing story is Story 5 in
`design/market-health/data-stories.md`; licences are in `LICENSING.md`; where each source sits
among all the others is `DATA_SOURCES.md` §2 / §3c. This file is the map, not a duplicate.

**Status (2026-09-25): backend built and verified live** against the production database and ONS's own figures (25 series, 7,575
figures, Sep 2026 release). Still to do: the Story 5 frontend, and a scheduled Railway service (`DEPLOYMENT.md`). Deviations from the
spec and the real-data findings are in `backend/specs/trusted-statistics/api.md` — "Implementation notes".

---

## The core fact this all follows from

This category holds **published statistics from trusted institutions** — a fourth shape of data,
alongside job postings (`raw_postings`), employment events (`employment_events`) and scraped
market benchmarks (`market_observations`). It is **not** any of those and has no relationship to
them: no foreign key, no join, no shared table. Story 5's cross-check block reads this category
*and* `raw_postings` side by side, in separate queries, and never merges them.

It exists for two jobs: insight **beyond what the platform captures**, and an independent
reference to **cross-check** the platform's own figures. **Every figure always names its source.**

## The standard — eight rules

1. Standardise the **container and provenance**; keep source-specific code **at the edge**.
2. Keep **native codes** (`{system, code, label}`); crosswalks to our taxonomy are per cross-check.
3. **Never harmonise meaning** across publishers — the standard is structural, not semantic.
4. **A value never travels without its source** — non-optional `source` object on every read.
5. **Store what is published; derive the rest at read time** (no stored shares or changes).
6. **Revisions are vintages** — a changed value is a new row under the new release.
7. **No LLM** in ingestion; an unrecognised layout **rejects the release** rather than guessing.
8. **A cross-check is context, not proof** — two labelled values, never a difference or verdict.

## The tables (one set for every publisher)

| Table | One row per | Key fields |
|---|---|---|
| `statistic_series` | fully-specified series (a metric for one dimension combination) | `source`, `publisher`, `programme`, `dataset_code`, `series_code`, `unit`, `unit_scale`, `seasonal_adjustment`, `period_type`, `dimensions` (jsonb), `coverage_note`, `designation`, `licence`, `licence_confirmed`, `attribution_text` |
| `statistic_releases` | publisher release we ingested or rejected | `release_date`, `file_url`, `content_hash`, counts (new / revised / unchanged), `status`, `validation_summary` |
| `statistic_observations` | (series, period, release that changed it) | `period_start/end`, `period_label` (verbatim), `value`, `value_status`, `raw_cell`, `released_on`, `licence`, `licence_confirmed` |
| `statistics_ingestion_runs` | ingestion attempt (audit + cadence) | `source`, `ran_at`, `outcome`, `release_id`, `message` |

View `statistic_observations_latest` = the newest vintage per (series, period). **Every reader
uses the view**; only the admin detail page reads full history.

## The vocabulary (add to it here, never as a per-source column)

| Kind | Values in use / planned |
|---|---|
| `dimensions` systems | `SIC2007_section`, `SIC2007_aggregate`, `ONS_VS_size_band`, `ONS_area`; planned `NACE_Rev2` (Eurostat), `ISO_3166_1` (country) |
| `measure` | `vacancies_level`; planned `job_openings_rate`, `job_vacancy_rate`, `share_of_respondents` |
| `period_type` | `rolling_3_month`; planned `month`, `quarter`, `year` |
| `publisher_type` | `national_statistics_office` · `government_department` · `intergovernmental_body` · `research_institution` · `recognised_company_or_survey` |
| `designation` | `accredited_official_statistics` · `official_statistics` · `not_designated` · `unknown` |
| `value_status` | `provisional` · `final` · `revised` · `unknown` |

## Where the code lives

```
backend/src/trusted_stats/        # NOT `statistics/` — that shadows the Python standard library
    base.py         # PoliteFetcher, ingest_adapter() orchestrator, is_due(), LayoutError
    registry.py     # TRUSTED_PUBLISHERS (trust-bar sign-off, check interval)
    sic.py          # canonical SIC 2007 section names
    crosswalks.py   # our industry tag -> SIC section (versioned; completeness-tested)
    ons_vacancy.py  # the ONS adapter: discover / parse (pure) / validate
    xlsx_reader.py  # dependency-free .xlsx reader (standard library only — no openpyxl)
backend/src/statistics_storage.py       # mirrors scraping_storage.py
backend/src/ingest_trusted_statistics.py# the script (daily; enforced cadence)
backend/src/market_query.py             # query_trusted_statistics_data (shared read path)
backend/src/statistics_crosscheck.py    # industry_mix() / size_mix() — two labelled shares, never a difference
backend/tests/fixtures/                 # the REAL ONS files the parser tests run against
backend/tests/test_trusted_stats.py     # real-file regression tests
```

## Add a new source — the recipe

1. **Pass the trust bar** (`api.md` — "The trust bar"): named publisher; published methodology;
   citable URL; reuse terms **read off the publisher's own page**; a machine-readable route (a
   file or an API — if it needs HTML scraping, this is the wrong category: see
   `scraped-data-sources` and `/polite-scraping-review`); figures with a defined unit and period.
2. **Write the evidence**: `research/{date}-{publisher}-licence-and-access-confirmation.md` with
   the exact licence quotes, URLs and date read, and what the real files contain. (ONS's is the
   template: `research/2026-09-24-ons-licence-and-access-confirmation.md`.)
3. **Register** `SOURCE_LICENCES[<source>]` (exact attribution text, `confirmed` only if a human
   read it) **and** `TRUSTED_PUBLISHERS[<source>]` — in the same commit as the adapter
   (`test_source_licences.py` fails on a licence with no adapter, and on an adapter with no licence).
4. **Adapter**: `discover` (cheap), `parse` (pure function of bytes), `validate`
   (sum-of-parts, contiguity, cross-file checks — whatever the publisher's own data lets you
   verify). SDMX publishers: add a config entry to the shared SDMX adapter instead.
5. **Test against a small trimmed REAL file** with expected values taken from the publisher's own
   published figures — not a hand-made fixture.
6. **Run** `ingest_trusted_statistics.py --source <key>`; open `/admin/statistics-sources` and
   `/admin/statistics`; **compare the stored latest values with the publisher's own site**.
7. **Docs**: `DATA_SOURCES.md` §3c table row, `LICENSING.md` row, this file's vocabulary table if
   you introduced a new system/measure, `ACCESS.md` if it changes what MCP can reach.
8. If it needs a **cross-check crosswalk**, add it in `crosswalks.py` with a completeness test —
   and keep an honest `None` wherever no honest mapping exists.

## Things that will bite you (each was found in a real file)

- ONS's `description.releaseDate` in the page-data JSON is **2016** — the dataset's first release.
  Use `versions[-1].updateDate`.
- ONS header text has hyphenation artefacts ("Manu-    facturing"): **labels come from our own
  canonical tables; the code/ID rows are authoritative.**
- Files are ~720 rows with mostly empty rows and footnotes: locate by pattern, never by row number.
- The latest period is flagged **provisional** — it *will* be revised; that's why vintages exist.
- Rolling three-month windows **overlap**: consecutive periods are not independent observations.
- Our employer size bands (5,000+ / 500–5,000 / 50–500 / <50) **don't align** with ONS's
  (1–9 / 10–49 / 50–249 / 250–2,499 / 2,500+) — don't cross-check sizes until a standards-based
  band exists. See `EMPLOYER_SIZE_STANDARDS.md` (why ONS uses these bands, and which parts apply
  outside the UK). **Update 2026-09-25:** the platform's size label is now ONS's five bands, derived from
  cited headcounts (`backend/src/employer_headcount.py`, live) — so a size cross-check is now possible once
  this category's adapter is built. Caveats stay: headcounts are mostly worldwide, and ONS may size a group.
- The ONS Vacancy Survey covers **Great Britain** and ONS **weights it up to the UK** (Northern
  Ireland ≈3% of UK employment) — the published "UK" figure is derived, and the coverage note says
  so.
- ONS labels the smallest size band "1 - 9" in the file but "2 to 9" in its methodology: units with
  one person on the register are **modelled, not surveyed**.
- The size-of-business file has **no seasonal-adjustment wording**; ONS's methodology page says the
  by-size series is seasonally adjusted. Store the QMI's statement and record where it came from.
- ONS covers the **UK only** and excludes agriculture, households as employers and employment
  agencies; the platform's panel also has US and EU employers — restrict the platform side of
  any UK cross-check to UK-located postings.
- **Never use the ONS logo** — the OGL excludes logos.

## How to verify it yourself (once built)

- `/admin/statistics-sources` — is the source registered, licensed, due, holding the period you
  expect, with no rejected release?
- `/admin/statistics?series_code=AP2Y` — latest total; compare with ONS's own bulletin.
- `/admin/statistics/{id}` — vintage history: what changed between releases.
- `backend/tests/test_trusted_stats.py` — parse, validation, vintage, provenance and crosswalk
  tests.
