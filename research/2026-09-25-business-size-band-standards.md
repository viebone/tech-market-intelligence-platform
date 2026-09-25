source: internal
date: 2026-09-25

# Business size bands — what the standards are, why, and whether they apply outside the UK

Evidence record for `changes/2026-09-25-employer-size-standard-bands.md`. Each finding is tagged
with how it was obtained, because that decides how far to trust it:

- **[read]** — fetched and read directly on 2026-09-25 (the wording below is what the page said).
- **[snippet]** — taken from a web-search result summary; the primary document was **not** opened.
  Reasonable, but verify before relying on it for anything that matters.
- **[inference]** — my own reasoning, not stated by any source. Labelled so it is never mistaken
  for a finding.

## 1. ONS — the Vacancy Survey (the source that started this)

Source: ONS "Vacancy Survey QMI" (quality and methodology information),
https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/methodologies/vacancysurveyqmi **[read]**

- **Bands, verbatim:** "Businesses are grouped into five employment size-bands: 2 to 9, 10 to 49,
  50 to 249, 250 to 2,499 and 2,500 and over."
- **A discrepancy worth knowing:** the published data file (`VACS03`, read 2026-09-24) labels the
  smallest band **"1 - 9 employed"**; the methodology text says **"2 to 9"**. The methodology
  explains why they can both be true: "The Vacancy Survey uses **modelling rather than sampling**
  for enterprises with a register employment of 1. After detailed analysis it was found that the
  number of returns greater than zero from these companies was very small and was placing an
  unnecessary burden on these small companies." So businesses with one person on the register are
  in the published "1–9" figure but are *estimated by a model*, not surveyed. **[read]**
- **What "size" means:** the survey weights by **register employment** from the ONS business
  register (IDBR) — an enterprise-level figure held on the register, not a headcount the business
  reports on the form. Whether that counts only UK employment or a group's worldwide employment
  is **not stated on the page** — to be confirmed with ONS (contact on the dataset page). **[read]** for the
  wording, **[inference]** for the UK-only reading.
- **How the bands are used (the closest thing to a "why"):** they are the survey's **sampling
  strata**. "Questionnaires are sent to a sample of approximately 6,100 businesses every month …
  Approximately 1,400 large businesses are included in the survey every month. The remaining 4,700
  are smaller enterprises sampled randomly on a quarterly basis" and kept in the survey for five to
  nine quarters "depending on the size of the business." **[read]**
- **What the page does *not* say:** why the top split is at **2,500** specifically. It never
  states a rationale for any cut point. **[read]**
- **[inference]** — the 2,500 split most plausibly exists because a vacancy survey is dominated by
  a small number of very large employers, so the largest are surveyed every month while smaller
  ones are sampled; the top band marks where that "always included" group begins. I did not confirm
  that the ~1,400 "large businesses" are exactly the 2,500+ band.
- **Geography:** "The survey covers all sectors of the economy and all industries in England,
  Scotland and Wales (**Great Britain**)". Great Britain results are "weighted up … using
  employment estimates (**Northern Ireland accounts for around 3% of UK employment**)." So the
  published "UK" vacancy figures are a Great Britain survey scaled to the UK, not a UK-wide
  survey. **[read]** — *This is new and affects how Story 5 should be worded; see the change log.*
- **Excluded sectors:** agriculture, forestry and fishing (SIC 2007 section A); activities of
  households as employers (T); employment agencies (division 78). **[read]**
- **Seasonal adjustment:** "The three-month moving average series by industry and by size of
  business is seasonally adjusted directly … The monthly series is presented as a non-seasonally
  adjusted series." **[read]** — note the *file* for size of business states no adjustment (see
  `research/2026-09-24-ons-licence-and-access-confirmation.md`), yet the methodology says the
  by-size series is seasonally adjusted. The two are consistent in substance; the file is silent.
  We still store `unknown` for the size file — what the file says — and this QMI statement is a
  documented reason to expect it is adjusted. Confirm with ONS before stating it to users.
- **Revisions:** each month the latest estimate plus revisions to the previous three months; in
  April each year, the previous three years (38 months). **[read]**

The ONS page for the UK Standard Industrial Classification has nothing on size bands **[read]** — ONS
does not appear to publish one central "our size bands are X because Y" page; the bands are
defined survey by survey.

## 2. The international "core": 10 / 50 / 250

- **Eurostat** (Statistics Explained, "Glossary: Enterprise size") **[read]**: micro **< 10**
  persons employed; small **10–49**; medium-sized **50–249**; large **250 or more**; SMEs are
  **< 250**. The measure is *persons employed* — which "should not be confused with employees or
  full-time equivalents; 'persons employed' includes employees but also working proprietors,
  partners working regularly in the enterprise and unpaid family workers." In structural business
  statistics the classes use headcount only, no turnover or balance sheet.
