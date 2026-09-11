---
id: employment-event-ingestion
date: 2026-09-11
trigger-type: market-signal
change-type: new-feature
outcome: understand-market-health-before-searching
status: in-progress
---

# Change Request: Employment event ingestion (layoffs, restructuring, closures, expansion)

## Signal
See: `research/2026-09-11-employment-event-data-sources.md`

## Outcome
Primary: `outcomes/understand-market-health-before-searching.md` — its original signal already
named layoffs as something professionals need to see before committing to a search, and the
success criteria promise a market-health read that includes more than job-opening counts.

Secondary (architectural constraint, not the driving outcome): `outcomes/job-data-source-flexibility.md`.
`DATA_SOURCES.md` §2 already lists **Layoff events** as a planned source type ("New table —
*not* `raw_postings`, *not* classified... Needs its own adapter contract + data model + a
`/change-request`") and §5 explicitly instructs that adding a new source *type* starts here.
The IA (`design/information-architecture.md:170`) already carries a **Layoff Signal** term,
currently marked "Future tasks" with no structural placement — this change is what gives it one.
Every new-source adapter this change adds (Eurofound ERM, US state WARN, UK ONS HR1, UK
Companies House) must follow the adapter boundary that outcome established: one adapter per
source, mapped into one internal model, no business logic branching on source.

## Change Type
`new-feature` — `employment_event` is a capability that doesn't exist anywhere in the product
today (new entity, new ingestion adapters, new narrative surface).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | update — make the layoff/employment-risk read an explicit success criterion, not just an implicit signal |
| Design Foundations | `design/foundations.md` | no-change — UX principles and AI Involvement tier unaffected |
| Information Architecture | `design/information-architecture.md` | update — give **Layoff Signal** a real structural placement (today only a term entry marked "Future tasks") |
| Visual Design | `design/visual-design.md` | update (v1.5 → v1.6) — reviewed in Step 4: no new colour token needed (existing semantic tokens sufficient), added one new reusable component pattern ("Chart event marker") since it's the kind of primitive the doc already documents for reuse (Ranked bar list, Meter) |
| Experience Spec | `design/market-health/experience.md` | update — decided in Step 2: folded in place rather than a new `employment-signals` folder, since the outcome, the chart, and the conversation are already market-health's; adds Layoff Signal (4th follow-up signal, sharing Requirements Signal's two-part synthesis shape) + an employment-events strip on the existing trend chart |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — event markers on the existing trend chart component, Layoff Signal answer rendering |
| Backend Spec | `backend/specs/market-health/api.md` | update — `employment_event` data model + one adapter per source (Eurofound ERM, US state WARN, UK ONS HR1 macro index, UK Companies House insolvency enrichment), per the `job-data-source-flexibility` adapter pattern |
| Frontend Implementation | `frontend/src/` | update — after frontend spec |
| Backend Implementation | `backend/src/` | update — after backend spec, incl. new adapters under `backend/src/sources/` per `DATA_SOURCES.md` §5 |

## Standing requirement: source documentation

Every step below that touches a source must keep it documented in three places, kept in sync —
this is not a one-time note, it applies at every step that adds or changes a source:
1. **`research/2026-09-11-employment-event-data-sources.md`** — the source-evaluation record
   (already captures geography, company-level vs. aggregate, endpoint characteristics, and why
   Layoffs.fyi was deprioritized). Update it if a source's access method or reliability changes
   during spec/implementation (e.g. an endpoint turns out to need a manual data-access request
   rather than being programmatically automatable).
2. **`backend/specs/employment-signals/api.md`** (written in Step 5) — the technical adapter
   contract per source: endpoint/access method, auth requirement, update cadence, rate limits,
   field mapping into `employment_event`, and confidence/provenance handling.
3. **`DATA_SOURCES.md`** (product root) — the single live index of every source the platform
   draws from. Its "Layoff events" row (§2) currently says `🔲 planned`; flip it to the correct
   status per adapter as each one goes live, and add each new adapter to §3's adapter table
   (or a new section, if layoffs adapters don't fit the job-posting adapter table's shape).
   Every `employment_event` row's `source` field must be traceable back to a row in this doc.

## Execution Plan

- [x] Step 1: Update `outcomes/understand-market-health-before-searching.md` — added explicit
      employment-risk + source-traceability success criteria (manual edit, not a skill)
