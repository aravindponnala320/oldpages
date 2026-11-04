import { notFound } from "next/navigation";
import Link from "next/link";
import { apiClient } from "../../../lib/api";
import { ListingActions } from "./ListingActions";
import { ListingMessagesTab } from "./ListingMessagesTab";
import type { ListingResponse, ConditionGrade } from "@oldpages/shared-types";
import {
  Badge,
  BookCover,
  ConditionBadge,
  Container,
  Icon,
  Section,
  colors,
  font,
  formatPrice,
  radius,
} from "../../../components/ui";

export const revalidate = 30;

interface ListingPageProps {
  params: Promise<{ id: string }>;
}

const MODE_LABEL: Record<string, string> = {
  sell: "For Sale",
  exchange: "Exchange",
  sell_exchange: "Sale / Exchange",
  donate: "Donate",
  lend: "Lend",
  rent: "Rent",
  request: "Wanted",
  giveaway: "Giveaway",
};

function ConditionDetails({ condition }: { condition: NonNullable<ListingResponse["condition"]> }) {
  const flags: string[] = [];
  if (condition.handwritten_notes) flags.push("Handwritten notes");
  if (condition.highlighting_percent != null && condition.highlighting_percent > 0) flags.push(`${condition.highlighting_percent}% highlighted`);
  if (condition.torn_pages) flags.push("Torn pages");
  if (condition.water_damage) flags.push("Water damage");
  if (condition.stains) flags.push("Stains");
  if (condition.stickers) flags.push("Stickers");
  if (condition.loose_binding) flags.push("Loose binding");
  if (condition.missing_pages) flags.push("Missing pages");
  if (condition.library_markings) flags.push("Library markings");
  if (condition.name_written_inside) flags.push("Name written inside");
  if (condition.odor_or_smoke_exposure) flags.push("Odor/smoke exposure");
  if (condition.signed_by_author) flags.push("Signed by author");
  if (condition.first_edition) flags.push("First edition");

  return (
    <div>
      <div style={{ marginBottom: 10 }}>
        <ConditionBadge condition={condition.condition} size="md" />
      </div>
      {flags.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 8 }}>
          {flags.map((flag) => <Badge key={flag} label={flag} />)}
        </div>
      )}
      {condition.damage_details && (
        <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textSubtle }}>{condition.damage_details}</p>
      )}
    </div>
  );
}

