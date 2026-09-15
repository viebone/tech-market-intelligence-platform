/**
 * Plain-language scope labels for the Connected Assistant card's chips.
 * Deliberately duplicated from backend/src/mcp_access/oauth.py's
 * SCOPE_DESCRIPTIONS, not imported — one is Python rendered server-side
 * (the consent screen), this one is bundled into the SPA. See
 * frontend/specs/mcp-access/architecture.md — Data Requirements: this pair
 * only changes together, and a raw scope identifier (e.g. "jobs.read")
 * must never be shown to a user directly (design/visual-design.md's
 * "Plain language over raw identifiers" rule).
 */
export const SCOPE_LABELS: Record<string, string> = {
  "jobs.read": "Can read job demand and skill trends",
  "companies.read": "Can read company employment risk (layoffs, expansion)",
  "compensation.read": "Can read salary data",
};

export function scopeLabel(scope: string): string {
  return SCOPE_LABELS[scope] ?? scope;
}
