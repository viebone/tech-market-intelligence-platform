source: stakeholder-request
date: 2026-09-18

Raw plan as pasted by the user, proposing a deliberately-designed, stratified UK employer panel
(~36 employers to start, targeting ~500 long-term across a size/sector/geography/occupation
sampling frame) to replace ad-hoc company addition, plus new ATS source adapters
(Teamtailor, Workable, SmartRecruiters, Workday, SuccessFactors) and new per-observation
provenance fields (employer_size_band, employer_sector, employer_region, source_type,
ats_platform, collection_method, first_seen_at, last_seen_at, published_at, closed_at):

---

Yes. I'd build this as a deliberately designed employer panel, rather than simply adding every
company we can find.

For the first version, I'd target roughly 40–50 employers, selected to give you variation
across employer size, industry, geography and type of work. Then we can expand toward 200–500
once the collection pipeline is reliable.

One important distinction: a careers page being publicly accessible for free does not
automatically mean unrestricted automated crawling is permitted. Before activating each
crawler, I would have your system check robots.txt, terms, rate limits and whether there is an
underlying public ATS/feed/API. Where Greenhouse/Ashby/Lever is already available to you, use
that rather than scraping HTML.

[... full pasted plan, including the 36-employer table, the "architecture I'd use" section,
"the next adapters I'd build," the new database fields, and the closing recommendation to
implement the 36-employer panel + Teamtailor/Workable adapters and measure for 30 days before
expanding further — see the conversation transcript for the complete verbatim text.]

---

## Assistant's evaluation (this session, same day)

Agreed with the core direction (source-adapter architecture, bias correction, provenance
fields) but pushed back on scope and unverified claims:
- This is 6+ separate change requests, not one step — sequencing matters (Rule 8).
- None of the 36 companies' claimed ATS platforms are verified — same discipline that just
  caught real problems with the Indeed and Reed research needs to apply here too, per-company,
  before anything is added to a real `COMPANIES` list.
- "Check robots.txt, terms, rate limits" conflates a mechanical check (already automated by
  `PoliteScraper`) with a human/AI judgment call (ToS review) that can't be automated.
- Custom careers-page and public-sector adapters are each their own IT-Jobs-Watch-weight
  effort, not a generic reusable mechanism — deferred.
- `closed_at`/posting-lifecycle tracking is a real new capability (ingestion is insert-only
  today), not a free column.
- Recommended first concrete step: the `employer_size_band`/`employer_sector`/`employer_region`
  schema addition (no new adapters, backfillable today), then one new ATS adapter (not five),
  verified against real companies before scaling.

User's decision: store the panel as a tracked backlog to work through one entry at a time,
rather than building anything yet. See `EMPLOYER_PANEL.md` (product root).
