source: stakeholder-request
date: 2026-09-06

"we need the category unknown to be improved. can you pass to gemini batch all unknown for
recalification?"

Context: `role_category = 'unknown'` currently holds 136 classifications. Classification is
**title-only** by design (`design/market-health/job-classification.md` — Classification
Method), so `unknown` means "the title alone can't tell." Re-running the same titles through
the classifier reproduces the same `unknown` labels — no improvement.

`job-classification.md` (Unknown vs. Other) already anticipates the fix: "a high `unknown`
rate ... might mean the title-only classification rule ... needs a fallback."

Sample `unknown` titles (all have `raw_response` / description text available): "Deployment
Strategist", "GRC Engineer", "Design Engineer", "Developer Relations", "Compliance Engineer",
"Embedded Legal Engineer", "Analyst", "AI Strategist, Legal". Many are resolvable from the
description.

Stakeholder direction (2026-09-06): description-assisted **one-time Gemini Batch API** job,
re-classifying every `unknown` posting from title + a description snippet; genuinely
ambiguous ones stay `unknown`. On the classification (prepaid) key. Not wired into the daily
pipeline for now.
