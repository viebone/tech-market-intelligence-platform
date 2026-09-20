---
source: internal
date: 2026-09-20
---

Following up on the real, half-open Taleo lead from pass 5
(`research/2026-09-20-large-employer-pass5-findings.md`) — Taleo's
`careersection/rest/jobboard/searchjobs` endpoint responded 405/400 (live, not 404) across 3
now-confirmed employers (Tesco, BAE Systems, Sky), the strongest "one adapter unlocks several"
opportunity in the panel. Same discipline as the Indeed/Reed/Workday research: check the
platform's own terms directly before building anything, not just confirm the endpoint responds.

## Licence check

Oracle's Taleo career sections carry no visible terms/legal link of their own (checked BAE
Systems' live page — the only legal-adjacent link found was BAE Systems' own cookie statement,
nothing Oracle-specific). Went to the source instead: **Oracle Web Sites Terms of Use**
(`oracle.com/legal/terms/`), fetched directly (not from a search summary — the page 403s a bare
fetch without a browser User-Agent; retried with one and got a real 200).

**Scope** — verbatim, opening paragraph: *"Welcome to the Oracle Web sites (the 'Site'). Through
the Site, you have access to a variety of resources and content... The following are terms of a
legal agreement between you... and Oracle Corporation and its affiliated companies."* The
definition is broad — "the Oracle Web sites" generically, not scoped to `oracle.com` specifically.
`taleo.net` is Oracle-owned, Oracle-operated infrastructure (Oracle acquired Taleo in 2012; every
career section, regardless of which employer it's branded for, runs on Oracle's own domain) —
if anything, a **stronger** case for being "an Oracle Web site" than Workday's tenant-subdomain
ambiguity was (Workday's own terms named `workday.com` specifically and left `myworkdayjobs.com`
tenant pages ambiguous; Taleo's customer-branded career sections sit on Oracle's own domain from
the start, no equivalent ambiguity).

**The prohibition** — verbatim, Section on Site conduct: *"You agree not to use any robot,
spider, scraper or other automated means to access the Site or any Oracle accounts, computer
systems or networks without Oracle's express written permission."*

Document metadata: "Last Revised: August 10, 2024" — current, not stale.

## Decision

Same shape of finding as Indeed, Reed, and Workday: a technically-open, unauthenticated endpoint
(confirmed live via real HTTP requests against BAE Systems' instance,
`research/2026-09-20-large-employer-pass5-findings.md`) with an explicit written prohibition
against exactly what building an adapter would do. Treated the same way: **do not build a Taleo
adapter without Oracle's express written permission** — this affects all 3 currently-identified
Taleo employers (Tesco, BAE Systems, Sky), not just one.

Real verification footprint for this check: 2 requests to fetch/re-fetch the terms document
(one 403 without a User-Agent, one successful 200 with one) — not an ongoing scrape.
