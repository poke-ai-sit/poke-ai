"use client";

import { ReactNode } from "react";

type Variant = "default" | "red" | "dialog";

interface FireRedPanelProps {
  children: ReactNode;
  variant?: Variant;
  className?: string;
}

const variantClass: Record<Variant, string> = {
  default: "fr-panel",
  red: "fr-panel-red",
  dialog: "fr-panel-dialog",
};

export default function FireRedPanel({
  children,
  variant = "default",
  className = "",
}: FireRedPanelProps) {
  return (
    <div className={`${variantClass[variant]} ${className}`}>{children}</div>
  );
}
