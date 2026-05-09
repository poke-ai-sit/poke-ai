"use client";

interface ErrorDialogProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorDialog({ message, onRetry }: ErrorDialogProps) {
  return (
    <div className="fr-panel-red p-6 fr-appear">
      <div className="flex items-start gap-3 mb-4">
        <span className="fr-heading fr-red-txt shrink-0">!</span>
        <div>
          <p className="fr-label fr-red-txt mb-2">Oh no!</p>
          <p className="fr-body">{message}</p>
        </div>
      </div>
      <hr className="fr-divider mb-4" />
      <button className="fr-btn fr-btn-red" onClick={onRetry}>
        ▶ Try Again
      </button>
    </div>
  );
}
