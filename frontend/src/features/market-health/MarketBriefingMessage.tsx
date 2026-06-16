import { MarketHealthSignal, MarketHealthSignalData } from "./MarketHealthSignal";
import { SearchImplication, SearchImplicationData } from "./SearchImplication";
import { FilterControls, Filters } from "./FilterControls";
import { TrendGrid, TrendsData } from "./TrendGrid";

export const OPENING_PROMPT =
  "Give me the current market health signal and search implication, followed by demand signals, compensation signals, and layoff signals — with filter controls so I can narrow by role, seniority, and location. I want to assess the current state of the tech job market.";

interface MarketBriefingMessageProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
  signal: MarketHealthSignalData | null;
  implication: SearchImplicationData | null;
  signalLoading: boolean;
  signalFetching: boolean;
  signalError: Error | null;
  onRetrySignal: () => void;
  trends: TrendsData | undefined;
  trendsLoading: boolean;
  trendsFetching: boolean;
  trendsError: Error | null;
  onRetryTrends: () => void;
}

export function MarketBriefingMessage({
  filters,
  onFiltersChange,
  signal,
  implication,
  signalLoading,
  signalFetching,
  signalError,
  onRetrySignal,
  trends,
  trendsLoading,
  trendsFetching,
  trendsError,
  onRetryTrends,
}: MarketBriefingMessageProps) {
  return (
    <div className="flex flex-col gap-5">
      {signalError ? (
        <div className="rounded-lg border border-red-100 bg-red-50 px-6 py-5">
          <p className="text-sm font-medium text-red-700 mb-1">Could not load market signal</p>
          <p className="text-sm text-red-600 mb-3">{signalError.message}</p>
          <button
            onClick={onRetrySignal}
            className="text-sm text-red-700 underline hover:no-underline focus:outline-none"
          >
            Retry
          </button>
        </div>
      ) : signalLoading ? (
        <div className="rounded-lg border border-gray-100 bg-white px-6 py-5 animate-pulse" role="status">
          <span className="sr-only">Loading…</span>
          <div className="h-3 bg-gray-100 rounded w-24 mb-4" />
          <div className="h-10 bg-gray-100 rounded w-48 mb-3" />
          <div className="h-4 bg-gray-50 rounded w-full max-w-sm" />
        </div>
      ) : (
        <div className="relative">
          {signalFetching && (
            <div className="absolute top-3 right-4 z-10" role="status" aria-label="Refreshing">
              <svg className="animate-spin h-4 w-4 text-gray-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
            </div>
          )}
          <MarketHealthSignal signal={signal} />
        </div>
      )}

      {!signalError && implication && (
        <SearchImplication implication={implication} />
      )}

      <FilterControls filters={filters} onChange={onFiltersChange} />

      {trendsError ? (
        <div className="rounded-lg border border-red-100 bg-red-50 px-4 py-4">
          <p className="text-sm font-medium text-red-700 mb-1">Could not load trend data</p>
          <p className="text-sm text-red-600 mb-3">{trendsError.message}</p>
          <button
            onClick={onRetryTrends}
            className="text-sm text-red-700 underline hover:no-underline focus:outline-none"
          >
            Retry
          </button>
        </div>
      ) : (
        <TrendGrid
          trends={trends}
          isLoading={trendsLoading || trendsFetching}
        />
      )}

    </div>
  );
}
