---
source: internal
date: 2026-09-20
---

Following up on the user's question: "what about going directly to the companies' career
portals?" — real research on whether bypassing the ATS-vendor question by going straight to the
employer's own domain actually opens anything up.

## Bucket 1 — there is no separate "company portal" (Workday/Taleo/Eightfold-hosted cases)

Confirmed directly: BAE Systems' own careers page (`baesystems.com/en-uk/careers/careers-in-
the-uk/search-and-apply`) does not serve real content to an automated request at all — it loads
an Incapsula/Imperva bot-challenge iframe (`_Incapsula_Resource`), a separate, independent wall
from the Taleo ToS question. For Barclays/AstraZeneca/Rolls-Royce (Workday) and Tesco/BAE/Sky
(Taleo) and HSBC (Eightfold), the company's own marketing site redirects or embeds straight into
the vendor's hosted domain — there is no alternate "company portal" distinct from what was
already checked. Going directly to the employer's site doesn't create a new option here.

## Bucket 2 — BT, VodafoneThree, Sainsbury's: already looking at the employer's own domain

These three genuinely do serve real job content from their own domain (`jobs.bt.com`,
`jobs.three.co.uk`, `sainsburys.jobs`) — which is exactly what was already fetched in the
pass-5/remaining-4-platforms research. The open gap was whether each employer's *own* general
website terms (as opposed to any ATS vendor's) say anything. Checked directly:

| Employer | Own general "website terms of use"? | Finding |
|---|---|---|
| BT Group | **None found** | `jobs.bt.com`'s footer links only Privacy Policy, Modern Slavery Statement, Recruitment Privacy Notice, and Accessibility — no general Terms of Use document exists to check at all |
| VodafoneThree | **None found** (relevant to this) | `jobs.three.co.uk`'s footer links only a "Code of Practice" (a telecom regulatory document, not a website ToU), plus Privacy/Cookies |
| Sainsbury's | **Found, but unreachable** | `sainsburys.jobs`'s footer points to `sainsburys.co.uk/terms` for general Terms & Conditions — that page returned HTTP 403 to a direct fetch even with a real browser User-Agent, i.e. bot-protected. Can't verify its content either way. |

**Net for this bucket**: BT and VodafoneThree have no company-level document prohibiting this
(nor permitting it) — genuinely neutral, same "unresolved, not blocked" status as before, just
now confirmed at the employer level too, not only the vendor level. VodafoneThree still carries
its own negative signal regardless (robots.txt disallowing `/jobs?*`,
`research/2026-09-20-remaining-large-employer-licence-check.md`). Sainsbury's remains genuinely
unresolved — its own stated terms exist but can't be read.

**An important distinction from Greenhouse/Lever/Ashby/Workable, though.** Those adapters were
built on "no restriction found" because each also had a **purpose-built public JSON API** — a
structural signal the vendor intended this exact kind of programmatic consumption. BT,
VodafoneThree, and Sainsbury's have no known structured feed at all — building anything here
would mean real HTML scraping against a site with no documented API, the same category this
panel's own "Deferred" section already names as **Custom careers-page adapter**: real,
permission-seeking, IT-Jobs-Watch-weight effort, not a quick technical win. "No restriction
found" carries much less weight without that structural signal alongside it.

## A new, separate finding: several employer domains are themselves actively bot-protected

Beyond BAE Systems' marketing site (above): **Civil Service Jobs** (`civilservicejobs.service.
gov.uk`) returns a real "Quick Check Needed" bot-challenge page (`<meta name="robots"
content="noindex">`, loads `/protect/main.js`) to a direct request — confirmed via a real HTTP
200 that serves the challenge page itself, not real content. **Sainsbury's main retail domain**
(`sainsburys.co.uk`, where its Terms & Conditions live) also returned a 403. This means the Open
Government Licence question for Civil Service Jobs (a genuinely different, more permissive
licensing regime than any commercial ATS vendor's terms — UK government content is often
published for free reuse) turns out to be moot in practice: the site is bot-walled before you'd
ever get far enough to rely on that licence.

## Conclusion

Going directly to the company's own portal doesn't unlock anything for the 7 vendor-hosted
employers (Bucket 1) — it's the same page already checked. For BT/VodafoneThree/Sainsbury's
(Bucket 2), it confirms a genuinely neutral, still-unresolved position (no prohibition, no
permission) rather than a green light — and reclassifies what building against them would
actually require: a bespoke scraper against an undocumented HTML page, not a quick adapter,
the same weight of effort as IT Jobs Watch's own onboarding (which required actually asking and
receiving explicit permission, not just finding no objection).
