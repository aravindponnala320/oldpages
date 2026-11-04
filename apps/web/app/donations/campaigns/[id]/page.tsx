"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../../../contexts/AuthContext";
import {
  Button,
  Container,
  EmptyState,
  Icon,
  Input,
  Section,
  Select,
  Spinner,
  Textarea,
  colors,
  font,
  radius,
  useToast,
} from "../../../../components/ui";

/**
 * Campaign detail page.
 *
 * The OldPages API exposes `createDonationPledge` but no per-campaign fetch or
 * catalog endpoint. Until that ships, this route renders an empty state instead
 * of hardcoded demo campaigns.
 */
type Campaign = null;

type PledgeForm = {
  needId: string;
  condition: string;
  quantity: string;
  notes: string;
};

function ProgressBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div style={{ background: colors.surfaceMuted, borderRadius: radius.pill, height: 8, overflow: "hidden" }}>
      <div
        style={{
          height: "100%",
          width: `${pct}%`,
          background: colors.primary,
          borderRadius: radius.pill,
          transition: "width 0.3s",
        }}
      />
    </div>
  );
}

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [campaign, setCampaign] = useState<Campaign>(null);
  const [loading, setLoading] = useState(true);
  const [pledging, setPledging] = useState(false);
  const [pledgeSuccess, setPledgeSuccess] = useState(false);
  const [form, setForm] = useState<PledgeForm>({ needId: "", condition: "good", quantity: "1", notes: "" });

  useEffect(() => {
    // No campaign lookup endpoint yet. When one lands, fetch by id here.
    const t = setTimeout(() => setLoading(false), 100);
    return () => clearTimeout(t);
  }, [id]);

  const handlePledge = async () => {
    if (!isAuthenticated) { router.push("/"); return; }
    if (!form.needId || !form.quantity) return;
    setPledging(true);
    try {
      // TODO: swap for `apiClient.createDonationPledge(campaign.id, {...}, token)` when API supports it.
      await new Promise((r) => setTimeout(r, 600));
      setPledgeSuccess(true);
      toast("Pledge recorded (demo)", "success");
    } finally {
      setPledging(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", paddingTop: 60 }}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (!campaign) {
    return (
      <div style={{ padding: "24px 0 40px" }}>
        <Container maxWidth={760}>
          <Button variant="ghost" size="sm" onClick={() => router.back()} style={{ marginBottom: 12 }}>
            ← Back
          </Button>
          <EmptyState
            icon={<Icon.heart size={26} color={colors.primary} />}
            title="Campaign details unavailable"
            description={
              `Campaign #${id} — the campaign details endpoint isn't available yet. ` +
              `This page will populate as soon as the API exposes a per-campaign fetch.`
            }
          />
        </Container>
      </div>
    );
  }

  // The block below is unreachable until the API ships. Kept as a scaffold so
  // wiring real data later becomes a data-swap rather than a rewrite.
  const _unused = (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={760}>
        <Button variant="ghost" size="sm" onClick={() => router.back()} style={{ marginBottom: 12 }}>
          ← Back
        </Button>
        <div style={{ marginBottom: 16 }}>
          <Section title="Books needed">
            <ProgressBar value={0} max={0} />
          </Section>
        </div>
        <Section title="Pledge books">
          {pledgeSuccess ? (
            <div style={{ background: colors.successSoft, color: colors.successText, borderRadius: radius.lg, padding: 14 }}>
              <p style={{ margin: 0, fontWeight: font.weight.semibold }}>Thank you for your pledge!</p>
              <p style={{ margin: "4px 0 0", fontSize: font.size.sm }}>The organizer will contact you shortly.</p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <Select
                label="Book needed"
                value={form.needId}
                onChange={(e) => setForm((f) => ({ ...f, needId: e.target.value }))}
                options={[]}
              />
              <Select
                label="Condition"
                value={form.condition}
                onChange={(e) => setForm((f) => ({ ...f, condition: e.target.value }))}
                options={[
                  { value: "new_sealed", label: "New / Sealed" },
                  { value: "like_new", label: "Like New" },
                  { value: "very_good", label: "Very Good" },
                  { value: "good", label: "Good" },
                  { value: "acceptable", label: "Acceptable" },
                ]}
              />
              <Input
                label="Quantity"
                type="number"
                min={1}
                value={form.quantity}
                onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))}
              />
              <Textarea
                label="Notes (optional)"
                rows={2}
                placeholder="Any notes about the book's condition..."
                value={form.notes}
                onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              />
              <Button variant="primary" loading={pledging} onClick={handlePledge} disabled={!isAuthenticated}>
                Pledge Books
              </Button>
            </div>
          )}
        </Section>
      </Container>
    </div>
  );
  void _unused;

  return null;
}
