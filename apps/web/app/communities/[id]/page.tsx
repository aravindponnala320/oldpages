"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../../contexts/AuthContext";
import { apiClient } from "../../../lib/api";
import { getAccessToken } from "../../../lib/auth";
import {
  Avatar,
  Badge,
  Button,
  Container,
  EmptyState,
  Icon,
  LinkButton,
  Section,
  Spinner,
  Tabs,
  Textarea,
  colors,
  font,
  radius,
  shadow,
  useToast,
} from "../../../components/ui";
import type {
  CommunityResponse,
  CommunityPostResponse,
  CommunityMemberResponse,
  EventResponse,
  ListingResponse,
  PostReactionType,
} from "@oldpages/shared-types";

type Tab = "feed" | "members" | "events" | "marketplace";

const REACTIONS: { type: PostReactionType; emoji: string }[] = [
  { type: "like", emoji: "👍" },
  { type: "love", emoji: "❤️" },
  { type: "insightful", emoji: "📚" },
];

function PostCard({
  post,
  onReact,
}: {
  post: CommunityPostResponse;
  onReact: (postId: string, type: PostReactionType) => void;
}) {
  return (
    <div
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.xl,
        padding: 16,
        boxShadow: shadow.sm,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
        <Avatar name={`User ${post.author.id.slice(0, 4)}`} size="sm" />
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ margin: 0, fontWeight: font.weight.semibold, fontSize: font.size.base, color: colors.text }}>
            User {post.author.id.slice(0, 8)}
          </p>
          <p style={{ margin: 0, fontSize: font.size.xs, color: colors.textFaint }}>
            {new Date(post.created_at).toLocaleString()}
          </p>
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          {post.is_pinned && <Badge variant="info" label="Pinned" />}
          {post.is_announcement && <Badge variant="warning" label="Announcement" />}
        </div>
      </div>
      {post.title && (
        <h3 style={{ margin: "0 0 6px", fontSize: font.size.md, fontWeight: font.weight.semibold, color: colors.text }}>
          {post.title}
        </h3>
      )}
      {post.body && (
        <p style={{ margin: "0 0 12px", fontSize: font.size.base, color: colors.textMuted, lineHeight: font.lineHeight.relaxed }}>
          {post.body}
        </p>
      )}
      <div style={{ display: "flex", alignItems: "center", gap: 6, borderTop: `1px solid ${colors.divider}`, paddingTop: 10 }}>
        {REACTIONS.map((r) => {
          const active = post.viewer_reaction === r.type;
          return (
            <button
              key={r.type}
              onClick={() => onReact(post.id, r.type)}
              style={{
                background: active ? colors.primarySoft : "transparent",
                border: `1px solid ${active ? "#c7dbff" : colors.borderStrong}`,
                borderRadius: radius.pill,
                padding: "3px 10px",
                cursor: "pointer",
                fontSize: font.size.sm,
                color: colors.text,
              }}
            >
              {r.emoji} {post.reaction_counts[r.type] ?? 0}
            </button>
          );
        })}
        <span style={{ fontSize: font.size.sm, color: colors.textFaint, marginLeft: "auto" }}>
          {post.comment_count} comment{post.comment_count !== 1 ? "s" : ""}
        </span>
      </div>
    </div>
  );
}

function CreatePostForm({
  communityId,
  onPosted,
}: {
  communityId: string;
  onPosted: (post: CommunityPostResponse) => void;
}) {
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async () => {
    const token = getAccessToken();
    if (!token || !body.trim()) return;
    setLoading(true);
    try {
      const post = await apiClient.createCommunityPost(
        communityId,
        { body: body.trim(), post_type: "text" },
        token,
      );
      onPosted(post);
      setBody("");
      toast("Posted", "success");
    } catch {
      toast("Failed to post", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.xl,
        padding: 16,
        marginBottom: 12,
      }}
    >
      <Textarea
        placeholder="Share something with the community..."
        value={body}
        onChange={(e) => setBody(e.target.value)}
        rows={3}
        containerStyle={{ marginBottom: 10 }}
      />
      <Button variant="primary" size="sm" loading={loading} disabled={!body.trim()} onClick={handleSubmit}>
        Post
      </Button>
    </div>
  );
}

