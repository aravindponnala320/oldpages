"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { colors, font, radius, shadow, zIndex } from "./theme";
import { Icon } from "./Icon";

type ModalProps = {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  footer?: ReactNode;
};

const widths = { sm: 400, md: 560, lg: 720, xl: 960 };

export function Modal({ isOpen, onClose, title, children, size = "md", footer }: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const content = (
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      role="dialog"
      aria-modal
      aria-labelledby={title ? "op-modal-title" : undefined}
      style={{
        position: "fixed", inset: 0, zIndex: zIndex.modal,
        background: "rgba(15, 23, 42, 0.55)",
        backdropFilter: "blur(4px)",
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: 16,
      }}
    >
      <div
        ref={dialogRef}
        style={{
          background: colors.surface,
          borderRadius: radius.xl,
          boxShadow: shadow.lg,
          width: "100%",
          maxWidth: widths[size],
          maxHeight: "90vh",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {title && (
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "16px 20px", borderBottom: `1px solid ${colors.border}`,
          }}>
            <h2 id="op-modal-title" style={{ margin: 0, fontSize: font.size.lg, fontWeight: font.weight.bold, color: colors.text }}>
              {title}
            </h2>
            <button
              onClick={onClose}
              aria-label="Close"
              style={{
                background: "transparent", border: "none", cursor: "pointer",
                padding: 6, borderRadius: radius.md,
                display: "inline-flex", alignItems: "center", justifyContent: "center",
              }}
            >
              <Icon.x />
            </button>
          </div>
        )}
        <div style={{ padding: 20, overflowY: "auto", flex: 1 }}>{children}</div>
        {footer && (
          <div style={{
            padding: "12px 20px", borderTop: `1px solid ${colors.border}`,
            display: "flex", justifyContent: "flex-end", gap: 8,
          }}>
            {footer}
          </div>
        )}
      </div>
    </div>
  );

  if (typeof document === "undefined") return null;
  return createPortal(content, document.body);
}