- **OECD** **[snippet]**: micro 1–9, small 10–49, medium 50–249, large 250+; data collected through
  harmonised questionnaires from national statistical offices.
- **UK government business population statistics (Department for Business and Trade)**
  **[snippet]**: micro 0–9 (shown as 1–9 with "non-employers" separate), small 10–49, medium
  50–249, large 250+.
- **So ONS's lower three cut points (10, 50, 250) are the shared international standard.** Only the
  split of "large" into 250–2,499 and 2,500+ is ONS's own.

**Why 10 / 50 / 250?** The primary documents were not opened, so this is what the search results
said **[snippet]**: in a 1992 report to the Council (requested at the 28 May 1990 "Industry"
Council) the Commission "proposed limiting the proliferation of definitions of small and
medium-sized enterprises", proposing thresholds of **50 and 250 employees**. Commission
Recommendation **96/280/EC** (3 April 1996) set micro <10, small <50, medium <250, on the idea that
"the existence of different definitions at Community level and at national level could create
inconsistencies" and that, "following the logic of a single market without internal frontiers, the
treatment of enterprises should be based on a set of common rules." Recommendation **2003/361/EC**
replaced it from 1 January 2005, updating the financial ceilings and adding rules for linked
enterprises. **The reason for the numbers themselves is a harmonisation convention — the sources
found give no economic derivation for why 250 rather than, say, 200.** Do not present the
thresholds to users as if they were scientifically derived.

**EU policy definition is more than headcount [snippet]:** for policy eligibility an SME must also
meet a **turnover or balance-sheet ceiling** and ownership-linkage rules; statistical size classes
(Eurostat) use headcount only. **New in 2025 [snippet]:** Commission Recommendation (EU) 2025/1099
(21 May 2025) adds a **"small mid-cap"** category — fewer than **750** employees and turnover not
above **EUR 150 million** or balance sheet not above **EUR 129 million** — for firms that have
outgrown 250 employees but are not "large". So the EU itself is now adding a band between 250 and
"large" — the same region of the scale where ONS and the US both split differently.

## 3. United States — different again

- **BLS JOLTS** **[read]** — six *establishment* (site) size classes: **1–9, 10–49, 50–249, 250–999,
  1,000–4,999, 5,000+**. "These estimates are based on **size of establishment, not size of firm**."
  Size is the maximum employment over the last 12 months. The page gives no rationale for the cut
  points, only that the sampling frame is stratified by size class (same role as ONS's bands).
- **BLS QCEW / BED firm size classes** **[snippet]**: 1–4, 5–9, 10–19, 20–49, 50–99, 100–249,
  250–499, 500–999, 1,000+.
- **US Small Business Administration** **[snippet]**: "small business" is typically fewer than
  **500 employees**, but the standard is **set per industry** and is often based on annual receipts
  instead (many manufacturers: 1,000 employees).

## 4. What this means for "does this apply to all countries?"

| Question | Answer |
|---|---|
| Are 10 / 50 / 250 international? | **Largely yes** — Eurostat, OECD, UK statistics and even the US JOLTS use 10, 50 and 250 as boundaries |
| Is ONS's five-band scheme international? | **No** — the 2,500 split is ONS-specific; the US splits the large end at 1,000 and 5,000; the SBA uses 500; the EU is adding 750 |
| Is the *measure* the same everywhere? | **No** — persons employed (Eurostat) vs register employment (ONS) vs establishment employment (US JOLTS) vs enterprise-with-ownership-links (EU policy) |
| Is "size" one company's global headcount? | **Not for any of these** — they measure the national business unit (UK enterprise, US establishment), not a multinational's worldwide total |

**Consequence for this platform:** no single publisher's bands can be "the" standard, and a
company's *worldwide* headcount (what most of our research figures are) is not what ONS or the US
bands measure. The robust design is to store the **headcount estimate itself** (a range, with
basis — worldwide or national — source and date) and **derive a named band per publisher**
(`ONS_VS_size_band`, an EU/OECD 10/50/250 class, `US_JOLTS_establishment_size_class`, …) when a
cross-check needs one. That fits the `{system, code, label}` dimension model already specified in
`backend/specs/trusted-statistics/api.md`.

## 5. Sources not opened / gaps
- Eurostat's own methodology, Recommendation 96/280/EC and 2003/361/EC, 2025/1099 primary text,
  and the DBT Business Population Estimates methodology were **not** read — search summaries only.
- Whether ONS "register employment" is UK-only enterprise employment: not stated; ask ONS
  (labour.market@ons.gov.uk / vacancy.survey@ons.gov.uk).
- Other countries' statistical offices (Statistics Canada, ABS, Destatis…) were not checked; the
  "core 10/50/250" finding rests on Eurostat, OECD, ONS/DBT and US JOLTS only.
