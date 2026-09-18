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

**Read fixed data stories with no AI involved.** Three standing reports — "What we know about
the market," "Employment risk across the market," and _(new, 2026-09-18)_ "Independent market
benchmark" (a second, outside read on hiring demand and pay from a specialist third-party site,
shown separately, never blended with this platform's own numbers) — are built straight from
the data, no model call, so they're instant and can't be wrong in the way an AI answer
occasionally can be.

**Bring your own AI.** _(New, 2026-09-15.)_ Rather than only using this platform's own chat, you
can connect Claude, ChatGPT, Gemini, or any compatible AI assistant directly to this platform's
data — sign up, connect it from the Settings tab, and ask your own AI the same kinds of
questions, using *your* AI subscription instead of this platform's. Revoke access anytime.

**(Operator only) See what the data pipeline actually did.** A separate, password-protected
dashboard shows every job posting and employment event ingested, classified, and indexed, plus
every external data source's licence status — confirmed or not, commercial use permitted or
not, and under what attribution terms this platform may use its data — and _(new, 2026-09-18)_
the raw market-benchmark data itself (demand/salary snapshots and weighted skill associations)
plus when each scraped source last ran and whether it's due again. Not something an end user
ever sees or needs.

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
