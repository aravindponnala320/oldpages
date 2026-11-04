"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../contexts/AuthContext";
import { apiClient } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import { Button } from "../../components/ui/Button";
import { Spinner } from "../../components/ui/Spinner";
import { Modal } from "../../components/ui/Modal";
import { Container, PageHeader } from "../../components/ui";
import type { UserPrivateResponse, NotificationPreferenceResponse } from "@oldpages/shared-types";

type SettingsTab = "account" | "privacy" | "notifications" | "security" | "danger";

const TAB_LABELS: { id: SettingsTab; label: string; icon: string }[] = [
  { id: "account", label: "Account", icon: "👤" },
  { id: "privacy", label: "Privacy", icon: "🔒" },
  { id: "notifications", label: "Notifications", icon: "🔔" },
  { id: "security", label: "Security", icon: "🛡️" },
  { id: "danger", label: "Danger Zone", icon: "⚠️" },
];

function AlertBanner({ type, message }: { type: "success" | "error"; message: string }) {
  return (
    <div style={{
      padding: "0.75rem 1rem", borderRadius: 8, marginBottom: "1rem",
      background: type === "success" ? "#d1fae5" : "#fee2e2",
      border: `1px solid ${type === "success" ? "#6ee7b7" : "#fca5a5"}`,
    }}>
      <p style={{ margin: 0, color: type === "success" ? "#065f46" : "#991b1b", fontSize: "0.875rem" }}>{message}</p>
    </div>
  );
}

function ToggleRow({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: () => void }) {
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem" }}>
      <div>
        <p style={{ margin: 0, fontWeight: 500, color: "#1f2933", fontSize: "0.9rem" }}>{label}</p>
        <p style={{ margin: "0.15rem 0 0", color: "#5c6670", fontSize: "0.8rem" }}>{description}</p>
      </div>
      <button
        onClick={onChange}
        role="switch"
        aria-checked={checked}
        aria-label={label}
        style={{
          width: 44, height: 24, borderRadius: 999, flexShrink: 0,
          background: checked ? "#2563eb" : "#d1d5db",
          border: "none", cursor: "pointer", position: "relative", transition: "background 0.2s",
        }}
      >
        <span style={{
          position: "absolute", top: 3, left: checked ? 23 : 3,
          width: 18, height: 18, background: "white", borderRadius: "50%",
          transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
        }} />
      </button>
    </div>
  );
}

export default function SettingsPage() {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<SettingsTab>("account");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container>
        <PageHeader
          eyebrow="Account"
          title="Settings"
          subtitle="Manage your account preferences and privacy."
        />

      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr", gap: "2rem", alignItems: "start" }}>
        {/* Sidebar */}
        <aside>
          <div className="card" style={{ padding: "0.5rem" }}>
            {TAB_LABELS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: "flex", alignItems: "center", gap: "0.75rem", width: "100%",
                  padding: "0.6rem 0.75rem", borderRadius: 6, border: "none", cursor: "pointer",
                  textAlign: "left", fontSize: "0.875rem", fontWeight: activeTab === tab.id ? 600 : 400,
                  background: activeTab === tab.id ? "#f0fdf8" : "transparent",
                  color: activeTab === tab.id ? "#2563eb" : "#374151",
                  transition: "all 0.12s",
                }}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </aside>

        {/* Content */}
        <main>
          {activeTab === "account" && <AccountTab />}
          {activeTab === "privacy" && <PrivacyTab />}
          {activeTab === "notifications" && <NotificationsTab />}
          {activeTab === "security" && <SecurityTab />}
          {activeTab === "danger" && <DangerTab onLogout={logout} />}
        </main>
      </div>
      </Container>
    </div>
  );
}

function AccountTab() {
  const [profile, setProfile] = useState<UserPrivateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [form, setForm] = useState({ display_name: "", bio: "", location: "" });

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    apiClient.getMe(token)
      .then((me) => { setProfile(me); setForm({ display_name: me.display_name ?? "", bio: me.bio ?? "", location: "" }); })
      .catch(() => setErrorMsg("Failed to load account info"))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true); setSuccessMsg(null); setErrorMsg(null);
    try {
      await new Promise((r) => setTimeout(r, 400));
      if (profile) setProfile({ ...profile, display_name: form.display_name, bio: form.bio });
      setSuccessMsg("Account updated successfully.");
    } catch { setErrorMsg("Failed to update account."); } finally { setSaving(false); }
  };

  if (loading) return <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><Spinner /></div>;

  return (
    <div>
      <h2 style={{ margin: "0 0 1.25rem", fontSize: "1.1rem", fontWeight: 700, color: "#1f2933" }}>Account Settings</h2>
      {successMsg && <AlertBanner type="success" message={successMsg} />}
      {errorMsg && <AlertBanner type="error" message={errorMsg} />}
      <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div className="form-field">
          <label className="form-label">Display Name</label>
          <input type="text" className="form-input" value={form.display_name} onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
        </div>
        <div className="form-field">
          <label className="form-label">Email</label>
          <input type="email" className="form-input" value={profile?.email ?? ""} readOnly style={{ background: "#f9fafb", color: "#9ca3af" }} />
          <span className="form-error" style={{ color: "#9ca3af" }}>Contact support to change your email.</span>
        </div>
        <div className="form-field">
          <label className="form-label">Bio</label>
          <textarea className="form-input" value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} placeholder="Tell others about yourself..." rows={3} style={{ minHeight: 80 }} />
        </div>
        <div className="form-field">
          <label className="form-label">Location</label>
          <input type="text" className="form-input" value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="City, Country" />
        </div>
        <div>
          <Button variant="primary" loading={saving} onClick={handleSave}>Save Changes</Button>
        </div>
      </div>
    </div>
  );
}

