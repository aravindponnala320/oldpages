"use client";

import Link from "next/link";
import type { ButtonHTMLAttributes, CSSProperties, ReactNode } from "react";
import { colors, radius } from "./theme";

type Variant = "solid" | "ghost" | "outline";
type Size = "sm" | "md" | "lg";

const dims: Record<Size, number> = { sm: 32, md: 40, lg: 48 };

type CommonProps = {
  icon: ReactNode;
  variant?: Variant;
  size?: Size;
  ariaLabel: string;
  style?: CSSProperties;
};

function stylesFor(variant: Variant): CSSProperties {
  switch (variant) {
    case "solid":
      return { background: colors.primary, color: colors.textInverse, border: "1px solid transparent" };
    case "outline":
      return { background: colors.surface, color: colors.textMuted, border: `1px solid ${colors.borderStrong}` };
    default:
      return { background: "transparent", color: colors.textMuted, border: "1px solid transparent" };
  }
}

type ButtonProps = CommonProps &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children" | keyof CommonProps>;

export function IconButton({
  icon,
  ariaLabel,
  variant = "ghost",
  size = "md",
  style,
  ...rest
}: ButtonProps) {
  const s = dims[size];
  return (
    <button
      aria-label={ariaLabel}
      {...rest}
      style={{
        width: s,
        height: s,
        borderRadius: radius.lg,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        transition: "background 0.15s, border-color 0.15s",
        ...stylesFor(variant),
        ...style,
      }}
    >
      {icon}
    </button>
  );
}

export function IconLinkButton({
  icon,
  ariaLabel,
  href,
  variant = "ghost",
  size = "md",
  style,
}: CommonProps & { href: string }) {
  const s = dims[size];
  return (
    <Link
      href={href}
      aria-label={ariaLabel}
      style={{
        width: s,
        height: s,
        borderRadius: radius.lg,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        textDecoration: "none",
        ...stylesFor(variant),
        ...style,
      }}
    >
      {icon}
    </Link>
  );
}
