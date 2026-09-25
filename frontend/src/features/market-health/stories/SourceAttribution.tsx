// A story's visible attribution for an outside publisher's statistics — added 2026-09-25
// (changes/2026-09-24-uk-lmi-and-ons-vacancy-sources.md; frontend/specs/market-health/
// architecture.md — Story 5). Generic on purpose: it reads the `attribution` object the API sends
// with every figure and NEVER hard-codes a publisher or a licence string, so any future trusted
// source's story reuses it unchanged.
//
// Why it exists (design/market-health/data-stories.md — Visual standard, outside-publisher
// stories): the publisher's licence makes credit a CONDITION of showing the data, so the name and
// the exact attribution text render on the page itself beside the framing line — never only in
// the Reasoning Panel. A provisional figure is flagged in words. If the licence is not yet
// confirmed the caveat renders here too (data-legibility — Provenance): unused for the ONS
// (confirmed, OGL v3.0), but required for the first surface of any unconfirmed publisher.

export interface SourceAttributionData {
  publisher: string;
  programme: string;
  text: string;
  source_url: string;
  licence: string;
  licence_confirmed: boolean;
  period_label: string;
  value_status: string;
  released_on: string;
}

export function isSourceAttribution(value: unknown): value is SourceAttributionData {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return typeof v.publisher === "string" && typeof v.text === "string" && v.text.trim() !== "";
}

export function SourceAttribution({ attribution }: { attribution: SourceAttributionData }) {
  return (
    <div className="space-y-0.5 text-xs text-gray-500">
      <p>{attribution.text}</p>
      {attribution.value_status === "provisional" ? (
        <p>The latest figures are a first estimate and may be revised.</p>
      ) : null}
      {attribution.licence_confirmed ? null : (
        <p className="text-gray-400">The usage terms for this data are not yet confirmed.</p>
      )}
      {attribution.source_url ? (
        <p>
          <a
            href={attribution.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-400 underline decoration-gray-700 underline-offset-2 hover:text-gray-300"
          >
            View the source dataset
          </a>
        </p>
      ) : null}
    </div>
  );
}
