"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ApiClientError } from "@oldpages/api-client";
import { apiClient } from "../../../lib/api";
import { Button, Input, colors, font, radius } from "../../../components/ui";
import {
  MIN_PASSWORD_LENGTH,
  PasswordStrength,
} from "../../../components/PasswordStrength";

// The token is moved out of the address bar (history, screenshots, shared URLs) into this tab's
// session storage, so a reload still works.
const TOKEN_KEY = "op_reset_token";

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordInner />
    </Suspense>
  );
}

function readToken(fromUrl: string | null): string {
  try {
    if (fromUrl) {
      sessionStorage.setItem(TOKEN_KEY, fromUrl);
      return fromUrl;
    }
    return sessionStorage.getItem(TOKEN_KEY) ?? "";
  } catch {
    return fromUrl ?? "";
  }
}

function forgetToken() {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage blocked */
  }
}

function ResetPasswordInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [token, setToken] = useState<string | null>(null); // null until read on the client

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [linkDead, setLinkDead] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fromUrl = searchParams.get("token");
    setToken(readToken(fromUrl));
    if (fromUrl) window.history.replaceState(null, "", "/reset-password");
  }, [searchParams]);

  const tooShort = password.length > 0 && password.length < MIN_PASSWORD_LENGTH;
  const mismatch = confirm.length > 0 && confirm !== password;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`Use at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }
    if (password !== confirm) {
      setError("The two passwords don't match.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await apiClient.resetPassword(token ?? "", password);
      forgetToken();
      setDone(true);
      setTimeout(() => router.push("/login?reset=1"), 2000);
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 401) {
        forgetToken();
        setLinkDead(true);
      } else if (err instanceof ApiClientError && err.status === 422) {
        setError(`Use at least ${MIN_PASSWORD_LENGTH} characters.`);
      } else {
        setError(
          "Couldn't update your password. Check your connection and try again.",
        );
      }
    } finally {
      setLoading(false);
    }
  }

  if (token === null) return null;

  if (!token || linkDead) {
    return (
      <div>
        <div
          aria-hidden
          style={{
            width: 52,
            height: 52,
            borderRadius: 14,
            background: colors.dangerSoft,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 26,
            marginBottom: 16,
          }}
        >
          ⏳
        </div>
        <h1
          style={{
            fontSize: font.size["2xl"],
            fontWeight: font.weight.heavy,
            color: colors.text,
            margin: "0 0 10px",
          }}
        >
          {linkDead ? "This link has expired" : "Open the link from your email"}
        </h1>
        <p
          style={{
            color: colors.textMuted,
            fontSize: font.size.base,
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          {linkDead
            ? "Reset links work once and only for 30 minutes, and a newer link replaces older ones. Ask for a fresh one below."
            : "To set a new password, use the button in the reset email we sent you. If you can't find it, ask for a new one."}
        </p>
        <Link
          href="/forgot-password"
          style={{
            display: "block",
            textAlign: "center",
            borderRadius: radius.lg,
            padding: "13px",
            fontSize: font.size.base,
            fontWeight: font.weight.semibold,
            color: "#fff",
            textDecoration: "none",
            background: colors.primary,
            marginTop: 24,
          }}
        >
          Send me a new link
        </Link>
        <div
          style={{ textAlign: "center", marginTop: 16, fontSize: font.size.sm }}
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

  if (done) {
    return (
      <div>
        <div
          aria-hidden
          style={{
            width: 52,
            height: 52,
            borderRadius: 14,
            background: "#dcfce7",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 26,
            marginBottom: 16,
          }}
        >
          ✅
        </div>
        <h1
          style={{
            fontSize: font.size["2xl"],
            fontWeight: font.weight.heavy,
            color: colors.text,
            margin: "0 0 10px",
          }}
        >
          Password updated
        </h1>
        <p
          style={{
            color: colors.textMuted,
            fontSize: font.size.base,
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          For your safety we signed you out on every device. Taking you to sign
          in…
        </p>
      </div>
    );
  }

  const toggle = (
    <button
      className="op-tap"
      type="button"
      onClick={() => setShow((v) => !v)}
      aria-label={show ? "Hide password" : "Show password"}
      style={{
        background: "none",
        border: "none",
        cursor: "pointer",
        color: colors.textSubtle,
        fontSize: font.size.sm,
        fontWeight: font.weight.medium,
      }}
    >
      {show ? "Hide" : "Show"}
    </button>
  );

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
          Set a new password
        </h1>
        <p
          style={{
            color: colors.textSubtle,
            fontSize: font.size.base,
            margin: 0,
            lineHeight: 1.5,
          }}
        >
          At least {MIN_PASSWORD_LENGTH} characters. A short sentence is easy to
          remember and hard to guess.
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
        onSubmit={handleSubmit}
        noValidate
        style={{ display: "flex", flexDirection: "column", gap: 16 }}
      >
        <div>
          <Input
            label="New password"
            type={show ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={`At least ${MIN_PASSWORD_LENGTH} characters`}
            autoComplete="new-password"
            autoFocus
            required
            error={
              tooShort
                ? `${MIN_PASSWORD_LENGTH - password.length} more character${MIN_PASSWORD_LENGTH - password.length === 1 ? "" : "s"} needed`
                : undefined
            }
            suffix={toggle}
          />
          {password && <PasswordStrength password={password} />}
        </div>
        <Input
          label="Confirm new password"
          type={show ? "text" : "password"}
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          autoComplete="new-password"
          required
          error={mismatch ? "Passwords don't match" : undefined}
        />
        <Button
          type="submit"
          loading={loading}
          disabled={
            password.length < MIN_PASSWORD_LENGTH || confirm !== password
          }
          fullWidth
          size="lg"
        >
          Update password
        </Button>
      </form>
    </div>
  );
}
