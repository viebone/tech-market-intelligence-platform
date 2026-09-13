import { useMemo, useState } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";

// Served from public/ (copied from world-atlas's own countries-50m.json,
// not hand-built) rather than imported as a JS module — react-simple-maps
// fetches a string `geography` prop at runtime, so the ~740KB topology
// loads only when this story is opened and is browser-cacheable as a plain
// static asset, instead of bloating the app's main JS bundle for every
// visitor (confirmed: importing it as a module grew the main bundle from
// ~262KB to ~1.1MB gzip 82KB->352KB — this avoids that entirely).
const WORLD_TOPOLOGY_URL = "/world-countries-50m.json";

// World risk map — a country-level choropleth for Story 2 ("Employment risk
// across the market"). See design/visual-design.md — Data Story composition —
// "World risk map", and changes/2026-09-13-employment-risk-world-map.md.
//
// Uses world-atlas's 50m topology, not the more commonly used 110m one —
// verified directly against this product's real country data that the 110m
// file drops Singapore and Malta (both real countries here); 50m includes
// both. react-simple-maps auto-converts a raw TopoJSON Topology object (its
// "countries" object, confirmed the first key in this file) via
// topojson-client — no separate GeoJSON conversion step needed here.
//
// Each geography's `id` is a real ISO 3166-1 numeric code (e.g. "840" for
// the US) — verified against the actual topology file, not assumed. This
// product stores country as ISO-2 (`normalize_country()`,
// sources/base.py), so ISO2_TO_NUMERIC below is the bridge, built and
// verified only for the countries this platform's COUNTRY_NAME_TO_ISO2
// actually covers — not a general-purpose ISO table.

const ISO2_TO_NUMERIC: Record<string, string> = {
  US: "840", GB: "826", CA: "124", SG: "702", JP: "392", IN: "356", IE: "372",
  DE: "276", MX: "484", AU: "036", SE: "752", ES: "724", FR: "250", KR: "410",
  PL: "616", NL: "528", AE: "784", DK: "208", LT: "440", IL: "376", AT: "040",
  BE: "056", BG: "100", HR: "191", CY: "196", CZ: "203", EE: "233", FI: "246",
  GR: "300", HU: "348", IT: "380", LV: "428", LU: "442", MT: "470", NO: "578",
  PT: "620", RO: "642", SK: "703", SI: "705",
};

export interface CountryRiskRow {
  country: string; // ISO-2
  contraction_events: number;
  contraction_affected: number;
  expansion_events: number;
  expansion_affected: number;
}

const NO_DATA_FILL = "#1f2937"; // gray-800 — neutral, never implies "calm"
const BORDER = "#374151"; // gray-700
const CONTRACTION_HUE = [220, 38, 38] as const; // red-600
const EXPANSION_HUE = [5, 150, 105] as const; // emerald-600

function mix(hue: readonly [number, number, number], t: number): string {
  // t in [0,1] — interpolates between the neutral fill and the full-strength
  // semantic colour, so magnitude reads as intensity, not a new hue.
  const bg = [31, 41, 55] as const; // gray-800, matches NO_DATA_FILL
  const [r, g, b] = hue.map((c, i) => Math.round(bg[i] + (c - bg[i]) * t));
  return `rgb(${r}, ${g}, ${b})`;
}

export function WorldRiskMap({ rows }: { rows: CountryRiskRow[] }) {
  const [hovered, setHovered] = useState<{ row: CountryRiskRow; name: string; x: number; y: number } | null>(null);

  const byNumericId = useMemo(() => {
    const map = new Map<string, CountryRiskRow>();
    for (const row of rows) {
      const numeric = ISO2_TO_NUMERIC[row.country];
      if (numeric) map.set(numeric, row);
    }
    return map;
  }, [rows]);

  const maxAbsNet = useMemo(() => {
    let max = 0;
    for (const row of rows) {
      max = Math.max(max, Math.abs(row.expansion_affected - row.contraction_affected));
    }
    return max || 1;
  }, [rows]);

  function fillFor(row: CountryRiskRow | undefined): string {
    if (!row) return NO_DATA_FILL;
    const net = row.expansion_affected - row.contraction_affected;
    if (net === 0) return NO_DATA_FILL;
    const intensity = 0.3 + 0.7 * Math.min(Math.abs(net) / maxAbsNet, 1);
    return mix(net > 0 ? EXPANSION_HUE : CONTRACTION_HUE, intensity);
  }

  return (
    <div className="relative">
      <ComposableMap
        projection="geoEqualEarth"
        width={800}
        height={400}
        className="w-full h-auto"
      >
        <Geographies geography={WORLD_TOPOLOGY_URL}>
          {({ geographies }) =>
            geographies.map((geo) => {
              const row = byNumericId.get(String(geo.id));
              const name = (geo.properties as { name?: string })?.name ?? "";
              const isHovered = hovered?.row === row;
              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill={fillFor(row)}
                  stroke={BORDER}
                  strokeWidth={0.5}
                  style={{ outline: "none", filter: isHovered ? "brightness(1.25)" : undefined }}
                  onMouseEnter={(event) => {
                    if (row) setHovered({ row, name, x: event.clientX, y: event.clientY });
                  }}
                  onMouseMove={(event) => {
                    if (row) setHovered((prev) => (prev ? { ...prev, x: event.clientX, y: event.clientY } : prev));
                  }}
                  onMouseLeave={() => setHovered(null)}
                />
              );
            })
          }
        </Geographies>
      </ComposableMap>

      {hovered ? (
        <div
          className="pointer-events-none fixed z-10 rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-xs text-gray-300 shadow-lg"
          style={{ left: hovered.x + 12, top: hovered.y + 12 }}
        >
          <div className="font-semibold text-gray-100">{hovered.name}</div>
          <div>{hovered.row.contraction_affected.toLocaleString()} jobs reported affected by contraction</div>
          <div>{hovered.row.expansion_affected.toLocaleString()} jobs reported affected by expansion</div>
        </div>
      ) : null}

      {/* Legend — colour is never the only signal (Data Legibility, visual-design.md). */}
      <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "rgb(5, 150, 105)" }} />
          More reported hiring
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "rgb(220, 38, 38)" }} />
          More reported layoffs
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-gray-800 border border-gray-700" />
          No reported events in this window
        </span>
      </div>
    </div>
  );
}
