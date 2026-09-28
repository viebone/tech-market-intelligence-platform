source: stakeholder-request
date: 2026-09-28

The operator's own words, verbatim:

"ok. now sources and licensing should include scrapped sources and statistics sources, all in
one, if not is confusing keeping them separatedly."

Context: this follows directly from today's earlier work adding the Data Coverage & Quality and
Technical Data Visibility admin views (`changes/2026-09-28-data-insight-coverage-quality-admin-view.md`,
`changes/2026-09-28-technical-data-visibility-admin-view.md`), during which the admin dashboard's
existing source-related views were reviewed. Three separate views currently exist, all describing
the same underlying concept — "a registered external data source, and everything we know about
it" — but split by *when* each was added rather than by what an operator actually wants to know:

- `/admin/licensing` ("Sources & Licensing") — licence status for every registered source
  (already includes job-posting adapters, employment-event adapters, the scraped source
  `itjobswatch`, AND the trusted-statistics source `ons_vacancy_survey` — `source_licences.py`'s
  `SOURCE_LICENCES` registry already covers all 11 registered sources in one dict; confirmed by
  reading the file directly during triage)
- `/admin/scrape-runs` ("Scraped Source Runs") — run cadence (last run, next due) for scraped
  sources only (today: just `itjobswatch`)
- `/admin/statistics-sources` ("Statistics Sources") — trust-bar sign-off, cadence, latest
  release/period, and collected volume (series/observation counts) for trusted-statistics
  publishers only (today: just `ons_vacancy_survey`)

So the *licence* dimension is already unified across all source types; what's fragmented is
*cadence* and *collected volume*, which only scraped and trusted-statistics sources have their
own dedicated views for at all (job-posting and employment-event adapters run on a shared cron
schedule, not an individually-gated cadence, so they were never given their own cadence view).
