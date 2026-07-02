import { JobOpeningsChart, OpeningDataPoint, TimeRange } from "./JobOpeningsChart";

export const OPENING_PROMPT =
  "Show me the current trend in tech job openings by role category — Designer, Product Manager, " +
  "and Engineer — month over month. Display total openings per month for each category as a line chart " +
  "with time range options for This Year, Past 5 Years, and All Time. Then give me a brief written " +
  "summary of what the data shows: the overall direction, the magnitude of change, and any notable " +
  "differences between the three role categories.";

interface MarketBriefingMessageProps {
  range: TimeRange;
  onRangeChange: (r: TimeRange) => void;
  data: OpeningDataPoint[] | undefined;
  summary: string | undefined;
  isLoading: boolean;
  isFetching: boolean;
  error: Error | null;
  onRetry: () => void;
}

export function MarketBriefingMessage({
  range,
  onRangeChange,
  data,
  summary,
  isLoading,
  isFetching,
  error,
  onRetry,
}: MarketBriefingMessageProps) {
  if (error) {
    return (
      <div className="rounded-lg border border-red-900/40 bg-red-950/30 px-6 py-5">
        <p className="text-sm font-medium text-red-400 mb-1">Could not load market data</p>
        <p className="text-sm text-red-500/80 mb-3">{error.message}</p>
        <button
          onClick={onRetry}
          className="text-sm text-red-400 underline hover:no-underline focus:outline-none"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Chart */}
      <JobOpeningsChart
        data={data ?? []}
        range={range}
        onRangeChange={onRangeChange}
        isLoading={isLoading || isFetching}
      />

      {/* Written summary */}
      {isLoading ? (
        <div className="space-y-2 animate-pulse" role="status" aria-label="Loading summary">
          <div className="h-3.5 bg-gray-700 rounded w-full" />
          <div className="h-3.5 bg-gray-700 rounded w-11/12" />
          <div className="h-3.5 bg-gray-700 rounded w-4/5" />
          <div className="h-3.5 bg-gray-700 rounded w-3/4" />
        </div>
      ) : summary ? (
        <p className="text-sm text-gray-300 leading-relaxed">{summary}</p>
      ) : null}
    </div>
  );
}
