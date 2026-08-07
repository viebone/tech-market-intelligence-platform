---
id: adzuna-data-removal
date: 2026-08-05
trigger-type: stakeholder-request
change-type: technical-refactor
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Remove legacy Adzuna data from production

## Signal
See: `research/2026-08-05-adzuna-data-removal.md`

## Outcome
See: `outcomes/job-data-source-flexibility.md` — Adzuna's license termination (already the
trigger for `changes/2026-07-28-multi-source-job-data-ingestion.md`) is the same underlying
business constraint; this closes the loop by removing the data, not just the code path.

## Change Type
`technical-refactor` — data-only operation, no schema change, no code change, no user-facing
feature change. The `adzuna_client.py` adapter and its ingestion wiring were already removed
in the 2026-07-28 change; this removes the historical *data* that adapter produced, which
had been deliberately left in place at the time pending this exact decision.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | no-change — the existing Edge Case ("Insufficient data for a time range: Show what exists... 'Data available from [earliest date].'") already covers a shorter history gracefully; no new edge case needed |
| Backend Spec | `backend/specs/market-health/api.md` | no-change — no schema/model change, `source` was always documented as a free-text field; `"adzuna"` simply stops appearing as a value going forward |
| Backend Implementation | production database only (no source file changes) | data deletion, not a code change |

## Execution Plan

- [x] Step 1: Confirmed scope before acting — queried exact row counts (6,324 rows in each of
      `raw_postings` and `classifications`, matching 1:1 since 100% of legacy Adzuna postings
      had already been classified) and surfaced the historical-data trade-off to the user
      explicitly before proceeding.
- [x] Step 2: Deleted in a single atomic transaction (classifications first, respecting the
      foreign key, then raw_postings) — 6,324 rows removed from each table, verified 0
      remaining `source = 'adzuna'` rows afterward. Remaining data: 4,682 raw_postings
      (ashby: 1,600, greenhouse: 2,777, lever: 305), 3,662 classifications.
- [x] Step 3: Confirmed no further maintenance needed — table sizes (a few thousand rows,
      tens of MB) are far below any scale where manual `VACUUM` or similar intervention is
      warranted; Postgres autovacuum reclaims freed space automatically.

## Decision Log
- 2026-08-05: Classified `technical-refactor`, not `bug-fix` or `api-change` — nothing was
  broken and no contract changed; this is operational cleanup following a business decision
  (license risk) already established in an earlier change.
- 2026-08-05: Did not treat this as requiring a spec update — `raw_postings.source` was
  already documented as an open string, not a closed enum requiring `"adzuna"` to be listed;
  its absence going forward needs no spec change, same as adding a new source wouldn't
  require one.
- 2026-08-05: Explicitly surfaced the "Past 5 Years / All Time will show almost no history"
  consequence before deleting, rather than deleting first and explaining after — an
  irreversible action on production data warrants that ordering regardless of how confident
  the requester is.
