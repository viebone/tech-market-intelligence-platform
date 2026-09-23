import { lazy, Suspense } from "react";
import { RankedBarList, type RankedBarRow } from "./RankedBarList";
import { StoryBlock } from "./StoryBlock";
import type { YearOnYearContent } from "./YearOnYearGroupedBars";
import type { SkillDemandRow } from "./SkillDemandChart";
import { EmploymentRiskStoryMessage } from "./EmploymentRiskStoryMessage";
import { MarketBenchmarkStoryMessage } from "./MarketBenchmarkStoryMessage";
import { JobFunctionStoryMessage } from "./JobFunctionStoryMessage";
import { StoryFeedbackReaction } from "../../feedback/StoryFeedbackReaction";

// Lazy-loaded (added 2026-09-22, changes/2026-09-22-nivo-charting-library.md) — these two
// pull in @nivo/bar + @nivo/theming (~90KB gzipped, confirmed by a real build: the initial
// bundle grew from 130KB to 218KB gzipped before this fix, and Vite started warning about a
// >500KB chunk). Loaded only when a story that actually renders one of these blocks is
// opened, not bundled into every visitor's initial page load.
const YearOnYearGroupedBars = lazy(() =>
  import("./YearOnYearGroupedBars").then((m) => ({ default: m.YearOnYearGroupedBars })),
);
const SkillDemandChart = lazy(() =>
  import("./SkillDemandChart").then((m) => ({ default: m.SkillDemandChart })),
);
const SharePieChart = lazy(() =>
  import("./SharePieChart").then((m) => ({ default: m.SharePieChart })),
);
const CHART_LOADING_FALLBACK = <div className="h-40 animate-pulse rounded bg-gray-800" />;

// 2-category share colours — indigo-500 for the named/primary slice, gray-600 muted for its
// complement. Same convention as SkillDemandChart/YearOnYearGroupedBars: one accent, one
// neutral — never two accent hues in the same chart (design/visual-design.md — Charting
// library).
const DISCLOSED_COLOR = "#6366f1";
const UNDISCLOSED_COLOR = "#4b5563";

// Per-story renderer. Composes a framing line + StoryBlocks from the shared
// data-story component set (RankedBarList / StoryFigure / Meter), so every
// catalogue entry looks and reads like the last one. Standard:
// design/visual-design.md - Data Story composition; checklist:
// design/market-health/data-stories.md - Visual standard every story must meet;
// frontend/specs/market-health/architecture.md - Every story: the shared build.

export interface DataStorySection {
  id: string;
  title: string;
  status: "ready" | "insufficient_data";
  content: Record<string, unknown>;
  qualifier: string;
  message?: string;
}

