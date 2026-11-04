"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { LocationPayload, LocationSource } from "@oldpages/api-client";
import { encodeLocationHeader } from "@oldpages/api-client";
import { apiClient } from "../lib/api";
import { getAccessToken } from "../lib/auth";
import { useAuth } from "./AuthContext";

const STORAGE_KEY = "op:activeLocation";
const CONSENT_KEY = "op:geoConsent";
const COOKIE_NAME = "op_loc";
const COOKIE_MAX_AGE_DAYS = 90;

/**
 * Write the location as a same-origin cookie so Next.js server components can
 * read it via `cookies()` and forward it to the API on server-side fetches.
 * The API also sets its own cookie on its own origin — that one is used for
 * direct client-to-API calls; this one is used for the SSR path.
 */
function writeSameOriginCookie(loc: LocationPayload | null): void {
  if (typeof document === "undefined") return;
  if (!loc) {
    document.cookie = `${COOKIE_NAME}=; Path=/; Max-Age=0; SameSite=Lax`;
    return;
  }
  const value = encodeLocationHeader(loc);
  const maxAge = COOKIE_MAX_AGE_DAYS * 24 * 3600;
  document.cookie = `${COOKIE_NAME}=${value}; Path=/; Max-Age=${maxAge}; SameSite=Lax`;
}

type LocationContextType = {
  active: LocationPayload | null;
  home: LocationPayload | null;
  source: LocationSource;
  isReady: boolean;
  setActive: (location: LocationPayload, persistAsHome?: boolean) => Promise<void>;
  clear: () => Promise<void>;
  requestBrowserLocation: () => Promise<LocationPayload | null>;
};

const LocationContext = createContext<LocationContextType | null>(null);

function readStored(): LocationPayload | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as LocationPayload) : null;
  } catch {
    return null;
  }
}

function writeStored(loc: LocationPayload | null): void {
  if (typeof window === "undefined") return;
  try {
    if (loc) window.localStorage.setItem(STORAGE_KEY, JSON.stringify(loc));
    else window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* storage unavailable — fine */
  }
}

async function browserGeolocate(): Promise<GeolocationPosition | null> {
  if (typeof navigator === "undefined" || !navigator.geolocation) return null;
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve(pos),
      () => resolve(null),
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 5 * 60 * 1000 },
    );
  });
}

export function LocationProvider({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated } = useAuth();
  const [active, setActiveState] = useState<LocationPayload | null>(null);
  const [home, setHome] = useState<LocationPayload | null>(null);
  const [source, setSource] = useState<LocationSource>("unknown");
  const [isReady, setIsReady] = useState(false);
  const initialised = useRef(false);

  const persist = useCallback(
    async (loc: LocationPayload, persistAsHome: boolean) => {
      const token = getAccessToken();
      try {
        await apiClient.setActiveLocation(
          { location: loc, persist_as_home: persistAsHome && !!token },
          token ?? undefined,
        );
      } catch {
        /* API unreachable — still update local state so the UI stays consistent */
      }
      writeStored(loc);
      writeSameOriginCookie(loc); // so SSR-fetched pages can filter
      setActiveState(loc);
      setSource("manual");
      if (persistAsHome) setHome(loc);
    },
    [],
  );

  const setActive = useCallback(
    async (loc: LocationPayload, persistAsHome = false) => {
      await persist(loc, persistAsHome);
    },
    [persist],
  );

  const clear = useCallback(async () => {
    const token = getAccessToken();
    try {
      await apiClient.clearActiveLocation(token ?? undefined);
    } catch {
      /* ignore network errors on clear */
    }
    writeStored(null);
    writeSameOriginCookie(null);
    setActiveState(home);
    setSource(home ? "home" : "unknown");
  }, [home]);

  const requestBrowserLocation = useCallback(async (): Promise<LocationPayload | null> => {
    const pos = await browserGeolocate();
    if (!pos) return null;
    if (typeof window !== "undefined") {
      window.localStorage.setItem(CONSENT_KEY, "granted");
    }
    const reversed = await apiClient
      .reverseGeocode(pos.coords.latitude, pos.coords.longitude)
      .catch(() => null);
    const loc: LocationPayload = reversed ?? {
      latitude: pos.coords.latitude,
      longitude: pos.coords.longitude,
    };
    await persist(loc, isAuthenticated);
    setSource("browser");
    return loc;
  }, [isAuthenticated, persist]);

  useEffect(() => {
    if (initialised.current) return;
    initialised.current = true;
    (async () => {
      const stored = readStored();
      const token = getAccessToken();
      // 1. Ask the API for the canonical view (cookie + home for the logged-in user).
      let serverActive: LocationPayload | null = null;
      let serverHome: LocationPayload | null = null;
      let serverSource: LocationSource = "unknown";
      try {
        const resp = await apiClient.getMyLocation(token ?? undefined, stored);
        serverActive = resp.active;
        serverHome = resp.home;
        serverSource = resp.source;
      } catch {
        /* API might be down; fall back to local */
      }
      setHome(serverHome);
      if (serverActive) {
        writeStored(serverActive);
        writeSameOriginCookie(serverActive);
        setActiveState(serverActive);
        setSource(serverSource);
        setIsReady(true);
        return;
      }
      if (stored) {
        writeSameOriginCookie(stored);
        setActiveState(stored);
        setSource("manual");
        setIsReady(true);
        return;
      }
      // 2. Try IP detection (works without prompting the user).
      try {
        const detected = await apiClient.detectLocation();
        if (detected.location) {
          writeSameOriginCookie(detected.location);
          setActiveState(detected.location);
          setSource(detected.source);
          setIsReady(true);
          return;
        }
      } catch {
        /* no IP DB configured; that's fine */
      }
      setIsReady(true);
    })();
  }, []);

  // On login change (user object flips), refresh from server so home syncs.
  useEffect(() => {
    if (!initialised.current) return;
    (async () => {
      const token = getAccessToken();
      if (!token) {
        setHome(null);
        return;
      }
      try {
        const resp = await apiClient.getMyLocation(token, active);
        setHome(resp.home);
        if (!active && resp.active) {
          setActiveState(resp.active);
          setSource(resp.source);
        }
      } catch {
        /* ignore */
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  const value = useMemo<LocationContextType>(
    () => ({ active, home, source, isReady, setActive, clear, requestBrowserLocation }),
    [active, home, source, isReady, setActive, clear, requestBrowserLocation],
  );

  return <LocationContext.Provider value={value}>{children}</LocationContext.Provider>;
}

export function useLocation(): LocationContextType {
  const ctx = useContext(LocationContext);
  if (!ctx) throw new Error("useLocation must be used within LocationProvider");
  return ctx;
}
