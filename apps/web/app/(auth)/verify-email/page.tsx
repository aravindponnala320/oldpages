"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiClient } from "../../../lib/api";
import { colors, font, radius } from "../../../components/ui";

type State = "verifying" | "success" | "error";

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={null}>
      <VerifyEmailInner />
    </Suspense>
  );
}

function VerifyEmailInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token") ?? "";
  const [state, setState] = useState<State>("verifying");
  const [message, setMessage] = useState<string>("Verifying your email...");

  useEffect(() => {
    if (!token) {
      setState("error");
      setMessage("Verification link is missing a token.");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await apiClient.verifyEmail(token);
        if (cancelled) return;
        setState("success");
        setMessage("Your email is verified. Redirecting...");
        setTimeout(() => router.push("/dashboard"), 1800);
      } catch (err) {
        if (cancelled) return;
        setState("error");
        setMessage(
          err instanceof Error
            ? err.message
            : "This verification link is invalid or has expired.",
        );
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token, router]);

  const color =
    state === "success"
      ? colors.primary
      : state === "error"
      ? colors.dangerText
      : colors.text;

  return (
    <div>
      <h1 style={{ fontSize: font.size["2xl"], fontWeight: font.weight.heavy, margin: "0 0 10px", color }}>
        {state === "verifying" && "Verifying your email..."}
        {state === "success" && "Email verified"}
        {state === "error" && "Could not verify"}
      </h1>
      <p style={{ color: colors.textSubtle, fontSize: font.size.base, lineHeight: 1.5 }}>
        {message}
      </p>
      {state === "error" && (
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
      )}
    </div>
  );
}
