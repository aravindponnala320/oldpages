"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../contexts/AuthContext";
import { getAccessToken } from "../../lib/auth";
import { Container, PageHeader, Spinner, colors, radius } from "../../components/ui";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type Tab = "buying" | "selling" | "offers";
type TransactionStatus = "reserved" | "ready_for_pickup" | "completed" | "cancelled" | "disputed";
type OfferStatus = "pending" | "countered" | "accepted" | "rejected" | "withdrawn" | "expired";

interface UserSummary { id: string; display_name?: string | null; }
interface Transaction {
  id: string;
  status: TransactionStatus;
  amount_cents: number | null;
  currency: string;
  fulfillment_method: string;
  buyer: UserSummary;
  seller: UserSummary;
  listing_id: string;
  created_at: string;
  completed_at: string | null;
}
interface Offer {
  id: string;
  status: OfferStatus;
  amount_cents: number | null;
  currency: string;
  listing_id: string;
  listing_title: string | null;
  buyer: UserSummary;
  seller: UserSummary;
  fulfillment_method: string;
  message: string | null;
  created_at: string;
  transaction_id: string | null;
}

function formatPrice(cents: number | null | undefined, currency: string): string {
  if (cents == null) return "—";
  return `${currency === "INR" ? "₹" : currency}${(cents / 100).toLocaleString("en-IN")}`;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

const TXN_STATUS: Record<TransactionStatus, { bg: string; color: string; label: string; icon: string }> = {
  reserved:         { bg: "#fffbeb", color: "#92400e", label: "Reserved",         icon: "⏳" },
  ready_for_pickup: { bg: "#dbeafe", color: "#1e40af", label: "Ready for Pickup", icon: "🤝" },
  completed:        { bg: "#f0fdf4", color: "#15803d", label: "Completed",         icon: "✓" },
  cancelled:        { bg: "#fef2f2", color: "#991b1b", label: "Cancelled",         icon: "✕" },
  disputed:         { bg: "#fef3c7", color: "#92400e", label: "Disputed",          icon: "⚠" },
};

const OFFER_STATUS: Record<OfferStatus, { bg: string; color: string; label: string; icon: string }> = {
  pending:   { bg: "#fffbeb", color: "#92400e", label: "Pending",   icon: "⏳" },
  countered: { bg: "#dbeafe", color: "#1e40af", label: "Countered", icon: "🔄" },
  accepted:  { bg: "#f0fdf4", color: "#15803d", label: "Accepted",  icon: "✓" },
  rejected:  { bg: "#fef2f2", color: "#991b1b", label: "Rejected",  icon: "✕" },
  withdrawn: { bg: "#f3f4f6", color: "#374151", label: "Withdrawn", icon: "↩" },
  expired:   { bg: "#f3f4f6", color: "#374151", label: "Expired",   icon: "⌛" },
};

export default function OrdersPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("buying");
  const [buying, setBuying] = useState<Transaction[]>([]);
  const [selling, setSelling] = useState<Transaction[]>([]);
  const [buyerOffers, setBuyerOffers] = useState<Offer[]>([]);
  const [sellerOffers, setSellerOffers] = useState<Offer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    Promise.all([
      fetch(`${API_BASE}/api/v1/transactions?role=buyer&limit=50`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => r.ok ? r.json() : []),
      fetch(`${API_BASE}/api/v1/transactions?role=seller&limit=50`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => r.ok ? r.json() : []),
      fetch(`${API_BASE}/api/v1/offers?role=buyer&limit=50`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => r.ok ? r.json() : []),
      fetch(`${API_BASE}/api/v1/offers?role=seller&limit=50`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => r.ok ? r.json() : []),
    ]).then(([b, s, bo, so]) => {
      setBuying(Array.isArray(b) ? b : []);
      setSelling(Array.isArray(s) ? s : []);
      setBuyerOffers(Array.isArray(bo) ? bo : []);
      setSellerOffers(Array.isArray(so) ? so : []);
    }).catch(() => setError("Failed to load orders"))
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  if (isLoading || loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  const pendingBuyerOffers = buyerOffers.filter((o) => o.status === "pending" || o.status === "countered");
  const pendingSellerOffers = sellerOffers.filter((o) => o.status === "pending");
  const totalPending = pendingBuyerOffers.length + pendingSellerOffers.length;

  const buyingActive = buying.filter((t) => t.status !== "completed" && t.status !== "cancelled");
  const sellingActive = selling.filter((t) => t.status !== "completed" && t.status !== "cancelled");

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={960}>
        <PageHeader
          eyebrow="Marketplace"
          title="Orders & Offers"
          subtitle="Track all your buying and selling activity."
        />

        {error && (
          <div style={{ background: colors.dangerSoft, border: `1px solid #fecaca`, color: colors.dangerText, borderRadius: radius.lg, padding: "10px 14px", marginBottom: 14 }}>
            {error}
          </div>
        )}

        {/* Tabs */}
        <div style={{ display: "flex", gap: "0.25rem", background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: "0.25rem", marginBottom: "1.5rem" }}>
          {([
            { key: "buying" as const,  label: "Buying",  count: buying.length },
            { key: "selling" as const, label: "Selling", count: selling.length },
            { key: "offers" as const,  label: "Offers",  count: totalPending },
          ]).map((t) => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{ flex: 1, padding: "0.6rem", borderRadius: 8, border: "none", fontWeight: 600, fontSize: "0.875rem", cursor: "pointer", background: tab === t.key ? "#1f2933" : "transparent", color: tab === t.key ? "white" : "#6b7280", display: "flex", alignItems: "center", justifyContent: "center", gap: "0.375rem", transition: "all 0.15s" }}>
              {t.label}
              {t.count > 0 && (
                <span style={{ background: tab === t.key ? "rgba(255,255,255,0.2)" : t.key === "offers" && totalPending > 0 ? "#dc2626" : "#f3f4f6", color: tab === t.key ? "white" : t.key === "offers" && totalPending > 0 ? "white" : "#374151", borderRadius: 10, padding: "0.1rem 0.5rem", fontSize: "0.72rem", fontWeight: 700 }}>
                  {t.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* ── BUYING TAB ── */}
        {tab === "buying" && (
          <>
            {buyingActive.length > 0 && (
              <>
                <SectionHeader label="Active Orders" count={buyingActive.length} />
                <OrderList orders={buyingActive} role="buying" />
              </>
            )}
            {buying.filter((t) => t.status === "completed").length > 0 && (
              <>
                <SectionHeader label="Completed" count={buying.filter((t) => t.status === "completed").length} />
                <OrderList orders={buying.filter((t) => t.status === "completed")} role="buying" />
              </>
            )}
            {buying.length === 0 && <EmptyState icon="🛒" title="No orders yet" hint="Browse listings and make an offer to start buying." cta={{ href: "/search", label: "Browse Listings" }} />}
          </>
        )}

        {/* ── SELLING TAB ── */}
        {tab === "selling" && (
          <>
            {sellingActive.length > 0 && (
              <>
                <SectionHeader label="Active Sales" count={sellingActive.length} />
                <OrderList orders={sellingActive} role="selling" />
              </>
            )}
            {selling.filter((t) => t.status === "completed").length > 0 && (
              <>
                <SectionHeader label="Completed" count={selling.filter((t) => t.status === "completed").length} />
                <OrderList orders={selling.filter((t) => t.status === "completed")} role="selling" />
              </>
            )}
            {selling.length === 0 && <EmptyState icon="📦" title="No sales yet" hint="Your sales will appear here once buyers accept your terms." cta={{ href: "/listings/create", label: "Create Listing" }} />}
          </>
        )}

        {/* ── OFFERS TAB ── */}
        {tab === "offers" && (
          <>
            {pendingSellerOffers.length > 0 && (
              <>
                <SectionHeader label="Offers on Your Listings" count={pendingSellerOffers.length} highlight />
                <OfferList offers={pendingSellerOffers} role="seller" />
              </>
            )}
            {pendingBuyerOffers.length > 0 && (
              <>
                <SectionHeader label="Your Pending Offers" count={pendingBuyerOffers.length} />
                <OfferList offers={pendingBuyerOffers} role="buyer" />
              </>
            )}
            {(sellerOffers.filter((o) => o.status !== "pending").length > 0 || buyerOffers.filter((o) => o.status !== "pending" && o.status !== "countered").length > 0) && (
              <>
                <SectionHeader label="Past Offers" count={sellerOffers.filter((o) => o.status !== "pending").length + buyerOffers.filter((o) => o.status !== "pending" && o.status !== "countered").length} />
                <OfferList offers={[...sellerOffers.filter((o) => o.status !== "pending"), ...buyerOffers.filter((o) => o.status !== "pending" && o.status !== "countered")]} role="past" />
              </>
            )}
            {totalPending === 0 && sellerOffers.length === 0 && buyerOffers.length === 0 && (
              <EmptyState icon="💰" title="No offers yet" hint="Make offers on listings you like, or accept offers on your own." cta={{ href: "/search", label: "Browse Listings" }} />
            )}
          </>
        )}
      </Container>
    </div>
  );
}

function SectionHeader({ label, count, highlight }: { label: string; count: number; highlight?: boolean }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", margin: "1.25rem 0 0.75rem" }}>
      <h2 style={{ margin: 0, fontSize: "0.8rem", fontWeight: 700, color: "#374151", textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</h2>
      <span style={{ background: highlight ? "#dc2626" : "#e5e7eb", color: highlight ? "white" : "#374151", borderRadius: 10, padding: "0.1rem 0.5rem", fontSize: "0.7rem", fontWeight: 700 }}>
        {count}
      </span>
    </div>
  );
}

function OrderList({ orders, role }: { orders: Transaction[]; role: "buying" | "selling" }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
      {orders.map((order) => {
        const other = role === "buying" ? order.seller : order.buyer;
        const otherName = other.display_name ?? `User ${other.id.slice(0, 8)}`;
        const s = TXN_STATUS[order.status];
        return (
          <Link key={order.id} href={`/orders/${order.id}`} style={{ textDecoration: "none" }}>
            <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 10, padding: "1rem", display: "flex", alignItems: "center", gap: "1rem", transition: "box-shadow 0.15s, transform 0.1s" }}
              onMouseEnter={(e) => (e.currentTarget as HTMLDivElement).style.boxShadow = "0 4px 12px rgba(0,0,0,0.08)"}
              onMouseLeave={(e) => (e.currentTarget as HTMLDivElement).style.boxShadow = "none"}
            >
              <div style={{ width: 52, height: 64, background: "#eaf2ff", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.5rem", flexShrink: 0, border: "1px solid #e5e7eb" }}>
                📚
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem", flexWrap: "wrap" }}>
                  <span style={{ fontWeight: 700, fontSize: "0.875rem", color: "#1f2933" }}>Order #{order.id.slice(0, 8)}</span>
                  <span style={{ background: s.bg, color: s.color, fontSize: "0.7rem", fontWeight: 700, padding: "0.15rem 0.5rem", borderRadius: 20 }}>
                    {s.icon} {s.label}
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: "1.05rem", fontWeight: 800, color: "#2563eb" }}>
                  {formatPrice(order.amount_cents, order.currency)}
                </p>
                <p style={{ margin: "0.2rem 0 0", fontSize: "0.75rem", color: "#6b7280" }}>
                  {role === "buying" ? "Seller" : "Buyer"}: <strong style={{ color: "#374151" }}>{otherName}</strong> · {timeAgo(order.created_at)} · {order.fulfillment_method === "pickup" ? "🤝 Pickup" : "📦 Shipping"}
                </p>
              </div>
              <span style={{ color: "#9ca3af", fontSize: "1.2rem", flexShrink: 0 }}>›</span>
            </div>
          </Link>
        );
      })}
    </div>
  );
}

function OfferList({ offers, role }: { offers: Offer[]; role: "buyer" | "seller" | "past" }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.625rem" }}>
      {offers.map((offer) => {
        const s = OFFER_STATUS[offer.status];
        const other = role === "seller" ? offer.buyer : offer.seller;
        const otherName = other.display_name ?? `User ${other.id.slice(0, 8)}`;
        return (
          <Link key={offer.id} href={offer.transaction_id ? `/orders/${offer.transaction_id}` : `/listings/${offer.listing_id}`} style={{ textDecoration: "none" }}>
            <div style={{ background: "#fff", border: `1px solid ${role === "seller" && offer.status === "pending" ? "#fcd34d" : "#e5e7eb"}`, borderLeft: role === "seller" && offer.status === "pending" ? "4px solid #f59e0b" : "1px solid #e5e7eb", borderRadius: 10, padding: "1rem", transition: "box-shadow 0.15s" }}
              onMouseEnter={(e) => (e.currentTarget as HTMLDivElement).style.boxShadow = "0 4px 12px rgba(0,0,0,0.08)"}
              onMouseLeave={(e) => (e.currentTarget as HTMLDivElement).style.boxShadow = "none"}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem", marginBottom: "0.5rem" }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ margin: "0 0 0.2rem", fontSize: "0.72rem", color: "#2563eb", fontWeight: 600 }}>
                    📚 {offer.listing_title ?? "Listing"}
                  </p>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                    <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "#2563eb" }}>
                      {formatPrice(offer.amount_cents, offer.currency)}
                    </span>
                    <span style={{ background: s.bg, color: s.color, fontSize: "0.7rem", fontWeight: 700, padding: "0.15rem 0.5rem", borderRadius: 20 }}>
                      {s.icon} {s.label}
                    </span>
                  </div>
                </div>
                <span style={{ fontSize: "0.72rem", color: "#9ca3af", flexShrink: 0 }}>{timeAgo(offer.created_at)}</span>
              </div>
              <p style={{ margin: 0, fontSize: "0.78rem", color: "#6b7280" }}>
                {role === "seller" ? "From" : "To"}: <strong style={{ color: "#374151" }}>{otherName}</strong> · {offer.fulfillment_method === "pickup" ? "🤝 Pickup" : "📦 Shipping"}
              </p>
              {offer.message && (
                <p style={{ margin: "0.5rem 0 0", fontSize: "0.8rem", color: "#374151", fontStyle: "italic", background: "#f9fafb", padding: "0.5rem 0.625rem", borderRadius: 6 }}>
                  "{offer.message}"
                </p>
              )}
              {role === "seller" && offer.status === "pending" && (
                <p style={{ margin: "0.5rem 0 0", fontSize: "0.75rem", color: "#92400e", fontWeight: 600 }}>
                  → Tap to view listing and respond
                </p>
              )}
            </div>
          </Link>
        );
      })}
    </div>
  );
}

function EmptyState({ icon, title, hint, cta }: { icon: string; title: string; hint: string; cta?: { href: string; label: string } }) {
  return (
    <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 12, padding: "4rem 2rem", textAlign: "center" }}>
      <div style={{ fontSize: "2.5rem", marginBottom: "0.75rem" }}>{icon}</div>
      <h3 style={{ color: "#1f2933", margin: "0 0 0.5rem", fontSize: "1rem", fontWeight: 700 }}>{title}</h3>
      <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: "0 0 1.5rem" }}>{hint}</p>
      {cta && (
        <Link href={cta.href} style={{ display: "inline-block", background: "#2563eb", color: "white", padding: "0.65rem 1.5rem", borderRadius: 8, fontWeight: 700, fontSize: "0.875rem", textDecoration: "none" }}>
          {cta.label}
        </Link>
      )}
    </div>
  );
}
