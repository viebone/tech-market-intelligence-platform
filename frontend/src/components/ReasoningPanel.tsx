import { useState } from "react";

export interface SourceAccess {
  sequence: number;
  source_type: "data_source" | "tool";
  name: string;
  purpose: string;
}

export interface ReasoningStep {
  sequence: number;
  content: string;
}

export interface ReasoningTrace {
  input_context: string;
  sources_and_tools: SourceAccess[];
  reasoning_steps: ReasoningStep[];
  is_complete: boolean;
}

interface ReasoningPanelProps {
  trace: ReasoningTrace | null;
  generationTimeMs: number | null;
  isStreaming?: boolean;
}

function Skeleton() {
  return (
    <div className="space-y-1">
      <div className="animate-pulse bg-gray-700 rounded h-3 w-3/4" />
      <div className="animate-pulse bg-gray-700 rounded h-3 w-1/2" />
    </div>
  );
}

export function ReasoningPanel({
  trace,
  generationTimeMs,
  isStreaming,
}: ReasoningPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  const timeLabel =
    generationTimeMs !== null && generationTimeMs !== undefined
      ? `${(generationTimeMs / 1000).toFixed(1)}s`
      : null;

  return (
    <div className="mt-1">
      <button
        onClick={() => setIsOpen((v) => !v)}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 cursor-pointer bg-transparent border-none p-0 mt-1"
      >
        <span>{isOpen ? "↑" : "↓"}</span>
        <span>{isOpen ? "Hide thinking" : "View thinking"}</span>
        {timeLabel && (
          <>
            <span className="text-gray-600"> · </span>
            <span className="text-gray-600">{timeLabel}</span>
          </>
        )}
      </button>

      <div
        className={`overflow-hidden transition-all duration-200 ease-in-out ${
          isOpen ? "max-h-[2000px]" : "max-h-0"
        }`}
      >
        <div className="bg-gray-800 border-y border-gray-700 py-4 px-4 my-2 space-y-4">
          {isStreaming && !trace ? (
            <>
              {(["Input", "Sources & Tools", "Reasoning"] as const).map(
                (label) => (
                  <section key={label}>
                    <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
                      {label}
                    </p>
                    <Skeleton />
                  </section>
                )
              )}
            </>
          ) : !trace ? (
            <p className="text-xs italic text-gray-600">
              Reasoning trace unavailable for this response.
            </p>
          ) : (
            <>
              <section>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
                  Input
                </p>
                <p className="text-sm text-gray-300 leading-relaxed">
                  {trace.input_context}
                </p>
              </section>

              <section>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
                  Sources & Tools
                </p>
                {trace.sources_and_tools.length === 0 ? (
                  <p className="text-xs italic text-gray-600">
                    No external data sources or tools were used for this
                    response.
                  </p>
                ) : (
                  <ol className="space-y-2">
                    {[...trace.sources_and_tools]
                      .sort((a, b) => a.sequence - b.sequence)
                      .map((s) => (
                        <li key={s.sequence} className="text-sm">
                          <span className="text-gray-300">{s.name}</span>
                          <span className="text-gray-500 ml-1">
                            — {s.purpose}
                          </span>
                        </li>
                      ))}
                  </ol>
                )}
              </section>

              <section>
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">
                  Reasoning
                </p>
                {trace.reasoning_steps.length === 0 ? (
                  <p className="text-xs italic text-gray-600">
                    Reasoning steps unavailable for this response.
                  </p>
                ) : (
                  <ol className="space-y-2 list-decimal list-inside">
                    {[...trace.reasoning_steps]
                      .sort((a, b) => a.sequence - b.sequence)
                      .map((s) => (
                        <li
                          key={s.sequence}
                          className="text-sm text-gray-300 leading-relaxed"
                        >
                          {s.content}
                        </li>
                      ))}
                  </ol>
                )}
              </section>

              {!trace.is_complete && (
                <p className="text-xs italic text-gray-500">
                  Reasoning trace is incomplete.
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
