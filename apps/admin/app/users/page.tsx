"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface User {
  id: string;
  name?: string;
  email: string;
  created_at: string;
  listing_count?: number;
  is_verified?: boolean;
  status?: string;
}

interface SuspendModalState {
  userId: string;
  userName: string;
}

export default function UsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filterVerified, setFilterVerified] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [suspendModal, setSuspendModal] = useState<SuspendModalState | null>(null);
  const [suspendReason, setSuspendReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const LIMIT = 50;

  async function fetchUsers() {
    setLoading(true);
    setError(null);
    setUsers([]);
    setTotal(0);
    setLoading(false);
  }

  useEffect(() => { fetchUsers(); }, [offset, filterVerified, filterStatus]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setOffset(0);
    fetchUsers();
  }

  async function handleSuspend() {
    if (!suspendModal) return;
    setActionLoading(true);
    setSuspendModal(null);
    setSuspendReason("");
    setActionLoading(false);
  }

  const totalPages = Math.ceil(total / LIMIT);
  const currentPage = Math.floor(offset / LIMIT) + 1;

  return (
    <div>
      <div className="admin-page-header">
        <h1 className="admin-page-title">Users</h1>
        <span style={{ fontSize: ".875rem", color: "#5c6670" }}>{total} total</span>
      </div>

      <form onSubmit={handleSearch} className="admin-filter-bar">
        <input
          className="admin-input"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ minWidth: 240 }}
        />
        <select className="admin-select" value={filterVerified} onChange={(e) => { setFilterVerified(e.target.value); setOffset(0); }}>
          <option value="">All (verified)</option>
          <option value="true">Verified</option>
          <option value="false">Unverified</option>
        </select>
        <select className="admin-select" value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value); setOffset(0); }}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="banned">Banned</option>
        </select>
        <button className="admin-btn admin-btn-primary" type="submit">Search</button>
      </form>

      {loading && (
        <div style={{ display: "flex", justifyContent: "center", padding: "2rem" }}>
          <span className="spinner" />
        </div>
      )}

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
                  <th>Email</th>
                  <th>Joined</th>
                  <th>Listings</th>
                  <th>Verified</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr><td colSpan={8} style={{ textAlign: "center", color: "#5c6670", padding: "2rem" }}>No users found</td></tr>
                ) : users.map((user) => (
                  <tr
                    key={user.id}
                    style={{ cursor: "pointer" }}
                    onClick={() => router.push(`/users/${user.id}`)}
                  >
                    <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{user.id.slice(0, 8)}…</td>
                    <td>{user.name ?? "—"}</td>
                    <td>{user.email}</td>
                    <td style={{ color: "#5c6670", fontSize: ".8rem" }}>{new Date(user.created_at).toLocaleDateString()}</td>
                    <td>{user.listing_count ?? 0}</td>
                    <td>
                      {user.is_verified
                        ? <span className="admin-badge admin-badge-green">Verified</span>
                        : <span className="admin-badge admin-badge-gray">No</span>}
                    </td>
                    <td>
                      <span className={`admin-badge ${
                        user.status === "active" ? "admin-badge-green" :
                        user.status === "suspended" ? "admin-badge-yellow" :
                        user.status === "banned" ? "admin-badge-red" : "admin-badge-gray"
                      }`}>{user.status ?? "active"}</span>
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <button
                        className="admin-btn admin-btn-danger admin-btn-sm"
                        onClick={() => setSuspendModal({ userId: user.id, userName: user.name ?? user.email })}
                      >
                        Suspend
                      </button>
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

      {suspendModal && (
        <div className="admin-modal-backdrop">
          <div className="admin-modal">
            <div className="admin-modal-header">
              <h2 style={{ margin: 0, fontSize: "1rem" }}>Suspend User</h2>
              <button className="admin-btn admin-btn-secondary admin-btn-sm" onClick={() => setSuspendModal(null)}>✕</button>
            </div>
            <p style={{ fontSize: ".875rem", color: "#5c6670", marginBottom: "1rem" }}>
              Suspending <strong>{suspendModal.userName}</strong>. Provide a reason:
            </p>
            <textarea
              className="admin-input"
              rows={3}
              style={{ width: "100%", resize: "vertical" }}
              placeholder="Reason for suspension..."
              value={suspendReason}
              onChange={(e) => setSuspendReason(e.target.value)}
            />
            <div style={{ display: "flex", gap: ".75rem", marginTop: "1rem", justifyContent: "flex-end" }}>
              <button className="admin-btn admin-btn-secondary" onClick={() => setSuspendModal(null)}>Cancel</button>
              <button className="admin-btn admin-btn-danger" onClick={handleSuspend} disabled={actionLoading}>
                {actionLoading ? "Suspending…" : "Suspend User"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
