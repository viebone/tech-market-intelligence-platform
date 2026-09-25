import { ResponsiveBar } from "@nivo/bar";
import { nivoTheme } from "./nivoTheme";

// Two-series comparison — the platform's own composition placed beside an outside publisher's, over
// the same categories. Added 2026-09-25 (changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md;
// design/visual-design.md — Two-series comparison; Story 5's third movement).
//
// Rules this component enforces (they are the point of it):
//  - BOTH series are SHARES (%). Never one share and one count.
//  - It shows two labelled values and NOTHING ELSE: no difference, ratio, "over/under-represented"
//    wording, in the chart, the legend or the tooltip. A cross-check is context, not proof.
//  - Colour is never the only signal: the legend names both series in words (the API composes the
//    legend text — names, denominators, dates — so the client never builds provenance text).
//  - A row with no counterpart on the other side draws only the bar that exists (never a zero bar),
//    marked "*" with a footnote saying why.
//
// Primary series = the platform's own view (indigo-500); secondary = the outside publisher's, the
// muted reference series (gray-600) — one accent, one neutral, per the Charting library rule.
// Lazy-loaded by the caller (Nivo weight), themed via the shared nivoTheme.

export interface ComparisonRow {
  label: string;
  /** Share (%) for the platform's own figure, or null when there is no counterpart on this side. */
  primary: number | null;
  /** Share (%) for the outside publisher's figure, or null when there is no counterpart. */
  secondary: number | null;
}

interface SourceComparisonBarsProps {
  rows: ComparisonRow[];
  primaryName: string;
  secondaryName: string;
  missingSideNote?: string;
}

const PRIMARY_COLOR = "#6366f1"; // indigo-500 — the platform's own view
const SECONDARY_COLOR = "#4b5563"; // gray-600 — the outside reference

function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

interface ChartDatum {
  label: string;
  tick: string;
  primary: number;
  secondary: number;
  hasPrimary: boolean;
  hasSecondary: boolean;
}

export function SourceComparisonBars({
  rows,
  primaryName,
  secondaryName,
  missingSideNote = "* Shown for the side that has a figure — the other side has no counterpart for this row.",
}: SourceComparisonBarsProps) {
  if (rows.length === 0) return null;

  const anyMissing = rows.some((r) => r.primary === null || r.secondary === null);
  const data: ChartDatum[] = rows.map((r) => {
    const missing = r.primary === null || r.secondary === null;
    return {
      label: r.label,
      // The tick carries the marker: the full name stays in the tooltip.
      tick: truncate(r.label, 30) + (missing ? " *" : ""),
      primary: r.primary ?? 0,
      secondary: r.secondary ?? 0,
      hasPrimary: r.primary !== null,
      hasSecondary: r.secondary !== null,
    };
  });

  return (
    <div>
      <div style={{ height: Math.max(data.length * 46 + 60, 240) }}>
        <ResponsiveBar
          data={data as unknown as Record<string, string | number>[]}
          keys={["primary", "secondary"]}
          indexBy="label"
          layout="horizontal"
          groupMode="grouped"
          theme={nivoTheme}
          colors={[PRIMARY_COLOR, SECONDARY_COLOR]}
          padding={0.3}
          innerPadding={2}
          borderRadius={2}
          margin={{ top: 8, right: 24, bottom: 56, left: 210 }}
          valueFormat={(v) => `${v}%`}
          axisLeft={{
            format: (value) => {
              const found = data.find((d) => d.label === value);
              return found ? found.tick : String(value);
            },
          }}
          axisBottom={{
            legend: "Share (%)",
            legendPosition: "middle",
            legendOffset: 32,
          }}
          enableGridY={false}
          enableLabel={false}
          isInteractive
          tooltip={({ indexValue, data: rowData }) => {
            const d = rowData as unknown as ChartDatum;
            return (
              <div className="rounded border border-gray-700 bg-gray-800 px-2 py-1 text-xs text-gray-100">
                <span className="font-medium">{indexValue as string}</span>
                <br />
                {primaryName}: {d.hasPrimary ? `${d.primary}%` : "no figure"}
                <br />
                {secondaryName}: {d.hasSecondary ? `${d.secondary}%` : "no figure"}
              </div>
            );
          }}
          legends={[
            {
              dataFrom: "keys",
              anchor: "bottom",
              direction: "row",
              translateY: 56,
              itemsSpacing: 16,
              itemWidth: 170,
              itemHeight: 14,
              symbolSize: 10,
              symbolShape: "circle",
              data: [
                { id: "primary", label: primaryName, color: PRIMARY_COLOR },
                { id: "secondary", label: secondaryName, color: SECONDARY_COLOR },
              ],
            },
          ]}
        />
      </div>
      {anyMissing ? <p className="mt-1 text-xs text-gray-500">{missingSideNote}</p> : null}
    </div>
  );
}
