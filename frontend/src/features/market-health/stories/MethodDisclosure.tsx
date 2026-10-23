import { useId, useState } from "react";
import type { MethodText } from "./sampling";

// "How we read the market" — the welcome's collapsed-by-default disclosure (added 2026-10-23,
// design/market-health/experience.md — How we read the market; frontend spec — Sampling and the
// method text). Renders the four canonical points exactly as the API sends them. Same chevron
// disclosure pattern as "How this was generated"; local state only.

export function MethodDisclosure({ method }: { method: MethodText }) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  if (method.full.length === 0) return null;

  return (
    <div className="mt-2">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls={panelId}
        className="inline-flex min-h-[24px] items-center gap-1 rounded text-sm text-gray-400 hover:text-gray-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
      >
        <span aria-hidden="true" className={`inline-block transition-transform ${open ? "rotate-90" : ""}`}>›</span>
        How we read the market
      </button>
      {open ? (
        <ul id={panelId} className="mt-2 max-w-2xl space-y-2">
          {method.full.map((item) => (
            <li key={item.heading} className="text-sm leading-relaxed text-gray-400">
              <span className="font-semibold text-gray-300">{item.heading}.</span> {item.text}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
