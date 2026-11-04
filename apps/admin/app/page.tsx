"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { adminFetch } from "../lib/api";
import { useRouter } from "next/navigation";

interface ModerationCase {
  id: string;
  case_type: string;
  status: string;
  created_at: string;
  priority?: string;
}

export default function AdminDashboard() {
  const router = useRouter();
  const [recentCases, setRecentCases] = useState<ModerationCase[]>([]);
  const [pendingInstitutions, setPendingInstitutions] = useState(0);
  const [pendingBusinesses, setPendingBusinesses] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [casesData, instData, bizData] = await Promise.all([
          adminFetch<{ items: ModerationCase[] }>("/admin/moderation/cases?limit=5"),
          adminFetch<{ items: unknown[] }>("/institutions/pending?limit=1").catch(() => ({ items: [] })),
          adminFetch<unknown[]>("/business/pending?limit=50").catch(() => []),
        ]);
        setRecentCases(casesData.items ?? []);
        setPendingInstitutions((instData.items ?? []).length);
        setPendingBusinesses(Array.isArray(bizData) ? bizData.length : 0);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const totalPending = pendingInstitutions + pendingBusinesses;

  const statCards: { label: string; value: string | number; href?: string; highlight?: boolean }[] = [
    { label: "Total Users", value: "—" },
    { label: "Active Listings", value: "—" },
    { label: "Open Reports", value: "—" },
    { label: "Pending Approvals", value: totalPending, href: "/approvals", highlight: totalPending > 0 },
    { label: "Revenue", value: "—" },
    { label: "Active Subscriptions", value: "—" },
  ];

  return (
    <div>
      <div className="admin-page-header">
        <h1 className="admin-page-title">Dashboard</h1>
      </div>

      {loading && (
        <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
          <span className="spinner" />
        </div>
      )}

      {error && (
        <div style={{ background: "#fee2e2", color: "#991b1b", padding: ".75rem 1rem", borderRadius: 6, marginBottom: "1rem", fontSize: ".875rem" }}>
          {error}
        </div>
      )}

      {!loading && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
            {statCards.map((card) => (
              <div
                className="admin-stat-card"
                key={card.label}
                onClick={() => card.href && router.push(card.href)}
                style={{
                  cursor: card.href ? "pointer" : "default",
                  border: card.highlight ? "2px solid #f59e0b" : undefined,
                  background: card.highlight ? "#fffbeb" : undefined,
                }}
              >
                <span className="admin-stat-number" style={{ color: card.highlight ? "#d97706" : undefined }}>
                  {String(card.value)}
                </span>
                <span className="admin-stat-label">{card.label}</span>
                {card.highlight && (
                  <span style={{ fontSize: ".7rem", color: "#d97706", fontWeight: 600 }}>Review now →</span>
                )}
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: ".75rem", marginBottom: "2rem" }}>
            <Link href="/reports">
              <button className="admin-btn admin-btn-primary">Go to Reports Queue</button>
            </Link>
            <Link href="/moderation">
              <button className="admin-btn admin-btn-secondary">Moderate Content</button>
            </Link>
            <Link href="/users">
              <button className="admin-btn admin-btn-secondary">View Users</button>
            </Link>
          </div>

          <div className="admin-panel" style={{ padding: "1.25rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 600, margin: "0 0 1rem" }}>Recent Moderation Activity</h2>
            {recentCases.length === 0 ? (
              <p style={{ color: "#5c6670", fontSize: ".875rem" }}>No recent activity.</p>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Case ID</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {recentCases.map((c) => (
                    <tr key={c.id} style={{ cursor: "pointer" }} onClick={() => window.location.href = `/moderation`}>
                      <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{c.id.slice(0, 8)}…</td>
                      <td>{c.case_type}</td>
                      <td>
                        <span className={`admin-badge ${c.status === "open" ? "admin-badge-yellow" : c.status === "resolved" ? "admin-badge-green" : "admin-badge-gray"}`}>
                          {c.status}
                        </span>
                      </td>
                      <td>{c.priority ?? "—"}</td>
                      <td style={{ color: "#5c6670", fontSize: ".8rem" }}>{new Date(c.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
}
