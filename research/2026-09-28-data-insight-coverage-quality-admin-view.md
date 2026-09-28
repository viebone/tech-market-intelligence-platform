source: stakeholder-request
date: 2026-09-28

Prior turn (context, not the trigger itself): the operator asked for "a clear vision of the
sources that I am tracking, which companies on each source, the countries, what data belongs to
each source, company and country... which industries, which business areas.... I need to be able
to assess the quality of the data that I am capturing... what are the gaps."

The trigger — the operator's own follow-up, verbatim:

"yes, what I want in the admin is a clear picture of the data that I am capturing, I need a
summary page that reflects all of these . I want to be pragmatic. I want to understand the
coverage of the data and where I can provide stronger insights and what is weaker. And also I
need control over the data that I capture. Maybe 2 separate request, one is about the quality of
the data and the insights that I can provide, and the other is more technical. so about the
data: which countries I cover better, which ones are weaker; which company sizes I can provde
better insights, which are weaker; which sournces provide more data, which less; which business
areas I have more information, which i have less."

This file covers the first of the two requests the operator asked to split out — the
insight-coverage-and-quality one. See `research/2026-09-28-technical-data-visibility-admin-view.md`
for the second (technical/schema visibility) request, split from the same message.

Related prior research pulled during triage of this same conversation:
- `DATA_SOURCES.md` (product root) — the existing hand-maintained index of sources, adapters, and
  the 134-company tracked list with industry tags
- `backend/src/industries.py` — `COMPANY_INDUSTRY`, one flat industry string per company
- `backend/src/sources/base.py` — `COUNTRY_NAME_TO_ISO2` / `normalize_country()` — country is
  currently posting-level free text only, never a company attribute; Personio-sourced postings
  carry no country field at all (always NULL, never inferred)
- `backend/EMPLOYER_SIZE_STANDARDS.md` — `employer_size_band` exists per tracked company (cited
  headcount range, ONS band derived) but isn't cross-referenced against data volume/completeness
  anywhere today
