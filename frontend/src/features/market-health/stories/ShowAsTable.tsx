import { useState } from "react";

// A collapsed-by-default disclosure revealing the exact numbers a chart already plots, as a real
// <table> — the Chart accessibility standard's rule 9 (design/visual-design.md), added
// 2026-09-27 (changes/2026-09-26-data-story-chart-variety.md). Generic across every chart that
// uses it: each caller supplies its own caption/columns/rows, already formatted with units — this
// component never formats or computes a value itself. Not used by StatTilePair (no plot to
// tabulate, same carve-out the dataviz method gives a bare stat tile).

export interface ShowAsTableProps {
  /** States the window/scope/unit — same discipline as a chart's own subtitle. */
  caption: string;
  /** Column headers, units included, e.g. ["Role", "Median (£)", "n"]. */
  columns: string[];
  rows: (string | number)[][];
}

export function ShowAsTable({ caption, columns, rows }: ShowAsTableProps) {
  const [open, setOpen] = useState(false);
  if (rows.length === 0) return null;

  return (
    <div className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="inline-flex min-h-[24px] items-center rounded px-2 text-xs text-gray-400 underline decoration-gray-700 underline-offset-2 hover:text-gray-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
      >
        {open ? "Hide table" : "Show as table"}
      </button>
      {open ? (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full border-collapse text-left text-xs text-gray-300">
            <caption className="mb-1 text-left text-xs text-gray-400">{caption}</caption>
            <thead>
              <tr className="border-b border-gray-700">
                {columns.map((c) => (
                  <th key={c} scope="col" className="py-1 pr-4 font-medium text-gray-400">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i} className="border-b border-gray-800">
                  {row.map((cell, j) => (
                    <td key={j} className="py-1 pr-4 tabular-nums">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
