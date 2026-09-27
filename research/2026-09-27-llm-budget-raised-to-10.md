source: stakeholder-request
date: 2026-09-27

User: "we can increase the budget, lets run at 10 pounds a month, lets double it" — clarified
in follow-up: meant doubling the USD figure to $10/month (not literal GBP), and had already
raised the actual GCP prepaid balance to $10/month via the Google console before asking,
because the $5 target was "blocking everything."

Context: the $5/month figure is the user's own founding quote in
`outcomes/llm-spend-is-bounded-and-isolated.md` ("all of this within a budget of 5 dollars a
month... I must be sure that i am not going crazy with the expenses"). The only place that
figure appears as forward-looking operator guidance (not a historical quote or a change
request's dated decision log) is `DEPLOYMENT.md`'s "Gemini projects & LLM billing" section:
"Keep only a small balance loaded on each (target: ~$5/month of headroom)".

No code change: `DAILY_REQUEST_BUDGET` / `REQUIREMENTS_DAILY_REQUEST_BUDGET` (20/day each) are
a separate, unrelated request-pacing lever, explicitly parked ("must not be raised yet") until
a real dollar-based spend-ledger exists — not raised here, not asked for.
