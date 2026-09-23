import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { useMutation } from "@tanstack/react-query";
import { RatingControl } from "./RatingControl";

// The product-level Feedback Panel — opened from the Task Panel Footer's "Give
// Feedback" entry (frontend/specs/user-feedback/architecture.md). Portaled to
// document.body so it escapes TaskPanel's overflow-y-auto container, same reason
// any fixed-position overlay in this codebase needs a portal rather than relying
// on CSS position:fixed inside a scrolling ancestor.
//
// design/feedback/experience.md — User Flow / Edge Cases;
// design/visual-design.md — "Task Panel Footer & Feedback Panel".

type Phase = "form" | "submitting" | "confirmed" | "error";

const CONFIRMATION_AUTO_CLOSE_MS = 2500;

async function submitPlatformRating(rating: number, comment: string): Promise<void> {
  const res = await fetch("/api/feedback/platform-rating", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      rating,
      comment: comment.trim().length > 0 ? comment : undefined,
    }),
  });
  if (!res.ok) {
    throw new Error(`Failed to submit platform rating (${res.status})`);
  }
}

function CloseIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4">
      <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
    </svg>
  );
}

function CheckmarkIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-10 w-10 text-emerald-400">
      <path
        fillRule="evenodd"
        d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z"
        clipRule="evenodd"
      />
    </svg>
  );
}

interface FeedbackPanelProps {
  onClose: () => void;
}

export function FeedbackPanel({ onClose }: FeedbackPanelProps) {
  const [rating, setRating] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [phase, setPhase] = useState<Phase>("form");

  const submitMutation = useMutation({
    mutationFn: () => submitPlatformRating(rating as number, comment),
    onSuccess: () => setPhase("confirmed"),
    onError: () => setPhase("error"),
  });

  // Auto-close the confirmation state after a couple of seconds — or
  // immediately on any click/Escape, handled by the onClick/keydown
  // handlers below, whichever comes first (experience spec — Interactions).
  useEffect(() => {
    if (phase !== "confirmed") return;
    const timer = setTimeout(onClose, CONFIRMATION_AUTO_CLOSE_MS);
    return () => clearTimeout(timer);
  }, [phase, onClose]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  function handleSubmit() {
    if (rating === null || phase === "submitting") return;
    setPhase("submitting");
    submitMutation.mutate();
  }

  const submitDisabled = rating === null || phase === "submitting";

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/70"
      onClick={onClose}
    >
      <div
        className="w-full max-w-[420px] rounded-lg border border-gray-700 bg-gray-800 p-6"
        onClick={(event) => event.stopPropagation()}
      >
        {phase === "confirmed" ? (
          <div
            className="flex cursor-pointer flex-col items-center gap-3 py-4 text-center"
            onClick={onClose}
          >
            <CheckmarkIcon />
            <p className="text-sm text-gray-300">Thanks — that helps us improve the platform.</p>
          </div>
        ) : (
          <>
            <div className="mb-4 flex items-start justify-between gap-4">
              <h2 className="text-sm font-medium text-gray-100">
                How satisfied are you with this platform?
              </h2>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close"
                className="shrink-0 text-gray-400 hover:text-gray-200 transition-colors"
              >
                <CloseIcon />
              </button>
            </div>

            <RatingControl value={rating} onChange={setRating} />

            <div className="mt-4">
              <label htmlFor="feedback-comment" className="mb-1 block text-sm text-gray-300">
                Anything you'd like to tell us? (optional)
              </label>
              <textarea
                id="feedback-comment"
                rows={3}
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                maxLength={2000}
                className="w-full resize-y rounded-lg border border-gray-700 bg-gray-800 px-3.5 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            {phase === "error" && (
              <p className="mt-3 text-xs text-red-400">Couldn't send that — try again.</p>
            )}

            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={handleSubmit}
                disabled={submitDisabled}
                className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                  submitDisabled
                    ? "bg-gray-700 text-gray-500"
                    : "bg-indigo-600 text-white hover:bg-indigo-700"
                }`}
              >
                Submit
              </button>
            </div>
          </>
        )}
      </div>
    </div>,
    document.body,
  );
}
