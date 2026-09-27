---
id: llm-budget-raised-to-10
date: 2026-09-27
trigger-type: stakeholder-request
change-type: technical-refactor
outcome: llm-spend-is-bounded-and-isolated
status: complete
---

# Change Request: Update operator guidance for the raised $10/month LLM budget

## Signal
See: `research/2026-09-27-llm-budget-raised-to-10.md`

## Outcome
See: `outcomes/llm-spend-is-bounded-and-isolated.md` — refinement of an existing outcome, not a
new one. The outcome's own founding number ($5/month) is what changed; its actual mechanism
(a manually-topped-up prepaid GCP balance, auto-recharge off) is unchanged.

## Change Type
`technical-refactor` — operator/documentation correction only, no code, no user-facing change.
The real action (raising the GCP prepaid balance) was already taken by the operator directly in
the Google Cloud console; this closes the gap between that and what the docs say to do.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/llm-spend-is-bounded-and-isolated.md` | no-change — the quoted signal is a historical record of the original ask, left as-is; the outcome's success criteria (a hard ceiling, isolated workloads) are unaffected by the ceiling's size |
| Deployment guidance | `DEPLOYMENT.md` — "Gemini projects & LLM billing" | update — the one forward-looking "target: ~$5/month" line |
| Backend Implementation | `backend/src/classification.py`, `requirements.py` (`DAILY_REQUEST_BUDGET`, `REQUIREMENTS_DAILY_REQUEST_BUDGET`) | no-change — deliberately not touched; that guardrail is independent of the dollar ceiling and stays parked until a real spend-ledger exists |
| Plain-Language Overview | `OVERVIEW.md` | no-change — an internal ops/billing detail, not something a real user of the product notices |

## Execution Plan

- [x] Step 1: Confirmed with the user: doubling the USD figure to $10/month (not a literal GBP
      amount); the operator had already raised the real GCP prepaid balance themselves
- [x] Step 2: Updated `DEPLOYMENT.md`'s operator-responsibilities line from "~$5/month" to
      "~$10/month" and its budget-alert suggestion range

## Decision Log
- 2026-09-27: Left every *historical* $5/month reference untouched — the outcome file's quoted
  user signal, the research file's transcript, and the dated decision logs in
  `changes/2026-09-23-us-eu-employer-panel-expansion.md` and
  `changes/2026-09-26-personio-adapter.md` (each recorded what was true on that date). Rewriting
  those would falsify the audit trail this framework exists to keep. Only `DEPLOYMENT.md`'s
  forward-looking operator instruction was live/current-state text worth correcting.
- 2026-09-27: Did not raise `DAILY_REQUEST_BUDGET`/`REQUIREMENTS_DAILY_REQUEST_BUDGET` — the
  user asked to double the *balance*, not the request-pacing constants, and `DEPLOYMENT.md`
  explicitly says those wait for a real spend-ledger. Flagged as still open, not decided here.
