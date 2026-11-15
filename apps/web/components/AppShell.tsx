"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useAuth } from "../contexts/AuthContext";
import { LocationSwitcher } from "./LocationSwitcher";
import { Icon, SearchBar, colors, font, layout, zIndex } from "./ui";

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
      // Without the bottom nav the page is a full-height app view (e.g. a chat thread):
      // the shell fills the visible viewport and main takes the space under the header.
      className={hideBottomNav ? "op-shell-fullscreen" : "op-shell-with-nav"}
      style={{
        background: colors.bg,
        minHeight: "100vh",
        fontFamily: font.family,
        color: colors.text,
      }}
    >
      <TopHeader minimal={minimalHeader} />
      <main className="op-shell-main">{children}</main>
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
      <div className="op-header-inner" style={{ maxWidth: layout.maxWidth }}>
        {/* Brand */}
        <Link
          href="/"
          className="op-header-brand"
          aria-label="OldPages home"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            textDecoration: "none",
            flexShrink: 0,
          }}
        >
          <span className="op-header-logo">
            <Icon.logo size={42} />
          </span>
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
            <div
              className="op-header-tagline"
              style={{ fontSize: 12, color: colors.textSubtle, marginTop: 3 }}
            >
              Every old book finds a new reader
            </div>
          </div>
        </Link>

        {!minimal && (
          <div className="op-header-tools">
            <LocationSwitcher />
            <SearchBar />
          </div>
        )}

        <nav className="op-header-actions" aria-label="Account">
          <HeaderLink href="/inbox" icon={<Icon.chat />} label="Chats" />
          <HeaderLink
            href="/favorites"
            icon={<Icon.heart />}
            label="Favorites"
          />
          {isAuthenticated && user ? (
            <>
              <HeaderLink
                href="/my-listings"
                icon={<Icon.clipboard />}
                label="My Ads"
                desktopOnly
              />
              <HeaderLink
                href="/profile/me"
                icon={<Icon.user />}
                label={displayName(user.email)}
                desktopOnly
              />
            </>
          ) : (
            <HeaderLink href="/login" icon={<Icon.user />} label="Login" />
          )}
          <Link
            href="/listings/create"
            className="op-desktop-nav"
            style={{
              alignItems: "center",
              gap: 6,
              padding: "10px 18px",
              borderRadius: 999,
              background: colors.primary,
              color: "#fff",
              fontSize: font.size.base,
              fontWeight: font.weight.semibold,
              textDecoration: "none",
              whiteSpace: "nowrap",
            }}
          >
            + Sell
          </Link>
        </nav>
      </div>
    </header>
  );
}

function displayName(email: string): string {
  const local = email.split("@")[0] ?? email;
  return local.length > 14 ? `${local.slice(0, 12)}…` : local;
}

function HeaderLink({
  href,
  icon,
  label,
  desktopOnly,
}: {
  href: string;
  icon: ReactNode;
  label: string;
  desktopOnly?: boolean;
}) {
  return (
    <Link
      href={href}
      aria-label={label}
      title={label}
      className={
        desktopOnly ? "op-header-link op-desktop-nav" : "op-header-link"
      }
      style={{
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        minWidth: 40,
        minHeight: 40,
        textDecoration: "none",
        color: colors.textMuted,
        fontSize: font.size.base,
        fontWeight: font.weight.medium,
        whiteSpace: "nowrap",
      }}
    >
      {icon}
      <span className="op-header-label">{label}</span>
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
      className="op-bottom-nav"
      aria-label="Main"
      style={{
        position: "fixed",
        bottom: 0,
        left: 0,
        right: 0,
        background: colors.surface,
        borderTop: `1px solid ${colors.border}`,
        padding: "8px 0 calc(10px + env(safe-area-inset-bottom))",
        zIndex: zIndex.bottomNav,
      }}
    >
      <div
        style={{
          maxWidth: 640,
          margin: "0 auto",
          display: "grid",
          gridTemplateColumns: "repeat(5, 1fr)",
          alignItems: "center",
        }}
      >
        <NavItem
          href="/"
          label="Home"
          icon={
            <Icon.home
              color={isActive("/") ? colors.primary : colors.textSubtle}
            />
          }
          active={isActive("/")}
        />
        <NavItem
          href="/offers"
          label="Promotion"
          icon={
            <Icon.megaphone
              color={isActive("/offers") ? colors.primary : colors.textSubtle}
            />
          }
          active={isActive("/offers")}
        />
        <SellItem />
        <NavItem
          href="/my-listings"
          label="My Ads"
          icon={
            <Icon.clipboard
              color={
                isActive("/my-listings") ? colors.primary : colors.textSubtle
              }
            />
          }
          active={isActive("/my-listings")}
        />
        <NavItem
          href="/profile/me"
          label="Account"
          icon={
            <Icon.user
              color={isActive("/profile") ? colors.primary : colors.textSubtle}
            />
          }
          active={isActive("/profile")}
        />
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
      aria-current={active ? "page" : undefined}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 4,
        minHeight: 48,
        textDecoration: "none",
        color: active ? colors.primary : colors.textSubtle,
      }}
    >
      {icon}
      <span style={{ fontSize: font.size.sm, fontWeight: font.weight.medium }}>
        {label}
      </span>
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
      <span style={{ fontSize: font.size.sm, fontWeight: font.weight.medium }}>
        Sell
      </span>
    </Link>
  );
}
