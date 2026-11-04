"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../contexts/AuthContext";
import { getAccessToken } from "../../lib/auth";
import {
  Avatar,
  Badge,
  Button,
  Container,
  EmptyState,
  Icon,
  PageHeader,
  Spinner,
  Tabs,
  colors,
  font,
  radius,
  useToast,
} from "../../components/ui";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

interface UserSummary { id: string; display_name?: string | null; username?: string | null; }
interface ChatRequest {
  id: string;
  status: "pending" | "accepted" | "declined" | "blocked";
  initial_message: string | null;
  listing_id: string;
  listing_title: string | null;
  requester: UserSummary;
  recipient: UserSummary;
  conversation_id: string | null;
  created_at: string;
  responded_at: string | null;
}

const STATUS_VARIANT: Record<ChatRequest["status"], "warning" | "success" | "danger" | "default"> = {
  pending: "warning",
  accepted: "success",
  declined: "danger",
  blocked: "default",
};

const STATUS_LABEL: Record<ChatRequest["status"], string> = {
  pending: "Pending",
  accepted: "Accepted",
  declined: "Declined",
  blocked: "Blocked",
};

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 60_000) return "just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

export default function ChatRequestsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [incoming, setIncoming] = useState<ChatRequest[]>([]);
  const [sent, setSent] = useState<ChatRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [tab, setTab] = useState<"incoming" | "sent">("incoming");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/login");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    Promise.all([
      fetch(`${API_BASE}/api/v1/chat-requests?role=recipient&limit=50`, {
        headers: { Authorization: `Bearer ${token}` },
      }).then((r) => (r.ok ? r.json() : [])),
      fetch(`${API_BASE}/api/v1/chat-requests?role=requester&limit=50`, {
        headers: { Authorization: `Bearer ${token}` },
      }).then((r) => (r.ok ? r.json() : [])),
    ])
      .then(([inc, snt]) => {
        setIncoming(Array.isArray(inc) ? inc : []);
        setSent(Array.isArray(snt) ? snt : []);
      })
      .catch(() => toast("Failed to load chat requests", "error"))
      .finally(() => setLoading(false));
  }, [isAuthenticated, toast]);

  async function handleAccept(req: ChatRequest) {
    const token = getAccessToken();
    if (!token) return;
    setActionLoading(req.id);
    try {
      const res = await fetch(`${API_BASE}/api/v1/chat-requests/${req.id}/accept`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to accept");
      if (data.conversation_id) router.push(`/inbox/${data.conversation_id}`);
      else setIncoming((prev) => prev.map((r) => (r.id === req.id ? { ...r, status: "accepted" as const } : r)));
      toast("Request accepted", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to accept", "error");
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDecline(req: ChatRequest) {
    const token = getAccessToken();
    if (!token) return;
    setActionLoading(req.id);
    try {
      const res = await fetch(`${API_BASE}/api/v1/chat-requests/${req.id}/decline`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error("Failed to decline");
      setIncoming((prev) => prev.map((r) => (r.id === req.id ? { ...r, status: "declined" as const } : r)));
      toast("Request declined", "info");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to decline", "error");
    } finally {
      setActionLoading(null);
    }
  }

  if (isLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", paddingTop: 60 }}>
        <Spinner size="lg" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  const pendingCount = incoming.filter((r) => r.status === "pending").length;
  const currentList = tab === "incoming" ? incoming : sent;

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={800}>
        <PageHeader
          eyebrow="Messages"
          title="Chat Requests"
          subtitle={
            pendingCount > 0
              ? `${pendingCount} pending request${pendingCount !== 1 ? "s" : ""} need your response`
              : "Manage chat requests for your listings."
          }
          actions={
            <Link
              href="/inbox"
              style={{ fontSize: font.size.base, color: colors.primary, fontWeight: font.weight.semibold, textDecoration: "none" }}
            >
              Open Inbox →
            </Link>
          }
        />

        <div style={{ marginBottom: 18 }}>
          <Tabs
            tabs={[
              { key: "incoming", label: "Incoming", count: incoming.length },
              { key: "sent",     label: "Sent",     count: sent.length },
            ]}
            value={tab}
            onChange={(k) => setTab(k as "incoming" | "sent")}
          />
        </div>

        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
            <Spinner size="md" />
          </div>
        ) : currentList.length === 0 ? (
          <EmptyState
            icon={<Icon.chat size={26} color={colors.primary} />}
            title={tab === "incoming" ? "No incoming requests" : "No sent requests"}
            description={
              tab === "incoming"
                ? "When someone messages you about a listing, it appears here."
                : "When you message a seller, it appears here."
            }
          />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {currentList.map((req) => {
              const isPending = req.status === "pending";
              const isActing = actionLoading === req.id;
              const otherUser = tab === "incoming" ? req.requester : req.recipient;
              const otherName = otherUser.display_name ?? `User ${otherUser.id.slice(0, 8)}`;

              return (
                <div
                  key={req.id}
                  style={{
                    background: colors.surface,
                    border: `1px solid ${isPending && tab === "incoming" ? "#bbf7d0" : colors.border}`,
                    borderLeft: isPending && tab === "incoming" ? `4px solid ${colors.primary}` : `1px solid ${colors.border}`,
                    borderRadius: radius.xl,
                    padding: 18,
                  }}
                >
                  <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                    <Avatar name={otherName} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
                        <span style={{ fontWeight: font.weight.bold, color: colors.text, fontSize: font.size.md }}>
                          {otherName}
                        </span>
                        <Badge variant={STATUS_VARIANT[req.status]} label={STATUS_LABEL[req.status]} />
                        <span style={{ color: colors.textFaint, fontSize: font.size.xs, marginLeft: "auto" }}>
                          {timeAgo(req.created_at)}
                        </span>
                      </div>

                      {req.listing_title && (
                        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
                          <span style={{ fontSize: font.size.xs, color: colors.textFaint }}>Re:</span>
                          <Link
                            href={`/listings/${req.listing_id}`}
                            style={{
                              fontSize: font.size.sm,
                              color: colors.primary,
                              fontWeight: font.weight.semibold,
                              textDecoration: "none",
                            }}
                          >
                            {req.listing_title}
                          </Link>
                        </div>
                      )}

                      {req.initial_message && (
                        <div
                          style={{
                            background: colors.surfaceMuted,
                            borderRadius: radius.md,
                            padding: "10px 14px",
                            marginBottom: 12,
                            borderLeft: `3px solid ${colors.borderStrong}`,
                          }}
                        >
                          <p style={{ color: colors.textMuted, fontSize: font.size.base, margin: 0, fontStyle: "italic", lineHeight: 1.55 }}>
                            &ldquo;{req.initial_message}&rdquo;
                          </p>
                        </div>
                      )}

                      {tab === "incoming" && isPending && (
                        <div style={{ display: "flex", gap: 8 }}>
                          <Button
                            variant="primary"
                            size="sm"
                            loading={isActing}
                            onClick={() => handleAccept(req)}
                            style={{ flex: 1 }}
                          >
                            Accept &amp; Chat
                          </Button>
                          <Button variant="secondary" size="sm" disabled={isActing} onClick={() => handleDecline(req)}>
                            Decline
                          </Button>
                        </div>
                      )}

                      {req.status === "accepted" && req.conversation_id && (
                        <Link
                          href={`/inbox/${req.conversation_id}`}
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: 6,
                            background: colors.primarySoft,
                            color: colors.primary,
                            border: `1px solid #bbf7d0`,
                            padding: "8px 14px",
                            borderRadius: radius.md,
                            fontSize: font.size.sm,
                            fontWeight: font.weight.semibold,
                            textDecoration: "none",
                          }}
                        >
                          Open Conversation →
                        </Link>
                      )}
                    </div>
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
