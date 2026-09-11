source: stakeholder-request
date: 2026-09-11

See also: `changes/2026-09-11-employment-events-independent-scope.md` (Story 2, shipped
earlier today) and `changes/2026-09-11-employment-event-ingestion.md` (parent change).

Raw trigger:

> "that is great, now we need to add the dimension of country, we don't need to go in the
> detail of which us state for now but more by country."

Story 2's "Where it's happening" block currently groups by `COALESCE(region, country)` —
conflating US state codes (`"CA"`, `"WA"`) and country codes into one undifferentiated list.
With today's data 100% US-sourced, this reads as a flat state list with no country framing at
all; once a second country's source goes live (Eurofound ERM), the list would mix state-level
and country-level rows in one ranking, which is not a meaningful comparison. User wants
country as the dimension now, state-level detail deferred.
