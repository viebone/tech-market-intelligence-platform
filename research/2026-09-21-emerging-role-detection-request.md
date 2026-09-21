---
source: user-feedback
date: 2026-09-21
---

User (verbatim, this session, immediately after the specialization-widening + Job Function
revision shipped): "6 days is fine, but I am surprised you didn't come with a better breakdown
for designer: product design; user experience design; content design or product manager:
product owner; delivery manager... etc ... plus what would happen when new roles emerge? i like
your analysis, so I would like to run that analysis every month and come with emerging roles
once we start detecting them appearing often. maybe multiple change request in one so good to
document this ideas"

Checked both specific critiques against real data before responding (not just re-argued the
existing design):
- Designer: pulled real raw titles, not just specialization values — found the current dataset
  (only 174 classified rows) is genuinely dominated by Product Designer variants; "Content
  Design" and "UX Writer" already exist as two separate real specialization values in
  production (the LLM had already organically split them despite the spec bundling them as one
  slash-value) — the spec was undercounting real granularity that already existed, not missing
  it entirely.
- "Delivery Manager": real query found all 5 instances landing `role_category = "other"`, none
  under Product Manager — validated that this is correctly not a Product Manager specialization
  in this platform's real data/LLM judgment, and (thanks to the same-day Job Function work) now
  has a real home for the first time (`Operations & Business Ops`).

Two distinct ideas in this one message, split into two change requests per the user's own
request: (1) the Content-Designer/UX-Writer split + Delivery-Manager-to-Job-Function mapping,
folded into the still-unexecuted `changes/2026-09-21-taxonomy-revision-specialization-and-job-
function.md` before its backlog runs; (2) a new, standing "run this analysis monthly" operator
capability — `changes/2026-09-21-emerging-role-detection.md`.
