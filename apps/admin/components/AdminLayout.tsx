"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearTokens, getAccessToken, getUserEmail } from "../lib/auth";

const NAV_LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/approvals", label: "Approvals" },
  { href: "/users", label: "Users" },
  { href: "/listings", label: "Listings" },
  { href: "/reports", label: "Reports" },
  { href: "/moderation", label: "Moderation" },
  { href: "/payments", label: "Payments" },
  { href: "/communities", label: "Communities" },
  { href: "/analytics", label: "Analytics" },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [userEmail, setUserEmail] = useState<string>("");

  useEffect(() => {
    const token = getAccessToken();
    if (!token && pathname !== "/login") {
      router.replace("/login");
      return;
    }
    // Decode email from JWT payload (best-effort)
    if (token) {
      setUserEmail(getUserEmail() ?? "admin");
    }
  }, [pathname, router]);

  function handleLogout() {
    clearTokens();
    router.replace("/login");
  }

  if (pathname === "/login") {
    return <>{children}</>;
  }

  return (
    <div className="admin-shell">
      <header className="admin-header" style={{ height: 60 }}>
        <span className="admin-brand">OldPages Admin</span>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          {userEmail && (
            <span style={{ fontSize: ".875rem", color: "#5c6670" }}>{userEmail}</span>
          )}
          <button className="admin-btn admin-btn-secondary admin-btn-sm" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>
      <div className="admin-sidebar-layout">
        <nav className="admin-sidebar-nav" aria-label="Admin navigation">
          {NAV_LINKS.map((link) => {
            const isActive =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`admin-nav-item${isActive ? " active" : ""}`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
        <main className="admin-main-content">{children}</main>
      </div>
    </div>
  );
}
