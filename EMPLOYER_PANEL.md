# UK Employer Panel — Candidate List

**Status: 21 of 36 added and live** (16 from verification pass 1, 2026-09-18; 3 more from pass 2, plus Starling and Cuvva via the new Workable adapter, 2026-09-19 — below), the rest still
proposal/unverified. This is a backlog worked through one entry at a time, not a decision that
all 36 employers are confirmed sources. See `DATA_SOURCES.md` §5 ("How to change coverage") for
the actual procedure to promote a candidate into a real, live source — every `Unverified` row
below still needs that same real verification (a live HTTP 200 against the actual ATS endpoint,
or a real permission/licence check for anything that isn't a documented, public, unauthenticated
API) before it counts as a tracked company.

See `research/2026-09-18-uk-employer-panel-plan.md` for the full proposal this table distills,
including the rationale for a stratified employer × size × sector × geography panel over
simply adding whatever companies are convenient, and the longer-term ~500-employer segmentation
target. This file exists to track this specific candidate list's progress, not to re-argue the
plan.

---

## Why this exists (the gap it corrects)

The current 35 tracked companies (`DATA_SOURCES.md` §4) skew toward venture-backed tech
(Stripe, Airbnb, Figma, Notion, ...). This panel deliberately adds variation across employer
size, industry, and geography — traditional industries, public sector, and UK-regional
employers, not just the same category of company the platform already over-represents.

---

## Working process — how an entry moves through this list

1. **Unverified** (default state for everything below) — a candidate, nothing checked yet.
2. **Checking** — actively verifying: does the claimed ATS/board token actually resolve
   (real HTTP request, same discipline as every other adapter in this codebase)? If no ATS,
   is there a real public API/feed? If neither, what would a custom adapter need, and has
   permission been sought (same bar IT Jobs Watch's inclusion required)?
3. **Verified — ready to add** — real endpoint confirmed, licence/ToS position understood
   (confirmed permitted, or explicit permission obtained).
4. **Added** — actually in a real `COMPANIES` list + `industries.py` + (if a new mechanism)
   `source_licences.py`, per `DATA_SOURCES.md` §5.
5. **Rejected** — checked and it doesn't work (no accessible ATS, terms prohibit this use,
   token 404s) — recorded with the reason, never silently dropped (same "mark removed, don't
   erase" convention as the rest of this project).

Go in **priority order** (High first), and within a priority tier, prefer employers already on
`greenhouse`/`lever`/`ashby` (zero new adapter work) before ones that would require building a
new ATS adapter (Teamtailor, Workable, SmartRecruiters, Workday, SuccessFactors — see "Next
adapters," below) or a custom/public-sector mechanism (defer these — see the plan's own
Decision Log in the research file).

---

## Verification pass 1 — 2026-09-18

Checked every High/Medium-priority Small/Growth and Medium-size candidate against the three
already-built adapters' real public endpoints (`boards-api.greenhouse.io`, `api.lever.co`,
`api.ashbyhq.com`) — one real HTTP request per candidate per platform, same discipline as
`DATA_SOURCES.md` §5. Deliberately skipped the Large enterprise employers (Tesco, Sainsbury's,
BT, Vodafone, Sky, Barclays, NatWest, HSBC, AstraZeneca, BAE, Rolls-Royce, Civil Service) this
pass — those are correctly expected to need a new adapter (Workday/SuccessFactors) or a custom
mechanism, not a guess against Greenhouse/Lever/Ashby.

**16 real, verified, zero-new-adapter-work hits:**

| Employer | ATS | Real endpoint | Approx. real job count |
|---|---|---|---|
| Attio | Ashby | `jobs.ashbyhq.com/attio` | 63 |
| Griffin | Ashby | `jobs.ashbyhq.com/griffin` | resolves, count not re-verified precisely |
| Monzo | Greenhouse | `boards-api.greenhouse.io/v1/boards/monzo` | 73 |
| Wise | Greenhouse | `boards-api.greenhouse.io/v1/boards/wise` | 17 |
| Deliveroo | **Both** Greenhouse (`deliveroo`) and Ashby (`deliveroo`) | see note below | Greenhouse: large corporate/tech board; Ashby: separate "Hop" operational/warehouse board |
| Auto Trader | Greenhouse | `boards-api.greenhouse.io/v1/boards/autotrader` | 19 |
| Cleo | Greenhouse | `boards-api.greenhouse.io/v1/boards/cleo` | 6 |
| Zopa | Lever | `api.lever.co/v0/postings/zopa` | ~131 raw entries (unrefined count) |
| Quantexa | Ashby | `jobs.ashbyhq.com/quantexa` | ~36 raw entries |
| Faculty | Ashby | `jobs.ashbyhq.com/faculty` | ~69 raw entries |
| Sylvera | Ashby | `jobs.ashbyhq.com/sylvera` | ~6 raw entries |
| Trainline | Ashby | `jobs.ashbyhq.com/trainline` | ~52 raw entries |
| Motorway | Ashby | `jobs.ashbyhq.com/motorway` | ~20 raw entries |
| Marshmallow | Ashby | `jobs.ashbyhq.com/marshmallow` | ~11 raw entries |
| Multiverse | Ashby | `jobs.ashbyhq.com/multiverse` | ~20 raw entries |
| Beamery | Ashby | `jobs.ashbyhq.com/beamery` | ~5 raw entries |

