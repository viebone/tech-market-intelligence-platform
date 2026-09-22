import { ResponsiveBar } from "@nivo/bar";
import { RankedBarList } from "./RankedBarList";
import { nivoTheme } from "./nivoTheme";

// Replaces the hand-rolled ghost-bar comparison (YearOnYearBars.tsx, added 2026-09-10,
// removed 2026-09-22 — changes/2026-09-22-nivo-charting-library.md) with a real grouped bar
// chart: two 12-month windows, current vs. one year back — never more. Generic across
// role_category/level/track, same as its predecessor; a caller relabels row.value before
// this component ever sees it (see DataStoryMessage.tsx's role-mix-shift call site) rather
// than this component knowing about any one dimension's display names.
// See design/visual-design.md — Year-on-year comparison.

interface YoYWindow {
  start_date: string;
  end_date: string;
}

export interface YoYRow {
  value: string;
  current_count: number;
  current_share: number;
  prior_count: number | null;
  prior_share: number | null;
  delta_pp: number | null;
}

export interface YearOnYearContent {
  dimension: string;
  current_window: YoYWindow;
  prior_window: YoYWindow | null;
  comparison_available: boolean;
  rows: YoYRow[];
}

function monthYear(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString(undefined, {
    month: "short",
    year: "numeric",
  });
}

function WindowLine({ current, prior }: { current: YoYWindow; prior: YoYWindow | null }) {
  const cur = `${monthYear(current.start_date)} – ${monthYear(current.end_date)}`;
  return (
    <p className="mb-1 text-xs text-gray-500">
      {prior ? `${cur}, compared with the 12 months before it` : `${cur} — comparison window only`}
    </p>
  );
}

const CURRENT_COLOR = "#6366f1"; // indigo-500 — "now," the point of the block
const PRIOR_COLOR = "#4b5563"; // gray-600 — "a year ago," context only, never a role accent

interface Row {
  value: string;
  current: number;
  prior: number;
  delta: number | null;
}

export function YearOnYearGroupedBars({ content }: { content: YearOnYearContent }) {
  const { comparison_available, rows, current_window, prior_window } = content;

  // "No prior window yet" — same honesty state as before: the current window has real
  // data and is shown plainly, no ghost bar, no delta column.
  if (!comparison_available || rows.every((row) => row.delta_pp === null)) {
    return (
      <div>
        <WindowLine current={current_window} prior={null} />
        <RankedBarList
          rows={rows.map((row) => ({
            label: row.value,
            value: Math.round(row.current_share * 1000) / 10,
          }))}
          formatValue={(n) => `${n}%`}
        />
      </div>
    );
  }

  const data: Row[] = rows.map((row) => ({
    value: row.value,
    current: Math.round(row.current_share * 1000) / 10,
    prior: Math.round((row.prior_share ?? 0) * 1000) / 10,
    delta: row.delta_pp,
  }));

  return (
    <div>
      <WindowLine current={current_window} prior={prior_window} />
      <div style={{ height: Math.max(data.length * 40 + 40, 220) }}>
        <ResponsiveBar
          data={data as unknown as Record<string, string | number>[]}
          keys={["current", "prior"]}
          indexBy="value"
          layout="horizontal"
          groupMode="grouped"
          theme={nivoTheme}
          colors={[CURRENT_COLOR, PRIOR_COLOR]}
          padding={0.35}
          innerPadding={2}
          borderRadius={2}
          margin={{ top: 8, right: 24, bottom: 40, left: 150 }}
          valueFormat={(v) => `${v}%`}
          axisBottom={{
            legend: "Share of postings",
            legendPosition: "middle",
            legendOffset: 32,
          }}
          enableGridY={false}
          enableLabel={false}
          isInteractive
          tooltip={({ id, value, indexValue, data: rowData }) => {
            const delta = (rowData as unknown as Row).delta;
            return (
              <div className="rounded border border-gray-700 bg-gray-800 px-2 py-1 text-xs text-gray-100">
                <span className="font-medium">{indexValue as string}</span>
                <br />
                {id === "current" ? "Now" : "A year ago"}: {value}%
                {id === "current" && delta !== null ? (
                  <>
                    <br />
                    Change: {delta! >= 0 ? "+" : ""}
                    {delta!.toFixed(1)} pp
                  </>
                ) : null}
              </div>
            );
          }}
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
                { id: "current", label: "Now", color: CURRENT_COLOR },
                { id: "prior", label: "A year ago", color: PRIOR_COLOR },
              ],
            },
          ]}
        />
      </div>
    </div>
  );
}
