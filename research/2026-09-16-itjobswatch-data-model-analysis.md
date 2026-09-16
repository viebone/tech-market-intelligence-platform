source: stakeholder-request
date: 2026-09-16

Related: `research/2026-09-16-itjobswatch-scraping-permission.md` (the permission grant itself —
this file is a separate, follow-on signal: a detailed analysis of what IT Jobs Watch actually
publishes and how it should be modeled, received after that permission was already in hand).

## What this is

A third-party analysis (pasted verbatim by the operator) of IT Jobs Watch's actual published
data — what's on the site, why it's valuable, and a proposed data model. Full text preserved
below exactly as received, since the specific field names, examples, and reasoning are directly
load-bearing on the backend spec.

## The core argument

Don't treat IT Jobs Watch as "another job source" alongside Greenhouse/Lever/Ashby. Treat it as
a **market benchmark dataset** — a category of its own, parallel to (not a member of) the
existing job-posting sources. The proposed architecture:

```
                    YOUR PLATFORM

Individual vacancies                 Market datasets
─────────────────────                 ───────────────
Greenhouse                            IT Jobs Watch
Lever                                 ONS
Ashby                                 layoffs data
Company career sites                  other datasets
        │                                  │
        ▼                                  ▼
  Job-level database              Market observations
        │                                  │
        └──────────────┬───────────────────┘
                       ▼
                Analytics layer
                       │
                       ▼
                     LLM
```

This platform's own scraped/ingested postings tell you what's happening right now, at the
individual-job level, since ~5,000 jobs collected so far. IT Jobs Watch (and potentially future
sources like ONS) tell you the wider market's *aggregate* shape, with real history back to 2004
per its own claim (though how much of that is actually reachable by scraping today's rendered
pages, vs. requiring separate historical-view URLs, needs confirming empirically, not assumed).

## Proposed data model (verbatim structure from the analysis)

**`MarketObservation`** — one row per (entity, employment type, location, period):
- `date`, `period_start`, `period_end`
- `entity_type`: role | skill | technology | capability
- `entity_name`
- `employment_type`: permanent | contract
- `location`
- `rank`, `rank_yoy_change`
- `vacancy_count`, `vacancy_share`
- `salary_sample_size`, `salary_p10`, `salary_p25`, `salary_median`, `salary_p75`, `salary_p90`,
  `salary_yoy_change`
- `live_jobs`

**`SkillAssociation`** — one row per (role, skill, period), the market-derived role→skill graph
with weights:
- `date`, `role`, `skill`
- `job_count`, `percentage`, `rank`

## What IT Jobs Watch actually publishes (per this analysis)

Headline market statistics, skills/technology trends, job-role trends, salary benchmarking,
contractor-rate benchmarking, and skill-set analysis — recalculated daily, permanent and
contract markets kept as separate views. Concrete example given: its Product Owner page reports
355 permanent jobs in a six-month sample, 210 quoting salaries, median £70,000, with 10th/25th/
75th/90th percentiles, and year-over-year comparison against the same period in 2025 and 2024.

Four dimensions singled out as most valuable, roughly in this order:
1. **Historical role/skill demand** — vacancy count, market share (% of all vacancies), demand
   rank, rank movement year-over-year, historical trend. Enables statements like "vacancies rose
   in absolute terms but market share fell from 0.39% to 0.31%" — richer than a bare count.
2. **Salary intelligence** — full percentile spread (p10/p25/median/p75/p90), sample size, and
   year-over-year change, not just a single median. Calculated from salaries actually quoted in
   ads (excludes bonuses/benefits, per the source's own methodology).
3. **Geography** — UK region breakdowns (London, South East, North West, Scotland, Wales, Work
   from Home, etc.), each with its own vacancy count, salary, YoY change, rank change, live-job
   count.
4. **Skills intelligence** — per-role associated skills with frequency/weight (e.g. Product
   Owner: Roadmaps 49.3%, Agile 45.9%, User Stories 32.1%, AI 16.3%, ...), i.e. a market-derived
   role→skill graph with weighted edges. Flagged as ties directly into this platform's own
   existing skill-extraction work from job descriptions.

Two more dimensions noted but lower priority for a first cut:
- **Role taxonomy variants** — IT Jobs Watch distinguishes e.g. Product Owner / Product
  Ownership / Technical Product Owner / Digital Product Owner. Flagged as a possible future way
  to validate/enrich this platform's own taxonomy rather than relying solely on LLM
  classification — explicitly a future opportunity, not something to build now.
- **Permanent vs. contract as separate markets**, contract using day-rate rather than salary.

## Explicit caution repeated from the source analysis

> "The site says its published statistics and insights are released under a Creative Commons
> licence, but I'd verify the exact licensing terms and permitted automated access/API or
> scraping mechanism separately. 'Open data' doesn't automatically mean unrestricted crawling of
> the website itself."

This is a second, independent flag on top of the direct permission email — reinforcing that the
actual binding authority for how this is scraped is the email's specific conditions (robots.txt,
pacing, identification, caching, attribution), not "it's CC-licensed" as a blanket justification,
and that the specific CC variant still needs confirming against the site's own licence statement
before anything is stored or republished.

## Priority given for a first implementation cut

Historical role demand, salary distributions, geography, and role↔skill co-occurrence — in that
order. Contractor-rate benchmarking, live-job counts, and role-taxonomy-variant reconciliation
are real but lower priority for a first pass.
