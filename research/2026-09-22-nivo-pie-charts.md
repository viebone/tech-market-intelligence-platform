---
source: user-feedback
date: 2026-09-22
---

User, after yesterday's Story 1 Nivo integration: "ok can you apply this new chart library to
the Data Stories."

Evaluated all 4 stories honestly rather than forcing Nivo everywhere — the earlier instruction
("apply only those that make sense") still holds. Real distinct-visual-form usage checked
per story:
- Story 1: already upgraded yesterday (skill demand, year-on-year). Pay transparency remained
  a plain `Meter` — checked whether it's a genuine 2-category partition (disclosed vs.
  undisclosed, summing to 100% of postings) rather than a coverage percentage — it is.
- Story 2: `Meter` x1 + `RankedBarList` x2 + `WorldRiskMap` x1 = 3 distinct forms already, not
  under-composed the way Story 1 was. But the "contraction vs. expansion" `Meter` is the same
  genuine 2-category partition shape as Story 1's pay block.
- Story 3: `RankedBarList` x3 + `Meter` x1 — closest to Story 1's original repetition problem,
  but its `Meter` ("X of Y tracked roles have salary data reported") is a coverage/completion
  percentage, not a 2-way partition — forcing a donut here would misrepresent the number.
  Combining its demand/pay rankings into one chart was considered and rejected: the two series
  are on wildly different scales (vacancy counts vs. salary figures), and a shared-axis grouped
  bar would visually mislead. Left untouched.
- Story 4: `RankedBarList` x2 + `Meter` x1 — its "scale" `Meter` (outside vs. inside the 3
  tracked categories) is the same genuine 2-category partition shape again.

Real, consistent pattern found across 3 stories (Story 1's pay transparency, Story 2's
contraction-vs-expansion, Story 4's scale) — all `Meter`-only blocks that are actually 2-way
partitions of a meaningful whole population, not coverage percentages. Built one shared
component (`SharePieChart`) rather than 3 bespoke ones, applied to exactly those 3, left
Story 3's genuinely different `Meter` usage alone.
