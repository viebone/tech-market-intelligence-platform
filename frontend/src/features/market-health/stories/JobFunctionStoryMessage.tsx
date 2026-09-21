import { RankedBarList, type RankedBarRow } from "./RankedBarList";
import { StoryBlock } from "./StoryBlock";
import { Meter } from "./Meter";
import type { DataStoryResult } from "./DataStoryMessage";

// Story 4 — "Beyond Design, Product & Engineering" (added 2026-09-21,
// changes/2026-09-21-job-function-story.md). Built from
// classifications.job_function, populated only for role_category = "other"
// rows — never a fourth tracked category, never blended into the trend
// chart's own 3-line split. One movement, no year-on-year block (Job
// Function is brand new; there is no prior-year window yet). See
// design/market-health/data-stories.md — Story 4.

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

export function JobFunctionStoryMessage({ story }: { story: DataStoryResult }) {
  const breakdownSection = section(story, "beyond-tracked-roles-breakdown");
  const scaleSection = section(story, "beyond-tracked-roles-scale");
  const titlesSection = section(story, "beyond-tracked-roles-top-titles");

  const functionRows: RankedBarRow[] = listFrom(breakdownSection, "functions")
    .map((row) => ({ label: str(row.job_function), value: num(row.posting_count) }))
    .filter((row) => row.label !== "");

  const scaleContent = scaleSection?.content ?? {};
  const otherCount = num(scaleContent.other_count);
  const totalCount = num(scaleContent.total_count);
  const otherShare = num(scaleContent.other_share);

  const largestFunction = str(titlesSection?.content.job_function) || "the largest function";
  const titleRows: RankedBarRow[] = listFrom(titlesSection, "titles")
    .map((row) => ({ label: str(row.title), value: num(row.posting_count) }))
    .filter((row) => row.label !== "");

  return (
    <article className="space-y-5" aria-label={story.question}>
      <div>
        <h2 className="text-lg font-semibold text-gray-100">Beyond Design, Product &amp; Engineering</h2>
        <p className="mt-1 text-xs text-gray-500">Updated {new Date(story.as_of).toLocaleString()}</p>
      </div>

      {/* Framing line — states this is the picture beyond the 3 tracked categories,
          never a reconciliation or a 4th category. */}
      <p className="text-sm leading-relaxed text-gray-300">
        What the tracked companies are hiring for outside Design, Product, and Engineering —
        never a fourth tracked role category, and never blended into the trend chart above.
      </p>

      <StoryBlock
        heading="What the wider hiring picture looks like"
        subtitle="Postings outside Design, Product, and Engineering, by function."
        {...blockProps(breakdownSection, functionRows.length > 0)}
      >
        <RankedBarList rows={functionRows} limit={11} />
      </StoryBlock>

      <StoryBlock
        heading="How much of all hiring this actually is"
        {...blockProps(scaleSection, totalCount > 0)}
      >
        <Meter
          percent={otherShare}
          caption="of all classified postings are outside the 3 tracked categories"
          complement={`${otherCount.toLocaleString()} of ${totalCount.toLocaleString()} classified postings. The trend chart and "What we know about the market" only ever show the tracked slice.`}
        />
      </StoryBlock>

      <StoryBlock
        heading={`Most common titles in ${largestFunction}`}
        subtitle="Real job titles, not normalized."
        {...blockProps(titlesSection, titleRows.length > 0)}
      >
        <RankedBarList rows={titleRows} limit={10} />
      </StoryBlock>
    </article>
  );
}
