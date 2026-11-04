"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { adminFetch } from "../../../lib/api";

interface UserDetail {
  id: string;
  name?: string;
  email: string;
  created_at?: string;
  is_verified?: boolean;
  status?: string;
  trust_score?: number;
  avatar_url?: string;
  listing_count?: number;
}

interface ModerationUserResponse {
  email: string;
  id: string;
  report_count: number;
  status: string;
}

interface Listing {
  id: string;
  title: string;
  price?: number;
  status: string;
  created_at: string;
}

interface Report {
  id: string;
  reason: string;
  status: string;
  created_at: string;
}

interface ModerationCase {
  id: string;
  case_type: string;
  status: string;
  created_at: string;
}

type Tab = "listings" | "reports" | "moderation" | "audit" | "sessions";

interface ActionModal {
  type: "warn" | "suspend" | "unsuspend" | "ban";
  label: string;
}

export default function UserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const userId = params.id as string;

  const [user, setUser] = useState<UserDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("listings");
  const [tabData, setTabData] = useState<unknown[]>([]);
  const [tabLoading, setTabLoading] = useState(false);
  const [actionModal, setActionModal] = useState<ActionModal | null>(null);
  const [actionReason, setActionReason] = useState("");
  const [duration, setDuration] = useState("7d");
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    async function loadUser() {
      setLoading(true);
      try {
        const data = await adminFetch<ModerationUserResponse>(`/admin/moderation/users/${userId}`);
        setUser({
          id: data.id,
          email: data.email,
          status: data.status,
          trust_score: data.report_count,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load user");
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, [userId]);

  useEffect(() => {
    async function loadTab() {
      setTabLoading(true);
      setTabData([]);
      setTabLoading(false);
    }
    if (userId) loadTab();
  }, [tab, userId]);

  async function handleAction() {
    if (!actionModal) return;
    setActionLoading(true);
    setActionModal(null);
    setActionReason("");
    setActionLoading(false);
  }

  const ACTIONS: ActionModal[] = [
    { type: "warn", label: "Warn" },
    { type: "suspend", label: "Suspend" },
    { type: "unsuspend", label: "Unsuspend" },
    { type: "ban", label: "Ban" },
  ];

  if (loading) return <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><span className="spinner" /></div>;
  if (error) return <div style={{ color: "#991b1b", padding: "1rem" }}>{error}</div>;
  if (!user) return null;

  return (
    <div>
      <div className="admin-page-header">
        <div style={{ display: "flex", alignItems: "center", gap: ".75rem" }}>
          <button className="admin-btn admin-btn-secondary admin-btn-sm" onClick={() => router.back()}>← Back</button>
          <h1 className="admin-page-title">{user.name ?? user.email}</h1>
        </div>
      </div>

      <div className="admin-panel" style={{ marginBottom: "1.5rem" }}>
        <div style={{ display: "flex", gap: "1.5rem", alignItems: "flex-start" }}>
          {user.avatar_url && (
            <img src={user.avatar_url} alt="" style={{ width: 64, height: 64, borderRadius: "50%", objectFit: "cover" }} />
          )}
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
              <div>
                <div style={{ fontSize: ".75rem", color: "#5c6670", marginBottom: ".25rem" }}>Email</div>
                <div style={{ fontWeight: 500 }}>{user.email}</div>
              </div>
              <div>
                <div style={{ fontSize: ".75rem", color: "#5c6670", marginBottom: ".25rem" }}>Joined</div>
                <div>{user.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}</div>
              </div>
              <div>
                <div style={{ fontSize: ".75rem", color: "#5c6670", marginBottom: ".25rem" }}>Status</div>
                <span className={`admin-badge ${
                  user.status === "active" ? "admin-badge-green" :
                  user.status === "suspended" ? "admin-badge-yellow" :
                  user.status === "banned" ? "admin-badge-red" : "admin-badge-gray"
                }`}>{user.status ?? "active"}</span>
              </div>
              <div>
                <div style={{ fontSize: ".75rem", color: "#5c6670", marginBottom: ".25rem" }}>Verified</div>
                <span className={`admin-badge ${user.is_verified ? "admin-badge-green" : "admin-badge-gray"}`}>
                  {user.is_verified ? "Yes" : "No"}
                </span>
              </div>
              {user.trust_score !== undefined && (
                <div>
                  <div style={{ fontSize: ".75rem", color: "#5c6670", marginBottom: ".25rem" }}>Trust Score</div>
                  <div style={{ fontWeight: 600 }}>{user.trust_score}</div>
                </div>
              )}
              {user.listing_count !== undefined && (
                <div>
                  <div style={{ fontSize: ".75rem", color: "#5c6670", marginBottom: ".25rem" }}>Listings</div>
                  <div>{user.listing_count}</div>
                </div>
              )}
            </div>
          </div>
          <div style={{ display: "flex", gap: ".5rem", flexWrap: "wrap" }}>
            {ACTIONS.map((action) => (
              <button
                key={action.type}
                className={`admin-btn admin-btn-sm ${action.type === "ban" || action.type === "suspend" ? "admin-btn-danger" : action.type === "unsuspend" ? "admin-btn-secondary" : "admin-btn-secondary"}`}
                onClick={() => setActionModal(action)}
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="admin-tabs">
        {(["listings", "reports", "moderation", "audit", "sessions"] as Tab[]).map((t) => (
          <button key={t} className={`admin-tab${tab === t ? " active" : ""}`} onClick={() => setTab(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tabLoading && <div style={{ display: "flex", justifyContent: "center", padding: "2rem" }}><span className="spinner" /></div>}

      {!tabLoading && (
        <div className="admin-panel" style={{ padding: 0, overflow: "hidden" }}>
          {tabData.length === 0 ? (
            <div style={{ padding: "2rem", textAlign: "center", color: "#5c6670", fontSize: ".875rem" }}>No data available</div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              {tab === "listings" && (
                <table className="admin-table">
                  <thead><tr><th>ID</th><th>Title</th><th>Price</th><th>Status</th><th>Created</th></tr></thead>
                  <tbody>
                    {(tabData as Listing[]).map((l) => (
                      <tr key={l.id}>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{l.id.slice(0, 8)}…</td>
                        <td>{l.title}</td>
                        <td>{l.price != null ? `₹${l.price}` : "—"}</td>
                        <td><span className={`admin-badge ${l.status === "active" ? "admin-badge-green" : "admin-badge-gray"}`}>{l.status}</span></td>
                        <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(l.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              {tab === "reports" && (
                <table className="admin-table">
                  <thead><tr><th>ID</th><th>Reason</th><th>Status</th><th>Created</th></tr></thead>
                  <tbody>
                    {(tabData as Report[]).map((r) => (
                      <tr key={r.id}>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{r.id.slice(0, 8)}…</td>
                        <td>{r.reason}</td>
                        <td><span className={`admin-badge ${r.status === "open" ? "admin-badge-yellow" : "admin-badge-green"}`}>{r.status}</span></td>
                        <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(r.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              {tab === "moderation" && (
                <table className="admin-table">
                  <thead><tr><th>Case ID</th><th>Type</th><th>Status</th><th>Created</th></tr></thead>
                  <tbody>
                    {(tabData as ModerationCase[]).map((c) => (
                      <tr key={c.id}>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{c.id.slice(0, 8)}…</td>
                        <td>{c.case_type}</td>
                        <td><span className={`admin-badge ${c.status === "open" ? "admin-badge-yellow" : "admin-badge-green"}`}>{c.status}</span></td>
                        <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(c.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              {(tab === "audit" || tab === "sessions") && (
                <table className="admin-table">
                  <thead><tr><th>Entry</th></tr></thead>
                  <tbody>
                    {tabData.map((item, i) => (
                      <tr key={i}><td><pre style={{ margin: 0, fontSize: ".75rem" }}>{JSON.stringify(item, null, 2)}</pre></td></tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      )}

      {actionModal && (
        <div className="admin-modal-backdrop">
          <div className="admin-modal">
            <div className="admin-modal-header">
              <h2 style={{ margin: 0, fontSize: "1rem" }}>{actionModal.label} User</h2>
              <button className="admin-btn admin-btn-secondary admin-btn-sm" onClick={() => setActionModal(null)}>✕</button>
            </div>
            <p style={{ fontSize: ".875rem", color: "#5c6670", marginBottom: "1rem" }}>
              {actionModal.label} <strong>{user.name ?? user.email}</strong>?
            </p>
            {actionModal.type === "suspend" && (
              <div style={{ marginBottom: "1rem" }}>
                <label style={{ fontSize: ".8rem", fontWeight: 500, display: "block", marginBottom: ".375rem" }}>Duration</label>
                <select className="admin-select" value={duration} onChange={(e) => setDuration(e.target.value)}>
                  <option value="1d">1 day</option>
                  <option value="7d">7 days</option>
                  <option value="30d">30 days</option>
                  <option value="permanent">Permanent</option>
                </select>
              </div>
            )}
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ fontSize: ".8rem", fontWeight: 500, display: "block", marginBottom: ".375rem" }}>Reason</label>
              <textarea
                className="admin-input"
                rows={3}
                style={{ width: "100%", resize: "vertical" }}
                placeholder="Provide a reason..."
                value={actionReason}
                onChange={(e) => setActionReason(e.target.value)}
              />
            </div>
            <div style={{ display: "flex", gap: ".75rem", justifyContent: "flex-end" }}>
              <button className="admin-btn admin-btn-secondary" onClick={() => setActionModal(null)}>Cancel</button>
              <button
                className={`admin-btn ${actionModal.type === "ban" || actionModal.type === "suspend" ? "admin-btn-danger" : "admin-btn-primary"}`}
                onClick={handleAction}
                disabled={actionLoading}
              >
                {actionLoading ? "Processing…" : `Confirm ${actionModal.label}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
