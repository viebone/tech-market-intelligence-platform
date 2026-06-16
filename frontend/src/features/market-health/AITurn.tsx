import { ReactNode } from "react";
import { ProvenancePanel, ProvenanceData } from "./ProvenancePanel";

interface AITurnProps {
  children: ReactNode;
  provenance?: ProvenanceData;
  timeMs?: number;
}

function formatTime(ms: number): string {
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`;
}

export function AITurn({ children, provenance, timeMs }: AITurnProps) {
  return (
    <div className="flex items-start gap-3">
      <div className="shrink-0 w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center mt-0.5">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="white"
          className="w-4 h-4"
          aria-hidden="true"
        >
          <path d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2Zm0 18a8 8 0 1 1 0-16 8 8 0 0 1 0 16Zm-1-5h2v2h-2v-2Zm0-8h2v6h-2V7Z" />
        </svg>
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-semibold text-gray-500">Assistant</span>
          {timeMs !== undefined && (
            <span className="text-xs text-gray-300">· {formatTime(timeMs)}</span>
          )}
        </div>

        {provenance && <ProvenancePanel data={provenance} />}

        <div>{children}</div>
      </div>
    </div>
  );
}
