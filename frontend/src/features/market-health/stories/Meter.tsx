import { StoryFigure } from "./StoryFigure";

// One share as a part-to-whole bar: a Hero Figure percentage, a track+fill at
// that width, and a plain line stating the complement. For "6% of postings
// state a salary range" style facts. See design/visual-design.md - Meter.
// Added 2026-09-10, changes/2026-09-10-story-visual-standard.md.

export function Meter({
  percent,
  caption,
  complement,
}: {
  /** 0-100. */
  percent: number;
  /** Beside the figure, e.g. "of postings state a salary range". */
  caption: string;
  /** Below the bar, e.g. "The other 94% don't disclose compensation." */
  complement: string;
}) {
  const label = percent > 0 && percent < 1 ? "<1%" : `${Math.round(percent)}%`;
  return (
    <div>
      <StoryFigure value={label} caption={caption} />
      <span className="mt-3 block h-2 w-full overflow-hidden rounded-full bg-gray-800">
        <span
          className="block h-full rounded-full bg-indigo-500"
          style={{ width: `${Math.min(Math.max(percent, 1), 100)}%` }}
        />
      </span>
      <p className="mt-2 text-sm text-gray-400">{complement}</p>
    </div>
  );
}
