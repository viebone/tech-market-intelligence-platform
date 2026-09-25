---
id: uk-lmi-and-ons-vacancy-sources
date: 2026-09-24
trigger-type: market-signal
change-type: new-feature
outcome: job-data-source-flexibility
status: in-progress
---

# Change Request: Trusted external statistics — a new source type, first source ONS vacancies

(Originally "UK vacancy sources — LMI for All and ONS". Retitled scope 2026-09-24 after the PM
widened Part B into a new source type, then again — same day — to cover the data story, MCP
access, admin visibility, and licensing for it. Slug kept so the audit trail stays one file.)

## Signal
- `research/2026-09-24-uk-lmi-for-all-and-ons-vacancy-sources.md` — the original LMI/ONS pitch
- `research/2026-09-24-lmi-for-all-vacancy-feed-verification.md` — verification of it
- `research/2026-09-24-trusted-external-statistics-source-type.md` — PM go + widened scope
- `research/2026-09-24-ons-licence-and-access-confirmation.md` — ONS licence + real-file findings
- PM direction (chat, 2026-09-24): standardise and store this type together; then "document
  everything, save the license, prepare a data story for this type of stats, the MCP access and
  admin space, licensing, etc."

## Outcome
See: `outcomes/job-data-source-flexibility.md`. Success criteria **updated 2026-09-24** (new
bullet: trusted external statistics source type, always names its publisher, cross-check is
context not proof). Related: `outcomes/ai-reasoning-transparency.md` (provenance),
`outcomes/understand-market-health-before-searching.md`.

## Change Type
`new-feature` — a new source *type* plus its first consumer surfaces (story, MCP tool, admin
views). **This CR now covers specs and documentation; implementation is a separate, later step
(see Execution Plan) and has not been done.**

## Triage result

**Part A — LMI for All / Find a Job vacancy adapter → deferred, not building.** LMI for All is
past its own announced end-of-life; live vacancy searches returned empty; operator asks people
not to bulk-download; postings' licence unconfirmed; Find a Job is Adzuna-operated.
Detail: `research/2026-09-24-lmi-for-all-vacancy-feed-verification.md`.

**Part B — Trusted external statistics → GO (PM, 2026-09-24).** Market analysis and statistics
from trusted institutions (governments/statistical offices, intergovernmental bodies, other
well-recognised organisations), for insight beyond what the platform captures and for
cross-checking, always naming the source. First source: ONS Vacancy Survey (VACS02, VACS03).

### Design decisions (carried into the specs; PM may overrule)
1. **Standardise the container and the provenance, keep the source-specific code at the edge.**
   One long-format store for all trusted statistics (series + observations + releases). One
   small adapter per publisher format (a generic SDMX adapter can later cover
   OECD/Eurostat/ILO/ECB/IMF by config). Dimensions keep native code systems; crosswalks to our
   own taxonomy are built per cross-check, never forced at ingestion. Meaning across
   publishers is never harmonised.
2. **Own category** — supersedes the 2026-09-16 note in `DATA_SOURCES.md` §3b that ONS would be
   a `source` value in `market_observations`.
