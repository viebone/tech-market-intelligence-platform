---
source: internal
date: 2026-09-20
---

Continuing the 12 Large-employer panel candidates (Option 1 from the "what's next" menu,
`changes/2026-09-20-large-employer-ats-research.md` covered 5 of 12) — the remaining 7:
Sainsbury's, BT Group, VodafoneThree, Sky, BAE Systems, Rolls-Royce, Civil Service.

## Real platform identification (WebSearch + direct WebFetch content inspection, not guessed)

| Employer | Platform found | Evidence |
|---|---|---|
| Sainsbury's | **Oracle Recruiting Cloud / HCM** | `www.sainsburys.jobs/jobs` links to `https://hdhe.fa.em3.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX` — same platform family already suspected (not confirmed) for AJ Bell |
| BT Group | **SAP SuccessFactors** | `jobs.bt.com/BTGroup/` serves an image from `rmkcdn.successfactors.com`; cookie notice names "SAP as service provider" |
| VodafoneThree | **Attrax (acquired by Phenom)** | `jobs.three.co.uk/jobs` serves images from `attraxcdnprod1-....azurefd.net`; job reference format (`jid-####`) matches Attrax's known shape |
| Sky | **Oracle Taleo** (at least one instance) | `bskyb.taleo.net/careersection/bskyb_internal/jobsearch.ftl` — real Taleo career-section URL found via search. Sky's own privacy notice also names Workday, Avature, Cappfinity, and LaunchPad as ATS processors — plausibly different sub-brands/regions/hiring-stage tools, not one single platform. Taleo is the one confirmed by a real reachable URL. |
| BAE Systems | **Oracle Taleo** | `baesystems.taleo.net/careersection/2/jobsearch.ftl?lang=en` — real HTTP 200 (verified directly, not just found via search) |
| Rolls-Royce | **Workday** | `rollsroyce.wd3.myworkdayjobs.com/professional` (plus separate divisional tenants: `rrpowersystems`, and `rollsroycesmr.wd103.myworkdayjobs.com/RRSMR` for Small Modular Reactors) — same CXS-API platform already confirmed real for Barclays/AstraZeneca and already blocked on Workday's own ToS prohibition (`research/2026-09-20-workday-licence-check.md`). No new verification needed — same platform, same decision applies. |
| Civil Service | Still no official API | `civilservicejobs.service.gov.uk` remains HTML-only; only third-party commercial scraper products (Apify listings) exist, no first-party feed. Matches the panel's existing expectation that this needs a dedicated public-sector mechanism, not an ATS adapter. |

## A real, promising Taleo lead — found, not built

With Taleo now confirmed for 3 employers (Tesco, BAE Systems, Sky), checked whether Taleo career
sections expose any real API, since one adapter there would unlock 3 companies at once (the
whole point of this project's adapter-not-scraper architecture).

Direct requests against BAE Systems' instance:
- `GET .../careersection/2/jobsearch.ftl?lang=en` → real HTTP 200 (the HTML search page)
- `GET .../careersection/rest/jobboard/searchjobs?...` → HTTP 405 (Method Not Allowed) — the path
  exists, it just doesn't accept GET
- `POST .../careersection/rest/jobboard/searchjobs?...` with a guessed JSON body → HTTP 400 (Bad
  Request) — the endpoint is real and live, but the request body's actual required schema
  (correct `portal` id, `finder` object shape, etc.) isn't something to guess further at without
  Oracle's own API documentation

**Licence check attempted, inconclusive** — unlike Workday, no direct Oracle Taleo terms-of-use
document prohibiting scraping/automated access was found via search. Third-party commercial
scraper products for Taleo career sections exist openly (Apify listings), which is weak
supporting signal but not a substitute for actually reading Oracle's terms. **Treated the same as
Tesco's original Taleo finding: reachable, not confirmed permitted — do not build until this is
resolved, same bar as every other source in this project.**

## Outcome

Zero new companies added this pass (same as the prior 2026-09-20 pass) — but three real new
platforms identified (SuccessFactors, Attrax, and a second Oracle HCM sighting), one real
half-open technical lead (Taleo's REST endpoint) worth a future licence-focused follow-up, and
Rolls-Royce confirmed to fall under the existing Workday block rather than needing its own
separate decision.
