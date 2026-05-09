"use client";

import { useState } from "react";
import ImageUpload from "./ImageUpload";

interface Example { label: string; prompt: string; }

const EXAMPLES: Example[] = [
  { label: "Rusty Car",   prompt: "a small cute rusty old car, round headlights as eyes, happy expression, compact kei-car body style" },
  { label: "Red Ferrari", prompt: "a sleek red Ferrari sports car Pokemon, aggressive headlights as eyes, low to the ground, intimidating expression, exhaust flames coming from the back" },
  { label: "Jellyfish",   prompt: "a glowing blue jellyfish made of pure electricity, trailing crackling sparks, translucent bell, ethereal glow" },
];

interface SpriteGeneratorFormProps {
  onSubmit: (prompt: string, referenceImageBase64?: string) => void;
  isLoading: boolean;
}

export default function SpriteGeneratorForm({ onSubmit, isLoading }: SpriteGeneratorFormProps) {
  const [prompt, setPrompt] = useState("");
  const [refImage, setRefImage] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    onSubmit(prompt.trim(), refImage ?? undefined);
  }

  return (
    <form onSubmit={handleSubmit}>

      {/* Prompt input */}
      <div className="mb-6">
        <label className="fr-label block mb-3">
          DESCRIBE YOUR POKÉMON
        </label>
        <div className="fr-panel overflow-hidden">
          <textarea
            className="fr-input"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="A small dragon made of molten lava, fierce eyes, tiny wings…"
            rows={4}
            maxLength={500}
            disabled={isLoading}
          />
        </div>
        <p className="fr-small fr-muted text-right mt-2">
          {prompt.length} / 500
        </p>
      </div>

      <hr className="fr-divider mb-6" />

      {/* Example chips */}
      <div className="mb-6">
        <p className="fr-small fr-muted mb-3">QUICK EXAMPLES</p>
        <div className="flex flex-wrap gap-3">
          {EXAMPLES.map((ex) => (
            <button
              key={ex.label}
              type="button"
              onClick={() => setPrompt(ex.prompt)}
              disabled={isLoading}
              className="fr-btn"
              style={{ fontSize: "var(--fs-xs)", padding: "8px 14px" }}
            >
              {ex.label}
            </button>
          ))}
        </div>
      </div>

      <hr className="fr-divider mb-6" />

      {/* Image upload */}
      <div className="mb-8">
        <ImageUpload onImage={setRefImage} />
      </div>

      {/* Generate button */}
      <button
        type="submit"
        disabled={isLoading || !prompt.trim()}
        className="fr-btn fr-btn-generate"
      >
        {isLoading ? (
          <>
            <span className="fr-dot-1">.</span>
            <span className="fr-dot-2">.</span>
            <span className="fr-dot-3">.</span>
            &nbsp; GENERATING
          </>
        ) : (
          "▶ GENERATE POKÉMON"
        )}
      </button>
    </form>
  );
}
