"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../contexts/AuthContext";
import { Button, Input, colors, font, radius } from "../../../components/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <header style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: font.size["3xl"], fontWeight: font.weight.heavy, color: colors.text, margin: "0 0 6px", letterSpacing: "-0.02em" }}>
          Welcome back
        </h1>
        <p style={{ color: colors.textSubtle, fontSize: font.size.base, margin: 0 }}>
          Sign in to your OldPages account
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
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <span style={{ fontSize: font.size.sm, fontWeight: font.weight.semibold, color: colors.textMuted }}>Password</span>
            <Link href="/forgot-password" style={{ fontSize: font.size.sm, color: colors.primary, textDecoration: "none", fontWeight: font.weight.medium }}>
              Forgot password?
            </Link>
          </div>
          <Input
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
            required
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
        </div>

        <Button type="submit" loading={loading} disabled={!email || !password} fullWidth size="lg">
          Sign In
        </Button>
      </form>

      <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "24px 0" }}>
        <div style={{ flex: 1, height: 1, background: colors.borderStrong }} />
        <span style={{ color: colors.textFaint, fontSize: font.size.sm, fontWeight: font.weight.medium }}>New to OldPages?</span>
        <div style={{ flex: 1, height: 1, background: colors.borderStrong }} />
      </div>

      <Link
        href="/register"
        style={{
          display: "block", textAlign: "center",
          border: `1px solid ${colors.borderStrong}`,
          borderRadius: radius.lg, padding: "12px",
          fontSize: font.size.base, fontWeight: font.weight.semibold,
          color: colors.text, textDecoration: "none",
          background: colors.surface,
        }}
      >
        Create a free account
      </Link>
    </div>
  );
}
