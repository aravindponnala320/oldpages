"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiClient } from "../../../lib/api";
import { Button, Input, colors, font, radius } from "../../../components/ui";

const RESEND_SECONDS = 60;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);
  // Only a local/dev API returns the link itself (no email is sent there).
  const [devLink, setDevLink] = useState<string | null>(null);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [cooldown]);

  async function send() {
    const address = email.trim();
    if (!EMAIL_RE.test(address)) {
      setError("Enter a valid email address.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.forgotPassword(address);
      const token = res.development_token?.token;
      setDevLink(
        token ? `/reset-password?token=${encodeURIComponent(token)}` : null,
      );
      setSubmitted(true);
      setCooldown(RESEND_SECONDS);
    } catch {
      setError(
        "We couldn't send the email right now. Check your connection and try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (submitted) {
    return (
      <div>
        <div
          aria-hidden
          style={{
            width: 52,
            height: 52,
            borderRadius: 14,
            background: colors.primarySoft,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 26,
            marginBottom: 16,
          }}
        >
          ✉️
        </div>
        <h1
          style={{
            fontSize: font.size["2xl"],
            fontWeight: font.weight.heavy,
            color: colors.text,
            margin: "0 0 10px",
          }}
        >
          Check your email
        </h1>
        <p
          style={{
            color: colors.textMuted,
            fontSize: font.size.base,
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          If{" "}
          <strong style={{ color: colors.text, wordBreak: "break-all" }}>
            {email.trim()}
          </strong>{" "}
          has an OldPages account, a link to reset your password is on its way.
          It works once and expires in 30 minutes.
        </p>
        <p
          style={{
            color: colors.textSubtle,
            fontSize: font.size.sm,
            lineHeight: 1.6,
            margin: "12px 0 0",
          }}
        >
          Signed up with Google? The same link lets you add a password, or you
          can keep using{" "}
          <Link
            href="/login"
            style={{
              color: colors.primary,
              textDecoration: "none",
              fontWeight: font.weight.medium,
            }}
          >
            Continue with Google
          </Link>
          .
        </p>

        {devLink && (
          <div
            style={{
              marginTop: 16,
              padding: "10px 12px",
              borderRadius: radius.md,
              border: `1px dashed ${colors.borderStrong}`,
              fontSize: font.size.sm,
              color: colors.textMuted,
            }}
          >
            Development mode: no email is sent.{" "}
            <Link
              href={devLink}
              style={{
                color: colors.primary,
                fontWeight: font.weight.semibold,
              }}
            >
              Open the reset link
            </Link>
          </div>
        )}

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
            marginTop: 24,
          }}
        >
          <Button
            type="button"
            variant="secondary"
            fullWidth
            size="lg"
            disabled={cooldown > 0}
            loading={loading}
            onClick={send}
          >
            {cooldown > 0 ? `Resend email in ${cooldown}s` : "Resend email"}
          </Button>
          <p
            style={{
              color: colors.textSubtle,
              fontSize: font.size.sm,
              textAlign: "center",
              margin: 0,
            }}
          >
            Nothing yet? Check spam, or{" "}
            <button
              type="button"
              onClick={() => {
                setSubmitted(false);
                setDevLink(null);
              }}
              style={{
                background: "none",
                border: "none",
                padding: 0,
                color: colors.primary,
                cursor: "pointer",
                fontWeight: font.weight.medium,
                fontSize: "inherit",
              }}
            >
              use a different email
            </button>
            .
          </p>
        </div>

        <div
          style={{ textAlign: "center", marginTop: 20, fontSize: font.size.sm }}
        >
          <Link
            className="op-tap"
            href="/login"
            style={{
              color: colors.primary,
              textDecoration: "none",
              fontWeight: font.weight.medium,
            }}
          >
            Back to sign in
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      <header style={{ marginBottom: 24 }}>
        <h1
          style={{
            fontSize: font.size["3xl"],
            fontWeight: font.weight.heavy,
            color: colors.text,
            margin: "0 0 6px",
            letterSpacing: "-0.02em",
          }}
        >
          Forgot password?
        </h1>
        <p
          style={{
            color: colors.textSubtle,
            fontSize: font.size.base,
            margin: 0,
            lineHeight: 1.5,
          }}
        >
          Enter the email you use for OldPages and we&apos;ll send you a link to
          set a new password.
        </p>
      </header>

      {error && (
        <div
          role="alert"
          style={{
            background: colors.dangerSoft,
            border: "1px solid #fecaca",
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

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        noValidate
        style={{ display: "flex", flexDirection: "column", gap: 16 }}
      >
        <Input
          label="Email address"
          type="email"
          inputMode="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
          autoCapitalize="none"
          spellCheck={false}
          autoFocus
          required
        />
        <Button
          type="submit"
          loading={loading}
          disabled={!email.trim()}
          fullWidth
          size="lg"
        >
          Send reset link
        </Button>
      </form>

      <div
        style={{ textAlign: "center", marginTop: 20, fontSize: font.size.sm }}
      >
        <Link
          className="op-tap"
          href="/login"
          style={{
            color: colors.primary,
            textDecoration: "none",
            fontWeight: font.weight.medium,
          }}
        >
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
