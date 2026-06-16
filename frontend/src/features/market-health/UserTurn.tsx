import { useState, ReactNode } from "react";

interface UserTurnProps {
  prompt: string;
  preview?: ReactNode;
}

export function UserTurn({ prompt, preview }: UserTurnProps) {
  const [expanded, setExpanded] = useState(false);
  const TRUNCATE_AT = 120;
  const isTruncatable = prompt.length > TRUNCATE_AT;
  const displayText = !expanded && isTruncatable
    ? prompt.slice(0, TRUNCATE_AT).trimEnd() + "…"
    : prompt;

  return (
    <div className="flex items-start gap-3 justify-end">
      <div className="flex flex-col items-end gap-1 max-w-[80%]">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-gray-500">You</span>
        </div>

        <div className="rounded-2xl rounded-tr-sm bg-gray-800 px-4 py-3 text-sm text-gray-100 leading-relaxed">
          <p>{displayText}</p>
          {preview && !expanded && (
            <div className="mt-2 opacity-60">{preview}</div>
          )}
        </div>

        {isTruncatable && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors focus:outline-none"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              className={`w-3.5 h-3.5 transition-transform ${expanded ? "rotate-180" : ""}`}
            >
              <path
                fillRule="evenodd"
                d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z"
                clipRule="evenodd"
              />
            </svg>
            {expanded ? "Show less" : "Show full prompt"}
          </button>
        )}
      </div>

      <div className="shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold text-gray-600 mt-0.5">
        Y
      </div>
    </div>
  );
}
