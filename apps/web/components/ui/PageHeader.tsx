import type { ReactNode } from "react";
import { colors, font } from "./theme";

type Props = {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  icon?: ReactNode;
  actions?: ReactNode;
};

export function PageHeader({ title, subtitle, eyebrow, icon, actions }: Props) {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        gap: 16,
        marginBottom: 20,
      }}
    >
      <div style={{ minWidth: 0, flex: 1 }}>
        {eyebrow && (
          <div
            style={{
              color: colors.primary,
              fontSize: font.size.xs,
              fontWeight: font.weight.bold,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              marginBottom: 4,
            }}
          >
            {eyebrow}
          </div>
        )}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {icon}
          <h1
            style={{
              margin: 0,
              fontSize: font.size["2xl"],
              fontWeight: font.weight.bold,
              color: colors.text,
              letterSpacing: "-0.02em",
              lineHeight: 1.2,
            }}
          >
            {title}
          </h1>
        </div>
        {subtitle && (
          <p
            style={{
              margin: "4px 0 0",
              fontSize: font.size.base,
              color: colors.textSubtle,
              lineHeight: font.lineHeight.snug,
            }}
          >
            {subtitle}
          </p>
        )}
      </div>
      {actions && <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>{actions}</div>}
    </header>
  );
}
