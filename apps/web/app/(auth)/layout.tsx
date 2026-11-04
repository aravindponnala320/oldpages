import Link from "next/link";
import { Icon, colors, font, radius } from "../../components/ui";

const TRUST_POINTS = [
  { title: "Buy & sell textbooks", body: "Student-friendly prices, verified sellers." },
  { title: "Exchange nearby",       body: "Swap books directly with readers in your area." },
  { title: "Donate & discover",     body: "Give books a new life; find rare reads." },
  { title: "Trusted on campus",     body: "Active on 50+ Indian campuses today." },
];

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        background: colors.bg,
        fontFamily: font.family,
      }}
    >
      {/* Brand panel */}
      <aside
        style={{
          background: `linear-gradient(160deg, ${colors.primaryStrong} 0%, ${colors.primary} 60%, #3b82f6 100%)`,
          color: "#fff",
          padding: "48px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div
          aria-hidden
          style={{
            position: "absolute", inset: 0, opacity: 0.08,
            backgroundImage:
              "radial-gradient(circle at 20% 30%, white 1px, transparent 1px), radial-gradient(circle at 75% 65%, white 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
        <Link href="/" style={{ display: "inline-flex", alignItems: "center", gap: 10, textDecoration: "none", position: "relative" }}>
          <div
            style={{
              width: 44, height: 44, borderRadius: radius.lg,
              background: "rgba(255,255,255,0.16)",
              backdropFilter: "blur(8px)",
              border: "1px solid rgba(255,255,255,0.28)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}
          >
            <Icon.book size={22} color="#fff" />
          </div>
          <span style={{ color: "#fff", fontWeight: font.weight.heavy, fontSize: font.size["xl"], letterSpacing: "-0.02em" }}>
            OldPages
          </span>
        </Link>

        <div style={{ position: "relative" }}>
          <p
            style={{
              color: "rgba(255,255,255,0.65)",
              fontSize: font.size.xs,
              fontWeight: font.weight.bold,
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              margin: "0 0 14px",
            }}
          >
            India's book exchange platform
          </p>
          <h2
            style={{
              color: "#fff",
              fontSize: font.size["4xl"],
              fontWeight: font.weight.heavy,
              lineHeight: 1.15,
              margin: "0 0 24px",
              letterSpacing: "-0.02em",
            }}
          >
            Give books a second life.
            <br />
            Find your next read.
          </h2>
          <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 14 }}>
            {TRUST_POINTS.map((p) => (
              <li key={p.title} style={{ display: "flex", gap: 12 }}>
                <span
                  style={{
                    width: 32, height: 32, borderRadius: 8,
                    background: "rgba(255,255,255,0.14)",
                    display: "inline-flex", alignItems: "center", justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <Icon.check size={18} color="#fff" />
                </span>
                <div>
                  <div style={{ fontSize: font.size.md, fontWeight: font.weight.semibold, color: "#fff" }}>{p.title}</div>
                  <div style={{ fontSize: font.size.sm, color: "rgba(255,255,255,0.72)" }}>{p.body}</div>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div
          style={{
            position: "relative",
            borderTop: "1px solid rgba(255,255,255,0.18)",
            paddingTop: 20,
            display: "flex",
            gap: 32,
          }}
        >
          {[["10K+", "Books listed"], ["50+", "Campuses"], ["₹0", "Platform fee"]].map(([num, label]) => (
            <div key={label}>
              <div style={{ color: "#fff", fontWeight: font.weight.heavy, fontSize: font.size.xl }}>{num}</div>
              <div style={{ color: "rgba(255,255,255,0.6)", fontSize: font.size.xs }}>{label}</div>
            </div>
          ))}
        </div>
      </aside>

      {/* Form panel */}
      <main
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          padding: "48px 32px",
          background: colors.surface,
          overflowY: "auto",
        }}
      >
        <div style={{ width: "100%", maxWidth: 440 }}>{children}</div>
      </main>

      <style>{`
        @media (max-width: 900px) {
          div[style*="gridTemplateColumns: 1fr 1fr"] { grid-template-columns: 1fr !important; }
          aside[style*="linear-gradient"] { display: none !important; }
        }
      `}</style>
    </div>
  );
}
