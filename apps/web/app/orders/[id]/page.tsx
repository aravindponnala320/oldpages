"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../../contexts/AuthContext";
import { getAccessToken } from "../../../lib/auth";
import { Container, LinkButton, Spinner, colors, font, radius } from "../../../components/ui";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const WS_BASE = typeof window !== "undefined"
  ? `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host.replace(/:\d+$/, ":8000")}`
  : "ws://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────

type TxnStatus = "reserved" | "ready_for_pickup" | "completed" | "cancelled" | "disputed";
type PickupStatus = "proposed" | "confirmed" | "completed" | "cancelled";

interface UserSummary { id: string; display_name?: string | null; }
interface Pickup {
  id: string;
  status: PickupStatus;
  public_location_label: string;
  exact_address: string | null;
  exact_latitude: string | null;
  exact_longitude: string | null;
  handover_code: string | null;
  proposed_start_at: string | null;
  proposed_end_at: string | null;
  confirmed_at: string | null;
  confirmed_by_user_id: string | null;
  proposed_by_user_id: string;
  pickup_notes_private: string | null;
  transaction_id: string;
}
interface Transaction {
  id: string;
  status: TxnStatus;
  amount_cents: number | null;
  currency: string;
  fulfillment_method: string;
  quantity: number;
  buyer: UserSummary;
  seller: UserSummary;
  listing_id: string;
  offer_id: string;
  pickup: Pickup | null;
  created_at: string;
  completed_at: string | null;
  cancellation_reason: string | null;
  cancelled_at: string | null;
  cancelled_by_user_id: string | null;
  buyer_marked_received_at: string | null;
  seller_marked_delivered_at: string | null;
}
interface ListingLite {
  id: string;
  title: string;
  price_amount_cents: number | null;
  currency: string;
  image_url: string | null;
  location: { city: string; state?: string; public_area?: string } | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function getCurrentUserId(): string | null {
  const token = getAccessToken();
  if (!token) return null;
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    return JSON.parse(atob(payload)).sub ?? null;
  } catch { return null; }
}

