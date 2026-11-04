"use client";

import type { CSSProperties, SelectHTMLAttributes } from "react";
import { useId } from "react";
import { colors, font, radius } from "./theme";

type SelectOption = { value: string; label: string };

type SelectProps = {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  containerStyle?: CSSProperties;
} & SelectHTMLAttributes<HTMLSelectElement>;

export function Select({
  label,
  error,
  helperText,
  options,
  id,
  containerStyle,
  style,
  ...rest
}: SelectProps) {
  const auto = useId();
  const selectId = id ?? `sel-${auto}`;
  const borderColor = error ? colors.danger : colors.borderStrong;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, ...containerStyle }}>
      {label && (
        <label
          htmlFor={selectId}
          style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.textMuted }}
        >
          {label}
        </label>
      )}
      <select
        id={selectId}
        {...rest}
        style={{
          appearance: "none",
          WebkitAppearance: "none",
          border: `1px solid ${borderColor}`,
          borderRadius: radius.lg,
          padding: "0 36px 0 14px",
          height: 40,
          fontSize: font.size.base,
          fontFamily: font.family,
          color: colors.text,
          background: `${colors.surface} url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E") no-repeat right 12px center / 14px 14px`,
          outline: "none",
          ...style,
        }}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error ? (
        <span style={{ fontSize: font.size.sm, color: colors.danger }}>{error}</span>
      ) : helperText ? (
        <span style={{ fontSize: font.size.sm, color: colors.textSubtle }}>{helperText}</span>
      ) : null}
    </div>
  );
}
