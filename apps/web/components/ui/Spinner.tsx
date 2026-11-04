import { colors } from "./theme";

type Size = "xs" | "sm" | "md" | "lg";
const px: Record<Size, number> = { xs: 12, sm: 14, md: 20, lg: 32 };

export function Spinner({ size = "md", color = colors.primary }: { size?: Size; color?: string }) {
  const s = px[size];
  const border = Math.max(2, Math.round(s / 8));
  return (
    <span
      role="status"
      aria-label="Loading"
      style={{
        display: "inline-block",
        width: s,
        height: s,
        border: `${border}px solid rgba(37,99,235,0.18)`,
        borderTopColor: color,
        borderRadius: "50%",
        animation: "op-spin 0.7s linear infinite",
        flexShrink: 0,
      }}
    />
  );
}
