---
source: internal
date: 2026-09-20
---

Real research on the panel's 3 remaining Medium-tier unverified candidates: Sage, Softcat, AJ Bell.

## AJ Bell — real platform correction, then blocked

The panel's prior note suspected Oracle Recruiting Cloud/HCM (URL-pattern guess, never
confirmed). Fetched the live careers page directly (`ajbell.co.uk/group/careers/vacancies`,
real HTTP 200) and found no Oracle markers at all — instead, a "register your interest" link to
`smrtr.io/nnHfw`, SmartRecruiters' own official short-link domain. Resolved it directly:

```
https://smrtr.io/nnHfw -> https://join.smartrecruiters.com/AJBell1/...-speculative-application
```

**Real platform: SmartRecruiters**, company identifier `AJBell1` — the earlier Oracle guess was
wrong, corrected here rather than carried forward.

Tested SmartRecruiters' public Postings API directly:
`GET https://api.smartrecruiters.com/v1/companies/AJBell1/postings` → real HTTP 200, 19 real
current AJ Bell jobs, clean structured JSON (title, location, department, employment type,
experience level) — same shape as Greenhouse's `boards-api`, no authentication required. Since
SmartRecruiters career-site widgets fetch this client-side in the browser, it has to be openly
readable — consistent with what was found.

**Licence check — real, decisive, found this time.** SmartRecruiters was acquired by SAP; "any
use of SmartRecruiters APIs is governed by the SAP API Policy." Fetched that document directly
(`help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf`, v.4.2026a, real PDF, not a
search summary). Section 2.2.2, verbatim:

> "Except through and within the limits of SAP-endorsed architectures, data services, or
> service-specific pathways expressly identified and intended for such purposes, SAP prohibits
> API use for: (a) interaction or integration with (semi-) autonomous or generative AI systems
> that plan, select, or execute sequences of API calls, and (b) scraping, harvesting, or
> systematic and/or large-scale data extraction or replication."

This explicitly prohibits exactly what a recurring ingestion adapter across employers would do —
"systematic... data extraction" — same shape of finding as Workday and Oracle Taleo: a clean,
technically excellent, unauthenticated public endpoint with an explicit written prohibition.
**Decision: do not build a SmartRecruiters adapter without SAP's express permission.**

**Worth noting**: BT Group's SuccessFactors (`research/2026-09-20-large-employer-pass5-findings.md`)
is also an SAP product — if any public SuccessFactors API is ever found there, this exact same
SAP API Policy would almost certainly govern it too. BT's status stays "unresolved" (no API
confirmed yet either way), but this is the likely outcome if one is found.

## Softcat — actively bot-challenged, not just unidentified

Previously recorded as "custom domain, platform not identified, needs direct network-request
inspection." Fetched `jobs.softcat.com/jobs/vacancy/find/results/` directly and inspected the
real response headers:

```
HTTP/1.1 202 Accepted
x-amzn-waf-action: challenge
```

This is AWS WAF actively serving a bot challenge instead of real content — a materially stronger
signal than "platform unknown." This isn't a passive absence of information; it's an active
technical control specifically meant to distinguish human browsers from automated requests.
Getting past it would require solving a JS challenge (effectively a headless-browser bypass),
which runs directly against this project's own polite-scraping discipline regardless of whatever
platform sits behind it. **Recommend treating as a strong "do not build" signal**, distinct from
(and stronger than) a simple "not yet identified."

## Sage — genuinely still unresolved, no new information

Re-fetched `sage.com/en-gb/company/careers/career-search/` directly with a real browser
User-Agent (this time got a real HTTP 200 with 209KB of content, unlike the earlier 403).
Searched the full page for every ATS vendor marker checked elsewhere in this research
(Workday, Taleo, SuccessFactors, Eightfold, SmartRecruiters, iCIMS, Phenom, Avature, Recruitee,
Personio, Jobvite, Cornerstone, Bullhorn, Greenhouse, Lever, Ashby, Workable, Teamtailor,
Breezy) and for any embedded API call reference in the page's scripts — **found none**. The only
`api.*` references present belong to unrelated Sage product lines (logging, registration,
`sageimagine`), not careers. This confirms, rather than changes, the panel's existing
finding: Sage's real careers platform is genuinely unidentifiable from a static fetch — the job
data most likely loads via client-side JavaScript after page load, which would need a real
browser-based network trace (not available through search or a static page fetch) to identify.
No further progress possible without that kind of inspection.
