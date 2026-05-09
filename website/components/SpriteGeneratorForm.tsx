"use client";

import { useState } from "react";
import ImageUpload from "./ImageUpload";

const EXAMPLE_PROMPTS = [
  "a small cute rusty old car, round headlights as eyes, happy expression",
  "a sleek red Ferrari sports car, aggressive headlights, low to the ground, intimidating",
  "a glowing blue jellyfish made of electricity, trailing sparks, ethereal",
];

interface SpriteGeneratorFormProps {
  onSubmit: (prompt: string, referenceImageBase64?: string) => void;
  isLoading: boolean;
}

export default function SpriteGeneratorForm({
  onSubmit,
  isLoading,
}: SpriteGeneratorFormProps) {
  const [prompt, setPrompt] = useState("");
  const [refImage, setRefImage] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    onSubmit(prompt.trim(), refImage ?? undefined);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-[7px] mb-2 tracking-wider">
          DESCRIBE YOUR POKÉMON
        </label>
        <div className="fr-panel p-0 overflow-hidden">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="A small dragon made of molten lava..."
            rows={3}
            maxLength={500}
            disabled={isLoading}
            className="w-full p-3 bg-[var(--fr-cream)] text-[var(--fr-border)] text-[7px] leading-relaxed tracking-wide resize-none outline-none font-[inherit] placeholder:text-[var(--fr-gray)] disabled:opacity-60"
          />
        </div>
        <p className="text-[6px] text-[var(--fr-shadow)] mt-1 text-right">
          {prompt.length}/500
        </p>
      </div>

      {/* Example prompt chips */}
      <div>
        <p className="text-[6px] text-[var(--fr-shadow)] mb-2 tracking-wider">EXAMPLES</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_PROMPTS.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => setPrompt(ex)}
              disabled={isLoading}
              className="fr-btn text-[5px] px-2 py-1"
            >
              {ex.slice(0, 20)}…
            </button>
          ))}
        </div>
      </div>

      <ImageUpload onImage={setRefImage} />

      <button
        type="submit"
        disabled={isLoading || !prompt.trim()}
        className="fr-btn w-full text-[8px] py-3"
      >
        {isLoading ? "Generating…" : "Generate Pokémon"}
      </button>
    </form>
  );
}
