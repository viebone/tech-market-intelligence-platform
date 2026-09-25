import { ResponsiveBar } from "@nivo/bar";
import { RankedBarList } from "./RankedBarList";
import { nivoTheme } from "./nivoTheme";

// Replaces the hand-rolled ghost-bar comparison (YearOnYearBars.tsx, added 2026-09-10,
// removed 2026-09-22 — changes/2026-09-22-nivo-charting-library.md) with a real grouped bar
// chart: two 12-month windows, current vs. one year back — never more. Generic across
// role_category/level/track, same as its predecessor; a caller relabels row.value before
// this component ever sees it (see DataStoryMessage.tsx's role-mix-shift call site) rather
// than this component knowing about any one dimension's display names.
// See design/visual-design.md — Year-on-year comparison.

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

function monthYear(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString(undefined, {
    month: "short",
    year: "numeric",
  });
}

function WindowLine({ current, prior }: { current: YoYWindow; prior: YoYWindow | null }) {
  const cur = `${monthYear(current.start_date)} – ${monthYear(current.end_date)}`;
  return (
    <p className="mb-1 text-xs text-gray-500">
      {prior ? `${cur}, compared with the 12 months before it` : `${cur} — comparison window only`}
    </p>
  );
}

const CURRENT_COLOR = "#6366f1"; // indigo-500 — "now," the point of the block
const PRIOR_COLOR = "#4b5563"; // gray-600 — "a year ago," context only, never a role accent

interface Row {
  value: string;
  current: number;
  prior: number;
  delta: number | null;
}

function ShareGroupedBars({ content }: { content: YearOnYearContent }) {
  const { comparison_available, rows, current_window, prior_window } = content;

  // "No prior window yet" — same honesty state as before: the current window has real
  // data and is shown plainly, no ghost bar, no delta column.
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

  const data: Row[] = rows.map((row) => ({
    value: row.value,
    current: Math.round(row.current_share * 1000) / 10,
    prior: Math.round((row.prior_share ?? 0) * 1000) / 10,
    delta: row.delta_pp,
  }));

  return (
    <div>
      <WindowLine current={current_window} prior={prior_window} />
      <div style={{ height: Math.max(data.length * 40 + 40, 220) }}>
        <ResponsiveBar
          data={data as unknown as Record<string, string | number>[]}
          keys={["current", "prior"]}
          indexBy="value"
          layout="horizontal"
          groupMode="grouped"
          theme={nivoTheme}
          colors={[CURRENT_COLOR, PRIOR_COLOR]}
          padding={0.35}
          innerPadding={2}
          borderRadius={2}
          margin={{ top: 8, right: 24, bottom: 40, left: 150 }}
          valueFormat={(v) => `${v}%`}
          axisBottom={{
            legend: "Share of postings",
            legendPosition: "middle",
            legendOffset: 32,
          }}
          enableGridY={false}
          enableLabel={false}
          isInteractive
          tooltip={({ id, value, indexValue, data: rowData }) => {
            const delta = (rowData as unknown as Row).delta;
            return (
              <div className="rounded border border-gray-700 bg-gray-800 px-2 py-1 text-xs text-gray-100">
                <span className="font-medium">{indexValue as string}</span>
                <br />
                {id === "current" ? "Now" : "A year ago"}: {value}%
                {id === "current" && delta !== null ? (
                  <>
                    <br />
                    Change: {delta! >= 0 ? "+" : ""}
                    {delta!.toFixed(1)} pp
                  </>
                ) : null}
              </div>
            );
          }}
          legends={[
            {
              dataFrom: "keys",
              anchor: "bottom",
              direction: "row",
              translateY: 40,
              itemsSpacing: 16,
              itemWidth: 90,
              itemHeight: 14,
              symbolSize: 10,
              symbolShape: "circle",
              data: [
                { id: "current", label: "Now", color: CURRENT_COLOR },
                { id: "prior", label: "A year ago", color: PRIOR_COLOR },
              ],
            },
          ]}
        />
      </div>
    </div>
  );
}


