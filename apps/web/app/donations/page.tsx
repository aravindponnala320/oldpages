"use client";

import { useEffect, useState } from "react";
import {
  Container,
  EmptyState,
  Icon,
  LinkButton,
  PageHeader,
  Spinner,
  colors,
  font,
  radius,
  shadow,
} from "../../components/ui";

/**
 * Donation campaigns page.
 *
 * There is no `listDonationCampaigns` endpoint yet in the OldPages API — only
 * `createDonationPledge` on individual campaign pages. Until the list endpoint
 * ships, this route shows a proper empty state instead of hardcoded demo data.
 */
export default function DonationsPage() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // As soon as an endpoint exists (e.g. apiClient.listDonationCampaigns), swap
    // this fake tick for a real fetch and hydrate state below.
    const t = setTimeout(() => setLoading(false), 100);
    return () => clearTimeout(t);
  }, []);

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container>
        <PageHeader
          eyebrow="Give back"
          title="Book Donation Campaigns"
          subtitle="Pledge your books to campaigns helping schools, libraries, and communities across India."
        />

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 16,
            marginBottom: 24,
          }}
        >
          <StatCard label="Active Campaigns" value="—" />
          <StatCard label="Books Needed" value="—" />
          <StatCard label="Books Pledged" value="—" />
        </div>

        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
            <Spinner size="md" />
          </div>
        ) : (
          <EmptyState
            icon={<Icon.heart size={26} color={colors.primary} />}
            title="No campaigns available yet"
            description="Donation campaigns will appear here as soon as the campaign API endpoint is available. In the meantime, you can browse listings to donate directly to individual sellers."
            action={<LinkButton href="/search?listing_mode=donate">Browse Donation Listings</LinkButton>}
          />
        )}
      </Container>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div
      style={{
        background: colors.surface,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.xl,
        padding: 18,
        boxShadow: shadow.sm,
      }}
    >
      <div style={{ fontSize: font.size["2xl"], fontWeight: font.weight.heavy, color: colors.text }}>
        {value}
      </div>
      <div style={{ fontSize: font.size.sm, color: colors.textSubtle, marginTop: 4 }}>{label}</div>
    </div>
  );
}
