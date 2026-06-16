import { useState } from "react";
import { PromptViewer } from "./PromptViewer";

interface PromptBadgeProps {
  prompt: string;
}

export function PromptBadge({ prompt }: PromptBadgeProps) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="text-xs text-gray-300 hover:text-gray-500 transition-colors focus:outline-none"
      >
        view prompt
      </button>
      {open && <PromptViewer prompt={prompt} onClose={() => setOpen(false)} />}
    </>
  );
}
