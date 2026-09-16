// Catalogue-driven Task Panel (added 2026-09-04 — changes/2026-09-04-about-this-platform-welcome.md).
// Structure: a pinned welcome, then one item per story-catalogue entry, then pinned feature
// tasks. Only the pinned tasks are hardcoded here; the catalogue section comes from the
// `stories` prop (GET /api/market-health/stories) so a new backend story needs no change here.

export interface StoryMeta {
  id: string;
  display_name: string;
  question: string;
  example_phrasings?: string[];
}

export interface Task {
  id: string;
  label: string;
}

export const WELCOME_TASK_ID = "about-this-platform";
export const HIRING_STATUS_TASK_ID = "market-health";

const WELCOME_TASK: Task = { id: WELCOME_TASK_ID, label: "About this platform" };
const HIRING_STATUS_TASK: Task = { id: HIRING_STATUS_TASK_ID, label: "Tech market hiring status" };

interface TaskPanelProps {
  activeTaskId: string;
  onSelect: (id: string) => void;
  /** Current story catalogue (GET /api/market-health/stories). May be empty while loading. */
  stories: StoryMeta[];
}

export function TaskPanel({ activeTaskId, onSelect, stories }: TaskPanelProps) {
  const tasks: Task[] = [
    WELCOME_TASK,
    ...stories.map((story) => ({ id: story.id, label: story.display_name })),
    HIRING_STATUS_TASK,
  ];

  return (
    <aside className="w-60 shrink-0 flex flex-col border-r border-gray-800 bg-gray-900 overflow-y-auto">
      <div className="px-3 pt-4 pb-2">
        <p className="text-[10px] font-medium text-gray-500 uppercase tracking-widest px-2 mb-2">
          Tasks
        </p>
        <nav className="flex flex-col gap-0.5">
          {tasks.map((task) => {
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
