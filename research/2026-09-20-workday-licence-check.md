source: internal
date: 2026-09-20

Researching the 12 Large-employer panel candidates' real ATS platforms
(`EMPLOYER_PANEL.md`) surfaced Workday as a real, technically excellent option — confirmed via
direct verification (2 real POST requests) against Barclays and AstraZeneca's public,
unauthenticated CXS API (`https://{tenant}.wd{N}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs`):
clean, structured job data, hundreds of real postings, `"userAuthenticated":false`.

## Licence check (same discipline as the Indeed/Reed research, 2026-09-19)

Fetched Workday's own Terms of Service directly (`workday.com/en-us/legal/site-terms.html`).
Verbatim, Section 2 ("Prohibited Conduct and Content"):

> "Use any data mining, robots or similar data gathering or extraction methods designed to
> scrape or extract data from our Sites"

> "Develop or use any applications that interact with our Sites without our prior written
> consent"

> "Bypass or ignore instructions contained in our robots.txt file"

All three explicitly prohibited. Same shape of problem as Indeed and Reed: a technically-open
endpoint with an explicit written prohibition against exactly what building an adapter would do
— unlike Greenhouse/Lever/Ashby/Workable, whose own docs had no such restriction ("no
restriction found," not fabricated into a licence).

**One honest nuance, not fully resolved**: this document's "our Sites" is defined around
`workday.com` itself; it doesn't explicitly name `myworkdayjobs.com` tenant career pages. No
evidence of a more permissive carve-out was found either. Treated conservatively, the same way
as Indeed/Reed.

## Decision
Do not build a Workday adapter without explicit written permission (from Workday, or from the
individual employer operating the tenant) — user confirmed: "ok, lets skip workday for now."

Real verification footprint: 2 POST requests total (Barclays, AstraZeneca), made to confirm the
technical claim before deciding — not an ongoing scrape.
