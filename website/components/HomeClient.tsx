"use client";

import { useReducer } from "react";
import { GenerateState } from "@/lib/types";
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
    case "START":
      return { status: "loading" };
    case "SUCCESS":
      return { status: "success", sprite: action.sprite, icon: action.icon };
    case "ERROR":
      return { status: "error", message: action.message };
    case "RESET":
      return { status: "idle" };
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
        dispatch({
          type: "ERROR",
          message: data.error ?? "Generation failed.",
        });
        return;
      }

      dispatch({
        type: "SUCCESS",
        sprite: data.spriteBase64,
        icon: data.iconBase64,
      });
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
    <div
      className="fr-scanlines"
      style={{ minHeight: "100vh", padding: "24px 16px 40px" }}
    >
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        {/* ── Title bar ─── mimics the FireRed naming screen header */}
        <div
          className="fr-panel fr-appear"
          style={{
            marginBottom: 24,
            padding: "20px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div>
            {/* Red accent bar left of title — Pokédex red */}
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <div
                style={{
                  width: 8,
                  alignSelf: "stretch",
                  background: "var(--fr-red)",
                  minHeight: 40,
                  flexShrink: 0,
                  border: "2px solid var(--fr-border)",
                  boxShadow:
                    "inset 1px 1px 0 var(--fr-red-lt), inset -1px -1px 0 var(--fr-red-dk)",
                }}
              />
              <div>
                <h1
                  className="fr-title"
                  style={{
                    margin: 0,
                    background:
                      "linear-gradient(90deg, var(--fr-red) 0%, var(--fr-orange) 60%, #ffaa22 100%)",
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                  }}
                >
                  PokéLive
                </h1>
                <p className="fr-label fr-muted" style={{ margin: "4px 0 0" }}>
                  CUSTOM POKÉMON CREATOR
                </p>
              </div>
            </div>
          </div>
          <div
            className="fr-panel-dark"
            style={{
              padding: "8px 16px",
              display: "flex",
              alignItems: "center",
              gap: 10,
            }}
          >
            <span
              style={{
                display: "inline-block",
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: "#58c840",
                boxShadow: "0 0 6px #58c840",
                flexShrink: 0,
              }}
            />
            <span className="fr-small" style={{ color: "var(--fr-cream)" }}>
              Powered by gpt-image-2
            </span>
          </div>
        </div>

        {/* ── Main two-column layout ── */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 24,
            alignItems: "start",
          }}
          className="main-grid"
        >
          {/* LEFT — Input panel */}
          <div>
            <div
              className="fr-panel fr-appear fr-appear-2"
              style={{ padding: "24px 24px 28px" }}
            >
              {/* Panel header mimicking FireRed screen title */}
              <div
                className="fr-panel-dark"
                style={{ padding: "10px 16px", marginBottom: 24 }}
              >
                <span className="fr-label" style={{ color: "var(--fr-cream)" }}>
                  ▶ WHAT POKÉMON SHALL I CREATE?
                </span>
              </div>

              <SpriteGeneratorForm
                onSubmit={handleGenerate}
                isLoading={isLoading}
              />
            </div>

            {/* Status dialogs appear below the form */}
            {state.status === "loading" && (
              <div style={{ marginTop: 20 }}>
                <LoadingDialog />
              </div>
            )}
            {state.status === "error" && (
              <div style={{ marginTop: 20 }}>
                <ErrorDialog
                  message={state.message}
                  onRetry={() => dispatch({ type: "RESET" })}
                />
              </div>
            )}
          </div>

          {/* RIGHT — Results panel */}
          <div>
            {state.status === "success" ? (
              <div
                style={{ display: "flex", flexDirection: "column", gap: 20 }}
              >
                <SpritePreview spriteBase64={state.sprite} />
                <IconPreview iconBase64={state.icon} />
                <div style={{ textAlign: "right" }}>
                  <button
                    className="fr-btn"
                    style={{ fontSize: "var(--fs-xs)" }}
                    onClick={() => dispatch({ type: "RESET" })}
                  >
                    ▶ Generate Another
                  </button>
                </div>
              </div>
            ) : (
              <div
                className="fr-panel fr-appear fr-appear-3"
                style={{
                  minHeight: 400,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  padding: 32,
                  gap: 20,
                }}
              >
                {/* Placeholder — styled like a blank Pokédex entry */}
                <div
                  style={{
                    width: 160,
                    height: 160,
                    border: "4px solid var(--fr-border)",
                    boxShadow:
                      "inset 3px 3px 0 var(--fr-white), inset -3px -3px 0 var(--fr-shadow)",
                    background: "var(--fr-white)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <span className="fr-heading fr-muted">?</span>
                </div>

                <div style={{ textAlign: "center" }}>
                  <p className="fr-label fr-muted">No. ???</p>
                  <p className="fr-small fr-muted" style={{ marginTop: 6 }}>
                    Describe your Pokémon
                    <br />
                    and press GENERATE
                  </p>
                </div>

                <div
                  className="fr-panel-dark"
                  style={{
                    padding: "10px 20px",
                    width: "100%",
                    textAlign: "center",
                  }}
                >
                  <span
                    className="fr-small"
                    style={{ color: "var(--fr-gray)" }}
                  >
                    Powered by OpenAI gpt-image-2
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Footer ── */}
        <div style={{ marginTop: 32, textAlign: "center" }}>
          <p className="fr-tiny fr-muted" style={{ letterSpacing: "0.12em" }}>
            AI ENGINEER HACKATHON · SINGAPORE · MAY 9 2026 · TEAM POKÉLIVE
          </p>
        </div>
      </div>

      {/* Responsive grid override */}
      <style>{`
        @media (max-width: 768px) {
          .main-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
}
