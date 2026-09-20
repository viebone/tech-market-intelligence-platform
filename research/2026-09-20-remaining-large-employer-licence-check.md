---
source: internal
date: 2026-09-20
---

Follow-up licence research on the 4 Large-employer platforms identified in pass 5 that hadn't
been checked yet: Sainsbury's (Oracle Recruiting Cloud/HCM), BT Group (SAP SuccessFactors),
VodafoneThree (Attrax/Phenom), HSBC (Eightfold.ai).

## A materially different shape than the Oracle Taleo / Workday cases

Both Taleo and Workday career sections live entirely on the vendor's own domain
(`{tenant}.taleo.net`, `{tenant}.wd{N}.myworkdayjobs.com`) — unambiguous: whoever operates that
domain, their terms apply. These 4 are different: the visible domain and every visible legal
link (privacy notice, cookie policy) belong to the **employer** (`jobs.bt.com`, `jobs.three.co.uk`,
`hsbc.eightfold.ai`'s own UI has `hide_eightfold_branding: true` set, `sainsburys.jobs`), not the
platform vendor. Concretely for HSBC: fetched the live careers page directly — only HSBC's own
privacy/cookie/accessibility links appear; no Eightfold-branded terms link is shown to a visitor
at all.

**Attempted to find each vendor's own applicable Terms of Use directly** (same standard as the
Oracle/Workday checks): no cleanly-applicable, directly-fetchable document was found for any of
the 4. Eightfold's likely general Terms of Use (quoted via a search summary as prohibiting "any
robot, spider, or other automatic device, process, or means to access the Website... without our
prior written consent") could not be independently verified by a direct fetch — both guessed
URLs (`/terms-of-use/`, `/terms-of-service/`) 404'd, and the eightfold.ai homepage footer only
links a Privacy Notice, no general Terms of Use. This is recorded honestly as **not verified**,
not treated as confirmed the way Oracle's and Workday's quotes were (both fetched directly, with
a visible revision date).

## robots.txt — real, checked directly, not assumed

Unlike the ToS question, this is unambiguous and free to check:

| Employer | robots.txt (fetched directly) |
|---|---|
| Sainsbury's | `Disallow:` empty (fully open) + explicit `Crawl-delay: 10` — a real, self-declared pacing signal |
| HSBC | Default `Disallow: /`, but `/careers`, `/careerhub/explore/jobs`, `/api/career_hub`, `/api/apply` explicitly `Allow`ed |
| BT Group | Only disallows account/subscribe/error/preapply paths — job search/listing paths are not disallowed |
| VodafoneThree | `Allow: /` broadly, but **`Disallow: /jobs?*`** — explicitly blocks the query-string job-search-results paths, the one clear negative signal of the four |

## Conclusion — genuinely unresolved, not a clean call either way

None of these 4 carry a confirmed, directly-quoted vendor prohibition the way Oracle Taleo and
Workday did. None of them carry a confirmed permission either. Per this project's own Rule 13, a
permissive `robots.txt` is a necessary check, never a substitute for a real, confirmed licence
record — so **none of these 4 are cleared to build against**, but none are blocked the clean way
Oracle/Workday are either. Honest status: **unresolved, needs either a real permission
conversation with the employer/vendor, or a deeper technical trace (e.g. checking whether
Sainsbury's job-listing data — which lives on their own `sainsburys.jobs` domain, separate from
the Oracle-hosted application-form redirect — has any structured public feed, such as a
WordPress REST API, worth investigating given the site's Yoast/WordPress footprint) before a real
build decision either way.**

Not attempting that deeper trace in this pass — flagging it as the concrete next step rather than
guessing further.
