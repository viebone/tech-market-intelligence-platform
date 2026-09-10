import { RankedBarList } from "./RankedBarList";

// A data-story block that shows how a set of proportions shifted between two
// 12-month windows — current vs one year back. Per row: a shared track with a
// gray-700 prior-year ghost behind an indigo-500 current fill (the visible gap
// is the change), plus a glyph+sign delta ("▲ +3 pp"). Colour never carries the
// direction — the glyph and sign do. Before a full prior window exists it shows
// the current window only, plain. See design/visual-design.md — Year-on-year
// comparison. Added 2026-09-10, changes/2026-09-10-story-yoy-breakdowns.md.

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

const HUE = "#6366f1"; // indigo-500 — same magnitude hue as Ranked bar list

function monthYear(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString(undefined, {
    month: "short",
    year: "numeric",
  });
}

function WindowLine({ current, prior }: { current: YoYWindow; prior: YoYWindow | null }) {
  const cur = `${monthYear(current.start_date)} – ${monthYear(current.end_date)}`;
  return (
    <p className="mb-3 text-xs text-gray-500">
      {prior ? `${cur}, compared with the 12 months before it` : `${cur} — comparison window only`}
    </p>
  );
}

function Delta({ pp }: { pp: number }) {
  const rounded = Math.round(pp * 10) / 10;
  if (rounded === 0) {
    return <span className="text-xs tabular-nums text-gray-500">– no change</span>;
  }
  const up = rounded > 0;
  return (
    <span className="text-xs tabular-nums text-gray-400">
      {up ? "▲ +" : "▼ −"}
      {Math.abs(rounded).toFixed(1)} pp
    </span>
  );
}

export function YearOnYearBars({ content }: { content: YearOnYearContent }) {
  const { comparison_available, rows, current_window, prior_window } = content;

  // "No prior window yet" — the current window still has data; show it plainly.
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

  const max = Math.max(
    ...rows.map((row) => Math.max(row.current_share, row.prior_share ?? 0)),
    0.01,
  );

  return (
    <div>
      <WindowLine current={current_window} prior={prior_window} />
      <ol className="flex flex-col gap-2">
        {rows.map((row, i) => (
          <li key={`${row.value}-${i}`} className="flex items-center gap-3">
            <span className="w-44 shrink-0 truncate text-sm text-gray-300" title={row.value}>
              {row.value}
            </span>
            <span className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-gray-800">
              <span
                className="absolute inset-y-0 left-0 rounded-full bg-gray-700"
                style={{ width: `${((row.prior_share ?? 0) / max) * 100}%` }}
              />
              <span
                className="absolute inset-y-0 left-0 rounded-full"
                style={{ width: `${(row.current_share / max) * 100}%`, backgroundColor: HUE, opacity: 0.7 }}
              />
            </span>
            <span className="w-20 shrink-0 text-right">
              {row.delta_pp !== null ? <Delta pp={row.delta_pp} /> : null}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
