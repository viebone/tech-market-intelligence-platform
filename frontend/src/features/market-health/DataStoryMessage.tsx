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

function numberFrom(sectionValue: DataStorySection | undefined, key: string): number | null {
  const value = sectionValue?.content[key];
  return typeof value === "number" ? value : null;
}

function listFrom(sectionValue: DataStorySection | undefined, key: string): Array<Record<string, unknown>> {
  const value = sectionValue?.content[key];
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

export function DataStoryMessage({ story }: { story: DataStoryResult }) {
  const coverage = section(story, "coverage-window");
  const dataset = section(story, "dataset-size");
  const companies = section(story, "companies-and-sources");
  const roles = section(story, "roles-offered");
  const skills = section(story, "employer-mentioned-skills");
  const totalPostings = numberFrom(dataset, "unique_postings");
  const companyCount = numberFrom(companies, "unique_companies");
  const roleRows = listFrom(roles, "role_categories");
  const skillRows = listFrom(skills, "skills");
  const topRole = roleRows[0];
  const topSkill = skillRows[0];
  const firstCapturedAt = coverage?.content.first_captured_at;

  return (
    <article className="space-y-5" aria-label={story.question}>
      <div>
        <h2 className="text-lg font-semibold text-gray-100">What we know about the market</h2>
        <p className="mt-1 text-xs text-gray-500">
          Updated {new Date(story.as_of).toLocaleString()}
        </p>
      </div>

      <div className="space-y-4 text-sm leading-relaxed text-gray-300">
        <section>
          <h3 className="text-sm font-semibold text-gray-200">Market snapshot</h3>
          <p className="mt-2">
            {totalPostings === null
              ? "We are still building a picture of the market from the roles we track."
              : `We have a live view built from ${totalPostings.toLocaleString()} jobs collected so far.`}
            {companyCount !== null
              ? ` Those jobs come from ${companyCount.toLocaleString()} companies.`
              : " Company coverage is still taking shape."}
          </p>
        </section>

        <section className="border-t border-gray-800 pt-4">
          <h3 className="text-sm font-semibold text-gray-200">What stands out</h3>
          <ul className="mt-2 space-y-2">
            {topRole ? (
              <li>
                <span className="text-gray-100">{String(topRole.role_category)}</span> is the
                largest role group in the jobs we have collected so far.
              </li>
            ) : null}
            {topSkill ? (
              <li>
                The most commonly mentioned skill group is
                <span className="text-gray-100"> {String(topSkill.skill_group)}</span>.
              </li>
            ) : null}
            {topRole === undefined && topSkill === undefined ? (
              <li>We need more classified job information before meaningful patterns emerge.</li>
            ) : null}
          </ul>
        </section>

        <section className="border-t border-gray-800 pt-4">
          <h3 className="text-sm font-semibold text-gray-200">How to read this</h3>
          <p className="mt-2">
            {firstCapturedAt
              ? `This view covers jobs collected since ${new Date(String(firstCapturedAt)).toLocaleDateString()}. `
              : "This view is based on the data collected so far. "}
            It reflects the companies and roles we currently track, so it is a useful market
            signal rather than a complete picture of every tech job available.
          </p>
        </section>
      </div>

      <div className="border-t border-gray-800 pt-4">
        <p className="text-xs text-gray-500">
          Data updates as new job information becomes available.
        </p>
      </div>
    </article>
  );
}