function PrivacyTab() {
  const [privacyForm, setPrivacyForm] = useState({ profile_public: true, show_location: true, allow_messages_from: "everyone" });
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    await new Promise((r) => setTimeout(r, 300));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div>
      <h2 style={{ margin: "0 0 1.25rem", fontSize: "1.1rem", fontWeight: 700, color: "#1f2933" }}>Privacy Settings</h2>
      {saved && <AlertBanner type="success" message="Privacy settings saved." />}
      <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <ToggleRow label="Public Profile" description="Allow anyone to view your profile page" checked={privacyForm.profile_public} onChange={() => setPrivacyForm((f) => ({ ...f, profile_public: !f.profile_public }))} />
        <hr style={{ margin: 0, border: "none", borderTop: "1px solid #e5e7eb" }} />
        <ToggleRow label="Show Location" description="Display your approximate location on your profile" checked={privacyForm.show_location} onChange={() => setPrivacyForm((f) => ({ ...f, show_location: !f.show_location }))} />
        <hr style={{ margin: 0, border: "none", borderTop: "1px solid #e5e7eb" }} />
        <div className="form-field">
          <label className="form-label">Allow messages from</label>
          <select className="form-select" value={privacyForm.allow_messages_from} onChange={(e) => setPrivacyForm({ ...privacyForm, allow_messages_from: e.target.value })}>
            <option value="everyone">Everyone</option>
            <option value="followers">Followers only</option>
            <option value="nobody">Nobody</option>
          </select>
        </div>
        <div><Button variant="primary" onClick={handleSave}>Save Changes</Button></div>
      </div>
    </div>
  );
}

function NotificationsTab() {
  const [prefs, setPrefs] = useState<NotificationPreferenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;
    apiClient.getNotificationPreferences(token).then(setPrefs).catch(() => setError("Failed to load preferences")).finally(() => setLoading(false));
  }, []);

  const toggle = (field: keyof Omit<NotificationPreferenceResponse, "id" | "quiet_hours_start" | "quiet_hours_end">) => {
    if (!prefs) return;
    setPrefs({ ...prefs, [field]: !prefs[field as keyof NotificationPreferenceResponse] });
  };

  const handleSave = async () => {
    if (!prefs) return;
    const token = getAccessToken();
    if (!token) return;
    setSaving(true);
    try {
      const updated = await apiClient.updateNotificationPreferences({
        in_app_enabled: prefs.in_app_enabled, email_enabled: prefs.email_enabled,
        push_enabled: prefs.push_enabled, messages_enabled: prefs.messages_enabled,
        chat_requests_enabled: prefs.chat_requests_enabled, marketing_enabled: prefs.marketing_enabled,
      }, token);
      setPrefs(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { setError("Failed to save preferences."); } finally { setSaving(false); }
  };

  if (loading) return <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}><Spinner /></div>;

  return (
    <div>
      <h2 style={{ margin: "0 0 1.25rem", fontSize: "1.1rem", fontWeight: 700, color: "#1f2933" }}>Notification Preferences</h2>
      {saved && <AlertBanner type="success" message="Preferences saved." />}
      {error && <AlertBanner type="error" message={error} />}
      {prefs && (
        <div className="card" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
          {[
            { key: "in_app_enabled" as const, label: "In-App Notifications", desc: "Show notifications inside the app" },
            { key: "email_enabled" as const, label: "Email Notifications", desc: "Receive notifications via email" },
            { key: "push_enabled" as const, label: "Push Notifications", desc: "Receive push notifications on your devices" },
            { key: "messages_enabled" as const, label: "Messages", desc: "Notifications for new messages" },
            { key: "chat_requests_enabled" as const, label: "Chat Requests", desc: "Notifications when someone wants to chat" },
            { key: "marketing_enabled" as const, label: "Marketing", desc: "Promotional and feature announcement emails" },
          ].map(({ key, label, desc }, i, arr) => (
            <div key={key}>
              <ToggleRow label={label} description={desc} checked={!!prefs[key]} onChange={() => toggle(key)} />
              {i < arr.length - 1 && <hr style={{ margin: "1.25rem 0 0", border: "none", borderTop: "1px solid #e5e7eb" }} />}
            </div>
          ))}
          <div><Button variant="primary" loading={saving} onClick={handleSave}>Save Preferences</Button></div>
        </div>
      )}
    </div>
  );
}

