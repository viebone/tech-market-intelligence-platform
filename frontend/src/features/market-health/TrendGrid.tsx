import { TrendChart, TrendDataPoint, TrendDirection } from "./TrendChart";
import { DataFreshnessLabel } from "../../components/DataFreshnessLabel";

export interface TrendSeries {
  id: string;
  title: string;
  data: TrendDataPoint[];
  direction: TrendDirection;
  asOf: string;
  source: string;
}

export interface LayoffEvent {
  id: string;
  company: string;
  sector: string;
  date: string;
  affectedCount?: number;
  notes?: string;
}

export interface TrendsData {
  demand: TrendSeries[];
  compensation: TrendSeries[];
  layoffs: LayoffEvent[];
  layoffsAsOf: string;
  layoffsSource: string;
}

interface TrendGridProps {
  trends: TrendsData | undefined;
  isLoading: boolean;
}

function SectionSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" aria-hidden="true">
      {[1, 2].map((i) => (
        <div
          key={i}
          className="rounded-lg border border-gray-100 bg-white p-4 h-40 animate-pulse"
        >
          <div className="h-3 bg-gray-100 rounded w-2/3 mb-3" />
          <div className="h-16 bg-gray-50 rounded" />
        </div>
      ))}
    </div>
  );
}

function EmptySection({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-gray-100 bg-gray-50 px-4 py-6 text-center">
      <p className="text-sm text-gray-400">{message}</p>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
      {children}
    </h2>
  );
}

function LayoffList({
  events,
  asOf,
  source,
  isLoading,
}: {
  events: LayoffEvent[];
  asOf: string;
  source: string;
  isLoading: boolean;
}) {
  if (isLoading) {
    return (
      <div className="space-y-2 animate-pulse" aria-hidden="true">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-12 bg-gray-50 rounded border border-gray-100" />
        ))}
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <EmptySection message="No layoff events recorded for this combination." />
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <ul className="divide-y divide-gray-100 rounded-lg border border-gray-100 bg-white overflow-hidden">
        {events.map((event) => (
          <li key={event.id} className="px-4 py-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {event.company}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {event.sector}
                  {event.affectedCount != null && (
                    <>
                      {" · "}
                      <span className="text-gray-500">
                        ~{event.affectedCount.toLocaleString()} affected
                      </span>
                    </>
                  )}
                </p>
                {event.notes && (
                  <p className="text-xs text-gray-400 mt-0.5 italic">{event.notes}</p>
                )}
              </div>
              <time
                dateTime={event.date}
                className="text-xs text-gray-300 tabular-nums shrink-0 pt-0.5"
              >
                {event.date}
              </time>
            </div>
          </li>
        ))}
      </ul>
      <DataFreshnessLabel asOf={asOf} source={source} />
    </div>
  );
}

export function TrendGrid({ trends, isLoading }: TrendGridProps) {
  return (
    <div className="space-y-8">
      {/* Demand Signals */}
      <section aria-labelledby="demand-heading">
        <SectionLabel>
          <span id="demand-heading">Demand Signals — Posting Volume</span>
        </SectionLabel>
        {isLoading && !trends ? (
          <SectionSkeleton />
        ) : trends && trends.demand.length > 0 ? (
          <div className="relative">
            {isLoading && (
              <div
                className="absolute inset-0 bg-white/60 z-10 rounded-lg flex items-center justify-center"
                aria-label="Refreshing demand data"
                role="status"
              >
                <span className="sr-only">Updating data…</span>
                <svg
                  className="animate-spin h-5 w-5 text-gray-400"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v8H4z"
                  />
                </svg>
              </div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {trends.demand.map((series) => (
                <TrendChart
                  key={series.id}
                  title={series.title}
                  data={series.data}
                  direction={series.direction}
                  asOf={series.asOf}
                  source={series.source}
                />
              ))}
            </div>
          </div>
        ) : (
          <EmptySection message="No demand data available for this combination." />
        )}
      </section>

      {/* Compensation Signals */}
      <section aria-labelledby="compensation-heading">
        <SectionLabel>
          <span id="compensation-heading">Compensation Signals — Salary Bands</span>
        </SectionLabel>
        {isLoading && !trends ? (
          <SectionSkeleton />
        ) : trends && trends.compensation.length > 0 ? (
          <div className="relative">
            {isLoading && (
              <div
                className="absolute inset-0 bg-white/60 z-10 rounded-lg flex items-center justify-center"
                aria-label="Refreshing compensation data"
                role="status"
              >
                <span className="sr-only">Updating data…</span>
                <svg
                  className="animate-spin h-5 w-5 text-gray-400"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8v8H4z"
                  />
                </svg>
              </div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {trends.compensation.map((series) => (
                <TrendChart
                  key={series.id}
                  title={series.title}
                  data={series.data}
                  direction={series.direction}
                  asOf={series.asOf}
                  source={series.source}
                />
              ))}
            </div>
          </div>
        ) : (
          <EmptySection message="Compensation data is not available for this combination." />
        )}
      </section>

      {/* Layoff Signals */}
      <section aria-labelledby="layoff-heading">
        <SectionLabel>
          <span id="layoff-heading">Layoff Signals</span>
        </SectionLabel>
        <LayoffList
          events={trends?.layoffs ?? []}
          asOf={trends?.layoffsAsOf ?? ""}
          source={trends?.layoffsSource ?? ""}
          isLoading={isLoading && !trends}
        />
      </section>
    </div>
  );
}
