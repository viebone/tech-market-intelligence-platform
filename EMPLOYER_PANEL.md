# UK Employer Panel — Candidate List

**Status: 19 of 36 added and live** (16 from verification pass 1, 2026-09-18; 3 more from pass 2, 2026-09-19 — below), the rest still
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

## Candidate panel (v1, ~36 employers)

| Employer | Size bucket | Sector | Why include | Priority | ATS / mechanism | Status |
|---|---|---|---|---|---|---|
| Tesco Careers | Large | Retail | Huge non-tech employer with digital/product/tech + operational jobs | High | Unverified | Unverified |
| Sainsbury's Jobs | Large | Retail | Retail + digital + data + product | High | Unverified | Unverified |
| BT Group Jobs | Large | Telecom | Strong engineering, product, data and cyber population | High | Unverified | Unverified |
| VodafoneThree Careers | Large | Telecom | Technology + network + product + commercial | High | Unverified | Unverified |
| Sky Careers | Large | Media/Telecom | Product, UX, engineering, data + operations | High | Unverified | Unverified |
| Barclays Careers | Large | Banking | Large UK tech/product employer | High | Unverified | Unverified |
| NatWest Group Careers | Large | Banking | Product, proposition, data and technology jobs visible directly | High | Unverified | Unverified |
| HSBC UK Jobs | Large | Banking | Broad UK geography and technology population | High | Unverified | Unverified |
| AstraZeneca UK Jobs | Large | Pharma | Science + AI/data + digital + corporate | High | Unverified | Unverified |
| BAE Systems UK Jobs | Large | Defence/Engineering | Engineering, software, cyber, UX and manufacturing | High | Unverified | Unverified |
| Rolls-Royce Careers | Large | Engineering | Strong engineering/manufacturing counterweight to tech | High | Unverified | Unverified |
| Civil Service Careers | Large | Public sector | Digital, product, policy, data + huge geographic spread | High | Unverified — likely needs a dedicated public-sector mechanism, deferred per the plan | Unverified |
| Monzo Careers | Medium | Fintech | Excellent product/engineering/design signal | High | **Greenhouse** (`monzo`) — verified | Added |
| Deliveroo UK Careers | Medium | Technology | Currently exposes a substantial UK job catalogue directly | High | **Greenhouse** (`deliveroo`) — verified; also resolves on Ashby but that board is operational/warehouse roles, recommend Greenhouse only, see note above | Added (Greenhouse board only) |
| Ocado Retail Careers | Medium | Retail/Tech | Digital + retail + supply chain + commercial | High | **Greenhouse** (`ocadogroup`) — verified | Added |
| Wise Careers | Medium | Fintech | Product-led technology employer | High | **Greenhouse** (`wise`) — verified | Added |
| Trainline Careers | Medium | Travel/Tech | Product, engineering, data and UX | High | **Ashby** (`trainline`) — verified | Added |
| Auto Trader Careers | Medium | Marketplace/Tech | Strong UK product organisation outside London | High | **Greenhouse** (`autotrader`) — verified | Added |
| Rightmove Careers | Medium | Marketplace/Tech | Product, engineering and data | High | **Greenhouse** (`rightmovecareers`) — verified | Added |
| Sage Careers | Medium | Software | Important non-London enterprise software employer | High | Unverified — the `sage49` Greenhouse board found is a different, unrelated US company (confirmed by content), real ATS still unknown | Unverified |
| Softcat Careers | Medium | IT services | Helps capture IT/services demand rather than only product companies | Medium | Unverified — custom domain `jobs.softcat.com`, ATS behind it not identified | Unverified |
| AJ Bell Careers | Medium | Financial services | Manchester/North-West + fintech/financial services | Medium | Unverified — URL pattern suggests Oracle Recruiting Cloud/HCM, a 6th ATS not yet on this project's radar | Unverified |
| Zopa Careers | Medium | Fintech | UK digital financial-services employer | High | **Lever** (`zopa`) — verified | Added |
| Starling Careers | Medium | Fintech | Engineering/product/data outside traditional banking | High | Confirmed **Workable** (`apply.workable.com/starling-bank`) — real, but not a built adapter yet | Unverified (needs Workable adapter) |
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
| Cuvva Careers | Small/Growth | Insurtech | Smaller technology employer | Medium | Unverified — no hit on `cuvva`/`cuvvainsurance` against any built adapter | Unverified |
| Beamery Careers | Small/Growth | HR Tech | B2B SaaS/product jobs | Medium | **Ashby** (`beamery`) — verified | Added |

---

## Next ATS adapters under consideration (unlocks many employers per adapter, not one)

Same "adapter, not per-company scraper" architecture already used for Greenhouse/Lever/Ashby.
**None of these are built yet** — this is a prioritized backlog, not a commitment on order:

| Adapter | Status | Notes |
|---|---|---|
| Teamtailor | Not started | Candidate first pick — reportedly common among smaller UK employers (per the plan's cited 2026 technology-detection dataset — treat as a discovery signal, not a verified census) |
| Workable | Not started | Same reasoning as Teamtailor |
| SmartRecruiters | Not started | Unverified how open/public its job API is — check before assuming Greenhouse-like access |
| Workday | Not started | Large-enterprise-favoured; likely more access-restricted than Greenhouse/Lever/Ashby — verify before assuming a Greenhouse-shaped public API exists |
| SuccessFactors | Not started | Same caveat as Workday |

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
