"use client";

import { useEffect, useRef, useState } from "react";
import type { GeoSearchItem, LocationPayload } from "@oldpages/api-client";
import { apiClient } from "../lib/api";
import { fromSearchItem, locateBrowser, placeContext } from "../lib/geo";
import { colors, font, radius } from "./ui";

// India first, then countries in alphabetical order. Postcodes elsewhere resolve through OSM.
const COUNTRY_OPTIONS: { code: string; label: string }[] = [
  { code: "IN", label: "India" },
  ...[
    ["AE", "United Arab Emirates"],
    ["AU", "Australia"],
    ["BD", "Bangladesh"],
    ["CA", "Canada"],
    ["DE", "Germany"],
    ["ES", "Spain"],
    ["FR", "France"],
    ["GB", "United Kingdom"],
    ["IE", "Ireland"],
    ["IT", "Italy"],
    ["JP", "Japan"],
    ["LK", "Sri Lanka"],
    ["MY", "Malaysia"],
    ["NL", "Netherlands"],
    ["NP", "Nepal"],
    ["NZ", "New Zealand"],
    ["QA", "Qatar"],
    ["SA", "Saudi Arabia"],
    ["SG", "Singapore"],
    ["US", "United States"],
    ["ZA", "South Africa"],
  ].map(([code, label]) => ({ code: code!, label: label! })),
];

type Status =
  | { kind: "idle" }
  | { kind: "busy"; text: string }
  | { kind: "error"; text: string };

/**
 * Three ways to set a location: the device's position, a PIN/ZIP code, or a
 * search over Indian cities and localities (and places abroad). Every path
 * yields coordinates, which the distance filter needs.
 */
