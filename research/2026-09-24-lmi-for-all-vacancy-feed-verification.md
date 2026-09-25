source: internal
date: 2026-09-24

# Verification of the LMI for All / Find a Job / ONS claims

Checked at triage against the sources' own pages and the live API, not against the signal's
say-so. Companion to `research/2026-09-24-uk-lmi-for-all-and-ons-vacancy-sources.md`.

## 1. LMI for All is being wound down — the signal's "continuously updated" no longer holds

- lmiforall.org.uk's own homepage carries this notice (read directly, 2026-09-24): *"At the end
  of 2024 the data available from LMI for All will no longer be updated. Access to LMI for All,
  including the API, will continue to be available until the end of October 2025."*
- Today is 2026-09-24 — nearly a year past the stated access end date. The API is still
  answering, but the operator has said it is no longer maintained and has no committed life.
- The live-vacancies documentation page (`/developers/data-documentation/vacancies-2/`) still
  describes the feed in the present tense ("at least a daily basis") and carries no closure
  notice — it was simply not updated. The notice above is the more authoritative statement.

## 2. The vacancy endpoint returns nothing useful

Live probes of `api.lmiforall.org.uk/api/v1/vacancies/search`, 2026-09-24:

| Query | Result |
|---|---|
| `developer`, `nurse`, `teacher`, `software` | HTTP 200, empty list `[]` |
| `engineer` (repeat, after a pause) | HTTP 200, empty list `[]` |
| `driver` (first attempt) | A single pseudo-record titled **"Too Many Requests"**: *"We are currently experiencing occasional, very large spikes of bulk vacancy download traffic, which has put considerable strain on the backend systems of our vacancy partners (Find A Job)… we have had to put in a rate limit on vacancy queries. You may query vacancies once eve…"* (message truncated in my read; the exact interval was not captured) |
| `driver` (repeat) | HTTP 200, empty list `[]` |

Other endpoints are alive but stale: `soc/search` answers; `ashe/estimatePay?soc=2136` returns
2020 and 2022 pay points only (latest year 2022 — consistent with "no longer updated").

Two things follow: (a) the vacancy feed is empty or effectively dead for every ordinary keyword
tried; (b) the operator has explicitly asked people not to bulk-download vacancies because it
strains Find a Job, and rate-limits it — a bulk connector is exactly the behaviour being
discouraged. This session made about 8 single-result probe calls to the vacancy endpoint, one of
which hit the rate-limit notice; no data was stored.

## 3. Licence — still unconfirmed for the vacancy content

- LMI for All's own FAQ (`/questions-and-answers/`) states: *"LMI for All is licensed under a UK
  Open Government license"*, suggested attribution *"Data powered by LMI for All."* That is the
  platform's licence over its data as a whole.
- The FAQ also says the vacancy data is *"supplied to us directly by the Findajob, provided by
  the Department for Work and Pensions"*, and the vacancies docs page says the feed is operated
  by **Adzuna on behalf of DWP**, and makes no explicit open-licence statement for it (it
  references UK data-protection law only).
- So: an OGL claim exists at the LMI for All level, but nothing read so far confirms DWP's or
  Adzuna's *own* terms for the underlying postings. The signal's own correction stands — this is
  **not confirmed**. A search-engine snippet claiming OGL applies to Find a Job vacancies is a
  third-party summary, not DWP, and was not relied on. A FOI thread on scraping Find a Job
  (whatdotheyknow.com) exists but returned HTTP 403 and was not read.

## 4. Overlap with a source this product deliberately retired

Find a Job is operated by Adzuna. This product retired Adzuna as a paid source
(`changes/2026-08-05-adzuna-data-removal.md`). Whether the LMI-exposed Find a Job feed is
functionally an Adzuna-sourced feed (and what that means for the product's earlier data-removal
decision and any Adzuna terms) is unresolved and should be answered before any vacancy adapter.

## 5. ONS side — the claim holds

The ONS Vacancy Survey (a statutory monthly business survey; excludes employment agencies and
agriculture/forestry/fishing) publishes, per ONS's own dataset pages:
- **VACS02** — Vacancies by industry (SIC 2007)
- **VACS03** — Vacancies by size of business
- **X06** — single-month vacancies by industry and size of business, not seasonally adjusted
  (not designated national statistics)
VACS01–03 three-month averages carry accredited official statistics status. These are
aggregate estimates, not postings. ONS licence was **not** read directly this pass (ONS content
is normally Open Government Licence, but that is an assumption until read off ons.gov.uk).
Fit with the existing model: aggregate vacancy counts by an entity (industry / size band) over a
period is the same shape as the `market_observations` benchmark category
(`DATA_SOURCES.md` §2), not a new shape of fact. Precedent to weigh: the earlier ONS HR1
integration was descoped because it was macro-only and did not fit `EmploymentEvent` — that
reasoning does not carry over, since benchmark datasets are explicitly aggregate.
