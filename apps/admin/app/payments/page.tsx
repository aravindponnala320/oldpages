"use client";

import { useEffect, useState } from "react";
import { adminFetch } from "../../lib/api";

type PaymentsTab = "orders" | "payments" | "payouts" | "refunds" | "disputes";

interface PaymentStats {
  total_revenue?: number;
  pending_payouts?: number;
  active_disputes?: number;
  refunds_this_month?: number;
}

interface Order {
  id: string;
  buyer_email?: string;
  seller_email?: string;
  amount: number;
  status: string;
  created_at: string;
}

interface Payment {
  id: string;
  order_id?: string;
  amount: number;
  method?: string;
  status: string;
  created_at: string;
}

interface Payout {
  id: string;
  seller_email?: string;
  amount: number;
  status: string;
  created_at: string;
}

interface Refund {
  id: string;
  order_id?: string;
  amount: number;
  reason?: string;
  status: string;
  created_at: string;
}

interface Dispute {
  id: string;
  order_id?: string;
  reason?: string;
  status: string;
  created_at: string;
  buyer_email?: string;
  seller_email?: string;
}

interface ResolveModal {
  disputeId: string;
  resolution: "resolved_buyer" | "resolved_seller" | "";
}

export default function PaymentsPage() {
  const [tab, setTab] = useState<PaymentsTab>("orders");
  const stats: PaymentStats = {};
  const [data, setData] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolveModal, setResolveModal] = useState<ResolveModal | null>(null);
  const [resolveNote, setResolveNote] = useState("");
  const [resolveLoading, setResolveLoading] = useState(false);

  useEffect(() => {
    async function loadTab() {
      setLoading(true);
      setError(null);
      try {
        if (tab === "orders") {
          const res = await adminFetch<{ items: unknown[] }>("/orders?limit=50");
          setData(res.items ?? []);
          return;
        }
        setData([]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setLoading(false);
      }
    }
    loadTab();
  }, [tab]);

  async function handleResolveDispute() {
    if (!resolveModal || !resolveModal.resolution) return;
    setResolveLoading(true);
    setResolveModal(null);
    setResolveNote("");
    setResolveLoading(false);
  }

  const TABS: { key: PaymentsTab; label: string }[] = [
    { key: "orders", label: "Orders" },
    { key: "payments", label: "Payments" },
    { key: "payouts", label: "Payouts" },
    { key: "refunds", label: "Refunds" },
    { key: "disputes", label: "Disputes" },
  ];

  const statsCards = [
    { label: "Total Revenue", value: stats.total_revenue != null ? `₹${stats.total_revenue.toLocaleString()}` : "—" },
    { label: "Pending Payouts", value: stats.pending_payouts != null ? `₹${stats.pending_payouts.toLocaleString()}` : "—" },
    { label: "Active Disputes", value: stats.active_disputes ?? "—" },
    { label: "Refunds This Month", value: stats.refunds_this_month != null ? `₹${stats.refunds_this_month.toLocaleString()}` : "—" },
  ];

  return (
    <div>
      <div className="admin-page-header">
        <h1 className="admin-page-title">Payments</h1>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
        {statsCards.map((card) => (
          <div className="admin-stat-card" key={card.label}>
            <span className="admin-stat-number" style={{ fontSize: "1.5rem" }}>{card.value}</span>
            <span className="admin-stat-label">{card.label}</span>
          </div>
        ))}
      </div>

      <div className="admin-tabs">
        {TABS.map((t) => (
          <button key={t.key} className={`admin-tab${tab === t.key ? " active" : ""}`} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
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
            {tab === "orders" && (
              <table className="admin-table">
                <thead><tr><th>ID</th><th>Buyer</th><th>Seller</th><th>Amount</th><th>Status</th><th>Created</th></tr></thead>
                <tbody>
                  {(data as Order[]).length === 0
                    ? <tr><td colSpan={6} style={{ textAlign: "center", color: "#5c6670", padding: "2rem" }}>No orders</td></tr>
                    : (data as Order[]).map((o) => (
                      <tr key={o.id}>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{o.id.slice(0, 8)}…</td>
                        <td style={{ fontSize: ".8rem" }}>{o.buyer_email ?? "—"}</td>
                        <td style={{ fontSize: ".8rem" }}>{o.seller_email ?? "—"}</td>
                        <td>₹{o.amount}</td>
                        <td><span className={`admin-badge ${o.status === "completed" ? "admin-badge-green" : o.status === "pending" ? "admin-badge-yellow" : "admin-badge-gray"}`}>{o.status}</span></td>
                        <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(o.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            )}
            {tab === "payments" && (
              <table className="admin-table">
                <thead><tr><th>ID</th><th>Order ID</th><th>Amount</th><th>Method</th><th>Status</th><th>Created</th></tr></thead>
                <tbody>
                  {(data as Payment[]).length === 0
                    ? <tr><td colSpan={6} style={{ textAlign: "center", color: "#5c6670", padding: "2rem" }}>No payments</td></tr>
                    : (data as Payment[]).map((p) => (
                      <tr key={p.id}>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{p.id.slice(0, 8)}…</td>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{p.order_id ? p.order_id.slice(0, 8) + "…" : "—"}</td>
                        <td>₹{p.amount}</td>
                        <td>{p.method ?? "—"}</td>
                        <td><span className={`admin-badge ${p.status === "success" ? "admin-badge-green" : p.status === "pending" ? "admin-badge-yellow" : "admin-badge-gray"}`}>{p.status}</span></td>
                        <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(p.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            )}
            {tab === "payouts" && (
              <table className="admin-table">
                <thead><tr><th>ID</th><th>Seller</th><th>Amount</th><th>Status</th><th>Created</th></tr></thead>
                <tbody>
                  {(data as Payout[]).length === 0
                    ? <tr><td colSpan={5} style={{ textAlign: "center", color: "#5c6670", padding: "2rem" }}>No payouts</td></tr>
                    : (data as Payout[]).map((p) => (
                      <tr key={p.id}>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{p.id.slice(0, 8)}…</td>
                        <td style={{ fontSize: ".8rem" }}>{p.seller_email ?? "—"}</td>
                        <td>₹{p.amount}</td>
                        <td><span className={`admin-badge ${p.status === "paid" ? "admin-badge-green" : p.status === "pending" ? "admin-badge-yellow" : "admin-badge-gray"}`}>{p.status}</span></td>
                        <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(p.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            )}
            {tab === "refunds" && (
              <table className="admin-table">
                <thead><tr><th>ID</th><th>Order ID</th><th>Amount</th><th>Reason</th><th>Status</th><th>Created</th></tr></thead>
                <tbody>
                  {(data as Refund[]).length === 0
                    ? <tr><td colSpan={6} style={{ textAlign: "center", color: "#5c6670", padding: "2rem" }}>No refunds</td></tr>
                    : (data as Refund[]).map((r) => (
                      <tr key={r.id}>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{r.id.slice(0, 8)}…</td>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{r.order_id ? r.order_id.slice(0, 8) + "…" : "—"}</td>
                        <td>₹{r.amount}</td>
                        <td style={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.reason ?? "—"}</td>
                        <td><span className={`admin-badge ${r.status === "completed" ? "admin-badge-green" : r.status === "pending" ? "admin-badge-yellow" : "admin-badge-gray"}`}>{r.status}</span></td>
                        <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(r.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
            )}
            {tab === "disputes" && (
              <table className="admin-table">
                <thead><tr><th>ID</th><th>Order ID</th><th>Buyer</th><th>Seller</th><th>Reason</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead>
                <tbody>
                  {(data as Dispute[]).length === 0
                    ? <tr><td colSpan={8} style={{ textAlign: "center", color: "#5c6670", padding: "2rem" }}>No disputes</td></tr>
                    : (data as Dispute[]).map((d) => (
                      <tr key={d.id}>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{d.id.slice(0, 8)}…</td>
                        <td style={{ fontFamily: "monospace", fontSize: ".8rem" }}>{d.order_id ? d.order_id.slice(0, 8) + "…" : "—"}</td>
                        <td style={{ fontSize: ".8rem" }}>{d.buyer_email ?? "—"}</td>
                        <td style={{ fontSize: ".8rem" }}>{d.seller_email ?? "—"}</td>
                        <td style={{ maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{d.reason ?? "—"}</td>
                        <td><span className={`admin-badge ${d.status === "open" ? "admin-badge-yellow" : d.status === "resolved" ? "admin-badge-green" : "admin-badge-gray"}`}>{d.status}</span></td>
                        <td style={{ fontSize: ".8rem", color: "#5c6670" }}>{new Date(d.created_at).toLocaleDateString()}</td>
                        <td>
                          {d.status === "open" && (
                            <button className="admin-btn admin-btn-primary admin-btn-sm" onClick={() => setResolveModal({ disputeId: d.id, resolution: "" })}>
                              Resolve
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {resolveModal && (
        <div className="admin-modal-backdrop">
          <div className="admin-modal">
            <div className="admin-modal-header">
              <h2 style={{ margin: 0, fontSize: "1rem" }}>Resolve Dispute</h2>
              <button className="admin-btn admin-btn-secondary admin-btn-sm" onClick={() => setResolveModal(null)}>✕</button>
            </div>
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ fontSize: ".8rem", fontWeight: 500, display: "block", marginBottom: ".375rem" }}>Resolution</label>
              <select
                className="admin-select"
                style={{ width: "100%" }}
                value={resolveModal.resolution}
                onChange={(e) => setResolveModal({ ...resolveModal, resolution: e.target.value as "resolved_buyer" | "resolved_seller" })}
              >
                <option value="">Select resolution...</option>
                <option value="resolved_buyer">Favour Buyer</option>
                <option value="resolved_seller">Favour Seller</option>
              </select>
            </div>
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ fontSize: ".8rem", fontWeight: 500, display: "block", marginBottom: ".375rem" }}>Note</label>
              <textarea
                className="admin-input"
                rows={3}
                style={{ width: "100%", resize: "vertical" }}
                placeholder="Resolution notes..."
                value={resolveNote}
                onChange={(e) => setResolveNote(e.target.value)}
              />
            </div>
            <div style={{ display: "flex", gap: ".75rem", justifyContent: "flex-end" }}>
              <button className="admin-btn admin-btn-secondary" onClick={() => setResolveModal(null)}>Cancel</button>
              <button
                className="admin-btn admin-btn-primary"
                onClick={handleResolveDispute}
                disabled={resolveLoading || !resolveModal.resolution}
              >
                {resolveLoading ? "Resolving…" : "Confirm Resolution"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
