"use client";

import type { CSSProperties, TextareaHTMLAttributes } from "react";
import { useId } from "react";
import { colors, font, radius } from "./theme";

type TextareaProps = {
  label?: string;
  error?: string;
  helperText?: string;
  containerStyle?: CSSProperties;
} & TextareaHTMLAttributes<HTMLTextAreaElement>;

export function Textarea({
  label,
  error,
  helperText,
  id,
  containerStyle,
  style,
  rows = 4,
  ...rest
}: TextareaProps) {
  const auto = useId();
  const textareaId = id ?? `ta-${auto}`;
  const borderColor = error ? colors.danger : colors.borderStrong;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, ...containerStyle }}>
      {label && (
        <label
          htmlFor={textareaId}
          style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.textMuted }}
        >
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        rows={rows}
        {...rest}
        style={{
          border: `1px solid ${borderColor}`,
          borderRadius: radius.lg,
          padding: "10px 14px",
          fontSize: font.size.base,
          fontFamily: font.family,
          color: colors.text,
          background: colors.surface,
          resize: "vertical",
          outline: "none",
          minHeight: 96,
          ...style,
        }}
      />
      {error ? (
        <span style={{ fontSize: font.size.sm, color: colors.danger }}>{error}</span>
      ) : helperText ? (
        <span style={{ fontSize: font.size.sm, color: colors.textSubtle }}>{helperText}</span>
      ) : null}
    </div>
  );
}