// ─────────────────────────────────────────────────────────────────────────────
// `mode="level"` — added 2026-09-25 (changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md;
// frontend/specs/market-health/architecture.md — Story 5). The same year-on-year idea for an OFFICIAL
// STATISTIC: two periods of the same length a year apart *as the publisher defines them* (ONS: two
// overlapping three-month averages, e.g. Jun–Aug 2026 vs Jun–Aug 2025), compared as LEVELS in
// thousands — not the platform's shares and "pp" deltas. Default mode stays "share", so every
// existing caller (Story 1's three shift blocks) is unchanged.
//
// Rendered with design/visual-design.md's ghost/solid anatomy (prior = muted ghost bar, now = solid
// bar over the same track) plus a ROW-ALIGNED delta with a glyph AND a signed number — "▲ +6
// thousand" / "▼ −12 thousand" / "– no change" — so direction never rests on colour alone. That
// row-aligned delta is not a Nivo primitive; the ghost/solid form is the design spec's own, and
// keeps this block out of the Nivo bundle. Deviation from the spec's "Nivo in level mode" wording
// is deliberate and recorded in the change request.
// ─────────────────────────────────────────────────────────────────────────────

export interface LevelYoYRow {
  label: string;
  current: number;
  prior: number;
  delta: number;
}

export interface LevelYoYContent {
  currentPeriodLabel: string;
  priorPeriodLabel: string | null;
  rows: LevelYoYRow[];
}

function formatDelta(delta: number): string {
  const magnitude = Math.abs(delta).toLocaleString(undefined, { maximumFractionDigits: 1 });
  if (delta > 0) return `▲ +${magnitude} thousand`;
  if (delta < 0) return `▼ −${magnitude} thousand`;
  return "– no change";
}

function LevelGroupedBars({ content }: { content: LevelYoYContent }) {
  const { rows, currentPeriodLabel, priorPeriodLabel } = content;
  if (rows.length === 0) return null;
  const max = Math.max(...rows.flatMap((r) => [r.current, r.prior]), 1);
  return (
    <div>
      <p className="mb-1 text-xs text-gray-500">
        {priorPeriodLabel
          ? `${currentPeriodLabel} compared with ${priorPeriodLabel} — three-month averages, in thousands of vacancies`
          : `${currentPeriodLabel} — three-month average, in thousands of vacancies`}
      </p>
      {priorPeriodLabel ? (
        <p className="mb-2 text-xs text-gray-500">
          Lighter bar: {priorPeriodLabel}. Solid bar: {currentPeriodLabel}.
        </p>
      ) : null}
      <ol className="flex flex-col gap-2">
        {rows.map((row) => (
          <li key={row.label} className="flex items-center gap-3">
            <span className="w-44 shrink-0 truncate text-sm text-gray-300" title={row.label}>
              {row.label}
            </span>
            <span className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-gray-800">
              <span
                className="absolute inset-y-0 left-0 rounded-full bg-gray-700"
                style={{ width: `${Math.max((row.prior / max) * 100, 2)}%` }}
              />
              <span
                className="absolute inset-y-0 left-0 rounded-full bg-indigo-500"
                style={{ width: `${Math.max((row.current / max) * 100, 2)}%`, opacity: 0.7 }}
              />
            </span>
            <span className="w-32 shrink-0 whitespace-nowrap text-right text-xs tabular-nums text-gray-400">
              {formatDelta(row.delta)}
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}

type YearOnYearGroupedBarsProps =
  | { mode?: "share"; content: YearOnYearContent }
  | { mode: "level"; content: LevelYoYContent };

export function YearOnYearGroupedBars(props: YearOnYearGroupedBarsProps) {
  if (props.mode === "level") return <LevelGroupedBars content={props.content} />;
  return <ShareGroupedBars content={props.content} />;
}
