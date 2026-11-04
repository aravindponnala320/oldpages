"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../contexts/AuthContext";
import {
  Badge,
  Button,
  Container,
  PageHeader,
  Section,
  Spinner,
  colors,
  font,
  radius,
  shadow,
  useToast,
} from "../../components/ui";

type Plan = {
  id: string;
  name: string;
  price_monthly: number | null;
  price_yearly: number | null;
  currency: string;
  features: string[];
  featured?: boolean;
  tagline: string;
};

const PLANS: Plan[] = [
  {
    id: "free", name: "Free", price_monthly: null, price_yearly: null, currency: "INR",
    tagline: "Perfect for casual readers",
    features: ["Up to 5 active listings", "Basic search", "Chat with buyers", "Community access (read-only)"],
  },
  {
    id: "plus", name: "Plus", price_monthly: 99, price_yearly: 799, currency: "INR", featured: true,
    tagline: "For active buyers & sellers",
    features: ["Up to 30 active listings", "Priority search placement", "Chat + offers", "Join communities", "Events RSVP", "Saved search alerts"],
  },
  {
    id: "pro", name: "Pro", price_monthly: 299, price_yearly: 2499, currency: "INR",
    tagline: "For power users & institutions",
    features: ["Unlimited listings", "Top search placement", "All Plus features", "Business profile", "Staff management", "Bulk inventory import", "Analytics dashboard", "Priority support"],
  },
];

const FEATURES_COMPARE = [
  { label: "Active listings",       values: ["5", "30", "Unlimited"] },
  { label: "Chat & offers",         values: ["✓", "✓", "✓"] },
  { label: "Communities",           values: ["Read-only", "Full access", "Full access"] },
  { label: "Events RSVP",           values: ["—", "✓", "✓"] },
  { label: "Saved search alerts",   values: ["—", "✓", "✓"] },
  { label: "Business profile",      values: ["—", "—", "✓"] },
  { label: "Bulk import",           values: ["—", "—", "✓"] },
  { label: "Analytics",             values: ["—", "—", "✓"] },
  { label: "Priority support",      values: ["—", "—", "✓"] },
];

type BillingCycle = "monthly" | "yearly";

