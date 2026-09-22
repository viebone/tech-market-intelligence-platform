import { lazy, Suspense } from "react";
import { RankedBarList, type RankedBarRow } from "./RankedBarList";
import { StoryBlock } from "./StoryBlock";
import type { DataStoryResult } from "./DataStoryMessage";

// Lazy-loaded, same pattern as changes/2026-09-22-nivo-charting-library.md.
const SharePieChart = lazy(() =>
  import("./SharePieChart").then((m) => ({ default: m.SharePieChart })),
);
const CHART_LOADING_FALLBACK = <div className="h-40 animate-pulse rounded bg-gray-800" />;
const OUTSIDE_COLOR = "#6366f1"; // indigo-500 — the named/primary slice, this story's own subject
const INSIDE_COLOR = "#4b5563"; // gray-600 — muted; deliberately not a role accent, since
// "inside the 3 tracked categories" isn't itself Design/Product/Engineering as a single hue

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
        What the tracked companies are hiring for outside Design, Product Management, and
        Engineering — never a fourth tracked role category, and never blended into the trend
        chart above.
      </p>

      <StoryBlock
        heading="What the wider hiring picture looks like"
        subtitle="Postings outside Design, Product Management, and Engineering, by function."
        {...blockProps(breakdownSection, functionRows.length > 0)}
      >
        <RankedBarList rows={functionRows} limit={11} />
      </StoryBlock>

      <StoryBlock
        heading="How much of all hiring this actually is"
        subtitle="All classified postings, split by whether they're inside or outside the 3 tracked categories."
        {...blockProps(scaleSection, totalCount > 0)}
      >
        <Suspense fallback={CHART_LOADING_FALLBACK}>
          <SharePieChart
            slices={[
              { id: "outside", label: "Outside the 3 tracked categories", value: otherCount, color: OUTSIDE_COLOR },
              { id: "inside", label: "Design, Product Management, Engineering", value: totalCount - otherCount, color: INSIDE_COLOR },
            ]}
          />
        </Suspense>
        <p className="mt-2 text-xs text-gray-500">
          {otherCount.toLocaleString()} of {totalCount.toLocaleString()} classified postings
          ({otherShare.toFixed(1)}%). The trend chart and "What we know about the market" only
          ever show the tracked slice.
        </p>
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
