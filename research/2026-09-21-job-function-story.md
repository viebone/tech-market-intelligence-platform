---
source: user-feedback
date: 2026-09-21
---

User: "ok but what about the job functions that we have created, we need to show them in the
overview, and we need a data story for it, we also need to track them in the admin right?"

This is the deferred `/data-surface-review` from `changes/2026-09-21-emerging-role-detection.md`
finally landing — that deferral's own stated precondition ("no real reclassified data exists
yet") is no longer true: today's backlog run already produced 2,013 real `job_function`-
classified rows. Three parts, triaged separately:

1. **"Show them in the overview"** — the Welcome ("About this platform")'s shortcut list reads
   the Story Catalogue live; adding a new catalogue entry (below) makes it appear there with no
   separate Welcome code change, same mechanism every prior story used.
2. **"A data story for it"** — a new Story 4, same weight as Story 3's own addition
   (`changes/2026-09-18-market-benchmark-story.md`): `ux-change` + `api-change`, not
   `new-feature`, since the Story Catalogue mechanism already exists.
3. **"Track them in the admin"** — already partially true (Taxonomy Health page,
   `/admin/` overview's Job Function dimension card, both from earlier today) — checked whether
   "track" implies something more (a drill-down filter on the Postings admin view) as part of
   this same pass.

Real, current honesty constraint this story must handle, not hide: the reclassification backlog
is still ~4 days from completing (`changes/2026-09-21-fold-reprocessing-into-ingest.md`) — a
real share of `other`-classified postings genuinely have `job_function IS NULL` right now,
because they haven't been reprocessed onto the new taxonomy version yet. This is the exact "real
lag must be stated plainly, never faked as fresh" case Rule 14 describes, live in production
today, not a hypothetical.
