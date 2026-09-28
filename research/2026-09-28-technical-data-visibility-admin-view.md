source: stakeholder-request
date: 2026-09-28

The trigger — the operator's own words, verbatim (second half of the same message that produced
`research/2026-09-28-data-insight-coverage-quality-admin-view.md`, which covers the first,
insight-coverage-and-quality request):

"Maybe 2 separate request, one is about the quality of the data and the insights that I can
provide, and the other is more technical. [...] the other is more technical: how many tables,
how much data; how many queries are open to mcp and to the front-end, etc etc.."

This is a distinct need from the insight-coverage one: not "where is the platform's analytical
coverage strong or weak" but "what does the platform's own data footprint and exposure surface
actually look like, structurally" — table/row counts, growth, and which queries/capabilities are
reachable from MCP vs. the frontend API vs. neither.

Related prior state pulled during triage of this same conversation:
- `ACCESS.md` (product root) — already the per-capability frontend/backend-API/MCP reachability
  matrix (built for Rule 12's MCP-exposure-review process) — likely the natural backing data for
  the "how many queries are open to MCP vs. frontend" part of this request, rather than something
  to build from scratch
- No existing admin view aggregates table/row counts across the platform's now-several storage
  categories (`raw_postings`/classifications, `employment_events`, `market_observations`/
  `skill_associations`, `statistic_series`/`statistic_observations`, feedback tables, MCP/account
  tables)
