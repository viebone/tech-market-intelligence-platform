source: internal
date: 2026-09-11

See also: `research/2026-09-11-employment-event-data-sources.md` (original source evaluation —
flagged Eurofound ERM's access mechanism as unconfirmed, needing a manual browser step to
capture a JS-triggered export URL) and the user's own request this same session: "I need more
data from Europe, what do you recommend?"

## The manual-step blocker is resolved — no browser step needed

Rather than asking the user to open DevTools and click "Export data," the real mechanism was
found by reading Eurofound's own client-side JS directly (`GET
https://apps.eurofound.europa.eu/restructuring-events/assets/js/scripts/search-page.js`):

```js
function getFactsheetCSV() {
  const csvEndpoint = new URL(window.location.href);
  csvEndpoint.search = query;                                    // same filters as the search form
  csvEndpoint.pathname = csvEndpoint.pathname.replace("search", "factsheetscsv");
  ...
}
```

The "Export data" button is just a normal `<a>` element whose `href` gets set to the search
page's own URL with `search` swapped for `factsheetscsv` in the path, then clicked — a plain,
unauthenticated GET, not a form POST or an API call needing headers/tokens.

**Verified live** (`curl`, 2026-09-11):

```
GET https://apps.eurofound.europa.eu/restructuring-events/factsheetscsv
→ 200 OK, Content-Type: text/csv, 33,509 data rows
```

Real columns: `Id, Announcement date, Country, Company, Sector, Restructuring type, Employment
Change`. Sample row: `301005,2026-09-08,Spain,Barceló Hotel Group,Accommodation / Food,Business
expansion,+100`. Freshest row dated 2026-09-08 — a live, current feed, not a stale archive.

No query params returns the **entire** dataset (all 33,509 cases, EU 27 + Norway + a handful of
`"European Union"`/`"World"`-scoped multi-country announcements) — there is no rate limit or
pagination requirement found; the endpoint is a flat CSV dump. Given the file's small size
(~2.8MB) and the adapter's own weekly schedule, fetching the full file every run and relying on
`insert_new_events()`'s existing id-based dedupe (proven correct for Companies House's
change-stream case) is simpler and more robust than a trailing-date-window design — no cursor
tracking needed, and any late-corrected historical row is naturally picked up on the next run.

## Real restructuring-type vocabulary (full file, all 33,509 rows)

| Type | Count | Maps to `event_type` |
|---|---|---|
| Business expansion | 13,203 | `expansion` |
| Internal restructuring | 12,326 | `restructuring` |
| Closure | 3,429 | `closure` |
| Bankruptcy | 1,652 | `bankruptcy` |
| Offshoring/Delocalisation | 1,176 | `offshoring` |
| Merger/Acquisition (+ 1 `"Merger /Acquisition"` typo variant) | 882 | **not mapped — direction is genuinely ambiguous (could be either), skipped rather than guessed** |
| Relocation | 380 | **not mapped — ambiguous, skipped** |
| Reshoring | 314 | **not mapped — skipped** (a defensible case exists for `expansion`, but deliberately not asserted without the same kind of confirmation the other 5 types have; left as an open question below) |
| Outsourcing | 147 | **not mapped — skipped** |

Five of nine real types map cleanly onto this platform's existing closed `event_type` set
(`employment_events/base.py`), covering 31,786 of 33,509 rows (**94.9%**). The remaining four
types (1,723 rows, 5.1%) are logged as skipped, not guessed — same "unrecognised type, log and
skip" discipline the adapter already had in place before this file existed, aggregated to one
summary log line per type per run rather than one line per record (1,723 individual warning
lines per run would be noise, not signal).

## Country coverage gap found and fixed

`sources/base.py`'s shared `normalize_country()` / `COUNTRY_NAME_TO_ISO2` (used by both
`raw_postings.country` and `employment_events.country`) only mapped 19 countries — none of them
most of the EU. Real ERM country values (`cut`/`csv.DictReader` over the full file): Austria,
Belgium, Bulgaria, Croatia, Cyprus, Czechia, Denmark, Estonia, Finland, France, Germany, Greece,
Hungary, Ireland, Italy, Latvia, Lithuania, Luxembourg, Malta, Netherlands, Norway, Poland,
Portugal, Romania, Slovakia, Slovenia, Spain, Sweden, United Kingdom, plus two non-ISO values
(`"European Union"`, `"World"` — genuinely not a single country, left unmapped/`NULL` rather
than guessed). Without extending the shared map, most EU country values would have silently
normalized to `NULL` — directly undermining the user's actual ask ("more data from Europe," a
by-country breakdown). Fixed by adding the missing 19 real EU/Norway entries to
`COUNTRY_NAME_TO_ISO2`.

## Open question

Whether `Reshoring` should map to `expansion` (a defensible reading: jobs returning onshore to
the country in that row) is left open rather than decided in this pass — flagged for a future
change if the ~1% this represents becomes worth a deliberate call, not resolved by default here.
