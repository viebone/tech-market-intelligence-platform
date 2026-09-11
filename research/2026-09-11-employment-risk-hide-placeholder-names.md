source: stakeholder-request
date: 2026-09-11

See also: `changes/2026-09-11-employment-risk-12-month-window.md` (same day, same story).

Raw trigger, after seeing UK Companies House events display as "Company 12028607":

> "ok I don't want names that doesn't mean anything, so whenever that happen, if it is an id
> and not a company, then don't show it. so for now, lets not worry about the companies and
> lets worry about the events. if company names are not clearly available don't show companies
> and show generic data"

Direction: when a source gives no real company name (only an id/number), don't display it as
if it were a company — but the underlying event is still real and should still count toward
aggregate ("generic") figures: direction totals, country breakdown, sector breakdown. Only the
company-name-specific display (the "Companies with the most reported impact" ranked list)
should exclude such rows.
