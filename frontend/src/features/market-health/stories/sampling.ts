// Sampling contract types (added 2026-10-23 — changes/2026-10-10-requirements-extraction-sampling.md;
// frontend/specs/market-health/architecture.md — Sampling and the method text). Every sentence
// about how data was gathered or how close an estimate is comes from the API (rendered once, by
// the backend's method_text.py) — this frontend never writes that wording itself.

export type EstimateConfidence = "full" | "estimate" | "small_sample" | "too_few" | "full_small";

export interface Estimate {
  is_estimate: boolean;
  sample_n: number;
  population_n: number;
  unread_n: number;
  margin_pts: number | null;
  confidence: EstimateConfidence;
  qualifier: string;
}

export interface MethodText {
  one_line: string;
  full: { heading: string; text: string }[];
  company_count: number | null;
  limit_per_group: number | null;
}

/** The one client-side sentence: the "± pts" how-to-read line, verbatim from
 * design/market-health/experience.md — Requirements estimates — Wording, per surface. */
export function howToReadLine(populationN: number): string {
  return `± pts: the real figure across all ${populationN.toLocaleString()} postings is very likely within this many points of the figure shown.`;
}

export function isEstimate(value: unknown): value is Estimate {
  return (
    typeof value === "object" && value !== null &&
    typeof (value as Estimate).qualifier === "string" &&
    typeof (value as Estimate).confidence === "string"
  );
}
