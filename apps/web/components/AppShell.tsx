"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useAuth } from "../contexts/AuthContext";
import { LocationSwitcher } from "./LocationSwitcher";
import {
  Icon,
  SearchBar,
  colors,
  font,
  layout,
  zIndex,
} from "./ui";

type Props = {
  children: ReactNode;
  /** Hide the bottom nav (e.g. on flows where it would compete for attention). */
  hideBottomNav?: boolean;
  /** Show a plain header without categories/search (e.g. auth pages). */
  minimalHeader?: boolean;
};

/**
 * App-wide shell: header on top, optional bottom nav, page content in between.
 *
 * The header matches the home-page design: brand + tagline, location, big
 * pill search, Chats/Favorites/Login (or user menu) on the right.
 * The bottom nav has 5 items with the elevated central "Sell" +.
 */
export function AppShell({ children, hideBottomNav, minimalHeader }: Props) {
  return (
    <div
      style={{
        background: colors.bg,
        minHeight: "100vh",
        fontFamily: font.family,
        paddingBottom: hideBottomNav ? 0 : layout.bottomNavHeight + 24,
        color: colors.text,
      }}
    >
      <TopHeader minimal={minimalHeader} />
      <main>{children}</main>
      {!hideBottomNav && <BottomNav />}
    </div>
  );
}

/* ─────────── Top header ─────────── */

function TopHeader({ minimal }: { minimal?: boolean }) {
  const { user, isAuthenticated } = useAuth();

  return (
    <header
      style={{
        background: colors.surface,
        borderBottom: `1px solid ${colors.border}`,
        position: "sticky",
        top: 0,
        zIndex: zIndex.header,
      }}
    >
      <div
        style={{
          maxWidth: layout.maxWidth,
          margin: "0 auto",
          padding: `16px ${layout.gutter}px`,
          display: "flex",
          alignItems: "center",
          gap: 24,
        }}
      >
        {/* Brand */}
        <Link
          href="/"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            textDecoration: "none",
            flexShrink: 0,
          }}
        >
          <Icon.logo size={42} />
          <div>
            <div
              style={{
                fontSize: font.size["2xl"],
                fontWeight: font.weight.heavy,
                color: colors.text,
                letterSpacing: "-0.02em",
                lineHeight: 1,
              }}
            >
              OldPages
            </div>
            <div style={{ fontSize: 10, color: colors.textSubtle, marginTop: 3 }}>
              Every old book finds a new reader
            </div>
          </div>
        </Link>

        {!minimal && (
          <>
            <LocationSwitcher />
            <SearchBar />
          </>
        )}

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 24,
            marginLeft: "auto",
            flexShrink: 0,
          }}
        >
          <HeaderLink href="/inbox" icon={<Icon.chat />} label="Chats" />
          <HeaderLink href="/favorites" icon={<Icon.heart />} label="Favorites" />
          {isAuthenticated && user ? (
            <HeaderLink href="/profile/me" icon={<Icon.user />} label={displayName(user.email)} />
          ) : (
            <HeaderLink href="/login" icon={<Icon.user />} label="Login" />
          )}
        </div>
      </div>
    </header>
  );
}

function displayName(email: string): string {
  const local = email.split("@")[0] ?? email;
  return local.length > 14 ? `${local.slice(0, 12)}…` : local;
}

function HeaderLink({ href, icon, label }: { href: string; icon: ReactNode; label: string }) {
  return (
    <Link
      href={href}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        textDecoration: "none",
        color: colors.textMuted,
        fontSize: font.size.base,
        fontWeight: font.weight.medium,
      }}
    >
      {icon}
      {label}
    </Link>
  );
}

/* ─────────── Bottom nav ─────────── */

function BottomNav() {
  const pathname = usePathname();
  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <nav
      style={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        background: colors.surface,
        borderTop: `1px solid ${colors.border}`,
        padding: "10px 0 12px",
        zIndex: zIndex.bottomNav,
      }}
    >
      <div
        style={{
          maxWidth: layout.maxWidth,
          margin: "0 auto",
          display: "grid",
          gridTemplateColumns: "repeat(5, 1fr)",
          alignItems: "center",
        }}
      >
        <NavItem href="/" label="Home" icon={<Icon.home color={isActive("/") ? colors.primary : colors.textSubtle} />} active={isActive("/")} />
        <NavItem href="/offers" label="Promotion" icon={<Icon.megaphone color={isActive("/offers") ? colors.primary : colors.textSubtle} />} active={isActive("/offers")} />
        <SellItem />
        <NavItem href="/my-listings" label="My Ads" icon={<Icon.clipboard color={isActive("/my-listings") ? colors.primary : colors.textSubtle} />} active={isActive("/my-listings")} />
        <NavItem href="/profile/me" label="Account" icon={<Icon.user color={isActive("/profile") ? colors.primary : colors.textSubtle} />} active={isActive("/profile")} />
      </div>
    </nav>
  );
}

function NavItem({
  href,
  label,
  icon,
  active,
}: {
  href: string;
  label: string;
  icon: ReactNode;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 4,
        textDecoration: "none",
        color: active ? colors.primary : colors.textSubtle,
      }}
    >
      {icon}
      <span style={{ fontSize: font.size.sm, fontWeight: font.weight.medium }}>{label}</span>
    </Link>
  );
}

function SellItem() {
  return (
    <Link
      href="/listings/create"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 6,
        textDecoration: "none",
        color: colors.textSubtle,
      }}
    >
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: "50%",
          background: colors.primary,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 6px 16px rgba(37,99,235,0.35)",
          marginTop: -22,
        }}
      >
        <Icon.plus />
      </div>
      <span style={{ fontSize: font.size.sm, fontWeight: font.weight.medium }}>Sell</span>
    </Link>
  );
}
