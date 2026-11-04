"use client";

import { useEffect, useState } from "react";
import { adminFetch } from "../../lib/api";

type ApprovalStatus = "pending" | "active" | "rejected";

interface Institution {
  id: string;
  name: string;
  type: string;
  status: ApprovalStatus;
  owner_user_id: string | null;
  city: string | null;
  state: string | null;
  description: string | null;
  website: string | null;
  created_at: string;
  rejected_reason: string | null;
}

interface Business {
  id: string;
  name: string;
  type: string;
  status: ApprovalStatus;
  owner_user_id: string;
  description: string | null;
  website: string | null;
  gstin: string | null;
  created_at: string;
  rejected_reason: string | null;
}

type Tab = "institutions" | "businesses";

export default function ApprovalsPage() {
  const [tab, setTab] = useState<Tab>("institutions");
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [rejectTarget, setRejectTarget] = useState<{ id: string; type: Tab } | null>(null);
  const [rejectReason, setRejectReason] = useState("");

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [instData, bizData] = await Promise.all([
        adminFetch<{ items: Institution[] }>("/institutions/pending?limit=50"),
        adminFetch<Business[]>("/business/pending?limit=50"),
      ]);
      setInstitutions(instData.items ?? []);
      setBusinesses(bizData ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load pending approvals");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleApprove(id: string, type: Tab) {
    setActionLoading(id);
    try {
      const path = type === "institutions"
        ? `/institutions/${id}/approve`
        : `/business/${id}/approve`;
      await adminFetch(path, { method: "POST" });
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to approve");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleReject() {
    if (!rejectTarget) return;
    setActionLoading(rejectTarget.id);
    try {
      const path = rejectTarget.type === "institutions"
        ? `/institutions/${rejectTarget.id}/reject`
        : `/business/${rejectTarget.id}/reject`;
      await adminFetch(path, {
        method: "POST",
        body: JSON.stringify({ reason: rejectReason || null }),
      });
      setRejectTarget(null);
      setRejectReason("");
      await loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to reject");
    } finally {
      setActionLoading(null);
    }
  }

  const currentItems = tab === "institutions" ? institutions : businesses;
  const isEmpty = currentItems.length === 0;

  return (
    <div>
      <div className="admin-page-header">
        <h1 className="admin-page-title">Pending Approvals</h1>
        <span style={{ fontSize: ".875rem", color: "#5c6670" }}>
          {institutions.length} institutions · {businesses.length} businesses pending
        </span>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: ".5rem", marginBottom: "1.25rem", borderBottom: "1px solid #d9ddd6", paddingBottom: ".75rem" }}>
        {(["institutions", "businesses"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: ".4rem .9rem",
              borderRadius: 6,
              border: "1px solid",
              fontSize: ".875rem",
              fontWeight: 500,
              cursor: "pointer",
              borderColor: tab === t ? "#1f2933" : "#d9ddd6",
              background: tab === t ? "#1f2933" : "#fff",
              color: tab === t ? "#fff" : "#1f2933",
            }}
          >
            {t === "institutions" ? "Institutions" : "Businesses"}
            {" "}
            <span style={{
              background: tab === t ? "rgba(255,255,255,0.2)" : "#f0f0ee",
              borderRadius: 10,
              padding: "1px 7px",
              fontSize: ".75rem",
              marginLeft: 4,
            }}>
              {t === "institutions" ? institutions.length : businesses.length}
            </span>
          </button>
        ))}
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

      {!loading && isEmpty && (
        <div className="admin-panel" style={{ padding: "3rem", textAlign: "center", color: "#5c6670" }}>
          <div style={{ fontSize: "2rem", marginBottom: ".5rem" }}>✓</div>
          <p style={{ margin: 0, fontSize: ".875rem" }}>
            No pending {tab} to review.
          </p>
        </div>
      )}

      {!loading && !isEmpty && (
        <div className="admin-panel" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Owner ID</th>
                  {tab === "institutions" && <th>Location</th>}
                  <th>Description</th>
                  <th>Submitted</th>
                  <th style={{ width: 180 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {currentItems.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <div style={{ fontWeight: 600, fontSize: ".875rem" }}>{item.name}</div>
                      {item.website && (
                        <a href={item.website} target="_blank" rel="noreferrer" style={{ fontSize: ".75rem", color: "#5c6670" }}>
                          {item.website}
                        </a>
                      )}
                    </td>
                    <td>
                      <span className="admin-badge admin-badge-blue">{item.type}</span>
                    </td>
                    <td style={{ fontFamily: "monospace", fontSize: ".75rem", color: "#5c6670" }}>
                      {item.owner_user_id?.slice(0, 12)}…
                    </td>
                    {tab === "institutions" && (
                      <td style={{ fontSize: ".8rem", color: "#5c6670" }}>
                        {[(item as Institution).city, (item as Institution).state].filter(Boolean).join(", ") || "—"}
                      </td>
                    )}
                    <td style={{ fontSize: ".8rem", color: "#5c6670", maxWidth: 220 }}>
                      {item.description
                        ? item.description.length > 80
                          ? item.description.slice(0, 80) + "…"
                          : item.description
                        : <span style={{ color: "#9ca3af" }}>No description</span>}
                    </td>
                    <td style={{ fontSize: ".8rem", color: "#5c6670" }}>
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: ".5rem" }}>
                        <button
                          className="admin-btn admin-btn-sm"
                          style={{ background: "#16a34a", color: "#fff", border: "none" }}
                          disabled={actionLoading === item.id}
                          onClick={() => handleApprove(item.id, tab)}
                        >
                          {actionLoading === item.id ? "…" : "Approve"}
                        </button>
                        <button
                          className="admin-btn admin-btn-secondary admin-btn-sm"
                          style={{ borderColor: "#dc2626", color: "#dc2626" }}
                          disabled={actionLoading === item.id}
                          onClick={() => {
                            setRejectTarget({ id: item.id, type: tab });
                            setRejectReason("");
                          }}
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {rejectTarget && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)",
          display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
        }}>
          <div style={{
            background: "#fff", borderRadius: 8, padding: "1.5rem",
            width: "100%", maxWidth: 440, boxShadow: "0 20px 60px rgba(0,0,0,0.2)",
          }}>
            <h3 style={{ margin: "0 0 .25rem", fontSize: "1rem", fontWeight: 700 }}>Reject Application</h3>
            <p style={{ margin: "0 0 1rem", fontSize: ".875rem", color: "#5c6670" }}>
              Optionally provide a reason. The applicant will see this.
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Incomplete information, please resubmit with a valid website and description."
              rows={4}
              style={{
                width: "100%", border: "1px solid #d9ddd6", borderRadius: 6,
                padding: ".625rem", fontSize: ".875rem", resize: "vertical",
                fontFamily: "inherit", boxSizing: "border-box",
              }}
            />
            <div style={{ display: "flex", gap: ".5rem", marginTop: "1rem", justifyContent: "flex-end" }}>
              <button
                className="admin-btn admin-btn-secondary"
                onClick={() => setRejectTarget(null)}
                disabled={!!actionLoading}
              >
                Cancel
              </button>
              <button
                className="admin-btn"
                style={{ background: "#dc2626", color: "#fff", border: "none" }}
                onClick={handleReject}
                disabled={!!actionLoading}
              >
                {actionLoading ? "…" : "Confirm Reject"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
