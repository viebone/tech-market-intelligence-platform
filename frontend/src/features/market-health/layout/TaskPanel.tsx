// Catalogue-driven Task Panel (added 2026-09-04 — changes/2026-09-04-about-this-platform-welcome.md).
// Structure: a pinned welcome, then one item per story-catalogue entry, then pinned feature
// tasks. Only the pinned tasks are hardcoded here; the catalogue section comes from the
// `stories` prop (GET /api/market-health/stories) so a new backend story needs no change here.
//
// Footer (added 2026-09-23 — changes/2026-09-23-user-feedback-mechanism.md): a fourth,
// persistent, non-task zone below the task list — see design/information-architecture.md —
// "Task Panel Footer" and design/feedback/experience.md. Selecting it opens an overlay rather
// than changing the active Task, so it's additive to, not part of, the task-list rendering
// above.

import { useState } from "react";
import { FeedbackPanel } from "../../feedback/FeedbackPanel";

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

function FeedbackIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
      <path
        fillRule="evenodd"
        d="M10 2c-2.236 0-4.43.18-6.57.524C1.993 2.755 1 4.014 1 5.426v5.148c0 1.413.993 2.67 2.43 2.902.848.137 1.705.248 2.57.331v3.443a.75.75 0 0 0 1.28.53l3.58-3.579a.78.78 0 0 1 .527-.224 41.202 41.202 0 0 0 5.183-.5c1.437-.232 2.43-1.49 2.43-2.902V5.426c0-1.413-.993-2.67-2.43-2.902A41.289 41.289 0 0 0 10 2Z"
        clipRule="evenodd"
      />
    </svg>
  );
}

export function TaskPanel({ activeTaskId, onSelect, stories }: TaskPanelProps) {
  const [isFeedbackPanelOpen, setIsFeedbackPanelOpen] = useState(false);

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

      <div className="mt-auto px-3 pt-2 pb-4 border-t border-gray-800">
        <button
          onClick={() => setIsFeedbackPanelOpen(true)}
          className="w-full text-left flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:text-gray-100 transition-colors"
        >
          <FeedbackIcon />
          <span className="truncate">Give Feedback</span>
        </button>
      </div>

      {isFeedbackPanelOpen && (
        <FeedbackPanel onClose={() => setIsFeedbackPanelOpen(false)} />
      )}
    </aside>
  );
}
