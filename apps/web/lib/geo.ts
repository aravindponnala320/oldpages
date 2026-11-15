import type { GeoSearchItem, LocationPayload } from "@oldpages/api-client";
import { apiClient } from "./api";

/** Read the `op_loc` cookie (base64url JSON, see encodeLocationHeader); null if unreadable. */
export function decodeLocationCookie(
  value: string | undefined,
): LocationPayload | null {
  if (!value) return null;
  try {
    const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
    const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes)) as LocationPayload;
  } catch {
    return null;
  }
}

export type LocateResult = { location: LocationPayload } | { error: string };

/** Ask the browser for the device position and name the area it falls in. */
export async function locateBrowser(): Promise<LocateResult> {
  if (typeof navigator === "undefined" || !navigator.geolocation) {
    return {
      error:
        "This browser can't share your location. Enter your PIN code instead.",
    };
  }
  if (typeof window !== "undefined" && !window.isSecureContext) {
    // Browsers only allow geolocation on https:// (and localhost).
    return {
      error:
        "Location needs a secure (https) connection. Enter your PIN code instead.",
    };
  }
  const position = await new Promise<
    GeolocationPosition | GeolocationPositionError
  >((resolve) => {
    navigator.geolocation.getCurrentPosition(resolve, resolve, {
      enableHighAccuracy: true,
      timeout: 12000,
      maximumAge: 2 * 60 * 1000,
    });
  });
  if (!("coords" in position)) {
    return {
      error:
        position.code === position.PERMISSION_DENIED
          ? "Location access is blocked. Allow it in your browser settings, or enter your PIN code."
          : "Couldn't find your location. Try again, or enter your PIN code.",
    };
  }
  const { latitude, longitude } = position.coords;
  const named = await apiClient
    .reverseGeocode(latitude, longitude)
    .catch(() => null);
  return { location: named ?? { latitude, longitude } };
}

export function fromSearchItem(
  item: GeoSearchItem,
  radiusKm?: number | null,
): LocationPayload {
  return {
    latitude: item.latitude,
    longitude: item.longitude,
    locality: item.locality ?? null,
    city: item.city ?? null,
    state: item.state ?? null,
    country: item.country ?? null,
    country_code: item.country_code ?? null,
    postal_code: item.postal_code ?? null,
    display_name: item.display_name,
    radius_km: radiusKm ?? null,
  };
}

/** Short label for a location: "Gachibowli, Hyderabad"; adds the country outside India. */
export function shortLocationLabel(loc: LocationPayload | null): string {
  if (!loc) return "Set location";
  const place = [loc.locality, loc.city].filter(Boolean).join(", ");
  if (place)
    return loc.country_code && loc.country_code !== "IN"
      ? `${place}, ${loc.country_code}`
      : place;
  if (loc.display_name)
    return loc.display_name.split(",").slice(0, 2).join(",");
  return `${loc.latitude.toFixed(2)}, ${loc.longitude.toFixed(2)}`;
}

/** Second line under a place name: everything after the first part. */
export function placeContext(loc: {
  locality?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
}): string {
  const parts = [loc.locality ? loc.city : null, loc.state, loc.country].filter(
    Boolean,
  );
  return parts.join(", ");
}

// Countries that measure road distance in miles.
const MILES_COUNTRIES = new Set(["US", "GB", "LR", "MM"]);

export function usesMiles(countryCode: string | null | undefined): boolean {
  return MILES_COUNTRIES.has((countryCode ?? "").toUpperCase());
}

/**
 * "< 1 km", "3 km", "12 mi" in the reader's units. Whole numbers only: public listing
 * positions are rounded to ~1 km for the seller's privacy, so decimals would be false precision.
 */
export function formatDistance(
  km: number,
  readerCountry: string | null | undefined,
): string {
  const miles = usesMiles(readerCountry);
  const value = miles ? km * 0.621371 : km;
  const unit = miles ? "mi" : "km";
  return value < 1
    ? `< 1 ${unit}`
    : `${Math.round(value).toLocaleString("en")} ${unit}`;
}

/** Card footer for a listing: "3 km · Gachibowli", or just the area when distance is unknown. */
export function listingPlaceLabel(
  listing: {
    distance_km?: number | null;
    location?: { neighborhood?: string | null; city?: string | null } | null;
  },
  readerCountry: string | null | undefined,
): string | null {
  const area = listing.location?.neighborhood || listing.location?.city || null;
  if (listing.distance_km == null) return area;
  const distance = formatDistance(listing.distance_km, readerCountry);
  return area ? `${distance} · ${area}` : distance;
}

/** "Within 25 km of Gachibowli, Hyderabad" (the API's default radius is 25 km). */
export function nearbyCaption(loc: LocationPayload | null): string | null {
  if (!loc || (!loc.city && !loc.locality)) return null;
  const radius = formatDistance(loc.radius_km ?? 25, loc.country_code);
  return `Within ${radius} of ${shortLocationLabel(loc)}`;
}
