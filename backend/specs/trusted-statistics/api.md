---
id: trusted-statistics
experience: market-health (Story 5 in `design/market-health/data-stories.md`) + pipeline-visibility (admin views)
directive: low
status: implemented
created: 2026-09-24
---

# Trusted External Statistics — Backend Architecture Spec

> **IMPLEMENTED 2026-09-25** (`changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md`, Steps 8): `backend/src/trusted_stats/`,
> `statistics_storage.py`, `statistics_crosscheck.py`, `ingest_trusted_statistics.py`, `query_trusted_statistics_data` in
> `market_query.py`, Story 5 (`market_stories.py`), the chat tool, the MCP tool `get_trusted_statistics`, three admin views, and
> `backend/tests/test_trusted_stats.py` (49 offline tests against the real ONS files). **Verified live** against the production
> database and ONS's own figures. Deviations and findings are in "Implementation notes" at the end of this file. **Frontend for
> Story 5 is not built.** Not yet a scheduled Railway service (`DEPLOYMENT.md`).

## Experience this implements
- `design/market-health/data-stories.md` — **Story 5, "UK vacancies (official data)"** — the first
  consumer of this data.
- `design/pipeline-visibility/experience.md` — User Flow step 11 (Trusted Statistics and
  Statistics Sources admin views).
- Outcome: `outcomes/job-data-source-flexibility.md` (success criterion added 2026-09-24).
- Change request: `changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md`.
- Evidence this spec was written against (real files, not fixtures):
  `research/2026-09-24-ons-licence-and-access-confirmation.md`.

## What this is — and what it is not

A **source category** for market analysis and statistics published by trusted institutions —
governments and statistical offices, intergovernmental bodies, other well-recognised
organisations — used to (a) give insight beyond what this platform captures and (b) provide an
independent reference to cross-check the platform's own figures against. Alongside job postings
(`raw_postings`), employment events (`employment_events`) and scraped market benchmarks
(`market_observations`) in `DATA_SOURCES.md` §2 — a fourth shape: **published statistical
series**, not a posting, not an event, not a scraped ranking.

It is **not** a place for narrative reports/articles (a later slice — `DATA_SOURCES.md` §2's
"Research / reports / articles" row keeps its own contract) and **not** a way to bypass a
publisher's terms: a source only enters through the trust bar below.

**This category supersedes** the 2026-09-16 note (`DATA_SOURCES.md` §3b,
`scraped-data-sources/api.md` Part 2) that a future benchmark source "e.g. ONS" would be a new
`source` value in `market_observations`. That note assumed an IT-Jobs-Watch-shaped role/skill
ranking; ONS vacancies are metric × dimension × period statistics, and the category must hold
other publishers' statistics later. `market_observations`/`skill_associations` are unchanged.

## Ground rules (the standard — every source of this type follows these)

1. **Standardise the container and the provenance; keep source-specific code at the edge.**
   One long-format store (series / releases / observations) for every publisher. One small
   adapter per publisher *format* maps into it. Adding a source = a registry entry + an adapter
   (or, for SDMX publishers, a config entry on the shared SDMX adapter) — never new tables, new
   endpoints, or new UI plumbing.
2. **Native codes are kept.** A dimension is stored as `{system, code, label}` (e.g.
   `{"system": "SIC2007_section", "code": "J", "label": "Information and communication"}`).
   Nothing is force-mapped into this platform's own taxonomy at ingestion. A mapping to our
   taxonomy (a *crosswalk*) exists only where a specific cross-check needs one, is curated, is
   versioned, and honestly says "unmapped" where no honest mapping exists.
3. **Meaning is never harmonised across publishers.** ONS "vacancies", Eurostat "job vacancy
   rate", and this platform's "postings" are different measures. The standard is structural
   (same shape, same provenance), not semantic (same meaning).
4. **A value never travels without its source.** Every read function returns statistics
   together with a non-optional `source` object (publisher, programme, dataset, series code,
   source URL, release date, licence + whether confirmed, attribution text, designation,
   seasonal adjustment, coverage note). There is no code path that returns a bare number. A
   test enforces this (Tech Decisions).
5. **Store what is published; derive the rest at read time.** No stored percentage changes or
   shares — those are computed from stored levels, so they can never disagree with the levels.
6. **Revisions are kept as vintages.** Statistics get revised (ONS flags the latest period
   provisional). A changed value is a new observation row under the new release; the latest
   vintage is what readers see, the history is what admin shows.
7. **No LLM in the ingestion path.** Structured statistics are parsed deterministically. If a
   layout is not what the parser expects, the release is **rejected and flagged**, never guessed
   at (the IT Jobs Watch regex-extraction lesson, `changes/2026-09-18-itjobswatch-llm-extraction.md`).
8. **A cross-check is context, not proof.** Backend code that puts a platform figure next to a
   statistic returns two labelled, separately-sourced values — never a difference, a score, or a
   verdict.

## The trust bar — what a publisher must pass to be added

Recorded per publisher in `TRUSTED_PUBLISHERS` (code, below) and reviewed by a human before the
first ingestion. All must hold:

| # | Requirement | How it's evidenced |
|---|---|---|
| 1 | A **named publisher** with a public identity (statistical office, intergovernmental body, or recognised institution/company) | `publisher`, `publisher_type` |
| 2 | **Published methodology** for the figures (what is counted, sample, exclusions) | `methodology_url` |
| 3 | A **stable, citable source URL** per dataset | `source_page_url` |
| 4 | **Reuse terms read off the publisher's own page** and permitting our use | a `SOURCE_LICENCES` entry with `confirmed=True` and a research file with the quotes (`LICENSING.md` discipline). If not yet confirmed: ingestion proceeds, flagged loudly, `licence_confirmed=False` travels with every row |
| 5 | **A machine-readable route** — a published data file or API. No HTML scraping in this category (a source that needs scraping goes through Rule 13 / `scraped-data-sources`) | adapter design |
| 6 | Statistics, not opinion — figures with a defined unit and period | series definition |

