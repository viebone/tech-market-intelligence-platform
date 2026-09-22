import { ResponsiveBar } from "@nivo/bar";
import { nivoTheme } from "./nivoTheme";

// Added 2026-09-22 (changes/2026-09-22-nivo-charting-library.md) — replaces a single Ranked
// bar list that only distinguished must-have vs. nice-to-have by bar opacity (a difference
// most people never noticed) with a real grouped bar chart and an explicit legend. See
// design/market-health/data-stories.md — Story 1, "What employers ask for."

export interface SkillDemandRow {
  skill_group: string;
  must_have: number;
  nice_to_have: number;
}

interface SkillDemandChartProps {
  rows: SkillDemandRow[];
  limit?: number;
}

const MUST_HAVE_COLOR = "#6366f1"; // indigo-500 — same hue Ranked bar list used for this data
const NICE_TO_HAVE_COLOR = "#4b5563"; // gray-600 — muted, never confused with a role accent

export function SkillDemandChart({ rows, limit = 8 }: SkillDemandChartProps) {
  const shown = [...rows]
    .sort((a, b) => b.must_have + b.nice_to_have - (a.must_have + a.nice_to_have))
    .slice(0, limit);
  if (shown.length === 0) return null;

  return (
    <div style={{ height: Math.max(shown.length * 36 + 40, 220) }}>
      <ResponsiveBar
        data={shown as unknown as Record<string, string | number>[]}
        keys={["must_have", "nice_to_have"]}
        indexBy="skill_group"
        layout="horizontal"
        groupMode="grouped"
        theme={nivoTheme}
        colors={[MUST_HAVE_COLOR, NICE_TO_HAVE_COLOR]}
        padding={0.35}
        innerPadding={2}
        borderRadius={2}
        margin={{ top: 8, right: 24, bottom: 40, left: 170 }}
        axisBottom={{
          legend: "Postings mentioning",
          legendPosition: "middle",
          legendOffset: 32,
        }}
        enableGridY={false}
        enableGridX
        enableLabel={false}
        isInteractive
        tooltip={({ id, value, indexValue }) => (
          <div className="rounded border border-gray-700 bg-gray-800 px-2 py-1 text-xs text-gray-100">
            <span className="font-medium">{indexValue as string}</span>
            <br />
            {id === "must_have" ? "Must-have" : "Nice-to-have"}: {value.toLocaleString()}
          </div>
        )}
        legends={[
          {
            dataFrom: "keys",
            anchor: "bottom",
            direction: "row",
            translateY: 40,
            itemsSpacing: 16,
            itemWidth: 90,
            itemHeight: 14,
            symbolSize: 10,
            symbolShape: "circle",
            data: [
              { id: "must_have", label: "Must-have", color: MUST_HAVE_COLOR },
              { id: "nice_to_have", label: "Nice-to-have", color: NICE_TO_HAVE_COLOR },
            ],
          },
        ]}
      />
    </div>
  );
}
