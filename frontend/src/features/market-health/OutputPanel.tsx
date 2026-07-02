import type { Message } from "ai";

interface OutputRef {
  id: string;
  type: "chart" | "analysis";
  label: string;
  description: string;
}

function scrollToTurn(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function ChartIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className="w-4 h-4"
    >
      <path d="M15.5 2A1.5 1.5 0 0 0 14 3.5v13a1.5 1.5 0 0 0 3 0v-13A1.5 1.5 0 0 0 15.5 2ZM9.5 6A1.5 1.5 0 0 0 8 7.5v9a1.5 1.5 0 0 0 3 0v-9A1.5 1.5 0 0 0 9.5 6ZM3.5 10A1.5 1.5 0 0 0 2 11.5v5a1.5 1.5 0 0 0 3 0v-5A1.5 1.5 0 0 0 3.5 10Z" />
    </svg>
  );
}

function TextIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className="w-4 h-4"
    >
      <path
        fillRule="evenodd"
        d="M4 4a2 2 0 0 1 2-2h4.586A2 2 0 0 1 12 2.586L15.414 6A2 2 0 0 1 16 7.414V16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4Zm2 6a1 1 0 0 1 1-1h6a1 1 0 1 1 0 2H7a1 1 0 0 1-1-1Zm1 3a1 1 0 1 0 0 2h4a1 1 0 1 0 0-2H7Z"
        clipRule="evenodd"
      />
    </svg>
  );
}

interface OutputPanelProps {
  messages: Message[];
}

export function OutputPanel({ messages }: OutputPanelProps) {
  const userMessages = messages.filter((m) => m.role === "user");
  const assistantMessages = messages.filter((m) => m.role === "assistant");

  const refs: OutputRef[] = [
    {
      id: "turn-opening",
      type: "chart",
      label: "Job openings trend",
      description: "Monthly openings by Designer, PM, Engineer",
    },
    ...assistantMessages.map((m, i) => {
      const question = userMessages[i]?.content ?? "";
      const label =
        question.length > 0
          ? question.slice(0, 44).trimEnd() + (question.length > 44 ? "…" : "")
          : `Response ${i + 1}`;
      const description =
        m.content.slice(0, 80).trimEnd() + (m.content.length > 80 ? "…" : "");
      return {
        id: `turn-${m.id}`,
        type: "analysis" as const,
        label,
        description,
      };
    }),
  ];

  return (
    <aside className="w-80 shrink-0 flex flex-col border-l border-gray-800 bg-gray-900 overflow-y-auto">
      <div className="shrink-0 px-4 py-3 border-b border-gray-800">
        <p className="text-[10px] font-medium text-gray-500 uppercase tracking-widest">
          Output
        </p>
      </div>

      <div className="flex-1 p-2 space-y-0.5">
        {refs.map((ref) => (
          <button
            key={ref.id}
            onClick={() => scrollToTurn(ref.id)}
            className="w-full text-left flex items-start gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-800 transition-colors group"
          >
            <span className="shrink-0 mt-0.5 text-gray-500 group-hover:text-gray-400 transition-colors">
              {ref.type === "chart" ? <ChartIcon /> : <TextIcon />}
            </span>
            <span className="min-w-0">
              <span className="block text-xs font-medium text-gray-300 group-hover:text-gray-100 transition-colors truncate">
                {ref.label}
              </span>
              <span className="block text-[11px] leading-normal text-gray-500 mt-0.5 line-clamp-2">
                {ref.description}
              </span>
            </span>
          </button>
        ))}
      </div>
    </aside>
  );
}
