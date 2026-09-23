import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

// Thumbs up/down "Was this useful?" control at the bottom of every Data
// Story. design/market-health/data-stories.md — "Feedback reaction — every
// story"; design/visual-design.md — "Data Story — Feedback reaction".
//
// Reaction and comment are two separate captures (backend/src/feedback.py —
// both hit POST /api/feedback/story-reaction). Re-clicking the already
// selected thumb is a pure local UI reset — there's no "un-set" endpoint, so
// nothing is sent for that case.

type Reaction = "up" | "down";

interface StoryFeedbackReactionProps {
  storyId: string;
}

async function submitStoryReaction(storyId: string, reaction: Reaction, comment?: string): Promise<void> {
  const res = await fetch("/api/feedback/story-reaction", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      story_id: storyId,
      reaction,
      ...(comment && comment.trim().length > 0 ? { comment } : {}),
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to submit story reaction (${res.status})`);
  }
}

function ThumbsUpIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
      <path d="M1 9.25a1.25 1.25 0 1 1 2.5 0v6.5a1.25 1.25 0 1 1-2.5 0v-6.5ZM11 3.5V2.4c0-.245.128-.482.362-.556A1.83 1.83 0 0 1 13 3.5c0 .911-.166 1.783-.47 2.587-.187.494.152 1.075.681 1.075h2.307c1.138 0 2.07.924 1.964 2.056a21.856 21.856 0 0 1-1.228 5.47C15.976 15.696 14.98 16.3 13.905 16.3H11a2.75 2.75 0 0 1-1.228-.29l-2.5-1.25A2.75 2.75 0 0 0 6.045 14.5H5v-6.5h.882c.627 0 1.152-.442 1.476-.978a3.672 3.672 0 0 1 1.984-1.584c.395-.13.78-.353.925-.745.147-.395.227-.824.227-1.271Z" />
    </svg>
  );
}

function ThumbsDownIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
      <path d="M19 10.75a1.25 1.25 0 1 1-2.5 0v-6.5a1.25 1.25 0 1 1 2.5 0v6.5ZM9 16.5v1.1c0 .245-.128.482-.362.556A1.83 1.83 0 0 1 7 16.5c0-.911.166-1.783.47-2.587.187-.494-.152-1.075-.681-1.075H4.482c-1.138 0-2.07-.924-1.964-2.056a21.856 21.856 0 0 1 1.228-5.47C4.024 4.304 5.02 3.7 6.095 3.7H9c.436 0 .866.101 1.228.29l2.5 1.25A2.75 2.75 0 0 0 13.955 5.5H15V12h-.882c-.627 0-1.152.442-1.476.978a3.672 3.672 0 0 1-1.984 1.584c-.395.13-.78.353-.925.745-.147.395-.227.824-.227 1.271Z" />
    </svg>
  );
}

export function StoryFeedbackReaction({ storyId }: StoryFeedbackReactionProps) {
  const [selected, setSelected] = useState<Reaction | null>(null);
  const [showCommentField, setShowCommentField] = useState(false);
  const [comment, setComment] = useState("");
  const [commentSubmitted, setCommentSubmitted] = useState(false);

  const reactionMutation = useMutation({
    mutationFn: (reaction: Reaction) => submitStoryReaction(storyId, reaction),
  });

  const commentMutation = useMutation({
    // The reaction is already recorded by the click above — this is a second,
    // independent capture carrying just the comment. The backend's
    // story_reaction schema still requires `reaction` on every request
    // (backend/src/feedback.py — StoryReactionRequest has no default), so it
    // repeats the down reaction that's already selected rather than omitting it.
    mutationFn: () => submitStoryReaction(storyId, "down", comment),
    onSuccess: () => setCommentSubmitted(true),
  });

  function handleThumbClick(reaction: Reaction) {
    if (selected === reaction) {
      // Clicking the already-selected thumb clears it — a pure local reset,
      // never a new request (no "un-set reaction" endpoint exists).
      setSelected(null);
      setShowCommentField(false);
      setComment("");
      setCommentSubmitted(false);
      return;
    }

    setSelected(reaction);
    reactionMutation.mutate(reaction);

    if (reaction === "down") {
      setShowCommentField(true);
      setCommentSubmitted(false);
    } else {
      setShowCommentField(false);
    }
  }

  function handleCommentSubmit() {
    if (comment.trim().length === 0) return;
    commentMutation.mutate();
  }

  return (
    <div className="flex flex-col items-center gap-2 pt-2">
      <p className="text-[11px] text-gray-500">Was this useful?</p>
      <div className="flex gap-2">
        <button
          type="button"
          aria-pressed={selected === "up"}
          aria-label="Thumbs up"
          onClick={() => handleThumbClick("up")}
          className={`flex h-8 w-8 items-center justify-center rounded-md border border-gray-700 transition-colors ${
            selected === "up" ? "bg-emerald-600 text-white" : "text-gray-400 hover:text-gray-100"
          }`}
        >
          <ThumbsUpIcon />
        </button>
        <button
          type="button"
          aria-pressed={selected === "down"}
          aria-label="Thumbs down"
          onClick={() => handleThumbClick("down")}
          className={`flex h-8 w-8 items-center justify-center rounded-md border border-gray-700 transition-colors ${
            selected === "down" ? "bg-gray-600 text-white" : "text-gray-400 hover:text-gray-100"
          }`}
        >
          <ThumbsDownIcon />
        </button>
      </div>

      {selected === "down" && showCommentField && !commentSubmitted && (
        <div className="w-full max-w-sm transition-all duration-200">
          <textarea
            rows={2}
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            maxLength={2000}
            placeholder="What could be better about this story?"
            className="w-full resize-y rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          {commentMutation.isError && (
            <p className="mt-1 text-xs text-red-400">Couldn't send that — try again.</p>
          )}
          <div className="mt-1 flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setShowCommentField(false)}
              className="text-xs text-gray-400 hover:text-gray-200 transition-colors"
            >
              Dismiss
            </button>
            <button
              type="button"
              onClick={handleCommentSubmit}
              disabled={commentMutation.isPending}
              className="text-xs text-gray-400 hover:text-gray-200 transition-colors"
            >
              Submit
            </button>
          </div>
        </div>
      )}

      {selected === "down" && commentSubmitted && (
        <p className="text-[11px] text-gray-500">Thanks for the detail.</p>
      )}
    </div>
  );
}