export default async function ListingPage({ params }: ListingPageProps) {
  const { id } = await params;

  let listing: ListingResponse;
  try {
    listing = await apiClient.getListing(id);
  } catch {
    notFound();
  }

  const primaryImage = listing.images.find((img) => img.is_primary) ?? listing.images[0];
  const otherImages = listing.images.filter((img) => img.id !== primaryImage?.id);

  const locationText = listing.location
    ? [listing.location.neighborhood, listing.location.city, listing.location.state].filter(Boolean).join(", ")
    : null;

  let relatedListings: { id: string; title: string; price_amount_cents: number | null; currency: string; condition: ConditionGrade | null }[] = [];
  try {
    const related = await apiClient.searchListings({ q: listing.book.title, limit: 4 });
    relatedListings = related.items.filter((r) => r.id !== listing.id).slice(0, 4).map((r) => ({
      id: r.id, title: r.title, price_amount_cents: r.price_amount_cents ?? null,
      currency: r.currency, condition: r.condition ?? null,
    }));
  } catch { /* ignore */ }

  return (
    <div style={{ padding: "20px 0 40px" }}>
      <Container>
        <nav
          style={{
            display: "flex", alignItems: "center", gap: 6,
            fontSize: font.size.sm, color: colors.textSubtle, marginBottom: 16,
          }}
        >
          <Link href="/" style={{ color: colors.textSubtle, textDecoration: "none" }}>Home</Link>
          <span>/</span>
          <Link href="/search" style={{ color: colors.textSubtle, textDecoration: "none" }}>Listings</Link>
          <span>/</span>
          <span style={{ color: colors.text }}>{listing.title}</span>
        </nav>

        <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 32, alignItems: "flex-start" }}>
          <div>
            <BookCover
              imageUrl={primaryImage?.public_url}
              title={listing.title}
              seed={listing.id}
              aspectRatio="3/4"
            />
            {otherImages.length > 0 && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, marginTop: 12 }}>
                {otherImages.slice(0, 4).map((img) =>
                  img.public_url ? (
                    <div
                      key={img.id}
                      style={{
                        aspectRatio: "1",
                        borderRadius: radius.md,
                        overflow: "hidden",
                        border: `1px solid ${colors.border}`,
                        background: colors.surfaceMuted,
                      }}
                    >
                      <img src={img.public_url} alt={img.alt_text ?? listing.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                    </div>
                  ) : null,
                )}
              </div>
            )}
          </div>

          <div>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
              {listing.listing_modes.map((mode) => (
                <Badge key={mode} variant="info" label={MODE_LABEL[mode] ?? mode} />
              ))}
            </div>
            <h1
              style={{
                margin: "0 0 4px",
                fontSize: font.size["2xl"],
                fontWeight: font.weight.bold,
                color: colors.text,
                letterSpacing: "-0.02em",
              }}
            >
              {listing.title}
            </h1>
            <p style={{ margin: "0 0 12px", fontSize: font.size.base }}>
              <Link href={`/books/${listing.book.id}`} style={{ color: colors.primary, textDecoration: "none" }}>
                View book details
              </Link>
            </p>

            <div
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: 10,
                marginBottom: 16,
              }}
            >
              <span style={{ fontSize: font.size["3xl"], fontWeight: font.weight.heavy, color: colors.text, letterSpacing: "-0.02em" }}>
                {formatPrice(listing.price_amount_cents, listing.currency)}
              </span>
              {listing.negotiable && (
                <span style={{ fontSize: font.size.sm, color: colors.textSubtle }}>· Negotiable</span>
              )}
            </div>

            {listing.condition && (
              <div style={{ marginBottom: 12 }}>
                <Section title="Condition">
                  <ConditionDetails condition={listing.condition} />
                </Section>
              </div>
            )}

            {locationText && (
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <Icon.pin color={colors.textSubtle} />
                <span style={{ color: colors.textMuted, fontSize: font.size.base }}>{locationText}</span>
                {listing.location?.campus_pickup && <Badge variant="info" label="Campus Pickup" />}
              </div>
            )}

            {listing.delivery_methods.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <Section title="Delivery options">
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {listing.delivery_methods.map((dm) => (
                      <div key={dm.method} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: font.size.base }}>
                        <span style={{ color: colors.textMuted, fontWeight: font.weight.medium }}>
                          {dm.method === "pickup" ? "Pickup" : "Shipping"}
                        </span>
                        {dm.price_amount_cents != null && dm.price_amount_cents > 0 ? (
                          <span style={{ color: colors.textSubtle }}>— ₹{(dm.price_amount_cents / 100).toLocaleString("en-IN")}</span>
                        ) : dm.method === "shipping" ? (
                          <Badge variant="success" label="Free" />
                        ) : null}
                        {dm.notes && <span style={{ color: colors.textFaint, fontSize: font.size.sm }}>({dm.notes})</span>}
                      </div>
                    ))}
                  </div>
                </Section>
              </div>
            )}

            <ListingActions listing={listing} />
          </div>
        </div>

        {listing.description && (
          <div style={{ marginTop: 24 }}>
            <Section title="Description">
              <p style={{ margin: 0, lineHeight: font.lineHeight.relaxed, color: colors.text, fontSize: font.size.base }}>
                {listing.description}
              </p>
            </Section>
          </div>
        )}

        {listing.exchange_preferences && (
          <div style={{ marginTop: 16 }}>
            <Section title="Exchange preferences">
              <p style={{ margin: 0, lineHeight: font.lineHeight.relaxed, color: colors.textMuted }}>
                {listing.exchange_preferences}
              </p>
            </Section>
          </div>
        )}

        {listing.return_policy && (
          <div style={{ marginTop: 16 }}>
            <Section title="Return policy">
              <p style={{ margin: 0, lineHeight: font.lineHeight.relaxed, color: colors.textMuted }}>
                {listing.return_policy}
              </p>
            </Section>
          </div>
        )}

        <div style={{ marginTop: 16 }}>
          <ListingMessagesTab listingId={listing.id} sellerId={listing.seller.id} />
        </div>

        {relatedListings.length > 0 && (
          <div style={{ marginTop: 24 }}>
            <Section title="More copies of this book">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 14 }}>
                {relatedListings.map((r) => (
                  <Link
                    key={r.id}
                    href={`/listings/${r.id}`}
                    style={{
                      textDecoration: "none",
                      background: colors.surface,
                      border: `1px solid ${colors.border}`,
                      borderRadius: radius.lg,
                      padding: 14,
                      display: "flex",
                      flexDirection: "column",
                      gap: 6,
                    }}
                  >
                    <p style={{ margin: 0, fontWeight: font.weight.semibold, fontSize: font.size.base, color: colors.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {r.title}
                    </p>
                    {r.condition && <ConditionBadge condition={r.condition} />}
                    <p style={{ margin: "6px 0 0", fontSize: font.size.lg, fontWeight: font.weight.bold, color: colors.text }}>
                      {formatPrice(r.price_amount_cents, r.currency)}
                    </p>
                  </Link>
                ))}
              </div>
            </Section>
          </div>
        )}
      </Container>
    </div>
  );
}
