source: internal
date: 2026-08-29

Raw input (from a working session on upgrading the LLM pipeline to a paid tier):

---

"ok, so what we need is a plan to upgrade to paid version. llm token economy is
still a primary issue to consider. What I am aiming to is: better job
classification, clean the backlog of unclassified jobs including those that
don't have clear classification and then improve the daily job sync so we
always keep no backlog of unclassified and high quality. all of this within a
budget of 5 dollars a month as I am going with prepay until things are clear. I
must be sure that i am not going crazy with the expenses. for now we keep the
free tier on the front-end chat, that is not changing for now but it could.
also need to open to the possibility of using other models in certain cases."

"yeah lets do it so I make sure chat is outside of paid model, for now"

"but it doesn't matter which model is for chat right? I just [want] whatever
comes for free"

---

## Investigation done this session (facts, not decisions)

Current Gemini project / key layout (from AI Studio, 2026-08-29):

| Project ID | Keys | Billing tier | Currently used by |
|---|---|---|---|
| `gen-lang-client-0963554051` | `…KtBINw` ("jobs"), `…dC4T4Q` ("chat") | Tier 1 · Prepay | classification + `/api/chat` |
| `gen-lang-client-0003173949` | `…1uPQZA` | Free | requirements extraction |
| `gen-lang-client-0993370124` | `…u-dw` ("Default") | Free | nothing (unused) |

- Billing is **per Google Cloud project**, not per API key. Chat and
  classification share one project — so chat currently runs on a Tier 1 ·
  Prepay (paid) project, i.e. chat traffic can incur spend today.
- The user wants chat on a **free-tier** project so it is structurally
  incapable of spending money ("for now").
- Live `generateContent` test 2026-08-29 against project
  `gen-lang-client-0003173949`:
  - `gemini-2.5-flash` → `404` "no longer available to new users, use
    `gemini-3.6-flash`"
  - `gemini-2.5-flash-lite` → `404` "use `gemini-3.5-flash-lite`"
  - `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite` → OK
  - `gemini-flash-latest`, `gemini-flash-lite-latest` → OK
  - (`ListModels` on this project *lists* `gemini-2.5-flash` but calling it
    404s — the list is not authoritative.)
- Project `gen-lang-client-0963554051` is grandfathered — `gemini-2.5-flash`
  works there. Project `gen-lang-client-0003173949` (created 2026-08-10) is
  not.
- Prepay with auto-recharge OFF is a genuine hard spend ceiling: when credit
  is exhausted, calls fail rather than billing continuing.

## Broader goals captured (not all in scope of the immediate change)

1. Chat isolated on free tier — cannot spend (immediate).
2. Both jobs LLM workloads (classification + requirements) on ONE prepaid
   project, capped at $5/month, with an app-level spend ledger + monthly
   ceiling so the pipeline stops itself before exhausting the prepay.
3. Better classification quality + a golden benchmark dataset.
4. Clear the backlog of unclassified / unknown-classification postings.
5. Daily sync keeps zero backlog going forward.
6. Open to non-Gemini models (e.g. Anthropic — key already present) for
   specific cases like an ambiguous-classification second pass.

Related prior research: `research/2026-07-16-adzuna-live-data-and-classification-taxonomy.md`,
`research/2026-08-04-classification-llm-call-reduction.md`,
`research/2026-08-05-cross-run-daily-budget-gap.md`,
`research/2026-08-09-skills-and-industry-signal.md` — all deal with the
free-tier 20-requests/day ceiling this work is meant to lift.
