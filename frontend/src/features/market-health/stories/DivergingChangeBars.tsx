import { ShowAsTable } from "./ShowAsTable";

// Change between two periods — one indigo-500 bar per row, either side of a zero line. Added
// 2026-09-27 (changes/2026-09-26-data-story-chart-variety.md), for Story 5's "Which industries
// are changing" block, replacing the grouped-bar year-on-year comparison used there before: the
// real question is "how much did it move," not "what were the two levels" a reader would
// otherwise have to subtract themselves. See design/visual-design.md — Diverging change bars.
//
// ONE hue in both directions — direction is carried by which side of the line the bar sits, the
// glyph, and the signed number, never by colour (a two-hue diverging scheme would say "good" and
// "bad", and a drop in vacancies can mean either slower hiring or roles being filled faster).

export interface DivergingRow {
  label: string;
  current: number;
  prior: number;
  /** Signed. */
  delta: number;
}

export interface DivergingChangeBarsProps {
  /** Pre-ordered by signed change, largest rise first — never re-sorted here. */
  rows: DivergingRow[];
  /** e.g. "thousand". */
  unit: string;
  tableCaption: string;
  currentPeriodLabel: string;
  priorPeriodLabel: string;
}

const HUE = "#6366f1"; // indigo-500 — one hue, both directions

function formatDelta(delta: number, unit: string): string {
  const magnitude = Math.abs(delta).toLocaleString(undefined, { maximumFractionDigits: 1 });
  if (delta > 0) return `▲ +${magnitude} ${unit}`;
  if (delta < 0) return `▼ −${magnitude} ${unit}`;
  return "– no change";
}

export function DivergingChangeBars({
  rows, unit, tableCaption, currentPeriodLabel, priorPeriodLabel,
}: DivergingChangeBarsProps) {
  if (rows.length === 0) return null;
  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.delta)), 1);

  return (
    <div>
      <p className="mb-1 text-xs text-gray-400">
        Right of the line: more vacancies than a year earlier. Left: fewer.
      </p>
      <p className="mb-2 text-center text-xs text-gray-400">No change</p>
      <ol className="flex flex-col gap-2">
        {rows.map((row) => {
          const pct = (Math.abs(row.delta) / maxAbs) * 50; // half-track = 50% of the row width
          const isPositive = row.delta > 0;
          return (
            <li key={row.label} className="flex items-center gap-3">
              <span className="w-40 shrink-0 truncate text-sm text-gray-300" title={row.label}>
                {row.label}
              </span>
              <span className="relative h-3 flex-1">
                <span className="absolute inset-y-0 left-1/2 w-px bg-gray-400" aria-hidden="true" />
                <span
                  className="absolute inset-y-0 rounded-full"
                  style={
                    isPositive
                      ? { left: "50%", width: `${pct}%`, backgroundColor: HUE }
                      : { right: "50%", width: `${pct}%`, backgroundColor: HUE }
                  }
                />
              </span>
              <span className="w-28 shrink-0 whitespace-nowrap text-right text-xs tabular-nums text-gray-400">
                {formatDelta(row.delta, unit)}
              </span>
            </li>
          );
        })}
      </ol>

      <ShowAsTable
        caption={tableCaption}
        columns={["Industry", currentPeriodLabel, priorPeriodLabel, "Change"]}
        rows={rows.map((r) => [
          r.label,
          `${r.current.toLocaleString()} ${unit}`,
          `${r.prior.toLocaleString()} ${unit}`,
          formatDelta(r.delta, unit),
        ])}
      />
    </div>
  );
}
