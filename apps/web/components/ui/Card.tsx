"use client";

import type { CSSProperties, KeyboardEvent, ReactNode } from "react";
import { colors, radius, shadow } from "./theme";

type Padding = "none" | "sm" | "md" | "lg";
type Tone = "default" | "muted" | "brand" | "success" | "warning" | "danger";

type CardProps = {
  children: ReactNode;
  padding?: Padding;
  tone?: Tone;
  interactive?: boolean;
  onClick?: () => void;
  style?: CSSProperties;
  className?: string;
};

const paddings: Record<Padding, string> = {
  none: "0",
  sm:   "12px",
  md:   "16px",
  lg:   "24px",
};

const tones: Record<Tone, { bg: string; border: string }> = {
  default: { bg: colors.surface,      border: colors.border },
  muted:   { bg: colors.surfaceMuted, border: colors.border },
  brand:   { bg: colors.primarySoft,  border: "#c7dbff" },
  success: { bg: colors.successSoft,  border: "#bbf7d0" },
  warning: { bg: colors.warningSoft,  border: "#fde68a" },
  danger:  { bg: colors.dangerSoft,   border: "#fecaca" },
};

export function Card({
  children,
  padding = "md",
  tone = "default",
  interactive,
  onClick,
  style,
  className,
}: CardProps) {
  const t = tones[tone];
  const clickable = interactive || !!onClick;

  const handleKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (!onClick) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      className={className}
      onClick={onClick}
      onKeyDown={clickable ? handleKey : undefined}
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
      style={{
        background: t.bg,
        border: `1px solid ${t.border}`,
        borderRadius: radius.xl,
        padding: paddings[padding],
        boxShadow: shadow.sm,
        cursor: clickable ? "pointer" : undefined,
        transition: "transform 0.15s, box-shadow 0.15s, border-color 0.15s",
        ...style,
      }}
    >
      {children}
    </div>
  );
}
