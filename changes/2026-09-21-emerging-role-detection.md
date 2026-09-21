---
id: emerging-role-detection
date: 2026-09-21
trigger-type: user-feedback
change-type: new-feature
outcome: pipeline-processing-visibility
status: complete
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

1. **Cadence — resolved: once a month.** User's decision. Implemented as a live, on-demand
   query recomputed on every page load, not a stored monthly snapshot — there's nothing for a
   cron to generate or mutate here (the function only reads, never writes), so "monthly"
   describes the operator's own habit of checking the page, not a backend automation. Named
   explicitly in the endpoint's own spec section so this isn't mistaken for an oversight later.
2. **Surface — resolved: a new dedicated `/admin/taxonomy-health` view.** User's decision,
   matching this project's own precedent of one dedicated admin route per real capability.
   Built: `admin_main.py::taxonomy_health()`, `admin_templates/taxonomy_health.html`, nav link
   in `base.html`. Rendered and verified directly against real production data (not assumed) —
   contains the real known off-canon value `"Engineering Manager"` and a correctly-computed
   unknown rate.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/pipeline-processing-visibility.md` | update — "Extended 2026-09-21" + new success criterion |
| Reference Spec | `design/market-health/job-classification.md` | update — "Monthly emerging-role detection" note under Job Function |
| Backend Implementation | `backend/src/classification.py` | new — `get_emerging_taxonomy_candidates()`, `MIN_EMERGING_OCCURRENCES` |
| Backend Spec | `backend/specs/pipeline-visibility/api.md` | update — new `GET /admin/taxonomy-health` endpoint section |
| Admin Implementation | `admin_main.py` | update — new `taxonomy_health()` route |
| Admin Implementation | `admin_templates/taxonomy_health.html`, `base.html` | new / update — new template, new nav link |
| Plain-Language Overview | `OVERVIEW.md` | update — "(Operator only)" paragraph gained a sentence. **Caught by a same-day audit, not the original commit** — see Decision Log. |
| MCP Access Review | `ACCESS.md` | update — new row, "Operator-only capabilities" table, same pattern as every other admin view. **Caught by the same audit.** |

## Execution Plan

- [x] Step 1: Designed the detection function's 3 signals from real taxonomy structure, not invented
- [x] Step 2: Built `get_emerging_taxonomy_candidates()`, sharing `SPECIALIZATIONS`/`JOB_FUNCTIONS` as the single source of truth with the LLM prompt
- [x] Step 3: Ran it for real against production — proved it works and immediately improved the same-day taxonomy revision
- [x] Step 4: Extended `outcomes/pipeline-processing-visibility.md` and `job-classification.md` documenting this as a standing capability
- [x] Step 5: User decided — cadence: once a month; surface: new dedicated view
- [x] Step 6: Built `GET /admin/taxonomy-health` (`admin_main.py`, `taxonomy_health.html`, `base.html` nav), documented in `pipeline-visibility/api.md`, rendered and verified directly against real production data

## Decision Log
- 2026-09-21: Built and proved the detection function itself now (cheap, backend-only, real
  value already demonstrated) but deliberately did not guess the cadence/surface decision —
  asked instead, consistent with this framework's own "ask when genuinely ambiguous" rule.
- 2026-09-21: User decided monthly cadence + a new dedicated view. Implemented cadence as a
  live on-demand query rather than a stored snapshot/cron — there is nothing for a scheduled
  job to generate here (the function only reads), so a cron would have added infrastructure
  with no real behavior behind it. Named this reasoning explicitly in the endpoint's spec
  section so it reads as a deliberate choice, not a shortcut, if revisited later.
- 2026-09-21 (caught by a same-day audit, "is all of the changes today well documented?"):
  the new `/admin/taxonomy-health` view had been built and spec'd in `pipeline-visibility/
  api.md`, but `OVERVIEW.md`'s "(Operator only)" paragraph and `ACCESS.md`'s Operator-only
  table — both of which every prior admin view (licensing 2026-09-16, market-observations
  2026-09-18) got a real entry in — were missed. Fixed same-day, not carried forward.
