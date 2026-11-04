import type { CSSProperties } from "react";
import { colors, radius } from "./theme";

type Props = {
  width?: number | string;
  height?: number | string;
  circle?: boolean;
  style?: CSSProperties;
};

export function Skeleton({ width = "100%", height = 12, circle, style }: Props) {
  return (
    <span
      aria-hidden
      style={{
        display: "inline-block",
        width,
        height,
        borderRadius: circle ? "50%" : radius.sm,
        background: `linear-gradient(90deg, ${colors.divider} 0%, ${colors.borderStrong} 50%, ${colors.divider} 100%)`,
        backgroundSize: "200% 100%",
        animation: "op-shimmer 1.4s ease-in-out infinite",
        ...style,
      }}
    />
  );
}

/** Skeleton for a book card in a grid. */
export function BookCardSkeleton() {
  return (
    <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: 10, overflow: "hidden" }}>
      <Skeleton height={200} style={{ display: "block", borderRadius: 0 }} />
      <div style={{ padding: 12, display: "flex", flexDirection: "column", gap: 8 }}>
        <Skeleton width="80%" height={14} />
        <Skeleton width="55%" height={11} />
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
          <Skeleton width={50} height={14} />
          <Skeleton width={40} height={11} />
        </div>
      </div>
    </div>
  );
}
