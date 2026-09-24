source: user-feedback
date: 2026-09-23

> "when i look at the ingestion run i only see jobs from greenhouse, ashby, lever and workable... i thought we had other sournces"

> "i need a strategy to get for free job posting on usa, uk, and europe so that I can have more variety. I need more sources for the ingestion runs"

> "what is missing from the earlier tier 1 expansion?" → "yes please" (start the change request, Tier 1 only)

Context established in the same conversation (facts, not decisions):

- `/admin/runs` covers job postings only. Employment events and the IT Jobs Watch scraper have their
  own tables/admin views and are not part of that page.
- Live today: ~56 tracked companies (Greenhouse 22, Lever 6, Ashby 26, Workable 2), mostly
  venture-backed US SaaS plus the UK employer panel.
- The UK panel (`EMPLOYER_PANEL.md`) is exhausted: 21 of 36 candidates live; the other 15 are
  blocked by written vendor terms (Workday, Taleo, SmartRecruiters), bot-walled (NatWest, Softcat,
  Civil Service Jobs), or unresolved with no confirmed feed (Sainsbury's, BT, VodafoneThree, HSBC,
  Sage). Cuvva is tracked but currently returns 0 roles.
- No US or continental-EU stratified candidate list exists. The long-term target in
  `EMPLOYER_PANEL.md` is ~500 employers (75 large / 125 mid / 200 smaller / 100 small).
- Follow-up ideas discussed but explicitly NOT part of this signal's change: France Travail,
  Arbeitnow, Jobicy and USAJOBS adapters; Personio/Recruitee adapters; `source_type` and
  `retention` fields; asking DWP for Find a Job access. Each needs its own change request and
  live terms verification (Rule 13).

Related: `research/2026-09-18-uk-employer-panel-plan.md`, `research/2026-09-18-uk-employer-panel-v1.md`,
`research/2026-09-19-employer-panel-schema.md`, `research/2026-09-20-direct-employer-portal-check.md`.
