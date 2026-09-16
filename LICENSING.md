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

Last reviewed: 2026-09-16.

---

## 1. Per-source licence status

| Source | Access | Licence | Confirmed? | Commercial use permitted? | Attribution required |
|---|---|---|---|---|---|
| **IT Jobs Watch** | Scraped (`scraping/itjobswatch.py`) | **CC BY-NC-SA 4.0** | ✅ Yes — read directly off itjobswatch.co.uk's own `/copyright.aspx` page, 2026-09-16 | ❌ **No** — the "NC" (NonCommercial) clause | ✅ Yes — "Source: IT Jobs Watch" |
| **SEC EDGAR** (8-K Item 2.05) | API (`employment_events/sec_edgar.py`) | Public domain / no copyright restriction | ✅ Yes — sec.gov's own reuse statement, 2026-09-16 | ✅ Yes | Not required, but this product cites its source anyway (provenance discipline) |
| **UK Companies House** | Streaming API (`employment_events/companies_house.py`) | Open Government Licence v3.0 | ✅ Yes — Companies House developer docs / gov.uk, 2026-09-16 | ✅ Yes | ✅ Yes — attribute Companies House / Crown copyright |
| **Eurofound ERM** | Keyless CSV export (`employment_events/eurofound_erm.py`) | The EU's own bespoke reuse policy (attribution required, no distortion) — not literally Creative Commons, similar in spirit | 🟡 Medium — general EU reuse framework confirmed; Eurofound's own copyright page rate-limited on direct fetch, 2026-09-16 (worth a direct re-check if this ever becomes higher-stakes) | ✅ Yes | ✅ Yes |
| **US WARN notices** (via WARN Firehose) | API (`employment_events/us_warn.py`) | Underlying government WARN data: public record, no copyright. **WARN Firehose's own Terms of Service separately restrict redistribution/resale of raw API access, bulk downloads, or data exports** without a commercial licence agreement | 🟡 Partial — the government-data layer is confirmed; WARN Firehose's own ToS as applied to *this account's actual use* is **not resolved** | ⚠️ **Unresolved** — see §3 | Attribution to WARN Firehose required if presenting derived data as original research |
| Greenhouse / Lever / Ashby (job postings) | Public APIs (`sources/*.py`) | Not a content-licensing question — these are structured job-posting feeds under each ATS's own API Terms of Service, not published/licensed editorial content | N/A | N/A (this product's own job postings, not republished third-party content) | N/A |

Full technical detail (adapters, fields, access mechanism) for each of these lives in
`DATA_SOURCES.md`. Full research trail:
- `research/2026-09-16-itjobswatch-scraping-permission.md` — the original permission grant
- `research/2026-09-16-existing-source-licensing-audit.md` — the audit behind the four
  employment-event rows above
- `research/2026-09-16-commercial-mode-kill-switch.md` — why §2 below exists

---

## 2. The commercial-use gate — what it does and doesn't do

**`TMIP_COMMERCIAL_MODE`** (env var, default `false`) is the one switch for "this product now
makes money, stop using anything we don't have commercial rights to." Two things to understand
about it, both deliberate:

**It gates *use*, never *collection*.** Flipping it to `true` does not stop any adapter from
running — every registered scraped source keeps being ingested regardless, because the data has
value independent of whether it's currently usable commercially (a licence can be
re-negotiated; internal analysis isn't "use" in the sense a licence restricts). What changes is
that `scraping.licences.is_source_usable(source)` starts returning `False` for a
non-commercially-licensed source — and **every future function that reads this data back out to
actually show or act on it (a chart, a chat answer, an MCP tool) is required to call that
function and exclude what it returns `False` for.** Nothing reads this data anywhere yet, so
today this is a forward-binding contract, not a live filter — see
`backend/specs/scraped-data-sources/api.md`'s Business Logic and Tech Decisions sections for the
full spec.

**It's conservative about "don't know."** A source whose licence isn't yet `confirmed` is
treated exactly like "not commercially usable," even if it might turn out to permit commercial
use once confirmed. Being unsure is not the same as being allowed.

**Today, with the switch off (the current, correct state)**: nothing is restricted anywhere.
This section exists so the mechanism is ready and understood *before* the day it's actually
needed, not designed from scratch under time pressure once a monetization decision is already
made.

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
- **Eurofound ERM's exact reuse policy wording** — confirmed to a medium confidence level only
  (see §1); worth a direct re-check of eurofound.europa.eu's own copyright page if this data is
  ever used somewhere the exact wording would matter.

---

## 4. Where this is enforced, and where it's only specified so far

| Layer | Status |
|---|---|
| Ingestion (`ingest_scraped_sources.py`) | ✅ Live — logs (non-blocking) when a collected source isn't commercially cleared; never skips collection |
| Storage (`market_observations` / `skill_associations`) | ✅ Live — every row carries `licence`, `licence_confirmed`; an unconfirmed source's ingestion also logs a `WARNING` |
| Any future query/display function | 📋 **Specified, not built** — must call `is_source_usable()` per source and exclude accordingly. Nothing reads this data anywhere in the product yet. |
| Operator visibility (an admin view listing every source's licence/commercial-use status) | 📋 **Requested, not yet speced** — see the change request this prompted |

---

## 5. Related

- `DATA_SOURCES.md` — every source's access mechanism, adapters, and control levers
- `ACCESS.md` — what's reachable from the frontend, backend API, and MCP, capability by capability
- `backend/specs/scraped-data-sources/api.md` — the full technical spec (Data Models,
  Business Logic, Tech Decisions) behind everything in §2 above
- `backend/src/scraping/licences.py` — the actual code: `SOURCE_LICENCES`, `get_licence()`,
  `is_commercial_mode()`, `is_source_usable()`
- `changes/2026-09-16-polite-scraping-adapters.md` — the full change history and decision log
  behind this entire file
