// Suggested-question chips (added 2026-09-06 —
// changes/2026-09-03-chat-resilience-and-instant-answers.md). Surfaces the curated
// instant-answer catalogue so the fast path (no model call, <1s) is one tap.
// A chip click submits the exact question through the same path as typing it; the
// backend matches it to the curated catalogue and returns the instant answer.
// See frontend/specs/market-health/architecture.md — Suggested questions.

import { useQuery } from "@tanstack/react-query";

interface ChatSuggestion {
  id: string;
  question: string;
}

async function fetchChatSuggestions(): Promise<{ suggestions: ChatSuggestion[] }> {
  const res = await fetch("/api/market-health/chat-suggestions");
  if (!res.ok) throw new Error(`Failed to load chat suggestions (${res.status})`);
  return res.json();
}

interface SuggestedQuestionsProps {
  onAsk: (question: string) => void;
  /** True while a chat request is streaming — chips are inert until it finishes. */
  disabled?: boolean;
}

export function SuggestedQuestions({ onAsk, disabled }: SuggestedQuestionsProps) {
  const { data } = useQuery({
    queryKey: ["market-health", "chat-suggestions"],
    queryFn: fetchChatSuggestions,
    staleTime: 5 * 60 * 1000,
  });

  const suggestions = data?.suggestions ?? [];
  if (suggestions.length === 0) return null; // enhancement, not a dependency

  return (
    <div className="flex flex-col gap-2">
      <p className="text-[10px] font-medium uppercase tracking-widest text-gray-500">
        Instant answers — no AI, under a second
      </p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((s) => (
          <button
            key={s.id}
            type="button"
            disabled={disabled}
            onClick={() => onAsk(s.question)}
            className="rounded-full border border-gray-700 bg-gray-800/60 px-3 py-1.5 text-xs text-gray-300 transition-colors hover:border-gray-500 hover:bg-gray-800 hover:text-gray-100 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {s.question}
          </button>
        ))}
      </div>
    </div>
  );
}
