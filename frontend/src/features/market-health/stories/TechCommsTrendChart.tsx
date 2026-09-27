import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent, MouseEvent } from "react";

// Story 5, block 4a — "Tech and communications vacancies since 2001". Hand-rolled inline SVG, not
// Nivo: @nivo/line isn't installed, and this block needs a per-series dash pattern, a conditionally
// hollow marker, and exact-point keyboard stepping with an announced tooltip — more than Nivo gives
// without fighting its API (the same call Story 5 already made once for its delta glyphs, and the
// World risk map made for its own SVG). See frontend/specs/market-health/architecture.md — Story 5,
// "Block 4a", and design/visual-design.md — Time series / Chart accessibility standard.
// changes/2026-09-26-story-5-tech-lens.md.
//
// Rules this component enforces:
//  - Every value shown here (points, peak, latest, table rows) comes straight from the API —
//    nothing is computed or re-based client-side (the index is a server-computed presentation of
//    published levels).
//  - Colour is never the only signal: the comparator line is dashed as well as a different colour,
//    and the latest point is drawn hollow (not just recoloured) when it's provisional.
//  - No event/recession shading or causal wording anywhere — only the two data-derived markers
//    (peak, latest) are annotated.

type SeriesPoint = { value: number; index: number; status: "final" | "provisional" | "revised" };

export interface TrendPoint {
  periodStart: string; // ISO date — x-position only, never rendered
  label: string; // "Apr–Jun 2001" — pre-formatted (en dash) by the API
  words: string; // "three months to Jun 2001"
  group: SeriesPoint;
  all: SeriesPoint;
}

interface TechCommsTrendChartProps {
  points: TrendPoint[];
  groupLabel: string;
  yAxisTitle: string;
  peak: { periodLabel: string; value: number; index: number };
  latest: { periodLabel: string; periodWords: string; provisional: boolean };
  legend: string;
  ariaLabel: string;
  summary: string;
  table: {
    caption: string;
    rows: Array<{ periodLabel: string; groupValue: number; allValue: number; groupIndex: number; allIndex: number }>;
  };
}

const GROUP_COLOR = "#6366f1"; // indigo-500 — the industry group
const COMPARATOR_COLOR = "#9ca3af"; // gray-400 — Chart accessibility standard's muted-series colour (gray-500 is retired)
const AXIS_COLOR = "#374151"; // gray-700
const TEXT_COLOR = "#9ca3af"; // gray-400
const SURFACE_COLOR = "#1f2937"; // gray-800 — fill for a hollow (provisional) marker
const FOCUS_COLOR = "#818cf8"; // indigo-400 — visible focus ring

const VIEW_W = 640;
const VIEW_H = 220;
const MARGIN = { top: 14, right: 12, bottom: 24, left: 12 };
const PLOT_W = VIEW_W - MARGIN.left - MARGIN.right;
const PLOT_H = VIEW_H - MARGIN.top - MARGIN.bottom;
const Y_MAX = 200;
const NARROW_WIDTH = 480;
// A real gap between these monthly-rolling three-month periods would be far larger than the ~28-31
// day step between them — this threshold is generous on purpose (none exists in the data today,
// but the line should never silently join across one if it ever did).
const GAP_THRESHOLD_DAYS = 45;

function toTs(periodStart: string): number {
  return new Date(periodStart).getTime();
}

function xPos(ts: number, minTs: number, maxTs: number): number {
  const span = maxTs - minTs || 1;
  return MARGIN.left + ((ts - minTs) / span) * PLOT_W;
}

function yPos(index: number): number {
  const clamped = Math.max(0, Math.min(index, Y_MAX));
  return MARGIN.top + (1 - clamped / Y_MAX) * PLOT_H;
}

/** Splits the series into contiguous runs — a real gap breaks the line, never interpolated. */
function segments(points: TrendPoint[]): TrendPoint[][] {
  const out: TrendPoint[][] = [];
  let current: TrendPoint[] = [];
  let prevTs: number | null = null;
  for (const p of points) {
    const ts = toTs(p.periodStart);
    if (prevTs !== null && (ts - prevTs) / 86_400_000 > GAP_THRESHOLD_DAYS) {
      if (current.length) out.push(current);
      current = [];
    }
    current.push(p);
    prevTs = ts;
  }
  if (current.length) out.push(current);
  return out;
}

function pathFrom(points: TrendPoint[], minTs: number, maxTs: number, pick: (p: TrendPoint) => number): string {
  return segments(points)
    .map((seg) =>
      seg
        .map((p, i) => `${i === 0 ? "M" : "L"}${xPos(toTs(p.periodStart), minTs, maxTs).toFixed(1)},${yPos(pick(p)).toFixed(1)}`)
        .join(" "),
    )
    .join(" ");
}

