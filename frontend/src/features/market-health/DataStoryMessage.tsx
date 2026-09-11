import { RankedBarList, type RankedBarRow } from "./RankedBarList";
import { StoryBlock } from "./StoryBlock";
import { Meter } from "./Meter";
import { YearOnYearBars, type YearOnYearContent } from "./YearOnYearBars";
import { EmploymentRiskStoryMessage } from "./EmploymentRiskStoryMessage";

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

export function DataStoryMessage({ story }: { story: DataStoryResult }) {
  // A thin router as the catalogue grows past one entry (added 2026-09-11) —
  // "a switch on story_id inside one file while the catalogue is small"
  // (frontend/specs/market-health/architecture.md — Every story: the shared
  // build). market-data-briefing keeps rendering inline below, unchanged.
  if (story.story_id === "employment-risk-overview") {
    return <EmploymentRiskStoryMessage story={story} />;
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

  // What employers ask for — one row per skill group, must-have mentions emphasised.
  const skillAgg = new Map<string, { value: number; mustHave: boolean }>();
  for (const row of listFrom(skills, "skills")) {
    const group = str(row.skill_group);
    if (!group) continue;
    const prev = skillAgg.get(group) ?? { value: 0, mustHave: false };
    skillAgg.set(group, {
      value: prev.value + num(row.posting_count),
      mustHave: prev.mustHave || str(row.requirement_level) === "must_have",
    });
  }
  const skillRows: RankedBarRow[] = [...skillAgg.entries()]
    .map(([label, { value, mustHave }]) => ({ label, value, emphasis: mustHave }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);

  // Pay transparency — share of postings that state a salary (structured + parsed).
  const payRows = listFrom(pay, "coverage_by_confidence");
  const disclosed = payRows
    .filter((row) => str(row.confidence) === "structured" || str(row.confidence) === "parsed")
    .reduce((sum, row) => sum + num(row.posting_count), 0);
  const payTotal = payRows.reduce((sum, row) => sum + num(row.posting_count), 0);
  const disclosedPct = payTotal > 0 ? (disclosed / payTotal) * 100 : 0;

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

      <StoryBlock heading="The roles being hired" {...blockProps(roles, roleRows.length > 0)}>
        <RankedBarList rows={roleRows} />
      </StoryBlock>

      <StoryBlock heading="What employers ask for" {...blockProps(skills, skillRows.length > 0)}>
        <RankedBarList rows={skillRows} limit={8} />
        <p className="mt-2 text-xs text-gray-500">Solid bars are must-have mentions.</p>
      </StoryBlock>

      <StoryBlock heading="Pay transparency" {...blockProps(pay, payTotal > 0)}>
        <Meter
          percent={disclosedPct}
          caption="of postings state a salary range"
          complement={`The other ${payTotal > 0 ? `${Math.round(100 - disclosedPct)}%` : "majority"} don't disclose compensation.`}
        />
      </StoryBlock>

      <StoryBlock heading="Where the roles are" {...blockProps(geo, cityRows.length > 0)}>
        <RankedBarList rows={cityRows} />
      </StoryBlock>

      <MovementLabel>How it&rsquo;s shifting — year on year</MovementLabel>

      {([
        [roleMixShift, "How the role mix is shifting"],
        [seniorityShift, "How seniority is shifting"],
        [trackShift, "IC vs. management"],
      ] as const).map(([sec, heading]) => {
        const content = yoyContent(sec);
        return (
          <StoryBlock
            key={heading}
            heading={heading}
            {...blockProps(sec, !!content && content.rows.length > 0)}
          >
            {content ? <YearOnYearBars content={content} /> : null}
          </StoryBlock>
        );
      })}
    </article>
  );
}
