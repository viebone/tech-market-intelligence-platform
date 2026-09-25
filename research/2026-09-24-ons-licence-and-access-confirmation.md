source: internal
date: 2026-09-24

# ONS Vacancy Survey — licence confirmation and real-file findings

Evidence record for the first trusted-statistics source (`changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md`).
Everything below was read directly from the named page or file on 2026-09-24, not recalled.

## 1. Licence — CONFIRMED: Open Government Licence v3.0

| Evidence | Where read | What it says |
|---|---|---|
| ONS dataset page for VACS03 | https://www.ons.gov.uk/employmentandlabourmarket/peoplenotinwork/unemployment/datasets/vacanciesbysizeofbusinessvacs03 | "All content is available under the Open Government Licence v3.0, except where otherwise stated". Dataset carries the UK Statistics Authority Official Statistics kitemark |
| ONS terms and conditions | https://www.ons.gov.uk/help/termsandconditions | "Most content on this website is subject to Crown copyright protection and is published under the Open Government Licence (OGL)." Exceptions: photographs, illustrations and videos with third-party copyright. Says nothing about API/automated access or rate limits |
| The licence text itself | https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/ | Permits commercial and non-commercial use ("exploit the Information commercially and non-commercially, for example, by combining it with other Information, or by including it in your own product or application"). Condition: "acknowledge the source of the Information in your product or application by including or linking to any attribution statement specified by the Information Provider(s)"; default wording: **"Contains public sector information licensed under the Open Government Licence v3.0."** |

**Exclusions that matter to us** (OGL v3.0): personal data in the Information; departmental
logos, crests and the Royal Arms (so **never use the ONS logo** in the product); third-party
rights the provider isn't authorised to license; other IP (trade marks, patents, designs).
We take numeric statistics only — none of these is engaged, but the logo rule is a real
constraint on any future surface.

**Commercial use: permitted.** Unlike IT Jobs Watch (CC BY-NC-SA), no conflict with the
Premium tier.

