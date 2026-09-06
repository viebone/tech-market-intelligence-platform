// Ranked bar list — a short "top N" magnitude comparison (top roles, skills, locations).
// One muted hue; length carries the value. See design/visual-design.md — Ranked bar list.
// Generic: reusable by any data story. Added 2026-09-06,
// changes/2026-09-06-market-story-visual-and-dedup.md.

export interface RankedBarRow {
  label: string;
  value: number;
  /** Optional second, ordered encoding — an emphasised row uses the full-opacity hue. */
  emphasis?: boolean;
}

interface RankedBarListProps {
  rows: RankedBarRow[];
  /** Cap the list — never a scrollbar. Default 7. */
  limit?: number;
  formatValue?: (n: number) => string;
}

const HUE = "#6366f1"; // indigo-500 — one hue for the whole list

export function RankedBarList({ rows, limit = 7, formatValue }: RankedBarListProps) {
  const shown = rows.slice(0, limit);
  if (shown.length === 0) return null;

  const max = Math.max(...shown.map((r) => r.value), 1);
  const fmt = formatValue ?? ((n: number) => n.toLocaleString());

  return (
    <ol className="flex flex-col gap-2">
      {shown.map((row, i) => (
        <li key={`${row.label}-${i}`} className="flex items-center gap-3">
          <span className="w-44 shrink-0 truncate text-sm text-gray-300" title={row.label}>
            {row.label}
          </span>
          <span className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-gray-800">
            <span
              className="absolute inset-y-0 left-0 rounded-full"
              style={{
                width: `${Math.max((row.value / max) * 100, 2)}%`,
                backgroundColor: HUE,
                opacity: (row.emphasis ?? true) ? 1 : 0.55,
              }}
            />
          </span>
          <span className="w-12 shrink-0 text-right text-xs tabular-nums text-gray-400">
            {fmt(row.value)}
          </span>
        </li>
      ))}
    </ol>
  );
}
