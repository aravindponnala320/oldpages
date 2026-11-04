"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../contexts/AuthContext";
import {
  Avatar,
  Badge,
  Button,
  Container,
  EmptyState,
  Icon,
  Input,
  Modal,
  PageHeader,
  Section,
  Select,
  Spinner,
  Textarea,
  colors,
  font,
  radius,
  shadow,
  useToast,
} from "../../components/ui";
import { getAccessToken } from "../../lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type BusinessStatus = "pending" | "active" | "rejected" | "suspended";

type StaffMember = {
  id: string;
  user_id: string;
  role: "owner" | "manager" | "staff";
  status: string;
  invited_at: string | null;
};

type Location = {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  is_primary: boolean;
};

type BusinessProfile = {
  id: string;
  name: string;
  slug: string;
  type: string;
  description: string | null;
  website: string | null;
  status: BusinessStatus;
  rejected_reason: string | null;
  listing_count: number;
  is_verified: boolean;
  created_at: string;
};

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const res = await fetch(`${API_BASE}/api/v1${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `API error ${res.status}`);
  }
  if (res.status === 204) return null as T;
  return res.json();
}

const ROLE_VARIANT: Record<string, "success" | "info" | "default"> = {
  owner: "success",
  manager: "info",
  staff: "default",
};

const STATUS_BANNER: Record<BusinessStatus, { bg: string; border: string; color: string; title: string; message?: string } | null> = {
  active: null,
  pending: {
    bg: colors.warningSoft,
    border: colors.warning,
    color: colors.warningText,
    title: "Pending approval",
    message: "Your business profile has been submitted and is awaiting moderator review. This usually takes 1–2 business days.",
  },
  rejected: {
    bg: colors.dangerSoft,
    border: colors.danger,
    color: colors.dangerText,
    title: "Application rejected",
    message: "Your application was not approved. Please review your details and resubmit.",
  },
  suspended: {
    bg: colors.dangerSoft,
    border: colors.danger,
    color: colors.dangerText,
    title: "Account suspended",
    message: "Your business profile has been suspended. Contact support for more information.",
  },
};

export default function BusinessPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [profile, setProfile] = useState<BusinessProfile | null | undefined>(undefined);
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createName, setCreateName] = useState("");
  const [createType, setCreateType] = useState("individual");
  const [createDescription, setCreateDescription] = useState("");
  const [createWebsite, setCreateWebsite] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);

  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteUserId, setInviteUserId] = useState("");
  const [inviteRole, setInviteRole] = useState<"manager" | "staff">("staff");
  const [inviteLoading, setInviteLoading] = useState(false);

  const [showLocationModal, setShowLocationModal] = useState(false);
  const [locName, setLocName] = useState("");
  const [locAddress, setLocAddress] = useState("");
  const [locCity, setLocCity] = useState("");
  const [locState, setLocState] = useState("");
  const [locLoading, setLocLoading] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    fetchProfile();
  }, [isAuthenticated]);

  async function fetchProfile() {
    setLoading(true);
    try {
      const data = await apiFetch<BusinessProfile | null>("/business/me");
      setProfile(data);
      if (data?.id) {
        const staffData = await apiFetch<StaffMember[]>(`/business/${data.id}/staff`).catch(() => []);
        setStaff(staffData);
        setLocations([]);
      }
    } catch {
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!createName.trim()) return;
    setCreating(true);
    setCreateError(null);
    try {
      await apiFetch<BusinessProfile>("/business", {
        method: "POST",
        body: JSON.stringify({
          name: createName.trim(),
          type: createType,
          description: createDescription.trim() || undefined,
          website: createWebsite.trim() || undefined,
        }),
      });
      setShowCreateModal(false);
      setCreateName("");
      setCreateDescription("");
      setCreateWebsite("");
      await fetchProfile();
      toast("Profile submitted for approval", "success");
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create profile");
    } finally {
      setCreating(false);
    }
  }

  async function handleInviteStaff() {
    if (!inviteUserId.trim() || !profile) return;
    setInviteLoading(true);
    try {
      await apiFetch(`/business/${profile.id}/staff`, {
        method: "POST",
        body: JSON.stringify({ user_id: inviteUserId.trim(), role: inviteRole }),
      });
      setShowInviteModal(false);
      setInviteUserId("");
      await fetchProfile();
      toast("Invitation sent", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to invite staff", "error");
    } finally {
      setInviteLoading(false);
    }
  }

  async function handleAddLocation() {
    if (!locName.trim() || !profile) return;
    setLocLoading(true);
    try {
      await apiFetch(`/business/${profile.id}/locations`, {
        method: "POST",
        body: JSON.stringify({
          name: locName.trim(),
          address: locAddress.trim(),
          city: locCity.trim(),
          state: locState.trim(),
          is_primary: locations.length === 0,
        }),
      });
      setShowLocationModal(false);
      setLocName(""); setLocAddress(""); setLocCity(""); setLocState("");
      await fetchProfile();
      toast("Location added", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to add location", "error");
    } finally {
      setLocLoading(false);
    }
  }

  if (isLoading || loading || profile === undefined) {
    return (
      <div style={{ display: "flex", justifyContent: "center", paddingTop: 60 }}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  if (!profile) {
    return (
      <div style={{ padding: "24px 0 40px" }}>
        <Container maxWidth={640}>
          <div
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: radius.xl,
              padding: 40,
              textAlign: "center",
              boxShadow: shadow.sm,
            }}
          >
            <div
              style={{
                width: 64, height: 64, borderRadius: "50%",
                background: colors.primarySoft, display: "flex", alignItems: "center", justifyContent: "center",
                margin: "0 auto 16px",
              }}
            >
              <Icon.book size={30} color={colors.primary} />
            </div>
            <h1 style={{ margin: "0 0 8px", fontSize: font.size["2xl"], fontWeight: font.weight.bold, color: colors.text }}>
              Create a Business Profile
            </h1>
            <p style={{ color: colors.textSubtle, fontSize: font.size.base, margin: "0 0 20px", lineHeight: font.lineHeight.relaxed }}>
              Run a bookstore, library, or book business? Create a profile to manage inventory, staff, and locations — pending moderator approval.
            </p>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 24px", textAlign: "left", display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                "Manage multiple locations",
                "Invite staff members",
                "Bulk import inventory via CSV",
                "Business analytics dashboard",
              ].map((f) => (
                <li key={f} style={{ fontSize: font.size.base, display: "flex", alignItems: "center", gap: 8, color: colors.textMuted }}>
                  <Icon.check size={16} color={colors.success} /> {f}
                </li>
              ))}
            </ul>
            <Button variant="primary" onClick={() => setShowCreateModal(true)}>Create Business Profile</Button>
          </div>

          <Modal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            title="Create Business Profile"
            footer={
              <>
                <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                <Button variant="primary" loading={creating} onClick={handleCreate} disabled={!createName.trim()}>
                  Submit for Approval
                </Button>
              </>
            }
          >
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {createError && (
                <div style={{ background: colors.dangerSoft, color: colors.dangerText, padding: 10, borderRadius: radius.md, fontSize: font.size.sm }}>
                  {createError}
                </div>
              )}
              <Input
                label="Business name *"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder="e.g. Campus Book Store"
              />
              <Select
                label="Type"
                value={createType}
                onChange={(e) => setCreateType(e.target.value)}
                options={[
                  { value: "individual",  label: "Individual Seller" },
                  { value: "shop",        label: "Book Shop" },
                  { value: "publisher",   label: "Publisher" },
                  { value: "library",     label: "Library" },
                  { value: "institution", label: "Institution" },
                ]}
              />
              <Textarea
                label="Description"
                rows={3}
                value={createDescription}
                onChange={(e) => setCreateDescription(e.target.value)}
                placeholder="Describe your business..."
              />
              <Input
                label="Website"
                type="url"
                value={createWebsite}
                onChange={(e) => setCreateWebsite(e.target.value)}
                placeholder="https://yourbusiness.com"
              />
            </div>
          </Modal>
        </Container>
      </div>
    );
  }

  const banner = STATUS_BANNER[profile.status];

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={960}>
        {banner && (
          <div
            style={{
              background: banner.bg,
              border: `1px solid ${banner.border}`,
              borderRadius: radius.lg,
              padding: "14px 18px",
              marginBottom: 20,
            }}
          >
            <p style={{ margin: "0 0 4px", fontWeight: font.weight.semibold, color: banner.color, fontSize: font.size.md }}>
              {banner.title}
            </p>
            {banner.message && (
              <p style={{ margin: 0, fontSize: font.size.sm, color: banner.color }}>{banner.message}</p>
            )}
          </div>
        )}

        <PageHeader
          eyebrow="Business"
          title={profile.name}
          subtitle={profile.description ?? undefined}
          actions={
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <Badge
                variant={profile.status === "active" ? "success" : profile.status === "pending" ? "warning" : "danger"}
                label={profile.status}
              />
              {profile.is_verified && <Badge variant="info" label="Verified" />}
            </div>
          }
        />

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
          <StatCard label="Active Listings" value={profile.listing_count} />
          <StatCard label="Staff Members" value={staff.length} />
          <StatCard label="Locations" value={locations.length} />
        </div>

        {profile.status === "active" && (
          <>
            <div style={{ marginBottom: 16 }}>
              <Section
                title="Locations"
                actions={
                  <Button variant="secondary" size="sm" onClick={() => setShowLocationModal(true)}>
                    Add Location
                  </Button>
                }
              >
                {locations.length === 0 ? (
                  <p style={{ color: colors.textSubtle, fontSize: font.size.base, margin: 0 }}>No locations yet.</p>
                ) : (
                  locations.map((loc) => (
                    <div
                      key={loc.id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 12,
                        padding: "10px 0",
                        borderBottom: `1px solid ${colors.divider}`,
                      }}
                    >
                      <Icon.pin color={colors.primary} />
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <span style={{ fontWeight: font.weight.semibold, fontSize: font.size.base, color: colors.text }}>
                            {loc.name}
                          </span>
                          {loc.is_primary && <Badge variant="info" label="Primary" />}
                        </div>
                        <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textFaint }}>
                          {loc.address}, {loc.city}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </Section>
            </div>

            <Section
              title="Staff members"
              actions={
                <Button variant="secondary" size="sm" onClick={() => setShowInviteModal(true)}>
                  Invite Staff
                </Button>
              }
            >
              {staff.length === 0 ? (
                <p style={{ color: colors.textSubtle, fontSize: font.size.base, margin: 0 }}>No staff yet.</p>
              ) : (
                staff.map((member) => (
                  <div
                    key={member.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      padding: "10px 0",
                      borderBottom: `1px solid ${colors.divider}`,
                    }}
                  >
                    <Avatar name={`User ${member.user_id.slice(0, 4)}`} size="md" />
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <span style={{ fontFamily: "monospace", fontSize: font.size.xs, color: colors.textMuted }}>
                          {member.user_id.slice(0, 12)}…
                        </span>
                        <Badge variant={ROLE_VARIANT[member.role]} label={member.role} />
                      </div>
                    </div>
                    {member.invited_at && (
                      <span style={{ fontSize: font.size.xs, color: colors.textFaint }}>
                        Joined {new Date(member.invited_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                ))
              )}
            </Section>
          </>
        )}

        {profile.status !== "active" && profile.status !== "pending" && (
          <EmptyState
            icon={<Icon.book size={26} color={colors.primary} />}
            title="Management unavailable"
            description="You can manage locations and staff once your profile is active."
          />
        )}

        <Modal
          isOpen={showInviteModal}
          onClose={() => setShowInviteModal(false)}
          title="Invite Staff Member"
          footer={
            <>
              <Button variant="secondary" onClick={() => setShowInviteModal(false)}>Cancel</Button>
              <Button variant="primary" loading={inviteLoading} onClick={handleInviteStaff} disabled={!inviteUserId.trim()}>
                Send Invite
              </Button>
            </>
          }
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <Input
              label="User ID"
              placeholder="Paste user's public ID"
              value={inviteUserId}
              onChange={(e) => setInviteUserId(e.target.value)}
            />
            <Select
              label="Role"
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value as typeof inviteRole)}
              options={[
                { value: "staff", label: "Staff" },
                { value: "manager", label: "Manager" },
              ]}
            />
          </div>
        </Modal>

        <Modal
          isOpen={showLocationModal}
          onClose={() => setShowLocationModal(false)}
          title="Add Location"
          footer={
            <>
              <Button variant="secondary" onClick={() => setShowLocationModal(false)}>Cancel</Button>
              <Button variant="primary" loading={locLoading} onClick={handleAddLocation} disabled={!locName.trim() || !locCity.trim()}>
                Add Location
              </Button>
            </>
          }
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <Input label="Location name *" value={locName} onChange={(e) => setLocName(e.target.value)} placeholder="e.g. Main Campus Store" />
            <Input label="Address" value={locAddress} onChange={(e) => setLocAddress(e.target.value)} placeholder="Block A, Ground Floor" />
            <Input label="City *" value={locCity} onChange={(e) => setLocCity(e.target.value)} placeholder="Pune" />
            <Input label="State *" value={locState} onChange={(e) => setLocState(e.target.value)} placeholder="Maharashtra" />
          </div>
        </Modal>
      </Container>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.xl,
        padding: 18,
        textAlign: "center",
        boxShadow: shadow.sm,
      }}
    >
      <p style={{ margin: 0, fontSize: font.size["2xl"], fontWeight: font.weight.heavy, color: colors.text }}>
        {value.toLocaleString()}
      </p>
      <p style={{ margin: "4px 0 0", fontSize: font.size.sm, color: colors.textSubtle }}>{label}</p>
    </div>
  );
}