`publisher_type` (closed set, informational, surfaced in admin): `national_statistics_office` ·
`government_department` · `intergovernmental_body` · `research_institution` ·
`recognised_company_or_survey`. **Tier does not skip the bar** — a prestigious name with
unconfirmed reuse terms is still flagged, never silently used.

## Data Models

Tables are created by `db.py`'s idempotent startup DDL, same pattern as every other table.

### StatisticSeries (`statistic_series` table)
One row per **fully-specified series** — a metric for one combination of dimensions (ONS: one
series ID = one industry section, or one size class, or the total). The natural key is the
publisher's own series identifier where one exists.

| Field | Type | Description |
|---|---|---|
| `id` | `str` (PK) | `f"{source}:{series_code}"`, e.g. `ons_vacancy_survey:JP9H`. ONS series IDs are unique across ONS, so `AP2Y` (all vacancies) appearing in both VACS02 and VACS03 is **one** series. |
| `source` | `str` | Registry key (`TRUSTED_PUBLISHERS`), e.g. `ons_vacancy_survey`. Must also be a key in `source_licences.SOURCE_LICENCES`. |
| `publisher` | `str` | Display name, e.g. `"Office for National Statistics"`. |
| `programme` | `str` | e.g. `"Vacancy Survey"`. |
| `dataset_code` | `str` | The dataset this series was first seen in, e.g. `"VACS02"`. |
| `series_code` | `str` | The publisher's own id, e.g. `"JP9H"`. |
| `title` | `str` | Our canonical label for the series (not the publisher's header text — see ONS quirks below), e.g. `"Vacancies — Mining and quarrying"`. |
| `measure` | `str` | Closed set, per adapter definition: `vacancies_level`, `job_openings_rate`, … Free to grow with new publishers; never inferred from `unit`. |
| `unit` | `str` | Words, exactly what a bare value counts: `"thousand vacancies"`, `"vacancies per 100 jobs"`. |
| `unit_scale` | `int` | Multiplier to a plain count (`1000` for "thousand vacancies", `1` where not a count). Readers convert for display; storage keeps the published value. |
| `seasonal_adjustment` | `"seasonally_adjusted" \| "not_adjusted" \| "unknown"` | **Read from the file, never assumed** (`unknown` if the file doesn't say). |
| `period_type` | `"rolling_3_month" \| "month" \| "quarter" \| "year" \| …` | ONS vacancies are `rolling_3_month` — overlapping windows; consecutive periods are not independent. |
| `frequency` | `str` | How often the publisher releases (`"monthly"`). |
| `dimensions` | `jsonb` | Map of dimension name → `{system, code, label}`. ONS VACS02 series: `{"industry": {...}, "geography": {"system":"ONS_area","code":"K02000001","label":"United Kingdom"}}`; VACS03: `{"size_band": {...}, "geography": {...}}`. |
| `dimension_type` | `str` | Primary dimension for indexing/filtering: `"total"`, `"industry"`, `"size_band"`, … |
| `definition_note` | `str` | What it counts, in the publisher's terms. |
| `coverage_note` | `str` | What it leaves out. ONS: *"All sectors except agriculture, forestry and fishing (SIC 2007 section A), activities of households as employers (section T) and employment agencies (division 78)."* — surfaced wherever the number is shown. **Also (ONS Vacancy Survey QMI, read 2026-09-25): the survey covers Great Britain (England, Scotland, Wales) and ONS weights it up to the UK using employment estimates — Northern Ireland is about 3% of UK employment.** The published figure is a UK estimate derived from a GB survey, and says so wherever coverage is stated. |
| `designation` | `"accredited_official_statistics" \| "official_statistics" \| "not_designated" \| "unknown"` | The publisher's own status for this dataset (ONS VACS01–03 three-month averages: accredited official statistics; X06: not designated). |
| `methodology_url` / `source_page_url` | `str` | Mandatory. |
| `licence` / `licence_confirmed` / `attribution_text` | `str` / `bool` / `str` | Mandatory — snapshot of `SOURCE_LICENCES` at ingestion so the naming and the "always flag if unconfirmed" caveat travel with the row (`data-legibility` Provenance; Rule 13's rule applied here). |
| `first_seen_at` / `updated_at` | `datetime` | |

### StatisticRelease (`statistic_releases` table)
One row per publisher release of a dataset that we have ingested (or rejected).

| Field | Type | Description |
|---|---|---|
| `id` | `str` (PK) | `f"{source}:{dataset_code}:{release_date}"`, e.g. `ons_vacancy_survey:VACS03:2026-09-15`. |
| `source` / `dataset_code` | `str` | |
| `release_date` | `date` | The publisher's own release date. **ONS: `versions[-1].updateDate` from the page-data JSON — never `description.releaseDate`** (stale, 2016). |
| `release_uri` | `str` | The addressable release (`…/current` or `…/previous/v128`). |
| `file_url` / `file_name` | `str` | The file actually parsed. |
| `content_hash` | `str` | SHA-256 of the downloaded file — the new-only guard: an unchanged hash is never re-parsed. |
| `fetched_at` | `datetime` | |
| `rows_parsed` / `observations_new` / `observations_revised` / `observations_unchanged` | `int` | Real counts, shown in admin. |
| `status` | `"ingested" \| "rejected_validation" \| "failed"` | A rejected release stores **no observations**. |
| `validation_summary` | `text` | Which checks ran and, if rejected, exactly which failed. |

### StatisticObservation (`statistic_observations` table)
One row per (series, period, release-that-changed-it).

| Field | Type | Description |
|---|---|---|
| `id` | `str` (PK) | `f"{series_id}:{period_start}:{release_date}"`. |
| `series_id` | `str` (FK → `statistic_series.id`) | |
| `release_id` | `str` (FK → `statistic_releases.id`) | Which release brought this value. |
| `period_start` / `period_end` | `date` | Exact window (`"Jun-Aug 2026"` → 2026-06-01 … 2026-08-31). |
| `period_label` | `str` | The publisher's own label verbatim (`"Jun-Aug 2026"`), shown to users in the publisher's own words. |
| `value` | `numeric` | As published (thousands for ONS levels). |
| `value_status` | `"provisional" \| "final" \| "revised" \| "unknown"` | From the file's own flag (ONS `(p)` = provisional). `revised` = a later release changed a previously stored value. |
| `raw_cell` | `text` | The verbatim cell text and flag, for audit. |
| `released_on` | `date` | Copy of the release's date (avoids a join for the latest-vintage query). |
| `licence` / `licence_confirmed` | `str` / `bool` | Mandatory copy, same as the series. |
| `fetched_at` / `created_at` | `datetime` | |

**Latest vintage.** A database view `statistic_observations_latest` selects, per
`(series_id, period_start)`, the row with the greatest `released_on`. Every reader uses the view;
only admin's detail page reads the full history.

### StatisticsIngestionRun (`statistics_ingestion_runs` table)
Audit + cadence record, mirroring `scrape_ingestion_runs`.

| Field | Type | Description |
|---|---|---|
| `id` | serial PK | |
| `source` | `str` | |
| `ran_at` | `datetime` | |
| `outcome` | `"new_release_ingested" \| "no_new_release" \| "skipped_not_due" \| "rejected_validation" \| "failed"` | |
| `release_id` | `str \| None` | |
| `message` | `text` | Human-readable; includes a loud `WARNING` line when the source's licence is unconfirmed. |

### In-code registries (no tables)

- **`TRUSTED_PUBLISHERS`** (`trusted_stats/registry.py`) — one `TrustedPublisher` per `source`:
  `source`, `publisher`, `publisher_type`, `programme`, `datasets`, `methodology_url`,
  `source_page_url`, `min_check_interval_hours` (ONS: 24), `trust_bar_reviewed_on` +
  `trust_bar_reviewed_by` (a human sign-off date), `notes`. **An adapter with no entry here, or
  no matching `SOURCE_LICENCES` entry, is a hard error** — same "refuse rather than guess" rule
  as `source_licences.py`.
- **`SOURCE_LICENCES["ons_vacancy_survey"]`** — the exact entry (registered **in the same commit
  as the adapter**, not before: `test_source_licences.py` fails the build on a registered
  licence with no adapter):
  ```python
  "ons_vacancy_survey": SourceLicence(
      source="ons_vacancy_survey",
      licence="Open Government Licence v3.0",
      attribution_text=("Source: Office for National Statistics — Vacancy Survey. "
                        "Contains public sector information licensed under the Open Government Licence v3.0."),
      licence_url="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
      confirmed=True,          # read off ons.gov.uk + the National Archives, 2026-09-24
      permits_commercial_use=True,
      data_summary=("Aggregate UK vacancy estimates by industry (SIC 2007) and size of business — "
                    "levels in thousands, 3-month rolling averages. No individual postings, no personal data."),
  )
  ```
  Evidence: `research/2026-09-24-ons-licence-and-access-confirmation.md`. **Never use the ONS logo**
  (OGL excludes departmental logos).
- **`SIC_2007_SECTIONS`** (`trusted_stats/sic.py`) — canonical section code → plain-language name
  (A…U). ONS header text is *not* used for labels (hyphenation artefacts — see the ONS adapter).
- **Crosswalks** (`trusted_stats/crosswalks.py`) — see Business Logic §6.

## Adapter interface (standardised edge)

```python
class StatisticsAdapter(Protocol):
    source: str                                            # key in TRUSTED_PUBLISHERS and SOURCE_LICENCES
    def discover(self, fetcher: PoliteFetcher) -> list[ReleaseRef]: ...
        # Cheap. Which releases exist, newest first; each with release_date, release_uri, file_url.
    def parse(self, ref: ReleaseRef, file_bytes: bytes) -> ParsedRelease: ...
        # Pure function of the bytes — no network, no database, no licence handling.
    def validate(self, parsed: ParsedRelease) -> list[str]: ...
        # Returns failures; non-empty = release rejected.
```
`ParsedRelease` = `SeriesDefinition[]` + `FetchedStatistic[]` (`series_code`, `period_start`,
`period_end`, `period_label`, `value`, `value_status`, `raw_cell`). **The adapter never touches
storage or licences.** The shared orchestrator (`trusted_stats/base.py::ingest_adapter`) owns
everything else: cadence, download, hashing, validation gate, licence stamping from the registry,
vintage-aware storage, run logging, fault isolation. `parse()` being pure is what makes real-file
regression tests possible (Tech Decisions).

## API Endpoints

**No new public REST endpoints.** Ingestion is a script (`ingest_trusted_statistics.py`), same
pattern as `ingest.py` / `ingest_scraped_sources.py`. Consumers:

- **Story 5** — `POST /api/market-health/stories/uk-vacancies-official` via the existing story
  route (a catalogue operation, `backend/specs/market-health/api.md`).
- **Chat** — `query_trusted_statistics_data` registered as a chat tool
  (`backend/specs/market-health/api.md`).
- **MCP** — `get_trusted_statistics` (`backend/specs/mcp-access/api.md`).
- **Admin** — `/admin/statistics`, `/admin/statistics/{id}`, `/admin/statistics-sources`
  (`backend/specs/pipeline-visibility/api.md`).

### Read function: `query_trusted_statistics_data(...)` (`market_query.py`)
The single read path all consumers above share (story, chat, MCP) — no consumer queries the
tables directly.

**Parameters** (all optional): `dimension` (`"total" | "industry" | "size_band"`, default
`"total"`), `publisher` (a `TRUSTED_PUBLISHERS` key), `industry_code`, `size_band`,
`period` (`"latest"` default | `"year_ago"` | `"previous_quarter"`), `date_from`, `date_to`.

**Returns:**
```json
{
  "statistics": [
    {
      "series": {
        "title": "Vacancies — Information and communication",
        "dimension": { "industry": { "system": "SIC2007_section", "code": "J", "label": "Information and communication" } },
        "unit": "thousand vacancies", "unit_scale": 1000,
        "seasonal_adjustment": "seasonally_adjusted", "period_type": "rolling_3_month",
        "coverage_note": "All sectors except agriculture, forestry and fishing …",
        "source": {
          "publisher": "Office for National Statistics", "programme": "Vacancy Survey",
          "dataset_code": "VACS02", "series_code": "JP9P",
          "source_url": "https://www.ons.gov.uk/…/vacanciesbyindustryvacs02",
          "designation": "accredited_official_statistics",
          "licence": "Open Government Licence v3.0", "licence_confirmed": true,
          "attribution_text": "Source: Office for National Statistics — Vacancy Survey. Contains public sector information licensed under the Open Government Licence v3.0."
        }
      },
      "observations": [
        { "period_label": "Jun-Aug 2026", "period_start": "2026-06-01", "period_end": "2026-08-31",
          "value": 61, "value_status": "provisional", "released_on": "2026-09-15" }
      ]
    }
  ],
  "sources_checked": ["ons_vacancy_survey"],
  "as_of": "2026-09-24T12:00:00Z",
  "total_matching": 21
}
```
**Contract:** every `statistics[]` entry carries `series.source` with every field non-empty
(rule 4). **Gate:** before querying, each candidate source passes
`source_licences.is_source_usable(source)`; a rejected source is excluded and named in
`sources_checked` with `"unavailable"` — never a stale render. **No data yet** → `statistics: []`
with `sources_checked` naming the registered-but-empty source, so a caller reads "we checked and
nothing has been collected yet", not "doesn't exist". The function never estimates, interpolates
or fills a missing period.

## Business Logic

### 1. Ingestion flow (per source, per run)
1. **Cadence gate — enforced in code, before any request.** `is_due(source,
   min_interval_hours)` against `statistics_ingestion_runs`; if not due, log `skipped_not_due`
   and stop. Survives the script being invoked more often than intended (Rule 13 constraint 1,
   applied in spirit — this is a file download, not scraping, but the discipline is identical).
   ONS: 24 h between release checks; a release lands ~monthly.
2. **Discover** (`adapter.discover`): ONS — GET `<dataset page URL>/current/data` (JSON). Newest
   release = `versions[-1]`; its `updateDate` is the release date; current file =
   `downloads[0].file` under `…/current/`. **One JSON request per dataset per check.**
3. **New-only.** If a `statistic_releases` row already exists for `(source, dataset_code,
   release_date)` with `status = 'ingested'` → log `no_new_release`, stop. **No file download.**
4. **Download** the file (ONE request), compute `content_hash`. If the hash matches any stored
   release's hash for this dataset (publisher re-stamped an identical file) → record the release,
   ingest nothing new.
5. **Parse** (`adapter.parse`) → `ParsedRelease`. Any unexpected layout raises `LayoutError`.
6. **Validate** (`adapter.validate`). **Non-empty failures = the whole release is rejected**:
   `statistic_releases.status = 'rejected_validation'`, no observations stored, a loud
   `WARNING` naming the failed checks, run outcome `rejected_validation`. Nothing is guessed
   around.
7. **Stamp** each series/observation with `licence`, `licence_confirmed`, `attribution_text` from
   the registry. If `confirmed` is `False`: ingestion proceeds, and a `WARNING` is logged at
   ingestion time ("data stored, licence not confirmed — see LICENSING.md") — never blocks,
   never buried (`polite-scraping-review` licence rule; `LICENSING.md` §2).
8. **Store, vintage-aware** (§3), then record the release and run. Store in one transaction per
   release: a crash mid-release leaves nothing half-written.
9. **Fault isolation.** One source or one dataset failing is logged (`failed`) and never stops
   the others, nor any other ingestion pipeline (same precedent as
   `changes/2026-07-27-adzuna-ingestion-resilience.md`).

**Politeness (all requests, `PoliteFetcher`):** descriptive User-Agent with a real contact
(`STATISTICS_CONTACT` env var — **refuses to run if unset**, same rule as `SCRAPER_CONTACT`);
≥ 3 s between any two requests to a host; `robots.txt` fetched and honoured (a 404 = no
restrictions, per RFC 9309 — ONS publishes none); conditional requests where the host supports
them. Steady state ≈ 3 requests per month for ONS.

### 2. The ONS Vacancy Survey adapter (`trusted_stats/ons_vacancy.py`) — written against the real files
Verified 2026-09-24 (`research/2026-09-24-ons-licence-and-access-confirmation.md`).

| Dataset | Sheet | What is parsed | Series identity | Dimension |
|---|---|---|---|---|
| **VACS03** | `VACS03` | Row 7 series IDs; period rows from the first period label; columns C (all) and G–K (size classes) | `AP2Y`; `ALY5`…`ALY9` | `size_band` (`ONS_VS_size_band`): `1-9`, `10-49`, `50-249`, `250-2499`, `2500+` employed. **Note:** the file labels the smallest band "1 - 9" but ONS's methodology (QMI) says "2 to 9" — businesses with one person on the business register are *modelled, not surveyed*, and are included in the published 1–9 figure. The stored code is `1-9` (what the file says); the difference goes in `definition_note` |
| **VACS02** | `levels` | Row 5 SIC codes + row 6 series IDs; period rows | `AP2Y` (`B-S` total); `JP9H`…`JP9Y` (the 18 sections B–S, in order — section J is `JP9P`); `JP9Z` (aggregate `G-S`, stored with system `SIC2007_aggregate`). Divisions 45/46/47 (columns W–Y) have **no series ID in row 6** in the 2026-09-24 file → **not ingested in the first slice** (Open Questions) | `industry` (`SIC2007_section`) |
| VACS02 | `job openings rate` | **Deferred** — the sheet's column set has not been inspected; added only after inspection (Open Questions) | — | — |
| X06 | — | **Deferred** — file layout not inspected | — | — |

Parsing rules (each one exists because of something seen in the real file):
- **Locate by pattern, not position.** Series IDs = the row whose cells all match `^[A-Z]{3,4}$`;
  period rows = column A matching `^[A-Z][a-z]{2}-\s*[A-Z][a-z]{2} \d{4}$` (a stray space exists:
  `"Nov- Jan 2002"`). The files have ~720 rows, most empty; row numbers are never hard-coded.
- **Skip non-period rows** (`Change on quarter`, `Change %`, `Change on year`, footnotes, source
  lines). Change columns are **not stored** — derived at read time (rule 5).
- **Period parsing.** `"Jun-Aug 2026"` → 2026-06-01 … 2026-08-31; a window crossing a year end
  (`"Nov-Jan 2002"`) ends in the following year and is labelled by its end year per ONS's own
  convention — verified against the file at implementation time, not assumed.
- **Flags.** Column B: `(p)` → `provisional`; blank → `final`; any other text → `unknown` with
  the text kept in `raw_cell`.
- **Values** are thousands as published → `unit = "thousand vacancies"`, `unit_scale = 1000`.
  A non-numeric cell in a data position (`..`, `-`) is stored as **no observation**, never `0`.
- **Labels** come from `SIC_2007_SECTIONS` and the size-class list above — never from the ONS
  header cells (`"Manu-    facturing"`, `"Construc-tion"`).
- **`seasonal_adjustment`** is read from the file, never assumed, **per series**. VACS02: the sheet
  title says "seasonally adjusted", but **footnotes 2 and 3 mark some series as not seasonally
  adjusted** (they show no seasonality, so the unadjusted series is ONS's best estimate) — the
  footnote markers on the header cells decide which; those series are stored `not_adjusted`
  with the footnote text in `definition_note`. **VACS03's file contains no adjustment wording at
  all** (checked across the whole workbook, 2026-09-24), **but ONS's own methodology page (QMI,
  read 2026-09-25) states: "The three-month moving average series by industry and by size of
  business is seasonally adjusted directly"** — so VACS03 is stored `seasonally_adjusted`, with
  `definition_note` recording that the source of that status is the QMI, not the file. (Still
  worth confirming with ONS before stating it to end users.) The status is never *assumed to
  match* another file without a documented statement. A surface that shows an adjustment status shows the stored value, including
  "not stated by the publisher" for `unknown`.
- **Scope note** (`coverage_note`) is copied from the file's own footnote 1, not paraphrased.

**Validation checks (release rejected if any fails):**
1. Expected anchors found (series-ID row, ≥ 1 period row, all expected series IDs present).
2. Period sequence contiguous and the newest period is **not older** than the newest already stored.
3. **Sum of parts:** at the newest period, VACS03's five size classes sum to `AP2Y` within
   rounding tolerance (real file 2026-09-24: 91+99+103+169+240 = 702 = total ✔); VACS02's
   sections B–S sum to `B-S` within rounding tolerance. Tolerances are calibrated against the real
   files at implementation and recorded in code.
4. **Cross-file:** `AP2Y` for every shared period is equal in VACS02 and VACS03 in the same
   release month — an independent check, from ONS's own data, that the parse is right.
5. Values within a plausible range (non-negative; total between 100k and 2M — a unit-slip guard).

### 3. New-only, vintages, and revisions
- **First run:** ingest the full history in the current file (VACS03: 302 periods × 6 series;
  VACS02: ~20 series) — ≈ 9k rows, small. Every row is `provisional`/`final` per its flag.
- **Later releases:** for each `(series, period)`, compare with the latest stored value. **Equal
  value and status → skip (no row).** Different → insert a new observation under the new release,
  `value_status = 'revised'` when the value changed (a `provisional → final` flip with the same
  value is also stored, `final`). A typical release therefore adds a handful of rows.
- **Past vintages** (`versions[]` lists 129 for VACS03): **not backfilled by default.** An
  explicit `--backfill-vintages N` option can fetch older releases one at a time under the same
  politeness rules — only if a revision-history feature is ever wanted (Open Questions).
- A statistic **never** shows "revised" language to users on its own (a future surface decides);
  admin shows the vintage history.

### 4. Licence gating and provenance
- Every consumer passes each candidate source through `is_source_usable(source)`.
- `ingest_trusted_statistics.py` emits the licence warning when `confirmed=False` (§1.7).
- A row's `licence_confirmed=False` must render a visible caveat on any surface (`data-legibility`
  Provenance) and in the Reasoning Panel wherever the figure is used. ONS is `True`, so nothing
  renders today — but the field travels so the first surface for a *future* unconfirmed publisher
  is required to render it.
- `/admin/licensing` lists the source automatically (it renders `SOURCE_LICENCES`).

### 5. The ad-hoc / chat / MCP path
`query_trusted_statistics_data` (above) is the only read path. It is registered:
- as a **chat tool** so a free-form question ("how many vacancies are there in UK construction?")
  reaches the data (`backend/specs/market-health/api.md` — chat tools; DB-only chat rule
  unchanged: the answer is composed only from stored statistics and names the publisher);
- as the wrapped function of the MCP tool `get_trusted_statistics`.
This closes the "new table only a hand-written story can read" gap (`data-surface-review`
Step 2d).

### 6. Cross-check support (Story 5's third movement)
- **`statistics_crosscheck.industry_mix()`** returns two independent, separately-labelled series:
  (a) *platform side* — share of **UK-located** postings currently in `raw_postings` by SIC 2007
  section, via the crosswalk; (b) *ONS side* — each section's share of the ONS all-industries
  total for the latest period. Both as shares (proportions), each with its own denominator, each
  named. **No difference, no score.** The platform side is restricted to the platform's
  normalised UK country value because ONS covers the UK only, while the panel also includes US
  and EU employers.
- **Crosswalk** (`trusted_stats/crosswalks.py::OUR_INDUSTRY_TO_SIC_SECTION`, versioned by
  `CROSSWALK_VERSION`): our free-form industry tag (`industries.COMPANY_INDUSTRY` values, e.g.
  `"Fintech"`) → SIC 2007 section code, or `None`. Draft rules, reviewed at implementation:
  software / AI / developer platforms / social / search / security / streaming and media
  software → **J** (Information and communication); Fintech / Insurtech → **K** (Financial and
  insurance); retail and e-commerce selling goods → **G**; education providers → **P**;
  health-tech → **Q**. **Ambiguous tags (marketplaces, travel, delivery, HR tech, climate/data
  mixes) stay `None`** — reported as a stated "not mapped to an industry group" share, never
  forced into a section. Mapping is by the tag, not per-company guesswork.
- **Completeness test:** every distinct value of `COMPANY_INDUSTRY` must be a key of the
  crosswalk (value or explicit `None`); adding a new industry tag without a mapping decision
  fails the build — the same enforcement pattern as `test_source_licences.py`.
- **Size-band cross-check — specified 2026-09-25; the headcount-derived band data now EXISTS (implemented
  2026-09-25, live), so this is buildable as soon as the trusted-statistics adapter itself is implemented** (`changes/2026-09-25-employer-size-standard-bands.md`; standards in
  `EMPLOYER_SIZE_STANDARDS.md`). Until then it is **not built**, because the platform's original labels
  (Large 5,000+, Medium 500–5,000, Small/Growth 50–500, Startup <50) did not align with ONS's classes
  and forcing a mapping would have fabricated a match. The design, decided by the PM (2026-09-25):
  the platform's default size label **is** ONS's five bands, **derived from a cited headcount range**
  (`market-health/api.md` — Employer size, revised). Then:
  - **`statistics_crosscheck.size_mix()`** returns two independent, separately-labelled series: (a)
    *platform side* — share of **UK-located** postings by ONS size band, the band derived from
    `COMPANY_HEADCOUNT` at query time; postings whose employer is `ambiguous` or has no entry are
    counted in an explicit **"Not placed in a size band"** row, never dropped and never forced into a
    band; (b) *ONS side* — each of the five classes' share of the `AP2Y` total for the latest period
    (VACS03), computed from stored levels. Shares, each with its own denominator; **no difference, no
    score** (rule 8).
  - **What the result is expected to show, from the 2026-09-25 research:** the tracked panel has **no
    company under 50 employees**, while ONS's own Jun–Aug 2026 figures put about 27% of UK vacancies at
    businesses under 50. The comparison is worth building precisely because it displays that lean; it
    must be worded as "how our view leans", never as a verdict on either side.
  - **Required qualifiers:** (1) the platform's headcounts are mostly **worldwide/group** figures whereas
    ONS sizes the **UK** business — derived bands for multinationals are approximations; (2) ONS's
    business unit may be the **enterprise group**, so a company acquired by a larger group may sit in a
    bigger ONS band than its own headcount implies (unverified — Open Questions); (3) the count of
    roles not placed; (4) the survey covers Great Britain, weighted to the UK.
  - The experience side (a size comparison next to the industry one in Story 5's third movement) is
    its own step in the change request (Step 7), **after** the data exists — this spec does not change
    Story 5 as currently specified.

### 7. Adding the next source (the recipe — full version in `backend/TRUSTED_STATISTICS.md`)
1. Pass the trust bar; write the research file with the licence quotes.
2. Register `SOURCE_LICENCES[...]` and `TRUSTED_PUBLISHERS[...]`.
3. Implement (or configure) the adapter: `discover`, `parse` (pure), `validate`.
4. Add real-file regression tests using a small trimmed real file.
5. Run `ingest_trusted_statistics.py --source <key>`; check admin; update `DATA_SOURCES.md`.
6. If it introduces a new *dimension system* or *measure*, add it to `TRUSTED_STATISTICS.md`'s
   vocabulary table — do not invent a per-source column.

## Paper-test: is the schema ONS-shaped? (the `job-data-source-flexibility` Adzuna lesson)
Checked on paper, before implementation, against two publishers of *different* shape. No
requests were made to either; details of each dataset must be verified at adoption.

| Test shape | How it maps | Verdict |
|---|---|---|
| **Eurostat job-vacancy statistics via SDMX** (quarterly, by NACE activity and country; a rate, not a level) | Series = (dataset, measure, NACE activity, country, size class); `dimensions` holds each as `{system: "NACE_Rev2", code, label}`; `measure = job_vacancy_rate`, `unit = "% of posts"`, `period_type = quarter`; SDMX flags (provisional/estimated) → `value_status`. One generic SDMX adapter covers OECD/Eurostat/ILO/ECB/IMF by config. | Fits with no schema change |
| **An annual survey/report from a non-government body** (e.g. a developer or salary survey: respondent-based shares, annual, with sample size) | Series = (survey, question, answer category, cohort); `period_type = year`; `measure = share_of_respondents`, `unit = "% of respondents"`; **sample size and margin are not a column** — they go in `definition_note` and a generic `qualifiers jsonb` on the series (added when this shape is first adopted; not built now — YAGNI, but the path is noted so it doesn't force a redesign) | Fits, one additive column later |

Both need **only** new adapters/config, new dimension-system names, and (for the second) an
optional qualifiers field. Neither needs a new table.

## MCP Access Review (recorded — `/mcp-access-review`, 2026-09-24)

| Capability | Decision |
|---|---|
| `query_trusted_statistics_data` — read trusted statistics by dimension | **Exposed** as `get_trusted_statistics` (scope `jobs.read`, every plan tier — OGL permits commercial use, so no premium gate is needed; gated per source by `is_source_usable`). A real consumer surface (Story 5) is specified, so — unlike the 2026-09-16 "deferred" call on benchmarks — nothing waits on one. Full tool definition in `backend/specs/mcp-access/api.md`. |
| `statistics_crosscheck.industry_mix()` — platform-vs-ONS composition | **Not exposed** — a pre-composed comparison; the outcome (`bring-your-own-ai-agent-access.md`) exposes primitives, and a calling AI holding `get_job_demand` and `get_trusted_statistics` composes any comparison itself, with each tool's own caveats. Also carries a curated crosswalk whose caveats belong in the story, not a bare tool output. |
| Story 5 itself | **Not exposed** — pre-composed reports are excluded by the same outcome direction (`ACCESS.md`, "Data stories"). |
| Admin views (`/admin/statistics*`) | **Not exposed** — operator-only, no end-user data. |
| Ingestion script | **Not applicable** — not a request-time capability. |
`ACCESS.md` updated accordingly.

## Polite Scraping Review — not applicable (recorded)
ONS is reached through its own page-data JSON and published dataset files; **no HTML is parsed,
no page is scraped**. The four Rule 13 constraints are nevertheless mirrored (cadence enforced in
code, robots.txt/pacing, new-only, real licence record) because the discipline is cheap and the
publisher states no access policy. If any future trusted source needs HTML parsing, it leaves
this category and goes through `scraped-data-sources` + `/polite-scraping-review`.

## Data Surface Review — recorded in the change request
New category; Story 5 (new, not an extension of Story 3); admin views; MCP tool; chat path — all
decided. Expected lag until first ingestion and after each monthly release is stated in the
story's own no-data state.

## External Dependencies
- ONS website: page-data JSON (`…/current/data`) and dataset files (XLSX). No key. No published
  rate policy (politeness rules above apply anyway).
- `openpyxl` (read-only mode) to read XLSX — add to `backend/requirements.txt`. (The 2026-09-24
  inspection used only the standard library, confirming the layout is simple enough that a
  dependency-free parse is possible if `openpyxl` is ever unwanted.)
- Env: `STATISTICS_CONTACT` (required, real contact for the User-Agent).
- Deployment: a small scheduled service (daily), like `job-sync`; not created by this spec
  (`DEPLOYMENT.md` updated at implementation).

## Tech Decisions
- **Package name is `trusted_stats/`, not `statistics/`** — `statistics` is a Python standard
  library module and a local package of that name would shadow it.
- Layout: `backend/src/trusted_stats/{base,registry,sic,crosswalks,ons_vacancy}.py`;
  `backend/src/statistics_storage.py` (mirrors `scraping_storage.py`);
  `backend/src/ingest_trusted_statistics.py` (script); read function in `market_query.py`.
- **Tests** (`backend/tests/test_trusted_stats.py`): (1) `parse()` against a **small trimmed
  real ONS file checked into `backend/tests/fixtures/`** — expected values taken from ONS's own
  published figures (e.g. Jun-Aug 2026 total 702k, size classes 91/99/103/169/240); (2) each
  validation check fails when its condition is violated; (3) vintage logic — unchanged skipped,
  changed inserted as `revised`; (4) **every function that returns statistic values returns a
  fully-populated `source` object** (rule 4); (5) crosswalk completeness; (6) registry
  completeness — every adapter has a `TRUSTED_PUBLISHERS` and a `SOURCE_LICENCES` entry and
  vice versa; (7) cadence gate skips without any request.
- Verification bar for "implemented": run against the **real** ONS files and compare the stored
  latest values with ONS's own published figures — not only fixtures (the 2026-09-18 lesson).

## Open Questions
- **ONS-compatible employer size band** — `changes/2026-09-25-employer-size-standard-bands.md`
  (`in-progress`; PM decided 2026-09-25: headcount is the source of truth, ONS's five bands are the
  default label). Unlocks the size cross-check specified in §6. Standards and rationale:
  `EMPLOYER_SIZE_STANDARDS.md`; evidence: `research/2026-09-25-panel-headcount-research.md`.
- **Is ONS's business unit the enterprise group?** If so, a subsidiary is sized as its parent. Ask ONS
  (labour.market@ons.gov.uk / vacancy.survey@ons.gov.uk); affects Faculty, Deliveroo, Contentful, Lever.
- **VACS02 divisions 45/46/47** — present as columns but with no series ID in the header row; work out their ONS identity from the file's other header rows before adding.
- **VACS02 `job openings rate` sheet** — inspect its columns, then decide whether to add it
  (a rate is a different `measure`; the schema already fits).
- **X06** — locate and inspect the file; only then add.
- **Vintage backfill** — do we ever want the 129-release revision history? Not until a feature
  needs it.
- **`qualifiers jsonb`** on `statistic_series` — add when the first survey-shaped source arrives.
- **Publisher-specified ONS attribution** — none found on the dataset page; the OGL default
  plus the named source is used. If ONS states a preferred wording, update `attribution_text`.
- **Crosswalk review** — the draft mapping rules need a human pass on the real tag list at
  implementation.
- **Second publisher** — which comes next (Eurostat SDMX is the natural test of the shared
  adapter) is a PM call; not decided here.

## Out of scope
- Narrative reports/articles (a later slice); scraping; any LLM extraction; a per-user data
  export; showing revision history to end users; the size-band cross-check; non-UK geography for
  Story 5.

---

## Implementation notes (2026-09-25) — what building it against the real thing found

**Deviations from the spec above, and why:**
1. **No `openpyxl`.** A dependency-free reader (`trusted_stats/xlsx_reader.py`, standard library only) is used instead — the ONS files are
   plain, it was proven on both real files, and it avoids a new dependency in the Railway build. The spec anticipated this option.
2. **Vintage rule refined.** `decide_vintage()`: a changed value is stored (`provisional` stays `provisional` while ONS still flags it,
   otherwise `revised`); an unchanged value is skipped — **including a repeated `(r)` flag on an unchanged value** (would otherwise be a
   new row each month); a provisional value confirmed at the same value *is* stored. ONS's own `(r)` flag maps to `revised`.
3. **Footnotes are per-series.** On VACS02's `levels` sheet, footnote 2 ("Not seasonally adjusted") applies to **Real estate and to
   Electricity/gas** (both stored `not_adjusted`); footnote 3 is a *coverage* note (Administrative and support services), not an adjustment
   note. VACS03's series are stored `seasonally_adjusted` on the strength of ONS's methodology page (the file is silent) with that source
   recorded in `definition_note`. (The spec's earlier "footnotes 2 and 3 mark series not adjusted" was a misreading of the second sheet.)
4. **Discovery/download.** Release discovery is the page-data JSON as specified, but the **file is downloaded from
   `https://www.ons.gov.uk/file?uri=<uri>/<file>`** — the bare path 404s. Found by the first live run (the offline fakes served any URL);
   now pinned by a test.
5. **A missing `STATISTICS_CONTACT` is a configuration error, not a failed run** — it propagates and records nothing, so it cannot start the
   24-hour cadence clock (found by the first live run).
6. **`statistics_ingestion_runs` cadence** counts every real run (including failed/rejected) but never a skipped one; a `--force` flag
   overrides the gate for a deliberate retry.
7. **Only `outcome` values actually recorded:** `new_release_ingested`, `no_new_release`, `rejected_validation`, `failed` (a skip is logged, not stored).

**Real-data findings that change what the cross-check can honestly say:**
- **72% of stored postings have no country recorded** (7,032 of 9,729 on 2026-09-25), and UK appears as both `GB` (587) and `UK` (70).
  The UK-located comparison therefore covers **657 roles** (`country IN ('GB','UK')`) and **states** how many roles it cannot place. This is a
  data-quality gap worth its own change request (country normalisation / recording), not something the cross-check papers over.
- **A group with no roles shows 0%**, not a missing bar: the platform side genuinely holds no UK role in Human health, Accommodation and food,
  Professional services or Administrative services. Only "Not placed in an industry group" has no ONS counterpart (`null`).

**What the live cross-check shows (2026-09-25, 657 UK-located roles; ONS Jun–Aug 2026):**
- *Industry* — roles we track: Information and communication **49%**, Financial and insurance **23%**, retail 4%, **24% not placed**;
  ONS: Human health and social work 17%, retail 13%, accommodation and food 10%, professional services 10%, administrative 7%, information and
  communication 5%, financial 4%.
- *Size* — roles we track: 250–2,499 **70%**, 2,500+ **24%**, 50–249 **7%**, **none under 50**; ONS: 1–9 13%, 10–49 14%, 50–249 15%,
  250–2,499 24%, 2,500+ 34%. (Size comparison is implemented in `statistics_crosscheck.size_mix()` but **not** yet in Story 5 — gated
  on the experience spec, `changes/2026-09-25-employer-size-standard-bands.md` Step 7.)
- These are context, not verdicts: different populations, mostly worldwide headcounts, possible group-level sizing at ONS.
