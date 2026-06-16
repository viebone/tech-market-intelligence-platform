---
id: provenance-panel
feature: market-health
directive: low
status: active
created: 2026-06-15
---

# Provenance Panel — Component Spec

## What this spec is

Documents the `ProvenancePanel` component: a collapsible "How this was generated" section
that appears at the top of every `AITurn`. It surfaces how the system produced an answer —
what filters were active, what data was loaded, and what external services were called.

Implements UX Principle 4 (Progressive Transparency with Full Inspectability) from
`design/foundations.md`.

This spec lives under `design/market-health/` because the component was first built for
Market Health. If provenance appears in other features, extract to `design/components/`.

---

## Data Shape

```ts
interface ProvenanceData {
  source: "briefing" | "chat";
  filters: {
    role: string;
    seniority: string;
    location: string;
    period: string;
  };
  signal: MarketHealthSignalData | null;
  demandCount: number;
  compCount: number;
  layoffCount: number;
}
```

`source` controls which sections are shown inside the expanded panel.

`signal` may be `null` when the current filter combination returned no market data.

**Snapshotting rule**: for chat turns, `ProvenanceData` must be captured at the moment
the user submits the message — not read from live query state. If the user changes filters
after submitting, the provenance must still reflect the filters that were active at submit
time. For the opening briefing, live query data is acceptable because the briefing always
reflects the current filters.

---

## Visual Pattern

- Collapsed by default
- Toggle: chevron-down icon + label "How this was generated"
- Trigger text: muted (`text-gray-400`), transitions to darker on hover (`text-gray-600`)
- Expanded panel: rounded border, light gray background, compact padding, divided into sections

---

## Sections

### Filters applied (always shown)

Renders the four active filter values as `Tag` chips:

| Filter | Value when "all" | Value otherwise |
|---|---|---|
| Role | "All roles" | The role value |
| Seniority | "All seniority" | The seniority value |
| Location | "All locations" | The location value |
| Period | always "Last {period}" | e.g. "Last 6m" |

`Tag`: small rounded pill, `bg-gray-100`, muted text.

---

### Data loaded / Context sent to Claude (always shown)

Section heading:
- `source === "briefing"` → **"Data loaded"**
- `source === "chat"` → **"Context sent to Claude"**

Rows shown (using `Row` layout: label left, value right, dividing border between rows):

| Label | Value |
|---|---|
| Market signal | `signal.verdict` + trend arrow icon; or "No data for these filters" if `signal` is null |
| (sub-line) | `as of {signal.asOf}` shown below the verdict when signal is present |
| Demand signals | `"{demandCount} matched"` |
| Compensation signals | `"{compCount} matched"` |
| Layoff events | `"{layoffCount} total"` |
| Model | `"Claude Haiku"` — **chat turns only**, omit for briefing |

**Trend arrow icon map**

| `signal.trendDirection` | Symbol | Colour class |
|---|---|---|
| `improving` | ↗ | `text-emerald-600` |
| `stable` | → | `text-amber-600` |
| `worsening` | ↘ | `text-red-600` |
| `declining` | ↘ | `text-red-600` |

---

### Sources (briefing only, signal present)

Section heading: **"Sources"**

Content: `signal.source` rendered as a paragraph. Omit this section entirely if
`signal` is null.

---

### API calls (briefing only, always shown)

Section heading: **"API calls"**

Content: two monospaced lines:
```
GET /api/market-health/summary
GET /api/market-health/trends
```

Always shown for briefing turns, even when signal is null.
Never shown for chat turns.

---

## States

| State | Sections rendered |
|---|---|
| Collapsed (default) | Toggle trigger only |
| Expanded · briefing · has signal | Filters + Data loaded + Sources + API calls |
| Expanded · briefing · no signal | Filters + Data loaded (with "No data" row) + API calls (Sources omitted) |
| Expanded · chat | Filters + Context sent to Claude (no Sources, no API calls) |

---

## What this rules out

- Editing provenance data from the panel (read-only)
- Showing provenance on `UserTurn` (AI-only)
- Sharing or copying provenance (no affordance in v1)
- Rendering the panel when `provenance` is undefined (panel is simply absent)
