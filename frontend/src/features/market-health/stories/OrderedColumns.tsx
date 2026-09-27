import { ShowAsTable } from "./ShowAsTable";

// A distribution over an ORDERED scale (a seniority ladder, business size) — the order is the
// meaning, so rows render in exactly the order given, never re-sorted by value. Added 2026-09-27
// (changes/2026-09-26-data-story-chart-variety.md), for Story 1's seniority block and Story 5's
// business-size block. Generic: one caller passes plain shares, the other passes a pre-formatted
// share+count label (`valueLabel`), same convention RankedBarList already uses.
// See design/visual-design.md — Ordered columns.
//
// Two layouts share one data model: vertical columns (≥480px container width) and, below that,
// ordered horizontal bars — same order, top to bottom — so a long step label never rotates or
// collides (Reflow & zoom rule). Both render from the same `rows`; CSS (not JS) picks which one
// is visible, so there is nothing to measure or recompute on resize.

export interface OrderedColumnRow {
  label: string;
  /** 0-100 (or any consistent unit) — bar/column length. */
  value: number;
  /** Pre-formatted text for the primary value, e.g. "14.1% · 99k" — falls back to `value`. */
  valueLabel?: string;
  /** The year-ago comparison, same unit as `value`. Absent = current-only state (no second bar). */
  compareValue?: number;
}

export interface OrderedColumnsProps {
  rows: OrderedColumnRow[];
  tableCaption: string;
  /** Shown only when at least one row has `compareValue`. */
  currentLegendLabel?: string;
  compareLegendLabel?: string;
  formatValue?: (n: number) => string;
}

const PRIMARY = "#6366f1"; // indigo-500
const COMPARE = "#6b7280"; // gray-500 — the muted comparator (Chart accessibility standard)

function Columns({ rows, fmt }: { rows: OrderedColumnRow[]; fmt: (n: number) => string }) {
  const max = Math.max(...rows.map((r) => Math.max(r.value, r.compareValue ?? 0)), 1);
  return (
    <div className="flex items-end justify-between gap-2">
      {rows.map((row) => {
        const pct = Math.max((row.value / max) * 100, 2);
        const comparePct = row.compareValue != null ? Math.max((row.compareValue / max) * 100, 2) : null;
        return (
          <div key={row.label} className="flex flex-1 flex-col items-center">
            <div className="relative flex h-32 items-end justify-center gap-1">
              <span
                className="absolute text-xs tabular-nums text-gray-300"
                style={{ bottom: `calc(${pct}% + 4px)` }}
              >
                {row.valueLabel ?? fmt(row.value)}
              </span>
              <div className="w-6 rounded-t bg-indigo-500" style={{ height: `${pct}%`, backgroundColor: PRIMARY }} />
              {comparePct !== null ? (
                <div className="w-3 rounded-t" style={{ height: `${comparePct}%`, backgroundColor: COMPARE }} />
              ) : null}
            </div>
            <p className="mt-1 text-center text-xs leading-tight text-gray-300">{row.label}</p>
          </div>
        );
      })}
    </div>
  );
}

function HorizontalBars({ rows, fmt }: { rows: OrderedColumnRow[]; fmt: (n: number) => string }) {
  const max = Math.max(...rows.map((r) => Math.max(r.value, r.compareValue ?? 0)), 1);
  return (
    <ol className="flex flex-col gap-2">
      {rows.map((row) => (
        <li key={row.label} className="flex items-center gap-3">
          <span className="w-32 shrink-0 truncate text-sm text-gray-300" title={row.label}>
            {row.label}
          </span>
          <span className="relative h-3 flex-1 overflow-hidden rounded-full bg-gray-800">
            <span
              className="absolute inset-y-0 left-0 rounded-full"
              style={{ width: `${Math.max((row.value / max) * 100, 2)}%`, backgroundColor: PRIMARY }}
            />
          </span>
          <span className="min-w-[3.5rem] shrink-0 whitespace-nowrap text-right text-xs tabular-nums text-gray-400">
            {row.valueLabel ?? fmt(row.value)}
          </span>
        </li>
      ))}
    </ol>
  );
}

export function OrderedColumns({
  rows, tableCaption, currentLegendLabel = "Now", compareLegendLabel = "A year ago", formatValue,
}: OrderedColumnsProps) {
  if (rows.length === 0) return null;
  const fmt = formatValue ?? ((n: number) => `${n}%`);
  const hasCompare = rows.some((r) => r.compareValue != null);

  return (
    <div>
      {hasCompare ? (
        <p className="mb-2 flex items-center gap-3 text-xs text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: PRIMARY }} />
            {currentLegendLabel}
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COMPARE }} />
            {compareLegendLabel}
          </span>
        </p>
      ) : null}

      {/* ≥480px: vertical columns, order = meaning. Below: ordered horizontal bars, same order. */}
      <div className="hidden min-[480px]:block">
        <Columns rows={rows} fmt={fmt} />
      </div>
      <div className="block min-[480px]:hidden">
        <HorizontalBars rows={rows} fmt={fmt} />
      </div>

      <ShowAsTable
        caption={tableCaption}
        columns={hasCompare ? ["Category", currentLegendLabel, compareLegendLabel] : ["Category", "Value"]}
        rows={rows.map((r) =>
          hasCompare
            ? [r.label, r.valueLabel ?? fmt(r.value), r.compareValue != null ? fmt(r.compareValue) : "—"]
            : [r.label, r.valueLabel ?? fmt(r.value)],
        )}
      />
    </div>
  );
}
