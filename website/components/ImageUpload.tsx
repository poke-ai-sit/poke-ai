"use client";

import { useRef, useState } from "react";

interface ImageUploadProps {
  onImage: (base64: string | null) => void;
}

const MAX_BYTES = 1_000_000;

function resizeImageClientSide(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const canvas = document.createElement("canvas");
      let { width, height } = img;
      const maxPx = Math.sqrt(MAX_BYTES / 3);
      if (width > maxPx || height > maxPx) {
        const scale = maxPx / Math.max(width, height);
        width = Math.floor(width * scale);
        height = Math.floor(height * scale);
      }
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      if (!ctx) return reject(new Error("Canvas unavailable"));
      ctx.drawImage(img, 0, 0, width, height);
      URL.revokeObjectURL(url);
      resolve(canvas.toDataURL("image/png").replace(/^data:image\/png;base64,/, ""));
    };
    img.onerror = () => reject(new Error("Image load failed"));
    img.src = url;
  });
}

export default function ImageUpload({ onImage }: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  async function handleFile(file: File) {
    try {
      const base64 = await resizeImageClientSide(file);
      setPreview(`data:image/png;base64,${base64}`);
      onImage(base64);
    } catch {
      onImage(null);
    }
  }

  function handleRemove() {
    setPreview(null);
    onImage(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div>
      <p className="fr-label mb-3" style={{ color: "var(--fr-shadow)" }}>
        REFERENCE IMAGE
        <span className="fr-small fr-muted ml-2">(optional)</span>
      </p>

      {preview ? (
        <div className="flex items-center gap-4">
          <div className="fr-panel p-2 inline-block">
            <img
              src={preview}
              alt="Reference"
              className="sprite-display"
              style={{ width: 80, height: 80, objectFit: "cover", display: "block" }}
            />
          </div>
          <div>
            <p className="fr-small fr-muted mb-3">Image ready!</p>
            <button className="fr-btn fr-btn-red" onClick={handleRemove}>
              Remove
            </button>
          </div>
        </div>
      ) : (
        <div
          role="button"
          tabIndex={0}
          className={`fr-panel p-6 text-center cursor-pointer transition-opacity ${dragging ? "opacity-60" : ""}`}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const file = e.dataTransfer.files[0];
            if (file) handleFile(file);
          }}
        >
          <p className="fr-label fr-muted mb-2">[ DROP IMAGE HERE ]</p>
          <p className="fr-small fr-muted">or press to browse</p>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
    </div>
  );
}
