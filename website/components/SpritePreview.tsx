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
    <div className="fr-panel p-3">
      <p className="text-[7px] mb-2 tracking-wider">SPRITE SHEET</p>
      <div className="flex justify-center mb-3">
        {/* Upscale 1024×1024 → display at 512×512 (0.5× of original, but 8× of the embedded 64×64 art) */}
        <img
          src={`data:image/png;base64,${spriteBase64}`}
          alt="Generated Pokémon sprite"
          width={512}
          height={512}
          className="sprite-display border-2 border-[var(--fr-border)]"
          style={{ maxWidth: "100%", height: "auto" }}
        />
      </div>
      <div className="flex gap-2 justify-center flex-wrap">
        <button
          className="fr-btn text-[7px]"
          onClick={() => downloadBase64Png(spriteBase64, "pokemon-sprite.png")}
        >
          Download Sprite
        </button>
      </div>
    </div>
  );
}
