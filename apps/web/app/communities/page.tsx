"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../contexts/AuthContext";
import { apiClient } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import {
  Badge,
  Button,
  Container,
  EmptyState,
  Icon,
  Input,
  LinkButton,
  PageHeader,
  Spinner,
  Tabs,
  colors,
  font,
  radius,
  shadow,
  useToast,
} from "../../components/ui";
import type { CommunitySummaryResponse, CommunityType } from "@oldpages/shared-types";

type Tab = "discover" | "mine";

const TYPE_COVER: Partial<Record<CommunityType, string>> = {
  college: "🎓",
  university: "🎓",
  school: "🏫",
  area: "📍",
  city: "🏙️",
  apartment: "🏢",
  workplace: "💼",
  language: "💬",
  genre: "🎭",
};

function CommunityCard({
  community,
  onJoin,
  onLeave,
  joining,
}: {
  community: CommunitySummaryResponse;
  onJoin: (id: string) => void;
  onLeave?: (id: string) => void;
  joining: boolean;
}) {
  const isMember = community.viewer_membership_status === "active";
  const icon = TYPE_COVER[community.community_type] ?? "👥";

  return (
    <div
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.xl,
        boxShadow: shadow.sm,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          height: 120,
          background: `linear-gradient(135deg, ${colors.primarySoft}, ${colors.featPurple})`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 44,
        }}
      >
        {icon}
      </div>
      <div style={{ padding: 16, display: "flex", flexDirection: "column", flex: 1 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8, marginBottom: 6 }}>
          <Link href={`/communities/${community.id}`} style={{ textDecoration: "none" }}>
            <h3 style={{ margin: 0, fontSize: font.size.md, fontWeight: font.weight.bold, color: colors.text }}>
              {community.name}
            </h3>
          </Link>
          <Badge label={community.community_type.replace(/_/g, " ")} />
        </div>
        {community.description && (
          <p
            style={{
              margin: "0 0 10px",
              fontSize: font.size.sm,
              color: colors.textSubtle,
              lineHeight: font.lineHeight.snug,
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            } as React.CSSProperties}
          >
            {community.description}
          </p>
        )}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
          <span style={{ fontSize: font.size.xs, color: colors.textFaint }}>
            {community.member_count.toLocaleString()} members
          </span>
          {community.city && <span style={{ fontSize: font.size.xs, color: colors.textFaint }}>· {community.city}</span>}
          {community.genre && <span style={{ fontSize: font.size.xs, color: colors.textFaint }}>· {community.genre}</span>}
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: "auto" }}>
          <LinkButton href={`/communities/${community.id}`} variant="secondary" size="sm">Visit</LinkButton>
          {isMember ? (
            onLeave ? (
              <Button variant="ghost" size="sm" loading={joining} onClick={() => onLeave(community.id)}>Leave</Button>
            ) : (
              <Badge variant="success" label="Member" />
            )
          ) : (
            <Button variant="primary" size="sm" loading={joining} onClick={() => onJoin(community.id)}>Join</Button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CommunitiesPage() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [communities, setCommunities] = useState<CommunitySummaryResponse[]>([]);
  const [mine, setMine] = useState<CommunitySummaryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("discover");
  const [search, setSearch] = useState("");
  const [cityFilter, setCityFilter] = useState("");
  const [joining, setJoining] = useState<string | null>(null);

  useEffect(() => {
    loadCommunities();
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    const token = getAccessToken();
    if (!token) return;
    apiClient
      .listCommunities({}, token)
      .then((res) => setMine(res.items.filter((c) => c.viewer_membership_status === "active")))
      .catch(() => {});
  }, [isAuthenticated]);

  async function loadCommunities() {
    setLoading(true);
    const token = getAccessToken() ?? undefined;
    try {
      const res = await apiClient.listCommunities({ city: cityFilter || null, genre: null }, token);
      setCommunities(res.items);
    } catch {
      toast("Failed to load communities", "error");
    } finally {
      setLoading(false);
    }
  }

  const handleJoin = async (communityId: string) => {
    if (!isAuthenticated) { router.push("/"); return; }
    const token = getAccessToken();
    if (!token) return;
    setJoining(communityId);
    try {
      await apiClient.joinCommunity(communityId, {}, token);
      setCommunities((prev) =>
        prev.map((c) =>
          c.id === communityId
            ? { ...c, viewer_membership_status: "active" as const, member_count: c.member_count + 1 }
            : c,
        ),
      );
      toast("Joined community", "success");
    } catch {
      toast("Failed to join community", "error");
    } finally {
      setJoining(null);
    }
  };

  const filtered = communities.filter(
    (c) =>
      !search ||
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.description?.toLowerCase().includes(search.toLowerCase()),
  );
  const displayed = tab === "discover" ? filtered : mine;

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container>
        <PageHeader
          eyebrow="Community"
          title="Communities"
          subtitle="Connect with readers in your city and join book clubs, swap groups, and more."
        />

        <div style={{ display: "flex", gap: 12, marginBottom: 20, flexWrap: "wrap" }}>
          <Input
            containerStyle={{ flex: 1, minWidth: 220 }}
            placeholder="Search communities..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            prefix={<Icon.search size={16} color={colors.textFaint} />}
          />
          <Input
            containerStyle={{ width: 160 }}
            placeholder="City"
            value={cityFilter}
            onChange={(e) => setCityFilter(e.target.value)}
            onBlur={() => loadCommunities()}
          />
          <Button variant="secondary" onClick={loadCommunities}>Apply</Button>
        </div>

        <div style={{ marginBottom: 20 }}>
          <Tabs
            tabs={[
              { key: "discover", label: "Discover" },
              { key: "mine", label: "My Communities", count: mine.length },
            ]}
            value={tab}
            onChange={(k) => setTab(k as Tab)}
          />
        </div>

        {loading && (
          <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
            <Spinner size="md" />
          </div>
        )}

        {!loading && displayed.length === 0 && (
          <EmptyState
            icon={<Icon.user size={26} color={colors.primary} />}
            title={tab === "mine" ? "No communities joined yet" : "No communities found"}
            description={
              tab === "mine"
                ? "Discover and join communities to get started."
                : "Try adjusting your search or filters."
            }
          />
        )}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16, alignItems: "start" }}>
          {displayed.map((community) => (
            <CommunityCard
              key={community.id}
              community={community}
              onJoin={handleJoin}
              joining={joining === community.id}
            />
          ))}
        </div>
      </Container>
    </div>
  );
}