export default function SubscriptionsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();
  const [billing, setBilling] = useState<BillingCycle>("monthly");
  const [subscribing, setSubscribing] = useState<string | null>(null);
  const [currentPlanId] = useState<string>("free");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/");
  }, [isAuthenticated, isLoading, router]);

  const handleSubscribe = async (planId: string) => {
    if (!isAuthenticated) { router.push("/"); return; }
    setSubscribing(planId);
    await new Promise((r) => setTimeout(r, 800));
    setSubscribing(null);
    toast(`Payment integration coming soon — ${planId} plan requested.`, "info");
  };

  if (isLoading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div style={{ padding: "32px 0 40px" }}>
      <Container>
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <PageHeader
            eyebrow="Subscription"
            title="Choose Your Plan"
            subtitle="Unlock more features to buy, sell, and connect with readers"
          />
        </div>

        <div style={{ display: "flex", justifyContent: "center", marginBottom: 28 }}>
          <div
            style={{
              background: colors.surfaceMuted,
              borderRadius: radius.pill,
              padding: 4,
              display: "inline-flex",
              gap: 4,
              border: `1px solid ${colors.border}`,
            }}
          >
            {(["monthly", "yearly"] as BillingCycle[]).map((cycle) => {
              const active = billing === cycle;
              return (
                <button
                  key={cycle}
                  onClick={() => setBilling(cycle)}
                  style={{
                    padding: "8px 18px",
                    borderRadius: radius.pill,
                    border: "none",
                    cursor: "pointer",
                    fontWeight: font.weight.semibold,
                    fontSize: font.size.base,
                    background: active ? colors.surface : "transparent",
                    color: active ? colors.text : colors.textSubtle,
                    boxShadow: active ? shadow.sm : "none",
                    transition: "all 0.2s",
                  }}
                >
                  {cycle.charAt(0).toUpperCase() + cycle.slice(1)}
                  {cycle === "yearly" && (
                    <span style={{ marginLeft: 6, fontSize: font.size.xs, color: colors.primary, fontWeight: font.weight.bold }}>−33%</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 20, marginBottom: 32, alignItems: "start" }}>
          {PLANS.map((plan) => {
            const price = billing === "monthly" ? plan.price_monthly : plan.price_yearly;
            const isCurrent = currentPlanId === plan.id;
            return (
              <div
                key={plan.id}
                style={{
                  background: colors.surface,
                  border: `${plan.featured ? "2px" : "1px"} solid ${plan.featured ? colors.primary : colors.border}`,
                  borderRadius: radius.xl,
                  padding: 24,
                  position: "relative",
                  boxShadow: plan.featured ? "0 4px 20px rgba(37,99,235,0.12)" : shadow.sm,
                }}
              >
                {plan.featured && (
                  <div
                    style={{
                      position: "absolute", top: -12, left: "50%", transform: "translateX(-50%)",
                      background: colors.primary, color: "#fff",
                      fontSize: font.size.xs, fontWeight: font.weight.bold,
                      padding: "3px 14px", borderRadius: radius.pill,
                    }}
                  >
                    Most Popular
                  </div>
                )}
                <h2 style={{ margin: "0 0 4px", fontSize: font.size.lg, fontWeight: font.weight.bold, color: colors.text }}>{plan.name}</h2>
                <p style={{ margin: "0 0 14px", fontSize: font.size.sm, color: colors.textSubtle }}>{plan.tagline}</p>
                {price != null ? (
                  <div>
                    <span style={{ fontSize: font.size["3xl"], fontWeight: font.weight.heavy, color: colors.text }}>₹{price.toLocaleString("en-IN")}</span>
                    <span style={{ fontSize: font.size.base, color: colors.textSubtle, marginLeft: 4 }}>/{billing === "monthly" ? "mo" : "yr"}</span>
                  </div>
                ) : (
                  <div>
                    <span style={{ fontSize: font.size["3xl"], fontWeight: font.weight.heavy, color: colors.text }}>Free</span>
                    <span style={{ fontSize: font.size.base, color: colors.textSubtle, marginLeft: 4 }}>forever</span>
                  </div>
                )}

                <ul style={{ listStyle: "none", padding: 0, margin: "18px 0", display: "flex", flexDirection: "column", gap: 8 }}>
                  {plan.features.map((f) => (
                    <li key={f} style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: font.size.base, color: colors.textMuted }}>
                      <span style={{ color: colors.primary, fontWeight: font.weight.bold, marginTop: 1 }}>✓</span>
                      {f}
                    </li>
                  ))}
                </ul>

                {isCurrent ? (
                  <Badge variant="success" label="Current Plan" size="md" />
                ) : (
                  <Button
                    variant={plan.featured ? "primary" : "secondary"}
                    fullWidth
                    loading={subscribing === plan.id}
                    onClick={() => plan.price_monthly != null && handleSubscribe(plan.id)}
                    disabled={plan.price_monthly == null}
                  >
                    {plan.price_monthly != null ? `Get ${plan.name}` : "Your Current Plan"}
                  </Button>
                )}
              </div>
            );
          })}
        </div>

        <Section title="Feature comparison">
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: font.size.base }}>
              <thead>
                <tr>
                  <th style={th}>Feature</th>
                  {PLANS.map((p) => (
                    <th key={p.id} style={{ ...th, textAlign: "center", color: p.featured ? colors.primary : colors.text, fontWeight: font.weight.bold }}>
                      {p.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {FEATURES_COMPARE.map((row, i) => (
                  <tr key={row.label} style={{ background: i % 2 === 0 ? colors.surfaceMuted : "transparent" }}>
                    <td style={{ ...td, color: colors.textMuted, fontWeight: font.weight.medium }}>{row.label}</td>
                    {row.values.map((v, j) => (
                      <td
                        key={j}
                        style={{
                          ...td,
                          textAlign: "center",
                          fontWeight: font.weight.semibold,
                          color: v === "—" ? colors.textFaint : v === "✓" ? colors.primary : colors.text,
                        }}
                      >
                        {v}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <p style={{ textAlign: "center", color: colors.textFaint, fontSize: font.size.sm, marginTop: 20 }}>
          Cancel anytime. No long-term contracts. All prices inclusive of GST.
        </p>
      </Container>
    </div>
  );
}

const th: React.CSSProperties = {
  textAlign: "left",
  padding: "10px 14px",
  borderBottom: `1px solid ${colors.border}`,
  color: colors.textSubtle,
  fontWeight: font.weight.semibold,
  fontSize: font.size.sm,
};
const td: React.CSSProperties = { padding: "10px 14px" };