export function PlacePicker({
  onPick,
  defaultCountry = "IN",
  autoFocus = false,
}: {
  onPick: (location: LocationPayload) => void | Promise<void>;
  defaultCountry?: string;
  autoFocus?: boolean;
}) {
  const [gps, setGps] = useState<Status>({ kind: "idle" });
  const [pin, setPin] = useState("");
  const [pinCountry, setPinCountry] = useState(
    COUNTRY_OPTIONS.some((c) => c.code === defaultCountry)
      ? defaultCountry
      : "IN",
  );
  const [pinStatus, setPinStatus] = useState<Status>({ kind: "idle" });
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GeoSearchItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const latestQuery = useRef("");

  useEffect(() => {
    const q = query.trim();
    latestQuery.current = q;
    if (q.length < 2) {
      setResults([]);
      setSearched(false);
      return;
    }
    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const resp = await apiClient.searchPlaces(q, { limit: 8 });
        if (latestQuery.current === q) setResults(resp.items);
      } catch {
        if (latestQuery.current === q) setResults([]);
      } finally {
        if (latestQuery.current === q) {
          setSearching(false);
          setSearched(true);
        }
      }
    }, 350);
    return () => clearTimeout(timer);
  }, [query]);

  async function useDeviceLocation() {
    setGps({ kind: "busy", text: "Finding your location…" });
    const result = await locateBrowser();
    if ("error" in result) {
      setGps({ kind: "error", text: result.error });
      return;
    }
    setGps({ kind: "idle" });
    await onPick(result.location);
  }

  async function findPin() {
    const code = pin.replace(/\s+/g, "");
    if (!code) return;
    if (pinCountry === "IN" && !/^[1-9]\d{5}$/.test(code)) {
      setPinStatus({
        kind: "error",
        text: "Indian PIN codes have 6 digits, e.g. 500032.",
      });
      return;
    }
    setPinStatus({ kind: "busy", text: "Looking up…" });
    try {
      const found = await apiClient.lookupPincode(code, pinCountry);
      if (!found) {
        setPinStatus({
          kind: "error",
          text: "We couldn't find that code. Check it, or search by area name.",
        });
        return;
      }
      setPinStatus({ kind: "idle" });
      setPin("");
      await onPick(found);
    } catch {
      setPinStatus({
        kind: "error",
        text: "Lookup failed. Check your connection and try again.",
      });
    }
  }

  function onSearchKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && results[0]) {
      e.preventDefault();
      void onPick(fromSearchItem(results[0]));
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div>
        <button
          type="button"
          onClick={useDeviceLocation}
          disabled={gps.kind === "busy"}
          style={{
            width: "100%",
            minHeight: 44,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            border: `1.5px solid ${colors.primary}`,
            borderRadius: radius.md,
            background: colors.primarySoft,
            color: colors.primary,
            fontSize: font.size.sm,
            fontWeight: font.weight.semibold,
            cursor: gps.kind === "busy" ? "wait" : "pointer",
          }}
        >
          <span aria-hidden>📍</span>
          {gps.kind === "busy" ? gps.text : "Use my current location"}
        </button>
        {gps.kind === "error" && (
          <p role="alert" style={noteStyle(colors.dangerText)}>
            {gps.text}
          </p>
        )}
      </div>

      <Divider label="or PIN code" />

      {/* Not a <form>: the picker also lives inside other forms (the listing editor). */}
      <div>
        <div style={{ display: "flex", gap: 6 }}>
          <select
            aria-label="Country"
            value={pinCountry}
            onChange={(e) => {
              setPinCountry(e.target.value);
              setPinStatus({ kind: "idle" });
            }}
            style={{ ...fieldStyle, flex: "0 0 72px", padding: "0 6px" }}
          >
            {COUNTRY_OPTIONS.map((c) => (
              <option key={c.code} value={c.code} title={c.label}>
                {c.code}
              </option>
            ))}
          </select>
          <input
            aria-label={pinCountry === "IN" ? "PIN code" : "Postal code"}
            type="text"
            inputMode={pinCountry === "IN" ? "numeric" : "text"}
            autoComplete="postal-code"
            maxLength={pinCountry === "IN" ? 6 : 10}
            placeholder={
              pinCountry === "IN" ? "6-digit PIN" : "ZIP / postal code"
            }
            value={pin}
            onChange={(e) => {
              setPin(
                pinCountry === "IN"
                  ? e.target.value.replace(/\D/g, "")
                  : e.target.value,
              );
              setPinStatus({ kind: "idle" });
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                void findPin();
              }
            }}
            enterKeyHint="search"
            style={{ ...fieldStyle, flex: 1, minWidth: 0 }}
          />
          <button
            type="button"
            onClick={findPin}
            disabled={pinStatus.kind === "busy" || !pin.trim()}
            style={{
              minHeight: 44,
              padding: "0 16px",
              border: "none",
              borderRadius: radius.md,
              background: colors.primary,
              color: "#fff",
              fontSize: font.size.sm,
              fontWeight: font.weight.semibold,
              cursor: "pointer",
              opacity: !pin.trim() ? 0.6 : 1,
            }}
          >
            Find
          </button>
        </div>
        {pinStatus.kind === "busy" && (
          <p style={noteStyle(colors.textSubtle)}>{pinStatus.text}</p>
        )}
        {pinStatus.kind === "error" && (
          <p role="alert" style={noteStyle(colors.dangerText)}>
            {pinStatus.text}
          </p>
        )}
      </div>

      <Divider label="or search" />

      <div>
        <input
          type="search"
          aria-label="Search area, city or town"
          placeholder="Area, city or town — e.g. Gachibowli"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onSearchKeyDown}
          autoFocus={autoFocus}
          enterKeyHint="search"
          style={{ ...fieldStyle, width: "100%" }}
        />
        {searching && <p style={noteStyle(colors.textSubtle)}>Searching…</p>}
        {!searching && searched && results.length === 0 && (
          <p style={noteStyle(colors.textSubtle)}>
            No places found. Try a nearby city or your PIN code.
          </p>
        )}
        {results.length > 0 && (
          <ul
            style={{
              listStyle: "none",
              margin: "6px 0 0",
              padding: 0,
              maxHeight: 264,
              overflowY: "auto",
            }}
          >
            {results.map((item, idx) => (
              <li key={`${item.latitude}-${item.longitude}-${idx}`}>
                <button
                  type="button"
                  onClick={() => onPick(fromSearchItem(item))}
                  className="op-place-option"
                  style={{
                    width: "100%",
                    minHeight: 44,
                    textAlign: "left",
                    padding: "8px 10px",
                    background: "none",
                    border: "none",
                    borderRadius: radius.sm,
                    cursor: "pointer",
                    display: "flex",
                    flexDirection: "column",
                    gap: 1,
                  }}
                >
                  <span
                    style={{
                      fontSize: font.size.sm,
                      fontWeight: font.weight.semibold,
                      color: colors.text,
                    }}
                  >
                    {item.locality ||
                      item.city ||
                      item.display_name.split(",")[0]}
                  </span>
                  <span
                    style={{ fontSize: font.size.xs, color: colors.textSubtle }}
                  >
                    {placeContext(item)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function Divider({ label }: { label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ flex: 1, height: 1, background: colors.border }} />
      <span
        style={{
          fontSize: font.size.xs,
          color: colors.textFaint,
          fontWeight: font.weight.semibold,
          textTransform: "uppercase",
          letterSpacing: "0.06em",
        }}
      >
        {label}
      </span>
      <div style={{ flex: 1, height: 1, background: colors.border }} />
    </div>
  );
}

const fieldStyle: React.CSSProperties = {
  height: 44,
  padding: "0 12px",
  border: `1.5px solid ${colors.borderStrong}`,
  borderRadius: radius.md,
  fontSize: font.size.sm,
  color: colors.text,
  background: "#fff",
  outline: "none",
  boxSizing: "border-box",
};

function noteStyle(color: string): React.CSSProperties {
  return { margin: "6px 0 0", fontSize: font.size.xs, color, lineHeight: 1.5 };
}
