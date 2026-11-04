"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { GeoSearchItem, LocationPayload } from "@oldpages/api-client";
import { apiClient } from "../lib/api";
import { useLocation } from "../contexts/LocationContext";

function pinNoteStyle(color: string): React.CSSProperties {
  return {
    marginTop: 6,
    fontSize: "0.72rem",
    color,
  };
}

function summarise(loc: LocationPayload | null): string {
  if (!loc) return "Set location";
  if (loc.city && loc.country_code) return `${loc.city}, ${loc.country_code}`;
  if (loc.city) return loc.city;
  if (loc.display_name) return loc.display_name.split(",")[0] ?? loc.display_name;
  return `${loc.latitude.toFixed(2)}, ${loc.longitude.toFixed(2)}`;
}

const COUNTRY_OPTIONS: { code: string; label: string }[] = [
  { code: "IN", label: "India" },
  { code: "US", label: "United States" },
  { code: "GB", label: "United Kingdom" },
  { code: "CA", label: "Canada" },
  { code: "AU", label: "Australia" },
  { code: "DE", label: "Germany" },
  { code: "FR", label: "France" },
  { code: "SG", label: "Singapore" },
];

export function LocationSwitcher() {
  const { active, isReady, setActive, requestBrowserLocation } = useLocation();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GeoSearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [radius, setRadius] = useState<number>(active?.radius_km ?? 25);
  const [pin, setPin] = useState("");
  const [pinCountry, setPinCountry] = useState(active?.country_code || "IN");
  const [pinLookup, setPinLookup] = useState<
    | { status: "idle" }
    | { status: "loading" }
    | { status: "found"; payload: LocationPayload }
    | { status: "notfound" }
    | { status: "error" }
  >({ status: "idle" });
  const debounce = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setRadius(active?.radius_km ?? 25);
  }, [active?.latitude, active?.longitude, active?.radius_km]);

  useEffect(() => {
    if (!open) return;
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    if (debounce.current) clearTimeout(debounce.current);
    debounce.current = setTimeout(async () => {
      setLoading(true);
      try {
        const resp = await apiClient.searchPlaces(query, { limit: 8 });
        setResults(resp.items);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => {
      if (debounce.current) clearTimeout(debounce.current);
    };
  }, [query, open]);

  async function pick(item: GeoSearchItem) {
    await setActive(
      {
        latitude: item.latitude,
        longitude: item.longitude,
        city: item.city ?? null,
        state: item.state ?? null,
        country: item.country ?? null,
        country_code: item.country_code ?? null,
        postal_code: item.postal_code ?? null,
        display_name: item.display_name,
        radius_km: radius,
      },
      false,
    );
    setOpen(false);
    setQuery("");
    router.refresh();
  }

  async function useMyLocation() {
    const loc = await requestBrowserLocation();
    if (loc) {
      setOpen(false);
      router.refresh();
    }
  }

  async function submitPincode(e?: React.FormEvent) {
    e?.preventDefault();
    const cleaned = pin.trim();
    if (!cleaned) return;
    setPinLookup({ status: "loading" });
    try {
      const payload = await apiClient.lookupPincode(cleaned, pinCountry);
      if (!payload) {
        setPinLookup({ status: "notfound" });
        return;
      }
      setPinLookup({ status: "found", payload });
    } catch {
      setPinLookup({ status: "error" });
    }
  }

  async function applyPincodeResult() {
    if (pinLookup.status !== "found") return;
    const merged: LocationPayload = {
      ...pinLookup.payload,
      radius_km: radius,
    };
    await setActive(merged, false);
    setOpen(false);
    setPin("");
    setPinLookup({ status: "idle" });
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
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.375rem",
          padding: "0.4rem 0.625rem",
          background: "#f7f7f3",
          border: "1.5px solid #e5e7eb",
          borderRadius: 8,
          fontSize: "0.8125rem",
          fontWeight: 600,
          color: "#1f2933",
          cursor: "pointer",
          whiteSpace: "nowrap",
          maxWidth: 180,
          overflow: "hidden",
          textOverflow: "ellipsis",
        }}
        title="Change location"
      >
        <span aria-hidden style={{ fontSize: "0.9rem" }}>📍</span>
        <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
          {isReady ? summarise(active) : "Locating..."}
        </span>
      </button>

      {open && (
        <>
          <div
            style={{ position: "fixed", inset: 0, zIndex: 49 }}
            onClick={() => setOpen(false)}
          />
          <div
            style={{
              position: "absolute",
              top: "calc(100% + 8px)",
              left: 0,
              width: 320,
              background: "white",
              border: "1px solid #e5e7eb",
              borderRadius: 10,
              boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
              padding: "0.75rem",
              zIndex: 50,
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "0.5rem",
              }}
            >
              <span style={{ fontWeight: 700, fontSize: "0.8125rem", color: "#1f2933" }}>
                Your location
              </span>
              <button
                type="button"
                onClick={useMyLocation}
                style={{
                  background: "none",
                  border: "none",
                  color: "#256f5b",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Use my location
              </button>
            </div>

            {/* PIN / ZIP code — quick fill */}
            <form onSubmit={submitPincode} style={{ marginBottom: "0.625rem" }}>
              <div style={{ display: "flex", gap: 6 }}>
                <select
                  value={pinCountry}
                  onChange={(e) => {
                    setPinCountry(e.target.value);
                    setPinLookup({ status: "idle" });
                  }}
                  style={{
                    padding: "0.5rem 0.375rem",
                    border: "1.5px solid #e5e7eb",
                    borderRadius: 8,
                    fontSize: "0.75rem",
                    background: "#fff",
                    color: "#1f2933",
                    outline: "none",
                    flex: "0 0 68px",
                  }}
                  title="Country"
                >
                  {COUNTRY_OPTIONS.map((c) => (
                    <option key={c.code} value={c.code}>
                      {c.code}
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="PIN / ZIP"
                  value={pin}
                  onChange={(e) => {
                    setPin(e.target.value);
                    setPinLookup({ status: "idle" });
                  }}
                  onBlur={() => {
                    if (pin.trim().length >= 3) submitPincode();
                  }}
                  style={{
                    flex: 1,
                    padding: "0.5rem 0.625rem",
                    border: "1.5px solid #e5e7eb",
                    borderRadius: 8,
                    fontSize: "0.8125rem",
                    outline: "none",
                  }}
                />
                <button
                  type="submit"
                  style={{
                    padding: "0.5rem 0.75rem",
                    background: "#256f5b",
                    color: "white",
                    border: "none",
                    borderRadius: 8,
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Find
                </button>
              </div>

              {pinLookup.status === "loading" && (
                <div style={pinNoteStyle("#9ca3af")}>Looking up…</div>
              )}
              {pinLookup.status === "notfound" && (
                <div style={pinNoteStyle("#b45309")}>No match for that code.</div>
              )}
              {pinLookup.status === "error" && (
                <div style={pinNoteStyle("#b91c1c")}>Lookup failed — try again.</div>
              )}
              {pinLookup.status === "found" && (
                <div
                  style={{
                    marginTop: 6,
                    padding: "0.5rem 0.625rem",
                    background: "#f0faf7",
                    border: "1px solid #b8e2d4",
                    borderRadius: 8,
                    fontSize: "0.75rem",
                    color: "#1f2933",
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>
                    {pinLookup.payload.city}
                    {pinLookup.payload.state && `, ${pinLookup.payload.state}`}
                    {pinLookup.payload.country && ` — ${pinLookup.payload.country}`}
                  </div>
                  <button
                    type="button"
                    onClick={applyPincodeResult}
                    style={{
                      padding: "0.25rem 0.625rem",
                      background: "#256f5b",
                      color: "white",
                      border: "none",
                      borderRadius: 6,
                      fontSize: "0.7rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Use this location
                  </button>
                </div>
              )}
            </form>

            <div
              style={{
                fontSize: "0.7rem",
                color: "#9ca3af",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                fontWeight: 700,
                margin: "0.375rem 0 0.375rem",
              }}
            >
              Or search by name
            </div>

            <input
              type="search"
              placeholder="City, neighborhood or place"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{
                width: "100%",
                padding: "0.5rem 0.625rem",
                border: "1.5px solid #e5e7eb",
                borderRadius: 8,
                fontSize: "0.8125rem",
                outline: "none",
                marginBottom: "0.5rem",
              }}
            />

            {loading && (
              <div style={{ padding: "0.5rem", fontSize: "0.75rem", color: "#9ca3af" }}>
                Searching...
              </div>
            )}

            {!loading && results.length > 0 && (
              <ul
                style={{
                  listStyle: "none",
                  margin: 0,
                  padding: 0,
                  maxHeight: 240,
                  overflowY: "auto",
                }}
              >
                {results.map((item, idx) => (
                  <li key={`${item.latitude}-${item.longitude}-${idx}`}>
                    <button
                      type="button"
                      onClick={() => pick(item)}
                      style={{
                        width: "100%",
                        textAlign: "left",
                        padding: "0.5rem 0.625rem",
                        background: "none",
                        border: "none",
                        borderRadius: 6,
                        fontSize: "0.8125rem",
                        color: "#1f2933",
                        cursor: "pointer",
                      }}
                      onMouseEnter={(e) =>
                        ((e.currentTarget as HTMLButtonElement).style.background = "#f9fafb")
                      }
                      onMouseLeave={(e) =>
                        ((e.currentTarget as HTMLButtonElement).style.background = "transparent")
                      }
                    >
                      {item.display_name}
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {active && (
              <div style={{ marginTop: "0.75rem", borderTop: "1px solid #f3f4f6", paddingTop: "0.625rem" }}>
                <label
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "0.75rem",
                    color: "#5c6670",
                    marginBottom: "0.25rem",
                  }}
                >
                  <span>Search radius</span>
                  <span style={{ fontWeight: 600 }}>{radius} km</span>
                </label>
                <input
                  type="range"
                  min={1}
                  max={200}
                  step={1}
                  value={radius}
                  onChange={(e) => setRadius(Number(e.target.value))}
                  onMouseUp={(e) => applyRadius(Number((e.target as HTMLInputElement).value))}
                  onTouchEnd={(e) => applyRadius(Number((e.target as HTMLInputElement).value))}
                  style={{ width: "100%" }}
                />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
