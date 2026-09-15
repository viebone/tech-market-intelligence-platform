/**
 * Rendered by ConnectionsList when the list is empty — actively explains
 * the value of connecting rather than a bare "No connections" with nothing
 * else, per design/mcp-access/experience.md Part 1's edge case.
 */
export function EmptyState() {
  return (
    <div className="rounded-lg border border-gray-700 bg-gray-800/60 p-3 text-sm text-gray-300">
      Ask Claude, ChatGPT, or another AI assistant about the job market — using this
      platform's data, with your own AI subscription. Copy the endpoint above and add it
      as a connector in your AI client of choice.
    </div>
  );
}
