source: market-signal
date: 2026-09-24

There's a really clean UK path. Let me give you the two most useful finds.

The single best one is D.W.P.'s "Find a Job" service, that's the government's own job board, and its live vacancies are exposed through a free platform called L.M.I. for All. It's an official government data source, continuously updated, and built specifically for developers to use, so it's legitimately free and you're not fighting anyone's terms. That gives you real individual postings across every sector and company size, not just tech, which is exactly the variety you're missing.

The second is the Office for National Statistics. They publish vacancy data by industry, and crucially, by size of business. That won't give you individual postings, but it's perfect as a benchmark layer, a way to sanity-check whether your scraped sample actually reflects the real UK market.

So my honest suggestion, make L.M.I. for All slash Find a Job your next connector. It's the fastest legal way to get sector and company-size variety in the UK. Want me to dig into how that A.P.I. actually works?The API: LMI for All (api.lmiforall.org.uk). It's a free UK government-funded labour market API. It has two useful parts:

A vacancy search that returns live postings from DWP's Find a Job, the government job board. This is what gives you jobs from all sectors and company sizes.
Statistics by occupation (SOC codes), such as pay, hours and employment projections. You'd use this as a benchmark, not as postings.

One correction: I told you earlier that the Find a Job feed is under the Open Government Licence. That claim came from a third-party GitHub note, not from DWP itself. Confirming the licence should be step one, before any building.

---
Related: `research/2026-09-24-lmi-for-all-vacancy-feed-verification.md` (verification of the claims above, done at triage).
Related prior context: `EMPLOYER_PANEL.md` (existing sector/size variety work), `DATA_SOURCES.md` §3a ("UK ONS HR1" descoped precedent).
