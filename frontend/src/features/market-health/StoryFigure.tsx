// The one Hero Figure a data story may lead a block with — a headline number
// plus a short caption. Never an accent colour (a hero figure is a headline
// metric, not a categorical data point). At most one per story.
// See design/visual-design.md - Hero Figure / Data Story composition.
// Added 2026-09-10, changes/2026-09-10-story-visual-standard.md.

export function StoryFigure({
  value,
  caption,
}: {
  /** Pre-formatted, e.g. "6%", "2,827", "$130k". */
  value: string;
  caption: string;
}) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-3xl font-bold text-gray-100">{value}</span>
      <span className="text-sm text-gray-400">{caption}</span>
    </div>
  );
}
