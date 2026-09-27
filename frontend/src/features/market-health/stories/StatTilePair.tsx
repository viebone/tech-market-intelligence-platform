// Two neutral tiles, side by side — exactly two shares that sum to 100%, where a chart would add
// nothing (design/visual-design.md — Stat Tile pair). Added 2026-09-27
// (changes/2026-09-26-data-story-chart-variety.md), for Story 1's IC-vs-management block. Not a
// chart — no plot, so no ShowAsTable (same carve-out StoryFigure already has).

export interface StatTile {
  label: string;
  /** Pre-formatted, e.g. "84%". */
  value: string;
  /** null = comparison not available yet — renders the muted "comparison starts…" line instead
   * of a delta (the block's own StoryBlock qualifier already states when it starts). */
  delta: { text: string; direction: "up" | "down" | "flat" } | null;
  comparisonStartsLine?: string;
}

export interface StatTilePairProps {
  tiles: [StatTile, StatTile];
}

function Tile({ tile }: { tile: StatTile }) {
  return (
    <div className="rounded-lg border border-gray-700 bg-gray-800/60 p-4">
      <p className="text-xs text-gray-400">{tile.label}</p>
      <p className="mt-1 text-2xl font-semibold text-gray-100">{tile.value}</p>
      <p className="mt-1 text-xs text-gray-400">
        {tile.delta ? tile.delta.text : tile.comparisonStartsLine ?? "Comparison not yet available."}
      </p>
    </div>
  );
}

export function StatTilePair({ tiles }: StatTilePairProps) {
  return (
    <div className="grid grid-cols-1 gap-3 min-[360px]:grid-cols-2">
      <Tile tile={tiles[0]} />
      <Tile tile={tiles[1]} />
    </div>
  );
}
