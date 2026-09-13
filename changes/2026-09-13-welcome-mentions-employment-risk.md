---
id: welcome-mentions-employment-risk
date: 2026-09-13
trigger-type: user-feedback
change-type: content-change, bug-fix
outcome: understand-market-health-before-searching
status: complete
---

# Change Request: "About this platform" mentions employment risk and its sources

## Signal
See: `research/2026-09-13-welcome-mentions-employment-risk.md`

## Outcome
See: `outcomes/understand-market-health-before-searching.md` — "see employment risk alongside
demand" only works if the platform's own front door doesn't tell the user it isn't there.

## Change Type
`content-change` (Hero/closing copy) + `bug-fix` — the current closing sentence ("We don't
cover layoffs...") is factually false since Story 2 shipped 2026-09-11, and self-contradicts
the shortcut card immediately above it, which the same welcome already renders for that story.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Experience Spec | `design/market-health/experience.md` | update — Opening Welcome Hero + Call to action content |
| Frontend Implementation | `frontend/src/features/market-health/WelcomeMessage.tsx` | update |

## Execution Plan

- [x] Step 1: Capture signal — `research/2026-09-13-welcome-mentions-employment-risk.md`
- [x] Step 2: Update `design/market-health/experience.md` — Opening Welcome content (manual edit)
- [x] Step 3: Update `WelcomeMessage.tsx` to match
- [x] Step 4: Verify — `npm run build` clean, confirm the self-contradiction is gone

## Decision Log
- 2026-09-13: "First hand sources" rendered as "official registries" in the actual copy — the
  accurate, honest framing for what these sources really are (Eurofound ERM, US state WARN,
  UK Companies House, SEC EDGAR — all official/statutory), consistent with this product's
  existing vocabulary (`confidence: "confirmed"` already means "a legal/statutory filing or an
  official register" elsewhere in this spec chain).
