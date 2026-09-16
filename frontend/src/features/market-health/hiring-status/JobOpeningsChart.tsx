import { useRef, useState, useCallback } from "react";

export type TimeRange = "six_months" | "this_year" | "past_5_years" | "all_time";
export type Granularity = "week" | "month";

export interface OpeningDataPoint {
  period: string;        // "YYYY-MM-DD" for week, "YYYY-MM" for month
  designer: number;
  product_manager: number;
  engineer: number;
}

interface JobOpeningsChartProps {
  data: OpeningDataPoint[];
  range: TimeRange;
  onRangeChange: (r: TimeRange) => void;
  granularity: Granularity;
  onGranularityChange: (g: Granularity) => void;
  isLoading?: boolean;
}

// ─── visual config ────────────────────────────────────────────────────────────

const RANGES: { value: TimeRange; label: string }[] = [
  { value: "six_months",    label: "6 Months" },
  { value: "this_year",    label: "This Year" },
  { value: "past_5_years", label: "Past 5 Years" },
  { value: "all_time",     label: "All Time" },
];

const GRANULARITIES: { value: Granularity; label: string }[] = [
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
];

const SERIES = [
  { key: "designer"        as keyof OpeningDataPoint, label: "Designer",           color: "#6366f1" },
  { key: "product_manager" as keyof OpeningDataPoint, label: "Product Manager",    color: "#a855f7" },
  { key: "engineer"        as keyof OpeningDataPoint, label: "Engineer",           color: "#10b981" },
] as const;

const PAD = { top: 20, right: 16, bottom: 52, left: 68 };
const SVG_H = 280;

// ─── helpers ──────────────────────────────────────────────────────────────────

// A month period is "YYYY-MM"; append a day so `Date` can parse it
// (`new Date("2026-08T00:00:00")` is Invalid Date).
function periodToDate(period: string): Date {
  const iso = period.length === 7 ? `${period}-01` : period;
  return new Date(`${iso}T00:00:00`);
}

function formatPeriod(period: string, granularity: Granularity): string {
  return periodToDate(period).toLocaleString("default", granularity === "week"
    ? { month: "short", day: "numeric", year: "2-digit" }
    : { month: "short", year: "2-digit" });
}

function formatPeriodShort(period: string, granularity: Granularity): string {
  return periodToDate(period).toLocaleString("default", granularity === "week"
    ? { month: "short", day: "numeric" }
    : { month: "short" });
}

function getYear(period: string): string {
  return period.slice(0, 4);
}

function niceTicks(min: number, max: number, count = 4): number[] {
  const range = max - min;
  if (!(range > 0)) return [Math.round(min)];
  const step = Math.pow(10, Math.floor(Math.log10(range / count)));
  const niceStep = [1, 2, 2.5, 5, 10].map(f => f * step).find(s => range / s <= count + 1) ?? step;
  const start = Math.ceil(min / niceStep) * niceStep;
  const ticks: number[] = [];
  for (let v = start; v <= max + niceStep * 0.01; v += niceStep) ticks.push(Math.round(v));
  return Array.from(new Set(ticks));
}

function formatCount(n: number): string {
  return n >= 1000 ? `${(n / 1000).toFixed(n % 1000 === 0 ? 0 : 1)}k` : String(n);
}

// ─── component ────────────────────────────────────────────────────────────────

