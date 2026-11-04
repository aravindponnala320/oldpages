"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../../contexts/AuthContext";
import { getAccessToken } from "../../../lib/auth";
import { Avatar, Badge, Spinner, colors, font, layout, radius } from "../../../components/ui";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const WS_BASE = typeof window !== "undefined"
  ? `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host.replace(/:\d+$/, ":8000")}`
  : "ws://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────

interface UserSummary { id: string; display_name?: string | null; username?: string | null; }
interface Message {
  id: string;
  body: string | null;
  sender: UserSummary;
  created_at: string;
  message_type: string;
  conversation_id: string;
  read_by_user_ids: string[];
  client_message_id?: string | null;
}
interface ListingCard {
  id: string;
  title: string;
  price_amount_cents: number | null;
  currency: string;
  negotiable: boolean;
  listing_modes: string[];
  status: string;
  image_url: string | null;
  condition: { condition: string } | null;
  location: { city: string; state?: string } | null;
}

interface ConversationMember { role: string; status: string; user: UserSummary; }
interface Conversation {
  id: string;
  listing_id: string | null;
  listing_title: string | null;
  members: ConversationMember[];
  status: string;
  unread_count: number;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatTime(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const isToday = d.toDateString() === now.toDateString();
  if (isToday) return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const yesterday = new Date(now); yesterday.setDate(yesterday.getDate() - 1);
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" }) + " · " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function dateSeparator(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) return "Today";
  const yesterday = new Date(now); yesterday.setDate(yesterday.getDate() - 1);
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return d.toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" });
}

function clientId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function getInitials(name: string): string {
  return name.split(" ").map((w) => w[0] ?? "").join("").slice(0, 2).toUpperCase() || "?";
}

// ── Main ───────────────────────────────────────────────────────────────────

export default function ConversationPage() {
  const { id } = useParams<{ id: string }>();
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();

  const [conv, setConv] = useState<Conversation | null>(null);
  const [listing, setListing] = useState<ListingCard | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [input, setInput] = useState("");
  const [connStatus, setConnStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const [error, setError] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const seenIds = useRef(new Set<string>());
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Load conversation + messages ──────────────────────────────────────

  const loadConversation = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !id) return;
    const [convRes, msgRes] = await Promise.all([
      fetch(`${API_BASE}/api/v1/conversations?limit=100`, { headers: { Authorization: `Bearer ${token}` } }),
      fetch(`${API_BASE}/api/v1/conversations/${id}/messages?limit=100`, { headers: { Authorization: `Bearer ${token}` } }),
    ]);
    if (convRes.ok) {
      const data = await convRes.json();
      const found: Conversation | null = (data.items ?? []).find((c: Conversation) => c.id === id) ?? null;
      setConv(found);
      // Fetch the listing for context
      if (found?.listing_id) {
        fetch(`${API_BASE}/api/v1/listings/${found.listing_id}`, { headers: { Authorization: `Bearer ${token}` } })
          .then((r) => r.ok ? r.json() : null)
          .then((l) => {
            if (l) setListing({
              id: l.id,
              title: l.title ?? l.book?.title ?? "Listing",
              price_amount_cents: l.price_amount_cents,
              currency: l.currency ?? "INR",
              negotiable: l.negotiable,
              listing_modes: l.listing_modes ?? [],
              status: l.status,
              image_url: l.images?.find((i: { is_primary: boolean; public_url?: string }) => i.is_primary)?.public_url ?? l.images?.[0]?.public_url ?? null,
              condition: l.condition ?? null,
              location: l.location ?? null,
            });
          }).catch(() => {});
      }
    }
    if (msgRes.ok) {
      const data = await msgRes.json();
      const items: Message[] = [...(data.items ?? [])].reverse();
      items.forEach((m) => seenIds.current.add(m.id));
      setMessages(items);
    }
    setLoading(false);
  }, [id]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) { router.replace("/login"); return; }
    if (!isAuthenticated) return;
    loadConversation();
  }, [isAuthenticated, isLoading, loadConversation, router]);

  // ── Scroll to bottom on new message ──────────────────────────────────

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── WebSocket with auto-reconnect ─────────────────────────────────────

  const connectWS = useCallback(() => {
    const token = getAccessToken();
    if (!token) return;

    if (wsRef.current) {
      wsRef.current.close();
    }

    setConnStatus("connecting");
    const ws = new WebSocket(`${WS_BASE}/ws/conversations?access_token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnStatus("connected");
      setError(null);
    };

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data as string);
        if (data.type === "message.created") {
          const msg = data.message as Message;
          if (msg.conversation_id === id && !seenIds.current.has(msg.id)) {
            seenIds.current.add(msg.id);
            // Remove optimistic version if this is our own sent message
            setMessages((prev) => {
              const withoutOptimistic = prev.filter((m) => m.client_message_id !== msg.client_message_id);
              return [...withoutOptimistic, msg];
            });
          }
        }
        if (data.type === "pong") {
          // heartbeat ack
        }
      } catch { /* ignore parse errors */ }
    };

    ws.onclose = () => {
      setConnStatus("disconnected");
      // Auto-reconnect after 3s
      reconnectTimer.current = setTimeout(() => connectWS(), 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [id]);

  useEffect(() => {
    if (!isAuthenticated || loading) return;
    connectWS();

    // Heartbeat ping every 30s to keep connection alive
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
  }, [isAuthenticated, loading, connectWS]);

  // ── Send message ──────────────────────────────────────────────────────

  async function sendMessage() {
    const text = input.trim();
    if (!text || sending) return;
    const token = getAccessToken();
    if (!token) return;

    const cid = clientId();
    const optimistic: Message = {
      id: cid,
      body: text,
      sender: { id: user?.id ?? "", display_name: null },
      created_at: new Date().toISOString(),
      message_type: "text",
      conversation_id: id,
      read_by_user_ids: [],
      client_message_id: cid,
    };
    seenIds.current.add(cid);
    setMessages((prev) => [...prev, optimistic]);
    setInput("");
    setSending(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/conversations/${id}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ body: text, client_message_id: cid, message_type: "text" }),
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail ?? "Failed to send");
      }
      const sent: Message = await res.json();
      seenIds.current.add(sent.id);
      // Replace optimistic with confirmed
      setMessages((prev) => prev.map((m) => m.id === cid ? { ...sent, client_message_id: cid } : m));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
      setMessages((prev) => prev.filter((m) => m.id !== cid));
      setInput(text);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }

  // ── Loading / unauthenticated ─────────────────────────────────────────

  if (isLoading || loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", height: `calc(100vh - ${layout.headerHeight}px)`, alignItems: "center", justifyContent: "center", background: colors.bg }}>
        <Spinner size="lg" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  // ── Derived ───────────────────────────────────────────────────────────

  const otherMember = conv?.members.find((m) => m.user.id !== user?.id);
  const otherName = otherMember?.user.display_name ?? `User ${otherMember?.user.id?.slice(0, 8) ?? "?"}`;

  const grouped: { date: string; msgs: Message[] }[] = [];
  for (const msg of messages) {
    const label = dateSeparator(msg.created_at);
    const last = grouped[grouped.length - 1];
    if (!last || last.date !== label) grouped.push({ date: label, msgs: [msg] });
    else last.msgs.push(msg);
  }

  // ── Render ────────────────────────────────────────────────────────────

  return (
    <div style={{ display: "flex", flexDirection: "column", height: `calc(100vh - ${layout.headerHeight}px)`, background: colors.bg }}>

      {/* ── Header ── */}
      <div style={{
        background: colors.surface,
        borderBottom: `1px solid ${colors.border}`,
        display: "flex", alignItems: "center", gap: 12,
        padding: "0 20px", height: 64, flexShrink: 0,
      }}>
        <button
          onClick={() => router.push("/inbox")}
          style={{ background: "none", border: "none", cursor: "pointer", color: colors.textSubtle, fontSize: 20, padding: 6, borderRadius: radius.md, display: "flex", alignItems: "center", lineHeight: 1 }}
        >
          ←
        </button>

        <Avatar name={otherName} size="md" />

        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ margin: 0, fontWeight: font.weight.bold, fontSize: font.size.md, color: colors.text, lineHeight: 1.3 }}>
            {otherName}
          </p>
          {conv?.listing_title ? (
            <Link href={`/listings/${conv.listing_id}`} style={{ fontSize: font.size.xs, color: colors.primary, textDecoration: "none", fontWeight: font.weight.semibold }}>
              {conv.listing_title}
            </Link>
          ) : (
            <span style={{ fontSize: font.size.xs, color: colors.textFaint }}>Conversation</span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div
            style={{
              width: 8, height: 8, borderRadius: "50%",
              background: connStatus === "connected" ? colors.success : connStatus === "connecting" ? colors.warning : colors.danger,
              transition: "background 0.3s",
            }}
          />
          <span style={{ fontSize: font.size.xs, color: colors.textFaint }}>
            {connStatus === "connected" ? "Live" : connStatus === "connecting" ? "Connecting…" : "Offline"}
          </span>
        </div>

        {(listing?.id ?? conv?.listing_id) && (
          <Link
            href={`/listings/${listing?.id ?? conv?.listing_id}`}
            style={{
              background: colors.primarySoft,
              border: `1px solid #c7dbff`,
              color: colors.primary,
              padding: "6px 14px",
              borderRadius: radius.md,
              fontSize: font.size.sm,
              fontWeight: font.weight.semibold,
              textDecoration: "none",
              whiteSpace: "nowrap",
              flexShrink: 0,
            }}
          >
            View Listing →
          </Link>
        )}
      </div>

      {/* ── Listing card ── */}
      {listing && (
        <Link href={`/listings/${listing.id}`} style={{ textDecoration: "none", flexShrink: 0 }}>
          <div style={{
            background: colors.surface,
            borderBottom: `1px solid ${colors.border}`,
            padding: "12px 20px",
            display: "flex", alignItems: "center", gap: 14,
          }}>
            <div style={{
              width: 44, height: 56, borderRadius: radius.md, flexShrink: 0,
              background: colors.primarySoft, overflow: "hidden",
              display: "flex", alignItems: "center", justifyContent: "center",
              border: `1px solid ${colors.border}`,
            }}>
              {listing.image_url
                ? <img src={listing.image_url} alt={listing.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                : <span style={{ fontSize: 20 }}>📚</span>
              }
            </div>

            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                <span style={{ fontSize: font.size.xs, color: colors.primary, fontWeight: font.weight.bold, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  {listing.listing_modes[0] === "sell" ? "For Sale" : listing.listing_modes[0] === "exchange" ? "Exchange" : listing.listing_modes[0] === "donate" ? "Free" : listing.listing_modes[0] ?? "Listing"}
                </span>
                {listing.status !== "active" && <Badge variant="warning" label={listing.status} />}
              </div>
              <p style={{ margin: 0, fontWeight: font.weight.bold, fontSize: font.size.base, color: colors.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {listing.title}
              </p>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 3 }}>
                {listing.price_amount_cents != null ? (
                  <span style={{ fontSize: font.size.base, fontWeight: font.weight.heavy, color: colors.text }}>
                    ₹{(listing.price_amount_cents / 100).toLocaleString("en-IN")}
                    {listing.negotiable && <span style={{ fontSize: font.size.xs, color: colors.textSubtle, fontWeight: font.weight.normal, marginLeft: 3 }}>· Negotiable</span>}
                  </span>
                ) : (
                  <span style={{ fontSize: font.size.base, fontWeight: font.weight.bold, color: "#7c3aed" }}>Free</span>
                )}
                {listing.condition?.condition && (
                  <span style={{ fontSize: font.size.xs, color: colors.textSubtle }}>
                    · {listing.condition.condition.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                  </span>
                )}
                {listing.location?.city && (
                  <span style={{ fontSize: font.size.xs, color: colors.textFaint }}>
                    · {listing.location.city}
                  </span>
                )}
              </div>
            </div>

            <span style={{ color: colors.textFaint, fontSize: font.size.base, flexShrink: 0 }}>→</span>
          </div>
        </Link>
      )}

      {/* ── Messages ── */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px", display: "flex", flexDirection: "column" }}>

        {error && (
          <div style={{ background: colors.dangerSoft, border: `1px solid #fecaca`, borderRadius: radius.md, padding: "10px 14px", marginBottom: 12, fontSize: font.size.sm, color: colors.dangerText }}>
            {error} <button onClick={() => setError(null)} style={{ background: "none", border: "none", cursor: "pointer", color: colors.dangerText, marginLeft: 8 }}>✕</button>
          </div>
        )}

        {messages.length === 0 && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 12 }}>
            <div style={{ width: 56, height: 56, borderRadius: "50%", background: colors.primarySoft, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26 }}>👋</div>
            <p style={{ color: colors.textMuted, fontWeight: font.weight.semibold, margin: 0, fontSize: font.size.md }}>Start the conversation</p>
            <p style={{ color: colors.textSubtle, margin: 0, fontSize: font.size.base, textAlign: "center", maxWidth: 280 }}>
              Send a message to {otherName} about {conv?.listing_title ?? "this listing"}.
            </p>
          </div>
        )}

        {grouped.map((group) => (
          <div key={group.date}>
            {/* Date separator */}
            <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "12px 0" }}>
              <div style={{ flex: 1, height: 1, background: colors.borderStrong }} />
              <span style={{ fontSize: font.size.xs, color: colors.textFaint, fontWeight: font.weight.semibold, whiteSpace: "nowrap", background: colors.bg, padding: "0 8px" }}>
                {group.date}
              </span>
              <div style={{ flex: 1, height: 1, background: colors.borderStrong }} />
            </div>

            {group.msgs.map((msg, i) => {
              const isOwn = msg.sender.id === user?.id;
              const prev = i > 0 ? group.msgs[i - 1] : null;
              const next = i < group.msgs.length - 1 ? group.msgs[i + 1] : null;
              const sameAsPrev = prev?.sender.id === msg.sender.id;
              const sameAsNext = next?.sender.id === msg.sender.id;
              const isOptimistic = msg.id === msg.client_message_id;
              const isRead = msg.read_by_user_ids.length > 1;

              const borderRadius = isOwn
                ? `16px 16px ${sameAsNext ? "4px" : "16px"} 16px`
                : `16px 16px 16px ${sameAsNext ? "4px" : "16px"}`;

              return (
                <div key={msg.id} style={{ display: "flex", justifyContent: isOwn ? "flex-end" : "flex-start", alignItems: "flex-end", gap: "0.5rem", marginBottom: sameAsNext ? "0.2rem" : "0.875rem" }}>

                  {!isOwn && (
                    <div style={{ width: 28, flexShrink: 0 }}>
                      {!sameAsNext && <Avatar name={otherName} size="xs" />}
                    </div>
                  )}

                  <div style={{ maxWidth: "72%" }}>
                    {!isOwn && !sameAsPrev && (
                      <p style={{ fontSize: font.size.xs, color: colors.textSubtle, margin: "0 0 3px 8px", fontWeight: font.weight.semibold }}>
                        {otherName}
                      </p>
                    )}

                    <div style={{
                      background: isOwn ? colors.primary : colors.surface,
                      color: isOwn ? "#fff" : colors.text,
                      padding: "10px 14px",
                      borderRadius,
                      border: isOwn ? "none" : `1px solid ${colors.border}`,
                      boxShadow: "0 1px 2px rgba(15,23,42,0.06)",
                      opacity: isOptimistic ? 0.65 : 1,
                      transition: "opacity 0.2s",
                    }}>
                      <p style={{ margin: 0, fontSize: font.size.base, lineHeight: 1.55, wordBreak: "break-word", whiteSpace: "pre-wrap" }}>
                        {msg.body}
                      </p>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 4, justifyContent: isOwn ? "flex-end" : "flex-start", marginTop: 3, paddingInline: 6 }}>
                      <span style={{ fontSize: 10, color: colors.textFaint }}>{formatTime(msg.created_at)}</span>
                      {isOwn && (
                        <span style={{ fontSize: 11, color: isOptimistic ? colors.textFaint : isRead ? colors.success : colors.textFaint, fontWeight: font.weight.bold }}>
                          {isOptimistic ? "⏳" : isRead ? "✓✓" : "✓"}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ))}

        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ── */}
      <div style={{
        background: colors.surface,
        borderTop: `1px solid ${colors.border}`,
        padding: "14px 20px",
        display: "flex", alignItems: "flex-end", gap: 10,
        flexShrink: 0,
      }}>
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            e.target.style.height = "auto";
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          placeholder="Message… (Enter to send · Shift+Enter for new line)"
          style={{
            flex: 1, border: `1px solid ${colors.borderStrong}`, borderRadius: radius.xl,
            padding: "10px 14px", fontSize: font.size.base, lineHeight: 1.5,
            resize: "none", outline: "none", fontFamily: font.family,
            height: 44, maxHeight: 120, overflowY: "auto",
            transition: "border-color 0.15s",
            background: colors.bg,
            color: colors.text,
          }}
          onFocus={(e) => e.target.style.borderColor = colors.primary}
          onBlur={(e) => e.target.style.borderColor = colors.borderStrong}
          rows={1}
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || sending}
          style={{
            width: 44, height: 44, borderRadius: "50%",
            background: input.trim() && !sending ? colors.primary : colors.borderStrong,
            border: "none", cursor: input.trim() && !sending ? "pointer" : "not-allowed",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0, transition: "background 0.2s",
          }}
          aria-label="Send message"
        >
          {sending ? (
            <Spinner size="sm" color="#fff" />
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style={{ marginLeft: 2 }}>
              <path d="M22 2L11 13" stroke={input.trim() ? "white" : colors.textFaint} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke={input.trim() ? "white" : colors.textFaint} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
