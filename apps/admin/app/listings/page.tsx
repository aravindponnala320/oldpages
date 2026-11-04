"use client";

import { useEffect, useState } from "react";

interface Listing {
  id: string;
  title: string;
  seller_email?: string;
  seller_name?: string;
  price?: number;
  status: string;
  created_at: string;
  flags_count?: number;
}

interface ActionModal {
  listingId: string;
  listingTitle: string;
  action: "suspend" | "approve" | "remove";
}

export default function ListingsPage() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState("");
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [actionModal, setActionModal] = useState<ActionModal | null>(null);
  const [actionReason, setActionReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const LIMIT = 50;

  async function fetchListings() {
    setLoading(true);
    setError(null);
    setListings([]);
    setTotal(0);
    setLoading(false);
  }

  useEffect(() => { fetchListings(); }, [offset, filterStatus, flaggedOnly]);

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
        <h1 className="admin-page-title">Listings</h1>
        <span style={{ fontSize: ".875rem", color: "#5c6670" }}>{total} total</span>
      </div>

      <div className="admin-filter-bar">
        <select className="admin-select" value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value); setOffset(0); }}>
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="rejected">Rejected</option>
          <option value="sold">Sold</option>
        </select>
        <label style={{ display: "flex", alignItems: "center", gap: ".5rem", fontSize: ".875rem", cursor: "pointer" }}>
          <input type="checkbox" checked={flaggedOnly} onChange={(e) => { setFlaggedOnly(e.target.checked); setOffset(0); }} />
          Flagged only
        </label>
        <input className="admin-input" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} placeholder="From" />
        <input className="admin-input" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} placeholder="To" />
        <button className="admin-btn admin-btn-primary" onClick={() => { setOffset(0); fetchListings(); }}>Apply</button>
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
                  <th>Title</th>
                  <th>Seller</th>
                  <th>Price</th>
                  <th>Status</th>
                  <th>Flags</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {listings.length === 0 ? (
                  <tr><td colSpan={8} style={{ textAlign: "center", color: "#5c6670", padding: "2rem" }}>No listings found</td></tr>
                ) : listings.map((listing) => (
                  <tr key={listing.id}>
                    <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{listing.id.slice(0, 8)}…</td>
                    <td style={{ maxWidth: 240, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{listing.title}</td>
                    <td style={{ fontSize: ".8rem" }}>{listing.seller_name ?? listing.seller_email ?? "—"}</td>
                    <td>{listing.price != null ? `₹${listing.price}` : "—"}</td>
                    <td>
                      <span className={`admin-badge ${
                        listing.status === "active" ? "admin-badge-green" :
                        listing.status === "suspended" ? "admin-badge-yellow" :
                        listing.status === "rejected" ? "admin-badge-red" : "admin-badge-gray"
                      }`}>{listing.status}</span>
                    </td>
                    <td>
                      {(listing.flags_count ?? 0) > 0
                        ? <span className="admin-badge admin-badge-red">{listing.flags_count}</span>
                        : <span style={{ color: "#5c6670" }}>0</span>}
                    </td>
                    <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(listing.created_at).toLocaleDateString()}</td>
                    <td>
                      <div style={{ display: "flex", gap: ".25rem" }}>
                        <button className="admin-btn admin-btn-secondary admin-btn-sm" onClick={() => setActionModal({ listingId: listing.id, listingTitle: listing.title, action: "approve" })}>Approve</button>
                        <button className="admin-btn admin-btn-danger admin-btn-sm" onClick={() => setActionModal({ listingId: listing.id, listingTitle: listing.title, action: "suspend" })}>Suspend</button>
                        <button className="admin-btn admin-btn-danger admin-btn-sm" onClick={() => setActionModal({ listingId: listing.id, listingTitle: listing.title, action: "remove" })}>Remove</button>
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
              <h2 style={{ margin: 0, fontSize: "1rem", textTransform: "capitalize" }}>{actionModal.action} Listing</h2>
              <button className="admin-btn admin-btn-secondary admin-btn-sm" onClick={() => setActionModal(null)}>✕</button>
            </div>
            <p style={{ fontSize: ".875rem", color: "#5c6670", marginBottom: "1rem" }}>
              {actionModal.action.charAt(0).toUpperCase() + actionModal.action.slice(1)}{" "}
              <strong>&quot;{actionModal.listingTitle}&quot;</strong>?
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
                className={`admin-btn ${actionModal.action === "approve" ? "admin-btn-primary" : "admin-btn-danger"}`}
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