**Deliveroo — a real, honest complication, not a bug.** It genuinely resolves on *both*
Greenhouse and Ashby — not a coincidence or a wrong guess, both returned real Deliveroo postings
(location strings like "London, United Kingdom - Deliveroo" on Greenhouse; a "Hop Site
Operations UK & EU" warehouse role on Ashby). Reading: Deliveroo appears to run its
corporate/tech hiring through Greenhouse and its operational/warehouse ("Hop" grocery-site)
hiring through Ashby. For this platform's purpose (tech/product/digital market intelligence),
**recommend adding only the Greenhouse board** — the Ashby board's warehouse-operations roles
would mostly classify as `other` in this platform's taxonomy and would skew the panel's
composition in a way the stratification design doesn't call for. Flagged for a decision, not
silently resolved.

**Not found on a first-guess slug — genuinely unverified, not rejected** (a wrong guess isn't
evidence there's no accessible source — these need real research, e.g. checking the company's
own careers page for its actual ATS, before another attempt): Rightmove, Starling, incident.io,
Ocado, Sage, AJ Bell, Softcat, Cuvva.

**Not attempted this pass** (expected to need a new adapter or a custom/public-sector
mechanism, per the panel's own sequencing — see "Next ATS adapters" and "Deferred," below):
Tesco, Sainsbury's, BT Group, VodafoneThree, Sky, Barclays, NatWest, HSBC, AstraZeneca, BAE
Systems, Rolls-Royce, Civil Service.

---

## Verification pass 2 — 2026-09-19

Went back to the 8 "not found on a first-guess slug" candidates from pass 1, this time with
real research (WebSearch for each company's actual careers page/board token) instead of another
guess, then the same real-HTTP-200 + content-inspection discipline before adding anything.

**3 more real, verified hits — added:**

| Employer | ATS | Real board token | Note |
|---|---|---|---|
| Rightmove | Greenhouse | `rightmovecareers` (not `rightmove`) | 34 real jobs |
| Ocado (Group) | Greenhouse | `ocadogroup` (not `ocado`) | 50 real jobs — board includes non-UK roles (Ocado licenses its robotics internationally), same "don't assume UK-only" caveat as any global board |
| incident.io | Ashby | `incident` (not `incidentio`) | 29 real jobs; confirmed genuinely incident.io by "incident.io" appearing literally in job description text, not just a plausible-looking slug |

**A real, important near-miss — caught, not shipped.** A Greenhouse board at slug `sage49`
resolved with HTTP 200 and looked plausible at first ("Jobs at Sage"). **Content inspection
showed this is a different, unrelated US company** — every job was US-only (Los Angeles, New
York, remote-US), with titles like "Network Cabling Project Manager" and "Edge Platform" that
don't match Sage Group plc (the UK enterprise accounting/software company this panel actually
wants). **Not added.** This is exactly why this project's own discipline requires inspecting
real content, not just a 200 status, before trusting a match — recorded here as the concrete
example of that discipline catching a real false positive.

**Still unverified, with real findings recorded (not another blind guess):**

| Employer | Finding |
|---|---|
| Starling | Confirmed via search: uses **Workable** (`apply.workable.com/starling-bank`) — a real, accessible board, but not one of this codebase's three built adapters yet. Candidate for whichever of Teamtailor/Workable gets built first (see "Next ATS adapters," below). |
| AJ Bell | Careers URL pattern (`ajbell.co.uk/group/careers/vacancies/{long-numeric-id}`) matches **Oracle Recruiting Cloud / Oracle HCM** — a 6th ATS not on this project's radar at all yet. Not a quick win; needs its own investigation before anyone commits to building it. |
| Softcat | Careers hosted at a custom domain, `jobs.softcat.com` — ATS behind it not identified from search alone. Needs a direct look at the page/network requests, not just a search. |
| Sage (Group plc) | The `sage49` Greenhouse board is a different company (see above) — Sage Group's real ATS is still unknown. Likely a large-enterprise mechanism (Workday/SuccessFactors/custom), consistent with it being grouped near the Large-employer tier despite this panel listing it as Medium. |
| Cuvva | No real hit found this pass either (tried `cuvva` and `cuvvainsurance` against all three built adapters) — genuinely unresolved, not rejected. |

---

## Verification pass 3 — 2026-09-19

After the Workable adapter was built (`changes/2026-09-19-workable-adapter.md`), re-tried
`cuvva` against all four built adapters (Greenhouse, Lever, Ashby, Workable) instead of just
the three from pass 1/2.

**1 more real hit — added**: Cuvva resolves on **Workable** (`cuvva`) — real board, currently
**0 open roles** (a legitimate "returns 0" state, same convention already documented for
Greenhouse's `clari`/`restream` — not an error or a wrong slug).

**Deeper research on Softcat and Sage, still inconclusive — recorded honestly, not abandoned
silently**:
- **Softcat**: the real listings URL is `jobs.softcat.com/jobs/vacancy/find/results/` — a
  distinctive shape, but it doesn't match any built adapter or common ATS brand searched for
  (Workday, SmartRecruiters, iCIMS, Eightfold, PhenomPeople, SuccessFactors). Likely a
  white-label or custom platform; identifying it for real would need direct network-request
  inspection (opening the page in a real browser and reading its actual API calls), not
  available through search or a static page fetch.
- **Sage Group**: `sage.com/company/careers/career-search` returns HTTP 403 to automated
  fetches. No conclusive ATS identification found via search either. Real ATS still unknown.

---

## Verification pass 4 — 2026-09-20

Started on the 12 Large-employer candidates, deliberately deferred until now (Option 1 from
the "what's next" menu). Real ATS identification for 5 of 12; the other 7 not reached this
pass.

| Employer | Real platform found | Verified how |
|---|---|---|
| Tesco | Oracle Taleo | URL pattern (`RedirectApply`) on `careers.tesco.com` |
| Barclays | Workday | Real POST to the CXS API — 873 real jobs, `userAuthenticated: false` |
| AstraZeneca | Workday | Same CXS API pattern, confirmed with a second real request |
| NatWest | Unknown — Cloudflare-blocked | `jobs.natwestgroup.com` returns a bot-challenge page (403) to a plain request |
| HSBC | Eightfold.ai | `hsbc.eightfold.ai/careers` |

**Workday found real and technically excellent — deliberately not built.** Checked Workday's
own Terms of Service directly (same discipline as the Indeed/Reed research, 2026-09-19) and
found an explicit, verbatim prohibition on exactly what an adapter would do: *"Use any data
mining, robots or similar data gathering or extraction methods designed to scrape or extract
data from our Sites"*; *"Develop or use any applications that interact with our Sites without
our prior written consent"*; *"Bypass or ignore instructions contained in our robots.txt
file."* Full detail: `research/2026-09-20-workday-licence-check.md`. This is the same shape of
finding as Indeed and Reed — a technically-open, unauthenticated endpoint with an explicit
written prohibition — and gets the same treatment: **no adapter without explicit permission.**
User confirmed 2026-09-20: "lets skip workday for now." Real footprint: 2 verification requests
total (Barclays, AstraZeneca), not an ongoing scrape.

Tesco (Taleo) and HSBC (Eightfold.ai) are two more new platforms this panel hadn't encountered
before — neither's terms have been checked yet, and neither is a quick technical win the way
Workday's CXS API was (no confirmed public API found for either in this pass).

---

## Verification pass 5 — 2026-09-20

Continued straight on to the remaining 7 Large-employer candidates not reached in pass 4:
Sainsbury's, BT Group, VodafoneThree, Sky, BAE Systems, Rolls-Royce, Civil Service. Full detail:
`research/2026-09-20-large-employer-pass5-findings.md`.

**Real platform identification for all 7** (WebSearch + direct WebFetch content inspection —
CDN domains and URL shapes read from the live page, same discipline as the `sage49` false-
positive catch in pass 2, not assumed from search summaries alone):

| Employer | Real platform found | Verified how |
|---|---|---|
| Sainsbury's | Oracle Recruiting Cloud / HCM | `sainsburys.jobs/jobs` links to `hdhe.fa.em3.oraclecloud.com/hcmUI/CandidateExperience/...` |
| BT Group | SAP SuccessFactors | `jobs.bt.com/BTGroup/` serves an asset from `rmkcdn.successfactors.com`; cookie notice names SAP |
| VodafoneThree | Attrax (now part of Phenom) | `jobs.three.co.uk/jobs` serves assets from `attraxcdnprod1-....azurefd.net` |
| Sky | Oracle Taleo (at least one instance) | Real reachable URL: `bskyb.taleo.net/careersection/bskyb_internal/jobsearch.ftl` — Sky's own privacy notice also names Workday/Avature/Cappfinity/LaunchPad, likely different sub-brands/stages, not confirmed the same way |
| BAE Systems | Oracle Taleo | Direct HTTP 200 on `baesystems.taleo.net/careersection/2/jobsearch.ftl?lang=en` |
| Rolls-Royce | Workday | `rollsroyce.wd3.myworkdayjobs.com/professional` (plus divisional tenants) — same CXS platform already confirmed for Barclays/AstraZeneca |
| Civil Service | Still no official API | `civilservicejobs.service.gov.uk` remains HTML-only; only third-party commercial scrapers exist, no first-party feed |

**Rolls-Royce needs no new decision** — it's the same Workday platform already blocked earlier
this same day (Barclays/AstraZeneca research), so the existing "skip Workday for now" decision
applies without re-litigating it.

**A real, half-open Taleo lead — found, not built.** With Taleo now confirmed for 3 employers
(Tesco, BAE Systems, Sky), checked whether it exposes any real API, since one adapter there would
unlock 3 companies at once. Direct requests against BAE Systems' instance: `GET .../careersection/
rest/jobboard/searchjobs` → HTTP 405 (path exists, wrong method); `POST` with a guessed JSON body
→ HTTP 400 (endpoint is real and live, but its actual required request schema isn't something to
guess further at without Oracle's own API docs). Licence check deferred to a same-day follow-up —
see "Oracle Taleo licence check," below.

---

## Oracle Taleo licence check — 2026-09-20

Followed up on the Taleo lead from pass 5 with the same document-fetching discipline used for
Workday. Full detail: `research/2026-09-20-oracle-taleo-licence-check.md`.

Taleo career sections carry no Oracle-specific legal link of their own (checked BAE Systems' live
page directly — only a BAE Systems cookie-statement link was found). Went to the source instead:
**Oracle Web Sites Terms of Use** (`oracle.com/legal/terms/`, fetched directly, "Last Revised:
August 10, 2024"). Verbatim:

> "Welcome to the Oracle Web sites (the 'Site')... The following are terms of a legal agreement
> between you... and Oracle Corporation and its affiliated companies."

> "You agree not to use any robot, spider, scraper or other automated means to access the Site or
> any Oracle accounts, computer systems or networks without Oracle's express written permission."

**Scope reasoning**: `taleo.net` is Oracle-owned, Oracle-operated infrastructure (Oracle acquired
Taleo in 2012) — every career section, however it's branded for the employer, runs on Oracle's
own domain from the start. If anything this is a **stronger** case for coverage than Workday's
tenant-subdomain ambiguity was (Workday's terms named `workday.com` specifically and left
`myworkdayjobs.com` tenant pages an open question; Taleo has no equivalent ambiguity — there's no
separate "tenant domain" at all, it's all `taleo.net`).

**Decision: do not build a Taleo adapter without Oracle's express written permission** — same
treatment as Indeed, Reed, and Workday, and it affects all 3 currently-identified Taleo employers
(Tesco, BAE Systems, Sky) at once, not just one.

---

## Remaining 4 platforms' licence check — 2026-09-20

Followed up on the 4 platforms from pass 5 that hadn't been checked yet: Sainsbury's (Oracle
Recruiting Cloud/HCM), BT Group (SAP SuccessFactors), VodafoneThree (Attrax/Phenom), HSBC
(Eightfold.ai). Full detail: `research/2026-09-20-remaining-large-employer-licence-check.md`.

**A materially different shape than Taleo/Workday.** Those two live entirely on the vendor's own
domain — unambiguous whose terms apply. These 4 are white-labeled: the visible domain and every
visible legal link belong to the **employer**, not the platform vendor (confirmed directly for
HSBC — its live careers page shows only HSBC's own privacy/cookie/accessibility links; Eightfold
branding is explicitly hidden via `hide_eightfold_branding: true`). No cleanly-applicable vendor
Terms of Use document was found directly for any of the 4 the way Oracle's and Workday's were.

**`robots.txt` checked directly for all 4** (real, unambiguous, regardless of the ToS gap):

| Employer | robots.txt |
|---|---|
| Sainsbury's | Fully open + explicit `Crawl-delay: 10` |
| HSBC | Default-deny, but `/careers`, `/careerhub/explore/jobs`, `/api/career_hub` explicitly allowed |
| BT Group | Job search/listing paths not disallowed |
| VodafoneThree | `Disallow: /jobs?*` — the one clear negative signal, on exactly the paths that matter |

**Honest conclusion: genuinely unresolved, not a clean call either way.** No confirmed vendor
prohibition (unlike Oracle/Workday) and no confirmed permission either. Per this project's own
Rule 13, a permissive `robots.txt` is a necessary check, never a substitute for a real licence
record — so **none of these 4 are cleared to build against, but none are cleanly blocked the way
Oracle/Workday are either.** Next concrete step, not yet taken: either a real permission
conversation, or a deeper technical trace — Sainsbury's is the most promising lead (job listings
live on their own WordPress/Yoast-footprint domain, separate from the Oracle-hosted application
redirect, with a generous robots.txt) worth checking for a structured feed.

---

## Direct-to-employer-portal check — 2026-09-20

User asked: "what about going directly to the companies' career portals?" Real research on
whether that opens anything the vendor research above didn't already cover. Full detail:
`research/2026-09-20-direct-employer-portal-check.md`.

**For the 7 vendor-hosted employers (Workday/Taleo/Eightfold), there is no separate "company
portal"** — confirmed directly for BAE Systems: its own marketing careers page
(`baesystems.com/.../search-and-apply`) doesn't serve real content to an automated request at
all, loading an Incapsula/Imperva bot-challenge instead — a second, independent wall, unrelated
to the Taleo ToS question already found. For all 7, the company's own site redirects/embeds
straight into the vendor's domain already checked — going "directly to the portal" doesn't
create a new option.

**For BT, VodafoneThree, and Sainsbury's — already looking at the employer's own domain.**
Checked each employer's own general website terms (as opposed to any ATS vendor's): BT and
VodafoneThree have **no general website Terms of Use at all** in their careers-site footer — no
prohibition, no permission, genuinely neutral. Sainsbury's does have one
(`sainsburys.co.uk/terms`) but it returned HTTP 403 even to a real browser User-Agent —
unreachable to verify.

**An important distinction from Greenhouse/Lever/Ashby/Workable**: those were built on "no
restriction found" *alongside* a purpose-built public JSON API — a structural signal the vendor
intended exactly this kind of consumption. BT/VodafoneThree/Sainsbury's have no known structured
feed at all — building anything here would be real HTML scraping against an undocumented page,
squarely the **Custom careers-page adapter** category already named in "Deferred," below: real,
permission-seeking, IT-Jobs-Watch-weight effort, not a quick technical win.

**A separate new finding**: Civil Service Jobs (`civilservicejobs.service.gov.uk`) is itself
actively bot-challenged (a real "Quick Check Needed" page, confirmed via direct fetch) — which
makes its Open Government Licence status (a genuinely more permissive regime than any commercial
ATS vendor's terms) moot in practice, since the site is bot-walled before that licence would
ever matter.

---

## Candidate panel (v1, ~36 employers)

| Employer | Size bucket | Sector | Why include | Priority | ATS / mechanism | Status |
|---|---|---|---|---|---|---|
| Tesco Careers | Large | Retail | Huge non-tech employer with digital/product/tech + operational jobs | High | **Oracle Taleo** confirmed (`careers.tesco.com` — `RedirectApply` URL pattern) — **deliberately not built**: Oracle's Terms of Use explicitly prohibit scraping/automated access without express written permission (`research/2026-09-20-oracle-taleo-licence-check.md`) | Unverified — blocked on permission, not technically |
| Sainsbury's Jobs | Large | Retail | Retail + digital + data + product | High | **Oracle Recruiting Cloud / HCM** confirmed for the application-form redirect only; job **listings** live on Sainsbury's own domain (`sainsburys.jobs`, WordPress/Yoast footprint), robots.txt fully open + `Crawl-delay: 10`. No vendor ToS confirmed either way — genuinely unresolved, not cleared (`research/2026-09-20-remaining-large-employer-licence-check.md`) | Unverified |
| BT Group Jobs | Large | Telecom | Strong engineering, product, data and cyber population | High | **SAP SuccessFactors** confirmed as backend infrastructure (`jobs.bt.com` serves an asset from `rmkcdn.successfactors.com`); robots.txt doesn't disallow job listing paths. No vendor ToS confirmed either way — genuinely unresolved, not cleared | Unverified |
| VodafoneThree Careers | Large | Telecom | Technology + network + product + commercial | High | **Attrax (Phenom)** confirmed as backend infrastructure (`jobs.three.co.uk` serves assets from `attraxcdnprod1-....azurefd.net`); robots.txt explicitly disallows `/jobs?*` — the one clear negative signal among the 4 unresolved platforms | Unverified |
| Sky Careers | Large | Media/Telecom | Product, UX, engineering, data + operations | High | **Oracle Taleo** confirmed for at least one instance (`bskyb.taleo.net`) — Sky's own privacy notice also names Workday/Avature/Cappfinity/LaunchPad. **Taleo instance deliberately not built** (Oracle's Terms of Use prohibition, `research/2026-09-20-oracle-taleo-licence-check.md`) | Unverified — blocked on permission, not technically |
| Barclays Careers | Large | Banking | Large UK tech/product employer | High | **Workday** confirmed real and technically accessible (public, unauthenticated CXS API, 873 real jobs) — **deliberately not built**: Workday's own Terms of Service explicitly prohibit scraping/automated access/apps interacting with their sites without written consent (`research/2026-09-20-workday-licence-check.md`). Needs explicit permission before any adapter work, same bar as Indeed/Reed | Unverified — blocked on permission, not technically |
| NatWest Group Careers | Large | Banking | Product, proposition, data and technology jobs visible directly | High | Real candidate site (`jobs.natwestgroup.com`) is Cloudflare-protected — returns a bot-challenge page (403) to a plain request regardless of underlying platform | Unverified |
| HSBC UK Jobs | Large | Banking | Broad UK geography and technology population | High | **Eightfold.ai** confirmed (`hsbc.eightfold.ai/careers`, Eightfold branding deliberately hidden via `hide_eightfold_branding: true`); robots.txt explicitly allows `/careers`, `/careerhub/explore/jobs`, `/api/career_hub` despite a default-deny — the most positive of the 4 unresolved-platform signals, but Eightfold's own Terms of Use couldn't be directly verified (guessed URLs 404'd) — genuinely unresolved, not cleared | Unverified |
| AstraZeneca UK Jobs | Large | Pharma | Science + AI/data + digital + corporate | High | **Workday** confirmed real and technically accessible (same public CXS API as Barclays) — same deliberate non-build decision, see Barclays row | Unverified — blocked on permission, not technically |
| BAE Systems UK Jobs | Large | Defence/Engineering | Engineering, software, cyber, UX and manufacturing | High | **Oracle Taleo** confirmed (`baesystems.taleo.net/careersection/2/jobsearch.ftl` — real HTTP 200; a real REST endpoint also exists, 405 on GET / 400 on a guessed POST). **Deliberately not built**: Oracle's Terms of Use explicitly prohibit scraping/automated access without express written permission (`research/2026-09-20-oracle-taleo-licence-check.md`) | Unverified — blocked on permission, not technically |
| Rolls-Royce Careers | Large | Engineering | Strong engineering/manufacturing counterweight to tech | High | **Workday** confirmed (`rollsroyce.wd3.myworkdayjobs.com/professional`) — same CXS platform already blocked for Barclays/AstraZeneca; inherits that decision, no separate one needed | Unverified — blocked on permission, not technically |
| Civil Service Careers | Large | Public sector | Digital, product, policy, data + huge geographic spread | High | Confirmed no official API — `civilservicejobs.service.gov.uk` is HTML-only; only third-party commercial scrapers exist. Likely needs a dedicated public-sector mechanism, deferred per the plan | Unverified |
| Monzo Careers | Medium | Fintech | Excellent product/engineering/design signal | High | **Greenhouse** (`monzo`) — verified | Added |
| Deliveroo UK Careers | Medium | Technology | Currently exposes a substantial UK job catalogue directly | High | **Greenhouse** (`deliveroo`) — verified; also resolves on Ashby but that board is operational/warehouse roles, recommend Greenhouse only, see note above | Added (Greenhouse board only) |
| Ocado Retail Careers | Medium | Retail/Tech | Digital + retail + supply chain + commercial | High | **Greenhouse** (`ocadogroup`) — verified | Added |
| Wise Careers | Medium | Fintech | Product-led technology employer | High | **Greenhouse** (`wise`) — verified | Added |
| Trainline Careers | Medium | Travel/Tech | Product, engineering, data and UX | High | **Ashby** (`trainline`) — verified | Added |
| Auto Trader Careers | Medium | Marketplace/Tech | Strong UK product organisation outside London | High | **Greenhouse** (`autotrader`) — verified | Added |
| Rightmove Careers | Medium | Marketplace/Tech | Product, engineering and data | High | **Greenhouse** (`rightmovecareers`) — verified | Added |
| Sage Careers | Medium | Software | Important non-London enterprise software employer | High | Unverified — re-fetched `sage.com/en-gb/company/careers/career-search/` directly (real 200 this time, 209KB), searched for every ATS vendor marker checked elsewhere in this panel — found none. Job data most likely loads via client-side JS after page load; would need a real browser network trace to identify, not available via search/static fetch (`research/2026-09-20-medium-tier-remaining-candidates.md`) | Unverified |
| Softcat Careers | Medium | IT services | Helps capture IT/services demand rather than only product companies | Medium | **Actively bot-challenged, not just unidentified** — `jobs.softcat.com/jobs/vacancy/find/results/` returns HTTP 202 with `x-amzn-waf-action: challenge` (AWS WAF actively serving a bot challenge instead of content). Getting past it would need a headless-browser bypass, against this project's own polite-scraping discipline regardless of platform. Recommend treating as a strong "do not build" signal | Unverified — effectively blocked, not just unidentified |
| AJ Bell Careers | Medium | Financial services | Manchester/North-West + fintech/financial services | Medium | **SmartRecruiters confirmed** (corrects the earlier Oracle guess) — `ajbell.co.uk`'s "register your interest" link resolves through `smrtr.io` to `join.smartrecruiters.com/AJBell1/...`. Public Postings API tested directly (`api.smartrecruiters.com/v1/companies/AJBell1/postings`, real 200, 19 real jobs) — but **deliberately not built**: SAP's own API Policy explicitly prohibits "scraping, harvesting, or systematic and/or large-scale data extraction" (`research/2026-09-20-medium-tier-remaining-candidates.md`) | Unverified — blocked on permission, not technically |
| Zopa Careers | Medium | Fintech | UK digital financial-services employer | High | **Lever** (`zopa`) — verified | Added |
| Starling Careers | Medium | Fintech | Engineering/product/data outside traditional banking | High | **Workable** (`starling-bank`) — verified, 55 real jobs, first company on the new adapter | Added |
| Quantexa Careers | Medium | AI/Data | Useful AI/data hiring signal | High | **Ashby** (`quantexa`) — verified | Added |
| Faculty Careers | Medium/Small | AI | AI engineers, data scientists, product and consulting | High | **Ashby** (`faculty`) — verified | Added |
| Motorway Careers | Medium | Marketplace | UK product/engineering scale-up | Medium | **Ashby** (`motorway`) — verified | Added |
| Marshmallow Careers | Medium | Insurtech | Growth-company product/data/engineering | Medium | **Ashby** (`marshmallow`) — verified | Added |
| Multiverse Careers | Medium | EdTech | Adds education/technology | Medium | **Ashby** (`multiverse`) — verified | Added |
| Attio Jobs | Small/Growth | SaaS | Excellent startup signal | High | **Ashby** (`attio`) — verified, real HTTP 200, 63 real jobs | Added |
| Griffin Jobs | Small/Growth | Fintech | UK-regulated bank/startup; UK/remote roles visible in Ashby | High | **Ashby** (`griffin`) — verified, real HTTP 200 | Added |
| Sylvera Jobs | Small/Growth | Climate/Data | ~130-person scale-up with data/science/engineering roles | High | **Ashby** (`sylvera`) — verified | Added |
| incident.io Careers | Small/Growth | SaaS | Strong software/product startup indicator | High | **Ashby** (`incident`) — verified, "incident.io" confirmed in job text | Added |
| Cleo Careers | Small/Growth | Fintech/AI | Consumer AI/product company | Medium | **Greenhouse** (`cleo`) — verified | Added |
| Cuvva Careers | Small/Growth | Insurtech | Smaller technology employer | Medium | **Workable** (`cuvva`) — verified real, currently 0 open roles ("returns 0," not an error) | Added |
| Beamery Careers | Small/Growth | HR Tech | B2B SaaS/product jobs | Medium | **Ashby** (`beamery`) — verified | Added |

---

## Next ATS adapters under consideration (unlocks many employers per adapter, not one)

Same "adapter, not per-company scraper" architecture already used for Greenhouse/Lever/Ashby.
**None of these are built yet** — this is a prioritized backlog, not a commitment on order:

| Adapter | Status | Notes |
|---|---|---|
| Teamtailor | Not started | Candidate next pick — reportedly common among smaller UK employers (per the plan's cited 2026 technology-detection dataset — treat as a discovery signal, not a verified census) |
| Workable | ✅ **Built 2026-09-19** (`changes/2026-09-19-workable-adapter.md`) | `backend/src/sources/workable.py` — public, unauthenticated widget API, same shape as Greenhouse. First company: `starling-bank` (55 real jobs). Multi-location jobs deduped to one row per distinct job (see the adapter's own module docstring) — a real data-shape quirk found and handled, not assumed away. |
| **SmartRecruiters** | ❌ **Blocked on permission, 2026-09-20** — not a build candidate right now | Confirmed used by AJ Bell (`AJBell1`). Technically excellent — a real, public, unauthenticated Postings API (`api.smartrecruiters.com/v1/companies/{id}/postings`), same shape as Greenhouse — but SAP (SmartRecruiters' parent company)'s own API Policy explicitly prohibits "scraping, harvesting, or systematic and/or large-scale data extraction or replication" — `research/2026-09-20-medium-tier-remaining-candidates.md`. Revisit only if explicit permission is obtained, same bar as Workday/Taleo/Indeed/Reed. |
| **Workday** | ❌ **Blocked on permission, 2026-09-20** — not a build candidate right now | Technically excellent (public, unauthenticated CXS API, confirmed real for Barclays + AstraZeneca) but Workday's own Terms of Service explicitly prohibit scraping/automated access without written consent — `research/2026-09-20-workday-licence-check.md`. Revisit only if explicit permission is obtained (from Workday or an individual tenant employer), same bar as Indeed/Reed. |
| SuccessFactors | Not started | Confirmed used by BT Group (2026-09-20, `rmkcdn.successfactors.com` asset evidence) — same caveat as Workday, check terms before assuming access |
| **Oracle Taleo** | ❌ **Blocked on permission, 2026-09-20** — not a build candidate right now | Confirmed used by Tesco, BAE Systems, and (at least one instance of) Sky — would have been the strongest "one adapter unlocks several" case in this backlog (a real REST endpoint, `careersection/rest/jobboard/searchjobs`, is live: 405/400, not 404). But Oracle's own Terms of Use explicitly prohibit "any robot, spider, scraper or other automated means" without Oracle's express written permission — `research/2026-09-20-oracle-taleo-licence-check.md`. Revisit only if explicit permission is obtained, same bar as Workday/Indeed/Reed. |
| Eightfold.ai | Not started | Confirmed used by HSBC (`hsbc.eightfold.ai`) — no known public API found yet, terms not checked |
| Oracle Recruiting Cloud / HCM | Not started | Confirmed used by Sainsbury's (2026-09-20) and suspected for AJ Bell — a platform new to this panel, no known public API found yet, terms not checked |
| Attrax (Phenom) | Not started | Confirmed used by VodafoneThree (2026-09-20, `attraxcdnprod1-....azurefd.net` asset evidence) — a platform new to this panel, no known public API found yet, terms not checked |

## Deferred (own future change requests, not bundled into this panel)

- **Custom careers-page adapter** — for employers with no ATS at all. Each one is real,
  IT-Jobs-Watch-weight effort (permission-seeking, `PoliteScraper`, licence registry entry),
  not a generic reusable adapter.
- **Public-sector adapter** — Civil Service Careers and similar; likely its own mechanism
  entirely, not a variant of the ATS adapters above.
- **`closed_at`/posting-lifecycle tracking** — this platform's ingestion is currently
  insert-only; nothing detects a posting going stale/closed. A real, separate feature.
- **ONS cross-referencing** — for the "vs. the wider market" credibility framing the plan
  describes. A new external data source in its own right.
- ~~**`employer_size_band` / `employer_sector` / `employer_region` schema addition**~~ **Done
  2026-09-19** — `changes/2026-09-19-employer-panel-schema.md`. `employer_sector` already
  existed as `raw_postings.industry`. `employer_region` is now populated for all 54 tracked
  companies. `employer_size_band` is populated for the 19 UK panel companies (user-supplied
  buckets) **and, as of the same day, 33 of the original 35** via real headcount research
  (`research/2026-09-19-original-35-size-bands.md`, cited ranges per company) — only `lever`
  (the ATS company itself, now a sub-brand of Employ Inc.) remains untagged, since no real
  figure was found. 53 of 54 tracked companies now have a real, cited `employer_size_band`.

---

## Long-term segmentation target (for reference, not a near-term commitment)

| Segment | Target employers |
|---|---|
| Large employers, 5,000+ employees | 75 |
| Mid-size, 500–5,000 | 125 |
| Smaller/growth, ~50–500 | 200 |
| Small/startup, <50 | 100 |
| **Total mature panel** | **~500** |

The ~36 above is the deliberately small first slice — go one by one, verify each, measure
real collection for a period before expanding further, per the plan's own closing
recommendation.
