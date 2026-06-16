interface PromptViewerProps {
  prompt: string;
  onClose: () => void;
}

export function PromptViewer({ prompt, onClose }: PromptViewerProps) {
  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg max-w-lg w-full p-6 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700">Prompt</h2>
          <button
            onClick={onClose}
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
        <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
          {prompt}
        </p>
      </div>
    </div>
  );
}
