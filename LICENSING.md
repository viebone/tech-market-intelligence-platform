# Data Source Licensing — What We're Allowed to Do With Each Source

**What this is:** the single place to check, per external data source, what licence or reuse
right this platform actually has — confirmed or not, commercial-use-permitted or not, and what
to do (or not do) with data from a given source. Companion to `DATA_SOURCES.md` (which covers
*mechanism* — how each source is fetched) and `ACCESS.md` (which covers *reachability* — what's
exposed from where). This file covers *rights* — what we're legally/contractually allowed to do
with the data once we have it.

**Why it exists:** this product pulls from sources with real, different, sometimes-restrictive
terms — a scraped site with an explicit permission grant, government registries under public
licences, a commercial API with its own Terms of Service. Nothing here is guessed: every row
below is either read directly off the source's own licence/terms page, or explicitly marked as
not yet confirmed. Kept current whenever a source is added or its terms are checked/re-checked.

Last reviewed: 2026-09-24 (trusted external statistics — ONS — added below).

---

## 1. Per-source licence status

**All eight real sources below are registered in code** (`backend/src/source_licences.py`'s
`SOURCE_LICENCES`), not just documented here — enforced by
`backend/tests/test_source_licences.py`, which fails the build the moment any adapter anywhere
in this codebase (job postings, employment events, or scraped) has no matching entry, or an
entry has no source, no `data_summary`, or no attribution text. This is what makes "every bit of
data can be tracked against a licence" real rather than a hope someone remembers to keep true.

