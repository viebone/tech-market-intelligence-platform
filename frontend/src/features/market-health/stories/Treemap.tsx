import { useMemo, useState } from "react";
import { ShowAsTable } from "./ShowAsTable";

// Parts of one whole across many categories — one tile per category, area = its share.
// Added 2026-09-27 (changes/2026-09-26-data-story-chart-variety.md), for Story 4's function
// breakdown, replacing a Ranked bar list (a dozen similar-length bars don't show "how big a
// slice" the way area does). Hand-rolled, single-level SLICE-AND-DICE layout — not a full
// squarified algorithm; at this story's real scale (currently under 15 tiles) this gives
// legible tile aspect ratios with far less layout code, and nothing here needs the finer
// packing a true squarify buys. See design/visual-design.md — Treemap.
//
// Shade-by-volume + real gap added 2026-09-27 (changes/2026-09-27-treemap-legibility.md) — the
// original one-fill, 1px-into-unset-background version was unreadable: adjacent similarly-sized
// tiles were indistinguishable. See design/visual-design.md — Treemap for the validated ramp.

export interface TreemapTile {
  key: string;
  name: string;
  count: number;
  /** 0-100. */
  share: number;
  /** "aggregate" = the server-computed "smaller functions" merge tile (dashed hollow outline).
   * "unknown" = a real, un-merged category the server never folds away (solid hollow outline).
   * "named" = a normal filled tile. */
  kind: "named" | "aggregate" | "unknown";
}

export interface TreemapProps {
  tiles: TreemapTile[];
  tableCaption: string;
}

// Sequential shade-by-volume ramp, dimmest (lowest quartile) -> brightest (highest quartile).
// Dark-mode sequential ramps anchor opposite light mode: bright reads as "more" against a dark
// surface, dim recedes toward it. indigo-500 is skipped — 3.97:1/4.06:1 text contrast either way,
// a dead zone under the 4.5:1 floor. indigo-700 is skipped too — 1.86:1 against the gray-800 gap
// (blends in) and only ΔL 0.054 from indigo-600 (indistinguishable). Validated:
// `node validate_palette.js "#4f46e5,#818cf8,#a5b4fc,#c7d2fe" --ordinal --mode dark --surface "#1f2937"`.
const SHADE_RAMP: { bg: string; text: "dark" | "light" }[] = [
  { bg: "#c7d2fe", text: "dark" }, // indigo-200 — highest quartile
  { bg: "#a5b4fc", text: "dark" }, // indigo-300
  { bg: "#818cf8", text: "dark" }, // indigo-400
  { bg: "#4f46e5", text: "light" }, // indigo-600 — lowest quartile
];

interface LaidOutTile { tile: TreemapTile; x: number; y: number; w: number; h: number }

// Percent-space layout (0-100 on both axes) — proportional to the real rendered rectangle on
// each axis regardless of the container's actual aspect ratio, since CSS %-width/height are
// relative to the real container size.
function layout(tiles: TreemapTile[], x: number, y: number, w: number, h: number, horizontal: boolean): LaidOutTile[] {
  if (tiles.length === 0) return [];
  if (tiles.length === 1) return [{ tile: tiles[0], x, y, w, h }];
  const total = tiles.reduce((s, t) => s + t.count, 0) || 1;
  let acc = 0;
  let splitIdx = 1;
  for (let i = 0; i < tiles.length; i++) {
    acc += tiles[i].count;
    if (acc >= total / 2) { splitIdx = i + 1; break; }
  }
  splitIdx = Math.min(Math.max(splitIdx, 1), tiles.length - 1);
  const groupA = tiles.slice(0, splitIdx);
  const groupB = tiles.slice(splitIdx);
  const fracA = groupA.reduce((s, t) => s + t.count, 0) / total;
  return horizontal
    ? [...layout(groupA, x, y, w * fracA, h, false), ...layout(groupB, x + w * fracA, y, w * (1 - fracA), h, false)]
    : [...layout(groupA, x, y, w, h * fracA, true), ...layout(groupB, x, y + h * fracA, w, h * (1 - fracA), true)];
}

