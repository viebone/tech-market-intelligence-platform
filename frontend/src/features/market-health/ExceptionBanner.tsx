export interface Exception {
  id: string;
  title: string;
  description: string;
  severity: "info" | "warning" | "critical";
  createdAt: string;
}

interface ExceptionBannerProps {
  exceptions: Exception[];
  onDismiss: () => void;
}

export function ExceptionBanner({ exceptions, onDismiss }: ExceptionBannerProps) {
  if (exceptions.length === 0) {
    return null;
  }

  return (
    <div
      role="alert"
      aria-live="polite"
      className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-amber-900">
            {exceptions.length === 1
              ? "1 unresolved alert since your last visit"
              : `${exceptions.length} unresolved alerts since your last visit`}
          </p>
          <ul className="mt-2 space-y-1">
            {exceptions.map((ex) => (
              <li key={ex.id} className="text-sm text-amber-800">
                <span className="font-medium">{ex.title}</span>
                {ex.description && (
                  <span className="text-amber-700"> — {ex.description}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Dismiss alerts"
          className="shrink-0 rounded p-1 text-amber-600 hover:bg-amber-100 hover:text-amber-800 focus:outline-none focus:ring-2 focus:ring-amber-400 transition-colors"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            className="w-4 h-4"
            aria-hidden="true"
          >
            <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
          </svg>
        </button>
      </div>
    </div>
  );
}
