import { DataFreshnessLabel } from "../../components/DataFreshnessLabel";

export type Verdict = "Healthy" | "Cautious" | "Contracting";

export interface MarketHealthSignalData {
  verdict: Verdict;
  explanation: string;
  trendDirection: "improving" | "stable" | "worsening";
  asOf: string;
  source: string;
}

interface MarketHealthSignalProps {
  signal: MarketHealthSignalData | null;
}

const verdictConfig: Record<
  Verdict,
  { label: string; colorClass: string; bgClass: string; borderClass: string }
> = {
  Healthy: {
    label: "Healthy",
    colorClass: "text-emerald-700",
    bgClass: "bg-emerald-50",
    borderClass: "border-emerald-200",
  },
  Cautious: {
    label: "Cautious",
    colorClass: "text-amber-700",
    bgClass: "bg-amber-50",
    borderClass: "border-amber-200",
  },
  Contracting: {
    label: "Contracting",
    colorClass: "text-red-700",
    bgClass: "bg-red-50",
    borderClass: "border-red-200",
  },
};

export function MarketHealthSignal({ signal }: MarketHealthSignalProps) {
  if (signal === null) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 px-6 py-5">
        <p className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-1">
          Market Health
        </p>
        <p className="text-2xl font-semibold text-gray-400">Insufficient data</p>
        <p className="mt-1 text-sm text-gray-400">
          There is not enough data to determine a market verdict for this combination of filters.
        </p>
      </div>
    );
  }

  const config = verdictConfig[signal.verdict];

  return (
    <div
      className={`rounded-lg border ${config.borderClass} ${config.bgClass} px-6 py-5`}
    >
      <p className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-1">
        Market Health
      </p>
      <p className={`text-4xl font-bold tracking-tight ${config.colorClass}`}>
        {config.label}
      </p>
      <p className="mt-2 text-base text-gray-700 leading-relaxed max-w-prose">
        {signal.explanation}
      </p>
      <div className="mt-3">
        <DataFreshnessLabel asOf={signal.asOf} source={signal.source} />
      </div>
    </div>
  );
}