3. **Statistics first; narrative reports later** (the existing planned "Research / reports /
   articles" row keeps its own slice).
4. **Trust bar per publisher, registered in code** (named publisher, published methodology,
   citable URL, reuse terms read off the publisher's own page). Unconfirmed reuse terms → loud
   flag, never hidden, never block ingestion (existing `LICENSING.md` discipline).
5. **"Always naming the source" is structural** — a read function cannot return a value without
   its series (publisher, dataset, URL, release date, licence, attribution).
6. **A cross-check is context, not proof.** Never a score, a diff, or a verdict.
7. **Revisions are kept** — statistics get revised; each release is a vintage.
8. **No LLM in the ingestion path** for structured statistics — deterministic parse.
9. **Story decision (data-surface-review 2a): a new Story 5, not an extension of Story 3.**
   Story 3 is one specialist site's role/skill ranking for a curated IT role set and explicitly
   never blends with platform numbers; ONS is an economy-wide vacancy estimate by industry and
   size. Different fact, different publisher, different question — extending Story 3 would
   mix two populations under one heading.
10. **Cross-check scope, decided from real data:** industry mix can be cross-checked honestly
    through a small curated crosswalk (our industry tags → SIC 2007 sections). **Size-band
    cross-check is deferred**: our employer size bands (Large 5,000+, Medium 500–5,000,
    Small/Growth 50–500, Startup <50) do not line up with ONS's (1–9, 10–49, 50–249,
    250–2,499, 2,500+ employed) — comparing them would fabricate a match. Follow-up: record an
    ONS-compatible band alongside our own from the headcount research already done.
11. **The seams that make this work were checked against real files 2026-09-24**: ONS's
    page-data JSON (`…/current/data`) lists the current file and the full release history
    (129 releases for VACS03, each addressable — so vintages can be backfilled); its
    `description.releaseDate` is stale (2016) and must not be used; VACS02/VACS03 headers carry
    stable ONS series IDs (e.g. `AP2Y`, `ALY5`) used as natural keys.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | **update — done** |
| Design Foundations | `design/foundations.md` | no-change — provenance principle + "data without provenance" anti-pattern already cover it |
| Information Architecture | `design/information-architecture.md` | no-change — a new story appears in the Task Panel via the catalogue with no IA edit (catalogue rule); admin is outside the IA by prior decision |
| Visual Design | `design/visual-design.md` | update — add the two-source comparison chart to the Data Story visual vocabulary (no new tokens) |
| Experience Spec | `design/market-health/data-stories.md` | **update — Story 5 + catalogue amendments** |
| Experience Spec (admin) | `design/pipeline-visibility/experience.md` | update — new admin views, nav entries |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — Story 5 renderer + one new shared chart component |
| Backend Spec | `backend/specs/trusted-statistics/api.md` | **create** |
| Backend Spec (stories/chat) | `backend/specs/market-health/api.md` | update — Story 5 build function + `query_trusted_statistics_data` chat tool |
| Backend Spec (admin) | `backend/specs/pipeline-visibility/api.md` | update — new admin routes |
| Backend Spec (MCP) | `backend/specs/mcp-access/api.md` + `ACCESS.md` | update — new tool + decisions (MCP Access Review) |
| Frontend / Backend Implementation | `frontend/src/`, `backend/src/` | **no-change in this CR's spec phase** — implementation is Steps 8–9 |
| Plain-Language Overview | `OVERVIEW.md` | update **when Story 5 ships** (Step 10) — a user notices nothing until then |
| Docs | `DATA_SOURCES.md`, `LICENSING.md`, `backend/TRUSTED_STATISTICS.md` (new), product `CLAUDE.md` | update / create |
| Polite Scraping Review | — | not-applicable — ONS is fetched via its own page-data JSON and published dataset files, no HTML parsed; recorded in the backend spec |
| Data Surface Review | — | **run — recorded below** |

## Data Surface Review (recorded 2026-09-24, per `/data-surface-review`)
- **New category:** `statistic_series` / `statistic_observations` / `statistic_releases` — external
  published statistics, first source ONS Vacancy Survey.
- **(a) Story coverage → add a new Story 5**, not extend Story 3 (decision 9 above).
- **(b) Admin visibility → needed and specified:** Trusted Statistics (list + detail with
  vintage history) and Statistics Sources (flat: registry, cadence, next release).
- **(c) MCP → decided: exposed** as `get_trusted_statistics` (see `ACCESS.md`), not left open.
- **(d) Ad-hoc query path → gap named and closed in spec:** new `query_trusted_statistics_data`
  in `market_query.py`, registered as a chat tool; MCP wraps the same function.
- **Lag statement:** until the first ONS ingestion runs, Story 5 and the admin views show their
  honest "not collected yet" state; after that, new figures appear on ONS's monthly release
  (next: 20 Oct 2026). This is expected lag, stated in the story's own no-data state — not a
  defect.

## Execution Plan

- ✅ Step 0: PM go — 2026-09-24
- ✅ Step 1: Confirm ONS licence — OGL v3.0, read off ons.gov.uk and the National Archives, 2026-09-24
- ✅ Step 1b: Update `outcomes/job-data-source-flexibility.md`
- ✅ Step 1c: Inspect the real ONS files/endpoints (VACS02, VACS03, page-data JSON) so the spec is written against reality
- ✅ Step 2: `/new-backend-spec` → `backend/specs/trusted-statistics/api.md` (status `draft`) — incl. MCP Access Review, Data Surface Review reference, polite-scraping not-applicable note, paper-test against two other publisher shapes
- ✅ Step 3: Experience: Story 5 in `design/market-health/data-stories.md` (+ catalogue-rule amendments; `data-legibility` and `end-user-content` checks applied) and the admin experience (`design/pipeline-visibility/experience.md` step 11 + nav)
- ✅ Step 4: `design/visual-design.md` v2.0 — Two-series comparison + official-statistic year-on-year variant (no new tokens)
- ✅ Step 5: Consumer backend specs — `market-health/api.md` (Story 5 contract, chat tool), `pipeline-visibility/api.md` (3 admin routes), `mcp-access/api.md` (`get_trusted_statistics`, `get_taxonomy` extension, not-a-tool decisions) + `ACCESS.md`
- ✅ Step 6: Frontend spec — Story 5 section in `frontend/specs/market-health/architecture.md`
- ✅ Step 7: Docs — `DATA_SOURCES.md` (§2 row, §3b note superseded, new §3c, §7, §8), `LICENSING.md` (ONS confirmed row in a separate "not yet registered" table + OGL exclusions), `backend/TRUSTED_STATISTICS.md` (new), product `CLAUDE.md` status + key constraints, `ONBOARDING.md`
- ✅ Step 8 (2026-09-25): `/implement-backend` — built, 49 offline tests, **verified live against production data and ONS's own figures**.  Registers `SOURCE_LICENCES["ons_vacancy_survey"]` and `TRUSTED_PUBLISHERS` in the same commit as the adapter
- ✅ Step 9 (2026-09-25): `/implement-frontend` — Story 5 built (see the frontend spec's implementation notes); build clean; verified by server-side render against the live story; **charts not visually checked in a browser**
- [ ] Step 10: Update `OVERVIEW.md` when Story 5 ships; run the ONS ingestion against the real files and verify stored latest values against ONS's own published figures

**Status stays `in-progress`**: the spec and documentation phase is complete; implementation and
`OVERVIEW.md` remain. Nothing in `backend/src/` or `frontend/src/` has been touched.

## Decision Log
- 2026-09-24: Signal maps to `job-data-source-flexibility`. Verified against primary sources
  before triage; LMI for All vacancy feed dead/being wound down → Part A deferred.
- 2026-09-24: PM confirmed Part B and widened it to a new source type; then asked for
  standardisation ("stored together… or custom for each source?") — answer: standardised
  container + provenance, small per-source adapter at the edge (design decision 1).
- 2026-09-24: PM asked for the data story, MCP access, admin space, licensing and full
  documentation. Scope of this CR widened accordingly; implementation deliberately kept out
  until the specs are reviewed.
- 2026-09-24: Story 5 rather than extending Story 3, and size-band cross-check deferred — both
  decided from the real data (decisions 9 and 10), not assumed.
- 2026-09-24: Real ONS files were inspected before the spec was written (VACS02, VACS03, the page-data JSON, robots.txt — five direct requests, recorded honestly in the research file). Findings changed the spec: series IDs as natural keys, `releaseDate` unusable, label hyphenation, divisions 45/46/47 without IDs (deferred), provisional flag → vintages.
- 2026-09-25: **Step 8 implemented (PM go: "yes to all").** Built: `trusted_stats/` (base, registry, sic, crosswalks, xlsx_reader, ons_vacancy), `statistics_storage.py`, `statistics_crosscheck.py`, `ingest_trusted_statistics.py`, `query_trusted_statistics_data`, Story 5 backend (`uk-vacancies-official`), chat tool, MCP tool `get_trusted_statistics` + `get_taxonomy` extension, admin views `/admin/statistics`, `/admin/statistics/{id}`, `/admin/statistics-sources`, ONS licence registered in `source_licences.py`, `test_trusted_stats.py` (49 tests, offline, real ONS fixtures). First live run ingested the Sep 2026 release: 25 series, 7,575 figures; latest values match ONS (702k total; 91/99/103/169/240 by size); re-run downloads nothing; cadence gate makes no request. **Two bugs only the live run could find, both fixed and pinned by tests:** wrong file-download URL (`/file?uri=`), and a missing contact being recorded as a run. Full deviations and findings: the spec's "Implementation notes".
- 2026-09-25: **Step 9 implemented** (PM go: "yes please"). `UkVacanciesStoryMessage`, generic `SourceAttribution`, `SourceComparisonBars`, `YearOnYearGroupedBars` `mode="level"`, `RankedBarList` `valueLabel`. A server-side render of the real component against the live production story found four real problems, all fixed at the source and pinned by backend tests: SIC codes and "QMI" in visible copy (now plain words), a raw ISO date and "Jun-Aug" in the legend (now "25 Sep 2026" and "three months to August 2026"), a duplicated empty-state message, and "three months to ." in empty-state subtitles.
- 2026-09-25: **Still NOT done:** committing and deploying (backend + frontend are now safe to ship together — the earlier warning about deploying the backend first no longer applies once both go out); a browser check of the two chart blocks; a scheduled Railway service (config file committed, service not created — needs the dashboard flow and your `STATISTICS_CONTACT`); deployment of this code (uncommitted; the size-band commit is the only thing deployed today); `OVERVIEW.md` (Step 10, updates when Story 5 is user-visible).
- 2026-09-25: **Disclosure:** earlier in this session my direct requests to ONS (research on 2026-09-24/25) carried the operator's email address in the User-Agent, contrary to the instruction not to send it to third-party services unless asked. The first live ingestion run used a project URL as the identifying contact instead. The operator should set `STATISTICS_CONTACT` to the contact they want ONS to see.
- 2026-09-25: Reading ONS's methodology page (QMI) corrected three points in the specs above:
  the survey covers **Great Britain** and is weighted up to the UK (coverage note, Story 5
  qualifier); the smallest size band is "2 to 9" in the methodology but "1 - 9" in the file
  (modelled, not surveyed); and the by-size series **is** described as seasonally adjusted by
  ONS's methodology though not in the file (stored `seasonally_adjusted`, source noted — not `unknown`).
  Specs corrected: `backend/specs/trusted-statistics/api.md`, `backend/specs/market-health/api.md`,
  `design/market-health/data-stories.md`, `backend/TRUSTED_STATISTICS.md`, and an appendix in
  `research/2026-09-24-ons-licence-and-access-confirmation.md`. Company-size follow-up is its own
  change request: `changes/2026-09-25-employer-size-standard-bands.md`.
- 2026-09-24: **Do not add the ONS entry to `source_licences.py` yet.** `test_source_licences.py`
  fails the build on a registered licence with no matching adapter, so the entry is specified
  (exact contents in the backend spec) and registers in the same commit as the adapter.
- 2026-09-24: **Process slip, recorded honestly:** the outcome edit (Step 1b) was made a moment
  *before* an earlier revision of this change request listed it. Content unaffected; noted so
  the audit trail matches what happened.
