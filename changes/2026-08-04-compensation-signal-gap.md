---
id: compensation-signal-gap
date: 2026-08-04
trigger-type: internal
change-type: new-feature, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Deliver the Compensation Signal and enrich the Demand Signal

## Signal
See: `research/2026-08-04-compensation-signal-gap.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md`

Confirmed, not assumed: the outcome's "Success looks like" section already states both
"They can set a realistic salary target before applying to anything" AND "They can identify
which roles and skills are in demand vs. declining" (since 2026-06-10).
`design/information-architecture.md`'s Content Taxonomy already defines **Demand Signal**
("A data point representing job posting volume trend for a given role or skill" — marked
shipped/active) and **Compensation Signal** ("...for a given role, seniority, or
location" — marked "Future tasks"). This change activates the not-yet-built concept
(Compensation Signal) and enriches the already-shipped one (Demand Signal) with dimensions
that are already fully classified and stored but never surfaced beyond the top-level Role
Category. It does not open new outcome scope — including location: the IA's own
Compensation Signal definition already names location as one of its three facets, so
location work here is justified by an existing definition, not invented scope.

## Change Type
`new-feature` — Compensation Signal doesn't exist anywhere in the product today: no chart
element, no chat-answerable dimension, no backend field, no data model.
`ux-change` — Demand Signal (the existing trend chart + chat) already exists; this enriches
it with seniority, sub-specialization, track, and (Greenhouse-only) department dimensions
that are already classified/stored but never exposed. No new extraction pipeline needed for
this part — the data already exists in `classifications` and `raw_postings.raw_response`.
`api-change` — new data model for normalized compensation (salary) and new query/aggregation
support for the additional Demand Signal dimensions and location.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/understand-market-health-before-searching.md` | no-change — confirmed the salary success criterion already exists, verified by reading the file, not assumed |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change — "Compensation Signal" term already defined; this change activates it, doesn't redefine it. Experience spec must use this exact term, per the Content Taxonomy's "must not introduce synonyms" rule. |
| Visual Design | `design/visual-design.md` | no-change for this triage — revisit only if `/new-experience` determines a genuinely new visual token is needed (e.g. a confidence-level indicator style) |
| Experience Spec | `design/market-health/experience.md` | update — (a) define how Compensation Signal is surfaced (chart element, chat-answerable dimension, or both), including how the honest per-source confidence difference is communicated (Ashby: structured/reliable; Lever: parsed/mostly reliable; Greenhouse: extracted from free text/least reliable); (b) define how Demand Signal exposes seniority, sub-specialization, track, and location drill-down beyond the current three role-category lines — likely via the existing open-ended chat path already spec'd for this feature, possibly plus chart-level filters. Both are real UX/trust decisions left to the Designer role in `/new-experience`, not decided here. |
| Backend Spec | `backend/specs/market-health/api.md` | update — (a) new data model for normalized compensation (min/max/currency/confidence/extraction-method, linked to `raw_postings`) and per-source extraction business logic: Ashby (read structured field directly, zero LLM), Lever (regex-first, LLM fallback), Greenhouse (LLM extraction from `content`, flagged lowest confidence); (b) location normalization per source (Lever: already-clean `country` field; Ashby: `addressCountry`/`addressLocality`, needs light normalization e.g. "USA" vs "United States"; Greenhouse: weakest, needs parsing out of combined free-text location strings); (c) query/aggregation support so seniority/sub-specialization/track/department become filterable dimensions on top of existing classification data, not just internal fields |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update — render whatever the experience spec decides for both signals, including surfacing confidence/source honestly per the provenance principle already established for this feature |
| Backend Implementation | `backend/src/` | update |
| Frontend Implementation | `frontend/src/` | update |

## Execution Plan

- [x] Step 1: `/new-experience` — updated `design/market-health/experience.md`: both
      Compensation Signal and enriched Demand Signal (sub-specialization/seniority/track/
      location) are reached only through follow-up conversation — the fixed opening view
      (chart + summary) is deliberately unchanged, per Principle 3. Compensation answers
      must lead with disclosed-salary figures, state sample size, and never blend
      lower-confidence (free-text-inferred) estimates into the headline number without an
      explicit label. Added 2 Interactions rows, 3 Edge Cases, 2 Evaluation Metrics, and 2
      Open Questions (inline compensation visual, whether to promote it to the default
      view later) — deliberately deferred rather than decided now.
- [x] Step 2: `/new-backend-spec` — updated `backend/specs/market-health/api.md`. Confirmed
      and documented that sub-specialization/seniority/track drill-down needs **zero backend
      change** (`query_market_data` already supports it). Added 7 nullable `raw_postings`
      columns (`country`, `city`, `salary_min/max/currency/confidence/extraction_method`) via
      the established migration pattern. New Business Logic: per-source location
      normalization (Lever clean, Ashby normalized, Greenhouse best-effort/partial) and
      per-source compensation extraction (Ashby structured/free, Lever regex/free, Greenhouse
      explicitly excluded to avoid reopening per-posting LLM cost). Added a second data tool,
      `query_compensation_data`, alongside the existing `query_market_data`, both callable in
      the same stage. Extended `FetchedPosting` with the new optional fields. Fixed a
      contradiction found in `/api/chat`'s reasoning-trace section (hardcoded single-tool
      assumption, now tool-agnostic).
- [x] Step 3: `/new-frontend-spec` — verified (against actual `ReasoningPanel.tsx` code, not
      just its spec) that **no frontend code changes are needed**. Both new capabilities are
      conversation-only; the reasoning panel already renders `sources_and_tools` generically
      with no hardcoded tool name; compensation answers are plain markdown prose through the
      existing follow-up rendering path. Added a third "Reviewed 2026-08-04" entry to
      `frontend/specs/market-health/architecture.md`, matching the two existing precedents
      for backend-only changes.
- [x] Step 4: `/implement-backend` — implemented across 8 files, verified with `py_compile`,
      a runtime import check, and extraction logic tested against real stored posting data
      (not just compiled):
      - `sources/base.py`: extended `FetchedPosting` with 7 new optional fields; added shared
        `normalize_country()` (free-text → ISO-2, e.g. "United States"/"USA" → "US").
      - `sources/lever.py`: `country` direct from the source's own ISO field; `city` best-effort
        split of `categories.location`; salary via regex on `additionalPlain`
        (`salary_confidence: "parsed"`).
      - `sources/ashby.py`: `country`/`city` via `normalize_country()` +
        `address.postalAddress`; salary read directly from
        `compensation.summaryComponents` (`salary_confidence: "structured"`).
      - `sources/greenhouse.py`: best-effort `city`/`country` from `offices[0].location` when
        present; salary intentionally left unextracted (documented exclusion).
      - `db.py`: 7 new nullable `raw_postings` columns + an index on `country`, same
        `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` pattern as prior migrations.
      - `raw_postings.py`: `insert_new_postings` now persists the 7 new fields.
      - `market_query.py`: `query_market_data` gained `country` as a filter/group_by
        dimension (confirmed sub_specialization/seniority/track needed no change, already
        supported); added `query_compensation_data` — groups by (confidence, currency) so a
        range is never computed by mixing currencies, prefers structured over parsed per the
        experience spec's confidence rule.
      - `chat.py`: registered `query_compensation_data` as a second tool alongside
        `query_market_data` in the same call; updated the system prompt to describe both
        tools and the confidence-blending rule; fixed two places that hardcoded
        `"query_market_data"` in the synthesis prompt and reasoning-trace builder (now use
        `call.name` — a real bug this change would otherwise have introduced, since a
        `query_compensation_data` call would have been mislabeled in both places).
      - Verified extraction logic against real production data (not just syntax): correct
        ISO normalization ("United States"/"USA" → "US", "Japan" → "JP"), correct Lever
        salary regex matches (including a true-negative case with no match), correct Ashby
        structured reads, correct Greenhouse best-effort parsing and correct `None` fallback
        when `offices` is absent.
- [x] Step 5: `/implement-frontend` — confirmed the Step 3 finding holds now that the
      backend is real: `chat.py` produces `purpose=f"{call.name}(...)"`, which will read
      `"query_compensation_data(...)"` when that tool is called — `ReasoningPanel.tsx`
      already renders this generically (`s.name`/`s.purpose`), no code change needed.

Explicitly not in this plan: `/new-outcome` (outcome already covers this),
`/new-design-foundations` (foundations already active, unaffected),
`/new-information-architecture` (term already defined, no structural change).

## Decision Log
- 2026-08-04: Tracked against `understand-market-health-before-searching` — confirmed by
  reading the outcome file directly rather than assuming, since a wrong assumption here
  would misclassify a promise-fulfillment change as new scope.
- 2026-08-04: Classified `new-feature` despite mapping to an existing outcome — the change
  type taxonomy describes the nature of the change (a capability that doesn't exist yet
  anywhere in the product), which is independent of whether the outcome itself is new.
  Followed the `new-feature` canonical execution sequence, but explicitly skipped the
  steps that don't apply (outcome, foundations, IA all already in place) rather than
  running them as no-op busywork.
- 2026-08-04: Deliberately did not pre-decide the experience-level design (how salary is
  shown, how confidence differences are communicated) in this triage step — that's the
  Designer role's call in `/new-experience`, not PM triage's to make.
- 2026-08-04: Widened this change from "salary only" to also enrich the existing Demand
  Signal (seniority, sub-specialization, track, department) after the user pushed back —
  correctly: that data is already fully classified and stored, never surfaced, so it's the
  same "activate what's already promised/defined" shape as Compensation Signal, not new
  scope invention. Folded location into this change too, on the basis that the IA's own
  Compensation Signal definition already names location as one of its facets — building
  location support in service of that existing definition isn't the same as formally adding
  "geography" as a new, independent outcome success criterion (still not done here).
- 2026-08-04: Still left "Skills-in-demand extraction" out of this change — different cost
  shape (per-posting, not per-title, LLM extraction), deserves its own triage regardless of
  how the rest of this change grew.
- 2026-08-04: Did not touch "Company-specific breakdowns" — outcome explicitly lists this
  as out of scope; per-company salary comparisons would contradict that boundary and aren't
  part of this change.
