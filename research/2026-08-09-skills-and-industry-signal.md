source: stakeholder-request
date: 2026-08-09

User laid out a full 10-category product vision (market health, opportunities,
positioning, skills demand, competition, salary, company risk, job evaluation, personal
search tracking, strategic recommendations) — see conversation for the complete list of
example questions per category. Explicit examples driving this signal:

> "we need classification to read through the job description an be able to summarise
> how the job post was structured, what are the skills required, the responsibilities of
> the job, the level of studies required, the languages required, etc etc... we need a
> standard structure with a separated column to capture information which is not part of
> the standard. but if the user ask, should I learn to code as a ux designer? the system
> should be able to look at the ux design jobs, skills required, must have, nice to have
> and draw a recommendation"

> "lets extend points 1 to 6 [...] but we need to set the foundation so that the product
> can grow and ask questions that may need other type of data, other sources, etc..
> for example layoff data, which is in our core idea, but we haven't touch it yet"

After mapping all 10 categories against what currently exists and what's structurally
possible (see conversation), agreed scope for this change:

1. **Skills/requirements extraction** — per-posting LLM extraction of skills (must-have vs
   nice-to-have), responsibilities, education level, language requirements, plus an
   explicit freeform catch-all field for anything not fitting the standard taxonomy.
2. **Industry tagging** — static, curated company→industry lookup (35 companies), zero
   LLM cost, same maintenance discipline as the existing curated `COMPANIES` lists.
3. **New query tool(s)** so the chat can aggregate and answer using these new dimensions,
   including synthesis-style questions ("should I learn to code as a UX designer?").

Explicitly excluded from this change, discussed and agreed:
- Company-level hiring-velocity/risk questions — outcome already excludes
  "company-specific research"; a separate scope decision, not part of this change.
- Applicant-count/competition questions — structurally impossible, no source API exposes
  this data.
- Job Application Tracker / CV matching / personalized search-funnel questions — an
  entirely different product surface needing user accounts and personal data this
  codebase has never had any form of. Needs its own future `/new-outcome`.
- Layoff Signal — already a named-but-unbuilt IA concept ("Future tasks" in Content
  Taxonomy, same as Compensation Signal was before this week). Not built now; used as the
  reasoning for keeping this change's architecture disciplined (dedicated per-signal-type
  data model/adapter/query tool, not a shared generic table) so Layoff Signal can be added
  properly later without unwinding anything done now.

Cost re-framing established during discussion: this is the same *class* of problem as the
earlier-deferred Greenhouse-salary/skills idea (per-posting, not per-title, extraction —
no title-cache shortcut since descriptions are unique even when titles match). But real
production data confirmed over the past week shows steady-state new-posting volume is only
~43-115/day, not thousands as originally assumed when this was first deferred — so giving
every new posting the full rich-extraction treatment daily is likely realistic within the
existing Gemini free-tier budget. The real cost is a one-time backlog (~4,700+ postings
predating this feature) needing the same oldest-first/daily-budget-clamp pattern already
proven for classification (changes/2026-08-04-classification-llm-call-reduction.md,
changes/2026-08-05-cross-run-daily-budget-gap.md).
