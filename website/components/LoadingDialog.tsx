"use client";

export default function LoadingDialog() {
  return (
    <div className="fr-panel-dialog p-4 text-center">
      <p className="text-[8px] leading-relaxed tracking-wider">
        Generating your Pokémon
        <span className="loading-dot-1 ml-1">.</span>
        <span className="loading-dot-2">.</span>
        <span className="loading-dot-3">.</span>
      </p>
      <p className="text-[7px] mt-3 text-[var(--fr-shadow)]">
        This may take up to 90s
      </p>
    </div>
  );
}
