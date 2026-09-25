---
id: employer-size-standard-bands
date: 2026-09-25
trigger-type: stakeholder-request
change-type: api-change
outcome: job-data-source-flexibility
status: in-progress
---

# Change Request: Replace the platform's own employer size bands with headcount-derived, standards-based bands

## Signal
See: `research/2026-09-25-adopt-ons-size-breakpoints.md`
Standards research: `research/2026-09-25-business-size-band-standards.md`
Reference doc written with this CR: `EMPLOYER_SIZE_STANDARDS.md`

## Outcome
`outcomes/job-data-source-flexibility.md` — the trusted-statistics criterion (added 2026-09-24)
asks for the platform's own figures to be cross-checkable against independent authorities. Its
employer size metadata is what stops that cross-check working for company size. No outcome
change needed. (Bucket A — maps to an existing outcome.)

## Change Type
`api-change` (a stored data-model attribute and its derivation) — internal. A later, separate
`ux-change` (Story 5 gains a size comparison) is part of the plan below, gated on the data.

## What is being changed, and why
Today `raw_postings.employer_size_band` holds one of four platform-invented labels — Startup
(<50), Small/Growth (50–500), Medium (500–5,000), Large (5,000+) — looked up per company from
`industries.COMPANY_SIZE_BAND` at ingestion. The boundaries at 500 and 5,000 match no published
standard, so nothing external can be compared against them. Story 5's size cross-check was
deliberately dropped for exactly that reason (`changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md`,
decision 10).

**PM direction (2026-09-25):** use ONS's breakpoints instead. Research
(`research/2026-09-25-business-size-band-standards.md`) refines that:
- ONS's lower three cut points (10 / 50 / 250) are the *international* standard (Eurostat, OECD,
  UK business statistics, US JOLTS). Its split of "large" at **2,500** is ONS-specific. Other
  publishers split the top end differently (US JOLTS 1,000 and 5,000; US SBA ~500; EU new
  "small mid-cap" under 750).
- What is measured also differs: persons employed (Eurostat), register employment (ONS),
  establishment employment (US), and — for our figures — usually a company's *worldwide*
  headcount, which none of those measure.
- So **any single publisher's bands as the platform's only bands would just move the mismatch
  elsewhere** the moment a second publisher is added.

