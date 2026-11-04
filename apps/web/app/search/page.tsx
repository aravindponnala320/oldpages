import Link from "next/link";
import { cookies } from "next/headers";
import { apiClient } from "../../lib/api";
import type {
  ConditionGrade,
  ListingMode,
  ListingSearchResult,
  SearchSort,
} from "@oldpages/shared-types";
import {
  BookCard,
  Container,
  EmptyState,
  Icon,
  LinkButton,
  PageHeader,
  Section,
  colors,
  font,
  formatPrice,
  layout,
  radius,
  type BookCardData,
} from "../../components/ui";

interface SearchPageProps {
  searchParams: Promise<{
    q?: string;
    listing_mode?: string;
    min_price?: string;
    max_price?: string;
    condition?: string;
    sort?: string;
    cursor?: string;
    category?: string;
  }>;
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

const LISTING_MODES: { value: ListingMode; label: string }[] = [
  { value: "sell",     label: "For Sale" },
  { value: "exchange", label: "Exchange" },
  { value: "donate",   label: "Donate" },
  { value: "lend",     label: "Lend" },
  { value: "request",  label: "Wanted" },
  { value: "rent",     label: "Rent" },
  { value: "giveaway", label: "Giveaway" },
];

const SORT_OPTIONS: { value: SearchSort; label: string }[] = [
  { value: "relevance",      label: "Relevance" },
  { value: "newest",         label: "Newest" },
  { value: "lowest_price",   label: "Price: Low to High" },
  { value: "highest_price",  label: "Price: High to Low" },
  { value: "best_condition", label: "Best Condition" },
  { value: "most_saved",     label: "Most Saved" },
];

function toBookCard(l: ListingSearchResult): BookCardData {
  return {
    id: l.id,
    href: `/listings/${l.id}`,
    title: l.title,
    author: l.book?.authors?.[0] ?? null,
    imageUrl: l.image_url ?? null,
    priceLabel: formatPrice(l.price_amount_cents, l.currency),
    condition: l.condition ?? null,
    location: l.location?.city ?? null,
  };
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const params = await searchParams;
  const q            = params.q ?? "";
  const listingMode  = params.listing_mode as ListingMode | undefined;
  const minPrice     = params.min_price ? parseInt(params.min_price, 10) : undefined;
  const maxPrice     = params.max_price ? parseInt(params.max_price, 10) : undefined;
  const condition    = params.condition as ConditionGrade | undefined;
  const sort         = (params.sort as SearchSort) ?? "relevance";
  const cursor       = params.cursor;

  let results = { items: [] as ListingSearchResult[], next_cursor: null as string | null, result_count: 0 };
  let fetchError: string | null = null;

  const cookieStore = await cookies();
  const activeLocationCookie = cookieStore.get("op_loc")?.value;

  try {
    const response = await apiClient.searchListings(
      {
        q: q || null,
        listing_mode: listingMode ?? null,
        min_price_amount_cents: minPrice != null ? minPrice * 100 : null,
        max_price_amount_cents: maxPrice != null ? maxPrice * 100 : null,
        condition: condition ?? null,
        sort: sort ?? null,
        cursor: cursor ?? null,
        limit: 24,
      },
      undefined,
      activeLocationCookie ? { "X-User-Location": activeLocationCookie } : undefined,
    );
    results = { items: response.items, next_cursor: response.next_cursor ?? null, result_count: response.result_count };
  } catch (err) {
    fetchError = err instanceof Error ? err.message : "Failed to load results";
  }

  const buildUrl = (overrides: Record<string, string | undefined>) => {
    const p = new URLSearchParams();
    const merged: Record<string, string | undefined> = {
      q, listing_mode: listingMode, min_price: minPrice?.toString(),
      max_price: maxPrice?.toString(), condition, sort, cursor, ...overrides,
    };
    for (const [key, val] of Object.entries(merged)) if (val) p.set(key, val);
    return `/search?${p.toString()}`;
  };

  return (
    <div style={{ padding: `20px 0 40px` }}>
      <Container>
        <PageHeader
          eyebrow="Browse"
          title={q ? `Results for "${q}"` : "Browse Listings"}
          subtitle={`${results.result_count} listing${results.result_count !== 1 ? "s" : ""} found`}
        />

        <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 20, alignItems: "flex-start" }}>
          {/* Filters */}
          <aside
            style={{
              background: colors.surface,
              border: `1px solid ${colors.border}`,
              borderRadius: radius.xl,
              padding: 20,
              position: "sticky",
              top: layout.headerHeight + 12,
            }}
          >
            <form method="GET" action="/search" style={{ display: "flex", flexDirection: "column", gap: 18 }}>
              <FilterBlock title="Search">
                <input
                  type="text"
                  name="q"
                  defaultValue={q}
                  placeholder="Title, author, ISBN..."
                  style={filterInputStyle}
                />
              </FilterBlock>

