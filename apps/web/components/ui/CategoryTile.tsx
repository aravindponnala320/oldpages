import Link from "next/link";
import type { ReactNode } from "react";
import { colors, font } from "./theme";

type Props = {
  name: string;
  href: string;
  color: string;
  icon: ReactNode;
};

export function CategoryTile({ name, href, color, icon }: Props) {
  return (
    <Link
      href={href}
      style={{
        textDecoration: "none",
        color: "inherit",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 10,
        padding: "8px 4px",
      }}
    >
      <div
        style={{
          width: 76,
          height: 76,
          borderRadius: "50%",
          background: color,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {icon}
      </div>
      <span style={{ fontSize: font.size.base, fontWeight: font.weight.medium, color: colors.textMuted }}>{name}</span>
    </Link>
  );
}
