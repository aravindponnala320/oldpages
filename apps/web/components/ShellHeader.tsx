"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { Avatar } from "./ui/Avatar";
import { LocationSwitcher } from "./LocationSwitcher";

const navLinks = [
  { href: "/search", label: "Browse" },
  { href: "/communities", label: "Communities" },
  { href: "/events", label: "Events" },
  { href: "/reading", label: "Reading" },
];

export function ShellHeader() {
  const { user, isAuthenticated, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = searchQuery.trim();
    if (q) router.push(`/search?q=${encodeURIComponent(q)}`);
  }

  return (
    <header style={{
      background: "#fff",
      borderBottom: "1px solid #e5e7eb",
      position: "sticky", top: 0, zIndex: 50,
    }}>
      <div style={{
        maxWidth: 1200, margin: "0 auto",
        padding: "0 1.5rem",
        height: 60,
        display: "flex", alignItems: "center", gap: "1rem",
      }}>
        {/* Logo */}
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: "0.5rem", textDecoration: "none", flexShrink: 0 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 8,
            background: "#256f5b",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontWeight: 800, color: "white", fontSize: "0.85rem",
          }}>
            OP
          </div>
          <span style={{ fontWeight: 800, color: "#1f2933", fontSize: "1rem", letterSpacing: "-0.01em" }}>
            OldPages
          </span>
        </Link>

        {/* Nav */}
        <nav style={{ display: "flex", gap: "0.125rem", marginLeft: "0.5rem" }}>
          {navLinks.map((link) => {
            const active = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                style={{
                  padding: "0.4rem 0.75rem",
                  borderRadius: 6,
                  fontSize: "0.875rem",
                  fontWeight: active ? 600 : 500,
                  color: active ? "#256f5b" : "#5c6670",
                  textDecoration: "none",
                  background: active ? "#f0faf7" : "transparent",
                  transition: "background 0.15s, color 0.15s",
                }}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Search */}
        <form onSubmit={handleSearch} style={{ flex: 1, maxWidth: 380, margin: "0 auto" }}>
          <div style={{
            display: "flex", alignItems: "center",
            background: "#f7f7f3", border: "1.5px solid #e5e7eb",
            borderRadius: 8, overflow: "hidden",
            transition: "border-color 0.15s",
          }}
            onFocusCapture={(e) => (e.currentTarget as HTMLDivElement).style.borderColor = "#256f5b"}
            onBlurCapture={(e) => (e.currentTarget as HTMLDivElement).style.borderColor = "#e5e7eb"}
          >
            <span style={{ padding: "0 0.625rem", color: "#9ca3af", fontSize: "0.875rem" }}>🔍</span>
            <input
              type="search"
              placeholder="Search books..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                flex: 1, border: "none", outline: "none",
                background: "transparent", fontSize: "0.875rem",
                color: "#1f2933", padding: "0.5rem 0",
              }}
            />
          </div>
        </form>

        {/* Location switcher */}
        <LocationSwitcher />

        {/* Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginLeft: "auto", flexShrink: 0 }}>
          {isAuthenticated && user ? (
            <>
              <Link href="/listings/create" style={{
                background: "#256f5b", color: "white",
                padding: "0.45rem 0.875rem",
                borderRadius: 7, fontSize: "0.8rem", fontWeight: 700,
                textDecoration: "none", whiteSpace: "nowrap",
              }}>
                + List Book
              </Link>

              <Link href="/notifications" style={{ padding: "0.4rem", borderRadius: 6, color: "#5c6670", textDecoration: "none", fontSize: "1.1rem", lineHeight: 1 }} title="Notifications">
                🔔
              </Link>
              <Link href="/inbox" style={{ padding: "0.4rem", borderRadius: 6, color: "#5c6670", textDecoration: "none", fontSize: "1.1rem", lineHeight: 1 }} title="Messages">
                ✉️
              </Link>

              {/* User menu */}
              <div style={{ position: "relative" }}>
                <button
                  onClick={() => setMenuOpen((v) => !v)}
                  style={{
                    background: "none", border: "1.5px solid #e5e7eb",
                    borderRadius: 8, padding: "0.25rem",
                    cursor: "pointer", display: "flex", alignItems: "center",
                  }}
                >
                  <Avatar name={user.email} size="sm" />
                </button>

                {menuOpen && (
                  <>
                    <div style={{ position: "fixed", inset: 0, zIndex: 49 }} onClick={() => setMenuOpen(false)} />
                    <div style={{
                      position: "absolute", right: 0, top: "calc(100% + 8px)",
                      background: "white", border: "1px solid #e5e7eb",
                      borderRadius: 10, minWidth: 200,
                      boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
                      zIndex: 50, overflow: "hidden",
                      padding: "0.25rem",
                    }}>
                      <div style={{ padding: "0.625rem 0.75rem", borderBottom: "1px solid #f3f4f6", marginBottom: "0.25rem" }}>
                        <p style={{ fontSize: "0.75rem", color: "#9ca3af", margin: "0 0 0.125rem" }}>Signed in as</p>
                        <p style={{ fontSize: "0.825rem", fontWeight: 600, color: "#1f2933", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {user.email}
                        </p>
                      </div>

                      {[
                        { href: "/dashboard", label: "Dashboard", icon: "⊞" },
                        { href: "/my-listings", label: "My Listings", icon: "📋" },
                        { href: "/orders", label: "Orders", icon: "📦" },
                        { href: "/business", label: "My Business", icon: "🏪" },
                        { href: "/institution", label: "My Institution", icon: "🏫" },
                        { href: "/profile", label: "Profile", icon: "👤" },
                      ].map((item) => (
                        <Link
                          key={item.href}
                          href={item.href}
                          onClick={() => setMenuOpen(false)}
                          style={{
                            display: "flex", alignItems: "center", gap: "0.625rem",
                            padding: "0.55rem 0.75rem", borderRadius: 7,
                            color: "#374151", textDecoration: "none",
                            fontSize: "0.875rem",
                            transition: "background 0.1s",
                          }}
                          onMouseEnter={(e) => (e.currentTarget as HTMLAnchorElement).style.background = "#f9fafb"}
                          onMouseLeave={(e) => (e.currentTarget as HTMLAnchorElement).style.background = "transparent"}
                        >
                          <span style={{ fontSize: "0.9rem", width: 18, textAlign: "center" }}>{item.icon}</span>
                          {item.label}
                        </Link>
                      ))}

                      <div style={{ borderTop: "1px solid #f3f4f6", marginTop: "0.25rem", paddingTop: "0.25rem" }}>
                        <button
                          onClick={() => { setMenuOpen(false); logout(); }}
                          style={{
                            display: "flex", alignItems: "center", gap: "0.625rem",
                            width: "100%", padding: "0.55rem 0.75rem", borderRadius: 7,
                            background: "none", border: "none", cursor: "pointer",
                            fontSize: "0.875rem", color: "#ef4444", textAlign: "left",
                            transition: "background 0.1s",
                          }}
                          onMouseEnter={(e) => (e.currentTarget as HTMLButtonElement).style.background = "#fff1f2"}
                          onMouseLeave={(e) => (e.currentTarget as HTMLButtonElement).style.background = "transparent"}
                        >
                          <span style={{ fontSize: "0.9rem", width: 18, textAlign: "center" }}>↩</span>
                          Sign Out
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </>
          ) : (
            <>
              <Link href="/login" style={{
                padding: "0.45rem 0.875rem", borderRadius: 7,
                fontSize: "0.875rem", fontWeight: 500, color: "#374151",
                textDecoration: "none", border: "1.5px solid #e5e7eb",
                background: "#fff",
              }}>
                Sign In
              </Link>
              <Link href="/register" style={{
                padding: "0.45rem 0.875rem", borderRadius: 7,
                fontSize: "0.875rem", fontWeight: 700,
                background: "#256f5b", color: "white",
                textDecoration: "none",
              }}>
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
