import type { ReactNode } from "react";
import { colors, font, radius, shadow } from "./theme";

type Props = {
  title?: string;
  subtitle?: string;
  eyebrow?: string;
  icon?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  padded?: boolean;
};

/**
 * Section: a self-contained card panel with an optional title row.
 * Use for grouping related content on a page (e.g. "Nearby Books", "Recent Orders").
 */
export function Section({ title, subtitle, eyebrow, icon, actions, children, padded = true }: Props) {
  const hasHeader = !!(title || eyebrow || actions);
  return (
    <section
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.xl,
        boxShadow: shadow.sm,
        overflow: "hidden",
      }}
    >
      {hasHeader && (
        <header
          style={{
            padding: padded ? "18px 20px 12px" : "16px 16px 12px",
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: 12,
          }}
        >
          <div>
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
            {title && (
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {icon}
                <h2
                  style={{
                    margin: 0,
                    fontSize: font.size.xl,
                    fontWeight: font.weight.bold,
                    color: colors.text,
                    letterSpacing: "-0.01em",
                  }}
                >
                  {title}
                </h2>
              </div>
            )}
            {subtitle && (
              <p
                style={{
                  margin: "4px 0 0",
                  fontSize: font.size.sm,
                  color: colors.textSubtle,
                }}
              >
                {subtitle}
              </p>
            )}
          </div>
          {actions && <div style={{ display: "flex", alignItems: "center", gap: 8 }}>{actions}</div>}
        </header>
      )}
      <div style={{ padding: padded ? "8px 20px 20px" : 0 }}>{children}</div>
    </section>
  );
}
