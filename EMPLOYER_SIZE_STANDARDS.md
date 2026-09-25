# Employer Size Standards — how "company size" is defined, by whom, and what we do about it

**What this is:** the one place that explains how official bodies classify business size, why,
whether those classifications apply outside the UK, and how this platform's own employer size
metadata should relate to them. Reference material, not a spec. Evidence, with sources and how
confident each finding is: `research/2026-09-25-business-size-band-standards.md`. The change that
acts on it: `changes/2026-09-25-employer-size-standard-bands.md` (status `in-progress`). **The
design in §4 was decided by the PM on 2026-09-25 and IMPLEMENTED the same day (`backend/src/employer_headcount.py`) — not yet
deployed to production.**

Last reviewed: 2026-09-25 (after the PM's decisions and the panel headcount research).

---

## 1. The size classifications in use

| Scheme | Bands (employees unless stated) | What is counted | Unit | Where it matters to us |
|---|---|---|---|---|
| **ONS Vacancy Survey** (VACS02/VACS03) | 1–9 (file) / 2–9 (methodology), 10–49, 50–249, 250–2,499, **2,500+** | Register employment held on the ONS business register (IDBR) | Enterprise | The source Story 5 reads |
| **UK business population statistics** (DBT) | Micro 0–9 (shown 1–9), small 10–49, medium 50–249, large 250+ | Employment | Enterprise | Reference only |
| **Eurostat** (structural business statistics) / **OECD** | Micro <10 (OECD: 1–9), small 10–49, medium 50–249, large 250+ | **Persons employed** — includes working proprietors, partners and unpaid family workers; *not* employees, *not* full-time equivalents | Enterprise | Future EU/OECD publishers |
| **EU policy definition** (Recommendation 2003/361/EC; **2025/1099** adds "small mid-cap") | Micro <10, small <50, medium <250, **small mid-cap <750** | Headcount **and** a turnover / balance-sheet ceiling **and** ownership-linkage rules | Enterprise (autonomous / partner / linked) | Not statistics — eligibility rules; don't mix with statistical classes |
| **US BLS JOLTS** | 1–9, 10–49, 50–249, 250–999, 1,000–4,999, **5,000+** | Maximum employment over the last 12 months | **Establishment** (a site), *not* the firm | Future US publisher |
| **US BLS BED / QCEW** | 1–4, 5–9, 10–19, 20–49, 50–99, 100–249, 250–499, 500–999, 1,000+ | Employment | Firm / establishment | Future US publisher |
| **US SBA** | Usually <500, **set per industry**, sometimes by revenue instead (many manufacturers 1,000) | Employees or receipts | Firm | Eligibility rules — not statistics |
| **This platform, today** | Startup <50, Small/Growth 50–500, Medium 500–5,000, Large 5,000+ | A headcount estimate — usually **worldwide**, from conflicting sources | Company | `raw_postings.employer_size_band` (nothing reads it) |

## 2. Why ONS uses these bands

- **10 / 50 / 250 are a harmonisation convention, not a derived quantity.** They come from the
  EU: a 1992 Commission report proposed 50 and 250 to stop "the proliferation of definitions";
  Recommendation 96/280/EC (1996) set micro <10, small <50, medium <250 so that treatment of
  firms follows "a set of common rules" across a single market; 2003/361/EC replaced it from
  2005. OECD, Eurostat and UK statistics adopted the same lines so figures compare across
  countries. The sources found **give no economic derivation** for why 250 rather than another
  number — don't describe them to users as scientifically chosen.
- **The extra 2,500 split is ONS's own, and ONS doesn't say why.** ONS uses its bands as the
  Vacancy Survey's **sampling strata**: about 6,100 businesses a month, of which "approximately
  1,400 large businesses are included in the survey every month" and the other ~4,700 smaller ones
  are sampled quarterly and rotated through the survey for five to nine quarters "depending on the
  size of the business". *(Our reading, not ONS's statement: the top band marks where "always
  surveyed" begins, because a vacancy survey is dominated by a few very large employers.)*
- **The "2–9" vs "1–9" difference:** businesses with one person on the register are estimated by a
  model rather than surveyed — returns from them were "very small" and "placing an unnecessary
  burden on these small companies". The published "1–9" includes those modelled units.

## 3. Does this apply to every country?

**Partly.**
- **Shared everywhere we checked:** the boundaries **10, 50 and 250**. Eurostat, OECD, UK statistics
  and even the US JOLTS use them.
- **Not shared:** anything above 250. ONS splits at 2,500; the US JOLTS at 1,000 and 5,000; the US
  SBA uses about 500; the EU has just added 750. ONS's five-band scheme is **UK-specific**.
- **Not shared:** *what is counted* (persons employed vs register employment vs establishment
  employment), and *what unit* (enterprise vs site).
- **None of them measure a multinational's worldwide headcount** — they measure the national
  business (a UK enterprise, a US establishment).
- Other countries' statistical offices (Canada, Australia, Germany, …) were **not** checked.

## 4. What this means for our metadata (**decided by the PM 2026-09-25; implemented, not yet deployed**)

**Decisions:** headcount is the source of truth (Option A); the platform's **default size label is ONS's five
bands** (chosen for consistency with the source it is compared against). Consequence: the label inherits
ONS's UK-specific 2,500 split; the international 10/50/250 class and other publishers' systems stay derivable
from the same headcount when needed.


1. **Store the headcount estimate, not a band.** A range, with its **basis** (worldwide / national
   / unknown), **source** and **as-of date**. Bands are then *derived*, per publisher, as named
   systems: `ONS_VS_size_band` (five bands — **the platform's default label**, PM decision), an
   international 10/50/250 class, `US_JOLTS_establishment_size_class`, … — the same `{system, code, label}` shape the
   trusted-statistics dimension model uses.
2. **A range that straddles a boundary is "ambiguous" unless a human records a choice.** The PM decided (2026-09-25)
   to choose the more probable band for the companies affected; each choice stores its reasoning and stays
   `confidence = low`. A company with no figure at all stays `None` — never guessed.
3. **Compare like with like.** A UK cross-check uses **UK-based roles** and, ideally, the **UK
   headcount** of the employer; a worldwide headcount is labelled as such wherever it is used.
4. **Never present the thresholds as natural or scientific**, and never mix EU/US *policy*
   definitions (which add turnover and ownership tests) with *statistical* size classes.
5. **Keep the two things apart in wording:** "employees" (ONS register employment, JOLTS) and
   "persons employed" (Eurostat, which includes owners and unpaid family workers) are not the same
   measure.

## 4b. What the headcount research found (2026-09-25, `research/2026-09-25-panel-headcount-research.md`)

- 82 tracked companies: **9** in ONS's 50–249, **52** in 250–2,499, **20** in 2,500+, **1 with no figure** (Lever) —
  and **none** under 50 employees. (The research found 6 straddling ranges; by PM decision 5 were resolved to the more
  probable band — all 250–2,499, each with recorded reasoning — and Khan Academy's range sits inside one band.) ONS's own figures put about
  27% of UK vacancies at businesses under 50; the panel cannot represent them.
- **5 of the 21 user-assigned UK buckets didn't fit the headcount** (Monzo, Wise, Ocado, Cleo, Motorway) —
  the practical argument for storing a cited number instead of a bucket.
- Every figure is a **worldwide/group** headcount, gathered from search summaries (filings not opened) — see the
  research file for confidence per company.

## 4c. A caveat to verify: ONS may size the *group*, not the brand

**[inference, not read on any page]** ONS's business register groups legal units into enterprises, and the survey
goes "mainly via head offices". If so, a company acquired by a larger group is sized as the group. Panel companies
reported as acquired: Faculty (Accenture), Deliveroo (DoorDash), Contentful (Salesforce, announced), Lever (Employ
Inc.). Ask ONS before relying on a derived band for these.

## 5. Open questions (carry into the change request)
- Is ONS "register employment" UK-only enterprise employment? Ask ONS.
- What to do with the 6 ambiguous companies and Lever (store `ambiguous` — recommended — or resolve by hand)?
- Other countries' offices, and the primary EU texts (96/280/EC, 2003/361/EC, 2025/1099), were not
  read — verify before quoting any threshold or ceiling in a user-facing surface.

## 6. Related
- `research/2026-09-25-business-size-band-standards.md` — sources, quotes, confidence per finding
- `changes/2026-09-25-employer-size-standard-bands.md` — the change request
- `EMPLOYER_PANEL.md` — the panel and its current size bands
- `research/2026-09-19-original-35-size-bands.md` — the headcount research already on file
- `backend/specs/trusted-statistics/api.md` — where a size cross-check would be specified
