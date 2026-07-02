import { useCallback, useState } from "react";

interface LocationDataPoint {
  location: string;
  ux: number;
  pm: number;
}

// June 2026 totals: Senior + Mid combined per location
// Derived from mock_data.py DEMAND_SIGNALS
const DATA: LocationDataPoint[] = [
  { location: "London",   ux: 528, pm: 453 },
  { location: "New York", ux: 695, pm: 900 },
  { location: "Remote",   ux: 560, pm: 327 },
];

const UX_COLOR = "#6366f1"; // indigo-500 — consistent with briefing chart
const PM_COLOR = "#a855f7"; // purple-500 — consistent with briefing chart

const PAD = { top: 24, right: 24, bottom: 56, left: 64 };
const SVG_H = 240;
const BAR_GAP = 4;  // gap between the two bars within a group

function niceTicks(max: number, count = 4): number[] {
  const step = Math.pow(10, Math.floor(Math.log10(max / count)));
  const niceStep =
    [1, 2, 2.5, 5, 10].map((f) => f * step).find((s) => max / s <= count + 1) ??
    step;
  const ticks: number[] = [];
  for (let v = 0; v <= max + niceStep * 0.01; v += niceStep)
    ticks.push(Math.round(v));
  return ticks;
}

function formatCount(n: number): string {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n);
}