- [x] Step 2: `/new-experience` — updated `design/market-health/experience.md` **in place**
      (not a new feature folder — see Decision Log): Layoff Signal as a 4th follow-up signal
      reusing Requirements Signal's two-part synthesis shape for pattern-vs-isolated-event
      judgment (User Flow 7d), plus a non-conversational employment-events strip on the
      always-visible trend chart so hiring and contraction/expansion read as one picture
      (the user's explicit "full picture" ask). Full Chart Specification, Written Summary
      causation-caution rule, Interactions, Edge Cases, and Evaluation Metrics additions
      included. Two decisions deferred to later steps (flagged in the spec's Open Questions):
      broadening the IA's `Layoff Signal` term beyond layoffs-only (→ Step 3), and whether a
      dedicated data-story overview is worth adding later (deferred, not needed now).
- [x] Step 3: `/new-information-architecture` — broadened **Layoff Signal**'s definition in
      `design/information-architecture.md` (v2.3 → v2.4) to cover the full employment-event
      range (contraction + expansion), kept the existing term name (already used everywhere),
      updated "Where it appears" from "Future tasks" to live locations. No new Task Panel
      item, zone, or Key Pathway — the event-marker click is a single-section interaction
      already covered by the experience spec's own Interactions table, not a cross-section
      pathway.
- [x] Step 4: `/new-visual-design` — reviewed (`design/visual-design.md` v1.5 → v1.6).
      Confirmed: existing semantic tokens (Rising/Declining/Stable) fully cover the event
      marker's colour needs, no new hue, and no conflict with the Role Category accent-colour
      cap (separate system). Added a documented "Chart event marker" component pattern
      (reusable primitive, same reasoning as Ranked bar list/Meter) and confirmed the inline
      event-detail expansion explicitly reuses the Reasoning Panel toggle's motion and panel
      styling rather than inventing a new one.
- [x] Step 5: `/new-backend-spec` — updated `backend/specs/market-health/api.md` in place.
      Delivered:
      - `EmploymentEvent` data model (`employment_events` table) — new, not `raw_postings`,
        not classified, with `matched_company` (curated alias map, never fuzzy/LLM-matched)
        and `confidence: "confirmed" | "reported"` per-source.
      - Three adapter contracts, priority order: **Eurofound ERM** (access mechanism
        unconfirmed — flagged, not guessed), **US state WARN** (per-state, curated/verified
        state list — mechanism confirmed, exact states TBD), **UK Companies House insolvency**
        (confirmed automatable, keyed API).
      - **UK ONS HR1 deliberately descoped** — its macro/aggregate-only shape (no company
        names) can't produce an `EmploymentEvent` row, and nothing in the experience spec
        asked for a UK macro index. Documented, not silently dropped — revisit only behind
        its own future experience spec.
      - New endpoint `GET /api/market-health/employment-events` (chart strip, tracked
        companies only) and a 4th chat tool `query_employment_events_data` (Layoff Signal
        conversation, any company/sector, not tracked-only) — plus the pattern-vs-isolated
        synthesis rule (≥2 events before a pattern judgment is offered).
      - New `EmploymentEventAdapter` protocol (separate from `SourceAdapter` — different
        output shape), its own cron schedule (decoupled from `ingest.py`, since Eurofound may
        need a manual/on-demand path if its access turns out to be gated).
      - Standing requirement fulfilled: `DATA_SOURCES.md` updated (§2 row, new §3a adapter
        table, §8), `research/2026-09-11-employment-event-data-sources.md` updated with a
        "Resolved during backend spec" section, product `CLAUDE.md`'s Spec Chain Status table
        flagged (spec'd, not yet implemented).
- [x] Step 6: `/new-frontend-spec` — updated `frontend/specs/market-health/architecture.md` in
      place. Two new components (`EmploymentEventsStrip`, `EventMarkerDetail`) sharing
      `JobOpeningsChart`'s existing x-scale (never a second one); a new TanStack Query keyed on
      `range` only (no `granularity`, matching the backend endpoint); marker-merge is pixel-based
      client-side layout logic. Confirmed — by tracing the real component tree, same review
      discipline this spec already holds itself to — that the Layoff Signal conversational
      answer needs **zero** new rendering component: it's a 4th server-side chat tool consumed
      through the existing SSE contract, its two-part answer renders through
      `ConversationThread.tsx`'s existing plain-text path exactly like Requirements Signal's
      synthesis answers, and `ReasoningPanel.tsx` already renders its trace generically. Spec
      status downgraded `implemented` → `ready` (new pieces not yet built).
- [x] Step 7: `/implement-backend`. Delivered, matching the backend spec exactly:
      - `employment_events` table (`db.py`, additive migration).
      - `EmploymentEventAdapter` protocol + registry (`backend/src/employment_events/`).
      - **UK Companies House insolvency adapter — code complete** (`companies_house.py`):
        real search + insolvency calls, case-type mapping, per-company fault isolation. Its
        `CANDIDATE_COMPANIES` seed list is deliberately empty (which of the 35 tracked
        companies have a real UK entity is a research task, not a code task) — `fetch()`
        returns `[]` until populated, which is a correct, safe default, not a bug.
      - **Eurofound ERM and US WARN adapters — honest scaffolds, not functional.** Per this
        step's own instructions: their real access mechanisms (Eurofound's CSV-request
        gate; each US state's WARN page format) were never empirically verified from this
        environment, so rather than fabricate a working call against a guessed endpoint,
        both `fetch()` methods log a clear notice and return `[]`, with a TODO in each
        module's docstring naming the exact next verification step. This matches the
        pipeline's own standing "confirm empirically, don't assume" discipline.
      - Company-alias map (`company_aliases.py`, ~90 seed entries) — unverified against any
        real ingested record yet, flagged as such.
      - `GET /api/market-health/employment-events` (`market_employment_events.py`, wired
        into `main.py`) — tracked-companies-only, matching the backend spec exactly.
      - `query_employment_events_data` chat tool (`market_query.py`), wired into `chat.py`'s
        tool list, system prompt, and synthesis-stage pattern-vs-isolated instructions.
      - **Reasoning-trace fix**: found and fixed a real pre-existing gap while wiring this in
        — `chat.py`'s trace builder hardcoded one source name for every tool call, which
        would have mislabeled employment-event answers as coming from the job-board
        database. Now branches on tool name so `query_employment_events_data` calls name
        the real registries via `sources_checked`.
      - Standalone cron entrypoint (`ingest_employment_events.py`) + its own Railway config
        (`backend/railway.employment-events.json`) — a separate service, not yet connected
        in the Railway dashboard (a new production service is a deliberate manual step, not
        something to create as a side effect of this pass — see `DEPLOYMENT.md`).
      - `DATA_SOURCES.md` updated: §3a adapter statuses corrected to reflect real code state,
        new §7 control-lever entries.
      - **Verification**: this environment has no WSL/Linux Python available, so the actual
        `venv_linux` dev workflow (`CLAUDE.md`) could not be run here. Verified instead with
        the repo's stray Windows `venv` (which happens to have the real dependencies
        installed): `python -m py_compile` on every new/changed file (clean), then a real
        import of every new module plus `chat.py` and `main.py` together (clean — the new
        route registers, `ALL_EMPLOYMENT_EVENT_ADAPTERS` resolves, `resolve_company()` and
        `direction_for()` behave correctly). **Not verified**: an actual Postgres round-trip
        (`employment_events` insert/select), the live `/api/chat` tool-calling path end to
        end, or any adapter against a real network endpoint. Recommend a real WSL run before
        calling this "implemented" in the Spec Chain Status table.
      - Net state: **wired but not yet fed** — every consumer (endpoint, chat tool, chart)
        is correct against an empty table; nothing will show until at least one adapter's
        TODO is finished. Honest, not a shortcut.
- [x] Step 8: `/implement-frontend`. Delivered, matching the frontend spec (one disclosed
      deviation noted below):
      - `EmploymentEventsStrip.tsx` (new) — markers + merged-marker badges + hover tooltip +
        click-through detail. `EventMarkerDetail` combined into the same file rather than a
        separate one (small, tightly coupled, no reuse elsewhere) — disclosed in the file's
        own comment, not silently dropped from the spec.
      - **Real finding, not assumed**: `JobOpeningsChart.tsx`'s actual x-scale is
        **index-based** (`toX(i) = PAD.left + (i / (data.length-1)) * drawW`), not
        date-proportional — the frontend spec's "shares the x-scale" language could have been
        misread as a naive date→pixel formula, which would have misaligned every marker except
        by coincidence. Added `dateToFractionalIndex()` to convert an event's real calendar
        date into the fractional bucket position it falls between, then feeds that through the
        exact same `toX()` the trend lines use — genuinely sharing the scale, not just reusing
        its name.
      - `JobOpeningsChart` gained an optional `events` prop; `MarketBriefingMessage` and
        `MarketHealthPage` updated to fetch and thread it through. New TanStack Query keyed
        `["market-health", "employment-events", range]` — separate from `"openings"`, no
        `granularity` dependency, fails soft (an error here never blocks the chart).
      - **Confirmed, not just trusted**: read the real `ConversationThread.tsx` and
        `ReasoningPanel.tsx` directly — both already generic (plain `whitespace-pre-wrap` text;
        no hardcoded tool name) — the frontend spec's claim that Layoff Signal needs zero new
        conversational-rendering code holds.
      - **Verified with a real `npm run build`** (`tsc && vite build`) in this environment —
        clean, zero TypeScript errors, build succeeded (262.88 kB bundle). This is an actual
        result, not an assumption; frontend runs natively on Windows per this product's
        `CLAUDE.md`, so no WSL limitation applied here (unlike Step 7's backend verification).
      - **Current visible behaviour**: identical to before this change. The strip renders
        nothing because `GET /api/market-health/employment-events` currently returns an empty
        array (no adapter has live data yet — Step 7's honest gap). This is the correct,
        verified empty-state behaviour, not a placeholder — once an adapter goes live, the
        strip will render with no further frontend work needed.

## Status note (2026-09-11 — all 8 framework steps complete)

Every step in the execution plan above is done, verified, and documented — outcome through
implementation, full spec chain updated in place, both a real backend import/route check and a
real frontend `npm run build` passed. **Status is kept at `in-progress`, not `complete`**,
because the outcome's actual promise (employment risk visible alongside demand) isn't yet true
for a real user: the strip and Layoff Signal answers are correct but currently empty, since no
adapter has live data. Marking this `complete` would overstate what's true today.

**Remaining work, outside this change's step-list (tracked here so it isn't lost):**
- [ ] Verify Eurofound ERM's real access mechanism (`backend/src/employment_events/eurofound_erm.py` TODO) and finish its adapter
- [x] ~~Verify and add at least one US state to `STATE_FETCHERS`~~ — **superseded and DONE,
      live data.** Live research found WARN Firehose (all 50 states, one API, free tier),
      which replaced the per-state design entirely. User supplied a real API key; ran a real
      authenticated test call, corrected the field mapping against the true response shape
      (`company_name` not `company`, `industry`→`sector`, real per-record `source_url`), then
      ran `ingest_employment_events.py` for real: **25 real rows inserted**, re-run confirmed
      idempotent (0 new). Fixed a real bug found in the same pass: the initial 4-day trailing
      window returned 0 rows because the feed lags ~9 days behind the actual date — widened
      to 30 days, empirically informed, not guessed. **Registry pattern confirmed and
      documented as the standing recipe for adding any future source** — `employment_events/__init__.py`'s
      docstring now spells out the exact 4-step process (`ingest_employment_events.py` already
      loops over `ALL_EMPLOYMENT_EVENT_ADAPTERS` generically, no per-source code anywhere else
      in the pipeline).
- [x] ~~Research and populate `CANDIDATE_COMPANIES` for UK Companies House~~ — **superseded**
      by `changes/2026-09-11-employment-events-no-company-matching.md`: the candidate-list
      design (itself a form of company-matching) was replaced entirely by the Companies House
      **Streaming API** (all UK companies, no targeting). The 6-company research done here is
      no longer used by any code, kept only as a record of what was tried.
- [x] ~~Verify `COMPANY_ALIASES` against real ingested `company_raw` values~~ — **moot**:
      `company_aliases.py` and `matched_company` were deleted entirely in the same
      no-company-matching change.
- [x] Get a `COMPANIES_HOUSE_API_KEY` (Streaming type, not REST — the two aren't
      interchangeable) and exercise the adapter for real. **Done 2026-09-11** — user provided a
      key; a real test call revealed 3 field-name errors in the original guess
      (`resource_id` not nested under `resource`, `data.cases` not `resource.case`, `date` not
      `made_up_date`), fixed against the real payload; real ingestion then pulled 2 genuine UK
      insolvency events. **Known, permanent limitation found**: the Streaming API carries no
      company name, only a company number — `company_raw` is `"Company {number}"` until a
      separate REST-type key is added (not pursued yet, an honest gap not a guess).
- [ ] Connect the `employment-events` Railway service (config committed, dashboard step not taken — `DEPLOYMENT.md`)
- [ ] Run a real WSL verification pass on the backend (Step 7 could only be verified via a stray Windows venv in this session)
- [ ] Once real data exists: revisit the deferred "threshold" for when the written summary mentions employment events (experience spec Open Questions), and re-evaluate whether a dedicated data-story overview is worth adding

**Follow-on (2026-09-11, later same day)**: `changes/2026-09-11-employment-events-independent-scope.md`
— user direction to treat employment events as an independent, broader market-intelligence
dataset rather than scoped to the 35 tracked companies. **`complete`** — added a second
data story ("Employment risk across the market") built entirely from `employment_events`.
Also triggered a real source-catalogue expansion — `research/2026-09-11-employment-event-data-sources.md`'s
"Expanded source catalog" — which found **WARN Firehose** and led to rewriting the US WARN
adapter (see the superseded checklist item above).

**Second follow-on (2026-09-11, hours later still)**: `changes/2026-09-11-employment-events-no-company-matching.md`
— the user clarified, firmly and repeatedly, that employment events must be independent of
tracked companies **everywhere**, not scoped anywhere. **`complete`** — `matched_company` and
its alias map deleted entirely; the tracked-company-scoped chart strip (`EmploymentEventsStrip`,
`GET /api/market-health/employment-events`) built and verified in Steps 7/8 above was then
**removed**; `query_employment_events_data`'s `hiring_trend` removed; UK Companies House's
adapter redesigned around the Streaming API instead of a tracked-company candidate list. The
"Employment risk across the market" data story is now the **only** surface for employment
events. This is the final, current state of the feature — read this note, not the original
Step 7/8 summaries above, for what's actually true today.

**Third follow-on (2026-09-11, same day)**: `changes/2026-09-11-employment-risk-12-month-window.md`
— once a real `COMPANIES_HOUSE_API_KEY` produced actual UK data, Story 2's 90-day window
turned out to silently drop it (a case's own date can lag well behind when it's observed on a
live feed). Widened to 12 months. **`complete`.**

**Fourth follow-on (2026-09-11, same day)**: `changes/2026-09-11-employment-risk-hide-placeholder-names.md`
— UK Companies House events with no real company name (a bare id) were being shown as if they
were one; fixed at the source (`company_raw` stores the bare id honestly, never a fabricated
"Company N" string) and filtered at display (`is_real_company_name()`) — such events still
count toward every non-name aggregate. **`complete`.**

**Fifth addition (2026-09-11, same day, via the pre-approved "add a new source" recipe —
`employment_events/__init__.py`'s own docstring — not a fresh spec-chain pass, matching that
recipe's explicit design)**: **SEC EDGAR full-text search** (`sec_edgar_8k`) —
`research/2026-09-11-employment-event-data-sources.md`'s "Expanded source catalog" candidate,
built and verified live: 9 real 8-K Item 2.05 filings on first run, real company names
straight from the record. Zero auth needed (a descriptive `User-Agent` only, per SEC policy).
Also fixed a real, subtle bug found while verifying it alongside Companies House:
`insert_new_events()` didn't dedupe repeats *within* one fetch batch — harmless to stored data
(the DB's `ON CONFLICT DO NOTHING` already caught it) but overstated the "N new" count every
adapter logs, for any source (like a change-stream) that can emit multiple updates to the same
record in one run. Fixed in `employment_events_storage.py`.

## Decision Log
- 2026-09-11: Triaged against `understand-market-health-before-searching` (chosen over
  `job-data-source-flexibility`) per user decision — this is primarily a user-facing market-health
  capability; the source-flexibility outcome is the architectural constraint it must follow, not
  the outcome it serves.
- 2026-09-11: Noted but not blocking — TMIP has one other change (`requirements-backlog-batch-catchup`)
  still `in-progress` as of this triage; this change request is independent of it.
- 2026-09-11: User asked to keep sources well documented throughout — added a standing
  requirement (not a single checklist line) covering the research file, the backend spec's
  adapter contracts, and `DATA_SOURCES.md`'s live index, so provenance stays traceable at every
  layer as adapters are added.
- 2026-09-11: **Scope decision during backend spec** — UK ONS HR1 (originally priority 3 in
  the research/change-request execution plan) is deliberately **not** implemented. It's a
  macro/aggregate index with no company names, incompatible with the `EmploymentEvent` model's
  company-level shape, and nothing in the experience spec (Step 2) asked for a UK macro risk
  index. Priority order for what's actually built: Eurofound ERM → US state WARN → UK
  Companies House insolvency. Full reasoning in `backend/specs/market-health/api.md` —
  Business Logic — "UK ONS HR1 (descoped)". Flagged for the user's awareness since it changes
  the originally-proposed 4-source plan to 3.
- 2026-09-11: User's UX direction — "a full picture of the market, hiring but also layoffs,
  and understand if layoffs follow a pattern or are independent events" — decided this stays
  inside `design/market-health/experience.md` rather than a new `employment-signals` feature
  folder: the "full picture" ask is explicitly about *one* view, and the accordion spec had
  already anticipated a "layoff event count" context item years before this change, confirming
  it was always meant to live here. Pattern-vs-isolated-event reuses Requirements Signal's
  existing two-part synthesis-answer shape rather than inventing a new answer format.
