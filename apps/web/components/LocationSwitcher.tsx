"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { LocationPayload } from "@oldpages/api-client";
import { useLocation } from "../contexts/LocationContext";
import { placeContext, shortLocationLabel } from "../lib/geo";
import { PlacePicker } from "./PlacePicker";

const RADIUS_STEPS = [5, 10, 25, 50, 100, 200];

export function LocationSwitcher() {
  const { active, isReady, setActive } = useLocation();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [radius, setRadius] = useState<number>(active?.radius_km ?? 25);

  useEffect(() => {
    setRadius(active?.radius_km ?? 25);
  }, [active?.latitude, active?.longitude, active?.radius_km]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  async function pick(loc: LocationPayload) {
    await setActive({ ...loc, radius_km: radius }, false);
    setOpen(false);
    router.refresh();
  }

  async function applyRadius(next: number) {
    setRadius(next);
    if (active) {
      await setActive({ ...active, radius_km: next }, false);
      router.refresh();
    }
  }

  return (
    <div style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="dialog"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.375rem",
          padding: "0.4rem 0.625rem",
          minHeight: 40,
          background: "#f7f7f3",
          border: "1.5px solid #e5e7eb",
          borderRadius: 8,
          fontSize: "0.8125rem",
          fontWeight: 600,
          color: "#1f2933",
          cursor: "pointer",
          whiteSpace: "nowrap",
          maxWidth: "min(200px, 42vw)",
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
        title={active?.display_name ?? "Choose your location"}
      >
        <span aria-hidden style={{ fontSize: "0.9rem" }}>
          📍
        </span>
        <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
          {isReady ? shortLocationLabel(active) : "Locating…"}
        </span>
      </button>

      {open && (
        <>
          <div
            style={{ position: "fixed", inset: 0, zIndex: 49 }}
            onClick={() => setOpen(false)}
          />
          <div
            role="dialog"
            aria-label="Choose your location"
            style={{
              position: "absolute",
              top: "calc(100% + 8px)",
              left: 0,
              width: "min(340px, calc(100vw - 32px))",
              maxHeight: "calc(100dvh - 140px)",
              overflowY: "auto",
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: 10,
              boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
              padding: "0.875rem",
              zIndex: 50,
            }}
          >
            <div style={{ marginBottom: "0.75rem" }}>
              <div
                style={{
                  fontWeight: 700,
                  fontSize: "0.875rem",
                  color: "#1f2933",
                }}
              >
                Your location
              </div>
              <div
                style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: 2 }}
              >
                {active
                  ? [shortLocationLabel(active), placeContext(active)]
                      .filter(Boolean)
                      .join(" · ")
                  : "Set it to see books near you first."}
              </div>
            </div>

            <PlacePicker
              onPick={pick}
              defaultCountry={active?.country_code ?? "IN"}
            />

            {active && (
              <div
                style={{
                  marginTop: "0.875rem",
                  borderTop: "1px solid #f3f4f6",
                  paddingTop: "0.75rem",
                }}
              >
                <div
                  id="op-radius-label"
                  style={{
                    fontSize: "0.75rem",
                    color: "#5c6670",
                    marginBottom: "0.375rem",
                  }}
                >
                  Show books within
                </div>
                <div
                  role="radiogroup"
                  aria-labelledby="op-radius-label"
                  style={{ display: "flex", flexWrap: "wrap", gap: 6 }}
                >
                  {RADIUS_STEPS.map((km) => {
                    const selected = radius === km;
                    return (
                      <button
                        key={km}
                        type="button"
                        role="radio"
                        aria-checked={selected}
                        onClick={() => applyRadius(km)}
                        style={{
                          minHeight: 36,
                          padding: "0 12px",
                          borderRadius: 999,
                          border: `1.5px solid ${selected ? "#2563eb" : "#e5e7eb"}`,
                          background: selected ? "#eaf2ff" : "#fff",
                          color: selected ? "#2563eb" : "#374151",
                          fontSize: "0.8125rem",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        {km} km
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
