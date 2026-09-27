import { useMemo, useState } from "react";
import { ShowAsTable } from "./ShowAsTable";

// The spread of a value per entity — one row per role, a whisker (10th-90th percentile), a band
// (25th-75th), and a median dot. Added 2026-09-27 (changes/2026-09-26-data-story-chart-variety.md),
// for Story 3's pay-by-role block, replacing a Ranked bar list of the median alone (bars from
// zero exaggerated differences and hid the real spread this platform already stores). Hand-drawn
// SVG per the frontend spec's decision — no box-and-whisker form in the installed Nivo packages.
// See design/visual-design.md — Range chart.
//
// Rows arrive pre-ordered by median descending; this component never re-sorts them. The axis
// does NOT start at zero — position encodes the value and there's no bar length to distort, and
// the scale's own starting value is printed, both on the axis and in the how-to-read line the
// caller supplies (Chart accessibility standard).

export interface RangeChartRow {
  entityName: string;
  median: number;
  p10: number | null;
  p25: number | null;
  p75: number | null;
  p90: number | null;
  sampleSize: number | null;
  smallSample: boolean;
}

export interface RangeChartProps {
  rows: RangeChartRow[];
  formatValue: (n: number) => string;
  tableCaption: string;
}

const ROW_HEIGHT = 40;
const CHART_UNITS = 1000; // arbitrary SVG-space width for the value axis; real width comes from the container
const PRIMARY = "#6366f1"; // indigo-500

function niceStep(rawStep: number): number {
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const residual = rawStep / magnitude;
  const niceResidual = residual < 1.5 ? 1 : residual < 3 ? 2 : residual < 7 ? 5 : 10;
  return niceResidual * magnitude;
}

function domainAndTicks(rows: RangeChartRow[], tickCount = 4): { min: number; max: number; ticks: number[] } {
  const values = rows.flatMap((r) => [r.p10 ?? r.median, r.p90 ?? r.median, r.median]);
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const step = niceStep((rawMax - rawMin) / Math.max(tickCount - 1, 1)) || 1;
  const min = Math.floor(rawMin / step) * step;
  const max = Math.ceil(rawMax / step) * step;
  const ticks: number[] = [];
  for (let v = min; v <= max + step / 2; v += step) ticks.push(Math.round(v));
  return { min, max: max || 1, ticks };
}

function describeRow(row: RangeChartRow, fmt: (n: number) => string): string {
  const median = `median ${fmt(row.median)}`;
  const range = row.p10 != null && row.p90 != null
    ? `, middle 80% ${fmt(row.p10)} to ${fmt(row.p90)}, middle 50% ${fmt(row.p25 ?? row.median)} to ${fmt(row.p75 ?? row.median)}`
    : ", range not reported";
  const n = row.sampleSize != null ? `, based on ${row.sampleSize} salaries` : "";
  return `${row.entityName}: ${median}${range}${n}${row.smallSample ? " (small sample)" : ""}`;
}

export function RangeChart({ rows, formatValue, tableCaption }: RangeChartProps) {
  const [focused, setFocused] = useState(0);
  const { min, max, ticks } = useMemo(() => domainAndTicks(rows), [rows]);
  if (rows.length === 0) return null;

  const x = (v: number) => ((v - min) / (max - min)) * CHART_UNITS;
  const totalHeight = rows.length * ROW_HEIGHT;

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") { setFocused((i) => Math.min(i + 1, rows.length - 1)); e.preventDefault(); }
    else if (e.key === "ArrowUp") { setFocused((i) => Math.max(i - 1, 0)); e.preventDefault(); }
    else if (e.key === "Home") { setFocused(0); e.preventDefault(); }
    else if (e.key === "End") { setFocused(rows.length - 1); e.preventDefault(); }
  }

  return (
    <div>
      <div
        role="img"
        aria-label={`Salary range by role. ${describeRow(rows[focused], formatValue)}`}
        tabIndex={0}
        onKeyDown={onKeyDown}
        className="rounded outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
      >
        <div className="flex">
          <div className="flex flex-col" style={{ width: 140 }}>
            {rows.map((row) => (
              <div key={row.entityName} className="flex flex-col justify-center pr-2" style={{ height: ROW_HEIGHT }}>
                <span className="truncate text-sm text-gray-300" title={row.entityName}>
                  {row.entityName}
                </span>
                <span className="text-xs text-gray-400">
                  n = {row.sampleSize ?? "—"}
                  {row.smallSample ? " · small sample" : ""}
                </span>
              </div>
            ))}
          </div>
          <div className="relative flex-1">
            <svg
              width="100%"
              height={totalHeight}
              viewBox={`0 0 ${CHART_UNITS} ${totalHeight}`}
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              {rows.map((row, i) => {
                const cy = i * ROW_HEIGHT + ROW_HEIGHT / 2;
                const isFocused = i === focused;
                const hasRange = row.p10 != null && row.p90 != null;
                return (
                  <g key={row.entityName}>
                    {isFocused ? (
                      <rect x={0} y={i * ROW_HEIGHT} width={CHART_UNITS} height={ROW_HEIGHT} fill="#1f2937" />
                    ) : null}
                    {hasRange ? (
                      <>
                        <line x1={x(row.p10!)} x2={x(row.p90!)} y1={cy} y2={cy} stroke={PRIMARY} strokeWidth={2} />
                        <rect
                          x={x(row.p25 ?? row.p10!)}
                          width={Math.max(x(row.p75 ?? row.p90!) - x(row.p25 ?? row.p10!), 1)}
                          y={cy - 5}
                          height={10}
                          rx={2}
                          fill={PRIMARY}
                        />
                      </>
                    ) : null}
                    <circle
                      cx={x(row.median)}
                      cy={cy}
                      r={5}
                      fill={row.smallSample ? "#1f2937" : "#f3f4f6"}
                      stroke={row.smallSample ? "#f3f4f6" : "none"}
                      strokeWidth={row.smallSample ? 2 : 0}
                    />
                    {isFocused ? (
                      <circle cx={x(row.median)} cy={cy} r={9} fill="none" stroke="#818cf8" strokeWidth={2} />
                    ) : null}
                  </g>
                );
              })}
            </svg>
            <div className="mt-1 flex justify-between text-xs text-gray-400">
              {ticks.map((t) => (
                <span key={t}>{formatValue(t)}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <p aria-live="polite" className="sr-only">
        {describeRow(rows[focused], formatValue)}
      </p>

      <p className="mt-2 text-xs text-gray-400">
        Line: the middle 80% of advertised salaries (10th to 90th percentile). Bar: the middle
        50% (25th to 75th). Dot: the median.
        {rows.some((r) => r.smallSample) ? " Hollow dot: fewer than 30 salaries — indicative only." : ""}
      </p>

      <ShowAsTable
        caption={tableCaption}
        columns={["Role", "10th", "25th", "Median", "75th", "90th", "n"]}
        rows={rows.map((r) => [
          r.entityName,
          r.p10 != null ? formatValue(r.p10) : "—",
          r.p25 != null ? formatValue(r.p25) : "—",
          formatValue(r.median),
          r.p75 != null ? formatValue(r.p75) : "—",
          r.p90 != null ? formatValue(r.p90) : "—",
          r.sampleSize ?? "—",
        ])}
      />
    </div>
  );
}
