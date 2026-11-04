"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { AppShell } from "./AppShell";

const AUTH_PATHS = ["/login", "/register", "/forgot-password"];

/**
 * Routes that get the AppShell header but not the bottom nav. Fullscreen views
 * (chat threads, order flows, listing wizards) benefit from more vertical room.
 */
const HIDE_BOTTOM_NAV_PREFIXES = [
  "/inbox/",       // full-screen chat threads (bottom nav collides with input bar)
];

/**
 * Wraps children in the AppShell (header + bottom nav), except on auth pages
 * which render their own centered layout with no navigation chrome.
 */
export function ConditionalShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isAuth = AUTH_PATHS.some((p) => pathname.startsWith(p));
  if (isAuth) return <>{children}</>;

  const isFullscreen =
    HIDE_BOTTOM_NAV_PREFIXES.some((prefix) => {
      if (prefix.endsWith("/")) return pathname.startsWith(prefix) && pathname !== prefix.slice(0, -1);
      return pathname.startsWith(prefix);
    });

  return <AppShell hideBottomNav={isFullscreen}>{children}</AppShell>;
}

/** @deprecated Use ConditionalShell — kept for callers still importing this name. */
export function ConditionalHeader() {
  return null;
}
