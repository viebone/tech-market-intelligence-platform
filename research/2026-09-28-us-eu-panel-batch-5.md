source: stakeholder-request
date: 2026-09-28

User: "batch 5" — continuing `changes/2026-09-23-us-eu-employer-panel-expansion.md` straight
after batch 4's production verification.

## Backlog check before sizing

Classification backlog stood at 759 (not 0, for the first time all day) — today's daily LLM
budget had already been used by batches 3 and 4's own production runs, and self-heals on the
next run. Not a blocker (postings are never lost, just queued), but a real signal that today's
pipeline had already done a lot of work — reason enough to keep batch 5 modest rather than add
all 18 held candidates (~3,297 postings) at once.

## Batch 5 selection

All 18 candidates held from batch 4 (100–280 roles each) were re-probed live, not trusted from
the multi-day-old table. Real counts: nuro 106, instacart 116, planetlabs 120, ripple 122,
gleanwork 131, redwoodmaterials 140, epicgames 154, riotgames 165, lyft 175, flexport 201, sierra
202, scaleai 203, saronic 206, block 214, samsara 249, roblox 257, brex 259, oscar 277 — total
3,297.

Split at ~180 roles: **batch 5 (this one) takes the smaller 9** (nuro through lyft, 1,229
postings, comparable scale to batch 4). **The larger 9** (flexport through oscar, ~2,068
postings) are held for batch 6 — same "watch anything large individually" discipline this panel
already applies to 300+-role giants, now applied within this 100–280-role tier too.

Every one of the 9 content-checked (company name/context matches real job titles) — no false
positives.

## New industry tags and their crosswalk decisions

Three new tags, decided in `trusted_stats/crosswalks.py` (version `2026-09-28.3`):
- **Grocery Tech** (Instacart) → None — mixes a software platform with the actual grocery
  delivery/logistics operation, same reasoning as the existing "Food Delivery/Marketplace" tag.
- **Earth Observation** (Planet Labs) → None — mixes operating a physical satellite fleet (real
  space-hardware infrastructure) with selling imagery/data analytics software, same "hardware
  operation, not just software" reasoning as "Semiconductors/AI".
- **Climate/Materials** (Redwood Materials) → None — battery-materials recycling and processing,
  real industrial/manufacturing activity, not software.
