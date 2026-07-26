source: internal
date: 2026-07-22

Two related issues surfaced while manually testing the live-Adzuna Market Health work (see
research/2026-07-16-adzuna-live-data-and-classification-taxonomy.md, now shipped).

## 1. Chat answers from fake data with a fabricated source

User tested the Market Health chat with follow-up questions ("give me a list of the jobs by
category", "how many on each", "where are you getting that data?", "as of today, how many jobs
opening of each category do we have"). The AI answered with the OLD mock category names ("UX
Design", "Product Management", "Software Engineering"), fabricated numbers (4,000 / 1,783 /
1,680), and cited "LinkedIn job postings" as the source — none of which is real. The opening
trend chart is wired to the real Adzuna/classification pipeline (prior change), but
`chat.py`'s `_build_system_prompt()` still builds its context entirely from `mock_data.py` via
`_resolve_signal` / `_filter_demand` / `_filter_compensation` — a code path the prior change
never touched, since that change's scope was specifically the trend chart.

User's requirement, in their own words: "I would like the llm to draw answers related to my
data only when asking questions related to job tech market. but also I would like the llm to
provide its own knowledge. the important thing would be to clearly always explain where is
this data coming from on the reasoning" — and confirmed the classification decision itself:
"the classification I am ex[pe]cting the llm to decide in which category according to the
content."

So: when a question is answerable from the real dataset, answer from that. When it goes beyond
what the dataset covers, the model may use its own general knowledge. Every answer must clearly
attribute which parts came from which source — no blending without attribution, and never a
fabricated source label like "LinkedIn job postings" again.

## 2. Scheduled, independent classification agent

User wants the Adzuna-fetch + LLM-classification pipeline (currently `backend/src/ingest.py`,
manually triggered — every run this session was triggered by hand) turned into a properly
independent, scheduled process, decoupled from user-facing interactions. Requirements
discussed:

- Runs on a daily cron schedule on Railway (user has a paid Railway plan, $6/mo, already
  hosting the Postgres database) — not triggered by any user request path.
- Uses its own dedicated Gemini API key (`GEMINI_API_KEY_CLASSIFICATION`, already created and
  saved to `backend/.env`, not yet wired into code), separate from the key `/api/chat` uses —
  so a heavy classification day never competes with live user chat sessions for the same quota,
  and vice versa. Motivated directly by this session's real experience: manual classification
  testing repeatedly hit the same shared free-tier quota that live chat would also draw from.
- User's own definition of "agent" here, discussed and agreed: connects to an external tool
  (Adzuna), gathers data, and delegates the one step that genuinely requires reasoning
  (classifying a posting's category from its title/content) to the LLM within constraints the
  user sets (the closed taxonomy, the `other` escape hatch) — matches `design/foundations.md`
  Principle 1 (Intent First, Always Explicit — user sets constraints and delegation boundary,
  system operates within them).
- Agreed scope for making it more than a bare script: (a) a structured run summary/report each
  run (postings fetched, new vs. duplicate, classified vs. cache-hit, `other` rate, errors) so
  a run's outcome is inspectable rather than only existing in ephemeral logs; (b) basic anomaly
  flagging (a search term returning zero results, an `other` rate far outside historical norms)
  so the pipeline surfaces exceptions instead of silently continuing.
- Explicitly deferred: autonomous taxonomy-change suggestions (analysing raw title frequency in
  `other`-classified postings and proposing new search terms/categories for
  `job-classification.md`). Valuable but premature — not enough real run history yet to know
  what thresholds/patterns are worth flagging. Revisit as a future change once there's evidence
  to build against. If ever built, it must propose changes for human review, never edit
  `job-classification.md` directly — that spec only changes through `/change-request`.

User confirmed: combine both into a single change request rather than splitting them.
