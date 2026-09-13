---
id: welcome-employment-risk-proof
date: 2026-09-13
trigger-type: user-feedback
change-type: content-change, api-change
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: Real numbers backing the Welcome's employment-risk claim

## Signal
See: `research/2026-09-13-welcome-employment-risk-proof.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — a claim without a number is
weaker than one with; the Proof section exists specifically so the Hero's claims are backed by
live data, not just told.

## Change Type
`content-change` (a new stat line in the Welcome) + `api-change` (the welcome inventory needs
new aggregates over `employment_events`, which it never queried before).

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Experience Spec | `design/market-health/experience.md` | update — Opening Welcome Structure/Content/Data contract gain an employment-risk proof line |
| Backend Spec | `backend/specs/market-health/api.md` | no-change — `build_welcome()`'s response shape isn't separately enumerated there (same as the earlier World risk map finding); `data-stories.md`/this spec are the real contract |
| Backend Implementation | `backend/src/market_stories.py` | update — `build_welcome()` gains employment-events aggregates |
| Frontend Implementation | `frontend/src/features/market-health/WelcomeMessage.tsx` | update |

## Execution Plan

- [x] Step 1: Capture signal — `research/2026-09-13-welcome-employment-risk-proof.md`
- [x] Step 2: Update `design/market-health/experience.md` (manual edit)
- [x] Step 3: Implement backend — `build_welcome()` aggregates
- [x] Step 4: Implement frontend — new proof line in `WelcomeMessage.tsx`
- [x] Step 5: Verify — real API response, `npm run build` clean

## Decision Log
- 2026-09-13: Kept as its own visually distinct line, not merged into the existing job-openings
  stat row — mixing "postings" and "events" counts in one undifferentiated row risks exactly
  the kind of ambiguity `data-legibility` exists to catch (what is this number counting?).
  Also keeps the Welcome's single Hero Figure rule intact (job openings stays the one number
  this view leads with) — employment risk gets a supporting line, not a second Hero Figure.
- 2026-09-13: Event count excludes `superseded_by IS NOT NULL` rows (a corrected/retracted
  record) — same "don't count what's been superseded" rule the Employment Risk story itself
  already follows.
