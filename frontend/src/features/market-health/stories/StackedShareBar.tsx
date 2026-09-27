import { ShowAsTable } from "./ShowAsTable";

// Two 100%-stacked horizontal bars ("this year" over "a year ago") — a part-to-whole comparison
// across two periods, for a *few* categories (≤4). Added 2026-09-27
// (changes/2026-09-26-data-story-chart-variety.md), for Story 1's role-mix block — the exact
// pattern the whole change exists to break up (this was the first of three identical grouped-bar
// blocks). See design/visual-design.md — Stacked share bar.
//
// Generic: the caller supplies segments already in the FIXED order and colour it wants — this
// component never reorders or recolours (same "caller relabels/colours before this component
// sees it" convention as YearOnYearGroupedBars/nivoTheme's role-category lookup).

export interface ShareSegment {
  /** Stable id (e.g. the stored role_category value) — React key and change-line lookup, not
   * necessarily what's displayed. */
  key: string;
  label: string;
  color: string;
  /** 0-100 share of this window. */
  value: number;
}

export interface StackedShareBarProps {
  currentLabel: string;
  priorLabel: string;
  /** In the exact order to render — never re-sorted here. */
  current: ShareSegment[];
  /** Same keys/order as `current`. `null` = no comparison exists yet — renders nothing at all
   * (the caller's own StoryBlock still shows its qualifier, which already states when the
   * comparison starts; a current-only bar here would repeat the Welcome's own Category Share
   * Bar, per the experience spec's explicit decision). */
  prior: ShareSegment[] | null;
  tableCaption: string;
}

function Bar({ segments, showLabels }: { segments: ShareSegment[]; showLabels: boolean }) {
  return (
    <div className="flex h-3 w-full overflow-hidden rounded-full bg-gray-800" role="presentation">
      {segments.map((seg, i) => {
        const isFirst = i === 0;
        const isLast = i === segments.length - 1;
        return (
          <div
            key={seg.key}
            style={{
              width: `${Math.max(seg.value, 0)}%`,
              backgroundColor: seg.color,
              marginRight: isLast ? 0 : 2,
            }}
            className={`h-full ${isFirst ? "rounded-l-full" : ""} ${isLast ? "rounded-r-full" : ""}`}
            title={showLabels ? undefined : `${seg.label}: ${seg.value.toFixed(0)}%`}
          />
        );
      })}
    </div>
  );
}

function deltaGlyph(delta: number): string {
  if (delta > 0) return `▲ +${delta.toFixed(0)} pp`;
  if (delta < 0) return `▼ ${delta.toFixed(0)} pp`;
  return "– no change";
}

export function StackedShareBar({
  currentLabel, priorLabel, current, prior, tableCaption,
}: StackedShareBarProps) {
  if (prior === null || current.length === 0) return null;

  const priorByKey = new Map(prior.map((s) => [s.key, s]));

  return (
    <div role="img" aria-label={`${tableCaption} Legend: top bar is ${currentLabel}, bottom bar is ${priorLabel}.`}>
      <p className="mb-1 text-xs text-gray-400">
        {current.map((seg) => `${seg.label} ${seg.value.toFixed(0)}%`).join(" · ")} — {currentLabel}
      </p>
      <Bar segments={current} showLabels />
      <Bar segments={prior} showLabels={false} />
      <p className="mt-1 text-xs text-gray-400">
        Top bar: {currentLabel}. Bottom bar: {priorLabel}.
      </p>
      <p className="mt-2 text-xs tabular-nums text-gray-400">
        {current
          .map((seg) => {
            const p = priorByKey.get(seg.key);
            const delta = p ? seg.value - p.value : 0;
            return `${seg.label} ${deltaGlyph(delta)}`;
          })
          .join(" · ")}
      </p>
      <ShowAsTable
        caption={tableCaption}
        columns={["Category", currentLabel, priorLabel, "Change"]}
        rows={current.map((seg) => {
          const p = priorByKey.get(seg.key);
          const delta = p ? seg.value - p.value : 0;
          return [seg.label, `${seg.value.toFixed(1)}%`, p ? `${p.value.toFixed(1)}%` : "—", deltaGlyph(delta)];
        })}
      />
    </div>
  );
}
