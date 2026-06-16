import { useState } from "react";
import { Filters } from "./FilterControls";
import { MarketHealthSignalData } from "./MarketHealthSignal";

export interface ProvenanceData {
  source: "briefing" | "chat";
  filters: Filters;
  signal: MarketHealthSignalData | null;
  demandCount: number;
  compCount: number;
  layoffCount: number;
}

const TREND_ICON: Record<string, { symbol: string; color: string }> = {
  improving: { symbol: "↗", color: "text-emerald-600" },
  stable:    { symbol: "→", color: "text-amber-600" },
  worsening: { symbol: "↘", color: "text-red-600" },
  declining: { symbol: "↘", color: "text-red-600" },
};

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
      {children}
    </span>
  );
}

function Row({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <div className="flex items-start justify-between gap-4 py-1.5 border-b border-gray-100 last:border-0">
      <span className="text-gray-400 shrink-0">{label}</span>
      <span className="text-gray-700 text-right">
        {value}
        {sub && <span className="block text-gray-400 text-[10px] mt-0.5">{sub}</span>}
      </span>
    </div>
  );
}

interface ProvenancePanelProps {
  data: ProvenanceData;
}

export function ProvenancePanel({ data }: ProvenancePanelProps) {
  const [open, setOpen] = useState(false);

  const { filters, signal, demandCount, compCount, layoffCount, source } = data;

  const trendIcon = signal
    ? (TREND_ICON[signal.trendDirection] ?? TREND_ICON.stable)
    : null;

  const filterLabel = [
    filters.role === "all" ? "All roles" : filters.role,
    filters.seniority === "all" ? "All seniority" : filters.seniority,
    filters.location === "all" ? "All locations" : filters.location,
    `Last ${filters.period}`,
  ];

  return (
    <div className="mb-4">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 transition-colors focus:outline-none"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className={`w-3.5 h-3.5 transition-transform ${open ? "rotate-180" : ""}`}
        >
          <path
            fillRule="evenodd"
            d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z"
            clipRule="evenodd"
          />
        </svg>
        How this was generated
      </button>

      {open && (
        <div className="mt-2 rounded-lg border border-gray-100 bg-gray-50 px-4 py-3 text-xs space-y-4">

          {/* Filters */}
          <section>
            <p className="font-semibold text-gray-500 mb-2 uppercase tracking-wide text-[10px]">
              Filters applied
            </p>
            <div className="flex flex-wrap gap-1.5">
              {filterLabel.map((f) => (
                <Tag key={f}>{f}</Tag>
              ))}
            </div>
          </section>

          {/* Data loaded (briefing) or context sent (chat) */}
          <section>
            <p className="font-semibold text-gray-500 mb-1 uppercase tracking-wide text-[10px]">
              {source === "briefing" ? "Data loaded" : "Context sent to Claude"}
            </p>
            <div>
              <Row
                label="Market signal"
                value={
                  signal ? (
                    <span className="flex items-center gap-1 justify-end">
                      <span>{signal.verdict}</span>
                      {trendIcon && (
                        <span className={trendIcon.color}>{trendIcon.symbol}</span>
                      )}
                    </span>
                  ) : (
                    <span className="text-gray-400">No data for these filters</span>
                  )
                }
                sub={signal ? `as of ${signal.asOf}` : undefined}
              />
              <Row
                label="Demand signals"
                value={`${demandCount} matched`}
              />
              <Row
                label="Compensation signals"
                value={`${compCount} matched`}
              />
              <Row
                label="Layoff events"
                value={`${layoffCount} total`}
              />
              {source === "chat" && (
                <Row label="Model" value="Claude Haiku" />
              )}
            </div>
          </section>

          {/* Sources (briefing only) */}
          {source === "briefing" && signal && (
            <section>
              <p className="font-semibold text-gray-500 mb-1 uppercase tracking-wide text-[10px]">
                Sources
              </p>
              <p className="text-gray-500 leading-relaxed">{signal.source}</p>
            </section>
          )}

          {/* Endpoints (briefing only) */}
          {source === "briefing" && (
            <section>
              <p className="font-semibold text-gray-500 mb-1 uppercase tracking-wide text-[10px]">
                API calls
              </p>
              <div className="space-y-1 font-mono text-gray-400">
                <p>GET /api/market-health/summary</p>
                <p>GET /api/market-health/trends</p>
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
