source: stakeholder-request
date: 2026-09-27

User: "pick up batch 2 and employer size band" — continuing
`changes/2026-09-23-us-eu-employer-panel-expansion.md`, whose Step 5 (non-English classification
sample-check) and Step 7 (backlog/budget check after batch 1) were still open, and whose Step 9
holds 110 verified companies (~16,100 postings) for later batches.

## Step 5 (carried over): non-English classification sample-check

Only German had been tested (via the Personio CR). French was still untested, and
`EMPLOYER_PANEL.md`'s held list includes several mainly-French boards (Doctolib, Alan, Qonto,
BlaBlaCar, Mirakl, Contentsquare, Swile, Ledger, Sorare, Back Market) explicitly gated on this.

13 constructed French titles, classified via `classify_batch` (1 LLM request, title-only, no DB
writes): all 13 landed sensibly with `high` confidence — Ingénieur logiciel/Développeur →
Engineer; Responsable Ingénierie → lead/management; Chef de produit/Product Owner → Product
Manager; Designer produit/UX Designer → Designer; Stagiaire/Assistant(e) (Stage) → entry;
Chargé(e) de clientèle/Comptable → `other`. **Conclusion: French titles classify correctly, same
as German — no taxonomy or prompt change needed.**

## Step 7 (carried over): backlog/budget check

Done as part of the Personio adapter's production run (`changes/2026-09-26-personio-adapter.md`,
2026-09-27): classification backlog was 0, requirements backlog ~4,220 and draining normally,
and the LLM budget was raised $5→$10/month the same day
(`changes/2026-09-27-llm-budget-raised-to-10.md`). Real headroom exists for a batch larger than
batch 1's 26 companies.

## Batch 2 selection

35 companies, ~1,284 postings (real, live-verified counts — see the change request). Chosen from
the 110 held companies to:
- Bring in 9 countries with zero prior coverage: AT, BE, CH, IE, IT, LT, PL, PT (plus deepening
  DE/DK/ES/FI/FR/NL/SE/UK, which batch 1 only lightly touched).
- Exclude every 300+-role board (SumUp 359, Adyen, Celonis, HelloFresh, Wolt, Nord Security was
  checked live at 130 — under the threshold, kept in) — the CR's own explicit rule: giants go
  last, one at a time, so they don't dwarf the daily classification/requirements budget.
- Exclude the two identity-unconfirmed candidates (Intercom, Anysphere/Cursor) — still need a
  dedicated content check, not done here.

Every company was re-probed live (not trusted from the multi-day-old table) — this caught one
real error: TravelPerk's actual Ashby token is `perk`, not `travelperk` (the table's own working
notes had the right token; an initial guess at the plain slug would have 404'd). Real counts also
drifted meaningfully from the table for a few companies (raisin 34→35, cabify 67→68, oura
97→92) — normal day-to-day board churn, not a data-quality problem.
