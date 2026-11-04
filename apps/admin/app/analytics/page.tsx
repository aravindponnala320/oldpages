"use client";

import Link from "next/link";
import { useState } from "react";

interface AnalyticsStats {
  listings_today?: number;
  signups_today?: number;
  messages_today?: number;
  transactions_today?: number;
  listings_this_week?: number;
  signups_this_week?: number;
  messages_this_week?: number;
  transactions_this_week?: number;
  active_users_today?: number;
  total_listings?: number;
  total_users?: number;
}

export default function AnalyticsPage() {
  const [stats] = useState<AnalyticsStats>({});
  const [loading] = useState(false);
  const [error] = useState<string | null>(null);

  const todayCards = [
    { label: "Listings Today", value: stats.listings_today ?? "—", href: "/listings" },
    { label: "Signups Today", value: stats.signups_today ?? "—", href: "/users" },
    { label: "Messages Today", value: stats.messages_today ?? "—", href: null },
    { label: "Transactions Today", value: stats.transactions_today ?? "—", href: "/payments" },
  ];

  const weekCards = [
    { label: "Listings This Week", value: stats.listings_this_week ?? "—", href: "/listings" },
    { label: "Signups This Week", value: stats.signups_this_week ?? "—", href: "/users" },
    { label: "Messages This Week", value: stats.messages_this_week ?? "—", href: null },
    { label: "Transactions This Week", value: stats.transactions_this_week ?? "—", href: "/payments" },
  ];

  const overallCards = [
    { label: "Total Users", value: stats.total_users ?? "—", href: "/users" },
    { label: "Total Listings", value: stats.total_listings ?? "—", href: "/listings" },
    { label: "Active Users Today", value: stats.active_users_today ?? "—", href: "/users" },
  ];

  return (
    <div>
      <div className="admin-page-header">
        <h1 className="admin-page-title">Analytics</h1>
        <span style={{ fontSize: ".8rem", color: "#5c6670", background: "#f3f4f6", padding: ".25rem .75rem", borderRadius: 999 }}>
          Counts unavailable
        </span>
      </div>

      {loading && <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><span className="spinner" /></div>}

      {error && (
        <div style={{ background: "#fee2e2", color: "#991b1b", padding: ".75rem", borderRadius: 6, marginBottom: "1rem", fontSize: ".875rem" }}>
          {error}
        </div>
      )}

      {!loading && (
        <>
          <div style={{ marginBottom: "1.5rem" }}>
            <h2 style={{ fontSize: ".875rem", fontWeight: 600, color: "#5c6670", textTransform: "uppercase", letterSpacing: ".04em", margin: "0 0 .75rem" }}>Today</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "1rem" }}>
              {todayCards.map((card) => (
                <div className="admin-stat-card" key={card.label}>
                  <span className="admin-stat-number">{String(card.value)}</span>
                  <span className="admin-stat-label">{card.label}</span>
                  {card.href && (
                    <Link href={card.href} style={{ fontSize: ".75rem", color: "#256f5b", marginTop: ".25rem" }}>
                      View →
                    </Link>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: "1.5rem" }}>
            <h2 style={{ fontSize: ".875rem", fontWeight: 600, color: "#5c6670", textTransform: "uppercase", letterSpacing: ".04em", margin: "0 0 .75rem" }}>This Week</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "1rem" }}>
              {weekCards.map((card) => (
                <div className="admin-stat-card" key={card.label}>
                  <span className="admin-stat-number">{String(card.value)}</span>
                  <span className="admin-stat-label">{card.label}</span>
                  {card.href && (
                    <Link href={card.href} style={{ fontSize: ".75rem", color: "#256f5b", marginTop: ".25rem" }}>
                      View →
                    </Link>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <h2 style={{ fontSize: ".875rem", fontWeight: 600, color: "#5c6670", textTransform: "uppercase", letterSpacing: ".04em", margin: "0 0 .75rem" }}>Overall</h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "1rem" }}>
              {overallCards.map((card) => (
                <div className="admin-stat-card" key={card.label}>
                  <span className="admin-stat-number">{String(card.value)}</span>
                  <span className="admin-stat-label">{card.label}</span>
                  {card.href && (
                    <Link href={card.href} style={{ fontSize: ".75rem", color: "#256f5b", marginTop: ".25rem" }}>
                      View →
                    </Link>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="admin-panel" style={{ marginTop: "1.5rem" }}>
            <p style={{ margin: 0, fontSize: ".875rem", color: "#5c6670" }}>
              Analytics counters are not exposed by the current API.
            </p>
          </div>
        </>
      )}
    </div>
  );
}
