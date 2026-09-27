// The `YearOnYearGroupedBars` component (added 2026-09-10, changes/2026-09-10-story-yoy-
// breakdowns.md; `mode="level"` added 2026-09-25) — REMOVED 2026-09-27
// (changes/2026-09-26-data-story-chart-variety.md). Its last two callers were Story 1's three
// shift blocks (`mode="share"`, the default) and Story 5's "Which industries are changing"
// (`mode="level"`); this change replaced all four call sites with StackedShareBar/
// OrderedColumns/StatTilePair (Story 1) and DivergingChangeBars (Story 5) — a different chart
// form for each, since three-in-a-row of this one grouped-bar form was the exact repetition the
// change exists to fix. Confirmed by grep against the real files before deletion (this project's
// own "trace every import, verify before deleting" convention,
// changes/2026-09-16-frontend-organization.md).
//
// `LevelYoYRow`/`LevelYoYContent` (the level-mode types) went with it — nothing references them
// any more. `YoYRow`/`YearOnYearContent` below are kept: DataStoryMessage.tsx still uses them to
// type-parse the raw role-mix-shift/seniority-shift/track-shift section content before reshaping
// it for the new components (a caller-side concern, not this file's own rendering). History
// preserved here rather than erased, per this project's own "mark removed, don't erase"
// convention (see design/visual-design.md — "Chart event marker — removed").

export interface YoYWindow {
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
