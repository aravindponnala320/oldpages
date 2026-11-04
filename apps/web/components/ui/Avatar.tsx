import type { CSSProperties } from "react";

type Size = "xs" | "sm" | "md" | "lg" | "xl";
const dims: Record<Size, number> = { xs: 24, sm: 32, md: 40, lg: 56, xl: 72 };
const fontSizes: Record<Size, number> = { xs: 10, sm: 12, md: 14, lg: 18, xl: 22 };

const PALETTE = ["#2563eb", "#0891b2", "#a15c16", "#7c3aed", "#b42318", "#0f766e", "#1d4ed8", "#c026d3"];

function colorFromName(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return PALETTE[Math.abs(hash) % PALETTE.length] ?? PALETTE[0]!;
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0]!.slice(0, 2).toUpperCase();
  const first = parts[0]!;
  const last = parts[parts.length - 1]!;
  return `${first[0] ?? ""}${last[0] ?? ""}`.toUpperCase();
}

export function Avatar({
  name,
  src,
  size = "md",
  style,
}: {
  name: string;
  src?: string | null;
  size?: Size;
  style?: CSSProperties;
}) {
  const s = dims[size];
  return (
    <span
      aria-label={name}
      style={{
        width: s,
        height: s,
        borderRadius: "50%",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
        color: "#fff",
        fontSize: fontSizes[size],
        fontWeight: 700,
        background: src ? "#e5e7eb" : colorFromName(name),
        flexShrink: 0,
        ...style,
      }}
    >
      {src ? (
        <img src={src} alt={name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : (
        getInitials(name)
      )}
    </span>
  );
}
