source: internal
date: 2026-09-30

The two identity-unconfirmed candidates flagged since `changes/2026-09-23-us-eu-employer-panel-expansion.md`
(2026-09-23) and carried, unresolved, through every subsequent batch. Content-inspected both
live, one request per board, identified User-Agent.

## Intercom (Greenhouse, token `intercom`) — Rejected

`GET boards-api.greenhouse.io/v1/boards/intercom/jobs?content=true` → 200, 113 real postings.
The first job's own content:

> "Fin, now part of Salesforce, is on a mission to help businesses provide perfect customer
> experiences... Fin can also be combined with our natively integrated Intercom help desk."

This board is **Fin** (fin.ai) — Intercom's former AI Agent product, spun out and acquired by
Salesforce — not Intercom itself. "Intercom" appears 177 times in the raw response, but only as
references to the *integrated help desk product* Fin sells alongside itself, never as the
employer. Adding this board tagged "Intercom" would misattribute Salesforce/Fin hiring data to
an unrelated company. **Rejected** — removed from `EMPLOYER_PANEL.md`'s held table. A genuine
Intercom-run board, if one still exists on a different token, was not researched here.

## Anysphere / Cursor (Ashby, token `cursor`) — Verified

`GET api.ashbyhq.com/posting-api/job-board/cursor?includeCompensation=true` → 200, 128 real
postings. Confirmed via explicit text in a real posting:

> "As a Field Engineer, you'll be the technical face of **Anysphere** in the field, helping
> customers evaluate **Cursor**, guiding them through proofs of concept..."

Anysphere is the company; Cursor is its AI coding-assistant product — exactly the expected
relationship. Office locations (Palo Alto, Austin, New York, London, Germany, Japan, Australia,
Bengaluru) are consistent with a real, global engineering company. **Verified** — moved from
"identity unconfirmed" into `EMPLOYER_PANEL.md`'s held table (128 roles), ready for a future
batch. Not added to `COMPANIES` in this pass — classification backlog (1,753) can't drain until
tomorrow's daily LLM budget resets, so no new postings were added today, identity work only.

**One real data-quality artifact found in Anysphere's own posted content, left untouched**: 76 of
128 postings (59%) contain the literal string "SpaceXAI" inside the job description — almost
certainly an unsubstituted template variable in their own ATS content (a broken merge field),
not evidence this is the wrong company (the explicit "Anysphere... Cursor" text elsewhere is
unambiguous). `raw_response` is always stored verbatim, so this quirk will be visible in the
stored data once Anysphere is added — flagged here so it isn't mistaken for an ingestion bug
later.

Industry tag ready for when this is added: "AI Software" (already maps to SIC section J,
`trusted_stats/crosswalks.py`) — no crosswalk change needed.
