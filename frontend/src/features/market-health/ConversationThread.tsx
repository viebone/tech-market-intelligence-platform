import { useRef, useEffect, ReactNode } from "react";
import type { Message } from "ai";
import { UserTurn } from "./UserTurn";
import { AITurn } from "./AITurn";
import { OPENING_PROMPT } from "./MarketBriefingMessage";
import { ProvenanceData } from "./ProvenancePanel";

interface ConversationThreadProps {
  children: ReactNode;
  messages: Message[];
  isLoading: boolean;
  briefingProvenance: ProvenanceData;
  briefingTimeMs: number | null;
  chatProvenances: Map<string, ProvenanceData & { timeMs: number }>;
}

export function ConversationThread({
  children,
  messages,
  isLoading,
  briefingProvenance,
  briefingTimeMs,
  chatProvenances,
}: ConversationThreadProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isLoading]);

  // Group into [user, assistant] pairs
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

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">

        {/* Opening turn */}
        <UserTurn prompt={OPENING_PROMPT} />
        <AITurn
          provenance={briefingProvenance}
          timeMs={briefingTimeMs ?? undefined}
        >
          {children}
        </AITurn>

        {/* Follow-up turns */}
        {pairs.map(({ user, assistant }) => {
          const provenance = assistant ? chatProvenances.get(assistant.id) : undefined;
          return (
            <div key={user.id} className="space-y-8">
              <UserTurn prompt={user.content} />
              {assistant ? (
                <AITurn
                  provenance={provenance}
                  timeMs={provenance?.timeMs}
                >
                  <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {assistant.content}
                  </p>
                </AITurn>
              ) : isLoading ? (
                <AITurn>
                  <div className="flex items-center gap-1" role="status" aria-label="Loading response">
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

        <div ref={endRef} />
      </div>
    </div>
  );
}
