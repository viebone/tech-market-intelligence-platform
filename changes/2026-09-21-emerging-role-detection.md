---
id: emerging-role-detection
date: 2026-09-21
trigger-type: user-feedback
change-type: new-feature
outcome: pipeline-processing-visibility
status: in-progress
---

# Change Request: Recurring emerging-role detection (a real, repeatable "what's the taxonomy missing" query)

## Signal
User (this session), reacting to the specialization-widening work above: "i am surprised you
didn't come with a better breakdown for designer... plus what would happen when new roles
emerge? i like your analysis, so I would like to run that analysis every month and come with
emerging roles once we start detecting them appearing often. maybe multiple change request in
one so good to document this ideas." Two distinct things bundled in that message, split into
two change requests deliberately (this is the second — see
`changes/2026-09-21-taxonomy-revision-specialization-and-job-function.md` for the first, which
this one's real first test run directly improved before its own backlog even ran).

## Outcome
See: `outcomes/pipeline-processing-visibility.md` ("Extended 2026-09-21") — a new, distinct
operator need from what that outcome already covers: not "what has the pipeline processed" but
"what does the pipeline keep seeing that the taxonomy doesn't have a category for yet."

## Change Type
`new-feature` — a genuinely new operator capability (detecting real off-canon/emerging
classification signal on a repeatable cadence), not a refinement of an existing one. No
experience-spec/IA/visual-design layer needed — this is operator-only, same carve-out
`pipeline-processing-visibility` already has from the consumer-facing paradigm.

## What was built and proven, not just proposed
`classification.py::get_emerging_taxonomy_candidates()` — real, tested directly against
production (not assumed to work):
- `off_canon_specializations`: real specialization values under a tracked Role Category not yet
  in the canonical `SPECIALIZATIONS` dict (the same dict `SYSTEM_INSTRUCTION` is built from —
  single source of truth, cannot drift), grouped and ordered by real frequency
- `other_non_tech_titles`: real titles piling up under Job Function's `Other Non-Tech` catch-all
- `unknown_rate`: real `role_category = "unknown"` volume and share

**Its first real run immediately proved the concept**: it surfaced 7 real ≥10-occurrence
specialization gaps the earlier manual top-25 pull had missed entirely, plus a 4th real
classification inconsistency (`Technical Program Manager` landing under both `Engineer` and
`Product Manager`) — all folded into the taxonomy revision above, before its own reclassification
backlog spent a single request. That's the concrete answer to "what happens when new roles
emerge": this function is what would have caught them, on a monthly cadence, going forward.

Detection/reporting only, by design — it never coerces, renames, or discards anything.
Formalizing an emerging value is still always a human (PM) decision, same as every prior
taxonomy revision in this project's history (2026-08-11, 2026-09-21).

## What's deliberately left open — two real decisions, not guessed at

1. **Cadence**: an on-demand function an operator calls when they think to (simplest, already
   works) vs. an actual scheduled monthly job that produces a report automatically (matches the
   user's literal "run that analysis every month" more closely, but is more infrastructure —
   this codebase already runs scheduled ingestion/classification crons, so the mechanism exists,
   it would just need a new scheduled entry).
2. **Surface**: fold into the existing `/admin/` overview page (fastest, reuses
   `get_classification_distribution`'s existing template wiring) vs. a new dedicated
   `/admin/taxonomy-health` view (cleaner separation, matches this project's own precedent of a
   dedicated admin route per real capability — postings, runs, employment-events, licensing,
   market-observations, skill-associations, scrape-runs).

Not resolved in this change — genuinely the user's call, not assumed silently.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/pipeline-processing-visibility.md` | update — "Extended 2026-09-21" + new success criterion |
| Reference Spec | `design/market-health/job-classification.md` | update — "Monthly emerging-role detection" note under Job Function |
| Backend Implementation | `backend/src/classification.py` | new — `get_emerging_taxonomy_candidates()`, `MIN_EMERGING_OCCURRENCES` |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | **not yet updated** — pending the cadence/surface decision above; this function has no endpoint wired to it yet |
| Admin Implementation | `admin_main.py` | **not yet touched** — same reason |

## Execution Plan

- [x] Step 1: Designed the detection function's 3 signals from real taxonomy structure, not invented
- [x] Step 2: Built `get_emerging_taxonomy_candidates()`, sharing `SPECIALIZATIONS`/`JOB_FUNCTIONS` as the single source of truth with the LLM prompt
- [x] Step 3: Ran it for real against production — proved it works and immediately improved the same-day taxonomy revision
- [x] Step 4: Extended `outcomes/pipeline-processing-visibility.md` and `job-classification.md` documenting this as a standing capability
- [ ] Step 5: **Pending decision** — cadence (on-demand vs. scheduled) and surface (existing overview vs. new admin route) — see above
- [ ] Step 6: Once decided, `/new-backend-spec` (or a direct update to `pipeline-visibility/api.md`) + wire the actual admin route/cron

## Decision Log
- 2026-09-21: Built and proved the detection function itself now (cheap, backend-only, real
  value already demonstrated) but deliberately did not guess the cadence/surface decision —
  asked instead, consistent with this framework's own "ask when genuinely ambiguous" rule.
