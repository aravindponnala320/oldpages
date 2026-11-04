"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { apiClient } from "../../../../lib/api";
import { getAccessToken } from "../../../../lib/auth";
import {
  Button,
  Container,
  Input,
  PageHeader,
  Section,
  Select,
  Spinner,
  Textarea,
  colors,
  font,
  radius,
  useToast,
} from "../../../../components/ui";
import type { ListingResponse, ConditionGrade, ListingUpdateRequest } from "@oldpages/shared-types";

interface EditFormData {
  condition: ConditionGrade;
  handwritten_notes: boolean;
  highlighting_percent: string;
  torn_pages: boolean;
  water_damage: boolean;
  stains: boolean;
  stickers: boolean;
  loose_binding: boolean;
  missing_pages: boolean;
  name_written_inside: boolean;
  damage_details: string;
  price: string;
  negotiable: boolean;
  description: string;
  exchange_preferences: string;
  delivery_pickup: boolean;
  delivery_shipping: boolean;
  shipping_price: string;
  city: string;
  state: string;
  country: string;
  neighborhood: string;
  campus_pickup: boolean;
}

const CONDITIONS: { value: ConditionGrade; label: string }[] = [
  { value: "new_sealed", label: "New / Sealed" },
  { value: "like_new",   label: "Like New" },
  { value: "excellent",  label: "Excellent" },
  { value: "very_good",  label: "Very Good" },
  { value: "good",       label: "Good" },
  { value: "acceptable", label: "Acceptable" },
  { value: "poor",       label: "Poor" },
];

