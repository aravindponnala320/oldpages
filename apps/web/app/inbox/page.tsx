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
  Input,
  LinkButton,
  PageHeader,
  Spinner,
  colors,
  font,
  radius,
} from "../../components/ui";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

interface UserSummary {
  id: string;
  display_name?: string | null;
  username?: string | null;
}
interface ConversationMember { role: string; status: string; user: UserSummary; }
interface Conversation {
  id: string;
  status: string;
  listing_id: string | null;
  listing_title: string | null;
  last_message_at: string | null;
  last_message_preview: string | null;
  members: ConversationMember[];
  unread_count: number;
  created_at: string;
}

function timeAgo(iso: string | null | undefined): string {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 60_000) return "just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h`;
  if (diff < 7 * 86_400_000) return new Date(iso).toLocaleDateString("en-IN", { weekday: "short" });
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

export default function InboxPage() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    Promise.all([
      fetch(`${API_BASE}/api/v1/conversations?limit=50`, { headers: { Authorization: `Bearer ${token}` } })
        .then((r) => (r.ok ? r.json() : { items: [] })),
      fetch(`${API_BASE}/api/v1/chat-requests?role=recipient&status=pending&limit=50`, {
        headers: { Authorization: `Bearer ${token}` },
      }).then((r) => (r.ok ? r.json() : [])),
    ])
      .then(([convData, requests]) => {
        setConversations(convData.items ?? []);
        setPendingCount(
          Array.isArray(requests) ? requests.filter((r: { status: string }) => r.status === "pending").length : 0,
        );
      })
      .catch(() => setError("Failed to load inbox"))
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  if (isLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
        <Spinner size="lg" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  const totalUnread = conversations.reduce((s, c) => s + c.unread_count, 0);

  const filtered = conversations.filter((c) => {
    if (!search) return true;
    const q = search.toLowerCase();
    const otherMember = c.members.find((m) => m.user.id !== user?.id);
    const name = otherMember?.user.display_name ?? "";
    return name.toLowerCase().includes(q) || (c.listing_title ?? "").toLowerCase().includes(q);
  });

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={800}>
        <PageHeader
          eyebrow="Messages"
          title="Inbox"
          subtitle={totalUnread > 0 ? `${totalUnread} unread` : "Your conversations with buyers and sellers"}
          actions={
            <Link
              href="/chat-requests"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                background: colors.surface,
                border: `1px solid ${colors.borderStrong}`,
                color: colors.textMuted,
                padding: "9px 14px",
                borderRadius: radius.lg,
                fontSize: font.size.base,
                fontWeight: font.weight.semibold,
                textDecoration: "none",
              }}
            >
              Chat Requests
              {pendingCount > 0 && <Badge variant="danger" label={String(pendingCount)} />}
            </Link>
          }
        />

        {pendingCount > 0 && (
          <Link href="/chat-requests" style={{ textDecoration: "none" }}>
            <div
              style={{
                background: colors.warningSoft,
                border: `1px solid #fcd34d`,
                borderRadius: radius.lg,
                padding: "12px 16px",
                marginBottom: 14,
                display: "flex",
                alignItems: "center",
                gap: 12,
              }}
            >
              <span style={{ fontSize: 22 }}>⏳</span>
              <div style={{ flex: 1 }}>
                <p style={{ margin: 0, fontWeight: font.weight.bold, color: colors.warningText, fontSize: font.size.base }}>
                  {pendingCount} pending chat request{pendingCount !== 1 ? "s" : ""}
                </p>
                <p style={{ margin: 0, color: "#b45309", fontSize: font.size.sm }}>Tap to review and accept or decline</p>
              </div>
              <span style={{ color: "#b45309", fontWeight: font.weight.bold }}>→</span>
            </div>
          </Link>
        )}

        {error && (
          <div
            role="alert"
            style={{
              background: colors.dangerSoft,
              border: `1px solid #fecaca`,
              color: colors.dangerText,
              borderRadius: radius.lg,
              padding: "10px 14px",
              marginBottom: 14,
            }}
          >
            {error}
          </div>
        )}

        {conversations.length > 3 && (
          <div style={{ marginBottom: 14 }}>
            <Input
              placeholder="Search conversations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              prefix={<Icon.search size={16} color={colors.textFaint} />}
            />
          </div>
        )}

        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
            <Spinner size="md" />
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<Icon.chat size={26} color={colors.primary} />}
            title={search ? "No conversations match your search" : "No conversations yet"}
            description={
              search ? "Try a different search term." : "Browse listings and message sellers to start a conversation."
            }
            action={!search ? <LinkButton href="/search">Browse Listings</LinkButton> : undefined}
          />
        ) : (
          <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, borderRadius: radius.xl, overflow: "hidden" }}>
            {filtered.map((conv, i) => {
              const otherMember = conv.members.find((m) => m.user.id !== user?.id);
              const otherName = otherMember?.user.display_name ?? `User ${otherMember?.user.id?.slice(0, 8) ?? "?"}`;
              const isUnread = conv.unread_count > 0;

              return (
                <Link
                  key={conv.id}
                  href={`/inbox/${conv.id}`}
                  style={{
                    textDecoration: "none",
                    display: "flex",
                    alignItems: "center",
                    gap: 14,
                    padding: "14px 18px",
                    borderBottom: i < filtered.length - 1 ? `1px solid ${colors.divider}` : "none",
                    background: isUnread ? colors.primarySoft : colors.surface,
                  }}
                >
                  <Avatar name={otherName} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8, marginBottom: 2 }}>
                      <span style={{ fontWeight: isUnread ? font.weight.bold : font.weight.semibold, fontSize: font.size.base, color: colors.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {otherName}
                      </span>
                      <span style={{ color: colors.textFaint, fontSize: font.size.xs, flexShrink: 0 }}>
                        {timeAgo(conv.last_message_at ?? conv.created_at)}
                      </span>
                    </div>
                    {conv.listing_title && (
                      <p style={{ margin: "0 0 2px", fontSize: font.size.xs, color: colors.primary, fontWeight: font.weight.semibold, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {conv.listing_title}
                      </p>
                    )}
                    <p style={{ margin: 0, fontSize: font.size.sm, color: isUnread ? colors.textMuted : colors.textSubtle, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontWeight: isUnread ? font.weight.medium : font.weight.normal }}>
                      {conv.last_message_preview ?? "Start of conversation"}
                    </p>
                  </div>
                  {isUnread && (
                    <div style={{
                      width: 22, height: 22, borderRadius: "50%", background: colors.primary,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      color: "#fff", fontSize: font.size.xs, fontWeight: font.weight.heavy, flexShrink: 0,
                    }}>
                      {conv.unread_count > 9 ? "9+" : conv.unread_count}
                    </div>
                  )}
                </Link>
              );
            })}
          </div>
        )}
      </Container>
    </div>
  );
}