export interface DataStoryResult {
  story_id: string;
  question: string;
  as_of: string;
  sections: DataStorySection[];
  provenance: {
    sources: string[];
    model_used: boolean;
    query_time: string;
  };
  limitations: string[];
  /** Added 2026-09-18 (Story 3, market-benchmark) — a source's licence
   * attribution text, when the story's data requires visible credit on the
   * page itself, not only in the Reasoning Panel. Absent for every other
   * story. */
  attribution_text?: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function section(story: DataStoryResult, id: string): DataStorySection | undefined {
  return story.sections.find((item) => item.id === id);
}

function listFrom(sectionValue: DataStorySection | undefined, key: string): Array<Record<string, unknown>> {
  const value = sectionValue?.content[key];
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function str(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function num(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

const HIDDEN_ROLE_LABELS = new Set(["other", "unknown", ""]);

/** Bridges a resolved section to StoryBlock's props: empty when insufficient_data or no rows. */
function blockProps(sec: DataStorySection | undefined, hasData: boolean) {
  return {
    qualifier: sec?.qualifier,
    insufficient: sec?.status === "insufficient_data" || !hasData,
    emptyMessage: sec?.message,
  };
}

/** The eyebrow label that opens each movement of a two-movement story. */
function MovementLabel({ children }: { children: string }) {
  return (
    <p className="text-[10px] font-medium uppercase tracking-widest text-gray-500">{children}</p>
  );
}

function yoyContent(sec: DataStorySection | undefined): YearOnYearContent | undefined {
  const c = sec?.content;
  return c && Array.isArray((c as { rows?: unknown }).rows)
    ? (c as unknown as YearOnYearContent)
    : undefined;
}

// Display-only relabel (2026-09-22 — changes/2026-09-22-role-category-display-relabel.md):
// "Design" / "Product Management" / "Engineering" reads as the occupation family, matching
// job-classification.md's own internal "occupation family" reasoning. YearOnYearGroupedBars
// is generic (reused for role_category/level/track shifts alike), so this is applied only at
// the role-mix-shift call site below, not inside the shared component — level/track values
// must never pass through this map.
const ROLE_CATEGORY_LABEL: Record<string, string> = {
  Designer: "Design",
  "Product Manager": "Product Management",
  Engineer: "Engineering",
};

function relabelRoleCategoryRows(content: YearOnYearContent): YearOnYearContent {
  return {
    ...content,
    rows: content.rows.map((row) => ({ ...row, value: ROLE_CATEGORY_LABEL[row.value] ?? row.value })),
  };
}

// A thin router as the catalogue grows past one entry (added 2026-09-11) —
// "a switch on story_id inside one file while the catalogue is small"
// (frontend/specs/market-health/architecture.md — Every story: the shared
// build). market-data-briefing keeps rendering inline below, unchanged.
function renderStory(story: DataStoryResult) {
  if (story.story_id === "employment-risk-overview") {
    return <EmploymentRiskStoryMessage story={story} />;
  }
  if (story.story_id === "market-benchmark") {
    return <MarketBenchmarkStoryMessage story={story} />;
  }
  if (story.story_id === "beyond-tracked-roles") {
    return <JobFunctionStoryMessage story={story} />;
  }

  const roles = section(story, "roles-offered");
  const skills = section(story, "employer-mentioned-skills");
  const pay = section(story, "compensation-coverage");
  const geo = section(story, "geographic-coverage");
  const roleMixShift = section(story, "role-mix-shift");
  const seniorityShift = section(story, "seniority-shift");
  const trackShift = section(story, "track-shift");

  // The roles being hired — specialization is the meaningful "role", not the fragmented raw title.
  const roleRows: RankedBarRow[] = listFrom(roles, "top_specializations")
    .map((row) => ({ label: str(row.specialization), value: num(row.posting_count) }))
    .filter((row) => !HIDDEN_ROLE_LABELS.has(row.label.toLowerCase()))
    .slice(0, 7);

  // What employers ask for — must-have and nice-to-have kept as two real series
  // (added 2026-09-22, changes/2026-09-22-nivo-charting-library.md — see SkillDemandChart;
  // this used to collapse both into one number with a must-have opacity flag).
  const skillAgg = new Map<string, { mustHave: number; niceToHave: number }>();
  for (const row of listFrom(skills, "skills")) {
    const group = str(row.skill_group);
    if (!group) continue;
    const prev = skillAgg.get(group) ?? { mustHave: 0, niceToHave: 0 };
    const isMustHave = str(row.requirement_level) === "must_have";
    skillAgg.set(group, {
      mustHave: prev.mustHave + (isMustHave ? num(row.posting_count) : 0),
      niceToHave: prev.niceToHave + (isMustHave ? 0 : num(row.posting_count)),
    });
  }
  const skillRows: SkillDemandRow[] = [...skillAgg.entries()].map(
    ([skill_group, { mustHave, niceToHave }]) => ({
      skill_group,
      must_have: mustHave,
      nice_to_have: niceToHave,
    }),
  );

  // Pay transparency — share of postings that state a salary (structured + parsed).
  const payRows = listFrom(pay, "coverage_by_confidence");
  const disclosed = payRows
    .filter((row) => str(row.confidence) === "structured" || str(row.confidence) === "parsed")
    .reduce((sum, row) => sum + num(row.posting_count), 0);
  const payTotal = payRows.reduce((sum, row) => sum + num(row.posting_count), 0);

  // Where the roles are — top cities among the minority that carry a normalised location.
  const cityRows: RankedBarRow[] = listFrom(geo, "cities")
    .map((row) => ({ label: str(row.city), value: num(row.posting_count) }))
    .filter((row) => row.label !== "")
    .slice(0, 7);

  return (
    <article className="space-y-5" aria-label={story.question}>
      <div>
        <h2 className="text-lg font-semibold text-gray-100">What we know about the market</h2>
        <p className="mt-1 text-xs text-gray-500">Updated {new Date(story.as_of).toLocaleString()}</p>
      </div>

      <MovementLabel>The market right now</MovementLabel>

      {/* Framing line — no inventory figures; the welcome already carries those. */}
      <p className="text-sm leading-relaxed text-gray-300">
        Past the headcount, this is what the tech postings the platform tracks are actually
        asking for — the roles on offer, the skills employers name, how often pay is disclosed,
        and where the work sits.
      </p>

      <StoryBlock
        heading="The roles being hired"
        subtitle="Open postings currently tracked, by specialization."
        {...blockProps(roles, roleRows.length > 0)}
      >
        <RankedBarList rows={roleRows} />
      </StoryBlock>

      <StoryBlock
        heading="What employers ask for"
        subtitle="Postings mentioning each skill group, must-have vs. nice-to-have."
        {...blockProps(skills, skillRows.length > 0)}
      >
        <Suspense fallback={CHART_LOADING_FALLBACK}>
          <SkillDemandChart rows={skillRows} limit={8} />
        </Suspense>
      </StoryBlock>

      <StoryBlock
        heading="Pay transparency"
        subtitle="Postings that state a salary range vs. those that don't."
        {...blockProps(pay, payTotal > 0)}
      >
        <Suspense fallback={CHART_LOADING_FALLBACK}>
          <SharePieChart
            slices={[
              { id: "disclosed", label: "States a salary range", value: disclosed, color: DISCLOSED_COLOR },
              { id: "undisclosed", label: "Doesn't disclose", value: payTotal - disclosed, color: UNDISCLOSED_COLOR },
            ]}
          />
        </Suspense>
      </StoryBlock>

      <StoryBlock
        heading="Where the roles are"
        subtitle="Open postings currently tracked, by city."
        {...blockProps(geo, cityRows.length > 0)}
      >
        <RankedBarList rows={cityRows} />
      </StoryBlock>

      <MovementLabel>How it&rsquo;s shifting — year on year</MovementLabel>

      {([
        [roleMixShift, "How the role mix is shifting", "Share of postings by role category, this year vs. the year before.", true],
        [seniorityShift, "How seniority is shifting", "Share of postings by seniority level, this year vs. the year before.", false],
        [trackShift, "IC vs. management", "Share of postings by track, this year vs. the year before.", false],
      ] as const).map(([sec, heading, subtitle, isRoleCategory]) => {
        const rawContent = yoyContent(sec);
        const content = rawContent && isRoleCategory ? relabelRoleCategoryRows(rawContent) : rawContent;
        return (
          <StoryBlock
            key={heading}
            heading={heading}
            subtitle={subtitle}
            {...blockProps(sec, !!content && content.rows.length > 0)}
          >
            {content ? (
              <Suspense fallback={CHART_LOADING_FALLBACK}>
                <YearOnYearGroupedBars content={content} />
              </Suspense>
            ) : null}
          </StoryBlock>
        );
      })}
    </article>
  );
}

// Every Data Story — however it's routed above — ends with the same feedback
// reaction (added 2026-09-23, changes/2026-09-23-user-feedback-mechanism.md).
// A single change point here, rather than one inside each of the four
// branches, keeps the reaction generic across the whole catalogue as it grows
// — design/market-health/data-stories.md — "Feedback reaction — every story".
export function DataStoryMessage({ story }: { story: DataStoryResult }) {
  const renderedStory = renderStory(story);
  return (
    <>
      {renderedStory}
      <StoryFeedbackReaction storyId={story.story_id} />
    </>
  );
}
