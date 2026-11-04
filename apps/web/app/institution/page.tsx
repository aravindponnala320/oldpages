"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../contexts/AuthContext";
import {
  Avatar,
  Badge,
  Button,
  Container,
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

type InstitutionStatus = "pending" | "active" | "rejected" | "suspended";
type MemberRole = "admin" | "staff" | "student" | "alumni" | "member";

type Institution = {
  id: string;
  name: string;
  slug: string;
  type: string;
  status: InstitutionStatus;
  rejected_reason: string | null;
  description: string | null;
  website: string | null;
  city: string | null;
  state: string | null;
  country: string;
  is_verified: boolean;
  member_count: number;
  owner_user_id: string | null;
  created_at: string;
};

type Member = {
  id: string;
  user_id: string;
  role: MemberRole;
  status: string;
  joined_at: string | null;
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

const INSTITUTION_TYPES = [
  { value: "school",     label: "School" },
  { value: "college",    label: "College" },
  { value: "university", label: "University" },
  { value: "library",    label: "Library" },
  { value: "ngo",        label: "NGO" },
  { value: "coaching",   label: "Coaching Center" },
  { value: "publisher",  label: "Publisher" },
  { value: "bookstore",  label: "Bookstore" },
  { value: "other",      label: "Other" },
];

const ROLE_VARIANT: Record<MemberRole, "success" | "info" | "warning" | "default"> = {
  admin: "success",
  staff: "info",
  student: "default",
  alumni: "warning",
  member: "default",
};

const STATUS_BANNER: Record<InstitutionStatus, { bg: string; border: string; color: string; title: string; message?: string } | null> = {
  active: null,
  pending: {
    bg: colors.warningSoft, border: colors.warning, color: colors.warningText,
    title: "Pending approval",
    message: "Your institution has been submitted and is awaiting moderator review. This usually takes 1–2 business days.",
  },
  rejected: {
    bg: colors.dangerSoft, border: colors.danger, color: colors.dangerText,
    title: "Application rejected",
    message: "Your application was not approved. Please review your details and resubmit.",
  },
  suspended: {
    bg: colors.dangerSoft, border: colors.danger, color: colors.dangerText,
    title: "Account suspended",
    message: "Your institution has been suspended. Contact support for more information.",
  },
};

export default function InstitutionPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [institution, setInstitution] = useState<Institution | null | undefined>(undefined);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [form, setForm] = useState({
    name: "", type: "college", description: "", website: "", city: "", state: "",
  });

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    fetchInstitution();
  }, [isAuthenticated]);

  async function fetchInstitution() {
    setLoading(true);
    try {
      const storedId = sessionStorage.getItem("my_institution_id");
      if (storedId) {
        const data = await apiFetch<Institution>(`/institutions/${storedId}`);
        setInstitution(data);
        if (data?.id) {
          const memberData = await apiFetch<Member[]>(`/institutions/${data.id}/members`).catch(() => []);
          setMembers(memberData);
        }
      } else {
        setInstitution(null);
      }
    } catch {
      setInstitution(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!form.name.trim()) return;
    setCreating(true);
    setCreateError(null);
    try {
      const data = await apiFetch<Institution>("/institutions", {
        method: "POST",
        body: JSON.stringify({
          name: form.name.trim(),
          type: form.type,
          description: form.description.trim() || undefined,
          website: form.website.trim() || undefined,
          city: form.city.trim() || undefined,
          state: form.state.trim() || undefined,
        }),
      });
      sessionStorage.setItem("my_institution_id", data.id);
      setInstitution(data);
      setShowCreateModal(false);
      setForm({ name: "", type: "college", description: "", website: "", city: "", state: "" });
      toast("Institution submitted for approval", "success");
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Failed to create institution");
    } finally {
      setCreating(false);
    }
  }

  if (isLoading || loading || institution === undefined) {
    return (
      <div style={{ display: "flex", justifyContent: "center", paddingTop: 60 }}>
        <Spinner size="lg" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  if (!institution) {
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
              Register your institution
            </h1>
            <p style={{ color: colors.textSubtle, fontSize: font.size.base, margin: "0 0 20px", lineHeight: font.lineHeight.relaxed }}>
              Are you a school, college, university, or library? Register to connect with your students and staff on OldPages.
            </p>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 20px", textAlign: "left", display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                "Verify your institution's email domain",
                "Invite students and staff",
                "Create a book exchange community",
                "Track reading programs",
              ].map((f) => (
                <li key={f} style={{ fontSize: font.size.base, display: "flex", alignItems: "center", gap: 8, color: colors.textMuted }}>
                  <Icon.check size={16} color={colors.success} /> {f}
                </li>
              ))}
            </ul>
            <p style={{ fontSize: font.size.xs, color: colors.textFaint, margin: "0 0 20px" }}>
              Registration requires moderator approval (1–2 business days).
            </p>
            <Button variant="primary" onClick={() => setShowCreateModal(true)}>Register Institution</Button>
          </div>

          <Modal
            isOpen={showCreateModal}
            onClose={() => setShowCreateModal(false)}
            title="Register Institution"
            footer={
              <>
                <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                <Button variant="primary" loading={creating} onClick={handleCreate} disabled={!form.name.trim()}>
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
                label="Institution name *"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="e.g. Savitribai Phule Pune University"
              />
              <Select
                label="Type *"
                value={form.type}
                onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}
                options={INSTITUTION_TYPES}
              />
              <Textarea
                label="Description"
                rows={3}
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="Brief description of your institution..."
              />
              <Input
                label="Website"
                type="url"
                value={form.website}
                onChange={(e) => setForm((f) => ({ ...f, website: e.target.value }))}
                placeholder="https://institution.edu"
              />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <Input
                  label="City"
                  value={form.city}
                  onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))}
                  placeholder="Pune"
                />
                <Input
                  label="State"
                  value={form.state}
                  onChange={(e) => setForm((f) => ({ ...f, state: e.target.value }))}
                  placeholder="Maharashtra"
                />
              </div>
            </div>
          </Modal>
        </Container>
      </div>
    );
  }

  const banner = STATUS_BANNER[institution.status];

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
            <p style={{ margin: "0 0 4px", fontWeight: font.weight.semibold, color: banner.color }}>
              {banner.title}
            </p>
            {banner.message && (
              <p style={{ margin: 0, fontSize: font.size.sm, color: banner.color }}>
                {institution.status === "rejected" && institution.rejected_reason
                  ? institution.rejected_reason
                  : banner.message}
              </p>
            )}
          </div>
        )}

        <PageHeader
          eyebrow="Institution"
          title={institution.name}
          subtitle={`${institution.type} · ${[institution.city, institution.state].filter(Boolean).join(", ") || "India"}`}
          actions={
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <Badge
                variant={institution.status === "active" ? "success" : institution.status === "pending" ? "warning" : "danger"}
                label={institution.status}
              />
              {institution.is_verified && <Badge variant="info" label="Verified" />}
            </div>
          }
        />

        {institution.description && (
          <p style={{ margin: "-8px 0 20px", color: colors.textMuted, fontSize: font.size.base, lineHeight: font.lineHeight.relaxed }}>
            {institution.description}
          </p>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, marginBottom: 20 }}>
          <StatCard label="Members" value={institution.member_count.toString()} />
          <StatCard label="Type" value={institution.type} />
          <StatCard label="Registered" value={new Date(institution.created_at).toLocaleDateString()} />
        </div>

        {institution.status === "active" && (
          <Section title="Members">
            {members.length === 0 ? (
              <p style={{ color: colors.textSubtle, fontSize: font.size.base, margin: 0 }}>
                No members yet. Share your institution page to invite members.
              </p>
            ) : (
              members.map((m) => (
                <div
                  key={m.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "10px 0",
                    borderBottom: `1px solid ${colors.divider}`,
                  }}
                >
                  <Avatar name={`User ${m.user_id.slice(0, 4)}`} size="md" />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ fontFamily: "monospace", fontSize: font.size.xs, color: colors.textMuted }}>
                        {m.user_id.slice(0, 12)}…
                      </span>
                      <Badge variant={ROLE_VARIANT[m.role]} label={m.role} />
                    </div>
                    {m.joined_at && (
                      <p style={{ margin: 0, fontSize: font.size.xs, color: colors.textFaint }}>
                        Joined {new Date(m.joined_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
              ))
            )}
          </Section>
        )}
      </Container>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
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
      <p style={{ margin: 0, fontSize: font.size.xl, fontWeight: font.weight.heavy, color: colors.text }}>{value}</p>
      <p style={{ margin: "4px 0 0", fontSize: font.size.sm, color: colors.textSubtle }}>{label}</p>
    </div>
  );
}
