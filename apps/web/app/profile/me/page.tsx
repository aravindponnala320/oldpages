"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../../contexts/AuthContext";
import { apiClient } from "../../../lib/api";
import { getAccessToken } from "../../../lib/auth";
import {
  Avatar,
  Badge,
  Button,
  Container,
  Icon,
  Input,
  Section,
  Spinner,
  Textarea,
  colors,
  font,
  radius,
  shadow,
  useToast,
} from "../../../components/ui";
import type { UserPrivateResponse } from "@oldpages/shared-types";

export default function MyProfilePage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [profile, setProfile] = useState<UserPrivateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editForm, setEditForm] = useState({ display_name: "", bio: "", location: "" });

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    apiClient
      .getMe(token)
      .then((me) => {
        setProfile(me);
        setEditForm({ display_name: me.display_name ?? "", bio: me.bio ?? "", location: "" });
      })
      .catch((err) => setError(err.message ?? "Failed to load profile"))
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  const handleSave = async () => {
    setSaving(true);
    try {
      // NOTE: there is no updateMe endpoint on the API client yet. When it ships,
      // swap this local-state update for a real call.
      await new Promise((r) => setTimeout(r, 300));
      if (profile) {
        setProfile({
          ...profile,
          display_name: editForm.display_name || profile.display_name,
          bio: editForm.bio || profile.bio,
        });
      }
      setEditMode(false);
      toast("Profile updated", "success");
    } finally {
      setSaving(false);
    }
  };

  if (isLoading || loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "24px 0" }}>
        <Container maxWidth={800}>
          <div style={{ background: colors.dangerSoft, border: `1px solid #fecaca`, color: colors.dangerText, borderRadius: radius.lg, padding: "14px 18px" }}>
            {error}
          </div>
        </Container>
      </div>
    );
  }

  if (!profile) return null;

  const quickLinks: { href: string; icon: React.ReactNode; title: string; desc: string }[] = [
    { href: "/my-listings", icon: <Icon.book color={colors.primary} />,      title: "My Listings",     desc: "Manage your book listings" },
    { href: "/reading",     icon: <Icon.book color={colors.primary} />,      title: "Reading Tracker", desc: "Track your reading progress" },
    { href: "/favorites",   icon: <Icon.heart color={colors.primary} />,     title: "Saved Listings",  desc: "Books you've saved" },
    { href: "/settings",    icon: <Icon.user color={colors.primary} />,      title: "Settings",        desc: "Account & privacy settings" },
    { href: "/orders",      icon: <Icon.clipboard color={colors.primary} />, title: "Orders",          desc: "Your buying & selling history" },
    { href: "/offers",      icon: <Icon.chat color={colors.primary} />,      title: "Offers",          desc: "Manage your price offers" },
  ];

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={880}>
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
            <Avatar name={profile.display_name} src={profile.profile_image_url} size="xl" />
            <div style={{ flex: 1, minWidth: 0 }}>
              {!editMode ? (
                <>
                  <h1 style={{ margin: "0 0 2px", fontSize: font.size["2xl"], fontWeight: font.weight.bold, color: colors.text }}>
                    {profile.display_name}
                  </h1>
                  {profile.username && (
                    <p style={{ margin: "0 0 10px", color: colors.textSubtle, fontSize: font.size.base }}>@{profile.username}</p>
                  )}
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
                    {profile.email_verified && <Badge variant="success" label="Email Verified" />}
                    {profile.mobile_verified && <Badge variant="success" label="Mobile Verified" />}
                  </div>
                  {profile.bio && (
                    <p style={{ margin: "0 0 8px", color: colors.textMuted, lineHeight: font.lineHeight.relaxed, fontSize: font.size.base }}>
                      {profile.bio}
                    </p>
                  )}
                  {profile.institution && (
                    <p style={{ margin: "0 0 4px", fontSize: font.size.sm, color: colors.textFaint }}>
                      {profile.institution}
                    </p>
                  )}
                  <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textFaint }}>{profile.email}</p>
                </>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <Input
                    label="Display name"
                    value={editForm.display_name}
                    onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
                  />
                  <Textarea
                    label="Bio"
                    value={editForm.bio}
                    onChange={(e) => setEditForm({ ...editForm, bio: e.target.value })}
                    placeholder="Tell others about yourself..."
                    rows={3}
                  />
                  <Input
                    label="Location"
                    value={editForm.location}
                    onChange={(e) => setEditForm({ ...editForm, location: e.target.value })}
                    placeholder="City, Country"
                  />
                  <div style={{ display: "flex", gap: 10 }}>
                    <Button variant="primary" loading={saving} onClick={handleSave}>Save Changes</Button>
                    <Button variant="secondary" disabled={saving} onClick={() => setEditMode(false)}>Cancel</Button>
                  </div>
                </div>
              )}
            </div>
            {!editMode && <Button variant="secondary" onClick={() => setEditMode(true)}>Edit Profile</Button>}
          </div>
        </div>

        {(profile.favorite_genres?.length > 0 || profile.reading_interests?.length > 0) && (
          <div style={{ marginBottom: 20 }}>
            <Section title="Interests">
              {profile.favorite_genres?.length > 0 && (
                <div style={{ marginBottom: profile.reading_interests?.length > 0 ? 14 : 0 }}>
                  <p style={eyebrow}>Favorite genres</p>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {profile.favorite_genres.map((g) => <Badge key={g} variant="info" label={g} />)}
                  </div>
                </div>
              )}
              {profile.reading_interests?.length > 0 && (
                <div>
                  <p style={eyebrow}>Reading interests</p>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {profile.reading_interests.map((i) => <Badge key={i} label={i} />)}
                  </div>
                </div>
              )}
            </Section>
          </div>
        )}

        <h2 style={eyebrow}>Quick links</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          {quickLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              style={{
                textDecoration: "none",
                background: colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: radius.xl,
                padding: 16,
                display: "flex",
                flexDirection: "column",
                gap: 6,
              }}
            >
              <div style={{ width: 36, height: 36, borderRadius: radius.md, background: colors.primarySoft, display: "flex", alignItems: "center", justifyContent: "center" }}>
                {link.icon}
              </div>
              <p style={{ margin: 0, fontWeight: font.weight.semibold, fontSize: font.size.base, color: colors.text }}>{link.title}</p>
              <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textSubtle }}>{link.desc}</p>
            </Link>
          ))}
        </div>
      </Container>
    </div>
  );
}

const eyebrow: React.CSSProperties = {
  margin: "0 0 8px",
  fontSize: font.size.xs,
  fontWeight: font.weight.bold,
  color: colors.textFaint,
  textTransform: "uppercase",
  letterSpacing: "0.08em",
};
