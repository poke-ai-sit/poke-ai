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
      // Scale down until under MAX_BYTES (rough: 3 bytes/px for PNG)
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
      const dataUrl = canvas.toDataURL("image/png");
      resolve(dataUrl.replace(/^data:image\/png;base64,/, ""));
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
      <p className="text-[7px] mb-2 tracking-wider text-[var(--fr-shadow)]">
        REFERENCE IMAGE (optional)
      </p>
      {preview ? (
        <div className="flex items-center gap-3">
          <div className="fr-panel p-1">
            <img
              src={preview}
              alt="Reference"
              className="sprite-display w-16 h-16 object-cover"
            />
          </div>
          <button className="fr-btn fr-btn-red text-[6px]" onClick={handleRemove}>
            Remove
          </button>
        </div>
      ) : (
        <div
          className={`fr-panel p-4 text-center cursor-pointer transition-opacity ${
            dragging ? "opacity-60" : ""
          }`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const file = e.dataTransfer.files[0];
            if (file) handleFile(file);
          }}
        >
          <p className="text-[6px] text-[var(--fr-shadow)] leading-relaxed">
            Drop image here
            <br />
            or click to browse
          </p>
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
