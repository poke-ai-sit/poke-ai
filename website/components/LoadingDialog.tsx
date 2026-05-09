"use client";

export default function LoadingDialog() {
  return (
    <div className="fr-panel-dialog p-6 fr-appear">
      {/* Mimics the FireRed textbox layout */}
      <div className="flex items-start gap-4 mb-5">
        <span className="fr-body fr-red-txt shrink-0">▶</span>
        <p className="fr-body">
          Generating your Pokémon
          <span className="fr-dot-1">.</span>
          <span className="fr-dot-2">.</span>
          <span className="fr-dot-3">.</span>
        </p>
      </div>

      {/* HP-style progress bar */}
      <div className="mb-3">
        <div className="fr-small fr-muted mb-2">PROGRESS</div>
        <div
          className="fr-panel w-full overflow-hidden"
          style={{ padding: "6px 8px" }}
        >
          <div className="fr-loading-bar rounded-none" />
        </div>
      </div>

      <p className="fr-small fr-muted text-right">May take up to 90s</p>
    </div>
  );
}
