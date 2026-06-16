import { DataFreshnessLabel } from "../../components/DataFreshnessLabel";

export interface TrendDataPoint {
  period: string;
  value: number;
}

export type TrendDirection = "rising" | "stable" | "declining";

interface TrendChartProps {
  title: string;
  data: TrendDataPoint[];
  direction: TrendDirection;
  asOf: string;
  source: string;
}

const directionConfig: Record<
  TrendDirection,
  { label: string; colorClass: string; strokeColor: string; arrowPath: string }
> = {
  rising: {
    label: "Rising",
    colorClass: "text-emerald-600",
    strokeColor: "#059669",
    arrowPath: "M5 15l7-7 7 7",
  },
  stable: {
    label: "Stable",
    colorClass: "text-amber-600",
    strokeColor: "#d97706",
    arrowPath: "M3 12h18",
  },
  declining: {
    label: "Declining",
    colorClass: "text-red-600",
    strokeColor: "#dc2626",
    arrowPath: "M5 9l7 7 7-7",
  },
};

const SVG_WIDTH = 280;
const SVG_HEIGHT = 80;
const PADDING = { top: 8, right: 8, bottom: 8, left: 8 };

function buildPolylinePath(data: TrendDataPoint[]): string {
  if (data.length === 0) return "";
  if (data.length === 1) {
    const x = PADDING.left;
    const y = SVG_HEIGHT / 2;
    return `M${x},${y} L${x},${y}`;
  }

  const values = data.map((d) => d.value);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const range = maxVal - minVal || 1;

  const drawWidth = SVG_WIDTH - PADDING.left - PADDING.right;
  const drawHeight = SVG_HEIGHT - PADDING.top - PADDING.bottom;

  const points = data.map((d, i) => {
    const x = PADDING.left + (i / (data.length - 1)) * drawWidth;
    // Invert Y: higher value = higher up on SVG
    const y = PADDING.top + drawHeight - ((d.value - minVal) / range) * drawHeight;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  return `M${points.join(" L")}`;
}

export function TrendChart({
  title,
  data,
  direction,
  asOf,
  source,
}: TrendChartProps) {
  const config = directionConfig[direction];
  const hasData = data.length > 0;

  return (
    <div className="rounded-lg border border-gray-100 bg-white p-4 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium text-gray-700 leading-snug">{title}</h3>
        <span
          className={`inline-flex items-center gap-1 text-xs font-semibold ${config.colorClass} shrink-0`}
          aria-label={`Trend: ${config.label}`}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="w-3.5 h-3.5"
            aria-hidden="true"
          >
            <path d={config.arrowPath} />
          </svg>
          {config.label}
        </span>
      </div>

      {/* Chart */}
      {hasData ? (
        <div className="relative" aria-hidden="true">
          <svg
            viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
            width="100%"
            height={SVG_HEIGHT}
            role="img"
            aria-label={`${title} trend chart`}
          >
            {/* Subtle grid line at midpoint */}
            <line
              x1={PADDING.left}
              y1={SVG_HEIGHT / 2}
              x2={SVG_WIDTH - PADDING.right}
              y2={SVG_HEIGHT / 2}
              stroke="#f3f4f6"
              strokeWidth="1"
            />
            {/* Trend line */}
            <path
              d={buildPolylinePath(data)}
              fill="none"
              stroke={config.strokeColor}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {/* Data point dots */}
            {data.map((d, i) => {
              const values = data.map((p) => p.value);
              const minVal = Math.min(...values);
              const maxVal = Math.max(...values);
              const range = maxVal - minVal || 1;
              const drawWidth = SVG_WIDTH - PADDING.left - PADDING.right;
              const drawHeight = SVG_HEIGHT - PADDING.top - PADDING.bottom;
              const x =
                data.length === 1
                  ? PADDING.left + drawWidth / 2
                  : PADDING.left + (i / (data.length - 1)) * drawWidth;
              const y =
                PADDING.top +
                drawHeight -
                ((d.value - minVal) / range) * drawHeight;
              return (
                <circle
                  key={d.period}
                  cx={x.toFixed(1)}
                  cy={y.toFixed(1)}
                  r="3"
                  fill={config.strokeColor}
                />
              );
            })}
          </svg>
          {/* Period labels */}
          {data.length > 1 && (
            <div className="flex justify-between mt-1">
              {[data[0], data[data.length - 1]].map((d, i) => (
                <span
                  key={i}
                  className="text-[10px] text-gray-300 tabular-nums"
                >
                  {d.period}
                </span>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="h-20 flex items-center justify-center rounded bg-gray-50">
          <p className="text-xs text-gray-400">No data available</p>
        </div>
      )}

      {/* Freshness */}
      <div className="mt-auto">
        <DataFreshnessLabel asOf={asOf} source={source} />
      </div>
    </div>
  );
}
