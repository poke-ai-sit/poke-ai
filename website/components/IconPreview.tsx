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
    <div className="fr-panel p-3">
      <p className="text-[7px] mb-2 tracking-wider">PARTY ICON</p>
      <div className="flex items-center gap-4 mb-3">
        {/* Party slot: display 40×40 at 4× = 160×160 */}
        <div className="fr-panel p-2 inline-block">
          <img
            src={`data:image/png;base64,${iconBase64}`}
            alt="Pokémon party icon"
            width={160}
            height={160}
            className="sprite-display"
          />
        </div>
        <div>
          <p className="text-[6px] text-[var(--fr-shadow)] leading-relaxed">
            40×40 party
            <br />
            slot icon
          </p>
        </div>
      </div>
      <button
        className="fr-btn text-[7px]"
        onClick={() => downloadBase64Png(iconBase64, "pokemon-icon.png")}
      >
        Download Icon
      </button>
    </div>
  );
}
