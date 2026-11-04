"use client";

import Link from "next/link";
import type { ButtonHTMLAttributes, CSSProperties, ReactNode } from "react";
import { colors, font, radius, shadow } from "./theme";
import { Spinner } from "./Spinner";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "success";
type Size = "sm" | "md" | "lg";

type CommonProps = {
  variant?: Variant;
  size?: Size;
  fullWidth?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  loading?: boolean;
  children?: ReactNode;
  style?: CSSProperties;
  className?: string;
};

const sizes: Record<Size, CSSProperties> = {
  sm: { padding: "7px 14px", fontSize: font.size.sm, borderRadius: radius.md, minHeight: 32 },
  md: { padding: "10px 18px", fontSize: font.size.base, borderRadius: radius.lg, minHeight: 40 },
  lg: { padding: "13px 22px", fontSize: font.size.md, borderRadius: radius.lg, minHeight: 46 },
};

const variants: Record<Variant, CSSProperties> = {
  primary: {
    background: colors.primary,
    color: colors.textInverse,
    border: "1px solid transparent",
    boxShadow: shadow.sm,
  },
  secondary: {
    background: colors.surface,
    color: colors.text,
    border: `1px solid ${colors.borderStrong}`,
  },
  ghost: {
    background: "transparent",
    color: colors.textMuted,
    border: "1px solid transparent",
  },
  danger: {
    background: colors.danger,
    color: colors.textInverse,
    border: "1px solid transparent",
  },
  success: {
    background: colors.success,
    color: colors.textInverse,
    border: "1px solid transparent",
  },
};

const base: CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 8,
  fontFamily: font.family,
  fontWeight: font.weight.semibold,
  cursor: "pointer",
  textDecoration: "none",
  lineHeight: 1,
  whiteSpace: "nowrap",
  transition: "background 0.15s, border-color 0.15s, box-shadow 0.15s, opacity 0.15s",
};

export function buttonStyle({
  variant = "primary",
  size = "md",
  fullWidth,
  disabled,
  extra,
}: {
  variant?: Variant;
  size?: Size;
  fullWidth?: boolean;
  disabled?: boolean;
  extra?: CSSProperties;
} = {}): CSSProperties {
  return {
    ...base,
    ...sizes[size],
    ...variants[variant],
    width: fullWidth ? "100%" : undefined,
    opacity: disabled ? 0.55 : 1,
    pointerEvents: disabled ? "none" : undefined,
    ...extra,
  };
}

type ButtonProps = CommonProps &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, keyof CommonProps>;

export function Button({
  variant = "primary",
  size = "md",
  fullWidth,
  leftIcon,
  rightIcon,
  loading,
  children,
  style,
  disabled,
  ...rest
}: ButtonProps) {
  const isDisabled = !!disabled || !!loading;
  return (
    <button
      {...rest}
      disabled={isDisabled}
      style={buttonStyle({ variant, size, fullWidth, disabled: isDisabled, extra: style })}
    >
      {loading ? <Spinner size="sm" /> : leftIcon}
      {children}
      {rightIcon}
    </button>
  );
}

type LinkButtonProps = CommonProps & { href: string; target?: string; rel?: string };

export function LinkButton({
  href,
  target,
  rel,
  variant = "primary",
  size = "md",
  fullWidth,
  leftIcon,
  rightIcon,
  children,
  style,
}: LinkButtonProps) {
  return (
    <Link
      href={href}
      target={target}
      rel={rel}
      style={buttonStyle({ variant, size, fullWidth, extra: style })}
    >
      {leftIcon}
      {children}
      {rightIcon}
    </Link>
  );
}
