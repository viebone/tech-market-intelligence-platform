export interface Task {
  id: string;
  label: string;
}

export const TASKS: Task[] = [
  { id: "market-health", label: "Tech market hiring status" },
];

interface TaskPanelProps {
  activeTaskId: string;
  onSelect: (id: string) => void;
}

export function TaskPanel({ activeTaskId, onSelect }: TaskPanelProps) {
  return (
    <aside className="w-60 shrink-0 flex flex-col border-r border-gray-800 bg-gray-900 overflow-y-auto">
      <div className="px-3 pt-4 pb-2">
        <p className="text-[10px] font-medium text-gray-500 uppercase tracking-widest px-2 mb-2">
          Tasks
        </p>
        <nav className="flex flex-col gap-0.5">
          {TASKS.map((task) => {
            const isActive = task.id === activeTaskId;
            return (
              <button
                key={task.id}
                onClick={() => onSelect(task.id)}
                className={`w-full text-left flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-gray-800 text-gray-100 font-medium"
                    : "text-gray-400 hover:bg-gray-800/60 hover:text-gray-200"
                }`}
              >
                <span
                  className={`shrink-0 w-1.5 h-1.5 rounded-full transition-colors ${
                    isActive ? "bg-indigo-400" : "bg-transparent"
                  }`}
                />
                <span className="truncate">{task.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
