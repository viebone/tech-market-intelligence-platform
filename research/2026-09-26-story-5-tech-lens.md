source: stakeholder-request
date: 2026-09-26

Related: `research/2026-09-24-trusted-external-statistics-source-type.md` (the source type this story
reads), `research/2026-09-24-ons-licence-and-access-confirmation.md` (the real ONS files),
`changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md` (built Story 5). Overlaps in time with
`research/2026-09-26-data-story-chart-variety.md` (no change request yet) — both touch Story 5's
visual forms.

--- Message 1 (verbatim) ---

on story 5, from uk vancancies, we need to make it useful fo the tech market. can we extract from does trusted stats anything related to tech industry?

--- Message 2 (verbatim, approving the proposed option) ---

ok go ahead

--- Notes added when captured (not part of the raw input) ---

- "does trusted stats" = the ONS Vacancy Survey series already stored (VACS02 by industry, VACS03 by size).
- Message 2 approved **option 1** of four put to the PM: a "Tech and communications" block in Story 5,
  built only from data already ingested (no new ingestion). Not approved / not in scope: a separate
  tech-only story (advised against), ingesting the VACS02 "job openings rate" sheet (possible later
  step, its own change request), and other ONS datasets (online job adverts by occupation, workforce
  jobs by industry — unverified, never inspected).
- Evidence gathered before approval, read from the production database 2026-09-26 (`fetch_observations`,
  latest vintage, thousands of vacancies, three months to Aug of each year):

  | | 2019 | 2022 | 2023 | 2024 | 2025 | 2026 |
  |---|---|---|---|---|---|---|
  | SIC section J, Information and communication | 43 | 68 | 47 | 41 | 36 | 36 |
  | All UK vacancies (AP2Y) | 830 | 1,257 | 999 | 853 | 738 | 702 |
  | J share of all vacancies | 5.2% | 5.4% | 4.7% | 4.8% | 4.9% | 5.1% |

  J's own peak: 78k in Apr-Jun 2022. Section M (Professional, scientific and technical) is 69k now
  (128k in Jun-Aug 2022) — engineering/R&D sits there, not in J.
- Known limits of the data, to be stated on the page: section J is broader than tech (telecoms,
  publishing, film/TV/broadcasting, plus computer programming SIC 62 and information services SIC 63);
  ONS publishes whole thousands, so a series this small carries about ±1.4% rounding noise; the survey
  excludes employment agencies (SIC division 78), which is where a lot of recruitment sits.
