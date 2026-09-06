import type { ReactNode } from "react";

import { RankedBarList, type RankedBarRow } from "./RankedBarList";

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

/** A block heading + its honesty qualifier, wrapping either a chart or its "not enough data" line. */
function Block({
  heading,
  section: sec,
  hasData,
  children,
}: {
  heading: string;
  section: DataStorySection | undefined;
  hasData: boolean;
  children: ReactNode;
}) {
  const insufficient = sec?.status === "insufficient_data" || !hasData;
  return (
    <section className="border-t border-gray-800 pt-4">
      <h3 className="text-sm font-semibold text-gray-200">{heading}</h3>
      <div className="mt-3">
        {insufficient ? (
          <p className="text-sm text-gray-400">
            {sec?.message ?? "Not enough data yet."}
          </p>
        ) : (
          children
        )}
      </div>
      {sec?.qualifier ? (
        <p className="mt-2 text-xs text-gray-500">{sec.qualifier}</p>
      ) : null}
    </section>
  );
}

export function DataStoryMessage({ story }: { story: DataStoryResult }) {
  const roles = section(story, "roles-offered");
  const skills = section(story, "employer-mentioned-skills");
  const pay = section(story, "compensation-coverage");
  const geo = section(story, "geographic-coverage");

  // 2. The roles being hired — specialization is the meaningful "role", not the fragmented raw title.
  const roleRows: RankedBarRow[] = listFrom(roles, "top_specializations")
    .map((row) => ({ label: str(row.specialization), value: num(row.posting_count) }))
    .filter((row) => !HIDDEN_ROLE_LABELS.has(row.label.toLowerCase()))
    .slice(0, 7);

  // 3. What employers ask for — one row per skill group, must-have mentions emphasised.
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

  // 4. Pay transparency — share of postings that state a salary (structured + parsed).
  const payRows = listFrom(pay, "coverage_by_confidence");
  const disclosed = payRows
    .filter((row) => str(row.confidence) === "structured" || str(row.confidence) === "parsed")
    .reduce((sum, row) => sum + num(row.posting_count), 0);
  const payTotal = payRows.reduce((sum, row) => sum + num(row.posting_count), 0);
  const disclosedPct = payTotal > 0 ? (disclosed / payTotal) * 100 : 0;
  const pctLabel = disclosedPct > 0 && disclosedPct < 1 ? "<1%" : `${Math.round(disclosedPct)}%`;

  // 5. Where the roles are — top cities among the minority that carry a normalised location.
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

      {/* 1. Framing line — no inventory figures; the welcome already carries those. */}
      <p className="text-sm leading-relaxed text-gray-300">
        Past the headcount, this is what the tech postings the platform tracks are actually
        asking for — the roles on offer, the skills employers name, how often pay is disclosed,
        and where the work sits.
      </p>

      <Block heading="The roles being hired" section={roles} hasData={roleRows.length > 0}>
        <RankedBarList rows={roleRows} />
      </Block>

      <Block heading="What employers ask for" section={skills} hasData={skillRows.length > 0}>
        <RankedBarList rows={skillRows} limit={8} />
        <p className="mt-2 text-xs text-gray-500">Solid bars are must-have mentions.</p>
      </Block>

      <Block heading="Pay transparency" section={pay} hasData={payTotal > 0}>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-gray-100">{pctLabel}</span>
          <span className="text-sm text-gray-400">of postings state a salary range</span>
        </div>
        <span className="mt-3 block h-2 w-full overflow-hidden rounded-full bg-gray-800">
          <span
            className="block h-full rounded-full bg-indigo-500"
            style={{ width: `${Math.max(disclosedPct, 1)}%` }}
          />
        </span>
        <p className="mt-2 text-sm text-gray-400">
          The other {payTotal > 0 ? `${Math.round(100 - disclosedPct)}%` : "majority"} don't
          disclose compensation.
        </p>
      </Block>

      <Block heading="Where the roles are" section={geo} hasData={cityRows.length > 0}>
        <RankedBarList rows={cityRows} />
      </Block>
    </article>
  );
}
