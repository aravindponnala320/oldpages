"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../contexts/AuthContext";
import { colors, font, radius } from "./ui";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (resp: { credential: string }) => void;
            ux_mode?: "popup" | "redirect";
          }) => void;
          renderButton: (
            el: HTMLElement,
            options: {
              theme?: "outline" | "filled_blue" | "filled_black";
              size?: "large" | "medium" | "small";
              shape?: "rectangular" | "pill" | "circle" | "square";
              text?: "signin_with" | "signup_with" | "continue_with" | "signin";
              width?: number;
              logo_alignment?: "left" | "center";
            },
          ) => void;
        };
      };
    };
  }
}

export function GoogleSignInButton({ redirectTo = "/dashboard" }: { redirectTo?: string }) {
  const { loginWithGoogle } = useAuth();
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  useEffect(() => {
    if (!clientId || !containerRef.current) return;

    function initialize() {
      if (!window.google || !containerRef.current || !clientId) return;
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: async ({ credential }) => {
          setError(null);
          try {
            await loginWithGoogle(credential);
            router.push(redirectTo);
          } catch (err) {
            setError(err instanceof Error ? err.message : "Google sign-in failed.");
          }
        },
      });
      window.google.accounts.id.renderButton(containerRef.current, {
        theme: "outline",
        size: "large",
        shape: "rectangular",
        text: "continue_with",
        logo_alignment: "left",
        width: 320,
      });
    }

    if (window.google) {
      initialize();
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = initialize;
    document.head.appendChild(script);
  }, [clientId, loginWithGoogle, redirectTo, router]);

  if (!clientId) return null;

  return (
    <div>
      <div ref={containerRef} style={{ display: "flex", justifyContent: "center" }} />
      {error && (
        <div
          role="alert"
          style={{
            marginTop: 12,
            background: colors.dangerSoft,
            border: "1px solid #fecaca",
            color: colors.dangerText,
            borderRadius: radius.lg,
            padding: "10px 14px",
            fontSize: font.size.sm,
          }}
        >
          {error}
        </div>
      )}
    </div>
  );
}
