"use client";

import { useReducer } from "react";
import { GenerateState } from "@/lib/types";
import FireRedPanel from "./FireRedPanel";
import SpriteGeneratorForm from "./SpriteGeneratorForm";
import SpritePreview from "./SpritePreview";
import IconPreview from "./IconPreview";
import LoadingDialog from "./LoadingDialog";
import ErrorDialog from "./ErrorDialog";

type Action =
  | { type: "START" }
  | { type: "SUCCESS"; sprite: string; icon: string }
  | { type: "ERROR"; message: string }
  | { type: "RESET" };

function reducer(_state: GenerateState, action: Action): GenerateState {
  switch (action.type) {
    case "START":   return { status: "loading" };
    case "SUCCESS": return { status: "success", sprite: action.sprite, icon: action.icon };
    case "ERROR":   return { status: "error", message: action.message };
    case "RESET":   return { status: "idle" };
  }
}

export default function HomeClient() {
  const [state, dispatch] = useReducer(reducer, { status: "idle" });

  async function handleGenerate(prompt: string, referenceImageBase64?: string) {
    dispatch({ type: "START" });

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 90_000);

    try {
      const res = await fetch("/api/generate-sprite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, referenceImageBase64 }),
        signal: controller.signal,
      });

      const data = await res.json();

      if (!res.ok) {
        dispatch({ type: "ERROR", message: data.error ?? "Generation failed." });
        return;
      }

      dispatch({ type: "SUCCESS", sprite: data.spriteBase64, icon: data.iconBase64 });
    } catch (err) {
      const msg =
        err instanceof Error && err.name === "AbortError"
          ? "Request timed out after 90s. Please try again."
          : "Network error. Please check your connection.";
      dispatch({ type: "ERROR", message: msg });
    } finally {
      clearTimeout(timeout);
    }
  }

  const isLoading = state.status === "loading";

  return (
    <div className="min-h-screen p-4 md:p-8 scanlines relative">
      {/* Header */}
      <div className="max-w-5xl mx-auto mb-6">
        <FireRedPanel className="p-4 text-center">
          <h1 className="text-[10px] md:text-[12px] tracking-wider leading-relaxed">
            PokéLive
          </h1>
          <p className="text-[6px] text-[var(--fr-shadow)] mt-1 tracking-widest">
            CUSTOM POKÉMON CREATOR
          </p>
        </FireRedPanel>
      </div>

      {/* Main layout */}
      <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Form */}
        <div className="space-y-4">
          <FireRedPanel className="p-4">
            <SpriteGeneratorForm
              onSubmit={handleGenerate}
              isLoading={isLoading}
            />
          </FireRedPanel>

          {state.status === "loading" && <LoadingDialog />}
          {state.status === "error" && (
            <ErrorDialog
              message={state.message}
              onRetry={() => dispatch({ type: "RESET" })}
            />
          )}
        </div>

        {/* Right: Results */}
        <div className="space-y-4">
          {state.status === "success" ? (
            <>
              <SpritePreview spriteBase64={state.sprite} />
              <IconPreview iconBase64={state.icon} />
            </>
          ) : (
            <FireRedPanel className="p-4 flex items-center justify-center min-h-[200px]">
              <p className="text-[7px] text-[var(--fr-shadow)] text-center tracking-wide leading-relaxed">
                Your Pokémon
                <br />
                will appear here
              </p>
            </FireRedPanel>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-5xl mx-auto mt-6 text-center">
        <p className="text-[5px] text-[var(--fr-gray)] tracking-widest">
          AI ENGINEER HACKATHON · SINGAPORE · MAY 9 2026
        </p>
      </div>
    </div>
  );
}
