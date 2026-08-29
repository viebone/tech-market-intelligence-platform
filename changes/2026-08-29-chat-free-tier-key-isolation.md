---
id: chat-free-tier-key-isolation
date: 2026-08-29
trigger-type: internal
change-type: technical-refactor
outcome: llm-spend-is-bounded-and-isolated
status: in-progress
---

# Change Request: Isolate `/api/chat` onto a free-tier Gemini project

## Signal
See: `research/2026-08-29-llm-cost-governance.md`

## Outcome
See: `outcomes/llm-spend-is-bounded-and-isolated.md`

This is the **first slice** of that outcome — it delivers the "a workload that
must not cost money runs where a billable call cannot succeed" criterion for
chat, and consolidates the two paid jobs workloads onto one prepaid project. The
"hard monthly ceiling / spend ledger / in-product spend visibility" criteria are
a **separate follow-on change request** against the same outcome.

## Change Type
`technical-refactor` — no user-facing feature and no intentional UX change. Chat
keeps its exact behaviour and contract; only the credential it uses and the
Gemini model it names change. The model swap (`gemini-2.5-flash` →
`gemini-3.6-flash`) carries UX *risk* that must be verified end-to-end (see
Execution Plan step 6), but the intent is unchanged behaviour.

## What changes (Option A — key value swap, no var renames)

| Env var | Before → after (value) | Project before → after |
|---|---|---|
| `GEMINI_API_KEY` (`/api/chat`, reasoning trace) | `…dC4T4Q` → `…1uPQZA` | `gen-lang-client-0963554051` (Tier 1 Prepay) → `gen-lang-client-0003173949` (**Free**) |
| `GEMINI_API_KEY_REQUIREMENTS` (requirements extraction) | `…1uPQZA` → `…dC4T4Q` | `gen-lang-client-0003173949` (Free) → `gen-lang-client-0963554051` (**Tier 1 Prepay**) |
| `GEMINI_API_KEY_CLASSIFICATION` | unchanged | `gen-lang-client-0963554051` (Tier 1 Prepay) — unchanged |

- `_CHAT_MODEL` in `backend/src/chat.py`: `"gemini-2.5-flash"` → `"gemini-3.6-flash"`.
  Forced off `gemini-2.5-flash`: project `gen-lang-client-0003173949` returns
  `404` for it (live-tested 2026-08-29). Pinned to `gemini-3.6-flash` rather than
  the `gemini-flash-latest` alias `requirements.py` uses, because that alias
  consistently timed out on this free project when tested (4/4), while the pinned
  model it resolves to responded fine every time — free-tier throttling on the
  alias. Revisit the alias if that clears.
- `classification.py` — **no change.** Stays `gemini-2.5-flash`; its project
  (`…0963554051`) is grandfathered and now sole-purpose paid.
- `requirements.py` — **no change.** Stays `gemini-flash-latest`; now runs on the
  prepaid project instead of the free one.

## Spend safety during the gap before the follow-on CR

The existing per-workload request-count budgets (`DAILY_REQUEST_BUDGET = 20` for
classification; `REQUIREMENTS_DAILY_REQUEST_BUDGET` for requirements) stay in
force and are extremely conservative in dollar terms (pennies/day). They remain
the operative spend cap until the follow-on spend-ledger CR lands. **They must
not be raised before that CR.** Prepay balance with auto-recharge OFF is the
independent backstop.

## Specs Affected

| Layer | File | Action |
|---|---|---|
| Outcome | `outcomes/llm-spend-is-bounded-and-isolated.md` | no-change (created this session, already describes this) |
| Design Foundations | `design/foundations.md` | no-change |
| Information Architecture | `design/information-architecture.md` | no-change |
| Visual Design | `design/visual-design.md` | no-change |
| Experience Spec | `design/market-health/experience.md` | review, no change expected (verify new chat model still honours the sourcing rule + two-part answer format) |
| Experience Spec | `design/ai-reasoning-panel/experience.md` | review, no change expected (verify reasoning trace still renders) |
| Frontend Spec | `frontend/specs/market-health/architecture.md` | no-change (SSE contract unchanged; model is backend-internal) |
| Backend Spec | `backend/specs/market-health/api.md` | update — chat code examples' model name; factual note on the project reassignment + that request budgets remain the operative cap pending the spend-ledger CR |
| Backend Spec | `backend/specs/ai-reasoning-panel/api.md` | update — one code example's model name (`gemini-2.5-flash` → `gemini-3.6-flash`) |
| Backend Implementation | `backend/src/chat.py` | update — `_CHAT_MODEL` one line |
| Frontend Implementation | `frontend/src/` | no-change |

Non-spec operational docs also updated: `DEPLOYMENT.md` (per-service env-var →
project/tier mapping), product `CLAUDE.md` (key/project notes).

## Execution Plan

- [ ] **Step 1 — Operator prerequisite (user).** On project
  `gen-lang-client-0963554051`: confirm **auto-recharge is OFF**, confirm/load
  the prepaid balance, and (optional) set a cloud-console budget alert at
  $2/$3/$4. No API keys need creating — both already exist.
