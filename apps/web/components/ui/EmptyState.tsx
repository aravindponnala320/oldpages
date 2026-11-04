import type { ReactNode } from "react";
import { colors, font, radius } from "./theme";

type Props = {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
};

export function EmptyState({ icon, title, description, action }: Props) {
  return (
    <div
      style={{
        background: colors.surface,
        border: `2px dashed ${colors.borderStrong}`,
        borderRadius: radius.xl,
        padding: "48px 24px",
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
      }}
    >
      {icon && (
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            background: colors.primarySoft,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: colors.primary,
          }}
        >
          {icon}
        </div>
      )}
      <h3 style={{ margin: 0, fontSize: font.size.lg, fontWeight: font.weight.bold, color: colors.text }}>{title}</h3>
      {description && (
        <p style={{ margin: 0, fontSize: font.size.base, color: colors.textSubtle, maxWidth: 420, lineHeight: font.lineHeight.snug }}>
          {description}
        </p>
      )}
      {action && <div style={{ marginTop: 4 }}>{action}</div>}
    </div>
  );
}
