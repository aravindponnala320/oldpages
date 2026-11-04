"use client";

import { useEffect, useState } from "react";

interface Community {
  id: string;
  name: string;
  community_type?: string;
  member_count?: number;
  status?: string;
  created_at: string;
  reports_count?: number;
}

interface ActionModal {
  communityId: string;
  communityName: string;
  action: "suspend" | "unsuspend";
}

export default function CommunitiesPage() {
  const [communities, setCommunities] = useState<Community[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [actionModal, setActionModal] = useState<ActionModal | null>(null);
  const [actionReason, setActionReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const LIMIT = 50;

  async function fetchCommunities() {
    setLoading(true);
    setError(null);
    setCommunities([]);
    setTotal(0);
    setLoading(false);
  }

  useEffect(() => { fetchCommunities(); }, [offset]);

  async function handleAction() {
    if (!actionModal) return;
    setActionLoading(true);
    setActionModal(null);
    setActionReason("");
    setActionLoading(false);
  }

  const totalPages = Math.ceil(total / LIMIT);
  const currentPage = Math.floor(offset / LIMIT) + 1;

  return (
    <div>
      <div className="admin-page-header">
        <h1 className="admin-page-title">Communities</h1>
        <span style={{ fontSize: ".875rem", color: "#5c6670" }}>{total} total</span>
      </div>

      {loading && <div style={{ display: "flex", justifyContent: "center", padding: "2rem" }}><span className="spinner" /></div>}

      {error && (
        <div style={{ background: "#fee2e2", color: "#991b1b", padding: ".75rem", borderRadius: 6, marginBottom: "1rem", fontSize: ".875rem" }}>
          {error}
        </div>
      )}

      {!loading && (
        <div className="admin-panel" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Members</th>
                  <th>Status</th>
                  <th>Reports</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {communities.length === 0 ? (
                  <tr><td colSpan={8} style={{ textAlign: "center", color: "#5c6670", padding: "2rem" }}>No communities found</td></tr>
                ) : communities.map((c) => (
                  <tr key={c.id}>
                    <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{c.id.slice(0, 8)}…</td>
                    <td style={{ fontWeight: 500 }}>{c.name}</td>
                    <td style={{ fontSize: ".8rem" }}>{c.community_type ?? "—"}</td>
                    <td>{c.member_count ?? 0}</td>
                    <td>
                      <span className={`admin-badge ${
                        c.status === "active" ? "admin-badge-green" :
                        c.status === "suspended" ? "admin-badge-yellow" : "admin-badge-gray"
                      }`}>{c.status ?? "active"}</span>
                    </td>
                    <td>
                      {(c.reports_count ?? 0) > 0
                        ? <span className="admin-badge admin-badge-red">{c.reports_count}</span>
                        : <span style={{ color: "#5c6670" }}>0</span>}
                    </td>
                    <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(c.created_at).toLocaleDateString()}</td>
                    <td>
                      <div style={{ display: "flex", gap: ".25rem" }}>
                        {c.status !== "suspended" ? (
                          <button
                            className="admin-btn admin-btn-danger admin-btn-sm"
                            onClick={() => setActionModal({ communityId: c.id, communityName: c.name, action: "suspend" })}
                          >
                            Suspend
                          </button>
                        ) : (
                          <button
                            className="admin-btn admin-btn-secondary admin-btn-sm"
                            onClick={() => setActionModal({ communityId: c.id, communityName: c.name, action: "unsuspend" })}
                          >
                            Unsuspend
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && totalPages > 1 && (
        <div style={{ display: "flex", gap: ".5rem", alignItems: "center", marginTop: "1rem", justifyContent: "flex-end" }}>
          <button className="admin-btn admin-btn-secondary admin-btn-sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - LIMIT))}>Previous</button>
          <span style={{ fontSize: ".875rem", color: "#5c6670" }}>Page {currentPage} of {totalPages}</span>
          <button className="admin-btn admin-btn-secondary admin-btn-sm" disabled={offset + LIMIT >= total} onClick={() => setOffset(offset + LIMIT)}>Next</button>
        </div>
      )}

      {actionModal && (
        <div className="admin-modal-backdrop">
          <div className="admin-modal">
            <div className="admin-modal-header">
              <h2 style={{ margin: 0, fontSize: "1rem", textTransform: "capitalize" }}>{actionModal.action} Community</h2>
              <button className="admin-btn admin-btn-secondary admin-btn-sm" onClick={() => setActionModal(null)}>✕</button>
            </div>
            <p style={{ fontSize: ".875rem", color: "#5c6670", marginBottom: "1rem" }}>
              {actionModal.action.charAt(0).toUpperCase() + actionModal.action.slice(1)}{" "}
              <strong>&quot;{actionModal.communityName}&quot;</strong>?
            </p>
            <textarea
              className="admin-input"
              rows={3}
              style={{ width: "100%", resize: "vertical" }}
              placeholder="Reason..."
              value={actionReason}
              onChange={(e) => setActionReason(e.target.value)}
            />
            <div style={{ display: "flex", gap: ".75rem", marginTop: "1rem", justifyContent: "flex-end" }}>
              <button className="admin-btn admin-btn-secondary" onClick={() => setActionModal(null)}>Cancel</button>
              <button
                className={`admin-btn ${actionModal.action === "suspend" ? "admin-btn-danger" : "admin-btn-primary"}`}
                onClick={handleAction}
                disabled={actionLoading}
              >
                {actionLoading ? "Processing…" : `Confirm ${actionModal.action}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
