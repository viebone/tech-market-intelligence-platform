source: user-feedback
date: 2026-09-30

ok can you apply this to the existing even it passed and make sure the stats are accurate? it
may be good to show a chart of the number of companies tracked against number of roles tracked,
that is a separated chart for the opening question maybe?

## Context

Follow-on from `changes/2026-09-30-job-openings-trend-per-company-baseline.md` (same session).
That change fixed the Designer/Product Manager/Engineer job-openings trend chart, which had
shown an ascendant trend caused entirely by the `us-eu-employer-panel-expansion` change adding
56 → 170 tracked companies over 2026-09-24–2026-09-28, not real hiring growth.

The user's idea: a small, separate companion chart on Market Health showing tracked-companies
and tracked-roles counts over time, alongside (not merged into) the openings trend chart. This
would let anyone see at a glance when a bump in the openings trend lines up with a coverage
expansion rather than a real demand change — useful both for this incident and for the ~25
companies still held back from the panel expansion, and any future source/panel growth.

No new data needed — company-first-seen dates already exist in `raw_postings.fetched_at` /
`raw_postings.company`.