export default function EditListingPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const listingId = params.id;
  const { toast } = useToast();

  const [listing, setListing] = useState<ListingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { register, handleSubmit, reset, watch } = useForm<EditFormData>();

  useEffect(() => {
    async function loadListing() {
      const token = getAccessToken();
      if (!token) { router.push("/login"); return; }
      try {
        const data = await apiClient.getListing(listingId);
        setListing(data);
        const pickup = data.delivery_methods.find((d) => d.method === "pickup");
        const shipping = data.delivery_methods.find((d) => d.method === "shipping");
        reset({
          condition: data.condition?.condition ?? "good",
          handwritten_notes: data.condition?.handwritten_notes ?? false,
          highlighting_percent: String(data.condition?.highlighting_percent ?? 0),
          torn_pages: data.condition?.torn_pages ?? false,
          water_damage: data.condition?.water_damage ?? false,
          stains: data.condition?.stains ?? false,
          stickers: data.condition?.stickers ?? false,
          loose_binding: data.condition?.loose_binding ?? false,
          missing_pages: data.condition?.missing_pages ?? false,
          name_written_inside: data.condition?.name_written_inside ?? false,
          damage_details: data.condition?.damage_details ?? "",
          price: data.price_amount_cents != null ? String(data.price_amount_cents / 100) : "",
          negotiable: data.negotiable,
          description: data.description ?? "",
          exchange_preferences: data.exchange_preferences ?? "",
          delivery_pickup: !!pickup?.enabled,
          delivery_shipping: !!shipping?.enabled,
          shipping_price: shipping?.price_amount_cents != null ? String(shipping.price_amount_cents / 100) : "",
          city: data.location?.city ?? "",
          state: data.location?.state ?? "",
          country: data.location?.country ?? "India",
          neighborhood: data.location?.neighborhood ?? "",
          campus_pickup: data.location?.campus_pickup ?? false,
        });
      } catch (err) {
        setLoadError(err instanceof Error ? err.message : "Failed to load listing");
      } finally {
        setLoading(false);
      }
    }
    void loadListing();
  }, [listingId, reset, router]);

  async function onSubmit(data: EditFormData) {
    const token = getAccessToken();
    if (!token) { router.push("/login"); return; }
    setSubmitting(true);
    try {
      const payload: ListingUpdateRequest = {
        condition: {
          condition: data.condition,
          handwritten_notes: data.handwritten_notes,
          highlighting_percent: data.highlighting_percent ? parseInt(data.highlighting_percent, 10) : null,
          torn_pages: data.torn_pages,
          water_damage: data.water_damage,
          stains: data.stains,
          stickers: data.stickers,
          loose_binding: data.loose_binding,
          missing_pages: data.missing_pages,
          name_written_inside: data.name_written_inside,
          damage_details: data.damage_details || null,
        },
        price_amount_cents: data.price ? Math.round(parseFloat(data.price) * 100) : null,
        negotiable: data.negotiable,
        currency: "INR",
        description: data.description || null,
        exchange_preferences: data.exchange_preferences || null,
        delivery_methods: [
          ...(data.delivery_pickup ? [{ method: "pickup" as const, enabled: true }] : []),
          ...(data.delivery_shipping
            ? [{
                method: "shipping" as const,
                enabled: true,
                price_amount_cents: data.shipping_price ? Math.round(parseFloat(data.shipping_price) * 100) : 0,
              }]
            : []),
        ],
        location: {
          city: data.city,
          state: data.state || null,
          country: data.country,
          neighborhood: data.neighborhood || null,
          public_area: data.neighborhood || data.city,
          campus_pickup: data.campus_pickup,
        },
      };
      await apiClient.updateListing(listingId, payload, token);
      toast("Changes saved", "success");
      setTimeout(() => router.push(`/listings/${listingId}`), 800);
    } catch (err) {
      toast(err instanceof Error ? err.message : "Failed to save changes", "error");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (loadError || !listing) {
    return (
      <div style={{ padding: "24px 0" }}>
        <Container maxWidth={800}>
          <div style={{ background: colors.dangerSoft, border: `1px solid #fecaca`, color: colors.dangerText, borderRadius: radius.lg, padding: "14px 18px", marginBottom: 16 }}>
            {loadError ?? "Listing not found"}
          </div>
          <Button variant="ghost" onClick={() => router.back()}>← Back</Button>
        </Container>
      </div>
    );
  }

  const showShipping = watch("delivery_shipping");
  const showExchange = listing.listing_modes.includes("exchange") || listing.listing_modes.includes("sell_exchange");

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container maxWidth={800}>
        <Button variant="ghost" size="sm" onClick={() => router.back()} style={{ marginBottom: 12 }}>
          ← Back
        </Button>
        <PageHeader
          eyebrow="Edit"
          title="Edit Listing"
          subtitle={listing.title}
        />

        <form onSubmit={handleSubmit(onSubmit)} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <Section title="Condition">
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <Select
                label="Overall condition"
                {...register("condition")}
                options={CONDITIONS.map((c) => ({ value: c.value, label: c.label }))}
              />
              <Input
                label="Highlighting (%)"
                type="number"
                min="0"
                max="100"
                {...register("highlighting_percent")}
              />
              <div>
                <p style={fieldLabel}>Condition flags</p>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 8, marginTop: 8 }}>
                  {[
                    { name: "handwritten_notes" as const, label: "Handwritten notes" },
                    { name: "torn_pages" as const, label: "Torn pages" },
                    { name: "water_damage" as const, label: "Water damage" },
                    { name: "stains" as const, label: "Stains" },
                    { name: "stickers" as const, label: "Stickers" },
                    { name: "loose_binding" as const, label: "Loose binding" },
                    { name: "missing_pages" as const, label: "Missing pages" },
                    { name: "name_written_inside" as const, label: "Name written inside" },
                  ].map(({ name, label }) => (
                    <label key={name} style={checkboxLabel}>
                      <input type="checkbox" {...register(name)} style={{ accentColor: colors.primary }} />
                      {label}
                    </label>
                  ))}
                </div>
              </div>
              <Textarea label="Additional details" rows={3} {...register("damage_details")} />
            </div>
          </Section>

          <Section title="Price">
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <Input
                label="Price (INR)"
                type="number"
                min="0"
                step="1"
                placeholder="Leave blank if free"
                {...register("price")}
              />
              <label style={checkboxLabel}>
                <input type="checkbox" {...register("negotiable")} style={{ accentColor: colors.primary }} />
                Price is negotiable
              </label>
              {showExchange && (
                <Textarea
                  label="Exchange preferences"
                  rows={2}
                  {...register("exchange_preferences")}
                />
              )}
            </div>
          </Section>

          <Section title="Description">
            <Textarea rows={4} placeholder="Describe your listing..." {...register("description")} />
          </Section>

          <Section title="Delivery">
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <label style={checkboxLabel}>
                <input type="checkbox" {...register("delivery_pickup")} style={{ accentColor: colors.primary }} />
                Pickup available
              </label>
              <label style={checkboxLabel}>
                <input type="checkbox" {...register("delivery_shipping")} style={{ accentColor: colors.primary }} />
                Shipping available
              </label>
              {showShipping && (
                <Input
                  label="Shipping cost (INR, leave blank for free)"
                  type="number"
                  min="0"
                  {...register("shipping_price")}
                />
              )}
            </div>
          </Section>

          <Section title="Location">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <Input label="City *" {...register("city", { required: true })} />
              <Input label="State" {...register("state")} />
              <Input label="Neighborhood" {...register("neighborhood")} />
              <Input label="Country" {...register("country")} />
            </div>
            <label style={{ ...checkboxLabel, marginTop: 12 }}>
              <input type="checkbox" {...register("campus_pickup")} style={{ accentColor: colors.primary }} />
              Campus pickup available
            </label>
          </Section>

          <div style={{ display: "flex", gap: 10 }}>
            <Button type="submit" variant="primary" loading={submitting}>Save Changes</Button>
            <Button type="button" variant="secondary" onClick={() => router.push(`/listings/${listingId}`)}>
              Cancel
            </Button>
          </div>
        </form>
      </Container>
    </div>
  );
}

const fieldLabel: React.CSSProperties = {
  fontSize: font.size.sm,
  fontWeight: font.weight.semibold,
  color: colors.textMuted,
  margin: 0,
};
const checkboxLabel: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  fontSize: font.size.base,
  color: colors.textMuted,
  cursor: "pointer",
};