              <FilterBlock title="Sort by">
                <select name="sort" defaultValue={sort} style={filterSelectStyle}>
                  {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </FilterBlock>

              <FilterBlock title="Listing type">
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  <RadioLabel name="listing_mode" value="" label="All types" defaultChecked={!listingMode} />
                  {LISTING_MODES.map((m) => (
                    <RadioLabel
                      key={m.value}
                      name="listing_mode"
                      value={m.value}
                      label={m.label}
                      defaultChecked={listingMode === m.value}
                    />
                  ))}
                </div>
              </FilterBlock>

              <FilterBlock title="Price (INR)">
                <div style={{ display: "flex", gap: 8 }}>
                  <input type="number" name="min_price" defaultValue={minPrice} placeholder="Min" min="0" style={filterInputStyle} />
                  <input type="number" name="max_price" defaultValue={maxPrice} placeholder="Max" min="0" style={filterInputStyle} />
                </div>
              </FilterBlock>

              <FilterBlock title="Condition">
                <select name="condition" defaultValue={condition ?? ""} style={filterSelectStyle}>
                  <option value="">Any condition</option>
                  {CONDITIONS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                </select>
              </FilterBlock>

              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <button type="submit" style={applyBtn}>Apply Filters</button>
                <Link href="/search" style={clearBtn}>Clear All</Link>
              </div>
            </form>
          </aside>

          {/* Results */}
          <div>
            {fetchError ? (
              <Section>
                <div style={{ padding: "24px", textAlign: "center", color: colors.dangerText }}>
                  <p style={{ margin: "0 0 6px", fontWeight: font.weight.semibold }}>Could not load results</p>
                  <p style={{ margin: 0, fontSize: font.size.sm }}>{fetchError}</p>
                </div>
              </Section>
            ) : results.items.length === 0 ? (
              <EmptyState
                icon={<Icon.search size={24} color={colors.primary} />}
                title="No listings found"
                description="Try adjusting your filters, or list a book so someone else can find it."
                action={<LinkButton href="/listings/create">List a Book</LinkButton>}
              />
            ) : (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
                  gap: 16,
                }}
              >
                {results.items.map((l) => <BookCard key={l.id} book={toBookCard(l)} />)}
              </div>
            )}

            {(cursor || results.next_cursor) && (
              <div style={{ display: "flex", justifyContent: "center", gap: 12, marginTop: 24 }}>
                {cursor && <LinkButton href={buildUrl({ cursor: undefined })} variant="secondary">← First page</LinkButton>}
                {results.next_cursor && <LinkButton href={buildUrl({ cursor: results.next_cursor })}>Load more →</LinkButton>}
              </div>
            )}
          </div>
        </div>
      </Container>
    </div>
  );
}

function FilterBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 style={{ margin: "0 0 8px", fontSize: font.size.sm, fontWeight: font.weight.bold, color: colors.textMuted, textTransform: "uppercase", letterSpacing: "0.06em" }}>
        {title}
      </h3>
      {children}
    </div>
  );
}

function RadioLabel({ name, value, label, defaultChecked }: { name: string; value: string; label: string; defaultChecked?: boolean }) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: font.size.base, color: colors.textMuted, cursor: "pointer" }}>
      <input type="radio" name={name} value={value} defaultChecked={defaultChecked} style={{ accentColor: colors.primary }} />
      {label}
    </label>
  );
}

const filterInputStyle: React.CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  height: 38,
  padding: "0 12px",
  border: `1px solid ${colors.borderStrong}`,
  borderRadius: radius.md,
  background: colors.surface,
  fontSize: font.size.base,
  color: colors.text,
  outline: "none",
};

const filterSelectStyle: React.CSSProperties = { ...filterInputStyle, appearance: "none" };

const applyBtn: React.CSSProperties = {
  height: 40,
  border: "none",
  background: colors.primary,
  color: "#fff",
  fontWeight: font.weight.semibold,
  fontSize: font.size.base,
  borderRadius: radius.lg,
  cursor: "pointer",
};

const clearBtn: React.CSSProperties = {
  height: 40,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  border: `1px solid ${colors.borderStrong}`,
  background: colors.surface,
  color: colors.textMuted,
  fontWeight: font.weight.semibold,
  fontSize: font.size.base,
  borderRadius: radius.lg,
  textDecoration: "none",
};
