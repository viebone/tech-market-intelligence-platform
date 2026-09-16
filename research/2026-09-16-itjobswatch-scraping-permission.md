source: stakeholder-request
date: 2026-09-16

> **Note on fidelity**: this file is reconstructed from the conversation in which the email was
> shared, not copy-pasted from the literal original message — the exact original text was not
> retained verbatim across a context compaction. The substance and every specific condition
> below were confirmed against the operator's own account of the email's content at the time it
> was shared. If the literal wording matters later (e.g. citing it externally), go back to the
> operator's inbox rather than quoting this file as the source text.

## What happened

The operator emailed IT Jobs Watch (itjobswatch.co.uk) asking about programmatic/API access to
their UK tech salary and skill-demand data, for this personal project (TMIP).

IT Jobs Watch replied:
- **Declined** a paid/API arrangement — not set up for that, especially for a personal project.
- **Explicitly granted permission to scrape the site**, on these conditions:
  - Respect `robots.txt`.
  - Keep request rate low, with sensible pauses between requests — no hammering the server.
  - Identify the bot clearly: a descriptive User-Agent string plus a real contact address (so
    they can reach out if something misbehaves).
  - Cache pages rather than re-fetching ones that haven't changed.
  - Their content is published under a Creative Commons licence — **attribution is required**
    for anything republished from it, per that licence's terms.

## Why this matters now

This is the second time this session a "can't get an API, can get access some other way" pattern
has come up, and the operator was explicit that they want the *mechanism* built generally, not
as a one-off IT Jobs Watch scraper: "I would like to build in a way that same process could be
applied to other sources, those that cannot be accessed by API."

`DATA_SOURCES.md` §2 already anticipated this in the abstract — the "Company career pages / ATS
portals" row is marked planned, mechanism scraping, "needs a per-site adapter or a generic
HTML/JSON-LD adapter" — but no scraping mechanism exists in the codebase yet. Today's only
fetch machinery (`backend/src/sources/base.py`'s `PacedFetcher`) is built for polite calling of
*APIs* (JSON endpoints, no `robots.txt` concept, no HTML parsing, no page-level caching, no
licence/attribution tracking). IT Jobs Watch is the first real, permission-granted case that
needs the scraping-specific half of that: `robots.txt` compliance, a real User-Agent + contact
string, page-level caching (not just request pacing), and attribution recorded per fact pulled.

## What IT Jobs Watch data actually is

Aggregate UK IT-sector salary and skill/role demand statistics (trend series), not individual
job postings and not discrete employment events — a third shape distinct from both
`raw_postings` and `employment_events`. It doesn't fit either existing storage model as-is.

## Verbatim conditions (for the backend spec to bind to)

1. Respect `robots.txt`.
2. Low request rate, with pauses.
3. Clear User-Agent + contact address on every request.
4. Cache; don't re-fetch unchanged pages.
5. Attribute (CC licence) anywhere this data is republished/displayed.
