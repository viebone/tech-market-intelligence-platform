import { ResponsiveBar } from "@nivo/bar";
import { nivoTheme } from "./nivoTheme";
import { ShowAsTable } from "./ShowAsTable";

// Added 2026-09-22 (changes/2026-09-22-nivo-charting-library.md) — replaces a single Ranked
// bar list that only distinguished must-have vs. nice-to-have by bar opacity (a difference
// most people never noticed) with a real grouped bar chart and an explicit legend. See
// design/market-health/data-stories.md — Story 1, "What employers ask for."
//
// Revised 2026-10-23 (changes/2026-10-10-requirements-extraction-sampling.md; frontend spec —
// Sampling and the method text). Values are ESTIMATED % OF POSTINGS, read from a fair sample —
// never raw counts of sampled postings, which would understate the market. The one exception is
// `unit: "count"`: a slice of under 10 postings where every one was read shows plain counts
// ("3 of 8 postings"), because shares of a handful read as more precise than they are. The
// estimate's own wording (n of N, ± pts) lives in the block's qualifier, never written here.

export interface SkillDemandRow {
  skill_group: string;
  must_have: number;
  nice_to_have: number;
}

interface SkillDemandChartProps {
  rows: SkillDemandRow[];
  /** "pct" (default): estimated % of postings. "count": plain postings, every one read. */
  unit?: "pct" | "count";
  /** Total postings in the slice, for "count" labels ("3 of 8 postings"). */
  population?: number;
  /** The block's estimate qualifier, shown as the table's caption. */
  tableCaption: string;
  limit?: number;
}

const MUST_HAVE_COLOR = "#6366f1"; // indigo-500 — same hue Ranked bar list used for this data
const NICE_TO_HAVE_COLOR = "#4b5563"; // gray-600 — muted, never confused with a role accent

export function SkillDemandChart({ rows, unit = "pct", population, tableCaption, limit = 8 }: SkillDemandChartProps) {
  const shown = [...rows]
    .sort((a, b) => b.must_have + b.nice_to_have - (a.must_have + a.nice_to_have))
    .slice(0, limit);
  if (shown.length === 0) return null;

  const fmt = (value: number) =>
    unit === "pct" ? `${Math.round(value)}%` : `${value.toLocaleString()}${population ? ` of ${population.toLocaleString()}` : ""} postings`;

  return (
    <>
      <div style={{ height: Math.max(shown.length * 36 + 72, 250) }}>
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
          margin={{ top: 8, right: 24, bottom: 72, left: 220 }}
          axisBottom={{
            legend: unit === "pct" ? "% of postings" : "Postings",
            legendPosition: "middle",
            legendOffset: 32,
            format: (v) => (unit === "pct" ? `${v}%` : `${v}`),
          }}
          // Long group names would clip at the chart edge — shorten on the axis only; the full
          // name is in the tooltip and the "Show as table" view.
          axisLeft={{ format: (v) => (String(v).length > 32 ? `${String(v).slice(0, 31)}…` : String(v)) }}
          enableGridY={false}
          enableGridX
          enableLabel={false}
          isInteractive
          tooltip={({ id, value, indexValue }) => (
            <div className="rounded border border-gray-700 bg-gray-800 px-2 py-1 text-xs text-gray-100">
              <span className="font-medium">{indexValue as string}</span>
              <br />
              {id === "must_have" ? "Must-have" : "Nice-to-have"}: {fmt(value)}
              {unit === "pct" ? " of postings" : ""}
            </div>
          )}
          legends={[
            {
              dataFrom: "keys",
              anchor: "bottom",
              direction: "row",
              translateY: 66,
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
      <ShowAsTable
        caption={tableCaption}
        columns={["Skill group", unit === "pct" ? "Must-have (% of postings)" : "Must-have (postings)",
          unit === "pct" ? "Nice-to-have (% of postings)" : "Nice-to-have (postings)"]}
        rows={shown.map((r) => [r.skill_group, fmt(r.must_have), fmt(r.nice_to_have)])}
      />
    </>
  );
}
