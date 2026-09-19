source: user-feedback
date: 2026-09-19

> "Employer size/sector/region schema" — chosen as the next step from a menu of options, per
> the original UK employer panel plan's own recommendation (`research/2026-09-18-uk-employer-panel-plan.md`):
> add `employer_size_band`/`employer_sector`/`employer_region` so panel-composition claims
> ("Product Designer vacancies across N continuously tracked employers, covering N industries
> and N regions") are defensible, not asserted.

## Scope decision
`employer_sector` already exists as `raw_postings.industry`, populated at ingestion time from
`industries.COMPANY_INDUSTRY` (added 2026-08-09) — no new work needed there. The two genuinely
new fields are `employer_size_band` and `employer_region`, mirroring that exact same mechanism
(`industry_for()` → a new `size_band_for()`/`region_for()`, called at insert time in
`raw_postings.py`, same "static curated lookup, NULL until tagged, never guessed" discipline).

## Honesty constraint on population
`employer_region` is populated confidently for every one of the 54 tracked companies — HQ
country/region is well-established public fact for all of them, low risk to state.
`employer_size_band` is populated **only** where there's a real, stated basis — the 19 UK panel
companies use the size bucket the user's own plan already assigned them (Large/Medium/Small-
Growth — user-supplied classification, not this assistant's guess); the original 35 companies
are left untagged (`NULL`) rather than guessed from general impression, since a wrong band
would undermine the exact credibility goal this feature exists to serve. Recorded as a real
follow-up research task, not silently skipped.
