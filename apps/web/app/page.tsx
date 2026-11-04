import Link from "next/link";
import { cookies } from "next/headers";
import { apiClient } from "../lib/api";
import type { ListingSearchResult } from "@oldpages/shared-types";
import {
  BookCard,
  CategoryTile,
  Container,
  EmptyState,
  Icon,
  Section,
  colors,
  font,
  formatPrice,
  layout,
  radius,
  type BookCardData,
} from "../components/ui";

/* ─────────── static category configuration (mirrors demo image) ─────────── */

const CATEGORIES: Array<{ name: string; slug: string; color: string; icon: React.ReactNode }> = [
  {
    name: "School", slug: "school", color: colors.catPink,
    icon: (
      <svg width="34" height="34" viewBox="0 0 48 48" fill="none">
        <path d="M8 40V22l16-10 16 10v18" stroke="#c026d3" strokeWidth="2.5" strokeLinejoin="round" />
        <path d="M18 40V28h12v12" stroke="#c026d3" strokeWidth="2.5" strokeLinejoin="round" />
        <path d="M24 4v6M20 6h8" stroke="#c026d3" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    name: "College", slug: "college", color: colors.catBlue,
    icon: (
      <svg width="34" height="34" viewBox="0 0 48 48" fill="none">
        <path d="M4 18l20-9 20 9-20 9L4 18z" stroke="#2563eb" strokeWidth="2.5" strokeLinejoin="round" fill="#2563eb" fillOpacity="0.15" />
        <path d="M12 22v10c0 3 5.5 6 12 6s12-3 12-6V22M42 18v10" stroke="#2563eb" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    name: "Competitive", slug: "competitive", color: colors.catGreen,
    icon: (
      <svg width="34" height="34" viewBox="0 0 48 48" fill="none">
        <path d="M14 6h20v10a10 10 0 01-20 0V6z" stroke="#16a34a" strokeWidth="2.5" strokeLinejoin="round" />
        <path d="M14 10H8v4a6 6 0 006 6M34 10h6v4a6 6 0 01-6 6" stroke="#16a34a" strokeWidth="2.5" strokeLinejoin="round" />
        <path d="M20 28h8v6h-8zM14 40h20" stroke="#16a34a" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    name: "Fiction", slug: "fiction", color: colors.catOrange,
    icon: (
      <svg width="34" height="34" viewBox="0 0 48 48" fill="none">
        <path d="M4 10h16a4 4 0 014 4v24a4 4 0 00-4-4H4V10z" stroke="#ea580c" strokeWidth="2.5" strokeLinejoin="round" />
        <path d="M44 10H28a4 4 0 00-4 4v24a4 4 0 014-4h16V10z" stroke="#ea580c" strokeWidth="2.5" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    name: "Non Fiction", slug: "non-fiction", color: colors.catPurple,
    icon: (
      <svg width="34" height="34" viewBox="0 0 48 48" fill="none">
        <path d="M10 6h24a4 4 0 014 4v32a2 2 0 01-2 2H14a4 4 0 01-4-4V6z" stroke="#7c3aed" strokeWidth="2.5" strokeLinejoin="round" />
        <path d="M14 38h24" stroke="#7c3aed" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    name: "Others", slug: "others", color: colors.catYellow,
    icon: (
      <svg width="34" height="34" viewBox="0 0 48 48" fill="none">
        <circle cx="14" cy="14" r="5" stroke="#f59e0b" strokeWidth="2.5" />
        <circle cx="34" cy="14" r="5" stroke="#f59e0b" strokeWidth="2.5" />
        <circle cx="14" cy="34" r="5" stroke="#f59e0b" strokeWidth="2.5" />
        <circle cx="34" cy="34" r="5" stroke="#f59e0b" strokeWidth="2.5" />
      </svg>
    ),
  },
];

/* ─────────── data mapping ─────────── */

function toBookCard(l: ListingSearchResult): BookCardData {
  return {
    id: l.id,
    href: `/listings/${l.id}`,
    title: l.title,
    author: l.book?.authors?.[0] ?? null,
    imageUrl: l.image_url ?? null,
    priceLabel: formatPrice(l.price_amount_cents, l.currency),
    condition: l.condition ?? null,
    location:
      l.distance_km != null
        ? `${l.distance_km.toFixed(1)} km`
        : l.location?.city ?? null,
  };
}

// Using `cookies()` makes this route dynamic, so location changes are picked
// up immediately without a 60s revalidate lag.
export default async function HomePage() {
  const cookieStore = await cookies();
  const activeLocationCookie = cookieStore.get("op_loc")?.value;
  const activeLocation = decodeLocationCookie(activeLocationCookie);

  let listings: ListingSearchResult[] = [];
  try {
    const res = await apiClient.searchListings(
      { sort: "newest", limit: 8 },
      undefined,
      activeLocationCookie ? { "X-User-Location": activeLocationCookie } : undefined,
    );
    listings = res.items;
  } catch {
    listings = [];
  }

  const locationLabel = formatLocationLabel(activeLocation);

  return (
    <>
      {/* Categories */}
      <section style={{ background: colors.surface, borderBottom: `1px solid ${colors.border}` }}>
        <Container>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(6, 1fr)",
              gap: 16,
              padding: "24px 0",
            }}
          >
            {CATEGORIES.map((cat) => (
              <CategoryTile
                key={cat.slug}
                name={cat.name}
                href={`/search?category=${cat.slug}`}
                color={cat.color}
                icon={cat.icon}
              />
            ))}
          </div>
        </Container>
      </section>

      {/* Nearby Books */}
      <div style={{ marginTop: 8 }}>
        <Container>
          <section
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: radius.xl,
              padding: "20px 24px 28px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 18 }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                  <Icon.pin color={colors.text} />
                  <h2 style={{ margin: 0, fontSize: font.size.xl, fontWeight: font.weight.bold, color: colors.text }}>
                    Nearby Books
                  </h2>
                </div>
                <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textSubtle }}>
                  {locationLabel
                    ? `Showing books near ${locationLabel}`
                    : "Set your location above to see nearby books"}
                </p>
              </div>
              <Link href="/search" style={{ fontSize: font.size.base, fontWeight: font.weight.medium, color: colors.primary, textDecoration: "none" }}>
                View all
              </Link>
            </div>

            {listings.length === 0 ? (
              <EmptyState
                icon={<Icon.book size={28} color={colors.primary} />}
                title="No books nearby yet"
                description="Be the first to list a book in your area, or expand your search to include a wider radius."
                action={
                  <Link
                    href="/listings/create"
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: colors.primary,
                      color: "#fff",
                      textDecoration: "none",
                      padding: "10px 18px",
                      borderRadius: radius.lg,
                      fontWeight: font.weight.semibold,
                      fontSize: font.size.base,
                    }}
                  >
                    List a Book
                  </Link>
                }
              />
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))",
                  gap: 14,
                }}
              >
                {listings.map((l) => (
                  <BookCard key={l.id} book={toBookCard(l)} />
                ))}
              </div>
            )}
          </section>
        </Container>
      </div>

      {/* Feature cards */}
      <div style={{ marginTop: 20 }}>
        <Container>
          <Section padded>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16 }}>
              <FeatureCard
                bg={colors.featPurple}
                title="Sell Your Books"
                body="Earn from books you no longer need"
                accent="#7c3aed"
                cta={{ label: "Sell Now", href: "/listings/create" }}
                illustration={
                  <div style={{ position: "relative", width: 60, height: 60 }}>
                    <div style={{ position: "absolute", bottom: 0, right: 0, width: 56, height: 12, background: "#a78bfa", borderRadius: 2, transform: "rotate(-6deg)" }} />
                    <div style={{ position: "absolute", bottom: 12, right: 4, width: 50, height: 12, background: "#f472b6", borderRadius: 2, transform: "rotate(4deg)" }} />
                    <div style={{ position: "absolute", bottom: 24, right: 0, width: 54, height: 12, background: "#c084fc", borderRadius: 2, transform: "rotate(-3deg)" }} />
                    <div style={{ position: "absolute", bottom: 36, right: 8, width: 44, height: 12, background: "#ec4899", borderRadius: 2, transform: "rotate(6deg)" }} />
                  </div>
                }
              />
              <FeatureCard
                bg={colors.featBlue}
                title="College Communities"
                body="Connect with students from your college"
                accent={colors.text}
                illustration={
                  <svg width="56" height="56" viewBox="0 0 48 48" fill="none">
                    <path d="M4 20l20-9 20 9-20 9L4 20z" fill="#1e3a8a" />
                    <path d="M12 24v6c0 2.5 5 5 12 5s12-2.5 12-5v-6" stroke="#1e3a8a" strokeWidth="2.5" fill="#3b82f6" />
                    <path d="M42 20v9" stroke="#1e3a8a" strokeWidth="2.5" strokeLinecap="round" />
                    <circle cx="42" cy="31" r="2" fill="#fbbf24" />
                  </svg>
                }
              />
              <FeatureCard
                bg={colors.featGreen}
                title="Safe & Trusted"
                body="Verified users & secure transactions"
                accent={colors.successText}
                illustration={
                  <svg width="56" height="56" viewBox="0 0 48 48" fill="none">
                    <path d="M24 4l16 6v14c0 10-7 16-16 20-9-4-16-10-16-20V10l16-6z" fill="#16a34a" stroke="#15803d" strokeWidth="1.5" strokeLinejoin="round" />
                    <path d="M15 24l6 6 12-12" stroke="#fff" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                }
              />
              <FeatureCard
                bg={colors.featPink}
                title="Great Prices"
                body="Best deals on used books"
                accent="#be123c"
                illustration={
                  <svg width="60" height="60" viewBox="0 0 48 48" fill="none">
                    <path d="M6 6h20l16 16-20 20L6 26V6z" fill="#f472b6" stroke="#db2777" strokeWidth="1.5" strokeLinejoin="round" />
                    <circle cx="15" cy="15" r="3.5" fill="#fff" stroke="#db2777" strokeWidth="1.5" />
                  </svg>
                }
              />
            </div>
          </Section>
        </Container>
      </div>

      <div style={{ height: layout.gutter }} />
    </>
  );
}