export function UXvsPMChart() {
  const [svgWidth, setSvgWidth] = useState(600);
  const [hoveredGroup, setHoveredGroup] = useState<number | null>(null);

  const measuredRef = useCallback((node: SVGSVGElement | null) => {
    if (!node) return;
    const ro = new ResizeObserver((entries) => {
      setSvgWidth(entries[0].contentRect.width);
    });
    ro.observe(node);
  }, []);

  const drawW = svgWidth - PAD.left - PAD.right;
  const drawH = SVG_H - PAD.top - PAD.bottom;

  const allValues = DATA.flatMap((d) => [d.ux, d.pm]);
  const dataMax = Math.max(...allValues);
  const yMax = dataMax * 1.12;

  const yTicks = niceTicks(yMax, 4);

  const groupW = drawW / DATA.length;
  const barW = Math.min(groupW * 0.28, 52);

  function groupX(i: number) {
    return PAD.left + i * groupW + groupW / 2;
  }

  function barX(groupIdx: number, isUX: boolean) {
    const cx = groupX(groupIdx);
    return isUX ? cx - BAR_GAP / 2 - barW : cx + BAR_GAP / 2;
  }

  function toY(v: number) {
    return PAD.top + drawH - (v / yMax) * drawH;
  }

  function barH(v: number) {
    return (v / yMax) * drawH;
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div>
        <h3 className="text-sm font-semibold text-gray-100">
          UX Design vs Product Management — job openings by location
        </h3>
        <p className="text-xs text-gray-400 mt-0.5">
          Total openings (Mid + Senior combined) · June 2026
        </p>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-5">
        {[
          { color: UX_COLOR, label: "UX Design" },
          { color: PM_COLOR, label: "Product Management" },
        ].map(({ color, label }) => (
          <span key={label} className="flex items-center gap-1.5 text-xs text-gray-400">
            <span
              className="inline-block w-2.5 h-2.5 rounded-sm"
              style={{ backgroundColor: color }}
            />
            {label}
          </span>
        ))}
      </div>

      {/* Chart */}
      <div className="relative select-none">
        <svg
          ref={measuredRef}
          width="100%"
          height={SVG_H}
          viewBox={`0 0 ${svgWidth} ${SVG_H}`}
          className="overflow-visible"
          aria-label="UX Design vs Product Management job openings by location"
          role="img"
          onMouseLeave={() => setHoveredGroup(null)}
        >
          {/* Y axis label */}
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

          {/* Y grid lines + labels */}
          {yTicks.map((tick) => {
            const y = toY(tick);
            return (
              <g key={tick}>
                <line
                  x1={PAD.left}
                  y1={y}
                  x2={PAD.left + drawW}
                  y2={y}
                  stroke="#374151"
                  strokeWidth="1"
                />
                <text
                  x={PAD.left - 8}
                  y={y}
                  textAnchor="end"
                  dominantBaseline="middle"
                  className="fill-gray-500"
                  style={{ fontSize: 10 }}
                >
                  {formatCount(tick)}
                </text>
              </g>
            );
          })}

          {/* Bars + X labels */}
          {DATA.map((d, i) => {
            const isHovered = hoveredGroup === i;
            const uxX = barX(i, true);
            const pmX = barX(i, false);
            const uxH = barH(d.ux);
            const pmH = barH(d.pm);
            const uxY = toY(d.ux);
            const pmY = toY(d.pm);

            return (
              <g
                key={d.location}
                onMouseEnter={() => setHoveredGroup(i)}
                style={{ cursor: "default" }}
              >
                {/* Hover zone */}
                <rect
                  x={PAD.left + i * groupW}
                  y={PAD.top}
                  width={groupW}
                  height={drawH}
                  fill="transparent"
                />

                {/* UX bar */}
                <rect
                  x={uxX}
                  y={uxY}
                  width={barW}
                  height={uxH}
                  fill={UX_COLOR}
                  opacity={isHovered ? 1 : 0.8}
                  rx={2}
                />

                {/* PM bar */}
                <rect
                  x={pmX}
                  y={pmY}
                  width={barW}
                  height={pmH}
                  fill={PM_COLOR}
                  opacity={isHovered ? 1 : 0.8}
                  rx={2}
                />

                {/* Value labels on hover */}
                {isHovered && (
                  <>
                    <text
                      x={uxX + barW / 2}
                      y={uxY - 4}
                      textAnchor="middle"
                      className="fill-gray-200"
                      style={{ fontSize: 10, fontWeight: 600 }}
                    >
                      {d.ux.toLocaleString()}
                    </text>
                    <text
                      x={pmX + barW / 2}
                      y={pmY - 4}
                      textAnchor="middle"
                      className="fill-gray-200"
                      style={{ fontSize: 10, fontWeight: 600 }}
                    >
                      {d.pm.toLocaleString()}
                    </text>
                  </>
                )}

                {/* X axis location label */}
                <text
                  x={groupX(i)}
                  y={SVG_H - PAD.bottom + 16}
                  textAnchor="middle"
                  className="fill-gray-400"
                  style={{ fontSize: 11 }}
                >
                  {d.location}
                </text>
              </g>
            );
          })}

          {/* X axis baseline */}
          <line
            x1={PAD.left}
            y1={PAD.top + drawH}
            x2={PAD.left + drawW}
            y2={PAD.top + drawH}
            stroke="#374151"
            strokeWidth="1"
          />
        </svg>

        {/* Tooltip */}
        {hoveredGroup !== null && (() => {
          const d = DATA[hoveredGroup];
          const cx = groupX(hoveredGroup);
          const diff = d.ux - d.pm;
          const winner = diff > 0 ? "UX Design" : "Product Management";
          const pct = Math.round((Math.abs(diff) / Math.min(d.ux, d.pm)) * 100);
          return (
            <div
              className="pointer-events-none absolute top-4 z-20 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5"
              style={{
                left:
                  hoveredGroup === DATA.length - 1
                    ? `${cx - PAD.left - 8}px`
                    : `${cx - PAD.left + 12}px`,
                transform:
                  hoveredGroup === DATA.length - 1 ? "translateX(-100%)" : undefined,
                minWidth: 168,
              }}
            >
              <p className="text-xs font-medium text-gray-300 mb-1.5">{d.location}</p>
              <div className="flex items-center justify-between gap-4 mb-0.5">
                <span className="flex items-center gap-1.5 text-xs text-gray-400">
                  <span className="w-2 h-2 rounded-sm shrink-0" style={{ backgroundColor: UX_COLOR }} />
                  UX Design
                </span>
                <span className="text-xs font-medium text-white tabular-nums">
                  {d.ux.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between gap-4 mb-1.5">
                <span className="flex items-center gap-1.5 text-xs text-gray-400">
                  <span className="w-2 h-2 rounded-sm shrink-0" style={{ backgroundColor: PM_COLOR }} />
                  PM
                </span>
                <span className="text-xs font-medium text-white tabular-nums">
                  {d.pm.toLocaleString()}
                </span>
              </div>
              <p className="text-[10px] text-gray-500 border-t border-gray-700 pt-1.5">
                {winner} +{pct}% more openings
              </p>
            </div>
          );
        })()}
      </div>
    </div>
  );
}
