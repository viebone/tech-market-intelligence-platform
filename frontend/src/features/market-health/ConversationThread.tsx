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
    // changes/2026-08-17-chat-scroll-white-gap.md.
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages.length, isLoading, activeDemoSim?.phase, activeTaskId]);

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

  const dots = (
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
  );

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-[1200px] mx-auto px-6 py-8 space-y-8">

        {/* ── Opening turn for the active task ──────────────────────────────
            Each task is its own conversation (useChat id = activeTaskId). The
            opening turn is the task's seed; the conversation below it is that
            task's own history — the chat input always queries the active task.
            See changes/2026-09-06-chat-input-dead-on-non-conversation-tasks.md. */}

        {activeTaskId === WELCOME_TASK_ID && (
          <div id="turn-about-this-platform">
            {welcomeLoading ? (
              <AITurn trace={null} generationTimeMs={null} isStreaming={true}>{dots}</AITurn>
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
        )}

        {activeTaskId === HIRING_STATUS_TASK_ID && (
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
          </>
        )}

        {selectedStoryId && (
          <div id={`turn-${selectedStoryId}`}>
            {storyLoading ? (
              <AITurn trace={null} generationTimeMs={null} isStreaming={true}>{dots}</AITurn>
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
        )}

        {/* ── Instant-answer chips — every task ──────────────────────────── */}
        <SuggestedQuestions onAsk={onAskSuggestion} disabled={isLoading} />

        {/* ── This task's conversation — every task ─────────────────────────
            useChat's per-task message list. A question and its answer live in
            whichever task the user asked them from. */}
        {pairs.map(({ user, assistant }, index) => {
          const traceEntry = assistant ? traces.get(assistant.id) : undefined;
          const isStreamingThis = isLoading && assistant?.id === lastAssistantId;
          // The hiring-status task shows its own OPENING_PROMPT title above; on
          // the other tasks the first question is the conversation's opening.
          const isFirst = index === 0 && activeTaskId !== HIRING_STATUS_TASK_ID;

          return (
            <div key={user.id} className="space-y-8">
              <UserTurn prompt={user.content} isFirst={isFirst} />
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
                <AITurn>{dots}</AITurn>
              ) : null}
            </div>
          );
        })}

        {/* Demo simulation turn — driven by user submitting the chat input */}
        {activeDemoSim && (
          <div className="space-y-8">
            <UserTurn prompt={activeDemoSim.userPrompt} />
            {activeDemoSim.phase === "thinking" ? (
              <AITurn trace={null} generationTimeMs={null} isStreaming={true}>{dots}</AITurn>
            ) : (
              <AITurn trace={activeDemoSim.trace} generationTimeMs={activeDemoSim.generationTimeMs}>
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
