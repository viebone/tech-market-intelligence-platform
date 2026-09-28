---
id: uk-gb-country-normalization-bug
date: 2026-09-28
trigger-type: bug
change-type: bug-fix
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Fix UK/GB country normalization bug

## Signal
See: `research/2026-09-28-uk-gb-country-normalization-bug.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — any country-scoped answer this
product gives (the openings chart's country breakdown, chat's location-specific answers) is
subtly wrong wherever the underlying `raw_postings.country` value is the colloquial `"UK"`
instead of the correct ISO 3166-1 alpha-2 code `"GB"` — the same country's postings silently
split into two buckets. Also relevant to `outcomes/pipeline-processing-visibility.md`, since this
was discovered through the new Data Coverage & Quality admin view, but the actual defect being
fixed is in shared ingestion-time normalization logic, not that admin view itself.

## Change Type
`bug-fix`

## Root Cause
**Code is wrong, spec is correct** — `backend/specs/market-health/api.md`'s Business Logic —
Location normalization section accurately describes what each adapter does (Ashby/Greenhouse/
Workable pass their raw location text through `normalize_country()`) and never claims that
function is bug-free. The bug is entirely inside `sources/base.py`'s `normalize_country()`: its
"already 2 letters → assume valid ISO-2, return as-is" shortcut runs *before* the
`COUNTRY_NAME_TO_ISO2` dict lookup, so the dict's own `"uk": "GB"` entry is unreachable for any
2-letter raw input — a raw `"UK"` (or `"uk"`) is returned verbatim instead of being mapped to the
real ISO code `"GB"`. Confirmed against live production data from two independent sources
(Ashby's `motorway`, Greenhouse's `ripple`) — see the research file for the exact raw values.

No spec update needed — going straight to implementation.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change — success criteria don't change, this restores data accuracy they already assume |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md`, `design/pipeline-visibility/experience.md` | no-change — no user-facing flow, interaction, or state changes; this is a silent data-correctness fix |
| Frontend Spec | n/a | no-change |
| Backend Spec | `backend/specs/market-health/api.md` | no-change — code is wrong, spec is correct (see Root Cause) |
| Frontend Implementation | `frontend/src/` | no-change |
| Backend Implementation | `backend/src/` | update — fix `normalize_country()`'s check order in `sources/base.py`; one-time backfill of existing `raw_postings` rows where `country = 'UK'` to `'GB'` |
| Plain-Language Overview | `OVERVIEW.md` | no-change — invisible, silent data-correctness fix; nothing a user would describe as a new or changed capability |
| MCP Access Review | `ACCESS.md` + MCP backend spec | not-applicable — no capability added or changed, `get_job_demand`'s existing `country` field just becomes more accurate |
| Polite Scraping Review | `DATA_SOURCES.md` + affected backend spec | not-applicable — no scraped source touched |
| Data Surface Review | data-story catalogue / admin dashboard / ad-hoc query layer | not-applicable — no new data category, a correctness fix to an existing field |

## Execution Plan

- [x] Step 1: Fix `normalize_country()` in `backend/src/sources/base.py` — check `COUNTRY_NAME_TO_ISO2` before the 2-letter passthrough shortcut (verified with unit checks: `UK`→`GB`, `uk`→`GB`, `United Kingdom`→`GB`, `GB`/`US`/`DE` unchanged)
- [x] Step 2: One-time backfill script `backend/src/backfill_country_normalization.py` (mirroring `backfill_employer_size_band.py`'s precedent) — generic re-derive-and-diff, not hardcoded to UK/GB; dry run confirmed exactly 176 rows before applying
- [x] Step 3: Ran the backfill against the live production database with `--apply` (176 rows updated, matching the dry run exactly) — verified directly: `raw_postings` now has zero `UK` rows and 977 `GB` rows (801 + 176); `raw_postings.get_coverage_summary()` (the Data Coverage & Quality view's own function) now returns one `GB` row, not two

## Decision Log
- 2026-09-28: Confirmed empirically (not guessed) against live production data before writing
  any fix — the exact raw values behind both Ashby's and Greenhouse's `"UK"` rows were pulled and
  inspected first.
- 2026-09-28: Lever's separate passthrough-without-`normalize_country()` behavior was
  investigated and ruled out as a current contributor (all its real data is already correctly
  `"GB"`) — noted as a real but lower-priority inconsistency, deliberately left out of this fix's
  scope to keep the change narrow to the confirmed defect.
- 2026-09-28: `raw_postings` is documented as immutable except for a narrow, explicit backfill
  exception already established for `employer_size_band` (a derived-metadata column, not
  `raw_response` itself). `country` is the same kind of derived-metadata column, so the same
  exception applies — this backfill is not a new precedent, it follows an existing one.
