---
id: itjobswatch-expanded-role-coverage
date: 2026-09-18
trigger-type: user-feedback
change-type: content-change
outcome: job-data-source-flexibility
status: complete
---

# Change Request: Expand IT Jobs Watch tracked-role coverage, and standardise/document how roles are added

## Signal
See: `research/2026-09-18-itjobswatch-expanded-role-coverage.md`

## Outcome
See: `outcomes/job-data-source-flexibility.md` — this is content curation inside the already-
delivered `scraped-data-sources` capability (more of the same kind of data, not a new
capability), same weight as adding a tracked company under `job-data-source-flexibility`'s
existing scope. No success criteria change.

## Change Type
`content-change` — this is data curation (which roles a scraped source tracks), not a new
capability, endpoint, or data model. Same conceptual weight as `DATA_SOURCES.md` §5's existing
"add a tracked company" recipe, now established for scraped roles too.

## Triage Notes (Step 2)

Maps to `job-data-source-flexibility` — no new area. The user explicitly asked that this be
"standardised and documented properly," so this change request's real work is establishing a
repeatable, documented procedure (mirroring §5's company-add recipe), not just editing a list.

**Why these 5 roles**: checked against this platform's own job-posting taxonomy
(`classification.py`'s `ROLE_CATEGORIES = {"Designer", "Product Manager", "Engineer"}`) — the
original 3 `ROLE_SLUGS` (`product-owner`, `ux-designer`, `product-manager`) covered Product
Manager (2 of 3) and Designer (1 of 3) but had **zero** Engineer coverage, despite Engineer
being a core tracked category for job postings. Added `software-developer`, `devops-engineer`,
`data-engineer`, `full-stack-developer` (Engineer) and `product-designer` (Designer) to close
that gap and round out Designer.

**Verification, per this codebase's own "confirm empirically, never guess" discipline**: each
of the 5 new slugs was checked against the real live site via one approved `WebFetch` request
per slug (same caveat as the original 3-role check — this is outside the compliant
`PoliteScraper` path, a read-only confirmation, not a repeated pattern), quoting the real
rank/vacancy figures rather than assuming the slug resolves:

| Slug | Rank | Vacancy count |
|---|---|---|
| software-developer | 147 | 1,486 |
| devops-engineer | 169 | 1,339 |
| data-engineer | 102 | 2,064 |
| full-stack-developer | 213 | 1,027 |
| product-designer | 718 | 86 |

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | no-change |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | none (deliberate, per the original scraped-data-sources spec) | no-change |
| Frontend Spec | none | no-change |
| Backend Spec | `backend/specs/scraped-data-sources/api.md` | no-change (the adapter's generic design is unaffected — which specific roles are tracked is data curation, documented in `DATA_SOURCES.md`, not the backend contract) |
| Frontend Implementation | `frontend/src/` | no-change |
| Backend Implementation | `backend/src/scraping/itjobswatch.py` | update — `ROLE_SLUGS` (3 → 8), a name-override map for `devops-engineer` |
| Plain-Language Overview | `OVERVIEW.md` | no-change — this data isn't surfaced anywhere yet |
| MCP Access Review | `ACCESS.md` + `backend/specs/mcp-access/api.md` | no-change — still deferred/not exposed |
| Polite Scraping Review | `DATA_SOURCES.md` + affected backend spec | update — new §3b subsection ("Tracked roles") + a documented add/retire procedure, mirroring §5's tracked-companies recipe. Doesn't change any of the four enforced constraints themselves (cadence/robots/dedupe/licence all already cover any `entity_name`/`role_name` value generically) |

## Execution Plan

- [x] Step 1: Signal captured — `research/2026-09-18-itjobswatch-expanded-role-coverage.md`
- [x] Step 2: PM triage — mapped to `job-data-source-flexibility`, classified `content-change`
- [x] Step 3: Verified all 5 new role slugs against the real live site (rank/vacancy figures quoted above) before adding any of them
- [x] Step 4: Updated `DATA_SOURCES.md` §3b — new "Tracked roles" table (8 roles, mapped to `role_category`, verified figures) and a documented "add/retire a tracked role" procedure mirroring §5; updated the §7 control-lever index (new "Tracked roles" and "Extraction model" rows, corrected a stale "unverified against the real site" note)
- [x] Step 5: `backend/src/scraping/itjobswatch.py` — expanded `ROLE_SLUGS` to 8, added `_ROLE_NAME_OVERRIDES` for `devops-engineer` (`str.title()` would otherwise store "Devops Engineer" instead of the real "DevOps Engineer")
- [x] Step 6: Verified — `backend/tests/test_scraping.py` still 37/37 passing; module imports cleanly

## Decision Log
- 2026-09-18: Prioritized Engineer-category coverage first, since it was completely absent
  despite being a core tracked category for job postings — not an arbitrary pick.
- 2026-09-18: Verified every new slug against the real site before adding it, same discipline
  already established for tracked companies (§4) — a wrong slug should 404 loudly during
  verification, never silently ship as a guess.
- 2026-09-18: Established a real, documented, repeatable "add/retire a tracked role" procedure
  in `DATA_SOURCES.md` §3b, mirroring §5's tracked-companies recipe exactly, per the user's
  explicit request that this be "standardised and documented properly" rather than a one-off
  code edit.
- 2026-09-18: Did not trigger an immediate re-ingestion — the run-cadence gate
  (`scrape_ingestion_runs.last_run_at` for `itjobswatch`, 7-day interval) means the new 5 roles
  will be picked up on the next due run (2026-09-25) unless a manual one-time reset is
  explicitly requested, same "don't silently bypass the cadence guard" discipline the previous
  change (`changes/2026-09-18-itjobswatch-llm-extraction.md`) already established.