Each source gets a computed, single **Status** (`overall_status()`): **Pending** (not yet
confirmed — we genuinely don't know), **Licensed** (not rejected, and confirmed), or **Rejected**
(a human has explicitly set `rejected=True` for this source — see §2). See it live in the admin
dashboard's **Sources & Licensing** view (§4), which also shows the **What we take** column
below for every source. As of 2026-09-16, no source has `rejected=True` — nothing is restricted
anywhere, matching the real registry, not assumed.

| Source | Access | What we take | Licence | Confirmed? | Status today | Commercial use |
|---|---|---|---|---|---|---|
| **IT Jobs Watch** | Scraped (`scraping/itjobswatch.py`) | Aggregate market stats only (rank, vacancy share, salary percentiles, skill associations) — no individual postings, no PII | **CC BY-NC-SA 4.0** | ✅ Yes — read directly off itjobswatch.co.uk's own `/copyright.aspx` page, 2026-09-16 | **Licensed** | ❌ **No** — the "NC" clause |
| **SEC EDGAR** (8-K Item 2.05) | API (`employment_events/sec_edgar.py`) | Filing metadata only (company, date, CIK, accession number, state) — never the filing's full text | Public domain / no copyright restriction | ✅ Yes — sec.gov's own reuse statement, 2026-09-16 | **Licensed** | ✅ Yes |
| **UK Companies House** | Streaming API (`employment_events/companies_house.py`) | Company number (no name), case dates, insolvency type | Open Government Licence v3.0 | ✅ Yes — Companies House developer docs / gov.uk, 2026-09-16 | **Licensed** | ✅ Yes |
| **Eurofound ERM** | Keyless CSV export (`employment_events/eurofound_erm.py`) | Company name, event date, restructuring type, sector, country, jobs affected — full CSV row kept verbatim | The EU's own bespoke reuse policy (attribution required, no distortion) — not literally Creative Commons, similar in spirit | 🟡 Medium confidence — general EU reuse framework confirmed, but Eurofound's own copyright page rate-limited on direct fetch, 2026-09-16, so the registry honestly records this as **not** confirmed | **Pending** | Believed yes, not formally confirmed |
| **US WARN notices** (via WARN Firehose) | API (`employment_events/us_warn.py`) | Company name, industry/sector, jobs affected, event date, US state, source URL | Underlying government WARN data: public record, no copyright. **WARN Firehose's own Terms of Service separately restrict redistribution/resale of raw API access, bulk downloads, or data exports** | 🟡 The government-data layer is confirmed; WARN Firehose's own ToS as applied to *this account's actual use* is **not resolved** | **Pending** | Believed yes for the government data itself — the redistribution question is separate, see §3 |
| **Greenhouse** | Public, unauthenticated API (`sources/greenhouse.py`) | Full raw job-posting response kept verbatim (title, description HTML, location, department); parsed country/city/salary where present | No formal data-reuse licence published — docs describe the intended use as the hiring company building its own careers page; third-party read access neither addressed nor prohibited | ✅ Yes — read directly off `docs.greenhouse.io`, 2026-09-16 (confirms the *documentation was checked*, not that a formal licence exists — none does) | **Licensed** | ✅ Yes — nothing found restricting it |
| **Lever** | Public, unauthenticated API (`sources/lever.py`) | Full raw job-posting response kept verbatim; parsed country/city/salary where present | No formal data-reuse licence published — but Lever's own docs explicitly state: *"all job postings in the published state are publicly viewable. These jobs may be scraped by third parties."* | ✅ Yes — read directly off Lever's own `postings-api` docs, 2026-09-16 | **Licensed** | ✅ Yes |
| **Ashby** | Public, unauthenticated API (`sources/ashby.py`) | Full raw job-posting response kept verbatim (compensation data often present); parsed country/city/salary where present | No formal data-reuse licence published — docs describe the intended use as the hiring company building its own careers page; third-party read access neither addressed nor prohibited | ✅ Yes — read directly off `developers.ashbyhq.com`, 2026-09-16 | **Licensed** | ✅ Yes — nothing found restricting it |

### Trusted external statistics — now registered in `source_licences.py` (2026-09-25)

Kept as its own table because it is the first source of the trusted-statistics category. **It is registered in code as of
2026-09-25** (`SOURCE_LICENCES["ons_vacancy_survey"]`, added in the same change as its adapter, so `test_source_licences.py` —
which fails the build on a licence with no adapter — passes; that test now counts trusted-statistics adapters as a fourth category).
The table at the top of this section therefore has **nine** registered sources, not eight; this row is the ninth.

| Source | Access | What we take | Licence | Confirmed? | Status when registered | Commercial use |
|---|---|---|---|---|---|---|
| **ONS Vacancy Survey** (`ons_vacancy_survey`) — trusted external statistics | Page-data JSON + published XLSX (`trusted_stats/ons_vacancy.py`, 📋 not built) | Aggregate UK vacancy estimates by industry (SIC 2007) and by size of business — levels in thousands, 3-month rolling averages. No individual postings, no personal data | **Open Government Licence v3.0** | ✅ Yes — ONS dataset page ("All content is available under the Open Government Licence v3.0, except where otherwise stated"), ONS terms and conditions, and the licence text at nationalarchives.gov.uk, all read 2026-09-24 | **Licensed** (`overall_status()` = `licensed`, verified 2026-09-25) | ✅ **Yes** — the OGL expressly permits commercial and non-commercial use |

**Attribution to display wherever an ONS figure is shown** (always naming the source):
> Source: Office for National Statistics — Vacancy Survey. Contains public sector information licensed under the Open Government Licence v3.0.

The OGL requires acknowledging the source "by including or linking to any attribution statement
specified by the Information Provider(s)"; ONS's dataset page specifies none beyond the licence
notice, so the OGL's own default wording plus the named source is used. If ONS publishes a
preferred wording, update the registry entry.

Evidence, with exact quotes: `research/2026-09-24-ons-licence-and-access-confirmation.md`.

Full technical detail (adapters, fields, access mechanism) for each of these lives in
`DATA_SOURCES.md`. Full research trail:
- `research/2026-09-16-itjobswatch-scraping-permission.md` — the original permission grant
- `research/2026-09-16-existing-source-licensing-audit.md` — the audit behind the four
  employment-event rows above
- `research/2026-09-16-commercial-mode-kill-switch.md` — why §2 below exists
- `research/2026-09-16-all-sources-licensing-status.md` — the status-model refinement
- `research/2026-09-24-ons-licence-and-access-confirmation.md` — ONS / OGL v3.0, exact quotes,
  and what the real files contain
- `research/2026-09-16-job-posting-source-licensing.md` — Greenhouse/Lever/Ashby's own docs,
  checked directly, and the verbatim-content nuance in §3 below

---

## 2. The per-source switch — what it does and doesn't do

Revised 2026-09-16 per explicit direction: *"we can switch on/off by sources. Just make sure
that ingestions always work and that insights and other functionality always work unless we say
license rejected. but in any case the ingestions can work until we say the opposite."*

**Two independent lifecycles, never conflated:**

1. **Ingestion (collecting data)** — always runs, for every registered adapter, full stop.
   Nothing in this file, no env var, no status, ever stops a source from being fetched. The data
   has value on its own — internal analysis, a future re-negotiated licence — independent of
   whether it can currently be *used*.
2. **Use (a future chart, chat answer, MCP tool — anything that shows or acts on the data)** —
   gated by exactly one thing: `SourceLicence.rejected`, a plain boolean in
   `backend/src/source_licences.py`. Defaults to `False` — **every source is usable by default.**
   The only way a source stops being usable is a human explicitly setting `rejected=True` in
   that file: a deliberate, git-tracked, reviewable decision — never an automatic inference from
   `confirmed`, `permits_commercial_use`, or whether the product happens to be monetized.

**`TMIP_COMMERCIAL_MODE` is informational only now** — a reminder, surfaced in the admin view,
that "this product is monetized, go review sources and decide" — it does **not** automatically
flip anything. `confirmed` and `permits_commercial_use` stay in the registry as context a human
reads *before* deciding whether to set `rejected`; they no longer compute a block themselves.

**Today**: no source has `rejected=True` — nothing is restricted anywhere, by design, until a
human makes that call for a specific source.

---

## 3. Real, open flags — read before relying on any of this for something real

- **IT Jobs Watch's NonCommercial clause vs. this product's Premium paid tier.** Nothing
  violates this today (this data isn't surfaced anywhere yet, Free tier or Premium). But before
  it's ever exposed through anything monetized, this needs its own explicit resolution — keep it
  Free-tier-only, or confirm with IT Jobs Watch that this product's specific use qualifies as
  non-commercial. Not urgent; not to be forgotten either.
- **WARN Firehose's contractual redistribution restriction.** This is not a "read the public
  page" problem — it's a "does our actual use comply with what we agreed to" problem, and it
  needs the operator's own review of the account's actual accepted Terms of Service (which may
  differ from what a logged-out visitor sees), or a direct question to WARN Firehose the same
  way IT Jobs Watch was asked. **Not disabled pending that** — flagged, per this whole
  document's own "always flag, never silently block" discipline — but genuinely open.
- **Greenhouse/Lever/Ashby: job posting text is the hiring company's own copyrighted content,
  not licensed content in any formal sense.** No formal reuse licence exists for any of the
  three (Lever's docs come closest, explicitly acknowledging third-party scraping). This
  product stores the full raw job-posting response verbatim (`raw_postings.raw_response`,
  including full description text) — used internally for classification and trend analysis,
  never republished to end users as a full posting. That's the same "factual/transformative
  use" posture job aggregators generally rely on. Flagged so it's a deliberate, known posture —
  **if any future feature ever displays a raw job description verbatim to an end user** (as
  opposed to aggregate trends derived from it), that changes the analysis and deserves a fresh
  look before shipping, not an assumption that today's reasoning still covers it.
- **ONS / Open Government Licence v3.0 — what it does *not* cover.** The OGL excludes personal
  data, departmental/public-sector **logos, crests and the Royal Arms**, third-party rights the
  provider isn't authorised to license, and other IP (trade marks, designs). Numeric statistics
  are covered; **the ONS logo is not — never put it in the product** (including in a chart or
  a "sources" strip). The attribution line is a *condition*, not a courtesy: it must appear
  wherever the data is shown (Story 5 renders it beside the framing line, not only in the
  Reasoning Panel). No ONS API or rate-limit policy is published — the platform's own politeness
  rules (`DATA_SOURCES.md` §3c) apply regardless.
- **Eurofound ERM's exact reuse policy wording** — confirmed to a medium confidence level only
  (see §1); worth a direct re-check of eurofound.europa.eu's own copyright page if this data is
  ever used somewhere the exact wording would matter.

---

## 4. Where this is enforced, and where it's only specified so far

| Layer | Status |
|---|---|
| Ingestion (`ingest_scraped_sources.py`) | ✅ Live — logs (non-blocking) when a collected source isn't commercially cleared; never skips collection |
| Storage (`market_observations` / `skill_associations`) | ✅ Live — every row carries `licence`, `licence_confirmed`; an unconfirmed source's ingestion also logs a `WARNING` |
| Full-coverage traceability (every real adapter has a registered licence) | ✅ Live, enforced by a test — `backend/tests/test_source_licences.py` fails if any adapter (job postings, employment events, or scraped) has no `source_licences.py` entry, or vice versa (a stale entry with no matching adapter) |
| Any future query/display function reading `market_observations`/`skill_associations` | 📋 **Specified, not built** — must call `is_source_usable()` per source and exclude accordingly. Nothing reads this data anywhere in the product yet. |
| `raw_postings` / `employment_events` — no per-row licence field yet | 📋 **Traceable via `source` + the registry, not a stored snapshot.** Unlike the newer scraped tables, these two don't carry their own `licence`/`licence_confirmed` columns — full traceability today means looking up `get_licence(row.source)`, not reading it off the row directly. Adding that snapshot would be its own small schema change if ever needed; not built speculatively here. |
| Trusted-statistics licence stamping (`licence`, `licence_confirmed`, `attribution_text` on every series and observation) and the unconfirmed-licence ingestion `WARNING` | ✅ **Live** (2026-09-25) — stamped on every stored row (verified: 0 rows without a licence); the warning path is in `trusted_stats.base.ingest_adapter` |
| Any read of trusted statistics must call `is_source_usable()` and return a fully-populated `source` object | ✅ **Live and enforced** — `market_query.query_trusted_statistics_data` gates per source and `named_source()` refuses a statistic with an empty publisher/dataset/URL/licence/attribution; tests in `backend/tests/test_trusted_stats.py`; the chat trace and MCP envelope carry the licence and flag an unconfirmed one |
| Operator visibility (admin dashboard, **Sources & Licensing**, `/admin/licensing`) | ✅ **Live** (2026-09-16) — all 8 registered sources, what data is taken from each, Pending/Licensed/Rejected status, commercial-use permission, and attribution text, in one view |

---

## 5. Related

- `DATA_SOURCES.md` — every source's access mechanism, adapters, and control levers
- `ACCESS.md` — what's reachable from the frontend, backend API, and MCP, capability by capability
- `backend/specs/scraped-data-sources/api.md` — the full technical spec (Data Models,
  Business Logic, Tech Decisions) behind everything in §2 above
- `backend/src/source_licences.py` — the actual code: `SOURCE_LICENCES`, `get_licence()`,
  `is_commercial_mode()`, `is_source_usable()`
- `changes/2026-09-16-polite-scraping-adapters.md` — the full change history and decision log
  behind this entire file
