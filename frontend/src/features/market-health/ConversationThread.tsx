import { useRef, useEffect, ReactNode } from "react";
import type { Message } from "ai";
import { UserTurn } from "./UserTurn";
import { AITurn } from "./AITurn";
import { OPENING_PROMPT } from "./MarketBriefingMessage";
import { ReasoningTrace } from "../../components/ReasoningPanel";
import { DataStoryMessage, DataStoryResult } from "./DataStoryMessage";
import { WelcomeMessage, WelcomeResult } from "./WelcomeMessage";
import { SuggestedQuestions } from "./SuggestedQuestions";
import { WELCOME_TASK_ID, HIRING_STATUS_TASK_ID } from "./TaskPanel";

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
  activeTaskId: string;
  messages: Message[];
  isLoading: boolean;
  briefingTimeMs: number | null;
  briefingTrace: ReasoningTrace | null;
  briefingIsStreaming: boolean;
  traces: Map<string, TraceEntry>;
  activeDemoSim?: ActiveDemoSim | null;
  selectedStoryId: string | null;
  storyResult: DataStoryResult | null;
  storyLoading: boolean;
  storyError: Error | null;
  storyTrace: ReasoningTrace | null;
  welcomeResult: WelcomeResult | null;
  welcomeLoading: boolean;
  welcomeError: Error | null;
  welcomeTrace: ReasoningTrace | null;
  onSelectShortcut: (storyId: string) => void;
  onAskSuggestion: (question: string) => void;
}

export function ConversationThread({
  children,
  activeTaskId,
  messages,
  isLoading,
  briefingTimeMs,
  briefingTrace,
  briefingIsStreaming,
  traces,
  activeDemoSim,
  selectedStoryId,
  storyResult,
  storyLoading,
  storyError,
  storyTrace,
  welcomeResult,
  welcomeLoading,
  welcomeError,
  welcomeTrace,
  onSelectShortcut,
  onAskSuggestion,
}: ConversationThreadProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // block: "nearest" — the default ("start") asks every scrollable ancestor,
    // including the document itself if it's even marginally scrollable, to
    // align endRef with the top of *its* viewport. That's what was scrolling
    // the whole page (not just this container) — see
    // changes/2026-08-17-chat-scroll-white-gap.md. "nearest" only scrolls the
    // minimum needed to bring the target into view, within whichever
    // container actually needs it.
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
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

        {activeTaskId === WELCOME_TASK_ID ? (
          <div id="turn-about-this-platform">
            {welcomeLoading ? (
              <AITurn trace={null} generationTimeMs={null} isStreaming={true}>
                <div className="flex items-center gap-1" role="status" aria-label="Loading response">
                  <span className="sr-only">Loading welcome</span>
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-gray-300"
                      style={{ animationDelay: `${i * 150}ms` }}
                    />
                  ))}
                </div>
              </AITurn>
            ) : welcomeError ? (
              <AITurn trace={null} generationTimeMs={null}>
                <p className="text-sm text-gray-400">
                  The welcome is temporarily unavailable. Please try again shortly.
                </p>
              </AITurn>
            ) : welcomeResult ? (
              <AITurn trace={welcomeTrace} generationTimeMs={0}>
                <WelcomeMessage welcome={welcomeResult} onSelectShortcut={onSelectShortcut} />
              </AITurn>
            ) : null}
          </div>
        ) : activeTaskId === HIRING_STATUS_TASK_ID ? (
          <>
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

            {/* Curated instant-answer chips — the fast path, one tap. Added
                2026-09-06, changes/2026-09-03-chat-resilience-and-instant-answers.md. */}
            <SuggestedQuestions onAsk={onAskSuggestion} disabled={isLoading} />

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
          </>
        ) : selectedStoryId ? (
          <div id={`turn-${selectedStoryId}`}>
            {storyLoading ? (
              <AITurn trace={null} generationTimeMs={null} isStreaming={true}>
                <div className="flex items-center gap-1" role="status" aria-label="Loading response">
                  <span className="sr-only">Loading story</span>
                  {[0, 1, 2].map((i) => (
                    <span
                      key={i}
                      className="inline-block h-1.5 w-1.5 animate-bounce rounded-full bg-gray-300"
                      style={{ animationDelay: `${i * 150}ms` }}
                    />
                  ))}
                </div>
              </AITurn>
            ) : storyError ? (
              <AITurn trace={null} generationTimeMs={null}>
                <p className="text-sm text-gray-400">
                  This data story is temporarily unavailable. Please try again shortly.
                </p>
              </AITurn>
            ) : storyResult ? (
              <AITurn trace={storyTrace} generationTimeMs={0}>
                <DataStoryMessage story={storyResult} />
              </AITurn>
            ) : null}
          </div>
        ) : null}

        <div ref={endRef} />
      </div>
    </div>
  );
}
