import { ChangeEvent, FormEvent } from "react";

interface ChatInputProps {
  input: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
  isLoading: boolean;
}

export function ChatInput({ input, onChange, onSubmit, isLoading }: ChatInputProps) {
  return (
    <div className="shrink-0 border-t border-gray-100 bg-white px-4 py-3">
      <form onSubmit={onSubmit} className="flex items-center gap-2 max-w-3xl mx-auto">
        <input
          type="text"
          value={input}
          onChange={onChange}
          placeholder="Ask about the market…"
          disabled={isLoading}
          className="flex-1 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-800 placeholder:text-gray-300 focus:border-gray-400 focus:bg-white focus:outline-none focus:ring-1 focus:ring-gray-400 disabled:opacity-50 transition-colors"
          aria-label="Your question"
        />
        <button
          type="submit"
          disabled={isLoading || input.trim() === ""}
          className="shrink-0 rounded-md bg-gray-800 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  );
}
