"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../contexts/AuthContext";
import { getAccessToken } from "../../lib/auth";
import {
  Avatar,
  Badge,
  Container,
  EmptyState,
  Icon,
  LinkButton,
  PageHeader,
  Section,
  Spinner,
  colors,
  font,
  radius,
  shadow,
} from "../../components/ui";
import type { ListingSearchResult, ConversationResponse, NotificationResponse } from "@oldpages/shared-types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function notificationIcon(type: string): string {
  const icons: Record<string, string> = {
    chat_request: "💬", chat_accepted: "✅", chat_declined: "❌",
    message: "📩", saved_search_match: "🔍", system: "⚙️",
  };
  return icons[type] ?? "🔔";
}

export default function DashboardPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  const [listings, setListings] = useState<ListingSearchResult[]>([]);
  const [conversations, setConversations] = useState<ConversationResponse[]>([]);
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated || !user) return;
    const token = getAccessToken();
    if (!token) return;

    setDataLoading(true);
    const headers = { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };

    Promise.all([
      fetch(`${API_BASE}/api/v1/search/listings?limit=5`, { headers }).then((r) => r.json()).catch(() => ({ items: [], result_count: 0 })),
      fetch(`${API_BASE}/api/v1/conversations?limit=5`, { headers }).then((r) => r.json()).catch(() => ({ items: [] })),
      fetch(`${API_BASE}/api/v1/notifications?limit=10`, { headers }).then((r) => r.json()).catch(() => ({ items: [] })),
    ])
      .then(([listingsRes, convsRes, notifsRes]) => {
        setListings(listingsRes.items ?? []);
        setConversations(convsRes.items ?? []);
        setNotifications(notifsRes.items ?? []);
      })
      .catch((err) => setError(err.message ?? "Failed to load dashboard data"))
      .finally(() => setDataLoading(false));
  }, [isAuthenticated, user]);

  if (isLoading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated || !user) return null;

  const unreadMessages = conversations.reduce((sum, c) => sum + c.unread_count, 0);
  const unreadNotifications = notifications.filter((n) => n.status === "unread").length;
  const activeListings = listings.length;
  const displayName = (user as { display_name?: string }).display_name ?? user.email.split("@")[0] ?? user.email;

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container>
        <PageHeader
          eyebrow="Welcome back"
          title={`Hi, ${displayName}`}
          subtitle="Here's what's happening with your account today."
          actions={<LinkButton href="/listings/create" leftIcon={<Icon.plus size={14} />}>List a Book</LinkButton>}
        />

        {error && (
          <div
            role="alert"
            style={{
              background: colors.dangerSoft, border: `1px solid #fecaca`, color: colors.dangerText,
              borderRadius: radius.lg, padding: "10px 14px", marginBottom: 16,
            }}
          >
            {error}
          </div>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 20 }}>
          <Stat label="Active Listings" value={dataLoading ? "—" : activeListings} icon={<Icon.book size={20} color={colors.primary} />} />
          <Stat label="Unread Messages" value={dataLoading ? "—" : unreadMessages} icon={<Icon.chat size={20} color={colors.primary} />} />
          <Stat label="Notifications" value={dataLoading ? "—" : unreadNotifications} icon={<Icon.bell size={20} color={colors.primary} />} />
          <Stat label="Completed Sales" value={dataLoading ? "—" : 0} icon={<Icon.check size={20} color={colors.primary} />} />
        </div>

        <div style={{ marginBottom: 20 }}>
          <Section title="Quick actions">
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <LinkButton href="/listings/create">List a Book</LinkButton>
              <LinkButton href="/search" variant="secondary">Browse Books</LinkButton>
              <LinkButton href="/orders" variant="secondary">My Orders</LinkButton>
              <LinkButton href="/offers" variant="secondary">My Offers</LinkButton>
            </div>
          </Section>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <Section
            title="Recent listings"
            actions={<Link href="/my-listings" style={viewAllStyle}>View all →</Link>}
          >
            {dataLoading ? (
              <div style={{ display: "flex", justifyContent: "center", padding: 24 }}><Spinner /></div>
            ) : listings.length === 0 ? (
              <EmptyState
                icon={<Icon.book size={22} color={colors.primary} />}
                title="No listings yet"
                action={<LinkButton href="/listings/create" size="sm">List Your First Book</LinkButton>}
              />
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {listings.map((l) => (
                  <Link key={l.id} href={`/listings/${l.id}`} style={rowLink}>
                    {l.image_url ? (
                      <img src={l.image_url} alt={l.title} style={{ width: 40, height: 54, objectFit: "cover", borderRadius: 4, flexShrink: 0 }} />
                    ) : (
                      <div style={{ width: 40, height: 54, background: colors.surfaceMuted, borderRadius: 4, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <Icon.book size={18} color={colors.textFaint} />
                      </div>
                    )}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ margin: 0, fontSize: font.size.base, fontWeight: font.weight.semibold, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: colors.text }}>
                        {l.title}
                      </p>
                      <p style={{ margin: "2px 0 0", fontSize: font.size.sm, color: colors.textSubtle }}>
                        {l.book.authors.join(", ")}
                      </p>
                    </div>
                    {l.price_amount_cents != null && (
                      <span style={{ fontSize: font.size.base, fontWeight: font.weight.bold, color: colors.text, flexShrink: 0 }}>
                        ₹{(l.price_amount_cents / 100).toFixed(0)}
                      </span>
                    )}
                  </Link>
                ))}
              </div>
            )}
          </Section>

          <Section
            title="Recent messages"
            actions={<Link href="/inbox" style={viewAllStyle}>View all →</Link>}
          >
            {dataLoading ? (
              <div style={{ display: "flex", justifyContent: "center", padding: 24 }}><Spinner /></div>
            ) : conversations.length === 0 ? (
              <EmptyState
                icon={<Icon.chat size={22} color={colors.primary} />}
                title="No conversations yet"
              />
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {conversations.map((conv) => {
                  const otherId = conv.members[0]?.user.id ?? "?";
                  return (
                    <Link key={conv.id} href={`/inbox/${conv.id}`} style={rowLink}>
                      <Avatar name={`User ${otherId.slice(0, 4)}`} size="sm" />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <p style={{ margin: 0, fontSize: font.size.base, fontWeight: font.weight.semibold, color: colors.text }}>Conversation</p>
                        <p style={{ margin: "2px 0 0", fontSize: font.size.sm, color: colors.textSubtle }}>
                          {conv.last_message_at ? timeAgo(conv.last_message_at) : "No messages yet"}
                        </p>
                      </div>
                      {conv.unread_count > 0 && <Badge variant="info" label={String(conv.unread_count)} />}
                    </Link>
                  );
                })}
              </div>
            )}
          </Section>
        </div>

        {!dataLoading && notifications.filter((n) => n.status === "unread").length > 0 && (
          <div style={{ marginTop: 20 }}>
            <Section
              title="Recent notifications"
              actions={<Link href="/notifications" style={viewAllStyle}>View all →</Link>}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {notifications.filter((n) => n.status === "unread").slice(0, 5).map((n) => (
                  <div key={n.id} style={{
                    display: "flex", alignItems: "flex-start", gap: 10,
                    padding: 12, background: colors.primarySoft, borderRadius: radius.lg,
                    borderLeft: `3px solid ${colors.primary}`,
                  }}>
                    <span style={{ fontSize: 18, flexShrink: 0 }}>{notificationIcon(n.type)}</span>
                    <div style={{ flex: 1 }}>
                      <p style={{ margin: 0, fontWeight: font.weight.semibold, fontSize: font.size.base, color: colors.text }}>{n.title}</p>
                      <p style={{ margin: "2px 0 0", fontSize: font.size.sm, color: colors.textSubtle }}>{n.body}</p>
                    </div>
                    <span style={{ color: colors.textFaint, fontSize: font.size.xs, flexShrink: 0 }}>{timeAgo(n.created_at)}</span>
                  </div>
                ))}
              </div>
            </Section>
          </div>
        )}
      </Container>
    </div>
  );
}

function Stat({ label, value, icon }: { label: string; value: string | number; icon: React.ReactNode }) {
  return (
    <div style={{
      background: colors.surface, border: `1px solid ${colors.border}`,
      borderRadius: radius.xl, padding: 18, boxShadow: shadow.sm,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
        <div style={{ width: 32, height: 32, borderRadius: radius.md, background: colors.primarySoft, display: "flex", alignItems: "center", justifyContent: "center" }}>
          {icon}
        </div>
      </div>
      <div style={{ fontSize: font.size["2xl"], fontWeight: font.weight.heavy, color: colors.text }}>{value}</div>
      <div style={{ fontSize: font.size.sm, color: colors.textSubtle, marginTop: 2 }}>{label}</div>
    </div>
  );
}

const viewAllStyle: React.CSSProperties = {
  color: colors.primary, fontSize: font.size.sm, textDecoration: "none", fontWeight: font.weight.medium,
};

const rowLink: React.CSSProperties = {
  textDecoration: "none", background: colors.surface, border: `1px solid ${colors.border}`,
  borderRadius: radius.lg, padding: "10px 12px", display: "flex", alignItems: "center", gap: 10,
};
