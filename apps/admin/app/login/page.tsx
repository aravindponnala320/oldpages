"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { setTokens } from "../../lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw new Error("Invalid credentials");
      const data = await res.json();
      setTokens(data.tokens.access_token, data.tokens.refresh_token, data.user?.email);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#f7f7f3",
    }}>
      <div style={{
        background: "#fff",
        border: "1px solid #d9ddd6",
        borderRadius: 8,
        padding: "2rem",
        width: "100%",
        maxWidth: 400,
      }}>
        <h1 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 .25rem" }}>OldPages Admin</h1>
        <p style={{ color: "#5c6670", fontSize: ".875rem", margin: "0 0 1.5rem" }}>Sign in to continue</p>

        {error && (
          <div style={{ background: "#fee2e2", color: "#991b1b", padding: ".75rem", borderRadius: 6, marginBottom: "1rem", fontSize: ".875rem" }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: ".375rem" }}>
            <label style={{ fontSize: ".8rem", fontWeight: 500, color: "#1f2933" }}>Email</label>
            <input
              className="admin-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              style={{ width: "100%" }}
            />
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: ".375rem" }}>
            <label style={{ fontSize: ".8rem", fontWeight: 500, color: "#1f2933" }}>Password</label>
            <input
              className="admin-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              style={{ width: "100%" }}
            />
          </div>
          <button
            className="admin-btn admin-btn-primary"
            type="submit"
            disabled={loading}
            style={{ width: "100%", justifyContent: "center" }}
          >
            {loading ? <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
