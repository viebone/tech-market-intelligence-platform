import { lazy, Suspense } from "react";
import { RankedBarList, type RankedBarRow } from "./RankedBarList";
import { StoryBlock } from "./StoryBlock";
import { StoryFigure } from "./StoryFigure";
import { SourceAttribution, isSourceAttribution, type SourceAttributionData } from "./SourceAttribution";
import { TechCommsTrendChart, type TrendPoint } from "./TechCommsTrendChart";
import { OrderedColumns, type OrderedColumnRow } from "./OrderedColumns";
import { DivergingChangeBars, type DivergingRow } from "./DivergingChangeBars";
import type { ComparisonRow } from "./SourceComparisonBars";
import type { DataStoryResult, DataStorySection } from "./DataStoryMessage";

// Story 5 — "UK vacancies (official data)" (added 2026-09-25,
// changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md). The first story built from an outside
// publisher's statistics (the Office for National Statistics' Vacancy Survey), and the first with a
// third labelled movement and a platform-vs-publisher comparison.
// design/market-health/data-stories.md — Story 5; frontend/specs/market-health/architecture.md —
// Story 5; backend/specs/market-health/api.md — Story 5 (the response shape this reads).
//
// Rules this renderer keeps:
//  - The publisher's name and exact attribution text render beside the framing line, on the page
//    itself (SourceAttribution) — never only in the Reasoning Panel.
//  - Everything numeric arrives computed from the API; nothing here derives a difference or ratio
//    between the platform's figures and ONS's (the comparison payload carries none, on purpose).
//  - No implementation words in visible copy (no dataset codes, SIC, adapter, series).

// YearOnYearGroupedBars's lazy import (this block's own use of it, mode="level") was removed
// here 2026-09-27 (changes/2026-09-26-data-story-chart-variety.md) — "Which industries are
// changing" now uses DivergingChangeBars, which needs no Nivo import to defer.
const SourceComparisonBars = lazy(() =>
  import("./SourceComparisonBars").then((m) => ({ default: m.SourceComparisonBars })),
);
const CHART_LOADING_FALLBACK = <div className="h-40 animate-pulse rounded bg-gray-800" />;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function section(story: DataStoryResult, id: string): DataStorySection | undefined {
  return story.sections.find((item) => item.id === id);
}

