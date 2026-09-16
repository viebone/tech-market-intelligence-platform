---
id: full-source-licensing-coverage
date: 2026-09-16
trigger-type: stakeholder-request
change-type: api-change, ux-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Full source licensing coverage (all 8 sources) + enforced traceability

## Signal
See: `research/2026-09-16-job-posting-source-licensing.md`

User: "we are missing lots of sources? what about the api access to level [Lever], greenhouse,
etc etc... we need all sources, and we need to specify which data are we getting from those and
we need to make sure that every bit of data can be tracked against this licenses."

## Outcome
See: `outcomes/job-data-source-flexibility.md` — same bucket as
`changes/2026-09-16-polite-scraping-adapters.md` and
`changes/2026-09-16-admin-licensing-visibility.md`; this is the third, closing piece of the same
licensing-visibility thread, kept as its own record for a legible audit trail rather than
reopening an already-`complete` change a third time.

## Change Type
`api-change` (registry schema gains `data_summary`; three new entries; a new enforced
traceability test) + `ux-change` (the admin Sources & Licensing view gains a "What we take"
column and now lists all 8 sources instead of 5).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | no-change — already amended for the broader theme |
| Experience Spec | `design/pipeline-visibility/experience.md` | no-change — additive column on an already-specced table, not a structural change to the view |
| Backend Spec | `backend/specs/scraped-data-sources/api.md`, `backend/specs/pipeline-visibility/api.md` | update (module-path + status-model wording already updated same day; `data_summary` field noted) |
| Backend Implementation | `backend/src/` | update — `source_licences.py` (3 new entries, `data_summary` field), `admin_main.py`/`licensing.html` (new column) |
| Plain-Language Overview | `OVERVIEW.md` | no-change — still an operator-only view, no new end-user capability |
| Polite Scraping Review | `DATA_SOURCES.md` + affected backend spec | not-applicable — no new scraped source; Greenhouse/Lever/Ashby are existing API adapters, not scraping |

## What this closes

1. **All 8 real data sources now registered**, not just the 5 from earlier today — Greenhouse,
   Lever, and Ashby (the job-posting ATS APIs) were missing entirely. Checked directly against
   each platform's own current documentation (not guessed): none publishes a formal data-reuse
   licence; Lever's own docs explicitly acknowledge third-party scraping ("these jobs may be
   scraped by third parties"); Greenhouse and Ashby neither address nor prohibit it. Recorded
   honestly as "no formal licence — nothing found restricting it," not manufactured into a
   licence that doesn't exist.
2. **"Which data are we getting" is now answered next to the licence itself** —
   `SourceLicence.data_summary`, a new field, shown as its own column in the admin view.
3. **"Every bit of data can be tracked against a licence" is now an enforced test, not a
   promise** — `backend/tests/test_source_licences.py` reads the real adapter registries
   (`ALL_SOURCE_ADAPTERS`, `ALL_EMPLOYMENT_EVENT_ADAPTERS`, `ALL_SCRAPED_SOURCE_ADAPTERS`) and
   fails if any adapter has no `source_licences.py` entry, or any entry has no matching adapter
   (catches both a forgotten registration and a stale leftover entry).
4. **Named, not solved**: `raw_postings`/`employment_events` don't carry a per-row `licence`
   snapshot the way the newer scraped tables do — traceability today means looking up
   `get_licence(row.source)`, not reading it off the row. Recorded in `LICENSING.md` §4 as a
   real limitation, not hidden. Also named: job-posting description text is the hiring company's
   own copyrighted content with no formal reuse licence anywhere — fine for today's internal
   classification/trend use, worth a fresh look the moment any feature ever displays a raw
   description verbatim to an end user.

## Execution Plan

- [x] Step 1: Signal captured — `research/2026-09-16-job-posting-source-licensing.md`
- [x] Step 2: Researched Greenhouse/Lever/Ashby's own current API documentation directly (not
  guessed) — `docs.greenhouse.io/job-board.html`, `github.com/lever/postings-api`,
  `developers.ashbyhq.com/docs/public-job-posting-api`
- [x] Step 3: Added `data_summary` field to `SourceLicence`; registered `greenhouse`, `lever`,
  `ashby` with real findings; backfilled `data_summary` for all 5 existing entries
- [x] Step 4: New `backend/tests/test_source_licences.py` — full-coverage traceability check,
  4 tests passing
- [x] Step 5: Updated `admin_main.py`/`licensing.html` — "What we take" column, all 8 sources
  verified rendering correctly via a real test-client request
- [x] Step 6: Updated `LICENSING.md` (full 8-source table, new open flag on job-posting content,
  §4 traceability-limitation note) and `backend/specs/*.md` module-path/field references

## Decision Log (continued — same-day correction to the gating mechanism)
- 2026-09-16: User corrected the use-gating design: *"we can switch on/off by sources. Just
  make sure that ingestions always work and that insights and other functionality always work
  unless we say license rejected. but in any case the ingestions can work until we say the
  opposite."* Replaced the automatic `confirmed`/`permits_commercial_use`/commercial-mode
  inference (built earlier the same day) with a single explicit `SourceLicence.rejected: bool`,
  default `False` — the only thing that gates use, set only by a human deliberately editing
  `source_licences.py`. `TMIP_COMMERCIAL_MODE` demoted to purely informational (a review
  reminder, no longer a live filter). Ingestion's independence from all of this — already
  correct — is unchanged and now stated even more plainly. Renamed the third `overall_status()`
  value from `"not_licensed"` to `"rejected"` throughout (code, tests, templates, docs) to match
  the user's own term. Rewrote the corresponding tests (old commercial-mode-driven blocking
  tests no longer describe real behaviour) — 29 tests passing, all verified against the real
  registry and a real admin-page request in both `TMIP_COMMERCIAL_MODE` states, confirming
  identical status output either way.

## Decision Log
- 2026-09-16: Recorded Greenhouse/Lever/Ashby as `confirmed=True` in the registry — meaning
  "the source's own current documentation was actually read," not "a formal reuse licence was
  found" (none exists for any of the three). Chose honesty about *what was checked* over forcing
  these into the same "confirmed licence variant" shape as CC/OGL/public-domain sources, which
  would have overstated the legal picture.
- 2026-09-16: Did not add a per-row licence snapshot to `raw_postings`/`employment_events` —
  `source` + the registry already gives full traceability without a schema migration; adding a
  stored snapshot is a real future option if a need for point-in-time licence history ever
  arises, not built speculatively now.
