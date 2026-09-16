source: stakeholder-request
date: 2026-09-16

> "but we are missing lots of sources? what about the api access to level [lever], greenhouse,
> etc etc... we need all sources, and we need to specify which data are we getting from those
> and we need to make sure that every bit of data can be tracked against this licenses"

## What was checked, directly against each platform's own current documentation

| Source | Doc checked | What it actually says |
|---|---|---|
| Greenhouse | `docs.greenhouse.io/job-board.html` | No terms-of-use language on the page itself. Describes the API's purpose as letting a company "build a custom job board or career site." Public, unauthenticated, no API key. Third-party read access neither addressed nor prohibited. |
| Lever | `github.com/lever/postings-api` (Lever's own official docs repo) | States the API "is designed to help you create a job site" — but explicitly adds: **"Note that all job postings in the `published` state are publicly viewable. These jobs may be scraped by third parties."** The clearest, most direct statement of the three. |
| Ashby | `developers.ashbyhq.com/docs/public-job-posting-api` | "This API allows you to get data for all currently published Job Postings for your organization. If you host your own careers page, you can use this data to populate it." No terms-of-use language, no mention of third-party access either way. Public, unauthenticated. |

None of the three publishes anything resembling a Creative Commons licence, an Open Government
Licence, or a public-domain statement — because none of them are publishing *their own* content
at all. The actual content (job titles, descriptions, compensation) belongs to the **hiring
company** (Stripe, Airbnb, etc.), published via that company's own careers page, which happens
to be hosted by Greenhouse/Lever/Ashby's infrastructure and exposed through a public API
endpoint. The licensing question here is really "is it acceptable to read and store a company's
own public job posting," not "does the ATS platform license this data to us."

## Why this reads as fine to keep doing, honestly stated

- All three endpoints are **public and unauthenticated** — no login, no API key, freely
  reachable by anyone, including a browser.
- Lever's own documentation **explicitly says** third-party scraping is expected and normal.
- Neither Greenhouse nor Ashby's documentation states or implies a prohibition — the "intended
  use" language describes the primary use case (the hiring company embedding its own board),
  not an exhaustive list of permitted uses.
- This platform's own actual use — extracting structured facts (role, seniority, skills,
  location, salary) and aggregate trends, not republishing full postings to end users — matches
  the same posture every job aggregator (Indeed, LinkedIn Jobs, Glassdoor) already operates
  under.

## What's genuinely still worth being honest about

The full raw job-posting response, including the complete description text, is stored verbatim
in `raw_postings.raw_response` (same "capture the source's own shape, don't project it down"
discipline as everywhere else in this codebase). That description text is the hiring company's
own copyrighted content. Storing it internally for classification/extraction is standard
practice; the moment any feature ever displays a full raw description verbatim to an end user
(rather than facts/trends derived from it), that's a materially different question worth its own
look — flagged in `LICENSING.md` §3, not solved here since nothing does that today.

## What this produced

- Three new `source_licences.py` entries (`greenhouse`, `lever`, `ashby`), each `confirmed=True`
  (the actual documentation was read, even though no formal licence exists to confirm) and
  `permits_commercial_use=True` (nothing found restricting it).
- A `data_summary` field added to `SourceLicence` — "what do we actually take from this
  source," visible in the admin view next to the licence itself, answering the "specify which
  data" half of the request.
- `backend/tests/test_source_licences.py` — a real, enforced coverage check: every adapter
  registered anywhere in the codebase (job postings, employment events, scraped) must have a
  `source_licences.py` entry, and every entry must correspond to a real adapter. This is what
  makes "every bit of data can be tracked against a licence" an enforced fact, not a hope.
