source: stakeholder-request
date: 2026-09-11

See also: `changes/2026-09-11-employment-events-independent-scope.md` (built the independent
Employment Risk story, but kept `matched_company` and the tracked-company-scoped chart strip
alive alongside it) and `changes/2026-09-11-employment-event-ingestion.md` (parent change,
introduced `matched_company`/`company_aliases.py` in the first place).

Raw trigger — a firm, repeated correction after the independent-scope change shipped:

> "again, let's be clear, I want layoff to be independent from job post, totally different, we
> don't look to match the companies that we are getting jobs, is that clear? please update
> this and previous one to follow this comment"

This goes further than the previous change did. That change kept the chart strip
tracked-company-scoped (reasoning: "our own hiring vs. our own contraction is still a
coherent picture") and only added a *second*, independent surface alongside it. The user is
now saying: no — there should be **no company-matching concept anywhere** in the employment-
events pipeline, not even as one surface among several. Employment events are a wholly
separate dataset from job postings, full stop.

This means undoing, not just extending, part of what shipped today:
- `matched_company` (`employment_events.matched_company`, `company_aliases.py`'s
  `resolve_company()`) — the entire matching mechanism — removed.
- The trend chart's "Employment events strip" (`EmploymentEventsStrip`, `EventMarkerDetail`,
  `GET /api/market-health/employment-events`) — built entirely around showing *tracked-
  company-matched* events on the *tracked-company* hiring chart — has no remaining reason to
  exist once matching is gone the display concept was never independent to begin with, and the
  Employment Risk story is already the correct, fully-independent surface. Removed, not kept
  in a broken half-state.
- `query_employment_events_data`'s `hiring_trend` field (cross-references a matched company's
  `raw_postings` history) — removed; the tool answers about events only.
- UK Companies House's `CANDIDATE_COMPANIES` design (`backend/src/employment_events/companies_house.py`)
  — built by construction as "find the UK entity for each of our 35 tracked companies," which
  is itself a form of company-matching this direction rules out. Needs a different mechanism
  that doesn't start from the tracked-company list at all.