function formatPrice(cents: number | null | undefined, currency: string): string {
  if (cents == null) return "—";
  return `${currency === "INR" ? "₹" : currency}${(cents / 100).toLocaleString("en-IN")}`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

const STEPS: { key: TxnStatus; label: string; desc: string; icon: string }[] = [
  { key: "reserved",         label: "Order Placed",     desc: "Waiting for pickup arrangement", icon: "📝" },
  { key: "ready_for_pickup", label: "Ready for Pickup", desc: "Meet and exchange the book",     icon: "🤝" },
  { key: "completed",        label: "Completed",         desc: "Book handed over successfully",   icon: "✓" },
];

// ── Main ───────────────────────────────────────────────────────────────────

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  const [order, setOrder] = useState<Transaction | null>(null);
  const [listing, setListing] = useState<ListingLite | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showPickupModal, setShowPickupModal] = useState(false);
  const [showHandoverModal, setShowHandoverModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [showReceivedConfirm, setShowReceivedConfirm] = useState(false);
  const [showDeliveredConfirm, setShowDeliveredConfirm] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [handoverCode, setHandoverCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [connStatus, setConnStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Pickup form
  const [pickupLocation, setPickupLocation] = useState("");
  const [pickupAddress, setPickupAddress] = useState("");
  const [pickupDate, setPickupDate] = useState("");
  const [pickupTime, setPickupTime] = useState("");
  const [pickupNotes, setPickupNotes] = useState("");

  const currentUserId = getCurrentUserId();

  const loadOrder = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !id) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/transactions/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error("Order not found");
      const data: Transaction = await res.json();
      setOrder(data);
      // Load listing details
      const lres = await fetch(`${API_BASE}/api/v1/listings/${data.listing_id}`, { headers: { Authorization: `Bearer ${token}` } });
      if (lres.ok) {
        const l = await lres.json();
        setListing({
          id: l.id,
          title: l.title ?? l.book?.title ?? "Listing",
          price_amount_cents: l.price_amount_cents,
          currency: l.currency ?? "INR",
          image_url: l.images?.find((i: { is_primary: boolean; public_url?: string }) => i.is_primary)?.public_url ?? l.images?.[0]?.public_url ?? null,
          location: l.location ?? null,
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load order");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) { router.replace("/login"); return; }
    if (!isAuthenticated) return;
    loadOrder();
  }, [isAuthenticated, isLoading, loadOrder, router]);

  // ── WebSocket for real-time order updates ──────────────────────────
  useEffect(() => {
    if (!isAuthenticated || !id) return;

    function connect() {
      const token = getAccessToken();
      if (!token) return;
      if (wsRef.current) wsRef.current.close();

      setConnStatus("connecting");
      const ws = new WebSocket(`${WS_BASE}/ws/conversations?access_token=${token}`);
      wsRef.current = ws;

      ws.onopen = () => setConnStatus("connected");
      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data as string);
          if (data.type === "transaction.updated" && data.transaction?.id === id) {
            setOrder(data.transaction);
          }
        } catch { /* ignore */ }
      };
      ws.onclose = () => {
        setConnStatus("disconnected");
        reconnectTimer.current = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
    }

    connect();
    const ping = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 30_000);

    return () => {
      clearInterval(ping);
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [isAuthenticated, id]);

  const isBuyer = !!order && currentUserId === order.buyer.id;
  const isSeller = !!order && currentUserId === order.seller.id;

  // ── Actions ──────────────────────────────────────────────────────────

  async function handleProposePickup() {
    if (!order || !pickupLocation.trim()) return;
    const token = getAccessToken();
    if (!token) return;
    setSubmitting(true); setError(null);
    try {
      const startAt = pickupDate && pickupTime ? new Date(`${pickupDate}T${pickupTime}`).toISOString() : null;
      const endAt = startAt ? new Date(new Date(startAt).getTime() + 60 * 60 * 1000).toISOString() : null;
      const res = await fetch(`${API_BASE}/api/v1/pickups`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          transaction_id: order.id,
          public_location_label: pickupLocation.trim(),
          exact_address: pickupAddress.trim() || null,
          proposed_start_at: startAt,
          proposed_end_at: endAt,
          pickup_notes_private: pickupNotes.trim() || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to propose pickup");
      setSuccess("Pickup proposed! The other party can now confirm.");
      setShowPickupModal(false);
      setPickupLocation(""); setPickupAddress(""); setPickupDate(""); setPickupTime(""); setPickupNotes("");
      await loadOrder();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setSubmitting(false); }
  }

  async function handleConfirmPickup() {
    if (!order?.pickup) return;
    const token = getAccessToken();
    if (!token) return;
    setSubmitting(true); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/pickups/${order.pickup.id}/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({}),
      });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail ?? "Failed"); }
      setSuccess("Pickup confirmed! You'll get a handover code to exchange in person.");
      await loadOrder();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setSubmitting(false); }
  }

  async function handleComplete() {
    if (!order) return;
    const token = getAccessToken();
    if (!token) return;
    setSubmitting(true); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/transactions/${order.id}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ handover_code: handoverCode.trim() || null }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Invalid code");
      setSuccess("Transaction completed! 🎉 Thanks for using OldPages.");
      setShowHandoverModal(false); setHandoverCode("");
      await loadOrder();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setSubmitting(false); }
  }

  async function handleCancel() {
    if (!order) return;
    const token = getAccessToken();
    if (!token) return;
    setSubmitting(true); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/transactions/${order.id}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ reason: cancelReason.trim() || null }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to cancel");
      setSuccess("Order cancelled.");
      setShowCancelModal(false); setCancelReason("");
      await loadOrder();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setSubmitting(false); }
  }

  async function handleMarkReceived() {
    if (!order) return;
    const token = getAccessToken();
    if (!token) return;
    setSubmitting(true); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/transactions/${order.id}/mark-received`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed");
      setSuccess(data.status === "completed" ? "🎉 Order complete! Book received." : "Marked as received. Waiting for seller to confirm delivery.");
      setShowReceivedConfirm(false);
      await loadOrder();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setSubmitting(false); }
  }

  async function handleMarkDelivered() {
    if (!order) return;
    const token = getAccessToken();
    if (!token) return;
    setSubmitting(true); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/transactions/${order.id}/mark-delivered`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed");
      setSuccess(data.status === "completed" ? "🎉 Order complete! Both parties confirmed." : "Marked as delivered. Waiting for buyer to confirm receipt.");
      setShowDeliveredConfirm(false);
      await loadOrder();
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setSubmitting(false); }
  }

  // ── Loading ──────────────────────────────────────────────────────────

  if (isLoading || loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (!order) {
    return (
      <div style={{ padding: "40px 0" }}>
        <Container maxWidth={640}>
          <div style={{
            padding: 32, textAlign: "center",
            background: colors.surface, borderRadius: radius.xl, border: `1px solid ${colors.border}`,
          }}>
            <h1 style={{ margin: "0 0 8px", fontSize: font.size.xl, fontWeight: font.weight.bold, color: colors.text }}>Order not found</h1>
            <p style={{ color: colors.textSubtle, margin: "0 0 20px" }}>
              {error ?? "This order doesn't exist or you don't have access."}
            </p>
            <LinkButton href="/orders">← Back to Orders</LinkButton>
          </div>
        </Container>
      </div>
    );
  }

  const currentStepIndex = STEPS.findIndex((s) => s.key === order.status);
  const otherParty = isBuyer ? order.seller : order.buyer;
  const otherName = otherParty.display_name ?? `User ${otherParty.id.slice(0, 8)}`;

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={820}>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <Link href="/orders" style={{ fontSize: font.size.sm, color: colors.textSubtle, textDecoration: "none" }}>← All Orders</Link>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div
              style={{
                width: 8, height: 8, borderRadius: "50%",
                background: connStatus === "connected" ? colors.success : connStatus === "connecting" ? colors.warning : colors.danger,
                transition: "background 0.3s",
              }}
            />
            <span style={{ fontSize: font.size.xs, color: colors.textFaint }}>
              {connStatus === "connected" ? "Live updates" : connStatus === "connecting" ? "Connecting…" : "Offline"}
            </span>
          </div>
        </div>

        {error && (
          <div style={{ background: colors.dangerSoft, border: `1px solid #fecaca`, borderRadius: radius.md, padding: "10px 14px", marginBottom: 12 }}>
            <p style={{ color: colors.dangerText, fontSize: font.size.sm, margin: 0 }}>{error}</p>
          </div>
        )}
        {success && (
          <div style={{ background: colors.successSoft, border: `1px solid #bbf7d0`, borderRadius: radius.md, padding: "10px 14px", marginBottom: 12 }}>
            <p style={{ color: colors.successText, fontSize: font.size.sm, margin: 0 }}>{success}</p>
          </div>
        )}

        {/* Header card */}
        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: "1.5rem", marginBottom: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem", marginBottom: "1rem", flexWrap: "wrap" }}>
            <div>
              <p style={{ fontSize: "0.75rem", color: "#6b7280", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", margin: 0 }}>
                Order #{order.id.slice(0, 12)}
              </p>
              <p style={{ fontSize: "1.5rem", fontWeight: 800, color: "#1f2933", margin: "0.25rem 0 0", letterSpacing: "-0.02em" }}>
                {formatPrice(order.amount_cents, order.currency)}
              </p>
              <p style={{ fontSize: "0.8rem", color: "#6b7280", margin: "0.2rem 0 0" }}>
                Placed on {formatDate(order.created_at)}
              </p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "0.375rem" }}>
              <span style={{ background: "#eaf2ff", color: "#065f46", fontSize: "0.75rem", fontWeight: 700, padding: "0.3rem 0.7rem", borderRadius: 20 }}>
                {isBuyer ? "You're buying" : "You're selling"}
              </span>
              <span style={{ fontSize: "0.7rem", color: "#6b7280" }}>
                {order.fulfillment_method === "pickup" ? "🤝 In-person pickup" : "📦 Shipping"}
              </span>
            </div>
          </div>

          {/* Listing preview */}
          {listing && (
            <Link href={`/listings/${listing.id}`} style={{ textDecoration: "none" }}>
              <div style={{ display: "flex", gap: "0.875rem", padding: "0.875rem", background: "#f9fafb", borderRadius: 8, alignItems: "center", transition: "background 0.1s" }}
                onMouseEnter={(e) => (e.currentTarget as HTMLDivElement).style.background = "#eaf2ff"}
                onMouseLeave={(e) => (e.currentTarget as HTMLDivElement).style.background = "#f9fafb"}
              >
                <div style={{ width: 44, height: 56, borderRadius: 6, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid #e5e7eb", flexShrink: 0, overflow: "hidden" }}>
                  {listing.image_url ? <img src={listing.image_url} alt={listing.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : <span style={{ fontSize: "1.25rem" }}>📚</span>}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ margin: 0, fontWeight: 700, fontSize: "0.9rem", color: "#1f2933" }}>{listing.title}</p>
                  <p style={{ margin: "0.15rem 0 0", fontSize: "0.75rem", color: "#6b7280" }}>
                    {listing.location?.city ? `📍 ${listing.location.city}` : "View listing details"}
                  </p>
                </div>
                <span style={{ color: "#9ca3af", fontSize: "0.9rem" }}>→</span>
              </div>
            </Link>
          )}
        </div>

        {/* Status timeline */}
        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: "1.5rem", marginBottom: "1rem" }}>
          <h2 style={{ fontSize: "0.875rem", fontWeight: 700, color: "#374151", margin: "0 0 1.25rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Order Status</h2>
          <div style={{ display: "flex", justifyContent: "space-between", position: "relative" }}>
            {/* Line */}
            <div style={{ position: "absolute", top: 20, left: "10%", right: "10%", height: 3, background: "#e5e7eb", zIndex: 0 }} />
            <div style={{ position: "absolute", top: 20, left: "10%", width: `${Math.max(0, (currentStepIndex / (STEPS.length - 1)) * 80)}%`, height: 3, background: "#2563eb", zIndex: 0, transition: "width 0.3s" }} />

            {STEPS.map((step, i) => {
              const isDone = i <= currentStepIndex;
              const isCurrent = i === currentStepIndex;
              return (
                <div key={step.key} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "0.5rem", flex: 1, zIndex: 1, position: "relative" }}>
                  <div style={{ width: 40, height: 40, borderRadius: "50%", background: isDone ? "#2563eb" : "#fff", border: `3px solid ${isDone ? "#2563eb" : "#e5e7eb"}`, display: "flex", alignItems: "center", justifyContent: "center", color: isDone ? "white" : "#9ca3af", fontSize: "1rem", fontWeight: 700, transition: "all 0.3s" }}>
                    {isDone ? "✓" : i + 1}
                  </div>
                  <div style={{ textAlign: "center", maxWidth: 130 }}>
                    <p style={{ fontSize: "0.78rem", fontWeight: isCurrent ? 700 : 600, color: isDone ? "#1f2933" : "#9ca3af", margin: 0 }}>
                      {step.label}
                    </p>
                    <p style={{ fontSize: "0.7rem", color: "#6b7280", margin: "0.15rem 0 0", lineHeight: 1.4 }}>
                      {step.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Other party card */}
        <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: "1.25rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.875rem" }}>
          <div style={{ width: 44, height: 44, borderRadius: "50%", background: "#2563eb", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontSize: "0.9rem", fontWeight: 700 }}>
            {otherName.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase()}
          </div>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: "0.7rem", color: "#6b7280", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", margin: 0 }}>
              {isBuyer ? "Seller" : "Buyer"}
            </p>
            <p style={{ margin: "0.15rem 0 0", fontSize: "0.95rem", fontWeight: 700, color: "#1f2933" }}>{otherName}</p>
          </div>
          <Link href={`/inbox`} style={{ background: "#eaf2ff", border: "1px solid #a7f3d0", color: "#2563eb", padding: "0.5rem 0.875rem", borderRadius: 8, fontSize: "0.78rem", fontWeight: 600, textDecoration: "none" }}>
            💬 Message
          </Link>
        </div>

        {/* Pickup section — only for pickup orders */}
        {order.fulfillment_method === "pickup" && order.status !== "completed" && order.status !== "cancelled" && (
          <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: "1.5rem", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#1f2933", margin: "0 0 1rem" }}>Pickup Arrangement</h2>

            {!order.pickup && (
              <>
                <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: "0 0 1rem" }}>
                  {isSeller ? "Propose a safe public place to meet the buyer." : "Waiting for the seller to propose a pickup location."}
                </p>
                {isSeller && (
                  <button onClick={() => setShowPickupModal(true)} style={{ background: "#2563eb", color: "white", border: "none", padding: "0.75rem 1.5rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer" }}>
                    📍 Propose Pickup Location
                  </button>
                )}
              </>
            )}

            {order.pickup && (
              <div style={{ background: "#eaf2ff", border: "1px solid #a7f3d0", borderRadius: 10, padding: "1.25rem", marginBottom: "1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem", flexWrap: "wrap", gap: "0.5rem" }}>
                  <p style={{ fontWeight: 700, color: "#065f46", fontSize: "0.9rem", margin: 0 }}>
                    📍 {order.pickup.public_location_label}
                  </p>
                  <span style={{ fontSize: "0.7rem", background: order.pickup.status === "confirmed" || order.pickup.status === "completed" ? "#2563eb" : "#f59e0b", color: "white", padding: "0.2rem 0.55rem", borderRadius: 20, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.03em" }}>
                    {order.pickup.status}
                  </span>
                </div>
                {order.pickup.exact_address && (
                  <p style={{ fontSize: "0.8rem", color: "#374151", margin: "0 0 0.5rem" }}>
                    <strong>Address:</strong> {order.pickup.exact_address}
                  </p>
                )}
                {order.pickup.proposed_start_at && (
                  <p style={{ fontSize: "0.8rem", color: "#374151", margin: "0 0 0.5rem" }}>
                    <strong>When:</strong> {formatDate(order.pickup.proposed_start_at)}
                  </p>
                )}
                {order.pickup.pickup_notes_private && (
                  <p style={{ fontSize: "0.8rem", color: "#374151", margin: "0 0 0.5rem", fontStyle: "italic" }}>
                    Notes: {order.pickup.pickup_notes_private}
                  </p>
                )}

                {/* Handover code — shown to both parties once confirmed */}
                {order.pickup.handover_code && (order.pickup.status === "confirmed" || order.pickup.status === "completed") && (
                  <div style={{ background: "#fff", border: "2px dashed #2563eb", borderRadius: 8, padding: "1rem", marginTop: "0.75rem", textAlign: "center" }}>
                    <p style={{ fontSize: "0.7rem", color: "#6b7280", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 0.375rem" }}>
                      Handover Code
                    </p>
                    <p style={{ fontSize: "1.75rem", fontWeight: 800, color: "#2563eb", letterSpacing: "0.3em", margin: 0, fontFamily: "monospace" }}>
                      {order.pickup.handover_code}
                    </p>
                    <p style={{ fontSize: "0.72rem", color: "#6b7280", margin: "0.5rem 0 0" }}>
                      {isBuyer
                        ? "Share this with the seller when you receive the book"
                        : "Enter this code to complete the transaction"}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Actions based on pickup state */}
            {order.pickup && order.pickup.status === "proposed" && (
              <>
                {order.pickup.proposed_by_user_id !== currentUserId && (
                  <button onClick={handleConfirmPickup} disabled={submitting} style={{ background: "#2563eb", color: "white", border: "none", padding: "0.75rem 1.5rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer", marginRight: "0.5rem" }}>
                    {submitting ? "…" : "✓ Confirm Pickup"}
                  </button>
                )}
                {order.pickup.proposed_by_user_id === currentUserId && (
                  <p style={{ color: "#6b7280", fontSize: "0.825rem", margin: 0 }}>
                    Waiting for {isBuyer ? "seller" : "buyer"} to confirm this pickup.
                  </p>
                )}
              </>
            )}

            {order.pickup?.status === "confirmed" && isSeller && (
              <button onClick={() => setShowHandoverModal(true)} style={{ background: "#2563eb", color: "white", border: "none", padding: "0.75rem 1.5rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer" }}>
                ✓ Complete with Handover Code
              </button>
            )}
          </div>
        )}

        {/* ── Close Order — mutual confirmation ── */}
        {order.status !== "completed" && order.status !== "cancelled" && (
          <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: "1.5rem", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#1f2933", margin: "0 0 0.375rem" }}>Complete Order</h2>
            <p style={{ color: "#6b7280", fontSize: "0.825rem", margin: "0 0 1rem" }}>
              Both buyer and seller need to confirm to close this order.
            </p>

            {/* Progress indicators */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1.25rem" }}>
              <div style={{ background: order.seller_marked_delivered_at ? "#f0fdf4" : "#f9fafb", border: `1px solid ${order.seller_marked_delivered_at ? "#bbf7d0" : "#e5e7eb"}`, borderRadius: 8, padding: "0.875rem" }}>
                <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", margin: "0 0 0.35rem" }}>Seller</p>
                <p style={{ fontSize: "0.875rem", fontWeight: 700, color: order.seller_marked_delivered_at ? "#15803d" : "#6b7280", margin: 0 }}>
                  {order.seller_marked_delivered_at ? "✓ Marked delivered" : "⏳ Not yet marked"}
                </p>
                {order.seller_marked_delivered_at && (
                  <p style={{ fontSize: "0.7rem", color: "#6b7280", margin: "0.25rem 0 0" }}>{formatDate(order.seller_marked_delivered_at)}</p>
                )}
              </div>
              <div style={{ background: order.buyer_marked_received_at ? "#f0fdf4" : "#f9fafb", border: `1px solid ${order.buyer_marked_received_at ? "#bbf7d0" : "#e5e7eb"}`, borderRadius: 8, padding: "0.875rem" }}>
                <p style={{ fontSize: "0.7rem", fontWeight: 700, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.05em", margin: "0 0 0.35rem" }}>Buyer</p>
                <p style={{ fontSize: "0.875rem", fontWeight: 700, color: order.buyer_marked_received_at ? "#15803d" : "#6b7280", margin: 0 }}>
                  {order.buyer_marked_received_at ? "✓ Marked received" : "⏳ Not yet marked"}
                </p>
                {order.buyer_marked_received_at && (
                  <p style={{ fontSize: "0.7rem", color: "#6b7280", margin: "0.25rem 0 0" }}>{formatDate(order.buyer_marked_received_at)}</p>
                )}
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
              {isSeller && !order.seller_marked_delivered_at && (
                <button onClick={() => setShowDeliveredConfirm(true)} style={{ background: "#2563eb", color: "white", border: "none", padding: "0.75rem 1.5rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer" }}>
                  ✓ Mark as Delivered
                </button>
              )}
              {isBuyer && !order.buyer_marked_received_at && (
                <button onClick={() => setShowReceivedConfirm(true)} style={{ background: "#2563eb", color: "white", border: "none", padding: "0.75rem 1.5rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer" }}>
                  ✓ Mark as Received
                </button>
              )}
              {((isSeller && order.seller_marked_delivered_at) || (isBuyer && order.buyer_marked_received_at)) && (
                <div style={{ background: "#eff6ff", border: "1px solid #93c5fd", borderRadius: 8, padding: "0.75rem 1rem" }}>
                  <p style={{ fontSize: "0.825rem", color: "#1e40af", margin: 0 }}>
                    ✓ You've confirmed. Waiting for the other party to also confirm.
                  </p>
                </div>
              )}

              <button onClick={() => setShowCancelModal(true)} style={{ background: "none", border: "1.5px solid #fecaca", color: "#dc2626", padding: "0.6rem", borderRadius: 8, fontWeight: 600, fontSize: "0.825rem", cursor: "pointer" }}>
                Cancel Order
              </button>
            </div>

            <p style={{ fontSize: "0.72rem", color: "#9ca3af", margin: "0.875rem 0 0", textAlign: "center" }}>
              💡 The handover code below is optional. Use it in-person for extra verification.
            </p>
          </div>
        )}

        {/* Cancelled state */}
        {order.status === "cancelled" && (
          <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 12, padding: "1.5rem", marginBottom: "1rem" }}>
            <div style={{ fontSize: "1.75rem", marginBottom: "0.5rem", textAlign: "center" }}>✕</div>
            <p style={{ fontWeight: 700, color: "#991b1b", fontSize: "1rem", margin: "0 0 0.25rem", textAlign: "center" }}>Order Cancelled</p>
            {order.cancelled_at && (
              <p style={{ color: "#7f1d1d", fontSize: "0.825rem", margin: "0 0 0.5rem", textAlign: "center" }}>
                {formatDate(order.cancelled_at)}
              </p>
            )}
            {order.cancellation_reason && (
              <div style={{ background: "#fff", border: "1px solid #fecaca", borderRadius: 8, padding: "0.75rem 1rem", marginTop: "0.75rem" }}>
                <p style={{ fontSize: "0.72rem", color: "#991b1b", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", margin: "0 0 0.375rem" }}>Reason</p>
                <p style={{ fontSize: "0.875rem", color: "#374151", margin: 0 }}>{order.cancellation_reason}</p>
              </div>
            )}
          </div>
        )}

        {/* Completed state */}
        {order.status === "completed" && (
          <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 12, padding: "1.5rem", textAlign: "center" }}>
            <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>🎉</div>
            <p style={{ fontWeight: 700, color: "#15803d", fontSize: "1rem", margin: "0 0 0.25rem" }}>Order Complete!</p>
            <p style={{ color: "#374151", fontSize: "0.875rem", margin: "0 0 1rem" }}>
              {isBuyer ? "Thanks for buying! Consider leaving a review for the seller." : "Sale confirmed! Consider leaving a review for the buyer."}
            </p>
          </div>
        )}

        {/* ── Propose Pickup Modal ── */}
        {showPickupModal && (
          <Modal title="Propose Pickup Location" onClose={() => setShowPickupModal(false)}>
            <p style={{ fontSize: "0.8rem", color: "#6b7280", margin: "0 0 1rem" }}>Choose a safe, public location where you'll meet the buyer.</p>

            <Field label="Public location label *">
              <input type="text" value={pickupLocation} onChange={(e) => setPickupLocation(e.target.value)} placeholder="e.g. Central Library front entrance" style={inputStyle} />
            </Field>

            <Field label="Exact address (visible only after buyer confirms)">
              <input type="text" value={pickupAddress} onChange={(e) => setPickupAddress(e.target.value)} placeholder="e.g. Main Library, FC Road, Pune" style={inputStyle} />
            </Field>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
              <Field label="Date">
                <input type="date" value={pickupDate} onChange={(e) => setPickupDate(e.target.value)} style={inputStyle} />
              </Field>
              <Field label="Time">
                <input type="time" value={pickupTime} onChange={(e) => setPickupTime(e.target.value)} style={inputStyle} />
              </Field>
            </div>

            <Field label="Notes (optional)">
              <textarea rows={2} value={pickupNotes} onChange={(e) => setPickupNotes(e.target.value)} placeholder="e.g. I'll be wearing a red jacket" style={{ ...inputStyle, resize: "vertical", fontFamily: "inherit" }} />
            </Field>

            <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
              <button onClick={handleProposePickup} disabled={submitting || !pickupLocation.trim()} style={{ flex: 1, background: "#2563eb", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer", opacity: submitting ? 0.7 : 1 }}>
                {submitting ? "Sending…" : "Propose Pickup"}
              </button>
              <button onClick={() => setShowPickupModal(false)} style={{ padding: "0.75rem 1rem", background: "#fff", border: "1.5px solid #e5e7eb", borderRadius: 8, cursor: "pointer" }}>Cancel</button>
            </div>
          </Modal>
        )}

        {/* ── Mark Received Modal ── */}
        {showReceivedConfirm && (
          <Modal title="Confirm Book Received" onClose={() => setShowReceivedConfirm(false)}>
            <p style={{ color: "#374151", fontSize: "0.875rem", margin: "0 0 1rem", lineHeight: 1.6 }}>
              Confirm that you have received the book <strong>{listing?.title ?? "in this order"}</strong> from {otherName}.
            </p>
            <div style={{ background: "#f9fafb", borderRadius: 8, padding: "0.875rem", marginBottom: "1rem" }}>
              <p style={{ fontSize: "0.8rem", color: "#374151", margin: 0 }}>
                ✓ Once both you and the seller confirm, the order will be marked complete.
              </p>
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button onClick={handleMarkReceived} disabled={submitting} style={{ flex: 1, background: "#2563eb", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer", opacity: submitting ? 0.7 : 1 }}>
                {submitting ? "Confirming…" : "Yes, I Received It"}
              </button>
              <button onClick={() => setShowReceivedConfirm(false)} style={{ padding: "0.75rem 1rem", background: "#fff", border: "1.5px solid #e5e7eb", borderRadius: 8, cursor: "pointer" }}>Cancel</button>
            </div>
          </Modal>
        )}

        {/* ── Mark Delivered Modal ── */}
        {showDeliveredConfirm && (
          <Modal title="Confirm Book Delivered" onClose={() => setShowDeliveredConfirm(false)}>
            <p style={{ color: "#374151", fontSize: "0.875rem", margin: "0 0 1rem", lineHeight: 1.6 }}>
              Confirm that you have delivered/handed over <strong>{listing?.title ?? "the book"}</strong> to {otherName}.
            </p>
            <div style={{ background: "#f9fafb", borderRadius: 8, padding: "0.875rem", marginBottom: "1rem" }}>
              <p style={{ fontSize: "0.8rem", color: "#374151", margin: 0 }}>
                ✓ Once both you and the buyer confirm, the order will be marked complete.
              </p>
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button onClick={handleMarkDelivered} disabled={submitting} style={{ flex: 1, background: "#2563eb", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer", opacity: submitting ? 0.7 : 1 }}>
                {submitting ? "Confirming…" : "Yes, I Delivered It"}
              </button>
              <button onClick={() => setShowDeliveredConfirm(false)} style={{ padding: "0.75rem 1rem", background: "#fff", border: "1.5px solid #e5e7eb", borderRadius: 8, cursor: "pointer" }}>Cancel</button>
            </div>
          </Modal>
        )}

        {/* ── Cancel Modal ── */}
        {showCancelModal && (
          <Modal title="Cancel Order" onClose={() => setShowCancelModal(false)}>
            <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, padding: "0.875rem", marginBottom: "1rem" }}>
              <p style={{ fontSize: "0.825rem", color: "#991b1b", margin: 0, lineHeight: 1.5 }}>
                ⚠ This will cancel the order and release the listing back for other buyers.
              </p>
            </div>
            <Field label="Reason (optional)">
              <textarea rows={3} value={cancelReason} onChange={(e) => setCancelReason(e.target.value)} placeholder={isBuyer ? "e.g. Changed my mind, couldn't meet up..." : "e.g. Item no longer available, buyer unresponsive..."} style={{ ...inputStyle, resize: "vertical", fontFamily: "inherit" }} />
            </Field>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button onClick={handleCancel} disabled={submitting} style={{ flex: 1, background: "#dc2626", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer", opacity: submitting ? 0.7 : 1 }}>
                {submitting ? "Cancelling…" : "Confirm Cancel"}
              </button>
              <button onClick={() => setShowCancelModal(false)} style={{ padding: "0.75rem 1rem", background: "#fff", border: "1.5px solid #e5e7eb", borderRadius: 8, cursor: "pointer" }}>Keep Order</button>
            </div>
          </Modal>
        )}

        {/* ── Handover Modal ── */}
        {showHandoverModal && (
          <Modal title="Complete Transaction" onClose={() => setShowHandoverModal(false)}>
            <p style={{ fontSize: "0.875rem", color: "#374151", margin: "0 0 1rem" }}>
              Enter the handover code shown on the buyer's screen when they receive the book.
            </p>
            <Field label="Handover code">
              <input type="text" value={handoverCode} onChange={(e) => setHandoverCode(e.target.value.toUpperCase())} placeholder="ABCD" maxLength={12} style={{ ...inputStyle, textAlign: "center", fontSize: "1.25rem", fontWeight: 800, letterSpacing: "0.3em", fontFamily: "monospace" }} />
            </Field>
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
              <button onClick={handleComplete} disabled={submitting} style={{ flex: 1, background: "#2563eb", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer", opacity: submitting ? 0.7 : 1 }}>
                {submitting ? "Verifying…" : "Complete Transaction"}
              </button>
              <button onClick={() => setShowHandoverModal(false)} style={{ padding: "0.75rem 1rem", background: "#fff", border: "1.5px solid #e5e7eb", borderRadius: 8, cursor: "pointer" }}>Cancel</button>
            </div>
          </Modal>
        )}
      </Container>
    </div>
  );
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200, padding: "1rem" }}>
      <div style={{ background: "#fff", borderRadius: 12, padding: "1.5rem", width: "100%", maxWidth: 480, boxShadow: "0 20px 60px rgba(0,0,0,0.2)", maxHeight: "90vh", overflowY: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
          <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 700, color: "#1f2933" }}>{title}</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", fontSize: "1.25rem", cursor: "pointer", color: "#6b7280" }}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "0.875rem" }}>
      <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 600, color: "#374151", marginBottom: "0.35rem" }}>{label}</label>
      {children}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "0.65rem 0.875rem", border: "1.5px solid #e5e7eb",
  borderRadius: 8, fontSize: "0.875rem", background: "#fff", color: "#1f2933",
  outline: "none", boxSizing: "border-box", transition: "border-color 0.15s",
};
