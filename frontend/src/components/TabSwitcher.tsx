/**
 * Generic pill-style tab switcher — design/visual-design.md's "Tab / range
 * selector" pattern, extracted as a real component for the first time (the
 * existing chart controls that inspired it are still hand-rolled inline in
 * JobOpeningsChart.tsx; this doesn't touch those, but could replace them
 * later — see frontend/specs/mcp-access/architecture.md — Component
 * Breakdown). Takes options + active + onChange — no knowledge of what it's
 * switching between.
 */

interface TabOption {
  value: string;
  label: string;
}

interface TabSwitcherProps {
  options: TabOption[];
  active: string;
  onChange: (value: string) => void;
}

export function TabSwitcher({ options, active, onChange }: TabSwitcherProps) {
  return (
    <div className="inline-flex rounded-md bg-gray-800 p-0.5">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={
            "rounded px-3 py-1 text-xs transition-colors duration-150 " +
            (option.value === active
              ? "bg-gray-600 text-white"
              : "text-gray-400 hover:text-gray-200")
          }
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
