"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../contexts/AuthContext";
import { apiClient } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import {
  Button,
  Container,
  EmptyState,
  Icon,
  PageHeader,
  Spinner,
  colors,
  font,
  radius,
  useToast,
} from "../../components/ui";
import type { NotificationResponse, NotificationType } from "@oldpages/shared-types";

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

function getDateGroup(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / (1000 * 60 * 60 * 24));
  if (diff === 0) return "Today";
  if (diff === 1) return "Yesterday";
  if (diff < 7) return "This Week";
  return "Older";
}

const GROUP_ORDER = ["Today", "Yesterday", "This Week", "Older"];

function notifIcon(type: NotificationType): string {
  const icons: Record<string, string> = {
    chat_request: "💬",
    chat_accepted: "✅",
    chat_declined: "❌",
    message: "📩",
    saved_search_match: "🔍",
    system: "⚙️",
  };
  return icons[type] ?? "🔔";
}

function notifLink(notif: NotificationResponse): string {
  const { type, related_entity_id, related_entity_type } = notif;
  if (type === "message" && related_entity_id) return `/inbox/${related_entity_id}`;
  if (type === "chat_request") return "/chat-requests";
  if (type === "chat_accepted" && related_entity_id) return `/inbox/${related_entity_id}`;
  if (type === "saved_search_match") return "/search";
  if (related_entity_type === "listing" && related_entity_id) return `/listings/${related_entity_id}`;
  return "#";
}

export default function NotificationsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [markingAll, setMarkingAll] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const token = getAccessToken();
    if (!token) return;
    apiClient
      .listNotifications(token, { limit: 50 })
      .then((res) => setNotifications(res.items))
      .catch((err) => setError(err.message ?? "Failed to load notifications"))
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  const handleMarkAllRead = async () => {
    const token = getAccessToken();
    if (!token) return;
    setMarkingAll(true);
    const unread = notifications.filter((n) => n.status === "unread");
    await Promise.allSettled(unread.map((n) => apiClient.markNotificationRead(n.id, token)));
    setNotifications((prev) =>
      prev.map((n) => (n.status === "unread" ? { ...n, status: "read" } : n)),
    );
    setMarkingAll(false);
    toast("Marked all notifications as read", "success");
  };

  const handleClick = async (notif: NotificationResponse) => {
    if (notif.status !== "unread") return;
    const token = getAccessToken();
    if (token) {
      await apiClient.markNotificationRead(notif.id, token).catch(() => {});
      setNotifications((prev) =>
        prev.map((n) => (n.id === notif.id ? { ...n, status: "read" } : n)),
      );
    }
  };

  if (isLoading || loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  const unreadCount = notifications.filter((n) => n.status === "unread").length;

  const grouped: Record<string, NotificationResponse[]> = {};
  for (const notif of notifications) {
    const g = getDateGroup(notif.created_at);
    (grouped[g] ??= []).push(notif);
  }

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={780}>
        <PageHeader
          eyebrow="Inbox"
          title="Notifications"
          subtitle={unreadCount > 0 ? `${unreadCount} unread` : "You're all caught up."}
          actions={
            unreadCount > 0 && (
              <Button variant="secondary" size="sm" loading={markingAll} onClick={handleMarkAllRead}>
                Mark all read
              </Button>
            )
          }
        />

        {error && (
          <div
            role="alert"
            style={{
              background: colors.dangerSoft,
              border: `1px solid #fecaca`,
              color: colors.dangerText,
              borderRadius: radius.lg,
              padding: "10px 14px",
              marginBottom: 16,
            }}
          >
            {error}
          </div>
        )}

        {notifications.length === 0 ? (
          <EmptyState
            icon={<Icon.bell size={26} color={colors.primary} />}
            title="No notifications yet"
            description="You'll see notifications for messages, offers, and updates here."
          />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            {GROUP_ORDER.map((group) => {
              const items = grouped[group] ?? [];
              if (!items.length) return null;
              return (
                <div key={group}>
                  <h2
                    style={{
                      fontSize: font.size.xs,
                      fontWeight: font.weight.bold,
                      color: colors.textFaint,
                      textTransform: "uppercase",
                      letterSpacing: "0.08em",
                      margin: "0 0 10px",
                    }}
                  >
                    {group}
                  </h2>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {items.map((notif) => {
                      const href = notifLink(notif);
                      const isUnread = notif.status === "unread";
                      return (
                        <Link
                          key={notif.id}
                          href={href}
                          onClick={() => handleClick(notif)}
                          style={{
                            textDecoration: "none",
                            background: isUnread ? colors.primarySoft : colors.surface,
                            border: `1px solid ${colors.border}`,
                            borderLeft: isUnread ? `3px solid ${colors.primary}` : `1px solid ${colors.border}`,
                            borderRadius: radius.lg,
                            padding: 14,
                            display: "flex",
                            gap: 12,
                            alignItems: "flex-start",
                          }}
                        >
                          <span style={{ fontSize: 22, flexShrink: 0, lineHeight: 1 }}>{notifIcon(notif.type)}</span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <p style={{ margin: 0, fontWeight: isUnread ? font.weight.bold : font.weight.medium, fontSize: font.size.base, color: colors.text }}>
                              {notif.title}
                            </p>
                            <p style={{ margin: "2px 0 0", fontSize: font.size.sm, color: colors.textSubtle, lineHeight: 1.5 }}>
                              {notif.body}
                            </p>
                          </div>
                          <div style={{ flexShrink: 0, textAlign: "right", display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
                            <span style={{ color: colors.textFaint, fontSize: font.size.xs }}>{timeAgo(notif.created_at)}</span>
                            {isUnread && (
                              <span style={{ width: 8, height: 8, borderRadius: "50%", background: colors.primary }} />
                            )}
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Container>
    </div>
  );
}
