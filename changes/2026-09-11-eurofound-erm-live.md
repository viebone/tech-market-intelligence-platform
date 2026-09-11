---
id: eurofound-erm-live
date: 2026-09-11
trigger-type: stakeholder-request
change-type: api-change
outcome: understand-market-health-before-searching
status: in-progress
---

# Change Request: Eurofound ERM goes live — real EU/Norway employment-event coverage

## Signal
See: `research/2026-09-11-eurofound-erm-access-confirmed.md`

Raw trigger: "I need more data from Europe, what do you recommend?" — the platform's
employment-events pipeline had zero EU coverage (US via WARN Firehose/SEC EDGAR, UK via
Companies House). Eurofound ERM was already the #1-recommended EU source
(`research/2026-09-11-employment-event-data-sources.md`) but scaffolded, not live, blocked on
an unconfirmed access mechanism.

## Outcome
See: `outcomes/understand-market-health-before-searching.md`. Same outcome the original
employment-event ingestion change served — this closes its "Eurofound ERM real endpoint" item,
explicitly left open in `changes/2026-09-11-employment-event-ingestion.md`'s Remaining work.

## Change Type
`api-change` — activating an already-designed, already-registered adapter (real endpoint +
real field mapping replacing a placeholder), not a new feature. No new table, no new endpoint,
no new UI — `employment_events`, `GET /admin/employment-events`, the story, and the chat tool
all already handle "however many adapters are registered" generically (same precedent as US
WARN's per-state-scraper -> WARN Firehose revision and SEC EDGAR's addition, both same-day).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change — already covers employment risk broadly, not source-specific |
| Experience Spec | `design/market-health/experience.md` | no-change — Layoff Signal/Employment Risk story already source-agnostic |
| Backend Spec | `backend/specs/market-health/api.md` | update — Eurofound ERM adapter contract: real endpoint, real field mapping, real restructuring-type vocabulary, drop "access mechanism not yet confirmed"; External Dependencies row |
| Backend Implementation | `backend/src/employment_events/eurofound_erm.py`, `backend/src/sources/base.py` | update — real `fetch()`; extend shared `COUNTRY_NAME_TO_ISO2` with the missing EU/Norway entries (a real gap found while building this, not scope creep — without it most ERM country values would silently normalize to `NULL`) |

## Execution Plan

- [x] Step 1: Capture signal — `research/2026-09-11-eurofound-erm-access-confirmed.md`
- [x] Step 2: Update `backend/specs/market-health/api.md` — Eurofound ERM adapter contract + External Dependencies (manual edit)
- [x] Step 3: Implement — real `fetch()` in `eurofound_erm.py`, extend `COUNTRY_NAME_TO_ISO2`
- [x] Step 4: Verify against real live data before any production write (full CSV fetched, parsed, mapped — coverage/skip rates checked; found and fixed a real data quirk — 252 rows carry the literal string `"None"` for headcount, not an empty field)
- [x] Step 5: Ran real ingestion against production — 31,786 new rows inserted, re-run confirmed idempotent (0 new); `market_stories.build_employment_risk_overview()` sanity-checked against the new data (real EU company/country rankings — Bosch, Nestlé, Thales, Rheinmetall; Germany/France/Spain/Poland/Italy). Updated `backend/EMPLOYMENT_EVENTS.md` and `DATA_SOURCES.md` with real counts.
- [ ] Step 6: Commit, push, verify live (admin dashboard shows the new total + `eurofound_erm` row; weekly cron will no-op cleanly on next run since all rows are already seen)

## Decision Log
- 2026-09-11: Full-file refetch every run, not a trailing date window — the export endpoint is
  an unpaginated flat CSV with no observed rate limit, unlike WARN Firehose/SEC EDGAR (both
  genuinely rate/quota-constrained). `insert_new_events()`'s existing id-based dedupe already
  makes a full refetch safe and cheap; a window would only add complexity and risk missing a
  late-corrected historical row.
- 2026-09-11: 4 of 9 real restructuring types (Merger/Acquisition, Relocation, Reshoring,
  Outsourcing — 5.1% of rows) are skipped, not guessed onto the existing closed `event_type`
  set, because their direction is genuinely ambiguous or unconfirmed. See research file's Open
  Question for `Reshoring` specifically.