function capitalize(text: string): string {
  return text.length ? text.charAt(0).toUpperCase() + text.slice(1) : text;
}

function statusFlag(a: SeriesPoint, b: SeriesPoint): string {
  if (a.status === "provisional" || b.status === "provisional") return " — first estimate, may be revised";
  if (a.status === "revised" || b.status === "revised") return " — revised";
  return "";
}

function useContainerWidth() {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(VIEW_W);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) setWidth(entry.contentRect.width);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return { ref, width };
}

export function TechCommsTrendChart({
  points,
  groupLabel,
  yAxisTitle,
  peak,
  latest,
  legend,
  ariaLabel,
  summary,
  table,
}: TechCommsTrendChartProps) {
  const { ref: containerRef, width: containerWidth } = useContainerWidth();
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null);
  const [showTable, setShowTable] = useState(false);
  const narrow = containerWidth < NARROW_WIDTH;

  if (points.length === 0) return null;

  const timestamps = points.map((p) => toTs(p.periodStart));
  const minTs = Math.min(...timestamps);
  const maxTs = Math.max(...timestamps);
  const groupPath = pathFrom(points, minTs, maxTs, (p) => p.group.index);
  const allPath = pathFrom(points, minTs, maxTs, (p) => p.all.index);

  const peakPoint = points.find((p) => p.label === peak.periodLabel) ?? points[points.length - 1];
  const latestPoint = points[points.length - 1];
  const peakPos = { x: xPos(toTs(peakPoint.periodStart), minTs, maxTs), y: yPos(peakPoint.group.index) };
  const latestPos = { x: xPos(toTs(latestPoint.periodStart), minTs, maxTs), y: yPos(latestPoint.group.index) };

  // Year ticks: every 5 years (every 10 on a narrow panel), always including the first and last.
  const years = Array.from(new Set(points.map((p) => new Date(p.periodStart).getUTCFullYear())));
  const tickEvery = narrow ? 10 : 5;
  const firstYear = years[0];
  const lastYear = years[years.length - 1];
  const yearTicks = years.filter((yr) => yr === firstYear || yr === lastYear || yr % tickEvery === 0);

  const focused = focusedIndex !== null ? points[focusedIndex] : null;
  const announcement = focused
    ? `${capitalize(focused.words)} — ${groupLabel}: ${focused.group.value.toLocaleString()} thousand vacancies (index ${focused.group.index}) ` +
     `· All industries: ${focused.all.value.toLocaleString()} thousand (index ${focused.all.index})${statusFlag(focused.group, focused.all)}`
    : "";

  function moveFocus(delta: number) {
    setFocusedIndex((current) => {
      const base = current ?? points.length - 1;
      return Math.max(0, Math.min(points.length - 1, base + delta));
    });
  }

  function onKeyDown(e: KeyboardEvent<SVGSVGElement>) {
    if (e.key === "ArrowRight") { e.preventDefault(); moveFocus(1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); moveFocus(-1); }
    else if (e.key === "Home") { e.preventDefault(); setFocusedIndex(0); }
    else if (e.key === "End") { e.preventDefault(); setFocusedIndex(points.length - 1); }
  }

  function onMouseMove(e: MouseEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    if (rect.width === 0) return;
    const relX = ((e.clientX - rect.left) / rect.width) * VIEW_W;
    let nearest = 0;
    let nearestDist = Infinity;
    points.forEach((p, i) => {
      const dist = Math.abs(xPos(toTs(p.periodStart), minTs, maxTs) - relX);
      if (dist < nearestDist) { nearestDist = dist; nearest = i; }
    });
    setFocusedIndex(nearest);
  }

  const groupEndLabel = `${groupLabel} ${latestPoint.group.index} (${latestPoint.group.value.toLocaleString()} thousand vacancies)`;
  const allEndLabel = `All industries ${latestPoint.all.index} (${latestPoint.all.value.toLocaleString()} thousand vacancies)`;

  return (
    <div>
      {!narrow ? <p className="mb-2 text-xs text-gray-400">{legend}</p> : null}
      <div ref={containerRef}>
        <svg
          viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
          role="img"
          aria-label={ariaLabel}
          tabIndex={0}
          onKeyDown={onKeyDown}
          onMouseMove={onMouseMove}
          onMouseLeave={() => setFocusedIndex(null)}
          className="w-full rounded outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
        >
          <text x={MARGIN.left} y={10} fontSize={11} fill={TEXT_COLOR}>
            {yAxisTitle}
          </text>
          <line x1={MARGIN.left} x2={VIEW_W - MARGIN.right} y1={yPos(100)} y2={yPos(100)} stroke={AXIS_COLOR} strokeWidth={1} />
          <text x={VIEW_W - MARGIN.right} y={yPos(100) - 3} fontSize={10} fill={TEXT_COLOR} textAnchor="end">
            100
          </text>
          {yearTicks.map((yr) => {
            const point = points.find((p) => new Date(p.periodStart).getUTCFullYear() === yr);
            if (!point) return null;
            const tickX = xPos(toTs(point.periodStart), minTs, maxTs);
            return (
              <g key={yr}>
                <line x1={tickX} x2={tickX} y1={VIEW_H - MARGIN.bottom} y2={VIEW_H - MARGIN.bottom + 4} stroke={AXIS_COLOR} strokeWidth={1} />
                <text x={tickX} y={VIEW_H - MARGIN.bottom + 15} fontSize={11} fill={TEXT_COLOR} textAnchor="middle">
                  {yr}
                </text>
              </g>
            );
          })}
          <path d={allPath} fill="none" stroke={COMPARATOR_COLOR} strokeWidth={2} strokeDasharray="4 3" />
          <path d={groupPath} fill="none" stroke={GROUP_COLOR} strokeWidth={2} />
          <circle cx={peakPos.x} cy={peakPos.y} r={4} fill={GROUP_COLOR} />
          <text x={peakPos.x} y={Math.max(peakPos.y - 8, 20)} fontSize={10} fill={TEXT_COLOR} textAnchor="middle">
            {`Highest: ${peak.periodLabel}, ${peak.value.toLocaleString()} thousand`}
          </text>
          <circle
            cx={latestPos.x}
            cy={latestPos.y}
            r={4}
            fill={latest.provisional ? SURFACE_COLOR : GROUP_COLOR}
            stroke={GROUP_COLOR}
            strokeWidth={latest.provisional ? 2 : 0}
          />
          {!narrow ? (
            <>
              <text x={VIEW_W - MARGIN.right} y={Math.max(yPos(latestPoint.group.index) - 6, 20)} fontSize={10} fill={GROUP_COLOR} textAnchor="end">
                {groupEndLabel}
              </text>
              <text x={VIEW_W - MARGIN.right} y={Math.min(yPos(latestPoint.all.index) + 14, VIEW_H - MARGIN.bottom - 4)} fontSize={10} fill={COMPARATOR_COLOR} textAnchor="end">
                {allEndLabel}
              </text>
            </>
          ) : null}
          {focused ? (
            <circle
              cx={xPos(toTs(focused.periodStart), minTs, maxTs)}
              cy={yPos(focused.group.index)}
              r={6}
              fill="none"
              stroke={FOCUS_COLOR}
              strokeWidth={2}
            />
          ) : null}
        </svg>
      </div>
      {narrow ? <p className="mt-2 text-xs text-gray-400">{legend}</p> : null}
      {/* Hover-only information does not exist: the same text is announced on keyboard focus. */}
      <div aria-live="polite" className="sr-only">
        {announcement}
      </div>
      <p className="mt-2 text-sm text-gray-400">{summary}</p>
      <button
        type="button"
        onClick={() => setShowTable((v) => !v)}
        className="mt-2 min-h-[24px] text-xs text-gray-400 underline decoration-dotted underline-offset-2 hover:text-gray-300"
      >
        {showTable ? "Hide table" : "Show as table"}
      </button>
      {showTable ? (
        <table className="mt-2 w-full border-collapse text-xs text-gray-400">
          <caption className="mb-1 text-left">{table.caption}</caption>
          <thead>
            <tr className="border-b border-gray-800 text-gray-300">
              <th className="py-1 text-left font-medium">Period</th>
              <th className="py-1 text-right font-medium">{groupLabel} (thousand)</th>
              <th className="py-1 text-right font-medium">All industries (thousand)</th>
              <th className="py-1 text-right font-medium">{groupLabel} index</th>
              <th className="py-1 text-right font-medium">All industries index</th>
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row) => (
              <tr key={row.periodLabel} className="border-b border-gray-800/60">
                <td className="py-1">{row.periodLabel}</td>
                <td className="py-1 text-right tabular-nums">{row.groupValue.toLocaleString()}</td>
                <td className="py-1 text-right tabular-nums">{row.allValue.toLocaleString()}</td>
                <td className="py-1 text-right tabular-nums">{row.groupIndex.toLocaleString()}</td>
                <td className="py-1 text-right tabular-nums">{row.allIndex.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}
