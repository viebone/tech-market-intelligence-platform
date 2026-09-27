# What This Platform Does

A 2-minute plain-language map of this product — what it offers today, for whoever needs to
understand it quickly (you, a collaborator, a future you). No jargon, no file paths.

**If you need the technical deep-dive instead, that's [`ONBOARDING.md`](ONBOARDING.md).** This
file is deliberately the opposite of that one: short, capability-first, updated every time
something new ships — see "Keeping this current," below.

---

## What this is

A market intelligence tool for UX and other tech professionals. It tracks hiring demand,
skills, salaries, and employment risk (layoffs, closures, restructuring, expansion) so someone
can tell whether now is a good time to job-search, before they commit to one.

## What you can do with it today

**Get a market read, fast.** Open the product and ask, in plain English, whether now is a good
time to look for a role — which roles/skills are in demand or declining, what a realistic salary
looks like, whether layoffs are outpacing hiring. Answers come from this platform's own
collected data, never a guess.

**See the reasoning behind any answer.** Every AI response has a "View thinking" toggle showing
exactly what data it looked at and how it got there — so you can verify it instead of just
trusting it.

**Read fixed data stories with no AI involved.** Five standing reports — "What we know about
the market," "Employment risk across the market," "Independent market benchmark" (a second,
outside read on hiring demand and pay from a specialist third-party site, shown separately,
never blended with this platform's own numbers), _(new, 2026-09-21)_ "Beyond Design,
Product & Engineering" (what the tracked companies are actually hiring for outside the 3
tracked role categories — roughly half of all classified postings, never shown anywhere else),
and _(new, 2026-09-25 — corrected here, missed at the time)_ "UK vacancies (official data)"
(official UK government statistics on job vacancies economy-wide, by industry and by business
size, with the roles this platform tracks placed alongside them so you can see how far this
platform's own view leans) — are built straight from the data, no model call, so they're
instant and can't be wrong in the way an AI answer occasionally can be. _(New, 2026-09-27.)_
"UK vacancies (official data)" now also traces the official group closest to tech — it covers
software and IT services as well as telecoms, publishing, and broadcasting, so it's a wider
category than "tech" alone — back to 2001, so you can see how it has moved against the whole UK
market through the 2022 hiring peak and since. _(New, 2026-09-22.)_ Several blocks across these stories
now render as real comparison charts instead of plain ranked lists or a bare percentage bar —
"What we know about the market"'s skills-demand, year-on-year, and pay-transparency blocks;
"Employment risk"'s contraction-vs-expansion split; "Beyond Design, Product Management &
Engineering"'s share of all hiring — same underlying data, easier to read at a glance.
_(New, 2026-09-27.)_ Across all four of these stories, several more numbers now show up in
whichever picture actually fits the question, rather than a ranked list repeated three or four
times in a row: how the role mix, seniority, and individual-contributor-vs-management split are
shifting each get their own distinct shape; typical pay by role now shows the real range of
advertised salaries, not just one average figure; what the tracked companies hire for beyond
Design, Product Management, and Engineering is now sized visually by how much of the wider
picture each area actually is; and which industries are gaining or losing UK vacancies is now a
plain up-or-down comparison. Every chart also now has a "Show as table" option for the exact
numbers, works from the keyboard, and reads correctly with a screen reader. _(New, 2026-09-27.)_
"UK vacancies (official data)" now also places the roles this platform tracks alongside the
official figures by **company size**, not just by industry — so you can see, for example, that
none of the employers this platform tracks have under 50 people, while official figures put
roughly a quarter of all UK vacancies at businesses that small.

**Tell us how it's going.** _(New, 2026-09-23.)_ "Give Feedback" sits at the bottom of the task
list, always available — click it to rate overall satisfaction (1–5) and optionally say more, in
seconds, with no account needed. Every data story also ends with a quick thumbs up/down; a
thumbs down invites an optional comment on that specific story. Nothing is required, nothing is
ever forced on you, and every response is anonymous.

**Bring your own AI.** _(New, 2026-09-15.)_ Rather than only using this platform's own chat, you
can connect Claude, ChatGPT, Gemini, or any compatible AI assistant directly to this platform's
data — sign up, connect it from the Settings tab, and ask your own AI the same kinds of
questions, using *your* AI subscription instead of this platform's. Revoke access anytime.

**(Operator only) See what the data pipeline actually did.** A separate, password-protected
dashboard shows every job posting and employment event ingested, classified, and indexed, plus
every external data source's licence status — confirmed or not, commercial use permitted or
not, and under what attribution terms this platform may use its data — and _(new, 2026-09-18)_
the raw market-benchmark data itself (demand/salary snapshots and weighted skill associations)
plus when each scraped source last ran and whether it's due again. _(New, 2026-09-21.)_ Also
shows real recurring job titles/specializations the classification taxonomy doesn't have a
category for yet, so a future revision can be based on real signal rather than a manual check.
_(New, 2026-09-23.)_ Also shows user feedback — overall satisfaction average, a per-story
thumbs up/down breakdown, and every individual response with its written comment, if any. Not
something an end user ever sees or needs.

## How it's built, in one paragraph

The interface is a conversation, not a dashboard with a chat box bolted on — every screen is
designed around an AI-native, "ask and see" model. Underneath, real job postings and employment
records are collected daily from public sources, classified against a fixed taxonomy, and stored
— nothing here is mock data. Two independent pipelines feed it (job postings; employment-risk
events), and a small, explicit set of AI-provider adapters means the platform isn't locked into
one AI vendor for its own chat feature either.

## Where things actually run

`web` (what you open in a browser) talks to `api` (the backend) talks to one Postgres database.
Two scheduled jobs feed that database daily. Full detail: [`DEPLOYMENT.md`](DEPLOYMENT.md).

## Want more detail on any of this?

- **How to actually build on it**: [`ONBOARDING.md`](ONBOARDING.md) — the full guided reading path
- **Exactly what's reachable from where** (frontend, backend, or this platform's MCP server):
  [`ACCESS.md`](ACCESS.md)
- **Where the data comes from**: [`DATA_SOURCES.md`](DATA_SOURCES.md)
- **What we're actually allowed to do with each data source** (licence, commercial-use rights,
  open flags): [`LICENSING.md`](LICENSING.md)
- **Why any specific decision was made**: [`changes/`](changes/) — every change, dated, with its reasoning
- **What's deployed where**: [`DEPLOYMENT.md`](DEPLOYMENT.md)

---

## Keeping this current

This file exists specifically so understanding "what does this platform do" never requires
re-reading specs or code. That only works if it's actually kept current — so updating it is now
a **mandatory step of `/change-request`** for any change that adds, removes, or meaningfully
changes a capability (see the shared `change-request` skill). If you ever find this file out of
date, that's a process miss worth flagging, not a one-off oversight to quietly fix.
