source: stakeholder-request
date: 2026-08-05

While challenging the pipeline's dedup guarantees (see
research/2026-08-05-cross-run-daily-budget-gap.md's sibling investigation), the user
raised a separate concern: Adzuna's license was already confirmed retired/unusable
(changes/2026-07-28-multi-source-job-data-ingestion.md, 2026-08-03 update), and continuing
to store/serve their historical data risks a licensing problem even though it's no longer
being actively fetched. User's decision, verbatim intent: "I just have a few days of adzuna
and it would be enough to get a problem for using that data, so lets stick to 100% [legitimately
usable] data. Just make sure the db doesn't suffer."

Explicitly acknowledged trade-off before proceeding: this removes the platform's only
pre-2026-08-03 historical data, meaning the trend chart's "Past 5 Years"/"All Time" views
will show almost no history immediately after (real history restarts from the
Greenhouse/Lever/Ashby migration). User chose to proceed anyway, prioritizing licensing
safety over historical depth.