export default function CommunityDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [community, setCommunity] = useState<CommunityResponse | null>(null);
  const [feed, setFeed] = useState<CommunityPostResponse[]>([]);
  const [members, setMembers] = useState<CommunityMemberResponse[]>([]);
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [marketplace, setMarketplace] = useState<ListingResponse[]>([]);
  const [tab, setTab] = useState<Tab>("feed");
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { loadCommunity(); }, [id]);

  useEffect(() => {
    if (!community) return;
    if (tab === "feed") loadFeed();
    if (tab === "members") loadMembers();
    if (tab === "events") loadEvents();
    if (tab === "marketplace") loadMarketplace();
  }, [tab, community]);

  async function loadCommunity() {
    setLoading(true);
    const token = getAccessToken() ?? undefined;
    try {
      const c = await apiClient.getCommunity(id, token);
      setCommunity(c);
    } catch {
      setError("Community not found");
    } finally {
      setLoading(false);
    }
  }

  async function loadFeed() {
    const token = getAccessToken() ?? undefined;
    try {
      const res = await apiClient.getCommunityFeed(id, {}, token);
      setFeed(res.items);
    } catch { /* ignore */ }
  }

  async function loadMembers() { setMembers([]); }

  async function loadEvents() {
    const token = getAccessToken() ?? undefined;
    try {
      const res = await apiClient.listEvents({ community_id: id }, token);
      setEvents(res.items);
    } catch { /* ignore */ }
  }

  async function loadMarketplace() {
    const token = getAccessToken() ?? undefined;
    try {
      const res = await apiClient.getCommunityMarketplace(id, {}, token);
      setMarketplace(res.items);
    } catch { /* ignore */ }
  }

  const handleJoin = async () => {
    if (!isAuthenticated) { router.push("/"); return; }
    const token = getAccessToken();
    if (!token) return;
    setJoining(true);
    try {
      await apiClient.joinCommunity(id, {}, token);
      setCommunity((c) => (c ? { ...c, viewer_membership_status: "active" as const, member_count: c.member_count + 1 } : c));
      toast("Joined community", "success");
    } catch {
      toast("Failed to join community", "error");
    } finally {
      setJoining(false);
    }
  };

  const handleReact = async (postId: string, type: PostReactionType) => {
    if (!isAuthenticated) return;
    const token = getAccessToken();
    if (!token) return;
    try {
      await apiClient.setPostReaction(postId, { reaction_type: type }, token);
      setFeed((prev) =>
        prev.map((p) => {
          if (p.id !== postId) return p;
          const wasSame = p.viewer_reaction === type;
          const counts = { ...p.reaction_counts };
          if (p.viewer_reaction) counts[p.viewer_reaction] = Math.max(0, (counts[p.viewer_reaction] ?? 1) - 1);
          if (!wasSame) counts[type] = (counts[type] ?? 0) + 1;
          return { ...p, viewer_reaction: wasSame ? null : type, reaction_counts: counts };
        }),
      );
    } catch { /* ignore */ }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !community) {
    return (
      <div style={{ padding: "24px 0" }}>
        <Container>
          <div style={{ background: colors.dangerSoft, border: `1px solid #fecaca`, color: colors.dangerText, borderRadius: radius.lg, padding: "14px 18px", marginBottom: 16 }}>
            {error ?? "Community not found"}
          </div>
          <Button variant="ghost" onClick={() => router.back()}>← Back</Button>
        </Container>
      </div>
    );
  }

  const isMember = community.viewer_membership_status === "active";

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={1080}>
        <div
          style={{
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: radius.xl,
            padding: 20,
            marginBottom: 16,
            boxShadow: shadow.sm,
          }}
        >
          <div style={{ display: "flex", alignItems: "flex-start", gap: 16, flexWrap: "wrap" }}>
            <div
              style={{
                width: 72,
                height: 72,
                borderRadius: radius.lg,
                background: `linear-gradient(135deg, ${colors.primarySoft}, ${colors.featPurple})`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 32,
                flexShrink: 0,
              }}
            >
              📚
            </div>
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
                <h1 style={{ margin: 0, fontSize: font.size["2xl"], fontWeight: font.weight.bold, color: colors.text }}>
                  {community.name}
                </h1>
                <Badge label={community.community_type.replace(/_/g, " ")} />
                {isMember && <Badge variant="success" label="Member" />}
              </div>
              {community.description && (
                <p style={{ margin: "0 0 8px", fontSize: font.size.base, color: colors.textSubtle, lineHeight: font.lineHeight.snug }}>
                  {community.description}
                </p>
              )}
              <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                <span style={{ fontSize: font.size.sm, color: colors.textFaint }}>
                  {community.member_count.toLocaleString()} members
                </span>
                {community.city && <span style={{ fontSize: font.size.sm, color: colors.textFaint }}>{community.city}</span>}
              </div>
            </div>
            {!isMember && <Button variant="primary" loading={joining} onClick={handleJoin}>Join Community</Button>}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 16 }}>
          {[
            { label: "Members", value: community.member_count.toLocaleString() },
            { label: "Posts", value: feed.length || "—" },
            { label: "Events", value: events.length || "—" },
          ].map((s) => (
            <div
              key={s.label}
              style={{
                background: colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: radius.lg,
                padding: 16,
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: font.size["2xl"], fontWeight: font.weight.heavy, color: colors.text }}>{s.value}</div>
              <div style={{ fontSize: font.size.sm, color: colors.textSubtle, marginTop: 2 }}>{s.label}</div>
            </div>
          ))}
        </div>

        <div style={{ marginBottom: 16 }}>
          <Tabs
            tabs={[
              { key: "feed", label: "Feed" },
              { key: "members", label: "Members" },
              { key: "events", label: "Events" },
              { key: "marketplace", label: "Marketplace" },
            ]}
            value={tab}
            onChange={(k) => setTab(k as Tab)}
          />
        </div>

        {tab === "feed" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {isMember && <CreatePostForm communityId={id} onPosted={(post) => setFeed((prev) => [post, ...prev])} />}
            {feed.length === 0 ? (
              <EmptyState
                icon={<Icon.chat size={26} color={colors.primary} />}
                title={isMember ? "Be the first to post!" : "No posts yet"}
                description={isMember ? undefined : "Join the community to participate."}
              />
            ) : (
              feed.map((post) => <PostCard key={post.id} post={post} onReact={handleReact} />)
            )}
          </div>
        )}

        {tab === "members" && (
          members.length === 0 ? (
            <EmptyState
              icon={<Icon.user size={26} color={colors.primary} />}
              title="Member list not available"
              description="The members endpoint hasn't been wired up yet."
            />
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {members.map((m, i) => (
                <div
                  key={i}
                  style={{
                    background: colors.surface,
                    border: `1px solid ${colors.border}`,
                    borderRadius: radius.lg,
                    padding: 12,
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                  }}
                >
                  <Avatar name={`User ${m.user.id.slice(0, 4)}`} size="md" />
                  <span style={{ flex: 1, fontWeight: font.weight.medium, fontSize: font.size.base, color: colors.text }}>
                    User {m.user.id.slice(0, 8)}
                  </span>
                  <Badge label={m.role} />
                </div>
              ))}
            </div>
          )
        )}

        {tab === "events" && (
          events.length === 0 ? (
            <EmptyState
              icon={<Icon.book size={26} color={colors.primary} />}
              title="No upcoming events"
              description="Community events will appear here when scheduled."
            />
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 14 }}>
              {events.map((event) => (
                <div
                  key={event.id}
                  style={{
                    background: colors.surface,
                    border: `1px solid ${colors.border}`,
                    borderRadius: radius.lg,
                    padding: 16,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                    <span style={{ fontWeight: font.weight.semibold, fontSize: font.size.md, color: colors.text }}>
                      {event.title}
                    </span>
                    <Badge variant="info" label={event.event_type.replace(/_/g, " ")} />
                  </div>
                  <p style={{ margin: "0 0 4px", fontSize: font.size.sm, color: colors.textSubtle }}>
                    {new Date(event.starts_at).toLocaleString()}
                  </p>
                  {event.location_name && (
                    <p style={{ margin: "0 0 4px", fontSize: font.size.sm, color: colors.textSubtle }}>
                      {event.location_name}
                    </p>
                  )}
                  <p style={{ margin: "0 0 10px", fontSize: font.size.xs, color: colors.textFaint }}>
                    {event.rsvp_count} going
                  </p>
                  <LinkButton href={`/events/${event.id}`} variant="secondary" size="sm">View Event</LinkButton>
                </div>
              ))}
            </div>
          )
        )}

        {tab === "marketplace" && (
          marketplace.length === 0 ? (
            <EmptyState
              icon={<Icon.book size={26} color={colors.primary} />}
              title="No listings yet"
              description="Community-member listings will appear here as they're published."
            />
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 14 }}>
              {marketplace.map((l) => (
                <LinkButton
                  key={l.id}
                  href={`/listings/${l.id}`}
                  variant="secondary"
                  style={{ padding: 14, flexDirection: "column", alignItems: "flex-start", height: "auto", whiteSpace: "normal" }}
                >
                  <h3 style={{ margin: 0, fontSize: font.size.base, fontWeight: font.weight.semibold, color: colors.text, textAlign: "left" }}>
                    {l.title}
                  </h3>
                  <p style={{ margin: "6px 0 0", fontSize: font.size.md, fontWeight: font.weight.bold, color: colors.text }}>
                    {l.price_amount_cents != null ? `₹${(l.price_amount_cents / 100).toLocaleString()}` : "Free"}
                  </p>
                </LinkButton>
              ))}
            </div>
          )
        )}
      </Container>
    </div>
  );
}
