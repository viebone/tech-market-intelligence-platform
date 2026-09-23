// Presentational 1-5 satisfaction rating control, shared by the Feedback Panel
// (design/visual-design.md — "Task Panel Footer & Feedback Panel", rating control spec).
// No fetch logic here — purely controlled, reused only inside FeedbackPanel today.

const RATING_VALUES = [1, 2, 3, 4, 5] as const;

interface RatingControlProps {
  value: number | null;
  onChange: (value: number) => void;
}

export function RatingControl({ value, onChange }: RatingControlProps) {
  return (
    <div>
      <div className="flex gap-2">
        {RATING_VALUES.map((n) => {
          const selected = value === n;
          return (
            <button
              key={n}
              type="button"
              aria-pressed={selected}
              onClick={() => onChange(n)}
              className={`flex-1 rounded-md border border-gray-700 py-2 text-sm font-medium transition-colors ${
                selected
                  ? "bg-emerald-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:text-gray-200"
              }`}
            >
              {n}
            </button>
          );
        })}
      </div>
      <div className="mt-1 flex justify-between text-[11px] text-gray-500">
        <span>Not satisfied</span>
        <span>Very satisfied</span>
      </div>
    </div>
  );
}
