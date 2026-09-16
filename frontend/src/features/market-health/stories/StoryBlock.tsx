import type { ReactNode } from "react";

// The fixed data-story block anatomy: heading -> optional subtitle -> one visual
// -> honesty qualifier, with the divider that gives every story the same
// vertical rhythm. When the block has no data it shows a plain "not enough
// data yet" line instead of the visual. See design/visual-design.md - Data
// Story composition, Data Legibility, and design/market-health/data-stories.md
// - Visual standard every story must meet. Added 2026-09-10,
// changes/2026-09-10-story-visual-standard.md (extracted from
// DataStoryMessage's inline Block). `subtitle` added 2026-09-11,
// changes/2026-09-11-data-legibility-market-health.md — subtitle states what's
// being measured and its unit; qualifier states how much to trust it. The two
// are never merged into one line (see Data Legibility, visual-design.md).

export function StoryBlock({
  heading,
  subtitle,
  qualifier,
  insufficient = false,
  emptyMessage,
  children,
}: {
  heading: string;
  /** What's being measured and its unit, when the heading alone doesn't say — e.g. "Ranked
   * by jobs reported affected, summed across contraction events in the window." Omitted when
   * the heading (or the visual's own caption, e.g. Meter) already makes the unit obvious. */
  subtitle?: string;
  /** The section's honesty caveat (sample size / coverage). Omitted = no line. */
  qualifier?: string;
  /** True when the section is insufficient_data, or its visual has no rows. */
  insufficient?: boolean;
  /** Shown when `insufficient`; falls back to a generic line. */
  emptyMessage?: string;
  children: ReactNode;
}) {
  return (
    <section className="border-t border-gray-800 pt-4">
      <h3 className="text-sm font-semibold text-gray-200">{heading}</h3>
      {subtitle ? <p className="mt-0.5 text-xs text-gray-400">{subtitle}</p> : null}
      <div className="mt-3">
        {insufficient ? (
          <p className="text-sm text-gray-400">{emptyMessage ?? "Not enough data yet."}</p>
        ) : (
          children
        )}
      </div>
      {qualifier ? <p className="mt-2 text-xs text-gray-500">{qualifier}</p> : null}
    </section>
  );
}
