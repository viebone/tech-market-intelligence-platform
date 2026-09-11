source: market-signal
date: 2026-09-11

New research on external data sources for employment/layoff events, to potentially extend
beyond job postings into a company-level "employment_event" signal (layoffs, closures,
restructuring, bankruptcy, offshoring, expansion/hiring announcements). Candidate sources
identified:

1. **Eurofound European Restructuring Monitor (ERM)** — EU + Norway, company-level, 33,000+
   events, covers both job losses AND job creation, free CSV data access request available.
   Fields: company, country, date, sector, restructuring type, employment_change. For the
   latest 100-day period it reports ~47,582 announced job creations and ~60,880 job losses.
   Recommended as the #1 European source.

2. **US WARN Act notices** — company/facility-level, legally mandated, state-published (no
   unified federal API; would need per-state normalization or a secondary aggregator like the
   "Free WARN Layoff API," which currently only covers 5 states — ~7,470 notices, 5,842
   employers, 966,588 affected employees — not a complete US dataset on its own).

3. **UK ONS HR1 (Advanced Notification of Potential Redundancies)** — macro/aggregate only (no
   company names), weekly/monthly, published by ONS. Good as a UK risk index input
   (potential redundancies, number of employers, region, industry), not a company-level
   dataset.

4. **UK Companies House Public Data API — insolvency endpoint** — company-level risk
   enrichment (`GET /company/{company_number}/insolvency`, requires API key). Lets the system
   distinguish insolvency from restructuring/layoffs/closure.

Explicitly deprioritized: **Layoffs.fyi** — treat as secondary enrichment/validation only, not
the backbone, given weaker programmatic suitability than the official/quasi-official sources
above.

Suggested ingestion priority: Eurofound ERM → US state WARN → UK ONS HR1 (macro index) → UK
Companies House (risk enrichment).

## Proposed direction (not yet decided — for PM triage)

A new `employment_event` entity:

```
company_id
event_date
country
region
event_type   [LAYOFF | CLOSURE | RESTRUCTURING | BANKRUPTCY | OFFSHORING | EXPANSION | HIRING_ANNOUNCEMENT]
jobs_affected
direction
source
source_url
source_type
confidence
```

Combined with TMIP's existing job-posting time series per company, this could derive
deterioration/expansion signals — e.g. a declining open-jobs trend plus a restructuring
announcement reads as a risk signal; a rising open-jobs trend plus a hiring announcement reads
as an expansion signal. This connects to TMIP's existing candidate-risk-assessment framing:
job search isn't only about finding listings, it's about assessing the risk and quality of an
opportunity.

Note: none of the four sources above have yet been confirmed as automatable (no manual access
request) vs. requiring a registration/API-key step — that verification is a natural follow-up
once this is scoped as an outcome.

## Resolved during backend spec (2026-09-11 — `changes/2026-09-11-employment-event-ingestion.md` Step 5)

- **UK ONS HR1 — descoped, not built.** Confirmed during backend spec'ing: HR1's macro/
  aggregate-only shape (no company names) genuinely cannot produce a company-level
  `EmploymentEvent` row, and `design/market-health/experience.md`'s Layoff Signal behavior was
  scoped entirely around company/sector events — nothing asked for a UK macro risk index. Full
  reasoning in `backend/specs/market-health/api.md` — Business Logic — "UK ONS HR1
  (descoped)". Revisit only if a future outcome specifically wants a UK macro market-health
  index, with its own experience spec first.
- **Automation status per source, as spec'd** (this remains to be *empirically* confirmed at
  `/implement-backend` time, not assumed from the spec):
  - Eurofound ERM — **unconfirmed**. Whether the "Request data access (.csv)" option is a
    public bulk download or a gated manual-approval request is still open; first task for
    that adapter.
  - US state WARN — **partially confirmed**: the mechanism (per-state fetch/parse, no unified
    API) is settled, but the exact state list and each state's URL/format is not — a curated,
    verified-before-added subset, same discipline as the platform's 35 tracked companies.
  - UK Companies House insolvency — **confirmed automatable**: a keyed public REST API
    (`GET /company/{company_number}/insolvency`), free registration.

## Expanded source catalog (2026-09-11, later same day — live web research, not assumed)

