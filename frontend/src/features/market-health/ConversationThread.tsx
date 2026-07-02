import { useRef, useEffect, ReactNode } from "react";
import type { Message } from "ai";
import { UserTurn } from "./UserTurn";
import { AITurn } from "./AITurn";
import { OPENING_PROMPT } from "./MarketBriefingMessage";
import { ReasoningTrace } from "../../components/ReasoningPanel";

interface TraceEntry {
  trace: ReasoningTrace | null;
  generationTimeMs: number | null;
}

export interface ActiveDemoSim {
  userPrompt: string;
  phase: "thinking" | "done";
  trace: ReasoningTrace;
  generationTimeMs: number;
  content: ReactNode;
}

interface ConversationThreadProps {
  children: ReactNode;
  messages: Message[];
  isLoading: boolean;
  briefingTimeMs: number | null;
  briefingTrace: ReasoningTrace | null;
  briefingIsStreaming: boolean;
  traces: Map<string, TraceEntry>;
  activeDemoSim?: ActiveDemoSim | null;
}

export function ConversationThread({
  children,
  messages,
  isLoading,
  briefingTimeMs,
  briefingTrace,
  briefingIsStreaming,
  traces,
  activeDemoSim,
}: ConversationThreadProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isLoading, activeDemoSim?.phase]);

  const pairs: Array<{ user: Message; assistant: Message | null }> = [];
  for (let i = 0; i < messages.length; i++) {
    if (messages[i].role === "user") {
      const next = messages[i + 1];
      pairs.push({
        user: messages[i],
        assistant: next?.role === "assistant" ? next : null,
      });
      if (next?.role === "assistant") i++;
    }
  }

  let lastAssistantId: string | undefined;
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === "assistant") {
      lastAssistantId = messages[i].id;
      break;
    }
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-[1200px] mx-auto px-6 py-8 space-y-8">

        {/* Opening turn */}
        <UserTurn prompt={OPENING_PROMPT} isFirst={true} />
        <div id="turn-opening">
          <AITurn
            trace={briefingTrace}
            generationTimeMs={briefingTimeMs}
            isStreaming={briefingIsStreaming}
          >
            {children}
          </AITurn>
        </div>

        {/* Real follow-up turns from useChat */}
        {pairs.map(({ user, assistant }) => {
          const traceEntry = assistant ? traces.get(assistant.id) : undefined;
          const isStreamingThis =
            isLoading && assistant?.id === lastAssistantId;

          return (
            <div key={user.id} className="space-y-8">
              <UserTurn prompt={user.content} />
              {assistant ? (
                <div id={`turn-${assistant.id}`}>
                  <AITurn
                    trace={traceEntry?.trace ?? null}
                    generationTimeMs={traceEntry?.generationTimeMs ?? null}
                    isStreaming={isStreamingThis}
                  >
                    <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                      {assistant.content}
                    </p>
                  </AITurn>
                </div>
              ) : isLoading ? (
                <AITurn>
                  <div
                    className="flex items-center gap-1"
                    role="status"
                    aria-label="Loading response"
                  >
                    <span className="sr-only">Loading…</span>
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        className="inline-block w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce"
                        style={{ animationDelay: `${i * 150}ms` }}
                      />
                    ))}
                  </div>
                </AITurn>
              ) : null}
            </div>
          );
        })}

        {/* Demo simulation turn — driven by user submitting the chat input */}
        {activeDemoSim && (
          <div className="space-y-8">
            <UserTurn prompt={activeDemoSim.userPrompt} />
            {activeDemoSim.phase === "thinking" ? (
              <AITurn trace={null} generationTimeMs={null} isStreaming={true}>
                <div
                  className="flex items-center gap-1"
                  role="status"
                  aria-label="Loading response"
                >
                  <span className="sr-only">Loading…</span>
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="inline-block w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 150}ms` }}
                    />
                  ))}
                </div>
              </AITurn>
            ) : (
              <AITurn
                trace={activeDemoSim.trace}
                generationTimeMs={activeDemoSim.generationTimeMs}
              >
                {activeDemoSim.content}
              </AITurn>
            )}
          </div>
        )}

        <div ref={endRef} />
      </div>
    </div>
  );
}
