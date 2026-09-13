source: user-feedback
date: 2026-09-13

Raw trigger:

> "I would like to use folium to see in a map where the hiring is happening and where the
> layoff are happening. Maybe on the Data Story: Employment risk across the market, we can
> replace the list of events by country and instead use the folium with an overlay on the
> countries with events across the world. And move the the first place. what do you think?"

Discussed the implementation choice directly with the user: Folium (Python, generates a full
HTML/Leaflet doc, would need iframe-embedding into the React SPA) vs. a native React map
component. Folium would be the only block in either data story that isn't a typed-JSON-driven
component (every other endpoint in this product returns JSON, not HTML — the one deliberate
exception, the admin dashboard, is a separate app for exactly that reason), would sit inside an
isolated iframe unable to inherit this product's dark theme/typography without extra tile/CSS
work, and would need a full HTML regeneration + iframe reload on every data refresh rather than
a prop update. User agreed to a native React map instead, on the condition it's about as easy
to use as Folium — `react-simple-maps` (a thin declarative wrapper over d3-geo) is the
comparable-ergonomics native option.

## What this replaces

Story 2 ("Employment risk across the market")'s "By country" block — currently a `RankedBarList`
of the top 10 countries by combined (contraction + expansion) `jobs_affected` — becomes a world
map, moved to lead the story (ahead of "Contraction vs. expansion").

## Real technical verification done before deciding on the library/data combo

- `react-simple-maps@5.0.5` — current npm version, peer deps support React 18, ships its own
  TypeScript types (`dist/index.d.ts` — no separate `@types/` package needed, and installing one
  would conflict with its own bundled types).
- `world-atlas@2.0.2`'s `countries-110m.json` (the version almost every react-simple-maps
  tutorial uses) — checked against this product's real country data (38 countries currently
  seen in `employment_events`, the full `COUNTRY_NAME_TO_ISO2` list) and found **Singapore and
  Malta are missing** — the 110m resolution drops small/island nations. `countries-50m.json`
  (756KB raw) includes both, and every one of the 38 countries was verified to resolve to a real
  ISO 3166-1 numeric id against that file directly (not assumed) — e.g. `US -> "840"`,
  `SG -> "702"`, `MT -> "470"`. Using 110m would have silently dropped real Singapore/Malta
  layoff or hiring data from the map — the same "don't silently lose real data" discipline this
  pipeline has followed all along.

## The real data-shape change needed

Today's "By country" aggregate is one combined `affected` number per country, direction-blind.
To colour a country by "hiring here, layoffs there" the backend needs to group by
`country, direction` and return both a contraction total and an expansion total per country, so
the map can encode net direction (and total magnitude) — this is a real, scoped API change, not
only a frontend swap.