- [x] **Step 2 — Backend spec (manual edit).** ✅ 2026-08-29. Updated
  `backend/specs/market-health/api.md` (chat code examples → `gemini-3.6-flash`;
  new 3-key/2-project API-keys table; `job-sync` env-var list now includes
  `GEMINI_API_KEY_REQUIREMENTS`; superseded-note on the free-tier budget section)
  and `backend/specs/ai-reasoning-panel/api.md` (code example + model note).
- [x] **Step 3 — Operational docs (manual edit).** ✅ 2026-08-29. `DEPLOYMENT.md`:
  new "Gemini projects & LLM billing" section + updated `job-sync` and `api`
  env-var rows + the "deliberately a separate key" note. Product `CLAUDE.md`: new
  "LLM / Gemini billing" bullet in the production section.
- [x] **Step 4 — `/implement-backend`.** ✅ 2026-08-29. One line in `chat.py`:
  `_CHAT_MODEL = "gemini-3.6-flash"` (+ explanatory comment — pinned, not the
  `gemini-flash-latest` alias, which was timing out 4/4 on the free project;
  specs/docs updated to match). Confirmed `classification.py` (stays
  `gemini-2.5-flash`) and `requirements.py` (stays `gemini-flash-latest`) need no
  change; no other `gemini-2.5-flash` references in live code.
  `python -m py_compile chat.py` passes.
- [~] **Step 5 — Env var values.** Local `backend/.env` swapped ✅ 2026-08-29
  (with an explanatory comment). Post-swap live check: classification key +
  `gemini-2.5-flash` OK; `GEMINI_API_KEY_REQUIREMENTS` (now the ex-chat key) +
  `gemini-flash-latest` OK; `GEMINI_API_KEY` (now the free-project key) +
  `gemini-3.6-flash` OK. **Observation:** the `gemini-flash-latest` *alias*
  endpoint returned intermittent `503 "high demand"` / timeouts today from
  multiple keys — a Google-side capacity blip on the alias, not a key/project
  problem (pinned `gemini-3.6-flash`, which the alias resolves to, was fine). If
  chat sees persistent 503s in Step 6, pinning `_CHAT_MODEL` to `gemini-3.6-flash`
  is a trivial follow-up. **Still TODO (user):** Railway `api` service
  `GEMINI_API_KEY` and Railway `job-sync` service `GEMINI_API_KEY_REQUIREMENTS`
  (see the handoff message for exact values), then redeploy.
- [ ] **Step 6 — Verify chat (user + Claude).** 2–3 real `/api/chat`
  conversations on `gemini-3.6-flash`: SSE stream intact, `query_market_data`
  tool call works, search-grounding fallback works, reasoning panel renders, the
  two-part "data availability + external judgment" answer format still holds
  (`design/market-health/experience.md` sourcing rule). Confirm the chat key is
  on the free project (a billable overage would fail, not charge).
- [ ] **Step 7 — Verify jobs pipeline (user + Claude).** Trigger a `job-sync`
  run: requirements extraction succeeds against the new
  `GEMINI_API_KEY_REQUIREMENTS` value; classification unaffected.
- [ ] **Step 8 — Rotate the chat key.** It was pasted in a working-session
  transcript. Regenerate it in the console; update `backend/.env` + Railway
  `job-sync` (it is now the requirements key). Recommended, not blocking.
- [ ] **Step 9 — Close + hand off.** Mark this CR `complete`. Open the follow-on
  CR: app-level spend ledger + single monthly ceiling + admin-dashboard spend
  panel + safe raising of throughput budgets (rest of
  `llm-spend-is-bounded-and-isolated`).

## Decision Log
- 2026-08-29: Triaged against a **new** outcome
  (`llm-spend-is-bounded-and-isolated`). Considered `ai-provider-flexibility`
  (its "Out of scope" explicitly excludes cost-driven concerns) and
  `production-deploy-readiness` (about services *working*, not spend) — neither
  fit. Created the cost-governance outcome first per the framework gate.
- 2026-08-29: Change type is `technical-refactor`, not `ux-change` — chat's
  behaviour and contract are unchanged by intent. The model swap is forced by
  the target project's `gemini-2.5-flash` block, not chosen for UX reasons, and
  is verified rather than designed.
- 2026-08-29: **Option A (swap key values, keep var names)** chosen over Option B
  (move the billing account between projects). Option A is less console work and
  keeps classification on `gemini-2.5-flash` (grandfathered project). Cost: chat
  is forced off `gemini-2.5-flash` onto `gemini-3.6-flash` now — acceptable per
  user ("it doesn't matter which model is for chat, I just want whatever comes
  for free").
- 2026-08-29: Scoped to the key swap only. The spend ledger / monthly ceiling /
  in-product spend visibility are a follow-on CR — this slice is safe to ship
  alone because the existing request-count budgets keep spend at pennies/day and
  are left untouched.
- 2026-08-29: Env var **names** unchanged (`GEMINI_API_KEY`,
  `GEMINI_API_KEY_REQUIREMENTS`) — only their values swap — so all spec/doc
  references to the var names stay valid; only billing/project narrative changes.
