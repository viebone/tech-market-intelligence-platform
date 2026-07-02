import { useChat } from "ai/react";
import { useRef, useEffect } from "react";

interface ConversationalAreaProps {
  context: {
    role: string;
    seniority: string;
    location: string;
  };
}

export function ConversationalArea({ context }: ConversationalAreaProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { messages, input, handleInputChange, handleSubmit, isLoading, error, reload } =
    useChat({
      api: "/api/chat",
      streamProtocol: "data",
      body: { context },
    });

  // Scroll to bottom of message list when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full rounded-lg border border-gray-100 bg-white overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100 shrink-0">
        <h2 className="text-sm font-semibold text-gray-700">Ask about the market</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Ask a plain-language question. Answers cite the supporting signals.
        </p>
      </div>

      {/* Message thread */}
      <div
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4 min-h-0"
        aria-live="polite"
        aria-label="Conversation"
      >
        {messages.length === 0 && !isLoading && (
          <div className="text-center py-6">
            <p className="text-sm text-gray-300">
              Try: "Is now a good time to look for a senior UX role in London?"
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
                message.role === "user"
                  ? "bg-gray-100 text-gray-800"
                  : "bg-white border border-gray-100 text-gray-700"
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}

        {/* Streaming / loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-lg border border-gray-100 px-3 py-2" aria-label="Loading response">
              <span className="sr-only">Loading response…</span>
              <span className="inline-flex gap-1" aria-hidden="true">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="inline-block w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 150}ms` }}
                  />
                ))}
              </span>
            </div>
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <div className="flex justify-start">
            <div className="rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-600 max-w-[85%]">
              <p>Something went wrong getting a response.</p>
              <button
                type="button"
                onClick={() => reload()}
                className="mt-1 text-xs underline hover:no-underline focus:outline-none"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-gray-100 shrink-0">
        <form
          onSubmit={handleSubmit}
          className="flex items-center gap-2"
          aria-label="Send a message"
        >
          <input
            type="text"
            value={input}
            onChange={handleInputChange}
            placeholder="Ask a question about the market…"
            disabled={isLoading}
            className="flex-1 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-800 placeholder:text-gray-300 focus:border-gray-400 focus:bg-white focus:outline-none focus:ring-1 focus:ring-gray-400 disabled:opacity-50 transition-colors"
            aria-label="Your question"
          />
          <button
            type="submit"
            disabled={isLoading || input.trim() === ""}
            className="shrink-0 rounded-md bg-gray-800 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            aria-label="Send"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