**Attribution text to use wherever an ONS figure is shown** (publisher-specified attribution
was not found on the dataset page, so the OGL default plus a named source is used — always
naming the source, per the PM's direction):

> Source: Office for National Statistics — Vacancy Survey. Contains public sector information licensed under the Open Government Licence v3.0.

Not covered by this record: ONS API/rate-limit policy (none stated — see §3 for the enforced
politeness we apply anyway). Contact on the dataset page: labour.market@ons.gov.uk /
vacancy.survey@ons.gov.uk (file footer).

## 2. What the real files contain (downloaded once each, 2026-09-24)

Five direct requests to ons.gov.uk in total, identified with a descriptive User-Agent and
contact: `vacs03sep2026.xlsx` (54 KB), `vacs02sep2026.xlsx` (199 KB) 3 s later, one page-data JSON
after a further 3 s pause, and `robots.txt` twice back-to-back (the first attempt's output was
cut off by the shell, so it was re-fetched — the one place the 3 s pacing was not kept). Two
further reads of ONS pages (dataset page, terms page) went through the search tooling, not
direct requests. Files were kept only in the session scratchpad, not in the repo.

### Release discovery — the page-data JSON
`<dataset page URL>/current/data` returns JSON (HTTP 200, `application/json`):
- `downloads[0].file` → current file name (`vacs03sep2026.xlsx`); the file is at
  `<dataset page URL>/current/<file>`.
- `versions[]` → **every past release**, 129 for VACS03, each with `uri` (`…/current/previous/v128`)
  and `updateDate` (latest `2026-09-15T06:00:00Z`, previous `2026-08-18`, `2026-07-21`). So
  the latest release date is `versions[-1].updateDate`, and any past vintage is addressable.
- **`description.releaseDate` is `2016-08-16` — stale, the dataset's first release. Never use it.**
- No HTML parsing is needed to find the file or the release date. The ONS robots.txt path
  returned an HTML "Page not found" (no robots.txt published); the adapter still checks it and
  treats a 404 as "no restrictions", per RFC 9309.

### VACS03 — Vacancies by size of business
- One sheet, `VACS03`. Row 6 labels, **row 7 ONS series IDs** (`AP2Y` = all vacancies; `ALY5`…`ALY9`
  = the five size classes), row 8 "Levels (thousands)", data from row 10.
- Size classes (employees): **1–9, 10–49, 50–249, 250–2,499, 2,500+**.
- Period label is a 3-month **rolling** average: "Jun-Aug 2026" (302 periods, Apr-Jun 2001 →
  Jun-Aug 2026, overlapping windows). Values in **thousands**.
- Column B carries a status flag — **`(p)` = provisional** on the latest period. Revisions are
  therefore real and must be stored as vintages.
- Latest row (Jun-Aug 2026): all vacancies 702k (−8k, −1.1% on quarter); 1–9: 91k, 10–49: 99k,
  50–249: 103k, 250–2,499: 169k, 2,500+: 240k.
- Quirks found: stray space in a label ("Nov- Jan 2002"); summary rows ("Change on quarter",
  "Change on year") below the series; footnote rows; many empty rows to row 723 → the parser
  must key on the period-label pattern, not row numbers.
- Footnote (scope of the survey): covers all sectors **except** agriculture, forestry and
  fishing (SIC 2007 section A), activities of households as employers (section T), and
  employment agencies (division 78). "Change" columns compare with the previous
  **non-overlapping** three-month period.

### VACS02 — Vacancies by industry
- Two sheets: **`levels`** (thousands) and **`job openings rate`** (vacancies per 100 jobs).
- Row 4 labels, **row 5 SIC 2007 codes** (`B-S` total, sections `B`…`S`, aggregate `G-S`,
  divisions `45`, `46`, `47`), **row 6 ONS series IDs** (`AP2Y`, `JP9H`…). Sheet titles read
  "United Kingdom (thousands), seasonally adjusted" (`levels`) and "United Kingdom (job openings rate),
  seasonally adjusted". **But footnotes 2 and 3 state that some series are *not* seasonally adjusted**
  because they show no seasonality ("Therefore the unadjusted series is the best estimate of a
  'seasonally adjusted' series") — which series carry those footnote markers is in the header cells
  and must be read from the file, not assumed. **VACS03 contains no seasonal-adjustment wording at
  all** (searched the whole workbook, 2026-09-24) — so it is recorded as `unknown`, never assumed to
  match VACS02 (ONS's web page describes the VACS01–03 three-month averages as accredited official
  statistics, but not the adjustment status of the file).
- Label quirks: hyphenation artefacts in header text ("Manu-    facturing", "Construc-tion").
  So the **SIC code row is authoritative; labels come from our own canonical SIC 2007
  section-name table**, not from the header cells.

### Not yet inspected
- **X06** (single-month, industry × size, not seasonally adjusted, not National Statistics) —
  file location not confirmed. First slice covers VACS02 + VACS03 only; X06 is added only if
  its file layout is inspected first.
- The `job openings rate` sheet's full column set.

## 3. Politeness applied to a source with no published policy
Even though this is a file download from a public statistics publisher, not scraping, the same
discipline applies (Rule 13's spirit): a descriptive User-Agent with a contact address; the
release-discovery JSON checked at most once per day; a file downloaded **only when a new
release exists** (`versions[-1].updateDate` newer than the last stored) or its content hash
changed; pacing ≥3 s between any two requests to the host. Monthly release cadence means ~3
requests/month in steady state.

## 4. Update 2026-09-25 — from ONS's own methodology page (Vacancy Survey QMI)
Read 2026-09-25 (`research/2026-09-25-business-size-band-standards.md` has the full record). Three
points change what §2 above says or implies:
- **Geography:** the survey covers **Great Britain**; ONS weights it up to the **UK** (Northern
  Ireland ≈3% of UK employment). The published "United Kingdom" figures are derived from a GB survey.
- **Smallest size band:** the file says "1 - 9"; the methodology says "2 to 9" — businesses with one
  person on the register are modelled, not surveyed.
- **Seasonal adjustment of the by-size series:** the *file* is silent (§2), but the methodology page
  states "The three-month moving average series by industry and by size of business is seasonally
  adjusted directly". So VACS03 should be recorded as seasonally adjusted, with the methodology page
  named as the source — superseding the "store `unknown`" note in §2.
