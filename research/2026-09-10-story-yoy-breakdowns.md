---
source: stakeholder-request
date: 2026-09-10
---

> ok now I would like to enrich the what we know about the market and use some of the
> information in the backend admin panel, some of the data that we display there, it may be
> relevant, for example the proportion of pm, engineer and design roles, the proportion on
> seniority, the proportion on track, the top 10 specializations... all of that with an
> explanation of what it means and very clearly shown the time frame. I would do this year on
> year, one year back nor more. now we don't have the data, but when we have ...

The admin overview (`/admin/`) already computes `classification_distribution` —
`{ role_category, level, track, specialization }` value/count lists — plus
`skill_group_distribution`. The stakeholder wants a consumer-facing version of the same
breakdowns in the "What we know about the market" story, each with:
- a plain-language sentence on what the proportion means,
- the exact time frame shown clearly,
- a **year-on-year** comparison: the current 12 months vs the 12 months a year earlier —
  no further back than one year.

Collection started 2026-08-03, so there is not yet a year of data. This is a spec that
anticipates the data: until a year-ago window exists, each block shows only the current
window and says the comparison isn't available yet.

Tension to resolve: the 2026-09-06 redesign deliberately kept the role-category split OUT of
the story ("the welcome carries inventory; the story carries substance") and the 2026-09-10
visual standard's checklist bans "welcome-inventory duplication". This change wants the split
(and more) back in the story — but as *year-on-year change*, not as a current snapshot.

Related: `research/2026-09-06-market-story-visual-and-dedup.md`,
`research/2026-09-10-story-visual-standard.md`.
