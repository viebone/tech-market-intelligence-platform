source: internal
date: 2026-08-05

While designing a bigger "sample instead of exhaustive" redesign for classification
(prompted by Gemini's confirmed 20 requests/day/project/model free-tier ceiling), we pulled
real production numbers to size a sample. That surfaced two things:

1. Steady-state new-posting volume is tiny: ~30-46 new postings/day across all 35 tracked
   companies (confirmed via `ingestion_runs.total_inserted` over the last 5 days). The much
   larger `total_fetched` figures (~4,500+/day) are misleading on their own — none of
   Greenhouse/Lever/Ashby support incremental fetch, so the entire board is re-downloaded
   every run; dedup (raw_postings.id as PRIMARY KEY, checked via existing_ids() before
   insert) correctly discards the ~99% that's already stored. Proof: openai's ~736-posting
   Ashby board is fetched in full every run, yet only 749 rows exist for openai, all-time.
2. The large `llm_classified` counts seen recently (520-1,491/day) are mostly the pipeline
   draining a one-time backlog (1,020 postings currently unclassified) from the 2026-08-03
   migration burst, not steady-state daily load.

Given this, the user decided the full rich-sampling redesign (classification + salary +
skills together, per posting, ~360/day ceiling calculated from the quota) isn't justified
yet — deferred until/unless actually needed (e.g. the company list grows a lot). Instead,
two narrower things, confirmed with the user directly:

**A real, found-not-hypothetical gap**: `classification.py`'s `MAX_BATCHES_PER_RUN = 12`
(added 2026-08-04) resets per run invocation, not per calendar day. Manual "Run now"
testing this week repeatedly triggered more than one run per day — each run independently
gets its own fresh 12-batch allowance, so two runs in one day could together attempt up to
24 batches, exceeding the real 20/day ceiling. This has been narrowly avoided by luck this
week, not by design — a real latent cost/security gap.

User's ask, verbatim intent: "a customisable limit just for security" (fix the above, with
every number configurable — "so in the future we can increase it") "and making sure we
only store and only classify new job posts" (confirm this already-true guarantee is
explicit, not just implicit).
