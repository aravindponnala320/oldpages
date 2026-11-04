"use client";

import type { ReactNode } from "react";
import { colors, font } from "./theme";

export type Tab = { key: string; label: string; count?: number };

type Props = {
  tabs: Tab[];
  value: string;
  onChange: (key: string) => void;
  actions?: ReactNode;
};

export function Tabs({ tabs, value, onChange, actions }: Props) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "space-between",
        borderBottom: `1px solid ${colors.border}`,
        gap: 12,
      }}
    >
      <div style={{ display: "flex", gap: 4, overflowX: "auto" }}>
        {tabs.map((tab) => {
          const active = tab.key === value;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => onChange(tab.key)}
              style={{
                background: "transparent",
                border: "none",
                borderBottom: `2px solid ${active ? colors.primary : "transparent"}`,
                padding: "10px 14px",
                fontSize: font.size.base,
                fontWeight: active ? font.weight.semibold : font.weight.medium,
                color: active ? colors.primary : colors.textSubtle,
                cursor: "pointer",
                whiteSpace: "nowrap",
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              {tab.label}
              {typeof tab.count === "number" && (
                <span
                  style={{
                    background: active ? colors.primarySoft : colors.divider,
                    color: active ? colors.primary : colors.textSubtle,
                    fontSize: font.size.xs,
                    padding: "1px 6px",
                    borderRadius: 999,
                    fontWeight: font.weight.semibold,
                  }}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>
      {actions && <div style={{ paddingBottom: 6 }}>{actions}</div>}
    </div>
  );
}
