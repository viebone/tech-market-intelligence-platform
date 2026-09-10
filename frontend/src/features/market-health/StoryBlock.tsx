import type { ReactNode } from "react";

// The fixed data-story block anatomy: heading -> one visual -> honesty qualifier,
// with the divider that gives every story the same vertical rhythm. When the
// block has no data it shows a plain "not enough data yet" line instead of the
// visual. See design/visual-design.md - Data Story composition, and
// design/market-health/data-stories.md - Visual standard every story must meet.
// Added 2026-09-10, changes/2026-09-10-story-visual-standard.md (extracted from
// DataStoryMessage's inline Block).

export function StoryBlock({
  heading,
  qualifier,
  insufficient = false,
  emptyMessage,
  children,
}: {
  heading: string;
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
