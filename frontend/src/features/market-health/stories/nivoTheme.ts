import type { PartialTheme } from "@nivo/theming";

// Shared Nivo theme — added 2026-09-22 (changes/2026-09-22-nivo-charting-library.md).
// Matches design/visual-design.md's dark palette exactly (Nivo's own defaults are
// light-theme; every token below is a direct 1:1 mapping, not an approximation):
//   gray-100 #f3f4f6 (text primary) · gray-400 #9ca3af (text muted, axis labels)
//   gray-500 #6b7280 (tick lines) · gray-700 #374151 (borders, grid) · gray-800 #1f2937 (surface/tooltip bg)
// Every chart built with this theme must use it — no chart renders with Nivo's own
// light-theme defaults anywhere in this product (design/visual-design.md — Charting library).
export const nivoTheme: PartialTheme = {
  background: "transparent",
  text: {
    fontSize: 12,
    fill: "#9ca3af", // gray-400
    fontFamily: "ui-sans-serif, system-ui, -apple-system, sans-serif",
  },
  axis: {
    domain: { line: { stroke: "#374151", strokeWidth: 1 } }, // gray-700
    ticks: {
      line: { stroke: "#374151", strokeWidth: 1 },
      text: { fill: "#9ca3af", fontSize: 11 }, // gray-400
    },
    legend: { text: { fill: "#f3f4f6", fontSize: 12, fontWeight: 600 } }, // gray-100
  },
  grid: {
    line: { stroke: "#1f2937", strokeWidth: 1 }, // gray-800 — subtle, matches "Border subtle"
  },
  legends: {
    text: { fill: "#9ca3af", fontSize: 11 }, // gray-400
  },
  tooltip: {
    container: {
      background: "#1f2937", // gray-800, same as every other surface/tooltip in this product
      color: "#f3f4f6", // gray-100
      fontSize: 12,
      border: "1px solid #374151", // gray-700
      borderRadius: 6,
    },
  },
  labels: {
    text: { fill: "#f3f4f6", fontSize: 11 }, // gray-100
  },
  crosshair: {
    line: { stroke: "#6b7280", strokeWidth: 1, strokeOpacity: 0.6 }, // gray-500
  },
};

// The 3 tracked Role Categories' accent colours — design/visual-design.md's Accent
// palette, the same hues the trend chart and Category Share Bar already use. Kept
// keyed on the stored role_category value ("Designer"/"Product Manager"/"Engineer"),
// never the display label — same "value drives colour/lookup, label only changes what
// renders" rule changes/2026-09-22-role-category-display-relabel.md already established.
export const ROLE_CATEGORY_CHART_COLOR: Record<string, string> = {
  Designer: "#6366f1", // indigo-500
  "Product Manager": "#a855f7", // purple-500
  Engineer: "#10b981", // emerald-500
};
export const FALLBACK_CHART_COLOR = "#6b7280"; // gray-500 — an unrecognised category, never guessed
