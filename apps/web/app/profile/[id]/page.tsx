"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiClient } from "../../../lib/api";
import { getAccessToken } from "../../../lib/auth";
import { useAuth } from "../../../contexts/AuthContext";
import {
  Avatar,
  Badge,
  BookCard,
  Button,
  Container,
  EmptyState,
  Icon,
  LinkButton,
  Spinner,
  Tabs,
  colors,
  font,
  formatPrice,
  radius,
  shadow,
  type BookCardData,
} from "../../../components/ui";
import type { ListingSearchResult } from "@oldpages/shared-types";

type PublicUser = {
  id: string;
  display_name: string;
  bio?: string | null;
  username?: string | null;
  profile_image_url?: string | null;
  verification_badges?: string[];
  approximate_location?: string | null;
  institution?: string | null;
};

type Tab = "listings" | "reviews";

function toBookCard(l: ListingSearchResult): BookCardData {
  return {
    id: l.id,
    href: `/listings/${l.id}`,
    title: l.title,
    author: l.book?.authors?.[0] ?? null,
    imageUrl: l.image_url ?? null,
    priceLabel: formatPrice(l.price_amount_cents, l.currency),
    condition: l.condition ?? null,
    location: l.location?.city ?? null,
  };
}

export default function PublicProfilePage() {
  const params = useParams<{ id: string }>();
  const userId = params.id;
  const { user: currentUser, isAuthenticated } = useAuth();

  const [profileUser, setProfileUser] = useState<PublicUser | null>(null);
  const [listings, setListings] = useState<ListingSearchResult[]>([]);
  const [activeTab, setActiveTab] = useState<Tab>("listings");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [following, setFollowing] = useState(false);
  const [followId, setFollowId] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (!userId) return;
    setLoading(true);
    const token = getAccessToken() ?? undefined;
    Promise.all([
      apiClient.getMe(token ?? "").catch(() => null),
      apiClient.searchListings({ limit: 12 }, token).catch(() => ({ items: [], result_count: 0, next_cursor: null })),
    ])
      .then(([meRes, listingsRes]) => {
        if (meRes && meRes.id === userId) {
          setProfileUser({
            id: meRes.id,
            display_name: meRes.display_name,
            bio: meRes.bio,
            username: meRes.username,
            profile_image_url: meRes.profile_image_url,
            institution: meRes.institution,
          });
        } else {
          setProfileUser({ id: userId, display_name: `User ${userId.slice(0, 8)}` });
        }
        setListings(listingsRes.items);
      })
      .catch((err) => setError(err.message ?? "Failed to load profile"))
      .finally(() => setLoading(false));
  }, [userId]);

  const handleFollow = async () => {
    const token = getAccessToken();
    if (!token) return;
    setActionLoading(true);
    try {
      if (following && followId) {
        await apiClient.deleteFollow(followId, token);
        setFollowing(false);
        setFollowId(null);
      } else {
        const res = await apiClient.createFollow({ target_id: userId, target_type: "user" }, token);
        setFollowing(true);
        setFollowId(res.id);
      }
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !profileUser) {
    return (
      <div style={{ padding: "24px 0" }}>
        <Container>
          <div style={{ background: colors.dangerSoft, border: `1px solid #fecaca`, color: colors.dangerText, borderRadius: radius.lg, padding: "14px 18px" }}>
            {error ?? "Profile not found"}
          </div>
        </Container>
      </div>
    );
  }

  const isOwnProfile = currentUser?.id === userId;

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={1080}>
        <div
          style={{
            background: colors.surface,
            border: `1px solid ${colors.border}`,
            borderRadius: radius.xl,
            padding: 24,
            marginBottom: 20,
            boxShadow: shadow.sm,
          }}
        >
          <div style={{ display: "flex", alignItems: "flex-start", gap: 20, flexWrap: "wrap" }}>
            <Avatar name={profileUser.display_name} src={profileUser.profile_image_url} size="xl" />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
                <h1 style={{ margin: 0, fontSize: font.size["2xl"], fontWeight: font.weight.bold, color: colors.text }}>
                  {profileUser.display_name}
                </h1>
                {profileUser.username && (
                  <span style={{ color: colors.textFaint, fontSize: font.size.base }}>@{profileUser.username}</span>
                )}
                {profileUser.verification_badges?.map((b) => (
                  <Badge key={b} variant="success" label={b} />
                ))}
              </div>
              {profileUser.bio && (
                <p style={{ margin: "8px 0 10px", color: colors.textMuted, lineHeight: font.lineHeight.relaxed, fontSize: font.size.base }}>
                  {profileUser.bio}
                </p>
              )}
              <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
                {profileUser.approximate_location && (
                  <span style={{ fontSize: font.size.sm, color: colors.textFaint, display: "flex", alignItems: "center", gap: 4 }}>
                    <Icon.pin color={colors.textFaint} /> {profileUser.approximate_location}
                  </span>
                )}
                {profileUser.institution && (
                  <span style={{ fontSize: font.size.sm, color: colors.textFaint }}>{profileUser.institution}</span>
                )}
              </div>
            </div>

            <div style={{ display: "flex", gap: 24, flexShrink: 0 }}>
              <div style={{ textAlign: "center" }}>
                <p style={{ margin: 0, fontSize: font.size.xl, fontWeight: font.weight.bold, color: colors.text }}>{listings.length}</p>
                <p style={{ margin: 0, fontSize: font.size.xs, color: colors.textFaint }}>Listings</p>
              </div>
              <div style={{ textAlign: "center" }}>
                <p style={{ margin: 0, fontSize: font.size.xl, fontWeight: font.weight.bold, color: colors.text }}>0</p>
                <p style={{ margin: 0, fontSize: font.size.xs, color: colors.textFaint }}>Trades</p>
              </div>
            </div>

            <div style={{ display: "flex", gap: 8, flexShrink: 0, flexWrap: "wrap" }}>
              {isOwnProfile ? (
                <LinkButton href="/profile/me" variant="secondary" size="sm">Edit Profile</LinkButton>
              ) : (
                <>
                  {isAuthenticated && (
                    <Button
                      variant={following ? "secondary" : "primary"}
                      size="sm"
                      loading={actionLoading}
                      onClick={handleFollow}
                    >
                      {following ? "Unfollow" : "Follow"}
                    </Button>
                  )}
                  {isAuthenticated && (
                    <LinkButton href={`/inbox?user=${userId}`} variant="secondary" size="sm">Message</LinkButton>
                  )}
                </>
              )}
            </div>
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <Tabs
            tabs={[
              { key: "listings", label: "Listings", count: listings.length },
              { key: "reviews", label: "Reviews" },
            ]}
            value={activeTab}
            onChange={(k) => setActiveTab(k as Tab)}
          />
        </div>

        {activeTab === "listings" && (
          listings.length === 0 ? (
            <EmptyState
              icon={<Icon.book size={26} color={colors.primary} />}
              title="No active listings"
              description="This user hasn't listed any books yet."
            />
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16 }}>
              {listings.map((l) => <BookCard key={l.id} book={toBookCard(l)} />)}
            </div>
          )
        )}

        {activeTab === "reviews" && (
          <EmptyState
            icon={<Icon.check size={26} color={colors.primary} />}
            title="No reviews yet"
            description="Reviews will appear here once this user has completed transactions."
          />
        )}
      </Container>
    </div>
  );
}
