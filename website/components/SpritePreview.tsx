"use client";

interface SpritePreviewProps {
  spriteBase64: string;
}

function downloadBase64Png(base64: string, filename: string) {
  const link = document.createElement("a");
  link.href = `data:image/png;base64,${base64}`;
  link.download = filename;
  link.click();
}

export default function SpritePreview({ spriteBase64 }: SpritePreviewProps) {
  return (
    <div className="fr-panel p-5 fr-appear">

      {/* Section label — styled like a FireRed screen header */}
      <div className="fr-panel-dark p-3 mb-4 flex items-center justify-between">
        <span className="fr-label" style={{ color: "var(--fr-cream)" }}>
          SPRITE SHEET
        </span>
        <span className="fr-small" style={{ color: "var(--fr-gray)" }}>
          FRONT · BACK
        </span>
      </div>

      {/* Sprite display — pixelated upscale */}
      <div
        className="fr-panel mb-4 flex justify-center items-center overflow-hidden"
        style={{ padding: "16px", background: "var(--fr-white)" }}
      >
        <img
          src={`data:image/png;base64,${spriteBase64}`}
          alt="Generated Pokémon sprite sheet"
          className="sprite-display"
          style={{ width: "100%", maxWidth: 480, height: "auto", display: "block" }}
        />
      </div>

      <button
        className="fr-btn"
        style={{ width: "100%" }}
        onClick={() => downloadBase64Png(spriteBase64, "pokemon-sprite.png")}
      >
        ▶ DOWNLOAD SPRITE
      </button>
    </div>
  );
}