User direction: layoff/employment-event data should be a **generic, independent dataset** —
not scoped to the 35 companies tracked for job postings — feeding broader market-intelligence
insight (strategy, market understanding), not just a per-company overlay. Build a fuller
source list, prioritise by: automatable by code > global coverage preferred > free/open >
correctly contextualised. Every source below was checked live (WebSearch + WebFetch), not
assumed from prior knowledge — several findings revise the original evaluation.

| Source | Geography | Level | Free? | Auth | Automation | Notes |
|---|---|---|---|---|---|---|
| **WARN Firehose** (warnfirehose.com) | **All 50 US states**, one integration | Company | ✅ Free tier: 25 calls/day, no credit card, email verification | API key (free signup) | ✅ **Fully automatable today** | **New finding, best near-term ROI.** 90,868+ WARN notices across all 50 states in ONE API — replaces the per-state scraping this spec originally scoped. Also bundles **SEC filings** (101K+), **bankruptcies** (5K+), H-1B petitions, DOL claims, JOLTS in the same platform — SEC + bankruptcy data map directly onto our `event_type` set (restructuring/bankruptcy signals), potentially without building a separate SEC adapter. |
| **layoffdata.com — WARN Database** | All 50 US states | Company | ❌ **No free tier** — subscription required (confirmed via their own API docs) | Bearer token, paid | Automatable, but not free | Ruled out on the "free/open" criterion — otherwise excellent (13 fields/record, bulk CSV, 300 req/min). Revisit only if budget for a paid source is ever approved. |
| **Eurofound ERM** | EU + 27 states + Norway | Company | ✅ Free, public — confirmed a real "Export data" feature on the live search app (33,500+ events), not gated | None found, but exact endpoint not yet captured (JS-triggered export) | ⚠️ Needs one manual step: capture the real request URL from a browser's Network tab when "Export data" is clicked | Unchanged priority — still the strongest single EU source (company-level, both directions, sector-tagged), just needs that one URL to finish. |
| **SEC EDGAR full-text search** | US-listed companies (incl. many non-US companies via US listings) | Company, official filing | ✅ Free, public, no key (SEC's own API) | None | ✅ Automatable | **Built 2026-09-11** (`employment_events/sec_edgar.py`) — filtered to Item 2.05 filings, not general full-text matching (more precise than WARN Firehose's bundled SEC dataset, which this adapter turned out not to be redundant with in practice: WARN Firehose's own SEC coverage wasn't exercised/compared directly, but building the dedicated Item-2.05-filtered adapter gave real company names + a distinct "official company disclosure" tier WARN's state-filing tier doesn't have). Live, 9 real filings on first run. |
| **layoffs.fyi** | Global tech (2,900+ companies since 2020) | Company | ✅ Free for editorial/research/educational use, attribution requested | No documented public API found | ⚠️ Unconfirmed — likely has an unofficial JSON endpoint powering the live site (same "check the browser's Network tab" caveat as Eurofound); not yet captured | Best **global tech-specific** candidate by far if a usable endpoint exists. Originally deprioritized to "secondary enrichment only" in this file's first pass — worth reconsidering now given the "global preferred" priority, but still needs the same manual verification step as Eurofound before committing to it as a real adapter. |
| UK Companies House — insolvency | UK | Company | ✅ Free, keyed | API key | ✅ Automatable (already built) | Unchanged from above — only `CANDIDATE_COMPANIES` is unpopulated, and that's now moot if scope decouples from the 35 tracked companies (see note below). |
| ~~UK ONS HR1~~ | UK | Macro-only | — | — | — | Still descoped — no company names, doesn't fit `EmploymentEvent`. Unchanged. |

**Not yet researched** (flagged for a future pass, not fabricated): dedicated sources for
Asia-Pacific, Canada, Australia, or a single truly global feed. None turned up in this pass;
worth a dedicated search round if broader-than-EU/US/UK coverage becomes a priority.

**Architecture implication flagged, not yet decided**: the user's "generic, not connected to
companies" direction is a real change to a decision already recorded in three specs
(`design/market-health/experience.md`'s chart-strip scoping rationale,
`backend/specs/market-health/api.md`'s `GET /api/market-health/employment-events` endpoint,
which filters to `matched_company IS NOT NULL` by design). Per this project's own change
discipline, that revision needs its own `/change-request` pass before the specs or code
change — not a silent pivot mid-implementation.
