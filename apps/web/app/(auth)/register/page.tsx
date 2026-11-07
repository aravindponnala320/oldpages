"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../contexts/AuthContext";
import { Button, Input, colors, font, radius } from "../../../components/ui";
import { GoogleSignInButton } from "../../../components/GoogleSignInButton";

export default function RegisterPage() {
  const { register: registerUser } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ display_name: "", email: "", password: "", confirm_password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  function set(key: string, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
    setFieldErrors((e) =>
      key === "password"
        ? { ...e, password: "", confirm_password: "" }
        : { ...e, [key]: "" },
    );
  }

  function validate() {
    const errs: Record<string, string> = {};
    if (!form.display_name.trim() || form.display_name.trim().length < 2)
      errs.display_name = "At least 2 characters required";
    if (!form.email || !/\S+@\S+\.\S+/.test(form.email))
      errs.email = "Enter a valid email address";
    if (!form.password || form.password.length < 12)
      errs.password = "At least 12 characters required";
    if (form.password !== form.confirm_password)
      errs.confirm_password = "Passwords do not match";
    return errs;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) { setFieldErrors(errs); return; }
    setLoading(true);
    setError(null);
    try {
      await registerUser(form.display_name.trim(), form.email, form.password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = form.display_name && form.email && form.password && form.confirm_password && !loading;

  return (
    <div>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: font.size["3xl"], fontWeight: font.weight.heavy, color: colors.text, margin: "0 0 6px", letterSpacing: "-0.02em" }}>
          Create your account
        </h1>
        <p style={{ color: colors.textSubtle, fontSize: font.size.base, margin: 0 }}>
          Join thousands of readers on OldPages — free forever.
        </p>
      </header>

      {error && (
        <div
          role="alert"
          style={{
            background: colors.dangerSoft,
            border: `1px solid #fecaca`,
            color: colors.dangerText,
            borderRadius: radius.lg,
            padding: "10px 14px",
            marginBottom: 16,
            fontSize: font.size.sm,
          }}
        >
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <Input
          label="Full name"
          value={form.display_name}
          onChange={(e) => set("display_name", e.target.value)}
          placeholder="Arjun Sharma"
          autoComplete="name"
          error={fieldErrors.display_name}
        />
        <Input
          label="Email address"
          type="email"
          value={form.email}
          onChange={(e) => set("email", e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
          error={fieldErrors.email}
        />
        <div>
          <Input
            label="Password"
            type={showPassword ? "text" : "password"}
            value={form.password}
            onChange={(e) => set("password", e.target.value)}
            placeholder="Min. 12 characters"
            autoComplete="new-password"
            error={fieldErrors.password}
            suffix={
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                style={{ background: "none", border: "none", cursor: "pointer", color: colors.textSubtle, fontSize: font.size.sm, fontWeight: font.weight.medium }}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            }
          />
          {form.password && <PasswordStrength password={form.password} />}
        </div>
        <Input
          label="Confirm password"
          type="password"
          value={form.confirm_password}
          onChange={(e) => set("confirm_password", e.target.value)}
          placeholder="Re-enter your password"
          autoComplete="new-password"
          error={fieldErrors.confirm_password}
        />

        <Button type="submit" loading={loading} disabled={!canSubmit} fullWidth size="lg">
          Create Free Account
        </Button>
      </form>

      <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "20px 0" }}>
        <div style={{ flex: 1, height: 1, background: colors.borderStrong }} />
        <span style={{ color: colors.textFaint, fontSize: font.size.sm, fontWeight: font.weight.medium }}>or</span>
        <div style={{ flex: 1, height: 1, background: colors.borderStrong }} />
      </div>

      <GoogleSignInButton redirectTo="/dashboard" />

      <p style={{ fontSize: font.size.xs, color: colors.textFaint, textAlign: "center", margin: "16px 0 20px", lineHeight: 1.6 }}>
        By creating an account you agree to our{" "}
        <Link href="/terms" style={{ color: colors.primary, textDecoration: "none" }}>Terms of Service</Link>
        {" "}and{" "}
        <Link href="/privacy" style={{ color: colors.primary, textDecoration: "none" }}>Privacy Policy</Link>.
      </p>

      <div style={{ textAlign: "center", paddingTop: 12, borderTop: `1px solid ${colors.border}` }}>
        <span style={{ fontSize: font.size.base, color: colors.textSubtle }}>Already have an account? </span>
        <Link href="/login" style={{ fontSize: font.size.base, color: colors.primary, fontWeight: font.weight.semibold, textDecoration: "none" }}>
          Sign in
        </Link>
      </div>
    </div>
  );
}

function PasswordStrength({ password }: { password: string }) {
  const checks = [
    password.length >= 12,
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[^A-Za-z0-9]/.test(password),
  ];
  const score = checks.filter(Boolean).length;
  const bars = ["#ef4444", "#f97316", "#eab308", "#22c55e"];
  const labels = ["Weak", "Fair", "Good", "Strong"];
  const color = bars[score - 1] ?? colors.borderStrong;
  const label = labels[score - 1] ?? "";

  return (
    <div>
      <div style={{ display: "flex", gap: 3, marginTop: 8 }}>
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: 3,
              borderRadius: 2,
              background: i < score ? color : colors.borderStrong,
              transition: "background 0.2s",
            }}
          />
        ))}
      </div>
      {label && (
        <p style={{ fontSize: font.size.xs, color, margin: "4px 0 0", fontWeight: font.weight.semibold }}>{label}</p>
      )}
    </div>
  );
}
