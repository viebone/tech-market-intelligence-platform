import { ResponsivePie } from "@nivo/pie";
import { nivoTheme } from "./nivoTheme";

// Added 2026-09-22 (changes/2026-09-22-nivo-pie-charts.md) — for a real 2-category
// proportion (X vs. everything else, summing to a meaningful whole), not a coverage/
// completion percentage. See design/visual-design.md — Charting library: Meter stays the
// right form for "X% of Y have this property" (Story 3's salary-data coverage); this
// component is for "the population splits into exactly these categories" (disclosed vs.
// undisclosed, contraction vs. expansion, outside vs. inside the 3 tracked categories).

export interface ShareSlice {
  id: string;
  label: string;
  value: number;
  color: string;
}

interface SharePieChartProps {
  slices: ShareSlice[];
}

export function SharePieChart({ slices }: SharePieChartProps) {
  const total = slices.reduce((sum, s) => sum + s.value, 0);
  if (total <= 0) return null;

  return (
    <div style={{ height: 180 }}>
      <ResponsivePie
        data={slices}
        theme={nivoTheme}
        colors={{ datum: "data.color" }}
        innerRadius={0.6}
        padAngle={1.5}
        cornerRadius={2}
        margin={{ top: 10, right: 130, bottom: 10, left: 10 }}
        enableArcLinkLabels={false}
        arcLabel={(d) => `${Math.round((d.value / total) * 100)}%`}
        arcLabelsTextColor="#f3f4f6"
        isInteractive
        tooltip={({ datum }) => (
          <div className="rounded border border-gray-700 bg-gray-800 px-2 py-1 text-xs text-gray-100">
            {datum.label}: {datum.value.toLocaleString()} ({Math.round((datum.value / total) * 100)}%)
          </div>
        )}
        legends={[
          {
            anchor: "right",
            direction: "column",
            translateX: 100,
            itemWidth: 110,
            itemHeight: 20,
            itemsSpacing: 4,
            symbolSize: 10,
            symbolShape: "circle",
          },
        ]}
      />
    </div>
  );
}