function describe(tile: TreemapTile): string {
  return `${tile.name}: ${tile.count.toLocaleString()} postings, ${tile.share.toFixed(1)}%`;
}

export function Treemap({ tiles, tableCaption }: TreemapProps) {
  const [focused, setFocused] = useState(0);
  const sorted = useMemo(() => [...tiles].sort((a, b) => b.count - a.count), [tiles]);
  const laidOut = useMemo(() => layout(sorted, 0, 0, 100, 100, true), [sorted]);
  // Rank-quartile shade, not an absolute share threshold, so the ramp works the same regardless
  // of how concentrated or spread the data is. `sorted` is already desc by count.
  const shadeByKey = useMemo(() => {
    const named = sorted.filter((t) => t.kind === "named");
    const map = new Map<string, { bg: string; text: "dark" | "light" }>();
    named.forEach((t, i) => {
      const q = Math.min(Math.floor((i / named.length) * SHADE_RAMP.length), SHADE_RAMP.length - 1);
      map.set(t.key, SHADE_RAMP[q]);
    });
    return map;
  }, [sorted]);
  if (sorted.length === 0) return null;

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowRight" || e.key === "ArrowDown") { setFocused((i) => Math.min(i + 1, sorted.length - 1)); e.preventDefault(); }
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") { setFocused((i) => Math.max(i - 1, 0)); e.preventDefault(); }
    else if (e.key === "Home") { setFocused(0); e.preventDefault(); }
    else if (e.key === "End") { setFocused(sorted.length - 1); e.preventDefault(); }
  }

  const hasAggregate = sorted.some((t) => t.kind === "aggregate");
  const hasUnknown = sorted.some((t) => t.kind === "unknown");

  return (
    <div>
      <div
        role="img"
        aria-label={`Postings outside the 3 tracked categories, by function. ${describe(sorted[focused])}`}
        tabIndex={0}
        onKeyDown={onKeyDown}
        className="relative aspect-[2/1] min-h-[240px] w-full rounded bg-gray-800 outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
      >
        {laidOut.map(({ tile, x, y, w, h }) => {
          const isFocused = sorted[focused] === tile;
          const hollow = tile.kind !== "named";
          const shade = shadeByKey.get(tile.key);
          const textDark = hollow ? false : shade?.text !== "light";
          return (
            <div
              key={tile.key}
              style={{ left: `${x}%`, top: `${y}%`, width: `${w}%`, height: `${h}%` }}
              className="absolute p-0.5"
            >
              <div
                className={`flex h-full w-full flex-col justify-end overflow-hidden rounded p-1 ${
                  isFocused ? "ring-2 ring-indigo-400" : ""
                }`}
                style={
                  hollow
                    ? {
                        backgroundColor: "transparent",
                        border: `1px ${tile.kind === "aggregate" ? "dashed" : "solid"} #9ca3af`,
                      }
                    : { backgroundColor: shade?.bg }
                }
                title={describe(tile)}
              >
                <span
                  className={`truncate text-xs font-semibold ${
                    hollow ? "text-gray-300" : textDark ? "text-gray-900" : "text-gray-100"
                  }`}
                >
                  {tile.name}
                </span>
                <span
                  className={`truncate text-xs ${
                    hollow ? "text-gray-400" : textDark ? "text-gray-900" : "text-gray-100"
                  }`}
                >
                  {tile.count.toLocaleString()} · {tile.share.toFixed(1)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <p aria-live="polite" className="sr-only">
        {describe(sorted[focused])}
      </p>

      <p className="mt-2 text-xs text-gray-400">
        Tile size and shade both show each function's share of postings outside the 3 tracked
        categories — larger, brighter tiles hold more.
        {hasAggregate ? " Dashed outline: smaller functions grouped together." : ""}
        {hasUnknown ? " Solid outline: function not stated." : ""}
      </p>

      <ShowAsTable
        caption={tableCaption}
        columns={["Function", "Postings", "Share"]}
        rows={sorted.map((t) => [t.name, t.count.toLocaleString(), `${t.share.toFixed(1)}%`])}
      />
    </div>
  );
}