function listFrom(sec: DataStorySection | undefined, key: string): Array<Record<string, unknown>> {
  const value = sec?.content[key];
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function str(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function num(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

function numOrNull(value: unknown): number | null {
  return typeof value === "number" ? value : null;
}

function blockProps(sec: DataStorySection | undefined, hasData: boolean) {
  return {
    qualifier: sec?.qualifier,
    insufficient: sec?.status === "insufficient_data" || !hasData,
    emptyMessage: sec?.message,
  };
}

/** A nested-object field of a section's content, or {} — content.points[i].group, content.table, etc. */
function rec(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}

function seriesPoint(value: unknown): { value: number; index: number; status: "final" | "provisional" | "revised" } {
  const r = rec(value);
  const status = str(r.status);
  return { value: num(r.value), index: num(r.index), status: status === "provisional" || status === "revised" ? status : "final" };
}

/** The eyebrow label that opens each labelled movement of a story. Was 10px/gray-500; corrected
 * 2026-09-27 (changes/2026-09-26-data-story-chart-variety.md, design/visual-design.md's "Story
 * eyebrow") — 3.04:1 on gray-800, under the 4.5:1 text minimum. */
function MovementLabel({ children }: { children: string }) {
  return <p className="text-xs font-medium uppercase tracking-widest text-gray-400">{children}</p>;
}

const MONTHS: Record<string, string> = {
  Jan: "January", Feb: "February", Mar: "March", Apr: "April", May: "May", Jun: "June",
  Jul: "July", Aug: "August", Sep: "September", Oct: "October", Nov: "November", Dec: "December",
};

/** "Jun-Aug 2026" -> "August 2026" (the month a three-month period ends). Falls back to the raw label. */
function periodEnd(label: string): string {
  const m = /^[A-Za-z]{3}-\s*([A-Za-z]{3})\s+(\d{4})$/.exec(label.trim());
  if (!m) return label;
  const month = MONTHS[m[1].charAt(0).toUpperCase() + m[1].slice(1).toLowerCase()];
  return month ? `${month} ${m[2]}` : label;
}

/** "Jun-Aug 2026" -> "Aug 2026" (short, for a caption). */
function periodEndShort(label: string): string {
  const m = /^[A-Za-z]{3}-\s*([A-Za-z]{3})\s+(\d{4})$/.exec(label.trim());
  return m ? `${m[1]} ${m[2]}` : label;
}

function changeLine(change: number | null, pct: number | null, previousLabel: string | null): string | null {
  if (change === null || !previousLabel) return null;
  const since = `than the three months to ${periodEnd(previousLabel)}`;
  const pctText = pct === null ? "" : ` (${pct > 0 ? "+" : pct < 0 ? "−" : ""}${Math.abs(pct).toLocaleString(undefined, { maximumFractionDigits: 1 })}%)`;
  const n = Math.abs(change).toLocaleString();
  if (change < 0) return `▼ ${n} fewer ${since}${pctText}`;
  if (change > 0) return `▲ ${n} more ${since}${pctText}`;
  return `– no change ${since}`;
}

/** A long official industry name, shortened for a bar label: "Wholesale and retail trade; repair of …" -> "Wholesale and retail trade". */
function shortIndustry(label: string): string {
  return label.split(";")[0];
}

export function UkVacanciesStoryMessage({ story }: { story: DataStoryResult }) {
  const totalSection = section(story, "uk-vacancies-total");
  const industrySection = section(story, "uk-vacancies-by-industry");
  const sizeSection = section(story, "uk-vacancies-by-size");
  const techSection = section(story, "uk-tech-and-communications");
  const shiftSection = section(story, "uk-industry-shift");
  const crossSection = section(story, "industry-crosscheck");
  // Added 2026-09-27 (changes/2026-09-25-employer-size-standard-bands.md, Step 7/8) — the size
  // dimension's own comparison block, a sibling to crossSection above, same shape.
  const sizeCrossSection = section(story, "size-crosscheck");

  // The attribution comes from whichever section carries it (the API puts the same object on every
  // section with an ONS figure); absent only when nothing has been collected yet.
  const attribution: SourceAttributionData | null =
    [totalSection, industrySection, sizeSection, techSection, shiftSection, crossSection, sizeCrossSection]
      .map((s) => s?.content.attribution)
      .find(isSourceAttribution) ?? null;

  const totalContent = totalSection?.content ?? {};
  const periodLabel = str(totalContent.period_label);
  const total = num(totalContent.total);
  const previousLabel = str(totalContent.previous_period_label) || null;
  const line = changeLine(numOrNull(totalContent.change), numOrNull(totalContent.change_pct), previousLabel);

  const industryRows: RankedBarRow[] = listFrom(industrySection, "rows")
    .map((r) => ({ label: shortIndustry(str(r.label)), value: num(r.value) }))
    .filter((r) => r.label !== "");

  // Fixed size order from the API — the order IS the meaning, so it is never re-sorted here.
  // Revised 2026-09-27 (changes/2026-09-26-data-story-chart-variety.md) — was a RankedBarList
  // "in size order"; OrderedColumns makes that order structural rather than a caveat.
  const sizeRows: OrderedColumnRow[] = listFrom(sizeSection, "rows")
    .map((r) => {
      const share = num(r.share_pct);
      return {
        label: str(r.label),
        value: share,
        valueLabel: `${share.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}% · ${num(r.value).toLocaleString()}k`,
      };
    })
    .filter((r) => r.label !== "");

  // Revised 2026-09-27 — was rendered via YearOnYearGroupedBars mode="level"; DivergingChangeBars
  // replaces it (design/market-health/data-stories.md — Story 5, block 5). Same row shape
  // (label/current/prior/delta), so the mapping itself is unchanged.
  const shiftRows: DivergingRow[] = listFrom(shiftSection, "rows")
    .map((r) => ({
      label: shortIndustry(str(r.label)),
      current: num(r.current),
      prior: num(r.prior),
      delta: num(r.delta),
    }))
    .filter((r) => r.label !== "");
  const priorPeriodLabel = str(shiftSection?.content.prior_period_label) || null;

  // Block 4a — "Tech and communications vacancies since 2001" (changes/2026-09-26-story-5-tech-lens.md).
  // Every value is a straight pass-through from the API — the index, peak and table rows are all
  // computed server-side; nothing here re-derives them.
  const techContent = techSection?.content ?? {};
  const techGroupLabel = str(rec(techContent.group).label) || "Information and communication";
  const techPoints: TrendPoint[] = listFrom(techSection, "points")
    .map((r) => ({ periodStart: str(r.period_start), label: str(r.label), words: str(r.words), group: seriesPoint(r.group), all: seriesPoint(r.all) }))
    .filter((p) => p.periodStart !== "" && p.label !== "");
  const techPeakRaw = rec(techContent.peak);
  const techPeak = { periodLabel: str(techPeakRaw.period_label), value: num(techPeakRaw.value), index: num(techPeakRaw.index) };
  const techLatestRaw = rec(techContent.latest);
  const techLatest = {
    periodLabel: str(techLatestRaw.period_label),
    periodWords: str(techLatestRaw.period_words),
    provisional: Boolean(techContent.provisional),
  };
  const techTable = rec(techContent.table);
  const techTableRows = (Array.isArray(techTable.rows) ? techTable.rows.filter(isRecord) : []).map((r) => ({
    periodLabel: str(r.period_label), groupValue: num(r.group_value), allValue: num(r.all_value),
    groupIndex: num(r.group_index), allIndex: num(r.all_index),
  }));

  const crossContent = crossSection?.content ?? {};
  const crossRows: ComparisonRow[] = listFrom(crossSection, "rows")
    .map((r) => ({
      label: shortIndustry(str(r.label)),
      primary: numOrNull(r.primary_share_pct),
      secondary: numOrNull(r.secondary_share_pct),
    }))
    .filter((r) => r.label !== "");

  // Size labels ("1–9 employees", "Not placed in a size band") are already short and carry no
  // official long-form name to trim, unlike industry labels — no shortIndustry() here.
  const sizeCrossContent = sizeCrossSection?.content ?? {};
  const sizeCrossRows: ComparisonRow[] = listFrom(sizeCrossSection, "rows")
    .map((r) => ({
      label: str(r.label),
      primary: numOrNull(r.primary_share_pct),
      secondary: numOrNull(r.secondary_share_pct),
    }))
    .filter((r) => r.label !== "");

  // With nothing collected yet there is no period to name — never render "three months to ." (a real bug the
  // server-side render check found on the empty state).
  const inPeriod = periodLabel ? `, three months to ${periodEndShort(periodLabel)}` : "";

  const framing = periodLabel
    ? `Official estimates of UK job vacancies from the Office for National Statistics, for the three months to ${periodEnd(periodLabel)}. They cover the whole UK economy, not only the roles this platform tracks.`
    : "Official estimates of UK job vacancies from the Office for National Statistics. They cover the whole UK economy, not only the roles this platform tracks.";

  return (
    <article className="space-y-5" aria-label={story.question}>
      <div>
        <h2 className="text-lg font-semibold text-gray-100">UK vacancies (official data)</h2>
        <p className="mt-1 text-xs text-gray-400">Updated {new Date(story.as_of).toLocaleString()}</p>
      </div>

      {/* Framing line, then the publisher's name and exact attribution — on the page itself. */}
      <p className="text-sm leading-relaxed text-gray-300">{framing}</p>
      {attribution ? (
        <SourceAttribution attribution={attribution} />
      ) : story.attribution_text ? (
        <p className="text-xs text-gray-400">{story.attribution_text}</p>
      ) : null}

      <MovementLabel>The UK market right now</MovementLabel>

      <StoryBlock heading="UK job vacancies" {...blockProps(totalSection, total > 0)}>
        <StoryFigure
          value={total.toLocaleString()}
          caption={`estimated job vacancies, three months to ${periodEndShort(periodLabel)}`}
        />
        {line ? <p className="mt-2 text-sm text-gray-400">{line}</p> : null}
      </StoryBlock>

      <StoryBlock
        heading="Vacancies by industry"
        subtitle={`Estimated vacancies by industry, in thousands${inPeriod}.`}
        {...blockProps(industrySection, industryRows.length > 0)}
      >
        <RankedBarList rows={industryRows} limit={10} />
      </StoryBlock>

      <StoryBlock
        heading="Vacancies by size of business"
        subtitle="Share of all vacancies, by how many people the employing business has."
        {...blockProps(sizeSection, sizeRows.length > 0)}
      >
        <OrderedColumns
          rows={sizeRows}
          tableCaption="Share of all vacancies, by how many people the employing business has."
        />
      </StoryBlock>

      <MovementLabel>How it's shifting</MovementLabel>

      <StoryBlock
        heading="Tech and communications vacancies since 2001"
        subtitle={str(techContent.subtitle)}
        {...blockProps(techSection, techPoints.length > 0)}
      >
        {/* StoryBlock's own qualifier slot was text-gray-500 until changes/2026-09-26-data-story-chart-variety.md
            fixed it (now text-gray-400, matching the Chart accessibility standard) — this block used to render
            its qualifier manually to work around that; now that the shared fix has landed, it uses the normal
            blockProps path like every other block, above. */}
        <TechCommsTrendChart
          points={techPoints}
          groupLabel={techGroupLabel}
          yAxisTitle={str(techContent.y_axis_title)}
          peak={techPeak}
          latest={techLatest}
          legend={str(techContent.legend)}
          ariaLabel={str(techContent.aria_label)}
          summary={str(techContent.summary)}
          table={{ caption: str(techTable.caption), rows: techTableRows }}
        />
      </StoryBlock>

      <StoryBlock
        heading="Which industries are changing"
        subtitle={`Change in estimated vacancies by industry, in thousands: ${periodLabel ? `three months to ${periodEndShort(periodLabel)}` : "the latest three months"} vs. the same three months a year earlier.`}
        {...blockProps(shiftSection, shiftRows.length > 0)}
      >
        <DivergingChangeBars
          rows={shiftRows}
          unit="thousand"
          tableCaption="Change in estimated vacancies by industry, in thousands, this year vs. a year earlier."
          currentPeriodLabel={periodLabel || "This period"}
          priorPeriodLabel={priorPeriodLabel || "A year earlier"}
        />
        <p className="mt-2 text-sm text-gray-400">
          A drop can mean slower hiring or roles being filled faster — this shows the change, not the reason.
        </p>
      </StoryBlock>

      <MovementLabel>How this compares with the roles we track</MovementLabel>

      <StoryBlock
        heading="Where our roles sit against the UK market"
        subtitle="Share of the UK-based roles we track, and share of all UK vacancies, by industry group."
        {...blockProps(crossSection, crossRows.length > 0)}
      >
        {/* The legend is composed by the API (names, denominators, dates) — shown above the chart. */}
        {str(crossContent.legend) ? <p className="mb-2 text-xs text-gray-400">{str(crossContent.legend)}</p> : null}
        <Suspense fallback={CHART_LOADING_FALLBACK}>
          <SourceComparisonBars
            rows={crossRows}
            primaryName={str(crossContent.primary_name) || "Roles we track"}
            secondaryName={str(crossContent.secondary_name) || "UK vacancies (official)"}
          />
        </Suspense>
      </StoryBlock>

      {/* Added 2026-09-27 (changes/2026-09-25-employer-size-standard-bands.md, Step 7/8) — same
          two-series-comparison form as the block above, deliberately reused for the size
          dimension rather than given a new form (design/market-health/data-stories.md — Story 5,
          block 7). */}
      <StoryBlock
        heading="Where our headcount profile sits against the UK market"
        subtitle="Share of the UK-based roles we track, and share of all UK vacancies, by size of the employing business."
        {...blockProps(sizeCrossSection, sizeCrossRows.length > 0)}
      >
        {str(sizeCrossContent.legend) ? <p className="mb-2 text-xs text-gray-400">{str(sizeCrossContent.legend)}</p> : null}
        <Suspense fallback={CHART_LOADING_FALLBACK}>
          <SourceComparisonBars
            rows={sizeCrossRows}
            primaryName={str(sizeCrossContent.primary_name) || "Roles we track"}
            secondaryName={str(sizeCrossContent.secondary_name) || "UK vacancies (official)"}
          />
        </Suspense>
      </StoryBlock>
    </article>
  );
}
