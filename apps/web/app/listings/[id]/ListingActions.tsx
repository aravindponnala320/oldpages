"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getAccessToken } from "../../../lib/auth";
import type { ListingResponse } from "@oldpages/shared-types";
import { Avatar, colors, font, radius } from "../../../components/ui";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const WS_BASE = typeof window !== "undefined"
  ? `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host.replace(/:\d+$/, ":8000")}`
  : "ws://localhost:8000";

interface SellerProfile { display_name: string; username: string | null; }

interface Offer {
  id: string;
  status: string;
  amount_cents: number | null;
  currency: string;
  message: string | null;
  offer_type: string;
  fulfillment_method: string;
  listing_id: string;
  buyer: { id: string; display_name?: string | null };
  seller: { id: string; display_name?: string | null };
  proposer: { id: string; display_name?: string | null };
  parent_offer_id: string | null;
  created_at: string;
  transaction_id: string | null;
}

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
  if (cents == null) return "Free";
  return `${currency === "INR" ? "₹" : currency}${(cents / 100).toLocaleString("en-IN")}`;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

export function ListingActions({ listing }: { listing: ListingResponse }) {
  const router = useRouter();
  const [isOwner, setIsOwner] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [sellerProfile, setSellerProfile] = useState<SellerProfile | null>(null);
  const [isFavorited, setIsFavorited] = useState(false);
  const [activeModal, setActiveModal] = useState<"buy" | "offer" | "message" | "counter" | null>(null);
  const [pendingOffers, setPendingOffers] = useState<Offer[]>([]);
  const [myOffer, setMyOffer] = useState<Offer | null>(null);
  const [offerAmount, setOfferAmount] = useState("");
  const [offerMessage, setOfferMessage] = useState("");
  const [fulfillment, setFulfillment] = useState<"pickup" | "shipping">("pickup");
  const [messageText, setMessageText] = useState("");
  const [counterAmount, setCounterAmount] = useState("");
  const [counterMessage, setCounterMessage] = useState("");
  const [counterOfferId, setCounterOfferId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const isSell = listing.listing_modes.includes("sell");
  const isExchange = listing.listing_modes.includes("exchange");
  const isDonate = listing.listing_modes.includes("donate");
  const isLend = listing.listing_modes.includes("lend");
  const isRent = listing.listing_modes.includes("rent");

  useEffect(() => {
    const uid = getCurrentUserId();
    setIsLoggedIn(!!uid);
    const owner = !!uid && uid === listing.seller.id;
    setIsOwner(owner);

    // Fetch seller profile
    fetch(`${API_BASE}/api/v1/users/${listing.seller.id}`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => { if (d?.profile) setSellerProfile({ display_name: d.profile.display_name ?? "Seller", username: d.profile.username }); })
      .catch(() => {});

    // Fetch offers
    const token = getAccessToken();
    if (!token || !uid) return;

    if (owner) {
      // Seller: load pending offers on this listing
      fetch(`${API_BASE}/api/v1/offers?role=seller&listing_id=${listing.id}&limit=20`, {
        headers: { Authorization: `Bearer ${token}` },
      }).then((r) => r.ok ? r.json() : [])
        .then((data: Offer[]) => setPendingOffers(data.filter((o) => o.status === "pending")))
        .catch(() => {});
    } else {
      // Buyer: check if they already made an offer
      // API returns offers sorted by created_at DESC — latest offer in the negotiation is at [0]
      // We want the "active" one: pending, countered, or accepted takes priority over rejected/withdrawn
      fetch(`${API_BASE}/api/v1/offers?role=buyer&listing_id=${listing.id}&limit=20`, {
        headers: { Authorization: `Bearer ${token}` },
      }).then((r) => r.ok ? r.json() : [])
        .then((data: Offer[]) => {
          if (data.length === 0) return;
          // Prefer active offers (pending/countered/accepted) — data is DESC so [0] is newest
          const active = data.find((o) => ["pending", "countered", "accepted"].includes(o.status));
          setMyOffer(active ?? data[0] ?? null);
        })
        .catch(() => {});
    }
  }, [listing.id, listing.seller.id]);

  // ── WebSocket for real-time offer updates ────────────────────────────
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!isLoggedIn) return;

    function connect() {
      const token = getAccessToken();
      if (!token) return;
      if (wsRef.current) wsRef.current.close();

      const ws = new WebSocket(`${WS_BASE}/ws/conversations?access_token=${token}`);
      wsRef.current = ws;

      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data as string);
          if (data.type === "offer.updated" && data.offer) {
            const updated = data.offer as Offer;
            // Only care about offers on THIS listing
            if (updated.listing_id !== listing.id) return;

            if (isOwner) {
              // Seller view: refresh pending offers list
              setPendingOffers((prev) => {
                const filtered = prev.filter((o) => o.id !== updated.id);
                if (updated.status === "pending") {
                  return [updated, ...filtered];
                }
                return filtered;
              });
            } else {
              // Buyer view: update my current offer
              const currentUid = getCurrentUserId();
              if (updated.buyer.id === currentUid) {
                // Prefer active offers (pending/countered/accepted) over closed states
                setMyOffer((cur) => {
                  if (!cur) return updated;
                  // If update matches current, take it
                  if (cur.id === updated.id) return updated;
                  // If update is newer and active, replace
                  if (["pending", "countered", "accepted"].includes(updated.status)) {
                    return updated;
                  }
                  return cur;
                });
              }
            }
          }
        } catch { /* ignore */ }
      };

      ws.onclose = () => {
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
  }, [isLoggedIn, listing.id, isOwner]);

  async function handleBuyNow() {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    setSubmitting(true); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/offers`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          listing_id: listing.id,
          amount_cents: listing.price_amount_cents,
          currency: listing.currency ?? "INR",
          offer_type: "price",
          fulfillment_method: fulfillment,
          message: offerMessage || null,
          quantity: 1,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to place order");
      setMyOffer(data);
      setSuccess("Your offer has been sent! The seller will respond shortly.");
      setActiveModal(null);
      setOfferMessage("");
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setSubmitting(false); }
  }

  async function handleMakeOffer() {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    if (!offerAmount || parseFloat(offerAmount) <= 0) { setError("Enter a valid offer amount"); return; }
    setSubmitting(true); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/offers`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          listing_id: listing.id,
          amount_cents: Math.round(parseFloat(offerAmount) * 100),
          currency: listing.currency ?? "INR",
          offer_type: "price",
          fulfillment_method: fulfillment,
          message: offerMessage || null,
          quantity: 1,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to send offer");
      setMyOffer(data);
      setSuccess("Offer sent! Seller will respond soon.");
      setActiveModal(null); setOfferAmount(""); setOfferMessage("");
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setSubmitting(false); }
  }

  async function handleMessage() {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    if (!messageText.trim()) return;
    setSubmitting(true); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/chat-requests`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ listing_id: listing.id, message: messageText }),
      });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail ?? "Failed"); }
      setSuccess("Message sent! The seller will respond in your inbox.");
      setActiveModal(null); setMessageText("");
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setSubmitting(false); }
  }

  async function handleWithdrawOffer() {
    if (!myOffer) return;
    const token = getAccessToken();
    if (!token) return;
    setActionLoading("withdraw"); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/offers/${myOffer.id}/withdraw`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error("Failed to withdraw");
      setMyOffer(null); setSuccess("Offer withdrawn.");
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setActionLoading(null); }
  }

  async function handleCounterOffer() {
    if (!counterOfferId || !counterAmount) return;
    const token = getAccessToken();
    if (!token) return;
    setSubmitting(true); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/offers/${counterOfferId}/counter`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          amount_cents: Math.round(parseFloat(counterAmount) * 100),
          currency: listing.currency ?? "INR",
          message: counterMessage || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to send counter");
      // Remove the original offer and add the countered one back
      setPendingOffers((prev) => prev.filter((o) => o.id !== counterOfferId));
      setSuccess("Counter offer sent! The buyer will see your new price.");
      setActiveModal(null);
      setCounterOfferId(null); setCounterAmount(""); setCounterMessage("");
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setSubmitting(false); }
  }

  async function handleRejectMyOffer() {
    if (!myOffer) return;
    const token = getAccessToken();
    if (!token) return;
    setActionLoading("reject-my"); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/offers/${myOffer.id}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error("Failed to decline");
      setMyOffer({ ...myOffer, status: "rejected" });
      setSuccess("Counter offer declined.");
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setActionLoading(null); }
  }

  async function handleAcceptCounter() {
    if (!myOffer) return;
    const token = getAccessToken();
    if (!token) return;
    setActionLoading("accept-counter"); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/offers/${myOffer.id}/accept`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to accept");
      setMyOffer(data);
      setSuccess("Counter offer accepted! Transaction created.");
      if (data.transaction_id) setTimeout(() => router.push(`/orders/${data.transaction_id}`), 1000);
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setActionLoading(null); }
  }

  async function handleAcceptOffer(offer: Offer) {
    const token = getAccessToken();
    if (!token) return;
    setActionLoading(offer.id); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/offers/${offer.id}/accept`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to accept");
      setPendingOffers((prev) => prev.filter((o) => o.id !== offer.id));
      setSuccess(`Offer accepted! Transaction created. Go to Orders to arrange pickup.`);
      if (data.transaction_id) setTimeout(() => router.push(`/orders/${data.transaction_id}`), 1500);
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setActionLoading(null); }
  }

  async function handleRejectOffer(offer: Offer) {
    const token = getAccessToken();
    if (!token) return;
    setActionLoading(`reject-${offer.id}`); setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/offers/${offer.id}/reject`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error("Failed to reject");
      setPendingOffers((prev) => prev.filter((o) => o.id !== offer.id));
    } catch (err) { setError(err instanceof Error ? err.message : "Failed"); }
    finally { setActionLoading(null); }
  }

  async function handleFavorite() {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    try {
      await fetch(`${API_BASE}/api/v1/listings/${listing.id}/favorite`, {
        method: isFavorited ? "DELETE" : "POST", headers: { Authorization: `Bearer ${token}` },
      });
      setIsFavorited(!isFavorited);
    } catch { /* ignore */ }
  }

  async function handleDelete() {
    const token = getAccessToken();
    if (!token) return;
    try {
      await fetch(`${API_BASE}/api/v1/listings/${listing.id}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });
      router.push("/my-listings");
    } catch { setError("Failed to delete listing"); }
  }

  function handleShare() {
    if (navigator.share) navigator.share({ title: listing.title, url: window.location.href }).catch(() => {});
    else navigator.clipboard.writeText(window.location.href).then(() => setSuccess("Link copied!")).catch(() => {});
  }

  return (
    <>
      {/* ── Seller card ── */}
      <div style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.lg,
        padding: 16,
        marginBottom: 14,
      }}>
        <p style={{ fontSize: font.size.xs, fontWeight: font.weight.bold, color: colors.textSubtle, textTransform: "uppercase", letterSpacing: "0.06em", margin: "0 0 10px" }}>
          {isOwner ? "Your Listing" : "Seller"}
        </p>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Avatar name={sellerProfile?.display_name ?? "?"} size="md" />
          <div style={{ flex: 1 }}>
            <p style={{ margin: 0, fontSize: font.size.md, fontWeight: font.weight.semibold, color: colors.text }}>
              {sellerProfile?.display_name ?? "Loading…"}
            </p>
            {sellerProfile?.username && (
              <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textSubtle }}>@{sellerProfile.username}</p>
            )}
          </div>
          <Link
            href={`/profile/${listing.seller.id}`}
            style={{ fontSize: font.size.sm, color: colors.primary, textDecoration: "none", fontWeight: font.weight.medium }}
          >
            View profile →
          </Link>
        </div>
      </div>

      {/* ── Feedback banners ── */}
      {error && (
        <div style={{
          background: colors.dangerSoft, border: `1px solid #fecaca`,
          borderRadius: radius.md, padding: "10px 14px", marginBottom: 10,
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <p style={{ color: colors.dangerText, fontSize: font.size.sm, margin: 0 }}>{error}</p>
          <button
            onClick={() => setError(null)}
            style={{ background: "none", border: "none", cursor: "pointer", color: colors.dangerText, fontSize: 14, padding: 4 }}
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      )}
      {success && (
        <div style={{
          background: colors.successSoft, border: `1px solid #bbf7d0`,
          borderRadius: radius.md, padding: "10px 14px", marginBottom: 10,
        }}>
          <p style={{ color: colors.successText, fontSize: font.size.sm, margin: 0 }}>{success}</p>
        </div>
      )}

      {/* ── SELLER ACTIONS ── */}
      {isOwner && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
          {/* Pending offers */}
          {pendingOffers.length > 0 && (
            <div style={{ background: "#fffbeb", border: "1px solid #fcd34d", borderRadius: 10, padding: "1rem", marginBottom: "0.25rem" }}>
              <p style={{ fontWeight: 700, color: "#92400e", fontSize: "0.875rem", margin: "0 0 0.75rem" }}>
                {pendingOffers.length} pending offer{pendingOffers.length !== 1 ? "s" : ""}
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {pendingOffers.map((offer) => (
                  <div key={offer.id} style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8, padding: "0.875rem" }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.375rem" }}>
                      <span style={{ fontWeight: 600, fontSize: "0.875rem", color: "#1f2933" }}>
                        {offer.buyer.display_name ?? `Buyer ${offer.buyer.id.slice(0, 8)}`}
                      </span>
                      <span style={{ fontSize: "0.72rem", color: "#9ca3af" }}>{timeAgo(offer.created_at)}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.5rem" }}>
                      <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#2563eb" }}>
                        {formatPrice(offer.amount_cents, offer.currency)}
                      </span>
                      {listing.price_amount_cents && offer.amount_cents && offer.amount_cents < listing.price_amount_cents && (
                        <span style={{ fontSize: "0.72rem", color: "#9ca3af", textDecoration: "line-through" }}>
                          {formatPrice(listing.price_amount_cents, offer.currency)}
                        </span>
                      )}
                      <span style={{ fontSize: "0.72rem", background: "#f3f4f6", color: "#374151", padding: "0.1rem 0.4rem", borderRadius: 10 }}>
                        {offer.fulfillment_method === "pickup" ? "🤝 Pickup" : "📦 Shipping"}
                      </span>
                    </div>
                    {offer.message && (
                      <p style={{ fontSize: "0.8rem", color: "#374151", fontStyle: "italic", margin: "0 0 0.625rem", background: "#f9fafb", padding: "0.5rem 0.625rem", borderRadius: 6 }}>
                        "{offer.message}"
                      </p>
                    )}
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <button
                        onClick={() => handleAcceptOffer(offer)}
                        disabled={actionLoading === offer.id}
                        style={{ flex: 1, background: "#2563eb", color: "white", border: "none", padding: "0.55rem", borderRadius: 7, fontWeight: 700, fontSize: "0.8rem", cursor: "pointer" }}
                      >
                        {actionLoading === offer.id ? "…" : "✓ Accept"}
                      </button>
                      <button
                        onClick={() => { setCounterOfferId(offer.id); setCounterAmount(String((offer.amount_cents ?? 0) / 100)); setActiveModal("counter"); }}
                        style={{ flex: 1, background: "#fff", border: "1.5px solid #2563eb", color: "#2563eb", padding: "0.55rem", borderRadius: 7, fontWeight: 600, fontSize: "0.8rem", cursor: "pointer" }}
                      >
                        Counter
                      </button>
                      <button
                        onClick={() => handleRejectOffer(offer)}
                        disabled={!!actionLoading}
                        style={{ padding: "0.55rem 0.75rem", background: "#fff", border: "1.5px solid #e5e7eb", color: "#dc2626", borderRadius: 7, fontWeight: 600, fontSize: "0.8rem", cursor: "pointer" }}
                      >
                        Reject
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <Link href={`/listings/${listing.id}/edit`} style={{ display: "block", textAlign: "center", background: "#2563eb", color: "white", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", textDecoration: "none" }}>
            ✏️ Edit Listing
          </Link>
          <button onClick={handleShare} style={{ background: "#fff", border: "1.5px solid #e5e7eb", color: "#374151", padding: "0.7rem", borderRadius: 8, fontWeight: 600, fontSize: "0.875rem", cursor: "pointer" }}>
            Share
          </button>
          {!deleteConfirm
            ? <button onClick={() => setDeleteConfirm(true)} style={{ background: "none", border: "none", color: "#dc2626", fontSize: "0.8rem", cursor: "pointer" }}>Delete listing</button>
            : <div style={{ background: "#fff1f2", border: "1px solid #fecdd3", borderRadius: 8, padding: "0.875rem" }}>
                <p style={{ color: "#be123c", fontSize: "0.8rem", margin: "0 0 0.5rem", fontWeight: 600 }}>Delete permanently?</p>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button onClick={handleDelete} style={{ flex: 1, background: "#dc2626", color: "white", border: "none", padding: "0.5rem", borderRadius: 6, fontWeight: 700, fontSize: "0.8rem", cursor: "pointer" }}>Delete</button>
                  <button onClick={() => setDeleteConfirm(false)} style={{ flex: 1, background: "#fff", border: "1px solid #e5e7eb", padding: "0.5rem", borderRadius: 6, cursor: "pointer" }}>Cancel</button>
                </div>
              </div>
          }
        </div>
      )}

      {/* ── BUYER ACTIONS ── */}
      {!isOwner && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
          {!isLoggedIn && (
            <Link href="/login" style={{ display: "block", textAlign: "center", background: "#2563eb", color: "white", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", textDecoration: "none" }}>
              Sign in to buy or contact seller
            </Link>
          )}

          {isLoggedIn && myOffer && (() => {
            const currentUid = getCurrentUserId();
            const iAmProposer = myOffer.proposer.id === currentUid;
            const isCounterFromSeller = !iAmProposer && myOffer.status === "pending";
            // If the offer is pending and I'm NOT the proposer → seller sent me a counter
            const showType = isCounterFromSeller ? "seller_counter" : myOffer.status;

            const bgColor = myOffer.status === "accepted" ? "#f0fdf4"
              : isCounterFromSeller ? "#eff6ff"
              : myOffer.status === "rejected" ? "#fef2f2"
              : "#fffbeb";
            const borderColor = myOffer.status === "accepted" ? "#bbf7d0"
              : isCounterFromSeller ? "#93c5fd"
              : myOffer.status === "rejected" ? "#fecaca"
              : "#fcd34d";
            const textColor = myOffer.status === "accepted" ? "#15803d"
              : isCounterFromSeller ? "#1e40af"
              : myOffer.status === "rejected" ? "#991b1b"
              : "#92400e";

            return (
              <div style={{ background: bgColor, border: `1px solid ${borderColor}`, borderRadius: 10, padding: "1rem" }}>
                <p style={{ fontWeight: 700, color: textColor, fontSize: "0.9rem", margin: "0 0 0.375rem" }}>
                  {isCounterFromSeller && "🔄 Seller sent you a counter offer"}
                  {!isCounterFromSeller && myOffer.status === "pending" && "⏳ Offer pending seller response"}
                  {myOffer.status === "accepted" && "✓ Offer accepted!"}
                  {myOffer.status === "countered" && "🔄 You countered — waiting on seller"}
                  {myOffer.status === "rejected" && "✕ Offer was rejected"}
                  {myOffer.status === "withdrawn" && "Offer withdrawn"}
                  {myOffer.status === "expired" && "Offer expired"}
                </p>

                <div style={{ background: "#fff", borderRadius: 8, padding: "0.625rem 0.875rem", marginBottom: "0.75rem", border: "1px solid #e5e7eb" }}>
                  <p style={{ margin: "0 0 0.25rem", fontSize: "0.72rem", color: "#6b7280", fontWeight: 600, textTransform: "uppercase" }}>
                    {isCounterFromSeller ? "Seller's counter offer" : "Your offer"}
                  </p>
                  <p style={{ fontSize: "1.25rem", fontWeight: 800, color: isCounterFromSeller ? "#1e40af" : "#2563eb", margin: 0 }}>
                    {formatPrice(myOffer.amount_cents, myOffer.currency)}
                  </p>
                  {listing.price_amount_cents != null && (
                    <p style={{ fontSize: "0.72rem", color: "#6b7280", margin: "0.2rem 0 0" }}>
                      Listed at {formatPrice(listing.price_amount_cents, myOffer.currency)}
                    </p>
                  )}
                  {myOffer.message && (
                    <p style={{ margin: "0.5rem 0 0", fontSize: "0.8rem", color: "#374151", fontStyle: "italic" }}>"{myOffer.message}"</p>
                  )}
                </div>

                {myOffer.status === "accepted" && myOffer.transaction_id && (
                  <Link href={`/orders/${myOffer.transaction_id}`} style={{ display: "block", textAlign: "center", background: "#2563eb", color: "white", padding: "0.7rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", textDecoration: "none" }}>
                    View Order & Complete →
                  </Link>
                )}

                {/* Seller countered — buyer needs to accept / counter back / decline */}
                {isCounterFromSeller && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    <button onClick={handleAcceptCounter} disabled={!!actionLoading} style={{ background: "#2563eb", color: "white", border: "none", padding: "0.7rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer" }}>
                      {actionLoading === "accept-counter" ? "Accepting…" : "✓ Accept Counter"}
                    </button>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <button onClick={() => { setCounterOfferId(myOffer.id); setCounterAmount(String((myOffer.amount_cents ?? 0) / 100)); setActiveModal("counter"); }} style={{ flex: 1, background: "#fff", border: "1.5px solid #2563eb", color: "#2563eb", padding: "0.55rem", borderRadius: 8, fontWeight: 600, fontSize: "0.8rem", cursor: "pointer" }}>
                        Counter Back
                      </button>
                      <button onClick={handleRejectMyOffer} disabled={!!actionLoading} style={{ flex: 1, background: "#fff", border: "1.5px solid #e5e7eb", color: "#dc2626", padding: "0.55rem", borderRadius: 8, fontWeight: 600, fontSize: "0.8rem", cursor: "pointer" }}>
                        Decline
                      </button>
                    </div>
                  </div>
                )}

                {/* My pending offer — can withdraw */}
                {!isCounterFromSeller && (myOffer.status === "pending" || myOffer.status === "countered") && (
                  <button onClick={handleWithdrawOffer} disabled={actionLoading === "withdraw"} style={{ width: "100%", background: "#fff", border: "1.5px solid #e5e7eb", color: "#6b7280", padding: "0.6rem", borderRadius: 8, fontWeight: 500, fontSize: "0.8rem", cursor: "pointer" }}>
                    Withdraw offer
                  </button>
                )}

                {(myOffer.status === "rejected" || myOffer.status === "withdrawn" || myOffer.status === "expired") && (
                  <button onClick={() => { setMyOffer(null); }} style={{ width: "100%", background: "#2563eb", color: "white", border: "none", padding: "0.7rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer" }}>
                    Make a New Offer
                  </button>
                )}
              </div>
            );
          })()}

          {isLoggedIn && !myOffer && (
            <>
              {/* Buy Now — only for sell listings with a price */}
              {isSell && listing.price_amount_cents != null && (
                <button
                  onClick={() => setActiveModal("buy")}
                  style={{ background: "#2563eb", color: "white", border: "none", padding: "0.8rem", borderRadius: 8, fontWeight: 700, fontSize: "0.95rem", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}
                >
                  <span>Buy for {formatPrice(listing.price_amount_cents, listing.currency ?? "INR")}</span>
                </button>
              )}

              {/* Make an Offer — for negotiable sell listings */}
              {isSell && listing.negotiable && (
                <button
                  onClick={() => setActiveModal("offer")}
                  style={{ background: "#fff", border: "1.5px solid #2563eb", color: "#2563eb", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer" }}
                >
                  Make an Offer
                </button>
              )}

              {/* Exchange */}
              {isExchange && (
                <button onClick={() => setActiveModal("message")} style={{ background: "#2563eb", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer" }}>
                  🔄 Propose Exchange
                </button>
              )}

              {/* Donate / Free */}
              {isDonate && (
                <button onClick={() => setActiveModal("message")} style={{ background: "#9333ea", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer" }}>
                  🎁 Request this Book
                </button>
              )}

              {/* Lend */}
              {isLend && (
                <button onClick={() => setActiveModal("message")} style={{ background: "#d97706", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer" }}>
                  📤 Request to Borrow
                </button>
              )}

              {/* Rent */}
              {isRent && (
                <button onClick={() => setActiveModal("buy")} style={{ background: "#0891b2", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer" }}>
                  🔑 Request to Rent
                </button>
              )}

              {/* Message seller — always available */}
              <button onClick={() => setActiveModal("message")} style={{ background: "#fff", border: "1.5px solid #e5e7eb", color: "#374151", padding: "0.7rem", borderRadius: 8, fontWeight: 600, fontSize: "0.875rem", cursor: "pointer" }}>
                💬 Message Seller
              </button>
            </>
          )}

          {isLoggedIn && (
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button onClick={handleFavorite} style={{ flex: 1, background: isFavorited ? "#fef3c7" : "#fff", border: `1.5px solid ${isFavorited ? "#fcd34d" : "#e5e7eb"}`, color: isFavorited ? "#92400e" : "#374151", padding: "0.6rem", borderRadius: 8, fontWeight: 600, fontSize: "0.825rem", cursor: "pointer" }}>
                {isFavorited ? "♥ Saved" : "♡ Save"}
              </button>
              <button onClick={handleShare} style={{ flex: 1, background: "#fff", border: "1.5px solid #e5e7eb", color: "#374151", padding: "0.6rem", borderRadius: 8, fontWeight: 600, fontSize: "0.825rem", cursor: "pointer" }}>
                Share
              </button>
            </div>
          )}
        </div>
      )}

      {/* ── MODALS ── */}
      {(activeModal === "buy" || activeModal === "offer") && (
        <Modal title={activeModal === "buy" ? `Buy for ${formatPrice(listing.price_amount_cents, listing.currency ?? "INR")}` : "Make an Offer"} onClose={() => { setActiveModal(null); setError(null); }}>
          {activeModal === "offer" && (
            <div style={{ marginBottom: "1rem" }}>
              <label style={labelStyle}>Your offer price (₹) *</label>
              <div style={{ position: "relative", marginTop: "0.375rem" }}>
                <span style={{ position: "absolute", left: "0.875rem", top: "50%", transform: "translateY(-50%)", color: "#6b7280" }}>₹</span>
                <input type="number" min="1" value={offerAmount} onChange={(e) => setOfferAmount(e.target.value)} placeholder={listing.price_amount_cents ? String(listing.price_amount_cents / 100) : "0"} style={{ ...inputStyle, paddingLeft: "2rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
              </div>
              {listing.price_amount_cents && (
                <p style={{ fontSize: "0.75rem", color: "#6b7280", margin: "0.375rem 0 0" }}>
                  Listed at {formatPrice(listing.price_amount_cents, listing.currency ?? "INR")}
                  {listing.negotiable && " · Seller is open to negotiation"}
                </p>
              )}
            </div>
          )}

          <div style={{ marginBottom: "1rem" }}>
            <label style={labelStyle}>How will you receive it? *</label>
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.375rem" }}>
              {(["pickup", "shipping"] as const).filter((m) => {
                const methods = (listing as any).delivery_methods ?? [];
                return methods.length === 0 || methods.some((d: any) => d.method === m && d.enabled !== false);
              }).map((m) => (
                <button key={m} onClick={() => setFulfillment(m)} style={{ flex: 1, padding: "0.625rem", border: `1.5px solid ${fulfillment === m ? "#2563eb" : "#e5e7eb"}`, borderRadius: 8, background: fulfillment === m ? "#eaf2ff" : "#fff", color: fulfillment === m ? "#2563eb" : "#374151", fontWeight: 600, fontSize: "0.825rem", cursor: "pointer" }}>
                  {m === "pickup" ? "🤝 Pickup" : "📦 Shipping"}
                </button>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: "1.25rem" }}>
            <label style={labelStyle}>Message to seller <span style={{ fontWeight: 400, color: "#9ca3af" }}>(optional)</span></label>
            <textarea rows={3} value={offerMessage} onChange={(e) => setOfferMessage(e.target.value)} placeholder="When can you meet? Any questions about the book?" style={{ ...inputStyle, marginTop: "0.375rem", resize: "vertical", minHeight: 70, fontFamily: "inherit" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
          </div>

          {error && <p style={{ color: "#be123c", fontSize: "0.8rem", margin: "0 0 0.75rem" }}>{error}</p>}

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button onClick={activeModal === "buy" ? handleBuyNow : handleMakeOffer} disabled={submitting || (activeModal === "offer" && !offerAmount)} style={{ flex: 1, background: "#2563eb", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer", opacity: submitting ? 0.7 : 1 }}>
              {submitting ? "Sending…" : activeModal === "buy" ? `Confirm Purchase` : "Send Offer"}
            </button>
            <button onClick={() => { setActiveModal(null); setError(null); }} style={{ padding: "0.75rem 1rem", background: "#fff", border: "1.5px solid #e5e7eb", borderRadius: 8, cursor: "pointer" }}>Cancel</button>
          </div>
        </Modal>
      )}

      {activeModal === "counter" && (
        <Modal title="Send Counter Offer" onClose={() => { setActiveModal(null); setError(null); setCounterOfferId(null); }}>
          <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: "0 0 1rem" }}>
            Propose a different price to move the negotiation forward.
          </p>

          <div style={{ marginBottom: "1rem" }}>
            <label style={labelStyle}>Your counter price (₹) *</label>
            <div style={{ position: "relative", marginTop: "0.375rem" }}>
              <span style={{ position: "absolute", left: "0.875rem", top: "50%", transform: "translateY(-50%)", color: "#6b7280" }}>₹</span>
              <input type="number" min="1" value={counterAmount} onChange={(e) => setCounterAmount(e.target.value)} style={{ ...inputStyle, paddingLeft: "2rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
            </div>
            {listing.price_amount_cents && (
              <p style={{ fontSize: "0.75rem", color: "#6b7280", margin: "0.375rem 0 0" }}>
                Listed at {formatPrice(listing.price_amount_cents, listing.currency ?? "INR")}
              </p>
            )}
          </div>

          <div style={{ marginBottom: "1.25rem" }}>
            <label style={labelStyle}>Message <span style={{ fontWeight: 400, color: "#9ca3af" }}>(optional)</span></label>
            <textarea rows={3} value={counterMessage} onChange={(e) => setCounterMessage(e.target.value)} placeholder="Explain your counter offer..." style={{ ...inputStyle, marginTop: "0.375rem", resize: "vertical", minHeight: 70, fontFamily: "inherit" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
          </div>

          {error && <p style={{ color: "#be123c", fontSize: "0.8rem", margin: "0 0 0.75rem" }}>{error}</p>}

          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button onClick={handleCounterOffer} disabled={submitting || !counterAmount} style={{ flex: 1, background: "#2563eb", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer", opacity: submitting ? 0.7 : 1 }}>
              {submitting ? "Sending…" : "Send Counter Offer"}
            </button>
            <button onClick={() => { setActiveModal(null); setError(null); setCounterOfferId(null); }} style={{ padding: "0.75rem 1rem", background: "#fff", border: "1.5px solid #e5e7eb", borderRadius: 8, cursor: "pointer" }}>Cancel</button>
          </div>
        </Modal>
      )}

      {activeModal === "message" && (
        <Modal title={`Message ${sellerProfile?.display_name ?? "Seller"}`} onClose={() => { setActiveModal(null); setError(null); }}>
          <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: "0 0 1rem" }}>About: <strong style={{ color: "#1f2933" }}>{listing.title}</strong></p>
          <textarea rows={4} required value={messageText} onChange={(e) => setMessageText(e.target.value)} placeholder="Hi, I'm interested in this book. Is it still available?" style={{ ...inputStyle, resize: "vertical", minHeight: 90, fontFamily: "inherit", marginBottom: "1rem" }} onFocus={(e) => e.target.style.borderColor = "#2563eb"} onBlur={(e) => e.target.style.borderColor = "#e5e7eb"} />
          {error && <p style={{ color: "#be123c", fontSize: "0.8rem", margin: "0 0 0.75rem" }}>{error}</p>}
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button onClick={handleMessage} disabled={submitting || !messageText.trim()} style={{ flex: 1, background: "#2563eb", color: "white", border: "none", padding: "0.75rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", cursor: "pointer", opacity: submitting ? 0.7 : 1 }}>
              {submitting ? "Sending…" : "Send Message"}
            </button>
            <button onClick={() => { setActiveModal(null); setError(null); }} style={{ padding: "0.75rem 1rem", background: "#fff", border: "1.5px solid #e5e7eb", borderRadius: 8, cursor: "pointer" }}>Cancel</button>
          </div>
        </Modal>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </>
  );
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.45)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 200, padding: "1rem" }}>
      <div style={{ background: "#fff", borderRadius: 12, padding: "1.5rem", width: "100%", maxWidth: 440, boxShadow: "0 20px 60px rgba(0,0,0,0.2)", maxHeight: "90vh", overflowY: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
          <h3 style={{ margin: 0, fontSize: "1rem", fontWeight: 700, color: "#1f2933" }}>{title}</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", fontSize: "1.25rem", cursor: "pointer", color: "#6b7280", lineHeight: 1 }}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = { fontSize: "0.8rem", fontWeight: 600, color: "#374151" };
const inputStyle: React.CSSProperties = {
  width: "100%", padding: "0.7rem 0.875rem", border: "1.5px solid #e5e7eb",
  borderRadius: 8, fontSize: "0.875rem", background: "#fff", color: "#1f2933",
  outline: "none", boxSizing: "border-box", transition: "border-color 0.15s",
};
