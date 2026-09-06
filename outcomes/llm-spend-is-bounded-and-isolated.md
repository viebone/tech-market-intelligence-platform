---
id: llm-spend-is-bounded-and-isolated
source: business
priority: high
status: active
created: 2026-08-29
---

# Outcome: LLM spend stays under a hard ceiling it cannot exceed, and each workload's cost exposure is isolated

## Signal
See: `research/2026-08-29-llm-cost-governance.md`

> "all of this within a budget of 5 dollars a month as I am going with prepay
> until things are clear. I must be sure that i am not going crazy with the
> expenses. for now we keep the free tier on the front-end chat, that is not
> changing for now but it could."

The platform is about to move its job-classification and requirements-extraction
pipeline off the Gemini free tier (whose 20-requests/day ceiling structurally
caps progress — see the four prior classification-budget research files) onto a
paid, prepaid Gemini project. The user is willing to pay, but only against a
small fixed monthly budget, and is not willing to risk an open-ended bill from a
bug, a retry loop, or a large re-ingestion event. Separately, the user-facing
chat feature must stay on a tier where it is *incapable* of spending money — for
now.

## Context
Until now, cost control has been a side effect of the free tier: the pipeline
could not overspend because Gemini simply stopped answering at 20 requests/day.
That ceiling is the thing being removed. Once a real billing account is attached,
nothing in the current system prevents spend from growing without limit — the
existing budget machinery counts *requests against a free-tier quota*, not
*dollars against a balance*, and the retry logic (5 attempts per batch) now costs
real money on every attempt.

Two prior incidents on record show this is not hypothetical: multiple same-day
manual runs each took a fresh request allowance and nearly doubled the intended
daily ceiling (`research/2026-08-05-cross-run-daily-budget-gap.md`), and a
model's hidden double-billing silently spent ~2x what the local ledger counted
(`research/2026-08-09-skills-and-industry-signal.md`). On a free tier those were
harmless. On a paid tier they are money.

Cost exposure also needs to be *compartmentalised*. Chat, classification, and
requirements currently share Google Cloud projects in ways that were never
verified — chat and classification turn out to be the same project. A spike in
one workload should not be able to drain the budget another workload depends on,
and a workload that must never cost money (chat, for now) should be structurally
unable to, not merely expected not to.

If this is ignored: the free-tier ceiling gets removed with nothing put in its
place, and the first runaway loop, retry storm, or bulk re-ingestion produces a
bill the user explicitly said they need to be certain cannot happen.

## Success looks like

> **Amended 2026-09-03 (`changes/2026-09-03-chat-resilience-and-instant-answers.md`).**
> Chat is no longer a "must never cost money" workload. The free tier could not
> serve it reliably (persistent `503`s), so chat becomes free-tier-first with a
> **paid fallback that lives in its own dedicated Google Cloud project**, separate
> from every other workload, under its own per-day request cap. The isolation
> requirement is unchanged and now applies to chat too; the "cannot bill at all"
> requirement is replaced by "cannot bill beyond its own capped, isolated share".
> Chat also gains a zero-LLM answer path (curated questions answered from live
> data) that carries no cost at all and is the preferred path.
>
> **Further amended 2026-09-06 (same change).** After testing, the free tier is
> removed from chat entirely — its 20-requests/day ceiling and unpredictable
> latency made it unusable, and "free-first" wasted seconds per request retrying
> a dead tier. Chat now runs on its **dedicated paid project only**, with **no
> free tier**. The bullets below that say "free-tier-first" / "falls to its paid
> project only on a hard signal" are superseded: chat's paid project is its sole
> model tier, and the **per-day request cap (`CHAT_PAID_DAILY_REQUEST_CAP`) is the
> spend guard** — when it is reached, chat degrades to the zero-cost curated
> path. The isolation requirement and the "cannot bill beyond its own capped,
> isolated share" requirement are unchanged and fully intact.

- Every LLM workload runs against a credential/project scoped to that workload
  alone — a spike or a bug in one workload cannot draw down the balance another
  workload depends on (chat's paid fallback, classification, and requirements are
  three separate projects)
- The workload that should normally cost nothing (chat) runs free-tier-first and
  falls to its paid project only on a hard availability/quota signal — never for a
  routine answer — with a zero-cost curated-answer path tried before any model
  call at all
- Total LLM spend across all paid workloads cannot exceed a single configured
  monthly ceiling; when the ceiling is reached the pipeline stops itself and
  records that it stopped on purpose, the same way it already treats reaching a
  request budget as success rather than failure
- The configured ceiling sits below the prepaid balance, so the prepaid balance
  is a second independent backstop, not the first line of defence
- A bug, an infinite loop, a retry storm, or an unusually large ingestion event
  cannot produce spend beyond the ceiling — the cap is enforced before each
  call, not reconciled after
- Month-to-date spend, and spend broken down by workload, is visible without
  leaving the product (e.g. the admin dashboard) — the user never has to log
  into a cloud console to know where they stand against the budget
- Each paid workload has its own share of the ceiling, so a heavy day for one
  cannot starve another (chat's paid fallback has its own per-day request cap;
  when it is reached chat degrades to the curated-answer path rather than
  spending past the cap)
- Adding a new LLM-using workload requires giving it its own budgeted share —
  it cannot silently draw down an existing workload's headroom
- Spend accounting reflects real provider-side billing, including hidden costs
  like failed-but-billed attempts and multi-call model fallbacks

## Out of scope
- Reducing the *quality* or *coverage* of classification to save money — this
  outcome is about bounding spend, not minimising it; quality trade-offs belong
  to the classification outcomes
- Choosing which specific model or provider each workload uses — that stays an
  explicit call-site decision under `ai-provider-flexibility`
- Automatic switching between providers/models based on price or load (routing
  is always explicit, never cost-driven magic — consistent with
  `ai-provider-flexibility`'s own exclusion)
- ~~Billing/upgrading the chat workload — chat stays on the free tier "for now";
  if that changes it is a new change request against this same outcome~~
  **Done 2026-09-03 via `changes/2026-09-03-chat-resilience-and-instant-answers.md`**
  — chat is now free-first with an isolated, capped paid fallback (see the
  amendment note under "Success looks like")
- Forecasting or optimising cost per classification over time, or a cost
  dashboard richer than "where am I against this month's budget"
- Provisioning or managing the cloud billing account itself (attaching a card,
  loading prepay credit, setting cloud-console budget alerts) — those are
  operator actions this outcome assumes are done, not software behaviour
