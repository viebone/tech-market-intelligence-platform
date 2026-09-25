source: internal
date: 2026-09-25

# Panel headcount research — 48 companies (26 US/EU + Lever + 21 UK), plus ONS bands for the original 34 with figures on file

Step 4 of `changes/2026-09-25-employer-size-standard-bands.md`. **Research only — no code, no stored data, and `industries.py` are unchanged.** Figures are the *evidence* for a future headcount table (Option A); the derived ONS band is computed from the range, not chosen.

## How to read this

- **Range** — the lowest and highest credible figure found. Where sources disagreed I kept the range and excluded only figures that were inconsistent with a primary source (each exclusion is stated in the note). I did **not** pick a favourite to make a band come out cleanly.
- **Derived ONS band** — from the range using ONS's five bands: 1–9, 10–49, 50–249, 250–2,499, 2,500+. If the whole range sits in one band, that's the band. If it straddles a boundary the result is **AMBIGUOUS** — never guessed (the rule recorded in the change request).
- **Confidence** — **High** = the company's own filing or annual report; **Medium** = several sources broadly agree (mostly Revelio Labs workforce data plus aggregators); **Low** = sources conflict badly, a single aggregator, or a private company with no primary source.
- **How the data was gathered:** web-search result summaries (e.g. the search tool's digest of an SEC filing), **not** the filings opened and read. The filings named as "High" should be spot-checked before anything user-facing depends on them.
- **Basis:** every figure is a **worldwide / group** headcount — none is a UK-only figure (except Moonpig's ~93% UK share). ONS measures UK business size, so for multinationals the ONS band this table derives is **only an approximation** of what ONS would assign.
- **Dates:** the search results dated into 2026 (some to Aug 2026). They are what the tool returned; not independently dated by me.

## Summary

- **26 US/EU + Lever:** 250-2,499: 21, 2,500+: 2, AMBIGUOUS: 3, not derived: 1
- **21 UK:** 50-249: 6, 250-2,499: 9, 2,500+: 5, AMBIGUOUS: 1
- **Original 34 with headcounts (from `2026-09-19-original-35-size-bands.md`, no new research; the 35th, Lever, is in A):** 50-249: 3, 250-2,499: 16, 2,500+: 13, AMBIGUOUS: 2
- **All 82 tracked companies:** 50-249: 9, 250-2,499: 46, 2,500+: 20, AMBIGUOUS: 6, not derived: 1

- **Old UK buckets that don't fit the headcount:** 5 of 21 — Monzo, Wise, Cleo, Ocado Group, Motorway. (These were user-supplied buckets; the headcounts show they should not be relied on.)

## A. The 26 US/EU panel companies and Lever (assigned)

| Company | Headcount | As of | Basis | Source(s) | Conf. | Derived ONS band | Notes |
|---|---|---|---|---|---|---|---|
| Duolingo (`duolingo`) | 900–1,001 | Dec 2025 – Mar 2026 | worldwide | Company-reported 900 (31 Dec 2025, via search summary); Revelio Labs 1,001 (Mar 2026) | Medium | **250-2,499** | Two other aggregators show 2,948–3,100; excluded as inconsistent with the company's own figure. If they were right the band would be 2,500+. |
| Gusto (`gusto`) | 3,700–3,979 | Mar 2026 | worldwide | Revelio Labs 3,979; another aggregator ~3.7K | Medium | **2,500+** | One aggregator shows 7,834; excluded (unexplained, ~2x every other source). |
| Carta (`carta`) | 2,000–2,100 | Apr 2026 | worldwide | Aggregators only (~2K; ~2.1K) | Low | **250-2,499** | Close to the 2,500 boundary but below it in every figure seen. |
| Khan Academy (`khanacademy`) | 258–2,365 | unknown / Jul 2026 | worldwide | Form 990-derived 258 (year not stated, via aggregator) vs directory sites 2,315–2,365 | Low | **AMBIGUOUS** | Nonprofit; the two figures differ ~9x. The directory counts are very likely inflated (volunteers/contractors/ex-staff), but 258 sits only 8 above the 250 boundary and its year is unknown. Needs the latest Form 990 PDF (Part I line 5). |
| Doximity (`doximity`) | 880 | 31 Mar 2026 | worldwide | 10-K FY2026 (SEC): 880 full-time equivalent employees | High | **250-2,499** | Full-time equivalents, not headcount. |
| Glossier (`glossier`) | 402–679 | Dec 2025 – Jul 2026 | worldwide | Aggregators: 679 (Dec 2025), ~471–482 (Jul 2026), 402; layoffs of >50 in Feb 2026 (BoF) | Medium | **250-2,499** | Wide spread but every figure is inside 250–2,499. |
| Peloton (`peloton`) | 2,262 | 30 Jun 2026 | worldwide | 10-K FY2026 (SEC): 1,736 US + 526 international | High | **250-2,499** | 238 below the 2,500 boundary. US figure is total individuals employed; 1,673 of them full-time. |
| N26 (`n26`) | 1,600–2,399 | 2026 | worldwide | Wikipedia ~1,600; PitchBook 2,399; Owler 1,000–5,000 | Low | **250-2,499** | High end is close to 2,500. |
| GetYourGuide (`getyourguide`) | 1,300–1,502 | Feb – Mar 2026 | worldwide | Aggregators: 1.3K, 1.4K (1,410 at 28 Feb 2026), 1,502 | Medium | **250-2,499** |  |
| Contentful (`contentful`) | 956–1,045 | Dec 2025 – Jul 2026 | worldwide | Aggregators: 956 (Dec 2025) to 1,045 (31 Jul 2026) | Medium | **250-2,499** | Salesforce announced an acquisition in June 2026 — see the enterprise-group caveat. |
| Trustpilot (`trustpilot`) | 1,108 | 31 Dec 2025 | worldwide | Trustpilot Group plc Annual Report 2025: 1,108 (+120 on prior year) | High | **250-2,499** |  |
| Typeform (`typeform`) | 728–886 | Mar – Jul 2026 | worldwide | Revelio Labs 886; another source ~728 | Medium | **250-2,499** |  |
| Algolia (`algolia`) | 862–936 | 2025 – Aug 2026 | worldwide | Aggregators: 862 (2025), ~881 (Jul 2026), 936 (Aug 2026) | Medium | **250-2,499** |  |
| Gymshark (`gymshark`) | 900–2,554 | Dec 2025 – Jul 2026 | worldwide | Revelio Labs 1,980 (Dec 2025); Tracxn/RocketReach 2,552–2,554 (Jul 2026); another source 'over 900' | Low | **AMBIGUOUS** | Straddles the 2,500 boundary. UK-headquartered, so the Companies House accounts ('average monthly number of employees') would settle it — paywalled on the sites tried; a human should open the filing. |
| Spotify (`spotify`) | 7,287–7,323 | FY2025 | worldwide | 20-F FY2025 (SEC): 7,323 full-time employees at year end; 7,287 average | High | **2,500+** | Worldwide; UK share not needed for a UK cross-check of a Swedish company. |
| Moonpig (`moonpig`) | 763 | FY to 30 Apr 2026 | worldwide | Moonpig Group plc annual report FY2026: 763; ~93% of employees in the UK | High | **250-2,499** | ≈710 in the UK. |
| Substack (`substack`) | 1,634–3,513 | Mar – Jul 2026 | worldwide | Revelio Labs 1,634 (Mar 2026); other aggregators 2.6K–3.5K | Low | **AMBIGUOUS** | Private company; sources disagree by 2x and straddle 2,500. No primary source exists to settle it. |
| Vanta (`vanta`) | 1,635–1,979 | Mar 2026 | worldwide | Revelio Labs 1,635; PitchBook 1,979; another 1,766 | Medium | **250-2,499** |  |
| Lemonade (`lemonade`) | 1,282 | 31 Dec 2025 | worldwide | 10-K FY2025 (SEC): 1,282 total; 810 in the US, rest mainly Israel and the Netherlands | High | **250-2,499** |  |
| Pleo (`pleo`) | 737–1,000 | Mar – Aug 2026 | worldwide | Revelio Labs 737 (Mar 2026); other aggregators 933–1K | Medium | **250-2,499** |  |
| Mollie (`mollie`) | 1,100–1,170 | Feb – Jul 2026 | worldwide | Aggregators: ~1.1K; 1,170 (31 Jul 2026); Amsterdam hosts about half | Medium | **250-2,499** |  |
| DeepL (`deepl`) | 750–1,547 | May 2026 | worldwide | Reported 'slightly more than 1,000' before announcing ~250 cuts (25%) in May 2026; Tracxn 1,547 | Medium | **250-2,499** | Range brackets the announced cut; every value is inside 250–2,499. |
| Paddle (`paddle`) | 397–425 | 2026 | worldwide | Aggregators: ~397; 403; 425 (Aug 2026) | Medium | **250-2,499** |  |
| Synthesia (`synthesia`) | 550–700 | 2025 – 2026 | worldwide | Wikipedia 550 (2025); Forbes 600 (30 Jan 2026); ~700 (2026); offices also in Austin, Berlin, Paris, Zurich | Medium | **250-2,499** | UK share unknown. |
| Thought Machine (`thought-machine`) | 497–531 | End 2025 – May 2026 | worldwide | Revelio Labs 531 (Mar 2026); 497 full-time at end 2025; PitchBook 529 | Medium | **250-2,499** |  |
| Zego (`zego`) | 303–365 | May – Jul 2026 | worldwide | Aggregator 365 (31 May 2026); a 17% reduction announced Jul 2026 (~303 after) | Low | **250-2,499** | After the cut the figure is only ~50 above the 250 boundary. |
| Lever (the ATS company) (`lever`) | — | Aug 2022 | parent | Parent group Employ Inc.: 850 employees across Jobvite, JazzHR and Lever (Aug 2022, stale) | Low | **not derived** | No Lever-only figure found and the group figure is four years old. Not derived — left untagged rather than guessed. |

## B. The 21 UK panel companies (scope extension — see change request)

| Company | Headcount | As of | Source(s) | Conf. | Old bucket | Derived ONS band | Notes |
|---|---|---|---|---|---|---|---|
| Monzo (`monzo`) | 5,275–5,429 | Mar 2026 | Revelio Labs 5,429; Wikipedia 5,275; D&I report 5,281 | High | Medium | **2,500+** | ⚠ old label **Medium** does not fit (Large) Old bucket was Medium; the headcount is above 5,000 (the old Large). |
| Deliveroo (`deliveroo`) | 3,296–3,839 | Dec 2024 – Dec 2025 | Corporate employees 3,296 (Dec 2025), 3,839 (Dec 2024); excludes ~135–180k self-employed riders | Medium | Medium | **2,500+** | One aggregator shows 11,381 (Jun 2026); excluded as a different basis. Reported as acquired (DoorDash) — see enterprise-group caveat. |
| Wise (`wise`) | 7,585 | Mar 2026 | Revelio Labs 7,585 (FY2026 results 25 Jun 2026) | Medium | Medium | **2,500+** | ⚠ old label **Medium** does not fit (Large) Old bucket was Medium; headcount is well above 5,000. |
| Auto Trader (`autotrader`) | 1,249–1,267 | FY Mar 2025 – H1 FY26 | Annual report: average FTE 1,267 (FY to Mar 2025); 1,249 (six months to Sep 2025) | High | Medium | **250-2,499** | Full-time equivalents. |
| Cleo (`cleo`) | 666 | Mar 2026 | Revelio Labs 666; workforce 64.7% Northern Europe | Medium | Small/Growth | **250-2,499** | ⚠ old label **Small/Growth** does not fit (Medium) Old bucket was Small/Growth (50–500); headcount is above 500. |
| Rightmove (`rightmovecareers`) | 861–1,100 | 2024 – Dec 2025 | Company results: 'just under 900' (2024); Owler 861; LeadIQ ~1.1K | Medium | Medium | **250-2,499** | The 2025 annual report PDF was not opened; exact average-employee note not read. |
| Ocado Group (`ocadogroup`) | 11,941–11,942 | FY to 30 Nov 2025 | Annual report / Revelio Labs: 11,941 | Medium | Medium | **2,500+** | ⚠ old label **Medium** does not fit (Large) Old bucket was Medium; headcount is more than double 5,000. Group total — UK share not found. |
| Starling Bank (`starling-bank`) | 4,101–4,158 | 2025 – 2026 | Wikipedia 4,158 (2026); Revelio Labs 4,102; 4,101 (2025) | Medium | Medium | **2,500+** |  |
| Cuvva (`cuvva`) | 96–100 | May – Jul 2026 | Aggregators: 96 (31 May 2026); ~98; ~100 | Medium | Small/Growth | **50-249** |  |
| Zopa (`zopa`) | 900–1,000 | 2026 | PitchBook ~1,000; company press page '900+' (older) | Medium | Medium | **250-2,499** | LinkedIn range shown as 1,001–5,000 by one source — outside every other figure. |
| Trainline (`trainline`) | 990 | 28 Feb 2026 | Annual report: 990 (unchanged on prior year) | High | Medium | **250-2,499** |  |
| Quantexa (`quantexa`) | 872–951 | Dec 2025 – Jun 2026 | Aggregators: 951 (Dec 2025), ~897 (May 2026), 893 (Jun 2026), ~872 | Medium | Medium | **250-2,499** |  |
| Faculty (`faculty`) | 100–400 | 2026 | PitchBook 400; another 279; Owler 100–250 | Low | Medium/Small | **AMBIGUOUS** | Accenture reported to have acquired Faculty in Jan 2026 — see enterprise-group caveat. Straddles the 250 boundary. |
| Motorway (`motorway`) | 403–450 | 2024 – 2026 | Average employees 448 (2024), 403 (2025); ~428; 450+ (Wikipedia) | Medium | Medium | **250-2,499** | ⚠ old label **Medium** does not fit (Small/Growth) |
| Marshmallow (`marshmallow`) | 665–700 | Apr 2025 – Jun 2026 | Aggregators: 700 (Apr 2025, London and Budapest); 665 (30 Jun 2026) | Medium | Medium | **250-2,499** | UK share is below the total (Budapest office); likely still above 250. |
| Multiverse (`multiverse`) | 813–1,269 | Jan – Jun 2026 | 813 (Jan 2026); 1,269 (30 Jun 2026); rapid hiring | Medium | Medium | **250-2,499** |  |
| Attio (`attio`) | 115–177 | 2026 | PitchBook 115; Tracxn 177 (30 Apr 2026); Gartner range 51–200 | Medium | Small/Growth | **50-249** |  |
| Griffin (`griffin`) | 139–145 | Jan – Mar 2026 | Aggregators: 139 (5 Jan 2026); ~145 (Mar 2026) | Medium | Small/Growth | **50-249** |  |
| Sylvera (`sylvera`) | 150 | 2026 | PitchBook: 150 (single source) | Low | Small/Growth | **50-249** |  |
| Beamery (`beamery`) | 200–227 | 2026 | Wikipedia ~200; another source 227 (early 2026) | Medium | Small/Growth | **50-249** | 227 is 23 below the 250 boundary. |
| incident.io (`incident`) | 82–208 | Dec 2025 – Jul 2026 | Tracxn 208 (31 Jul 2026); TipRanks 200; PitchBook 146; LeadIQ ~140; Latka 82 | Medium | Small/Growth | **50-249** | Wide spread; every figure is inside 50–249. |

## C. The original 34 with headcounts — ONS bands derived from the figures already on file

Counts from `research/2026-09-19-original-35-size-bands.md` (Revelio Labs / company-reported, cited there). Lever (the company) has no figure — see table A.

| Company | Headcount | Old label | Derived ONS band | Flag |
|---|---|---|---|---|
| Stripe (`stripe`) | 9,007 | Large | **2,500+** |  |
| Airbnb (`airbnb`) | 8,200–8,539 | Large | **2,500+** |  |
| Pinterest (`pinterest`) | 5,491 | Large | **2,500+** |  |
| Asana (`asana`) | 1,922 | Medium | **250-2,499** |  |
| Reddit (`reddit`) | 2,751 | Medium | **2,500+** |  |
| Robinhood (`robinhood`) | 4,569 | Medium | **2,500+** |  |
| Coinbase (`coinbase`) | 4,300–4,951 | Medium | **2,500+** |  |
| Affirm (`affirm`) | 2,366 | Medium | **250-2,499** |  |
| Webflow (`webflow`) | 1,600–1,649 | Medium | **250-2,499** |  |
| Figma (`figma`) | 2,045 | Medium | **250-2,499** |  |
| Airtable (`airtable`) | 900–1,160 | Medium | **250-2,499** |  |
| Cloudflare (`cloudflare`) | 4,000–5,668 | Large | **2,500+** |  |
| Twilio (`twilio`) | 5,709 | Large | **2,500+** |  |
| Discord (`discord`) | 2,358 | Medium | **250-2,499** |  |
| GitLab (`gitlab`) | 2,700 | Medium | **2,500+** |  |
| Palantir (`palantir`) | 4,516 | Medium | **2,500+** |  |
| Plaid (`plaid`) | 1,697 | Medium | **250-2,499** |  |
| Clari (`clari`) | 1,658 | Medium | **250-2,499** |  |
| Restream (`restream`) | 94 | Small/Growth | **50-249** |  |
| Ramp (`ramp`) | 2,518 | Medium | **2,500+** |  |
| Linear (`linear`) | 118 | Small/Growth | **50-249** |  |
| OpenAI (`openai`) | 7,800–8,000 | Large | **2,500+** |  |
| Notion (`notion`) | 1,920–4,162 | Medium | **AMBIGUOUS** |  |
| Modal (`modal`) | 100–231 | Small/Growth | **50-249** |  |
| Replit (`replit`) | 417 | Small/Growth | **250-2,499** |  |
| Mercury (`mercury`) | 1,729 | Medium | **250-2,499** |  |
| Deel (`deel`) | 11,293 | Large | **2,500+** |  |
| Loom (`loom`) | 350 | Small/Growth | **250-2,499** |  |
| Vercel (`vercel`) | 847 | Medium | **250-2,499** |  |
| Supabase (`supabase`) | 240–386 | Small/Growth | **AMBIGUOUS** |  |
| Perplexity (`perplexity`) | 986–1,500 | Medium | **250-2,499** |  |
| ElevenLabs (`elevenlabs`) | 400–880 | Medium | **250-2,499** |  |
| Ashby (company) (`ashby`) | 406–491 | Small/Growth | **250-2,499** |  |
| Watershed (`watershed`) | 599 | Medium | **250-2,499** |  |

## D. What this shows

1. **The old UK size buckets can't be trusted.** 5 of the 21 (Monzo, Wise, Ocado Group, Cleo, Motorway) don't fit their headcount even under the old four-band scheme: Monzo, Wise and Ocado are above 5,000 (old "Large", tagged Medium), Cleo (666) is above 500 (tagged Small/Growth), and Motorway (403–450) is below 500 (tagged Medium). This is the concrete case for Option A: a bucket someone assigned by impression drifts; a stored, cited headcount doesn't.
2. **Six companies can't be given a band honestly** — the range straddles a boundary. What would settle each:
   | Company | Straddles | What would resolve it |
   |---|---|---|
   | Gymshark | 250–2,499 / 2,500+ | Latest Companies House accounts ("average monthly number of employees") — UK-headquartered, so it is a public filing |
   | Faculty | 50–249 / 250–2,499 | Companies House accounts; also affected by the acquisition (see caveat below) |
   | Khan Academy | 50–249 / 250–2,499 / unreliable | Latest Form 990 (Part I line 5) |
   | Substack | 250–2,499 / 2,500+ | Nothing public; private company, sources disagree 2x. Best left AMBIGUOUS |
   | Notion | 250–2,499 / 2,500+ | From the 2026-09-19 research (1,920–4,162); no new evidence |
   | Supabase | 50–249 / 250–2,499 | From the 2026-09-19 research (240–386); no new evidence |
   Plus **Lever**: no company-level figure, left untagged.
3. **Our sample contains no company under 50 employees.** Across the 82 tracked companies: 9 in 50–249, 46 in 250–2,499, 20 in 2,500+, 6 ambiguous, 1 not derived — **none in ONS's 1–9 or 10–49 bands.** For context, ONS's own Jun–Aug 2026 figures (read 2026-09-24) put about 27% of UK vacancies at businesses with fewer than 50 employees (91k + 99k of 702k), which this panel structurally cannot represent. That is the kind of "how does our sample lean" finding a size cross-check exists to show — and it holds whichever way the six ambiguous cases fall.
4. **Every figure is worldwide (or group).** Only Moonpig gives a UK share (~93%). ONS measures UK business size, so bands derived here are approximations for multinationals (Stripe, Spotify, Duolingo, …). For UK-headquartered firms the difference is usually small; for firms with a UK office of a few hundred people it can move the band.

## E. Caveat: ONS's unit is the enterprise (group), not the company brand — **unverified, ask ONS**

**[inference — not read on any page this session]** ONS's business register groups legal units into *enterprises*; the Vacancy Survey's methodology says questionnaires go "mainly via head offices". If the size band is the size of the enterprise group, then a company acquired by a larger group would be counted at the **group's** size in ONS's data, not its own. Companies in this panel reported as acquired in 2026 or earlier: **Faculty** (Accenture, Jan 2026), **Deliveroo** (reported acquisition by DoorDash), **Contentful** (Salesforce announced Jun 2026), **Lever** (Employ Inc., 2022). For these, the standalone headcount above may **understate** the size ONS would assign. This is one more reason the headcount table should record *what was measured* (standalone company vs group) and why the question to ONS (`changes/2026-09-25-employer-size-standard-bands.md`, Step 4) matters. It does **not** change any band in this file — it flags where the derived band may not match ONS's own classification.

## F. Primary sources to spot-check before use (found via search; not opened)

- Doximity 10-K FY2026 — https://www.sec.gov/Archives/edgar/data/0001516513/000151651326000025/docs-20260331.htm
- Peloton 10-K FY2026 — https://www.sec.gov/Archives/edgar/data/0001639825/000163982526000038/pton-20260630.htm
- Lemonade 10-K FY2025 — https://www.sec.gov/Archives/edgar/data/1691421/000169142126000016/lmnd-20251231.htm
- Spotify 20-F FY2025 — https://www.sec.gov/Archives/edgar/data/1639920/000162828026006874/ck0001639920-20251231.htm
- Trustpilot Annual Report 2025 — https://downloads.ctfassets.net/wonkqgvit51x/3ZteL0rrKrX9tFmBauBuPX/010202ae42bdac8e876e0f28384bcc88/Trustpilot_Annual_Report_2025_FINAL.pdf
- Auto Trader annual report — https://plc.autotrader.co.uk/media/ujinai40/at-ar25-web.pdf
- Rightmove annual report 2025 — https://plc.rightmove.co.uk/content/uploads/2026/03/RIG004-V2-2025-ARA-WEB-READY-260323.pdf
- Monzo annual report 2026 — https://monzo.com/annual-report/2026/Monzo-Annual-Report-2026.pdf
- Ocado Group annual report 2025 — https://www.ocadogroup.com/investors/results-and-presentations/2025-annual-report
- Wise FY2026 results — https://owners.wise.com/news-releases/news-release-details/wise-group-plc-reports-full-year-2026-financial-results
- Starling Bank annual report 2026 — https://www.starlingbank.com/investors/2026/annual-report-2026/
- Moonpig annual report FY2026 — https://www.moonpig.group/investors/results-reports-and-presentations/
- Gymshark filings — https://find-and-update.company-information.service.gov.uk/company/08130873/filing-history and https://find-and-update.company-information.service.gov.uk/company/12711328
- Khan Academy Form 990s — https://projects.propublica.org/nonprofits/organizations/261544963

Most of the rest are Revelio Labs workforce-intelligence pages and aggregators (Tracxn, PitchBook, LeadIQ, Owler); these are estimates of LinkedIn-visible headcount, not reported figures, and disagree with each other and with filings.

## G. Open items
- **Resolved 2026-09-25 (PM decision): the six ambiguous companies were assigned the more probable band** rather than left ambiguous. Five straddling entries (Gymshark, Faculty, Substack, Notion, Supabase) → 250–2,499, with reasoning stored per company in `employer_headcount.py`; Khan Academy's range sits inside 250–2,499 by the numbers. All stay `low` confidence. The tables above are unchanged as *evidence*.
- Open the six "High" filings above and the Gymshark / Faculty / Khan Academy filings; confirm or correct the ranges.
- Ask ONS (labour.market@ons.gov.uk, vacancy.survey@ons.gov.uk): is "register employment" UK-only? Is a subsidiary sized as its own enterprise or as its group?
- Decide (PM) what to do with the six ambiguous companies in the platform: store as `ambiguous` (recommended, and the cross-check simply excludes them and says how many) or resolve by hand.
- This research is **evidence, not data**: nothing here is loaded anywhere until the implementation step (held for a PM go).
