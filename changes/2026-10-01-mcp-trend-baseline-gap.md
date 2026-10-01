---
id: mcp-trend-baseline-gap
date: 2026-10-01
trigger-type: user-feedback
change-type: bug-fix
outcome: understand-market-health-before-searching
status: in-progress
---

# Change Request: query_market_data's month-trend grouping had no baseline exclusion at all

## Signal
See: `research/2026-10-01-mcp-trend-baseline-gap.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — same criterion as
`changes/2026-09-30-job-openings-trend-per-company-baseline.md`: "They can see the trends
clearly, how the hiring market numbers evolve through time." This is the same failure mode
reaching a second, separate surface.

## Change Type
`bug-fix`

## Root Cause

Yesterday's fix (`changes/2026-09-30-job-openings-trend-per-company-baseline.md`) only touched
`market_openings.py::_fetch_counts()`, the function behind the dedicated
`/api/market-health/openings` endpoint. `market_query.py::query_market_data()` is a completely
separate function — the general-purpose, model-callable query tool shared by three different
consumers:

- MCP tool `get_job_demand` (`mcp_access/tools.py`) — what the user hit directly
- `/api/chat`'s Stage 1 owned-data query (`chat.py`)
- `curated_answers.py`'s instant-answer path

It supports `group_by: [..., "month"]` for exactly the trend questions a user or an AI client
would ask ("how has Engineer demand changed recently"), but had **no baseline exclusion at
all** — not even the single-platform-wide version the openings chart had before yesterday. A
month-grouped query during the `us-eu-employer-panel-expansion` window (2026-09-24–2026-09-28)
would have returned the full, uncorrected bulk-load spike. This is strictly worse than the bug
just fixed, on a surface (MCP / chat) that reaches further than the one chart.

`backend/specs/market-health/api.md` (line 1525) already claimed this tool "matches the
trend-aggregation rule" — true only for the `role_category != 'other'` exclusion it shares;
never true for baseline exclusion, which the spec never actually specified for this function.
Spec overstated behavior that was never implemented — same "spec is incomplete" classification
as yesterday's fix.

## The Fix

Scoped to the `month` grouping only, not every call: `query_market_data` grouped by `month` now
joins the same per-company baseline CTE `market_openings.py` uses, excluding each company's own
first-observed day from the counted rows. **Every other grouping (role_category,
specialization, level, track, country alone) is unaffected** — those are stock questions ("how
many X are tracked right now"), where a bulk-loaded posting is still a real, currently-open
role and legitimately counts. `total_matching` also stays unfiltered regardless of `group_by`,
per its own existing docstring contract ("total postings matching every filter, independent of
group_by") — it's the stock total; the month-grouped rows are the organic-flow view. The gap
between the two (e.g. a much higher `total_matching` than the sum of monthly rows right after a
panel expansion) is itself informative, not something to paper over.

```sql
-- only when "month" is in group_by:
WITH company_baseline AS (
    SELECT company, min(fetched_at::date) AS day FROM raw_postings GROUP BY company
)
SELECT ..., count(*) AS count
FROM raw_postings rp
JOIN classifications c ON c.posting_id = rp.id
JOIN company_baseline cb ON cb.company IS NOT DISTINCT FROM rp.company
WHERE {existing filters} AND rp.fetched_at::date > cb.day
GROUP BY {group_by}
```

No backfill needed — live query, corrects immediately on deploy, same as yesterday's fix.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change |
| Design Foundations / IA / Visual Design | — | no-change |
| Experience Spec | `design/market-health/experience.md` | no-change — this is a data-correctness fix inside an already-specified tool, not a UX change |
| Backend Spec | `backend/specs/market-health/api.md` (query_market_data, ~line 1506-1540), `backend/specs/mcp-access/api.md` (`get_job_demand` wrapper) | update — both need the baseline-exclusion-on-month-grouping rule stated, since the "matching the trend-aggregation rule" claim was previously incomplete |
| Backend Implementation | `backend/src/market_query.py`, `backend/tests/` (regression test) | update |
| Frontend | — | no-change |
| Plain-Language Overview | `OVERVIEW.md` | no-change — bug-fix, no new capability |
| MCP Access Review | `ACCESS.md` | no-change — `get_job_demand`'s exposure decision is unchanged; only its underlying accuracy for month-grouped queries is corrected |
| Polite Scraping Review | — | not-applicable |
| Data Surface Review | — | not-applicable — no new data category |

## Execution Plan

- [x] ✅ Step 1: Root cause identified — `query_market_data` never implemented baseline exclusion
      for its `month` grouping, a gap yesterday's fix didn't reach (this document)
- [x] ✅ Step 2: Implemented the fix in `market_query.py::query_market_data()` — baseline CTE/join/
      WHERE added, scoped to `"month" in valid_group_by` only
- [x] ✅ Step 3: Updated `backend/specs/market-health/api.md` (`query_market_data` entry) and
      `backend/specs/mcp-access/api.md` (`get_job_demand` entry) with the baseline-on-`month`
      rule and the scoping rationale (stock vs. trend questions)
- [x] ✅ Step 4: Added `backend/tests/test_market_query_baseline.py` — synthetic fake-company rows
      in two past months; asserts the bulk-load month is unaffected, the later month gains
      exactly 1, **and** a `role_category`-only grouping (no `month`) counts all 3 rows
      immediately, confirming the fix doesn't leak into stock queries. Passed against live DB, 0
      leftover rows after cleanup
- [x] ✅ Step 5: Verified against live production data — `group_by=["month"]`, old vs. fixed:

  | Month | Old (no exclusion) | Fixed |
  |---|---|---|
  | 2026-08 | 3,072 | 766 |
  | 2026-09 | 4,196 | 1,060 |
  | 2026-10 (partial) | 100 | 100 |

  Worse than the chart's old bug, as expected — this function had never excluded even the
  platform's own original launch-day bulk load (2026-08-03), so **both** months were inflated,
  not just the panel-expansion month
- [x] ✅ Step 6: Called the real `get_job_demand` wrapper (`mcp_access/tools.py`) directly against
      production — returns the corrected `{2026-08: 766, 2026-09: 1060, 2026-10: 100}`,
      `total_matching: 7368` (correctly unfiltered, the stock total)
- [ ] Step 7: Commit, push, confirm deploy (auto-deploy is on for `api` — confirmed yesterday)

## Decision Log
- 2026-10-01: Classified `bug-fix`, not `api-change` — `query_market_data`'s contract (inputs,
  response shape) is unchanged; only the correctness of its `month`-grouped counts during a
  bulk-load window is corrected.
- 2026-10-01: Scoped the fix to the `month` grouping only, not every `query_market_data` call —
  a stock breakdown (role_category/specialization/etc. with no month dimension) is a different
  question ("what's tracked right now") from a trend breakdown ("what's new recently"), and
  only the latter is where a bulk load misrepresents the answer. Applying this everywhere would
  make simple counts (e.g. "how many Designer roles are tracked") quietly undercount real,
  currently-open postings — a different, worse bug.
- 2026-10-01: `total_matching` deliberately left unfiltered regardless of `group_by`, matching
  its own pre-existing documented contract ("independent of group_by") — changing that contract
  was out of scope and not what broke here.
