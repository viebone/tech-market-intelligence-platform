source: stakeholder-request
date: 2026-09-28

User: "lets do batch 4" — continuing `changes/2026-09-23-us-eu-employer-panel-expansion.md`
straight after batch 3's production verification.

## Batch 4 selection

All 45 remaining US candidates were probed live first (batch 3 had already cleared the last
non-giant EU/UK companies). Real counts totalled ~4,321 postings across all 45 — far too large
for one gradual batch, and out of proportion with batches 1–3 (1,130 / 1,284 / 1,571). Split by
size, same "watch anything large individually" discipline this panel already applies to
300+-role giants:

- **Batch 4 (this one): 27 companies under 100 open roles each, 1,024 postings.**
- **Held for batch 5: 18 companies at 100–280 roles each** (Oscar Health, Samsara, Brex, Roblox,
  Block, Scale AI, Flexport, Lyft, Riot Games, Epic Games, Redwood Materials, Ripple, Glean,
  Planet Labs, Instacart, Nuro, Saronic, Sierra) — none is a 300+-role giant, but several are
  close enough (Oscar Health 277, Brex 259, Roblox 257) that adding all 18 alongside the giants
  in one drop would be exactly the "one big drop" this panel's own constraints rule out.

Every one of the 27 re-probed live and content-checked (company name/context appears in real job
titles) — no false positives, no wrong platform/token this time.

## New industry tags and their crosswalk decisions

Ten new tags, decided in `trusted_stats/crosswalks.py` (version `2026-09-28.2`):
- **DevOps Software** (PagerDuty), **Observability Software** (New Relic), **Cloud Software**
  (Dropbox), **Edge Cloud** (Fastly), **Consumer Internet** (Nextdoor, Quora), **Media** (Vox
  Media, BuzzFeed, Medium), **Healthtech AI** (Abridge), **Nonprofit/Software** (Mozilla) → all
  J. Each is a pure software product/platform; Media is placed on SIC section J's own actual
  structure (its divisions include publishing, broadcasting and motion-picture activities, not
  by analogy), and Nonprofit/Software is classified by its underlying activity (software) rather
  than its legal/tax structure, the same reasoning already used for "Nonprofit/EdTech" → P.
- **Restaurant** (Sweetgreen) → **I** (Accommodation and food service activities) — a genuinely
  new section for this crosswalk. Unlike "Restaurant Tech" (a software vendor, already J),
  Sweetgreen is an unambiguous restaurant operator — the cleanest single-company fit for a new
  section this crosswalk has needed, no real mixing to weigh.
- **Digital Health** (Ro) → None — mixes a telehealth service with pharmacy/medication
  logistics, same reasoning as the existing "Healthtech" tag.