export function JobOpeningsChart({ data, range, onRangeChange, granularity, onGranularityChange, isLoading }: JobOpeningsChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const [tooltipX, setTooltipX] = useState(0);
  const [svgWidth, setSvgWidth] = useState(600);

  // measure rendered width
  const measuredRef = useCallback((node: SVGSVGElement | null) => {
    if (!node) return;
    const ro = new ResizeObserver(entries => {
      setSvgWidth(entries[0].contentRect.width);
    });
    ro.observe(node);
  }, []);

  const drawW = svgWidth - PAD.left - PAD.right;
  const drawH = SVG_H - PAD.top - PAD.bottom;

  // ── data ranges ──────────────────────────────────────────────────────────

  const allValues = data.flatMap(d => [d.designer, d.product_manager, d.engineer]);
  const dataMin = allValues.length ? Math.min(...allValues) : 0;
  const dataMax = allValues.length ? Math.max(...allValues) : 1000;
  const yPad = (dataMax - dataMin) * 0.08;
  let yMin = Math.max(0, dataMin - yPad);
  let yMax = dataMax + yPad;
  // Flat series or a single bucket: the value span is zero. Give the axis a
  // readable range so lines render instead of collapsing to NaN.
  if (yMax - yMin < 1) {
    const mid = (yMax + yMin) / 2;
    yMin = Math.max(0, Math.floor(mid - 1));
    yMax = Math.ceil(mid + 1);
    if (yMax === yMin) yMax = yMin + 1;
  }

  function toX(i: number) {
    if (data.length <= 1) return PAD.left + drawW / 2;
    return PAD.left + (i / (data.length - 1)) * drawW;
  }
  function toY(v: number) {
    return PAD.top + drawH - ((v - yMin) / (yMax - yMin)) * drawH;
  }

  // ── X axis labels ────────────────────────────────────────────────────────

  function xLabels(): { idx: number; label: string }[] {
    if (data.length === 0) return [];
    if (range === "six_months" || range === "this_year") {
      // Thin to a handful of evenly spaced labels so dense weekly views don't
      // overlap into mush. The line itself still uses every bucket.
      const MAX_LABELS = 8;
      if (data.length <= MAX_LABELS) {
        return data.map((d, i) => ({ idx: i, label: formatPeriodShort(d.period, granularity) }));
      }
      const stride = Math.ceil(data.length / MAX_LABELS);
      const labels: { idx: number; label: string }[] = [];
      for (let i = 0; i < data.length; i += stride) {
        labels.push({ idx: i, label: formatPeriodShort(data[i].period, granularity) });
      }
      const lastIdx = data.length - 1;
      if (labels[labels.length - 1].idx !== lastIdx) {
        labels.push({ idx: lastIdx, label: formatPeriodShort(data[lastIdx].period, granularity) });
      }
      return labels;
    }
    // Longer ranges: one label per calendar year, at that year's first bucket.
    // (Don't test for a period ending in "-01" — Monday-anchored week keys
    // almost never do, which left long weekly views with no labels at all.)
    const seen = new Set<string>();
    const labels: { idx: number; label: string }[] = [];
    data.forEach((d, i) => {
      const year = getYear(d.period);
      if (!seen.has(year)) {
        seen.add(year);
        labels.push({ idx: i, label: year });
      }
    });
    return labels;
  }

  // ── Y axis ticks ─────────────────────────────────────────────────────────

  const yTicks = data.length ? niceTicks(yMin, yMax, 4) : [];

  // ── polyline paths ───────────────────────────────────────────────────────

  function buildPath(key: keyof OpeningDataPoint): string {
    if (data.length === 0) return "";
    return data
      .map((d, i) => `${i === 0 ? "M" : "L"}${toX(i).toFixed(1)},${toY(d[key] as number).toFixed(1)}`)
      .join(" ");
  }

  // ── hover handling ───────────────────────────────────────────────────────

  function onMouseMove(e: React.MouseEvent<SVGSVGElement>) {
    if (data.length === 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const relX = mouseX - PAD.left;
    const rawIdx = (relX / drawW) * (data.length - 1);
    const idx = Math.round(Math.max(0, Math.min(data.length - 1, rawIdx)));
    setHoverIdx(idx);
    setTooltipX(toX(idx));
  }

  function onMouseLeave() {
    setHoverIdx(null);
  }

  const hovered = hoverIdx !== null ? data[hoverIdx] : null;

  // tooltip position: flip to left side when near right edge
  const tooltipOnLeft = hoverIdx !== null && (hoverIdx / Math.max(data.length - 1, 1)) > 0.6;

  // ── render ───────────────────────────────────────────────────────────────

  return (
    <div ref={containerRef} className="flex flex-col gap-3">

      {/* Title row: heading left, time range tabs right */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-100">Tech hiring demand</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {granularity === "week" ? "Weekly" : "Monthly"} job openings by role category
          </p>
        </div>
          <div className="flex items-center gap-2 shrink-0">
            <label className="flex items-center gap-1.5 text-xs text-gray-500">
              <span>Range</span>
              <select
                value={range}
                onChange={(event) => onRangeChange(event.target.value as TimeRange)}
                className="rounded-md border border-gray-700 bg-gray-800 px-2 py-1.5 text-xs text-gray-200 outline-none focus:border-gray-500"
                aria-label="Time range"
              >
                {RANGES.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-1.5 text-xs text-gray-500">
              <span>View</span>
              <select
                value={granularity}
                onChange={(event) => onGranularityChange(event.target.value as Granularity)}
                className="rounded-md border border-gray-700 bg-gray-800 px-2 py-1.5 text-xs text-gray-200 outline-none focus:border-gray-500"
                aria-label="Chart granularity"
              >
                {GRANULARITIES.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-5">
        {SERIES.map(s => (
          <span key={s.key} className="flex items-center gap-1.5 text-xs text-gray-400">
            <span className="inline-block w-3 h-0.5 rounded-full" style={{ backgroundColor: s.color }} />
            {s.label}
          </span>
        ))}
      </div>

      {/* Chart */}
      <div className="relative select-none">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900/60 rounded-lg z-10">
            <div className="flex gap-1" role="status" aria-label="Loading chart">
              {[0, 1, 2].map(i => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 150}ms` }}
                />
              ))}
            </div>
          </div>
        )}

        {!isLoading && data.length === 1 && (
          <div className="absolute inset-x-0 bottom-14 flex justify-center z-10 px-6">
            <p className="text-xs text-gray-400 bg-gray-900/80 rounded-md px-3 py-1.5 text-center">
              One complete {granularity === "week" ? "week" : "month"} of data so far
              ({formatPeriod(data[0].period, granularity)}). The trend line needs at least two.
            </p>
          </div>
        )}

        <svg
          ref={measuredRef}
          width="100%"
          height={SVG_H}
          viewBox={`0 0 ${svgWidth} ${SVG_H}`}
          onMouseMove={onMouseMove}
          onMouseLeave={onMouseLeave}
          className="overflow-visible cursor-crosshair"
          aria-label="Job openings trend chart"
          role="img"
        >
          {/* Y axis label — rotated, left of tick values */}
          <text
            transform="rotate(-90)"
            x={-(PAD.top + drawH / 2)}
            y={16}
            textAnchor="middle"
            className="fill-gray-500"
            style={{ fontSize: 10 }}
          >
            Openings
          </text>

          {/* X axis label — centred below tick marks */}
          <text
            x={PAD.left + drawW / 2}
            y={SVG_H - 6}
            textAnchor="middle"
            className="fill-gray-500"
            style={{ fontSize: 10 }}
          >
            {granularity === "week" ? "Week" : "Month"}
          </text>

          {/* Y grid lines + labels */}
          {yTicks.map(tick => {
            const y = toY(tick);
            return (
              <g key={tick}>
                <line
                  x1={PAD.left} y1={y}
                  x2={PAD.left + drawW} y2={y}
                  stroke="#374151" strokeWidth="1"
                />
                <text
                  x={PAD.left - 8} y={y}
                  textAnchor="end" dominantBaseline="middle"
                  className="fill-gray-500" style={{ fontSize: 10 }}
                >
                  {formatCount(tick)}
                </text>
              </g>
            );
          })}

          {/* X axis labels */}
          {xLabels().map(({ idx, label }) => (
            <text
              key={idx}
              x={toX(idx)} y={SVG_H - PAD.bottom + 14}
              textAnchor="middle"
              className="fill-gray-500" style={{ fontSize: 10 }}
            >
              {label}
            </text>
          ))}

          {/* Series lines */}
          {SERIES.map(s => (
            <path
              key={s.key}
              d={buildPath(s.key)}
              fill="none"
              stroke={s.color}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={isLoading ? 0.3 : 1}
            />
          ))}

          {/* Single bucket: a line has nothing to draw — mark the point. */}
          {data.length === 1 && SERIES.map(s => (
            <circle
              key={`point-${s.key}`}
              cx={toX(0)}
              cy={toY(data[0][s.key] as number)}
              r="3.5"
              fill={s.color}
              opacity={isLoading ? 0.3 : 1}
            />
          ))}

          {/* Hover cursor */}
          {hoverIdx !== null && (
            <>
              <line
                x1={tooltipX} y1={PAD.top}
                x2={tooltipX} y2={PAD.top + drawH}
                stroke="#6b7280" strokeWidth="1" strokeDasharray="4 3"
              />
              {/* Dots at each series */}
              {SERIES.map(s => hovered && (
                <circle
                  key={s.key}
                  cx={tooltipX}
                  cy={toY(hovered[s.key] as number)}
                  r="4"
                  fill={s.color}
                  stroke="#111827"
                  strokeWidth="2"
                />
              ))}
            </>
          )}
        </svg>

        {/* Tooltip */}
        {hovered && hoverIdx !== null && (
          <div
            className="pointer-events-none absolute top-4 z-20 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 shadow-xl"
            style={{
              left: tooltipOnLeft
                ? `${tooltipX - PAD.left - 8}px`
                : `${tooltipX - PAD.left + 12}px`,
              transform: tooltipOnLeft ? "translateX(-100%)" : undefined,
              minWidth: 148,
            }}
          >
            <p className="text-xs text-gray-400 mb-1.5 font-medium">
                {formatPeriod(hovered.period, granularity)}
            </p>
            {SERIES.map(s => (
              <div key={s.key} className="flex items-center justify-between gap-4">
                <span className="flex items-center gap-1.5 text-xs text-gray-300">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
                  {s.label}
                </span>
                <span className="text-xs font-medium text-white tabular-nums">
                  {(hovered[s.key] as number).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
