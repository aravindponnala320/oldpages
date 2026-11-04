"use client";

import type { CSSProperties, InputHTMLAttributes, ReactNode } from "react";
import { useId } from "react";
import { colors, font, radius } from "./theme";

type InputSize = "sm" | "md" | "lg";

type InputProps = {
  label?: string;
  helperText?: string;
  error?: string;
  prefix?: ReactNode;
  suffix?: ReactNode;
  containerStyle?: CSSProperties;
  inputSize?: InputSize;
} & Omit<InputHTMLAttributes<HTMLInputElement>, "size" | "prefix" | "suffix">;

const heights: Record<InputSize, number> = { sm: 34, md: 40, lg: 46 };
const pads: Record<InputSize, string> = {
  sm: "0 12px",
  md: "0 14px",
  lg: "0 16px",
};

export function Input({
  label,
  helperText,
  error,
  prefix,
  suffix,
  id,
  containerStyle,
  inputSize = "md",
  style,
  ...rest
}: InputProps) {
  const auto = useId();
  const inputId = id ?? `in-${auto}`;
  const borderColor = error ? colors.danger : colors.borderStrong;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, ...containerStyle }}>
      {label && (
        <label
          htmlFor={inputId}
          style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.textMuted }}
        >
          {label}
        </label>
      )}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: colors.surface,
          border: `1px solid ${borderColor}`,
          borderRadius: radius.lg,
          padding: pads[inputSize],
          height: heights[inputSize],
          transition: "border-color 0.15s, box-shadow 0.15s",
        }}
      >
        {prefix && (
          <span style={{ display: "flex", alignItems: "center", color: colors.textFaint }}>{prefix}</span>
        )}
        <input
          id={inputId}
          {...rest}
          style={{
            flex: 1,
            border: "none",
            outline: "none",
            background: "transparent",
            fontSize: font.size.base,
            fontFamily: font.family,
            color: colors.text,
            minWidth: 0,
            ...style,
          }}
        />
        {suffix && (
          <span style={{ display: "flex", alignItems: "center", color: colors.textFaint }}>{suffix}</span>
        )}
      </div>
      {error ? (
        <span style={{ fontSize: font.size.sm, color: colors.danger }}>{error}</span>
      ) : helperText ? (
        <span style={{ fontSize: font.size.sm, color: colors.textSubtle }}>{helperText}</span>
      ) : null}
    </div>
  );
}
