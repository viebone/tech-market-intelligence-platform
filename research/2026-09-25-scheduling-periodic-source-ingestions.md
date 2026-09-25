source: stakeholder-request
date: 2026-09-25

Follow-up to `changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md` (the ONS ingestion exists but nothing runs it).

PM, in order:

1. "how often the ons gets released?"

2. "ok so lets do two days after day release in case there are issues in their side, but we need a cron for this so that we don't for get. or can we use the same cron, ingestion run triggers the other ingestions when needed? what would better approach?"

3. "option A with it jobs included. make sure is well documented and that one failing doesn't bother the others"

(3 answered: "Option A: `job-sync` runs it first, isolated … Option B: a new Railway service … Do you want IT Jobs Watch included in the same step?")

---
Facts established while answering (2026-09-25, read from the systems, not assumed):
- ONS Vacancy Survey release history (129 releases, Nov 2015 – Sep 2026): monthly, mostly Tuesdays, gaps of 28 days (73 of 128) or
  35 days (32); occasional 30-33 day gaps and two 63-day gaps. Next release listed on the ONS page: 20 Oct 2026.
- Only `job-sync` (daily 06:00 UTC) and `employment-events` (Mondays 07:00 UTC — deployed, last insert 21 Sep 07:03; `DEPLOYMENT.md` wrongly
  says "not yet deployed") are scheduled. The IT Jobs Watch scrape has **no schedule**: last run 18 Sep, due weekly, so overdue since 25 Sep.
- Railway `job-sync` has `DATABASE_URL` and both Gemini keys but **neither `SCRAPER_CONTACT` nor `STATISTICS_CONTACT`**.
