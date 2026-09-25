# Test fixtures — real ONS Vacancy Survey files

`ons_vacs02_sep2026.xlsx` (VACS02, vacancies by industry) and `ons_vacs03_sep2026.xlsx` (VACS03, vacancies by
size of business) are the **real files ONS published on 2026-09-15**, downloaded once on 2026-09-24 from
ons.gov.uk, unmodified. They are fixtures for `test_trusted_stats.py` so the parser is tested against reality,
not a hand-made imitation (the lesson of `changes/2026-09-18-itjobswatch-llm-extraction.md`).

Expected values in the tests come from ONS's own published figures in these files (e.g. total vacancies
Jun–Aug 2026 = 702 thousand; by size 91 / 99 / 103 / 169 / 240 thousand).

Source: Office for National Statistics — Vacancy Survey. Contains public sector information licensed under the
Open Government Licence v3.0 (https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
