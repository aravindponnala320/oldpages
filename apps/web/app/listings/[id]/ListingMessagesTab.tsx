"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getAccessToken } from "../../../lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

interface UserSummary { id: string; display_name?: string | null; }
interface ConversationMember { role: string; user: UserSummary; }
interface Conversation {
  id: string;
  members: ConversationMember[];
  last_message_at: string | null;
  last_message_preview: string | null;
  unread_count: number;
  listing_title: string | null;
}

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 60_000) return "just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

function getInitials(name: string) {
  return name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();
}

interface Props {
  listingId: string;
  sellerId: string;
}

export function ListingMessagesTab({ listingId, sellerId }: Props) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSeller, setIsSeller] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) { setLoading(false); return; }

    // Decode JWT to get current user ID
    try {
      const part = token.split(".")[1];
      if (!part) return;
      const payload = JSON.parse(atob(part));
      const uid = payload.sub ?? null;
      setCurrentUserId(uid);
      setIsSeller(uid === sellerId);
    } catch { /* ignore */ }

    // Fetch conversations for this listing
    fetch(`${API_BASE}/api/v1/conversations?listing_id=${listingId}&limit=50`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : { items: [] })
      .then((data) => setConversations(data.items ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [listingId, sellerId]);

  if (!currentUserId) return null; // Not logged in — no tab shown
  if (!isSeller && conversations.length === 0) return null; // Buyer with no convo yet

  return (
    <div style={{ marginTop: "2rem" }}>
      {/* Tab header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem", paddingBottom: "0.75rem", borderBottom: "2px solid #e5e7eb" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
          <span style={{ fontSize: "1rem", fontWeight: 700, color: "#1f2933" }}>
            {isSeller ? "Buyer Messages" : "Your Conversation"}
          </span>
          {conversations.length > 0 && (
            <span style={{ background: "#2563eb", color: "white", borderRadius: 20, padding: "0.1rem 0.5rem", fontSize: "0.72rem", fontWeight: 700 }}>
              {conversations.length}
            </span>
          )}
          {conversations.some((c) => c.unread_count > 0) && (
            <span style={{ background: "#ef4444", color: "white", borderRadius: 20, padding: "0.1rem 0.5rem", fontSize: "0.7rem", fontWeight: 700 }}>
              {conversations.reduce((s, c) => s + c.unread_count, 0)} unread
            </span>
          )}
        </div>
        <Link href="/inbox" style={{ fontSize: "0.78rem", color: "#2563eb", fontWeight: 600, textDecoration: "none" }}>
          Open Inbox →
        </Link>
      </div>

      {loading && (
        <div style={{ padding: "2rem", textAlign: "center" }}>
          <div style={{ width: 24, height: 24, borderRadius: "50%", border: "3px solid #e5e7eb", borderTopColor: "#2563eb", animation: "spin 0.7s linear infinite", margin: "0 auto" }} />
        </div>
      )}

      {!loading && conversations.length === 0 && isSeller && (
        <div style={{ background: "#f9fafb", borderRadius: 10, padding: "2rem", textAlign: "center", border: "1px dashed #e5e7eb" }}>
          <p style={{ fontSize: "1.5rem", margin: "0 0 0.5rem" }}>💬</p>
          <p style={{ color: "#6b7280", fontSize: "0.875rem", margin: 0 }}>No messages yet. Buyers who message you about this listing will appear here.</p>
        </div>
      )}

      {!loading && conversations.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0", border: "1px solid #e5e7eb", borderRadius: 10, overflow: "hidden" }}>
          {conversations.map((conv, i) => {
            const other = conv.members.find((m) => m.user.id !== currentUserId);
            const otherName = other?.user.display_name ?? `User ${other?.user.id?.slice(0, 8) ?? "?"}`;
            const isUnread = conv.unread_count > 0;

            return (
              <Link key={conv.id} href={`/inbox/${conv.id}`} style={{ textDecoration: "none" }}>
                <div style={{
                  display: "flex", alignItems: "center", gap: "0.875rem",
                  padding: "0.875rem 1rem",
                  background: isUnread ? "#f0fdf8" : "#fff",
                  borderBottom: i < conversations.length - 1 ? "1px solid #f3f4f6" : "none",
                  transition: "background 0.1s",
                }}
                  onMouseEnter={(e) => (e.currentTarget as HTMLDivElement).style.background = isUnread ? "#e6faf3" : "#f9fafb"}
                  onMouseLeave={(e) => (e.currentTarget as HTMLDivElement).style.background = isUnread ? "#f0fdf8" : "#fff"}
                >
                  {/* Avatar */}
                  <div style={{ position: "relative", flexShrink: 0 }}>
                    <div style={{ width: 40, height: 40, borderRadius: "50%", background: "#2563eb", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontSize: "0.875rem", fontWeight: 700 }}>
                      {getInitials(otherName)}
                    </div>
                    {isUnread && (
                      <div style={{ position: "absolute", top: 0, right: 0, width: 10, height: 10, borderRadius: "50%", background: "#ef4444", border: "2px solid white" }} />
                    )}
                  </div>

                  {/* Content */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.2rem" }}>
                      <span style={{ fontWeight: isUnread ? 700 : 600, fontSize: "0.9rem", color: "#1f2933" }}>
                        {isSeller ? otherName : "Your conversation"}
                      </span>
                      <span style={{ fontSize: "0.72rem", color: "#9ca3af", flexShrink: 0 }}>
                        {timeAgo(conv.last_message_at)}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: "0.8rem", color: isUnread ? "#374151" : "#6b7280", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontWeight: isUnread ? 500 : 400 }}>
                      {conv.last_message_preview ?? "No messages yet"}
                    </p>
                  </div>

                  {/* Unread badge + arrow */}
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexShrink: 0 }}>
                    {isUnread && (
                      <div style={{ width: 20, height: 20, borderRadius: "50%", background: "#2563eb", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontSize: "0.65rem", fontWeight: 800 }}>
                        {conv.unread_count > 9 ? "9+" : conv.unread_count}
                      </div>
                    )}
                    <span style={{ color: "#d1d5db", fontSize: "0.875rem" }}>›</span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
