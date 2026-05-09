"use client";

interface IconPreviewProps {
  iconBase64: string;
}

function downloadBase64Png(base64: string, filename: string) {
  const link = document.createElement("a");
  link.href = `data:image/png;base64,${base64}`;
  link.download = filename;
  link.click();
}

export default function IconPreview({ iconBase64 }: IconPreviewProps) {
  return (
    <div className="fr-panel p-5 fr-appear fr-appear-2">

      {/* Section header */}
      <div className="fr-panel-dark p-3 mb-4 flex items-center justify-between">
        <span className="fr-label" style={{ color: "var(--fr-cream)" }}>
          PARTY ICON
        </span>
        <span className="fr-small" style={{ color: "var(--fr-gray)" }}>
          40 × 40 px
        </span>
      </div>

      <div className="flex items-center gap-5 mb-4">
        {/* Icon displayed at 4× (160×160) with pixelated rendering */}
        <div
          className="fr-panel flex-shrink-0"
          style={{ padding: 12, background: "var(--fr-white)" }}
        >
          <img
            src={`data:image/png;base64,${iconBase64}`}
            alt="Pokémon party icon"
            className="sprite-display"
            style={{ width: 160, height: 160, display: "block" }}
          />
        </div>

        <div>
          <p className="fr-label mb-2">In-game size</p>
          <div
            className="fr-panel mb-3"
            style={{ padding: 4, background: "var(--fr-white)", display: "inline-block" }}
          >
            <img
              src={`data:image/png;base64,${iconBase64}`}
              alt="Actual-size icon"
              className="sprite-display"
              style={{ width: 40, height: 40, display: "block" }}
            />
          </div>
          <p className="fr-small fr-muted">This appears in the party&nbsp;/ Pokédex list</p>
        </div>
      </div>

      <button
        className="fr-btn"
        style={{ width: "100%" }}
        onClick={() => downloadBase64Png(iconBase64, "pokemon-icon.png")}
      >
        ▶ DOWNLOAD ICON
      </button>
    </div>
  );
}