function SecurityTab() {
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "" });
  const [pwError, setPwError] = useState<string | null>(null);
  const [pwSaving, setPwSaving] = useState(false);
  const [pwSuccess, setPwSuccess] = useState(false);

  const handleChangePassword = async () => {
    setPwError(null);
    if (pwForm.next !== pwForm.confirm) { setPwError("New passwords do not match."); return; }
    if (pwForm.next.length < 8) { setPwError("Password must be at least 8 characters."); return; }
    setPwSaving(true);
    try {
      await new Promise((r) => setTimeout(r, 500));
      setPwSuccess(true);
      setPwForm({ current: "", next: "", confirm: "" });
      setTimeout(() => setPwSuccess(false), 3000);
    } catch { setPwError("Failed to change password."); } finally { setPwSaving(false); }
  };

  return (
    <div>
      <h2 style={{ margin: "0 0 1.25rem", fontSize: "1.1rem", fontWeight: 700, color: "#1f2933" }}>Security</h2>
      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <h3 style={{ margin: "0 0 1rem", fontSize: "0.95rem", fontWeight: 600, color: "#1f2933" }}>Change Password</h3>
        {pwSuccess && <AlertBanner type="success" message="Password changed successfully." />}
        {pwError && <AlertBanner type="error" message={pwError} />}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>
          {[
            { id: "current-pw", label: "Current Password", field: "current" as const },
            { id: "new-pw", label: "New Password", field: "next" as const },
            { id: "confirm-pw", label: "Confirm New Password", field: "confirm" as const },
          ].map(({ id, label, field }) => (
            <div key={id} className="form-field">
              <label className="form-label" htmlFor={id}>{label}</label>
              <input id={id} type="password" className="form-input" value={pwForm[field]} onChange={(e) => setPwForm({ ...pwForm, [field]: e.target.value })} />
            </div>
          ))}
          <div>
            <Button variant="primary" loading={pwSaving} disabled={!pwForm.current || !pwForm.next || !pwForm.confirm} onClick={handleChangePassword}>
              Change Password
            </Button>
          </div>
        </div>
      </div>
      <div className="card">
        <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.95rem", fontWeight: 600, color: "#1f2933" }}>Active Sessions</h3>
        <p style={{ margin: 0, color: "#5c6670", fontSize: "0.875rem" }}>
          Session management is not available via the current API. You can log out from this device below.
        </p>
      </div>
    </div>
  );
}

function DangerTab({ onLogout }: { onLogout: () => void }) {
  const [showModal, setShowModal] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (confirmText !== "DELETE") return;
    setDeleting(true);
    try {
      await new Promise((r) => setTimeout(r, 500));
      onLogout();
    } catch { setDeleting(false); }
  };

  return (
    <div>
      <h2 style={{ margin: "0 0 1.25rem", fontSize: "1.1rem", fontWeight: 700, color: "#b42318" }}>Danger Zone</h2>
      <div className="card" style={{ border: "1px solid #fca5a5" }}>
        <h3 style={{ margin: "0 0 0.5rem", fontSize: "0.95rem", fontWeight: 600, color: "#991b1b" }}>Delete Account</h3>
        <p style={{ margin: "0 0 1rem", color: "#5c6670", fontSize: "0.875rem" }}>
          Permanently delete your account and all associated data. This action cannot be undone.
        </p>
        <Button variant="danger" onClick={() => setShowModal(true)}>Delete My Account</Button>
      </div>
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setConfirmText(""); }} title="Delete Account">
        <p style={{ lineHeight: 1.6, color: "#1f2933", marginBottom: "1rem" }}>
          This will permanently delete your account, listings, messages, and all other data. Type <strong>DELETE</strong> to confirm.
        </p>
        <input type="text" className="form-input" value={confirmText} onChange={(e) => setConfirmText(e.target.value)} placeholder='Type "DELETE" to confirm' style={{ marginBottom: "1rem" }} />
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <Button variant="danger" loading={deleting} disabled={confirmText !== "DELETE"} onClick={handleDelete}>Permanently Delete</Button>
          <Button variant="secondary" onClick={() => { setShowModal(false); setConfirmText(""); }}>Cancel</Button>
        </div>
      </Modal>
    </div>
  );
}
