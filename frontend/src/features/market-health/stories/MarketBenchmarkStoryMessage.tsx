import { RankedBarList, type RankedBarRow } from "./RankedBarList";
import { StoryBlock } from "./StoryBlock";
import { Meter } from "./Meter";
import type { DataStoryResult } from "./DataStoryMessage";

// Story 3 — "Independent market benchmark" (added 2026-09-18,
// changes/2026-09-18-market-benchmark-story.md). Built from
// market_observations/skill_associations (source="itjobswatch"), deliberately
// never joined to or compared against raw_postings/classifications — a
// separate third-party benchmark, not a reconciliation. One movement, no
// year-on-year block (each tracked role has exactly one observed period so
// far). See design/market-health/data-stories.md — Story 3.

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

const formatCurrency = (n: number) => `£${Math.round(n).toLocaleString()}`;

export function MarketBenchmarkStoryMessage({ story }: { story: DataStoryResult }) {
  const demandSection = section(story, "market-benchmark-demand");
  const coverageSection = section(story, "market-benchmark-coverage");
  const paySection = section(story, "market-benchmark-pay");
  const skillsSection = section(story, "market-benchmark-skills");

  const demandRows: RankedBarRow[] = listFrom(demandSection, "roles")
    .map((row) => ({ label: str(row.entity_name), value: num(row.vacancy_count) }))
    .filter((row) => row.label !== "");

  const payRows: RankedBarRow[] = listFrom(paySection, "roles")
    .map((row) => ({ label: str(row.entity_name), value: num(row.salary_median) }))
    .filter((row) => row.label !== "");

  const skillRows: RankedBarRow[] = listFrom(skillsSection, "skills")
    .map((row) => ({ label: str(row.skill_name), value: num(row.job_count) }))
    .filter((row) => row.label !== "");

  const coverageContent = coverageSection?.content ?? {};
  const totalVacanciesTracked = num(coverageContent.total_vacancies_tracked);
  const salaryCoverageShare = num(coverageContent.salary_coverage_share);
  const rolesWithSalaryData = num(coverageContent.roles_with_salary_data);
  const observedRoleCount = num(coverageContent.observed_role_count);

  return (
    <article className="space-y-5" aria-label={story.question}>
      <div>
        <h2 className="text-lg font-semibold text-gray-100">Independent market benchmark</h2>
        <p className="mt-1 text-xs text-gray-500">Updated {new Date(story.as_of).toLocaleString()}</p>
      </div>

      {/* Framing line — states this is an independent third-party read, never
          blended with this platform's own postings numbers. */}
      <p className="text-sm leading-relaxed text-gray-300">
        A second, independent read on tech hiring demand and pay — from a specialist
        third-party market-data site, not this platform's own observed job postings. Shown
        separately, never merged with the numbers above.
      </p>
      {/* Visible attribution — rendered on the page itself, not only in the Reasoning
          Panel, per the source licence's own attribution condition. */}
      {story.attribution_text ? (
        <p className="text-xs text-gray-500">{story.attribution_text}</p>
      ) : null}

      <StoryBlock
        heading="Demand across tracked roles"
        subtitle="Permanent vacancies currently tracked by IT Jobs Watch, by role."
        {...blockProps(demandSection, demandRows.length > 0)}
      >
        <RankedBarList rows={demandRows} limit={10} />
      </StoryBlock>

      <StoryBlock
        heading="Coverage and pay data availability"
        {...blockProps(coverageSection, observedRoleCount > 0)}
      >
        <Meter
          percent={salaryCoverageShare}
          caption="of tracked roles have salary data reported"
          complement={`${totalVacanciesTracked.toLocaleString()} permanent vacancies tracked across ${observedRoleCount} observed role(s) (${rolesWithSalaryData} with salary data).`}
        />
      </StoryBlock>

      <StoryBlock
        heading="Typical pay by role"
        subtitle="Median annual salary (50th percentile), by role."
        {...blockProps(paySection, payRows.length > 0)}
      >
        <RankedBarList rows={payRows} limit={10} formatValue={formatCurrency} />
      </StoryBlock>

      <StoryBlock
        heading="Skills most associated with these roles"
        subtitle="Summed mention count across the tracked roles' vacancies, from IT Jobs Watch's own weighted skill data."
        {...blockProps(skillsSection, skillRows.length > 0)}
      >
        <RankedBarList rows={skillRows} limit={10} />
      </StoryBlock>
    </article>
  );
}
