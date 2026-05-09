"use client";

interface ErrorDialogProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorDialog({ message, onRetry }: ErrorDialogProps) {
  return (
    <div className="fr-panel-red p-4">
      <p className="text-[8px] leading-relaxed text-[var(--fr-red)] tracking-wide mb-3">
        ERROR!
      </p>
      <p className="text-[7px] leading-relaxed text-[var(--fr-border)] mb-4">
        {message}
      </p>
      <button className="fr-btn fr-btn-red text-[7px]" onClick={onRetry}>
        Try Again
      </button>
    </div>
  );
}
