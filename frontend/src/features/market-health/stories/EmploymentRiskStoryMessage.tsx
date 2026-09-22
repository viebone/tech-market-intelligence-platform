import { lazy, Suspense } from "react";
import { RankedBarList, type RankedBarRow } from "./RankedBarList";
import { StoryBlock } from "./StoryBlock";
import { WorldRiskMap, type CountryRiskRow } from "./WorldRiskMap";
import type { DataStoryResult } from "./DataStoryMessage";

// Lazy-loaded, same pattern as changes/2026-09-22-nivo-charting-library.md.
const SharePieChart = lazy(() =>
  import("./SharePieChart").then((m) => ({ default: m.SharePieChart })),
);
const CHART_LOADING_FALLBACK = <div className="h-40 animate-pulse rounded bg-gray-800" />;
const CONTRACTION_COLOR = "#dc2626"; // red-600 — matches WorldRiskMap's own contraction hue
const EXPANSION_COLOR = "#059669"; // emerald-600 — matches WorldRiskMap's own expansion hue

// Story 2 — "Employment risk across the market" (added 2026-09-11,
// changes/2026-09-11-employment-events-independent-scope.md). Built from
// employment_events, deliberately independent of the platform's 35 tracked
// job-posting companies — the company-independent counterpart to the trend
// chart's tracked-company-scoped EmploymentEventsStrip. One movement, no
// year-on-year block (event data isn't a 12-month-comparable series the way
// posting volume is). See design/market-health/data-stories.md — Story 2.

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function section(story: DataStoryResult, id: string) {
  return story.sections.find((item) => item.id === id);
}

function listFrom(sec: ReturnType<typeof section>, key: string): Array<Record<string, unknown>> {
  const value = sec?.content[key];
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function str(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function num(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

function blockProps(sec: ReturnType<typeof section>, hasData: boolean) {
  return {
    qualifier: sec?.qualifier,
    insufficient: sec?.status === "insufficient_data" || !hasData,
    emptyMessage: sec?.message,
  };
}

export function EmploymentRiskStoryMessage({ story }: { story: DataStoryResult }) {
  const directionSection = section(story, "contraction-vs-expansion");
  const companiesSection = section(story, "employment-risk-companies");
  const countriesSection = section(story, "employment-risk-countries");
  const sectorsSection = section(story, "employment-risk-sectors");

  const directionContent = directionSection?.content ?? {};
  const contractionRolesAffected = num(directionContent.contraction_roles_affected);
  const contractionShareOfEvents = num(directionContent.contraction_share_of_events);

  const companyRows: RankedBarRow[] = listFrom(companiesSection, "companies")
    .map((row) => ({ label: str(row.company_raw), value: num(row.affected) }))
    .filter((row) => row.label !== "");

  const countryRiskRows: CountryRiskRow[] = listFrom(countriesSection, "countries")
    .map((row) => ({
      country: str(row.country),
      contraction_events: num(row.contraction_events),
      contraction_affected: num(row.contraction_affected),
      expansion_events: num(row.expansion_events),
      expansion_affected: num(row.expansion_affected),
    }))
    .filter((row) => row.country !== "");

  const sectorRows: RankedBarRow[] = listFrom(sectorsSection, "sectors")
    .map((row) => ({ label: str(row.sector), value: num(row.affected) }))
    .filter((row) => row.label !== "");

  return (
    <article className="space-y-5" aria-label={story.question}>
      <div>
        <h2 className="text-lg font-semibold text-gray-100">Employment risk across the market</h2>
        <p className="mt-1 text-xs text-gray-500">Updated {new Date(story.as_of).toLocaleString()}</p>
      </div>

      {/* Framing line — states this is independent of the tracked-company chart. */}
      <p className="text-sm leading-relaxed text-gray-300">
        Reported layoffs, closures, restructuring, and expansion activity across the market
        over the last 12 months — from external registries, independent of the companies this
        platform tracks job postings for.
      </p>

      <StoryBlock
        heading="Where it's happening"
        subtitle="Hiring and layoff activity by country, over the trailing 12 months."
        {...blockProps(countriesSection, countryRiskRows.length > 0)}
      >
        <WorldRiskMap rows={countryRiskRows} />
      </StoryBlock>

      <StoryBlock
        heading="Contraction vs. expansion"
        subtitle="Share of reported events by direction, over the trailing 12 months."
        {...blockProps(directionSection, contractionRolesAffected > 0 || contractionShareOfEvents > 0)}
      >
        <Suspense fallback={CHART_LOADING_FALLBACK}>
          <SharePieChart
            slices={[
              { id: "contraction", label: "Contraction (layoffs, closures, restructuring)", value: contractionShareOfEvents, color: CONTRACTION_COLOR },
              { id: "expansion", label: "Expansion", value: 100 - contractionShareOfEvents, color: EXPANSION_COLOR },
            ]}
          />
        </Suspense>
        <p className="mt-2 text-xs text-gray-500">
          {contractionRolesAffected.toLocaleString()} roles reported affected by contraction events in this window.
        </p>
      </StoryBlock>

      <StoryBlock
        heading="Companies with the most reported impact"
        subtitle="Ranked by jobs reported affected, summed across contraction events in the window."
        {...blockProps(companiesSection, companyRows.length > 0)}
      >
        <RankedBarList rows={companyRows} limit={10} />
      </StoryBlock>

      <StoryBlock
        heading="By sector"
        subtitle="Jobs reported affected, summed by sector — only events whose source reports one."
        {...blockProps(sectorsSection, sectorRows.length > 0)}
      >
        <RankedBarList rows={sectorRows} limit={10} />
      </StoryBlock>
    </article>
  );
}
