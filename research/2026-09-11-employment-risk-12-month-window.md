source: stakeholder-request
date: 2026-09-11

See also: `changes/2026-09-11-employment-events-independent-scope.md` (Story 2, shipped
earlier today with a 90-day trailing window).

Raw trigger: after the first two real UK Companies House insolvency events were ingested
(case dates ~180 days and ~440 days old, reflecting when the underlying insolvency actually
started, not when the streaming API happened to push an update), both fell outside Story 2's
90-day window and didn't appear in "Employment risk across the market." User chose to widen
the window to 12 months rather than leave it at 90 days, given a decision between the two.
