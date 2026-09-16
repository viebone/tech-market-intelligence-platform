---
id: polite-scraping-adapters
date: 2026-09-16
trigger-type: stakeholder-request
change-type: new-feature
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Polite, generalizable scraping adapters (starting with IT Jobs Watch)

## Signal
See: `research/2026-09-16-itjobswatch-scraping-permission.md`

IT Jobs Watch declined API/paid access for this personal project but explicitly granted
permission to scrape their site (CC-licensed content), on conditions: respect `robots.txt`, low
request rate with pauses, identify with a clear User-Agent + contact address, cache rather than
re-fetch unchanged pages, and attribute anywhere republished.

## Outcome
See: `outcomes/job-data-source-flexibility.md` — amended today (this change) to name scraping as
a legitimate adapter mechanism alongside API-calling, with its own class of rules.

## Change Type
`new-feature` — no scraping mechanism exists in this codebase yet (today's only fetch machinery,
`PacedFetcher`, is API-shaped: JSON endpoints, no `robots.txt`, no HTML, no page cache, no
attribution tracking). This also has a `technical-refactor` flavor baked into it: the ask is
explicitly for a *generalizable* mechanism, not a one-off IT Jobs Watch script — "I would like to
build in a way that same process could be applied to other sources, those that cannot be
accessed by API."

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | update (done today — scraping named as a legitimate mechanism) |
| Design Foundations | `design/foundations.md` | no-change — no UX principle is implicated; nothing user-facing is being decided by this change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | — | no-change — see "Deliberately out of scope," below |
| Backend Spec | `backend/specs/scraped-data-sources/api.md` | create |
| Frontend Spec | — | no-change |
| Frontend Implementation | `frontend/src/` | no-change |
| Backend Implementation | `backend/src/` | update |
| Plain-Language Overview | `OVERVIEW.md` | no-change for now — this ships data acquisition with nothing new for a user to see or do yet. Revisit (mark update) the moment IT Jobs Watch data is actually surfaced anywhere a user can reach it. |
| Data Sources Index | `DATA_SOURCES.md` | update (manual edit, this doc's own convention — register the new mechanism + IT Jobs Watch as a source + new control-lever entries) |

## Deliberately out of scope for this change

- **Where/whether IT Jobs Watch's data ever surfaces to a user** — as a comparison in a data
  story, a chat tool, or an MCP tool. The operator's ask so far is "get the data in, politely" —
  not "show it." Surfacing is a real decision (what does "our number vs. their number" even mean
  to a job-seeker?) that deserves its own outcome/experience pass once real data exists to look
  at, not a guess bolted onto the ingestion work. Flagged here so it isn't forgotten, the same
  way employment events' company-matching question got its own explicit later decision rather
  than being assumed at ingestion time.
- Building every future scraped source (company career pages, etc.) — this change builds the
  *mechanism* and its first real user (IT Jobs Watch); each additional scraped source is a
  one-adapter addition afterward, same as any ATS adapter today.

## Execution Plan

- [x] Step 1: Signal captured — `research/2026-09-16-itjobswatch-scraping-permission.md`
- [x] Step 2: Outcome amended — `outcomes/job-data-source-flexibility.md`
- [x] Step 3: `/new-backend-spec` — `backend/specs/scraped-data-sources/api.md` (status: draft),
  `mcp-access-review` run as its own Step 6 — recorded **deferred** (no query surface exists yet
  to expose or withhold), `ACCESS.md` and `backend/specs/mcp-access/api.md`'s "What's
  deliberately not a tool" both updated. Covering:
  - The generic, reusable scraping-adapter abstraction (extends `backend/src/sources/base.py`'s
    existing `SourceAdapter`/`PacedFetcher` pattern rather than replacing it) — `robots.txt`
    fetch + cache + compliance check before any request, a configurable pacing/backoff policy
    (politeness, not just retry-on-error like `PacedFetcher` today), a page/response cache
    keyed so an unchanged page is never re-fetched, a required User-Agent + contact string
    convention (same spirit as the existing `SEC_EDGAR_CONTACT` env var precedent), and an
    attribution field carried on every record so licence terms can be honored wherever the data
    is later used.
  - IT Jobs Watch as the first concrete adapter built on that abstraction, plus its own data
    model — it's aggregate benchmark statistics (salary/demand trend series), not a
    `raw_postings` row or an `employment_events` row, so it needs its own table, not a forced
    fit into either existing shape.
  - Per `/new-backend-spec`'s own Step 6: this product has an MCP layer
    (`backend/specs/mcp-access/api.md`) — run `/mcp-access-review` once this spec exists, so
    whatever new query capability it creates gets an explicit exposed/not-exposed/deferred
    decision rather than drifting. (Likely **deferred** — no outcome yet calls for external-AI
    access to this data, and it isn't user-facing yet either per "Deliberately out of scope"
    above — but that's the reviewing skill's call to record, not this change request's.)
- [x] Step 4: `/implement-backend` — `backend/src/scraping/` (base.py, itjobswatch.py,
  __init__.py), `backend/src/scraping_storage.py`, `backend/src/ingest_scraped_sources.py`, four
  new tables in `db.py`, `SCRAPER_CONTACT` in `.env.example`, `beautifulsoup4`/`lxml` in
  `requirements.txt`, 11 passing tests (`backend/tests/test_scraping.py`) — verified by
  import-level and mocked-transport tests only, **not yet against a live database or the real
  itjobswatch.co.uk site** (see the spec's own Implementation note).
- [x] Step 5: Update `DATA_SOURCES.md` (manual edit) — registered in §2, new §3b (mirroring
  §3a's convention), new control-lever rows in §7, `backend/specs/scraped-data-sources/api.md`
  added to §8.
- [x] Step 6 (good-practices refinement, same day): backend spec revised in place (Business
  Logic rules 8-9, `SourceLicence`/`IngestionRun` data models, Tech Decisions) and re-implemented
  — `scrape_ingestion_runs` table, `scraping/licences.py`, run-cadence + value-level-dedupe logic
  in `scraping_storage.py`, `ingest_scraped_sources.py` updated to enforce both. 19 tests passing.
- [x] Step 7: Framework-level — Rule 13 (workspace `CLAUDE.md`) + new `.claude/skills/polite-scraping-review/`
  skill, wired into `/new-backend-spec` (Step 7) and `/change-request` (impact table, execution
  sequences, anti-patterns) the same way `mcp-access-review`/Rule 12 were.
- [x] Step 8: `/polite-scraping-review` run against this product — `DATA_SOURCES.md` §3b's review
  table added; 3/4 constraints fully enforced, licence variant still `confirmed: False` (a real,
  stated gap — not blocking the code, blocking real display/republishing until resolved).

## Decision Log
- 2026-09-16 (reopened, third time same day): New signal —
  `research/2026-09-16-scraping-good-practices-refinement.md` — asked for four concrete
  additions on top of the already-"complete" implementation: an enforced (not just documented)
  weekly run cadence; skipping storage for unchanged data ("focus on new, not old"); a real,
  source-keyed CC-licence registry (replacing the per-adapter placeholder string); and — the
  generalizing part — a framework-level principle and skill so any current or future scraped
  source gets this checked, mirroring `mcp-access-review`'s and `data-legibility`'s precedent.
  Classified `api-change` (business logic: run cadence, dedupe) — same outcome
  (`job-data-source-flexibility`), no new outcome needed. The framework-level principle/skill
  addition is handled directly, outside this product's change-request scope, matching how the
  `mcp-access-review` skill itself was created earlier this session (a meta/framework change,
  not a product change).
- 2026-09-16 (later same day): A follow-up signal —
  `research/2026-09-16-itjobswatch-data-model-analysis.md`, a detailed third-party analysis of
  what IT Jobs Watch actually publishes — arrived after Step 3 (`/new-backend-spec`) was already
  done but before implementation started. Revised the still-`draft` spec in place rather than
  opening a new change: replaced the single `itjobswatch_stats` table with a source-agnostic
  `market_observations` + `skill_associations` pair (mirroring how `employment_events` already
  sits alongside `raw_postings`), reframing IT Jobs Watch as the first adapter for a new
  **market benchmark dataset** category rather than an IT-Jobs-Watch-specific shape — a
  meaningfully better fit with this codebase's existing "one adapter, one shared model per
  source category" principle. No change to scope, change type, or the "deliberately out of
  scope" boundary — still ingestion-only, still deferred on MCP/surfacing.
- 2026-09-16: Triaged as Bucket A (maps to `job-data-source-flexibility`) — that outcome already
  frames "adapter per source, explicit at the point of use" as the model; scraping is a mechanism
  variant of the same idea, not a new outcome area. Amended its Out of scope / Success criteria
  narrowly rather than opening a new outcome.
- 2026-09-16: Classified as `new-feature` rather than `technical-refactor` alone, because IT Jobs
  Watch itself introduces a genuinely new data shape (third-party benchmark stats) needing its
  own data model — the change isn't purely internal restructuring.
- 2026-09-16: Scoped out any decision about surfacing this data to users — ingestion and the
  reusable mechanism only, this round.
- 2026-09-16 (implemented the good-practices refinement): enforced weekly run cadence
  (`scrape_ingestion_runs` + `scraping_storage.is_due()`, checked before an adapter is even
  constructed), value-level dedupe on both `market_observations`/`skill_associations` inserts,
  and a source-keyed licence registry (`scraping/licences.py`) replacing the per-adapter
  placeholder string. 19 tests passing (`backend/tests/test_scraping.py`). Framework-level:
  added Rule 13 (workspace `CLAUDE.md`) and the new `polite-scraping-review` skill, wired into
  `/new-backend-spec` and `/change-request` the same way `mcp-access-review`/Rule 12 were. Ran
  `/polite-scraping-review` against this product: 1 source reviewed, 3/4 constraints fully
  enforced, 1 real gap stated plainly — the CC licence variant is still unconfirmed
  (`confirmed: False`) — see `DATA_SOURCES.md` §3b's review table. Not a blocker for the code
  existing; is a blocker for relying on this data for real display/republishing, same as the
  still-unverified HTML parser.
- 2026-09-16 (licence actually confirmed): fetched itjobswatch.co.uk's own copyright page
  directly (WebFetch) and cross-checked via search — real, confirmed licence: **CC BY-NC-SA
  4.0**. Updated `scraping/licences.py` (`confirmed=True`), added a mandatory `licence_confirmed`
  field to both `FetchedMarketObservation`/`FetchedSkillAssociation` and their tables so the
  caveat travels with the data, added a `WARNING`-level ingestion-time log for any future
  unconfirmed source, and extended the framework-level `data-legibility` skill's Provenance
  section (+ Rule 13) so this "always flag, never block, never bury" obligation binds any future
  surface that ever shows this data. 21 tests passing. **New flag the confirmation itself
  surfaced**: CC BY-NC-SA's NonCommercial clause, against this product's Premium paid tier —
  unresolved, not urgent (nothing surfaces this data yet), recorded in `scraping/licences.py`
  and `DATA_SOURCES.md` §3b for whenever it becomes relevant. Separately, researched (not yet
  resolved) the three already-live employment-event sources' actual licensing — none are
  literally "Creative Commons" (SEC EDGAR: public domain/no restriction; UK Companies House:
  Open Government Licence v3.0; Eurofound ERM: EU's own bespoke reuse policy, attribution
  required, CC-like but not CC) — surfaced to the user as a real question rather than assumed,
  since a literal "CC-only" reading of the new "no licence, no use" rule would affect already-
  shipped production sources. Also surfaced: WARN Firehose's own Terms of Service prohibit
  redistributing/reselling raw API data or bulk exports without a separate commercial licence —
  a genuine finding needing the user's own review of what they agreed to, not something
  resolvable by reading a public page alone.
- 2026-09-16 (resolved): user confirmed "no licence, no use" means any confirmed *legitimate*
  reuse right — public domain, Open Government Licence, a source's own bespoke reuse policy, or
  CC — not literally the Creative Commons brand only. All three already-live employment-event
  sources keep running as-is (each has a confirmed legitimate basis, per the audit above).
  Recorded the full audit in `DATA_SOURCES.md` §3a and its own research file
  (`research/2026-09-16-existing-source-licensing-audit.md`) rather than touching the
  already-shipped adapters' code — the one real open item (WARN Firehose's contractual
  redistribution restriction) needs the operator's own action, not a code change.
- 2026-09-16 (commercial-use kill switch, `research/2026-09-16-commercial-mode-kill-switch.md`):
  built the actual switch — `SourceLicence.permits_commercial_use` (registry field),
  `TMIP_COMMERCIAL_MODE` env var (default `false`), `scraping.licences.is_commercial_mode()` /
  `is_source_usable()`, wired as the *first* check in `ingest_scraped_sources.ingest_adapter()`
  (before even the run-cadence check) — a source without a confirmed commercial-use licence is
  skipped entirely, no request made, once the switch is on. Deliberately conservative: an
  unconfirmed licence is treated as "not allowed" in commercial mode, even if
  `permits_commercial_use` happens to be set. Specified as forward-binding on any future
  query/display function too, per the same discipline as `licence_confirmed`'s propagation
  requirement. 25 tests passing.
- 2026-09-16 (corrected the switch's enforcement point): user clarified "we want to keep all
  sources in the ingestion runs... we would exclude the data later if we don't get a license" —
  the switch was wired to gate *ingestion* (skip the fetch entirely), which was wrong. Moved the
  gate to where it belongs: collection always proceeds regardless of `TMIP_COMMERCIAL_MODE`
  (data has value independent of current usability — a licence can be re-negotiated);
  `ingest_scraped_sources.py` now only logs, non-blocking, when a collected source isn't cleared
  for commercial use. `is_source_usable()` itself is unchanged and still the mechanism — it's
  now exclusively a forward-binding requirement on whatever future function actually *uses* this
  data (a chart, a chat answer, an MCP tool), never on the ingestion script. 25 tests still
  passing (the pure `is_source_usable()` tests needed no changes — only where it's called
  changed).
- 2026-09-16 (documentation consolidation): created `LICENSING.md` at the product root — the
  single, discoverable place for per-source licence status, the commercial-use gate's real
  behaviour, and every open flag (IT Jobs Watch's NC clause, WARN Firehose's ToS question,
  Eurofound's medium-confidence confirmation) — rather than leaving this scattered across
  `DATA_SOURCES.md`, the backend spec, and several research files. Linked from `README.md`,
  `OVERVIEW.md`, and `ONBOARDING.md`, matching the existing `ACCESS.md`/`DATA_SOURCES.md`
  pointer pattern. The admin-visibility idea raised alongside this (a licensed-vs-unlicensed
  sources view in the admin dashboard) is real new operator-facing functionality — routed
  through its own `/change-request` rather than bundled here, since it's a genuinely separate
  capability, not a continuation of this one.
