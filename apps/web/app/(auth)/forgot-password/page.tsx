"use client";

import Link from "next/link";
import { useState } from "react";
import { apiClient } from "../../../lib/api";
import { Button, Input, colors, font, radius } from "../../../components/ui";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await apiClient.forgotPassword(email);
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send reset email.");
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <div>
        <h1 style={{ fontSize: font.size["2xl"], fontWeight: font.weight.heavy, margin: "0 0 10px" }}>
          Check your email
        </h1>
        <p style={{ color: colors.textSubtle, fontSize: font.size.base, lineHeight: 1.5 }}>
          If an account exists for <strong>{email}</strong>, we&apos;ve sent a password reset link.
          The link expires in 30 minutes.
        </p>
        <p style={{ color: colors.textSubtle, fontSize: font.size.sm, marginTop: 24 }}>
          Didn&apos;t get it? Check your spam folder, or{" "}
          <button
            type="button"
            onClick={() => setSubmitted(false)}
            style={{ background: "none", border: "none", padding: 0, color: colors.primary, cursor: "pointer", fontWeight: font.weight.medium }}
          >
            try a different email
          </button>
          .
        </p>
        <Link
          href="/login"
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
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <div>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: font.size["3xl"], fontWeight: font.weight.heavy, color: colors.text, margin: "0 0 6px", letterSpacing: "-0.02em" }}>
          Forgot password?
        </h1>
        <p style={{ color: colors.textSubtle, fontSize: font.size.base, margin: 0 }}>
          Enter your email and we&apos;ll send you a link to reset your password.
        </p>
      </header>

      {error && (
        <div
          role="alert"
          style={{ background: colors.dangerSoft, border: "1px solid #fecaca", color: colors.dangerText, borderRadius: radius.lg, padding: "10px 14px", marginBottom: 16, fontSize: font.size.sm }}
        >
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <Input
          label="Email address"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
          required
        />
        <Button type="submit" loading={loading} disabled={!email} fullWidth size="lg">
          Send reset link
        </Button>
      </form>

      <div style={{ textAlign: "center", marginTop: 20, fontSize: font.size.sm }}>
        <Link href="/login" style={{ color: colors.primary, textDecoration: "none", fontWeight: font.weight.medium }}>
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
