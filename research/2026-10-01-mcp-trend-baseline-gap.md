source: user-feedback
date: 2026-10-01

I want t oshow the evolution on the amount of data that we capture, companies tracked against
job post classified. that is the goal so that someone can understand the data. before doing
this, please update the mcp access to the refined trends in job, the reading I got from claude
made me feel the mcp access to the data wasn't throwing the new results

## Investigation (same session)

Confirmed a real, separate gap from `changes/2026-09-30-job-openings-trend-per-company-baseline.md`.
That fix only touched `market_openings.py::_fetch_counts()` — the dedicated
`/api/market-health/openings` endpoint behind the trend chart. It never touched
`market_query.py::query_market_data()` — a completely different function, used by:

- the MCP tool `get_job_demand` (`mcp_access/tools.py`) — what the user actually hit asking
  Claude a trend question through the MCP connection
- `/api/chat`'s Stage 1 owned-data query (`chat.py`) — so any chat trend question had the same
  gap
- `curated_answers.py`'s instant-answer path

`query_market_data` supports `group_by: [..., "month"]` for trend questions, but had **zero**
baseline exclusion of any kind — not even the old platform-wide-only version the openings chart
had before yesterday's fix. Confirmed in code (`market_query.py` lines ~106-165): no baseline
CTE, no exclusion WHERE clause, nothing. Worse than the bug just fixed: a month-grouped
`query_market_data` call during the `us-eu-employer-panel-expansion` window would show the full,
uncorrected bulk-load spike — exactly what the user experienced via Claude/MCP.

The backend spec itself (`backend/specs/market-health/api.md` line 1525) already claims this
tool "always excludes `role_category: 'other'` rows, **matching the trend-aggregation rule**" —
but that claim was only ever true for the `other`-exclusion half of the rule, never the
baseline-exclusion half. Spec overstated what the code actually did.
