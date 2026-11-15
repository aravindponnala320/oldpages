"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../contexts/AuthContext";
import { Button, Input, colors, font, radius } from "../../../components/ui";
import { GoogleSignInButton } from "../../../components/GoogleSignInButton";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [justReset, setJustReset] = useState(false);

  useEffect(() => {
    // Set by the reset-password page; read here so the page needs no Suspense boundary.
    setJustReset(
      new URLSearchParams(window.location.search).get("reset") === "1",
    );
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Invalid email or password.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <header style={{ marginBottom: 28 }}>
        <h1
          style={{
            fontSize: font.size["3xl"],
            fontWeight: font.weight.heavy,
            color: colors.text,
            margin: "0 0 6px",
            letterSpacing: "-0.02em",
          }}
        >
          Welcome back
        </h1>
        <p
          style={{
            color: colors.textSubtle,
            fontSize: font.size.base,
            margin: 0,
          }}
        >
          Sign in to your OldPages account
        </p>
      </header>

      {justReset && !error && (
        <div
          role="status"
          style={{
            background: "#dcfce7",
            border: "1px solid #bbf7d0",
            color: "#166534",
            borderRadius: radius.lg,
            padding: "10px 14px",
            marginBottom: 16,
            fontSize: font.size.sm,
          }}
        >
          Your password was updated. Sign in with your new password.
        </div>
      )}

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
          <div style={{ marginTop: 6, color: colors.textMuted }}>
            Signed up with Google? Use <strong>Continue with Google</strong>{" "}
            below, or{" "}
            <Link
              href="/forgot-password"
              style={{ color: colors.primary, fontWeight: font.weight.medium }}
            >
              reset your password
            </Link>{" "}
            to add one.
          </div>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        noValidate
        style={{ display: "flex", flexDirection: "column", gap: 16 }}
      >
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
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 6,
            }}
          >
            <span
              style={{
                fontSize: font.size.sm,
                fontWeight: font.weight.semibold,
                color: colors.textMuted,
              }}
            >
              Password
            </span>
            <Link
              className="op-tap"
              href="/forgot-password"
              style={{
                fontSize: font.size.sm,
                color: colors.primary,
                textDecoration: "none",
                fontWeight: font.weight.medium,
              }}
            >
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
                className="op-tap"
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: colors.textSubtle,
                  fontSize: font.size.sm,
                  fontWeight: font.weight.medium,
                }}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            }
          />
        </div>

        <Button
          type="submit"
          loading={loading}
          disabled={!email || !password}
          fullWidth
          size="lg"
        >
          Sign In
        </Button>
      </form>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          margin: "24px 0",
        }}
      >
        <div style={{ flex: 1, height: 1, background: colors.borderStrong }} />
        <span
          style={{
            color: colors.textFaint,
            fontSize: font.size.sm,
            fontWeight: font.weight.medium,
          }}
        >
          or
        </span>
        <div style={{ flex: 1, height: 1, background: colors.borderStrong }} />
      </div>

      <GoogleSignInButton redirectTo="/dashboard" />

      <p
        style={{
          fontSize: font.size.xs,
          color: colors.textFaint,
          textAlign: "center",
          margin: "12px 0 0",
          lineHeight: 1.6,
        }}
      >
        By continuing with Google you agree to our{" "}
        <Link
          href="/terms"
          style={{ color: colors.primary, textDecoration: "none" }}
        >
          Terms of Service
        </Link>{" "}
        and{" "}
        <Link
          href="/privacy"
          style={{ color: colors.primary, textDecoration: "none" }}
        >
          Privacy Policy
        </Link>
        .
      </p>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          margin: "24px 0",
        }}
      >
        <div style={{ flex: 1, height: 1, background: colors.borderStrong }} />
        <span
          style={{
            color: colors.textFaint,
            fontSize: font.size.sm,
            fontWeight: font.weight.medium,
          }}
        >
          New to OldPages?
        </span>
        <div style={{ flex: 1, height: 1, background: colors.borderStrong }} />
      </div>

      <Link
        href="/register"
        style={{
          display: "block",
          textAlign: "center",
          border: `1px solid ${colors.borderStrong}`,
          borderRadius: radius.lg,
          padding: "12px",
          fontSize: font.size.base,
          fontWeight: font.weight.semibold,
          color: colors.text,
          textDecoration: "none",
          background: colors.surface,
        }}
      >
        Create a free account
      </Link>
    </div>
  );
}
