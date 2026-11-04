"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { colors, font, radius, shadow, zIndex } from "./theme";
import { Icon } from "./Icon";

type ToastType = "success" | "error" | "info" | "warning";

type ToastItem = { id: number; message: string; type: ToastType };
type ToastContextType = { toast: (message: string, type?: ToastType) => void };

const ToastContext = createContext<ToastContextType | null>(null);
let nextId = 0;

const toneMap: Record<ToastType, { bg: string; color: string; border: string }> = {
  success: { bg: colors.successSoft, color: colors.successText, border: "#bbf7d0" },
  error:   { bg: colors.dangerSoft,  color: colors.dangerText,  border: "#fecaca" },
  info:    { bg: colors.infoSoft,    color: colors.infoText,    border: "#bae6fd" },
  warning: { bg: colors.warningSoft, color: colors.warningText, border: "#fde68a" },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const toast = useCallback((message: string, type: ToastType = "info") => {
    const id = ++nextId;
    setToasts((p) => [...p, { id, message, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 4000);
  }, []);

  const dismiss = (id: number) => setToasts((p) => p.filter((t) => t.id !== id));

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {toasts.length > 0 && (
        <div
          aria-live="polite"
          style={{
            position: "fixed", top: 16, right: 16,
            display: "flex", flexDirection: "column", gap: 8,
            zIndex: zIndex.toast, maxWidth: 400,
          }}
        >
          {toasts.map((t) => {
            const tone = toneMap[t.type];
            return (
              <div
                key={t.id}
                role="alert"
                style={{
                  background: tone.bg, color: tone.color,
                  border: `1px solid ${tone.border}`,
                  borderRadius: radius.lg, padding: "10px 14px",
                  boxShadow: shadow.md,
                  display: "flex", alignItems: "center", gap: 10,
                  fontSize: font.size.base, fontWeight: font.weight.medium,
                }}
              >
                <span style={{ flex: 1 }}>{t.message}</span>
                <button
                  onClick={() => dismiss(t.id)}
                  aria-label="Dismiss"
                  style={{
                    background: "transparent", border: "none", cursor: "pointer",
                    padding: 2, display: "inline-flex",
                  }}
                >
                  <Icon.x color={tone.color} size={16} />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextType {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
