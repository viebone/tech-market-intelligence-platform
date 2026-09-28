source: stakeholder-request
date: 2026-09-28

User: "yes lets continue in order, lets do batch 3" — continuing
`changes/2026-09-23-us-eu-employer-panel-expansion.md`. Backlog/budget checked first: classification
backlog 0, requirements backlog 4,677 draining normally (batch 16 submitted this morning's real
06:05 UTC cron run), $10/month cap — healthy, room to continue.

## Batch 3 selection

14 companies, 1,571 real live-verified postings — every remaining **non-giant** EU/UK candidate
from the held list: Celonis (DE, 253), Flipdish (IE, 16), Adyen (NL, 208), Tide (UK, 88),
Stability AI (UK, 6), PolyAI (UK, 3), TrueLayer (UK, 3), Wolt (FI, 210), Graphcore (UK, 180),
Pigment (FR, 136), Doctolib (FR, 149), Alan (FR, 115), Wayve (UK, 199), Improbable (UK, 5).

Deliberately a clean "finish Europe" batch, distinct from batch 2's new-country push — this
closes out every EU/UK candidate the panel identified except:
- **300+-role giants** (SumUp 365 and the 14 US giants: SpaceX, Databricks, Anthropic, Shield AI,
  Rocket Lab, Datadog, MongoDB, Elastic, Waymo, Relativity Space, Okta, Toast, Harvey) — held per
  the CR's own rule, one at a time, in a future batch.
- **Identity-unconfirmed**: Intercom (Greenhouse board titled "Fin") and Anysphere/Cursor (Ashby
  `cursor`, name not in the job text) — still need a dedicated content check, not done here.

All ~40 remaining US mid-size companies (Oscar Health down to Medium) are held for a dedicated
US-focused batch 4 — batch 3 stays thematically coherent (Europe) rather than mixing regions.

Every company re-probed live, not trusted from the multi-day-old held-table counts (which drift
day to day — e.g. Celonis 262→253, Adyen 217→208, normal board churn). Two probes initially hit
the wrong platform by transcription slip (Improbable tried on Greenhouse, Graphcore on Ashby) —
caught immediately by the 404 and corrected against the held table's own recorded token/platform
before anything was added; a reminder that the table's data, not muscle memory, is the source of
truth even on a well-worn recipe.

## New industry tags and their crosswalk decisions

Five new tags, decided in `trusted_stats/crosswalks.py` (version `2026-09-28.1`):
- **Restaurant Tech** (Flipdish) → J — an ordering-software platform, not a restaurant operator.
- **Autonomous** (Wayve) → J — fundamentally an AI/software company (self-driving models), same
  reasoning as the existing "AI" tag, even though it also tests physical vehicles.
- **Insurtech/Health** (Alan) → K — a regulated health insurer; its telehealth clinic is
  additive, not its core regulated activity.
- **Delivery** (Wolt) → None — mixes a software platform with the actual delivery operation, same
  reasoning as the existing "Food Delivery/Marketplace" tag.
- **Semiconductors/AI** (Graphcore) → None — designs and manufactures physical AI accelerator
  chips, real manufacturing activity; no manufacturing SIC section is otherwise mapped in this
  crosswalk, so forcing one would be a guess.
