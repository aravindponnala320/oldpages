"use client";

import Link from "next/link";
import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "../../../lib/api";
import { Button, Input, colors, font, radius } from "../../../components/ui";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordInner />
    </Suspense>
  );
}

function ResetPasswordInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await apiClient.resetPassword(token, password);
      setDone(true);
      setTimeout(() => router.push("/login"), 1800);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "This reset link is invalid or expired.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <div>
        <h1 style={{ fontSize: font.size["2xl"], fontWeight: font.weight.heavy, margin: "0 0 10px" }}>
          Missing reset token
        </h1>
        <p style={{ color: colors.textSubtle, fontSize: font.size.base }}>
          Open the password reset link from your email.
        </p>
        <Link
          href="/forgot-password"
          style={{
            display: "block", textAlign: "center",
            border: `1px solid ${colors.borderStrong}`,
            borderRadius: radius.lg, padding: "12px",
            fontSize: font.size.base, fontWeight: font.weight.semibold,
            color: colors.text, textDecoration: "none",
            background: colors.surface,
            marginTop: 24,
          }}
        >
          Request a new link
        </Link>
      </div>
    );
  }

  if (done) {
    return (
      <div>
        <h1 style={{ fontSize: font.size["2xl"], fontWeight: font.weight.heavy, margin: "0 0 10px" }}>
          Password updated
        </h1>
        <p style={{ color: colors.textSubtle, fontSize: font.size.base }}>
          Redirecting you to sign in...
        </p>
      </div>
    );
  }

  return (
    <div>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: font.size["3xl"], fontWeight: font.weight.heavy, color: colors.text, margin: "0 0 6px", letterSpacing: "-0.02em" }}>
          Set a new password
        </h1>
        <p style={{ color: colors.textSubtle, fontSize: font.size.base, margin: 0 }}>
          Choose a strong password you haven&apos;t used before.
        </p>
      </header>

      {error && (
        <div role="alert" style={{ background: colors.dangerSoft, border: "1px solid #fecaca", color: colors.dangerText, borderRadius: radius.lg, padding: "10px 14px", marginBottom: 16, fontSize: font.size.sm }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <Input
          label="New password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
          autoComplete="new-password"
          required
          minLength={8}
        />
        <Input
          label="Confirm password"
          type="password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          autoComplete="new-password"
          required
          minLength={8}
        />
        <Button type="submit" loading={loading} disabled={!password || !confirm} fullWidth size="lg">
          Update password
        </Button>
      </form>
    </div>
  );
}
