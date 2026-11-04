import type { CSSProperties, ReactNode } from "react";
import { colors, font, radius } from "./theme";

type Variant =
  | "default"
  | "brand"
  | "success"
  | "warning"
  | "danger"
  | "error" // alias for danger, kept for pre-migration callers
  | "info"
  | "purple"
  | "neutral";

type Size = "sm" | "md";

type Props = {
  children?: ReactNode;
  label?: string;
  variant?: Variant;
  size?: Size;
  style?: CSSProperties;
};

const styles: Record<Variant, { bg: string; color: string }> = {
  default: { bg: colors.divider,      color: colors.textMuted },
  brand:   { bg: colors.primarySoft,  color: colors.primaryStrong },
  success: { bg: colors.successSoft,  color: colors.successText },
  warning: { bg: colors.warningSoft,  color: colors.warningText },
  danger:  { bg: colors.dangerSoft,   color: colors.dangerText },
  error:   { bg: colors.dangerSoft,   color: colors.dangerText },
  info:    { bg: colors.infoSoft,     color: colors.infoText },
  purple:  { bg: "#ede9fe",           color: "#5b21b6" },
  neutral: { bg: colors.surfaceMuted, color: colors.textSubtle },
};

const sizes: Record<Size, CSSProperties> = {
  sm: { fontSize: font.size.xs, padding: "3px 8px" },
  md: { fontSize: font.size.sm, padding: "4px 10px" },
};

export function Badge({ children, label, variant = "default", size = "sm", style }: Props) {
  const s = styles[variant];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        background: s.bg,
        color: s.color,
        borderRadius: radius.sm,
        fontWeight: font.weight.semibold,
        lineHeight: 1.2,
        ...sizes[size],
        ...style,
      }}
    >
      {children ?? label}
    </span>
  );
}

/** Maps a raw listing.condition string to a Badge. */
export function ConditionBadge({ condition, size = "sm" }: { condition: string | null | undefined; size?: Size }) {
  if (!condition) return null;
  const map: Record<string, { label: string; variant: Variant }> = {
    new_sealed: { label: "New",        variant: "success" },
    like_new:   { label: "Like New",   variant: "info" },
    excellent:  { label: "Excellent",  variant: "purple" },
    very_good:  { label: "Very Good",  variant: "brand" },
    good:       { label: "Good",       variant: "success" },
    acceptable: { label: "Acceptable", variant: "warning" },
    poor:       { label: "Poor",       variant: "danger" },
  };
  const cfg = map[condition] ?? { label: condition, variant: "neutral" as Variant };
  return <Badge label={cfg.label} variant={cfg.variant} size={size} />;
}
