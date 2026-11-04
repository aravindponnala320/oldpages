"use client";

import type { ReactNode } from "react";
import { colors, font, radius } from "./theme";

type Props = {
  children: ReactNode;
  active?: boolean;
  onClick?: () => void;
  leftIcon?: ReactNode;
};

export function Chip({ children, active, onClick, leftIcon }: Props) {
  return (
    <button
      onClick={onClick}
      type="button"
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "6px 12px",
        borderRadius: radius.pill,
        border: `1px solid ${active ? colors.primary : colors.borderStrong}`,
        background: active ? colors.primary : colors.surface,
        color: active ? colors.textInverse : colors.textMuted,
        fontSize: font.size.sm,
        fontWeight: font.weight.medium,
        cursor: onClick ? "pointer" : "default",
        transition: "background 0.15s, border-color 0.15s, color 0.15s",
        whiteSpace: "nowrap",
      }}
    >
      {leftIcon}
      {children}
    </button>
  );
}
