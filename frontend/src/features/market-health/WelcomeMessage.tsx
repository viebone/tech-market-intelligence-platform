// "About this platform" — the pinned welcome, styled as the product's one landing-page-style
// entry point: Hero / Proof / Call to action (added 2026-09-04, restructured 2026-09-04 — see
// changes/2026-09-04-about-this-platform-welcome.md and
// changes/2026-09-04-welcome-visual-data-points.md). See design/market-health/experience.md
// — Opening Welcome and design/visual-design.md — Entry-point components. Not a
// story-catalogue message itself — DataStoryMessage renders those, once a shortcut here is
// selected.

export interface WelcomeRoleBreakdownRow {
  role_category: string;
  postings: number;
}

export interface WelcomeInventory {
  total_postings: number;
  companies: number;
  collection_started_at: string | null;
  role_categories: string[];
  role_breakdown: WelcomeRoleBreakdownRow[];
  signals_available: string[];
}

export interface WelcomeStoryShortcut {
  id: string;
  display_name: string;
  question: string;
}

export interface WelcomeResult {
  inventory: WelcomeInventory;
  story_shortcuts: WelcomeStoryShortcut[];
  provenance: {
    sources: string[];
    model_used: boolean;
    query_time: string;
  };
  as_of: string;
}

// design/visual-design.md — Accent palette. Colour follows the entity (role category) by
// name, never by position — an unrecognised category falls back to neutral gray rather than
// guessing a hue. Same three hues the trend chart already uses for the same categories.
const ROLE_CATEGORY_COLOR: Record<string, string> = {
  Designer: "#6366f1",
  "Product Manager": "#a855f7",
  Engineer: "#10b981",
};
const FALLBACK_SEGMENT_COLOR = "#4b5563"; // gray-600

function formatMonthYear(iso: string): string {
  return new Date(iso).toLocaleDateString("default", { month: "long", year: "numeric" });
}

function formatCount(n: number): string {
  return n.toLocaleString();
}

interface WelcomeMessageProps {
  welcome: WelcomeResult;
  /** Selecting a shortcut selects that story's own task — same handler as the Task Panel. */
  onSelectShortcut: (storyId: string) => void;
}

export function WelcomeMessage({ welcome, onSelectShortcut }: WelcomeMessageProps) {
  const { inventory, story_shortcuts: shortcuts } = welcome;
  const hasCollected = inventory.total_postings > 0 && inventory.collection_started_at !== null;
  const breakdown = inventory.role_breakdown;
  const breakdownTotal = breakdown.reduce((sum, row) => sum + row.postings, 0);

  return (
    <article aria-label="About this platform" className="space-y-7">
      {/* Hero */}
      <div>
        <p className="mb-2 text-[10px] font-medium uppercase tracking-widest text-gray-500">
          Tech market intelligence
        </p>
        <h2 className="text-3xl font-bold leading-tight text-gray-100">
          Read the tech hiring market before you make a move.
        </h2>
        <p className="mt-3 max-w-xl text-sm leading-relaxed text-gray-400">
          We track job openings, skills, and pay across company career pages — so you see
          where demand is heading, not guess.
        </p>
      </div>

      {/* Proof */}
      <div className="border-t border-gray-800 pt-6">
        {hasCollected ? (
          <>
            <div className="flex flex-wrap items-end gap-x-10 gap-y-4">
              <div>
                <p className="text-4xl font-bold leading-none text-gray-100">
                  {formatCount(inventory.total_postings)}
                </p>
                <p className="mt-1.5 text-xs text-gray-500">job openings tracked</p>
              </div>
              <div>
                <p className="text-xl font-semibold leading-none text-gray-100">
                  {formatCount(inventory.companies)}
                </p>
                <p className="mt-1.5 text-xs text-gray-500">companies</p>
              </div>
              <div>
                <p className="text-xl font-semibold leading-none text-gray-100">
                  {inventory.collection_started_at
                    ? formatMonthYear(inventory.collection_started_at)
                    : "—"}
                </p>
                <p className="mt-1.5 text-xs text-gray-500">tracking since</p>
              </div>
            </div>

            {breakdown.length > 0 && breakdownTotal > 0 && (
              <div className="mt-6">
                <div
                  className="flex h-3 w-full gap-[2px] overflow-hidden rounded bg-gray-800"
                  role="img"
                  aria-label={`Job openings by role category: ${breakdown
                    .map((row) => `${row.role_category} ${formatCount(row.postings)}`)
                    .join(", ")}`}
                >
                  {breakdown.map((row) => {
                    const color = ROLE_CATEGORY_COLOR[row.role_category] ?? FALLBACK_SEGMENT_COLOR;
                    const pct = Math.round((row.postings / breakdownTotal) * 100);
                    return (
                      <div
                        key={row.role_category}
                        title={`${row.role_category}: ${formatCount(row.postings)} (${pct}%)`}
                        style={{ flex: `${row.postings} 1 0%`, backgroundColor: color }}
                        className="h-full"
                      />
                    );
                  })}
                </div>
                <div className="mt-2.5 flex flex-wrap gap-x-5 gap-y-1.5">
                  {breakdown.map((row) => {
                    const color = ROLE_CATEGORY_COLOR[row.role_category] ?? FALLBACK_SEGMENT_COLOR;
                    const pct = Math.round((row.postings / breakdownTotal) * 100);
                    return (
                      <span
                        key={row.role_category}
                        className="flex items-center gap-1.5 text-xs text-gray-400"
                      >
                        <span
                          className="inline-block h-2 w-2 shrink-0 rounded-full"
                          style={{ backgroundColor: color }}
                        />
                        <span className="text-gray-200">{row.role_category}</span>
                        <span className="tabular-nums">{pct}%</span>
                      </span>
                    );
                  })}
                </div>
              </div>
            )}

            <p className="mt-5 max-w-2xl text-sm leading-relaxed text-gray-400">
              This is a growing sample of the market, not every job out there — it reflects
              the companies and roles we follow today. For most of these we also have the
              skills employers mention, and pay figures where they're shared.
            </p>
          </>
        ) : (
          <p className="text-sm text-gray-400">
            We haven't collected any job openings yet. Once collection begins, this section
            will show how many openings and companies we're tracking and since when.
          </p>
        )}
      </div>

      {/* Call to action */}
      <div className="border-t border-gray-800 pt-6">
        <h3 className="text-sm font-semibold text-gray-200">Get an instant answer</h3>
        {shortcuts.length > 0 && (
          <ul className="mt-3 flex flex-col gap-2">
            {shortcuts.map((shortcut) => (
              <li key={shortcut.id}>
                <button
                  type="button"
                  onClick={() => onSelectShortcut(shortcut.id)}
                  className="group flex w-full items-center justify-between gap-3 rounded-lg border border-gray-700 bg-gray-800/60 px-3.5 py-2.5 text-left text-sm text-gray-200 transition-colors hover:border-gray-500 hover:bg-gray-800"
                >
                  <span>{shortcut.question}</span>
                  <span className="shrink-0 text-gray-500 transition-colors group-hover:text-gray-300">
                    →
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
        <p className="mt-4 text-sm leading-relaxed text-gray-400">
          You can also ask your own question about demand, skills, pay, or specific roles once
          you're in a conversation. We don't cover layoffs, company reviews, or application
          tracking.
        </p>
      </div>
    </article>
  );
}
