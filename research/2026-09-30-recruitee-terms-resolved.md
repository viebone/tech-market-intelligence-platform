source: stakeholder-request
date: 2026-09-30

User: "recruitees terms" — resolving the grey area flagged since 2026-09-26 (`changes/2026-09-26-personio-adapter.md`): "Recruitee's official docs say its Careers Site API needs a token, so its unauthenticated endpoint is a permission grey area."

## The endpoint

`GET https://{company}.recruitee.com/api/offers/` — confirmed live 2026-09-26 (real data for
`bunq`), re-confirmed today. No credentials.

## What Recruitee's own documentation actually says (read directly, not summarized)

**Recruitee's support FAQ** (`support.recruitee.com/en/articles/8213076-faq-api`) documents
three public feed URLs by name, under "How can I get the company's XML feed?" — a section
entirely separate from the API-token instructions above it:
- Formatted XML: `https://{yourcompany}.recruitee.com/api/feeds/offers.xml`
- Raw XML: `https://{yourcompany}.recruitee.com/api/offers.xml`
- **JSON: `https://{yourcompany}.recruitee.com/api/offers`** — the exact endpoint probed

No token requirement is mentioned for these. The token/authentication section immediately above
is a different topic (managing candidates and job postings via the authenticated API,
permissioned by the creating user's Hiring role).

**Recruitee's support article on scraping**
(`support.recruitee.com/en/articles/1066225-prevent-job-boards-from-scraping-your-jobs`) states
outright: *"Can Tellent Recruitee block a job board from scraping our careers site? **No.** A
public careers site can be crawled by anyone, and we can't stop a third party from doing so."*
Third-party reads of published job data are treated as an accepted, un-preventable reality, not
a violation to stop.

**The Careers Site API intro** (`docs.recruitee.com/reference/intro-to-careers-site-api`) states
its common usage is exactly this: *"Common usage of this API would be, for example, to display a
list of job offers or implement the application form on your custom website."*

## The actual legal document — Recruitee API Terms and Conditions v2022.1.0

Downloaded and read in full (`recruitee.com` → HubSpot-hosted PDF, 8 pages, last modified
2022-05-28). The decisive clause is **Section 1.1**:

> "These API Terms will solely govern any **Integration**... **that is offered by you to third
> parties**, that is intended by you to be offered to third parties or that is listed on the
> marketplace of Recruitee... **Other uses of the Recruitee SaaS, for example integrations or
> interconnections that you solely use internally (within your company) and that are solely
> intended to benefit your company, will be governed by the Recruitee Terms**" (the general ToS
> at recruitee.com/terms, not this document).

This document's Section 2.6.5 ("You may not... copy, scrape or export data in bulk from the
Recruitee SaaS") is real and would matter *if* it applied — but by the document's own scope
clause, it governs building an **Integration offered to third parties** (an app other Recruitee
customers install, potentially on Recruitee's Marketplace), not internal consumption of the
public job feed for one's own product. This platform is not building or offering a Recruitee
Integration; it is reading a company's own published, public job listing, same as every other
ATS adapter here.

## Conclusion

**Cleared — same confidence tier as Workable, Lever, and Personio.** A documented, credential-
free public feed (named by Recruitee's own docs), an explicit "third-party crawling can't be
stopped" acknowledgment, and the one restrictive clause found (bulk scraping, in the API Terms)
scoped by its own text to a different use case (registered third-party Integrations) than this
platform's. No formal data-reuse licence exists — same honest "no licence, nothing found
restricting this use" finding as every other ATS adapter's registry entry.

**Not built here** — this closes the terms question only, per the panel CR's own scoping
("New adapters:... Recruitee, others" listed as out of scope, needing "live terms verification
per Rule 13 before any code"). The adapter itself (feed shape, real-board content check,
`sources/recruitee.py`, licence registry entry, seed company list) is a separate change request,
same as Personio's own two-step process (terms first, then build).