## Approach (Option A confirmed by the PM 2026-09-25; Option B not taken)
**Option A — headcount as the source of truth; bands derived per publisher (CHOSEN).**
Store, per company, a headcount **range** with its **basis** (worldwide / national / unknown),
**source** and **as-of date** — most of this already exists in
`research/2026-09-19-original-35-size-bands.md`. Derive named bands from it when needed:
`ONS_VS_size_band` (five bands, for UK cross-checks), an international 10/50/250 class (the
platform's default label), and others (e.g. US JOLTS) when a publisher needs one. A range that
straddles a boundary yields **"ambiguous", never a guessed band**. This matches the
`{system, code, label}` dimension model already specified in
`backend/specs/trusted-statistics/api.md`.

**Option B — replace our four labels with ONS's five and stop there.** Simpler and quicker;
works for the UK cross-check; but hard-codes one publisher's scheme, discards the headcount
detail (so the 5,000+ vs 2,500–5,000 distinction is lost), and must be redone for any non-UK
publisher.

## Known facts that constrain the work
- **Nothing reads `employer_size_band` back today** — checked 2026-09-25: it is written by
  `raw_postings.py` and defined in `db.py`/`industries.py`; no story, chat tool, MCP tool, filter
  or admin page consumes it. (The `size_band` references in the new trusted-statistics specs are
  ONS's own dimension, not this field.) So a change is low-risk — this is the cheapest moment.
- **Stored rows carry the old labels** (no backfill was ever done for `raw_postings` fields
  populated at ingestion) — a one-off update from the company lookup is needed, or the new field
  starts empty for old rows and fills from the next ingestion.
- **Coverage gaps:** `lever` (the ATS company itself) has no figure; the 26 US/EU panel companies
  added 2026-09-23 were deliberately left untagged (`EMPLOYER_PANEL.md`); several existing
  figures conflict between sources.
- **Worldwide vs UK headcount:** for a UK cross-check the relevant size is the UK business's, not a
  multinational's global total. UK panel companies are mostly UK-headquartered so this matters
  mainly for multinationals (Stripe, Spotify, …). Whether ONS's register employment is UK-only is
  unconfirmed — ask ONS.
- **A comparison needs the UK-based roles only** (already the rule in the trusted-statistics spec).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/job-data-source-flexibility.md` | no-change |
| Design Foundations / IA / Visual Design | — | no-change |
| Experience Spec | `design/market-health/data-stories.md` — Story 5 | **update, gated** — add a size comparison next to the industry one once the data exists (Step 8); until then Story 5 stays as specified |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | update with the story change (Step 8); `SourceComparisonBars` already generic |
| Backend Spec | `backend/specs/market-health/api.md` — RawPosting `employer_size_band` + "Employer metadata tagging" | **update** (Step 3) |
| Backend Spec | `backend/specs/trusted-statistics/api.md` — §6 "Size-band cross-check is deliberately not built", Open Questions | **update** (Step 3) — becomes buildable |
| Docs | `EMPLOYER_PANEL.md` (size-band definitions), `DATA_SOURCES.md` §4 note, `backend/TRUSTED_STATISTICS.md` gotcha, `EMPLOYER_SIZE_STANDARDS.md` (new — written with this CR) | update |
| Backend Implementation | `backend/src/industries.py`, `raw_postings.py`, `db.py`, new derivation helper, backfill script, tests | update (Step 5) |
| Frontend Implementation | `frontend/src/` | update only with Step 8 |
| Plain-Language Overview | `OVERVIEW.md` | update when the size comparison ships (Step 9); no user-visible effect before |
| MCP Access Review | `ACCESS.md` | **not-applicable now** — no MCP tool exposes this field; revisit if `list_tracked_companies` ever returns it |
| Polite Scraping Review | — | not-applicable — no scraped source |
| Data Surface Review | — | **not-applicable** — an attribute of existing company metadata, not a new data category; no new table |

## PM Decisions (2026-09-25)
1. **Option A — headcount as the source of truth, bands derived per publisher.** ✅ Confirmed.
2. **Default size label = ONS's five bands** (1–9, 10–49, 50–249, 250–2,499, 2,500+), "to keep
   consistency". ✅ Decided by PM (recommendation had been the international four-class label). The
   international 10/50/250 class and other publishers' systems remain derivable from the same
   headcount when a publisher needs them; the platform-facing default is ONS's five. Consequence to
   record: our own display label now inherits ONS's UK-specific 2,500 split, and the platform's
   old 5,000+ "Large" distinction is derivable from headcount but no longer a label.
3. **Headcount research: assigned to me (Claude)** for the 26 US/EU panel companies and `lever`.
   **Scope note:** the 21 UK panel companies were tagged from a *user-supplied bucket*, not a
   headcount (e.g. "Medium 500–5,000" spans two ONS bands), so ONS's five bands cannot be derived
   for them either. They are the *most* relevant companies for a UK cross-check, so the research
   pass covers them too (48 companies in total). This extends the assignment by 21 companies;
   flagged so it is a visible choice, not silent scope growth.
4. **Headcount basis** (Open Decision 3 in the original CR, not answered explicitly): default to
   the recorded worldwide figure, **labelled as worldwide**, and record a UK figure only where one
   is readily published. UK-headquartered companies are treated as UK-dominated but still labelled
   with what the source actually measured.

## Execution Plan

- ✅ Step 0: PM decisions — see "PM Decisions" above (2026-09-25)
- ✅ Step 1: Standards research — `research/2026-09-25-business-size-band-standards.md`
- ✅ Step 2: Reference doc — `EMPLOYER_SIZE_STANDARDS.md`
- ✅ Step 3: `/new-backend-spec` update — `market-health/api.md` (field semantics, derivation, ambiguity rule) and `trusted-statistics/api.md` (size cross-check specified, Open Question closed). `/mcp-access-review` re-checked (expected: no change)
- ✅ Step 4 (research done 2026-09-25; two follow-ups remain that need a human): Research pass — headcount range, basis, source and date for the 26 US/EU companies, `lever`, **and the 21 UK panel companies** → `research/2026-09-25-panel-headcount-research.md`; confirm with ONS whether register employment is UK-only (**cannot be done by me — needs a human to email ONS**)
- ✅ Step 5 (implemented 2026-09-25; live database backfilled — see Decision Log): `/implement-backend` — headcount data, derivation helper, `db.py` column(s), `raw_postings.py`, backfill, tests (every tagged company derives a band or an explicit "ambiguous"; no company guessed)
- ✅ Step 6 (docs updated for the specified design; rewrite again when Step 5 ships): Update `EMPLOYER_PANEL.md`, `DATA_SOURCES.md`, `backend/TRUSTED_STATISTICS.md`, product `CLAUDE.md`
- [ ] Step 7: `/new-experience` — Story 5 size comparison (only after Step 5 data exists and `trusted-statistics` is implemented)
- [ ] Step 8: `/new-frontend-spec`, `/implement-frontend` for that story change
- [ ] Step 9: Update `OVERVIEW.md`

## Decision Log
- 2026-09-25: PM asked to use ONS breakpoints in place of ours, and to document ONS's standards,
  the reasons behind them, and whether they apply outside the UK.
- 2026-09-25: Research found ONS's 10/50/250 are the international core, its 2,500 split is
  ONS-specific, and the sources give no derivation of the cut points (a harmonisation
  convention, per the EU record). Therefore recommended storing headcount and deriving bands per
  publisher instead of adopting any single publisher's scheme.
- 2026-09-25: PM chose Option A, ONS's five bands as the default label, and assigned the headcount research to Claude. Status moved to `in-progress`. Steps 3, 4 and 6 (specs, research, docs) proceed; **Step 5 (implement-backend — including a backfill that rewrites stored `raw_postings` values) is deliberately held for an explicit PM go.**
- 2026-09-25: Steps 3, 4 and 6 done. **Research result:** 82 tracked companies → 9 in ONS 50–249, 46 in 250–2,499, 20 in 2,500+, 6 ambiguous, 1 not derivable (Lever); none under 50. 5 of 21 old UK buckets did not fit their headcount. All figures are worldwide/group headcounts gathered from search summaries — filings **not** opened; the High-confidence ones need a spot-check. Two things only a human can do: open Gymshark's/Faculty's Companies House accounts and Khan Academy's Form 990, and ask ONS whether register employment is UK-only and whether a subsidiary is sized as its group.
- 2026-09-25: **PM decision (superseding the request below):** for the ambiguous companies, "just choose one category which have more probabilities". Done: five entries (Gymshark, Faculty, Substack, Notion, Supabase) carry a recorded `band_choice = 250-2499` with reasoning and `confidence = low`; Khan Academy's 258–2,365 sits inside one band by the numbers so needed no choice. This overrides the "never guessed" default *for these five, by explicit PM decision, and visibly* — the choice, its reasoning and its low confidence are stored with the entry, and each should be verified from filings (Companies House accounts for Gymshark and Faculty).
- 2026-09-25: **Step 5 built and applied.** New `backend/src/employer_headcount.py` (headcount table for 81 companies + `UNKNOWN_HEADCOUNT` for Lever, `ons_size_band()`, `size_band_for()`); `industries.py` retired `COMPANY_SIZE_BAND` and re-exports the new function (so `raw_postings.insert_new_postings()` is unchanged); `backfill_employer_size_band.py`; `tests/test_employer_headcount.py` (14 tests — boundaries, entry validation, coverage of every tracked company, no company left ambiguous, only ONS codes emitted, backfill plan). Backfill applied to the live database: 9,729 rows / 73 companies in one transaction; verified afterwards (6,308 `2500+`, 3,248 `250-2499`, 173 `50-249`; no retired labels; no NULLs; `raw_response` untouched); second dry run = 0 changes.
- 2026-09-25: **A real bug the coverage test caught before it shipped:** the Rightmove entry was keyed `rightmove` but the tracked company key is `rightmovecareers`.
- 2026-09-25: **Deviations from the spec, and why:** (1) `as_of` is free text, not a date — sources date their figures inconsistently and a date type would be false precision (spec corrected); (2) the backfill also filled 8,642 previously-`NULL` rows, not only rows carrying an old label — the column had only ever been populated at ingestion going forward, and leaving old rows NULL would have made any size comparison silently under-count history (this goes slightly beyond "rewrite the old labels" as I first described it to the PM; disclosed here); (3) `band_choice` / `band_choice_reason` fields were added to implement the PM's choose-one decision without losing the reasoning.
- 2026-09-25: **Not deployed.** The Railway `job-sync`/`api` services still run the previous code (auto-deploy is off — `DEPLOYMENT.md`). Until they are redeployed, a newly ingested posting would carry a retired label; **re-run `python backfill_employer_size_band.py --apply` after deploying** (idempotent).
- 2026-09-25: (superseded) **New PM decision requested:** how to treat the 6 ambiguous companies (Gymshark, Faculty, Khan Academy, Substack, Notion, Supabase) — store `ambiguous` and have any comparison state how many roles are unplaced (recommended), or resolve by hand from filings.
- 2026-09-25: Opened as `triaged`, not `in-progress` — the approach is a PM decision (Open
  Decision 1) and no spec or implementation work has begun on it. Only documentation (Steps 1-2)
  was done with this CR.
- 2026-09-25: Research also found two facts that correct the ONS work already specified under
  `changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md` — the survey covers Great Britain and is
  weighted to the UK, and its smallest band is "2 to 9" in the methodology but "1 – 9" in the
  file. Those corrections are recorded against *that* change request's specs (its status is
  `in-progress`), not here.
