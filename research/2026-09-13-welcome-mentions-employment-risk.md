source: user-feedback
date: 2026-09-13

Raw trigger:

> "on the about this company, first opening story, we need to include that we also show layoff
> data and that we track us, europe from first hand sources"

## Real bug found while investigating

The "About this platform" welcome's Call to action closing sentence currently reads: "We don't
cover layoffs, company reviews, or application tracking." This is no longer true — Story 2
("Employment risk across the market") has been live since 2026-09-11, and because the
Call-to-action shortcut cards are generated generically from the story catalogue
(`design/market-health/data-stories.md`'s "Relationship to the Welcome" — adding a catalogue
entry changes the Welcome automatically, no copy change needed), the shortcut card for
"What does layoff and hiring activity look like across the market right now?" is **already
rendering directly above** the sentence claiming layoffs aren't covered — a live,
self-contradicting welcome message. This is a `bug-fix` as much as a `content-change`: the
Hero and closing copy are fixed, hand-written text that a new catalogue entry (Story 2) never
updates automatically, unlike the shortcut cards themselves.

## What the fix needs to say

- Hero subhead: currently only mentions job openings/skills/pay. Needs to also name
  layoffs/restructuring/hiring activity as a tracked signal, parallel to how it already names
  "job openings, skills, and pay."
- Geographic + source-quality claim: "US, Europe" and "first hand sources" — the real sources
  are official/statutory registries (Eurofound European Restructuring Monitor for EU+Norway,
  US state WARN notices via WARN Firehose, UK Companies House, SEC EDGAR 8-K filings) — not
  secondhand aggregators (this product's own research explicitly deprioritized layoffs.fyi for
  exactly that reason, `research/2026-09-11-employment-event-data-sources.md`). "Official
  registries" is the accurate framing for "first hand."
- Closing sentence: remove "layoffs" from the "don't cover" list (false), keep "company
  reviews" and "application tracking" (still genuinely out of scope).