type DecodedLocation = {
  city?: string | null;
  state?: string | null;
  country?: string | null;
  country_code?: string | null;
};

function decodeLocationCookie(raw: string | undefined): DecodedLocation | null {
  if (!raw) return null;
  try {
    const padded = raw + "=".repeat((4 - (raw.length % 4)) % 4);
    const normalized = padded.replace(/-/g, "+").replace(/_/g, "/");
    const json = Buffer.from(normalized, "base64").toString("utf-8");
    return JSON.parse(json) as DecodedLocation;
  } catch {
    return null;
  }
}

function formatLocationLabel(loc: DecodedLocation | null): string | null {
  if (!loc) return null;
  if (loc.city && loc.state) return `${loc.city}, ${loc.state}`;
  if (loc.city && loc.country_code) return `${loc.city}, ${loc.country_code}`;
  if (loc.city) return loc.city;
  return null;
}

function FeatureCard({
  bg,
  title,
  body,
  accent,
  illustration,
  cta,
}: {
  bg: string;
  title: string;
  body: string;
  accent: string;
  illustration: React.ReactNode;
  cta?: { label: string; href: string };
}) {
  return (
    <div style={{ background: bg, borderRadius: radius.lg, padding: 18, position: "relative", overflow: "hidden", minHeight: 130 }}>
      <h3 style={{ margin: 0, fontSize: font.size.md, fontWeight: font.weight.bold, color: accent }}>{title}</h3>
      <p style={{ margin: "4px 0 10px", fontSize: font.size.sm, color: colors.textSubtle, maxWidth: "70%" }}>
        {body}
      </p>
      {cta && (
        <Link
          href={cta.href}
          style={{
            display: "inline-block",
            background: accent,
            color: "#fff",
            textDecoration: "none",
            padding: "7px 14px",
            borderRadius: 6,
            fontSize: font.size.sm,
            fontWeight: font.weight.semibold,
          }}
        >
          {cta.label}
        </Link>
      )}
      <div style={{ position: "absolute", right: 14, bottom: 14 }}>{illustration}</div>
    </div>
  );
}
