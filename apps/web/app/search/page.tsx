import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { apiClient } from "../../lib/api";
import { VIEWER_COOKIE } from "../../lib/auth";
import { currencyForCountry } from "../../lib/currency";
import {
  decodeLocationCookie,
  listingPlaceLabel,
  shortLocationLabel,
  usesMiles,
} from "../../lib/geo";
import { isModeEnabled } from "../../lib/listingModes";
import type {
  ConditionGrade,
  DeliveryMethod,
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
import { SortSelect } from "./SortSelect";
import { CategoryPicker } from "../../components/CategoryPicker";
import { categoryTrail } from "../../lib/categories";

type Params = Partial<
  Record<
    | "q"
    | "sort"
    | "cursor"
    | "listing_mode"
    | "min_price"
    | "max_price"
    | "free"
    | "condition"
    | "within"
    | "category"
    | "format"
    | "language"
    | "author"
    | "publisher"
    | "year"
    | "delivery"
    | "negotiable"
    | "photos"
    | "signed"
    | "first_edition"
    | "campus"
    | "city"
    | "state"
    | "country",
    string
  >
>;

interface SearchPageProps {
  searchParams: Promise<Params>;
}

const CONDITIONS: { value: ConditionGrade; label: string }[] = [
  { value: "new_sealed", label: "New / Sealed" },
  { value: "like_new", label: "Like New" },
  { value: "excellent", label: "Excellent" },
  { value: "very_good", label: "Very Good" },
  { value: "good", label: "Good" },
  { value: "acceptable", label: "Acceptable" },
  { value: "poor", label: "Poor" },
  { value: "reference_only", label: "Reference only" },
];

const LISTING_MODES: { value: ListingMode; label: string }[] = (
  [
    { value: "sell", label: "For Sale" },
    { value: "exchange", label: "Exchange" },
    { value: "donate", label: "Free / Donate" },
    { value: "lend", label: "Lend" },
    { value: "request", label: "Wanted" },
    { value: "rent", label: "Rent" },
  ] as { value: ListingMode; label: string }[]
).filter((m) => isModeEnabled(m.value));

const SORT_OPTIONS: { value: SearchSort; label: string }[] = [
  { value: "relevance", label: "Best match" },
  { value: "nearest", label: "Nearest first" },
  { value: "newest", label: "Newest first" },
  { value: "lowest_price", label: "Price: low to high" },
  { value: "highest_price", label: "Price: high to low" },
  { value: "best_condition", label: "Best condition" },
  { value: "most_saved", label: "Most saved" },
];

const FORMATS = [
  { value: "paperback", label: "Paperback" },
  { value: "hardcover", label: "Hardcover" },
  { value: "spiral_bound", label: "Spiral bound" },
  { value: "loose_leaf", label: "Loose leaf" },
  { value: "ebook", label: "eBook" },
  { value: "audiobook", label: "Audiobook" },
];

const LANGUAGES = [
  ["en", "English"],
  ["hi", "Hindi"],
  ["te", "Telugu"],
  ["ta", "Tamil"],
  ["kn", "Kannada"],
  ["ml", "Malayalam"],
  ["mr", "Marathi"],
  ["bn", "Bengali"],
  ["gu", "Gujarati"],
  ["pa", "Punjabi"],
  ["or", "Odia"],
  ["ur", "Urdu"],
  ["sa", "Sanskrit"],
  ["es", "Spanish"],
  ["fr", "French"],
  ["de", "German"],
  ["ar", "Arabic"],
  ["zh", "Chinese"],
  ["ja", "Japanese"],
] as const;

const DELIVERY: { value: DeliveryMethod; label: string }[] = [
  { value: "pickup", label: "Pickup / meet up" },
  { value: "shipping", label: "Shipping" },
];

// Radius choices, in the reader's own unit (km or mi).
const WITHIN = [5, 10, 25, 50, 100, 200];
const KM_PER_MILE = 1.609344;

// Yes/no filters: URL key, API key, label.
const TOGGLES = [
  ["negotiable", "negotiable", "Price negotiable"],
  ["photos", "actual_photos", "Has real photos"],
  ["signed", "signed_copy", "Signed copy"],
  ["first_edition", "first_edition", "First edition"],
  ["campus", "campus_pickup", "Campus pickup"],
] as const;

function toBookCard(
  l: ListingSearchResult,
  readerCountry?: string | null,
): BookCardData {
  return {
    id: l.id,
    href: `/listings/${l.id}`,
    title: l.title,
    author: l.book?.authors?.[0] ?? null,
    imageUrl: l.image_url ?? null,
    priceLabel: formatPrice(l.price_amount_cents, l.currency),
    condition: l.condition ?? null,
    location: listingPlaceLabel(l, readerCountry),
  };
}

const num = (v: string | undefined) => {
  const n = v ? Number(v) : NaN;
  return Number.isFinite(n) && n >= 0 ? n : undefined;
};

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const params = await searchParams;
  // The filter form submits every field; drop the empty ones so URLs stay short and shareable.
  if (Object.values(params).some((v) => v === "")) {
    const clean = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v) as [string, string][],
    ).toString();
    redirect(clean ? `/search?${clean}` : "/search");
  }
  const q = params.q?.trim() ?? "";
  const listingMode = LISTING_MODES.some((m) => m.value === params.listing_mode)
    ? (params.listing_mode as ListingMode)
    : undefined;
  const condition = CONDITIONS.some((c) => c.value === params.condition)
    ? (params.condition as ConditionGrade)
    : undefined;
  const delivery = DELIVERY.some((d) => d.value === params.delivery)
    ? (params.delivery as DeliveryMethod)
    : undefined;
  const minPrice = num(params.min_price);
  const maxPrice = num(params.max_price);
  const freeOnly = params.free === "1";
  const within = WITHIN.includes(Number(params.within))
    ? Number(params.within)
    : undefined;
  const year = num(params.year);

  const cookieStore = await cookies();
  const activeLocation = decodeLocationCookie(cookieStore.get("op_loc")?.value);
  const viewerId = cookieStore.get(VIEWER_COOKIE)?.value;
  const unit = usesMiles(activeLocation?.country_code) ? "mi" : "km";
  // Price filters are in the currency where the reader is browsing.
  const currency = currencyForCountry(activeLocation?.country_code);
  const priceFiltered = minPrice != null || maxPrice != null;

  // "Nearest" needs an origin; without a location fall back to best match.
  const requestedSort = SORT_OPTIONS.some((o) => o.value === params.sort)
    ? (params.sort as SearchSort)
    : "relevance";
  const sort: SearchSort =
    requestedSort === "nearest" && !activeLocation
      ? "relevance"
      : requestedSort;
  const sortOptions = SORT_OPTIONS.filter(
    (o) => o.value !== "nearest" || activeLocation,
  );

  const [searchResult, categoryPath] = await Promise.all([
    apiClient
      .searchListings({
        q: q || null,
        listing_mode: listingMode ?? null,
        min_price_amount_cents:
          minPrice != null ? Math.round(minPrice * 100) : null,
        max_price_amount_cents:
          maxPrice != null ? Math.round(maxPrice * 100) : null,
        currency: priceFiltered ? currency : null,
        free_only: freeOnly || null,
        condition: condition ?? null,
        category: params.category || null,
        format: FORMATS.some((f) => f.value === params.format)
          ? params.format
          : null,
        language: params.language || null,
        author: params.author || null,
        publisher: params.publisher || null,
        publication_year:
          year != null && year >= 1450 && year <= 2200
            ? Math.round(year)
            : null,
        delivery_method: delivery ?? null,
        city: params.city || null,
        state: params.state || null,
        country: params.country || null,
        ...Object.fromEntries(
          TOGGLES.filter(([key]) => params[key] === "1").map(([, api]) => [
            api,
            true,
          ]),
        ),
        // Books from anywhere by default; the reader's location only adds distances (and the radius, if picked).
        latitude: activeLocation?.latitude ?? null,
        longitude: activeLocation?.longitude ?? null,
        distance_km:
          activeLocation && within
            ? Math.min(500, unit === "mi" ? within * KM_PER_MILE : within)
            : null,
        exclude_seller_id: viewerId || null,
        sort,
        cursor: params.cursor || null,
        limit: 24,
      })
      .then((r) => ({ ok: true as const, ...r }))
      .catch((err: unknown) => ({
        ok: false as const,
        error: err instanceof Error ? err.message : "Failed to load results",
      })),
    params.category
      ? apiClient
          .getCategoryLevels(params.category)
          .then((r) => r.path)
          .catch(() => [])
      : Promise.resolve([]),
  ]);

  const items = searchResult.ok ? searchResult.items : [];
  const resultCount = searchResult.ok ? searchResult.result_count : 0;
  const nextCursor = searchResult.ok
    ? (searchResult.next_cursor ?? null)
    : null;

  const buildUrl = (overrides: Params) => {
    const p = new URLSearchParams();
    for (const [key, val] of Object.entries({ ...params, ...overrides }))
      if (val) p.set(key, val);
    const s = p.toString();
    return s ? `/search?${s}` : "/search";
  };

  // Chips for every active filter; each one links to the same search without it.
  const chips: { label: string; href: string }[] = [];
  const chip = (label: string, ...keys: (keyof Params)[]) =>
    chips.push({
      label,
      href: buildUrl(
        Object.fromEntries(
          keys.map((k) => [k, undefined]).concat([["cursor", undefined]]),
        ),
      ),
    });
  if (q) chip(`“${q}”`, "q");
  if (listingMode)
    chip(
      LISTING_MODES.find((m) => m.value === listingMode)!.label,
      "listing_mode",
    );
  if (freeOnly) chip("Free only", "free");
  if (priceFiltered)
    chip(
      `${minPrice ?? 0} – ${maxPrice ?? "any"} ${currency}`,
      "min_price",
      "max_price",
    );
  if (condition)
    chip(CONDITIONS.find((c) => c.value === condition)!.label, "condition");
  if (within && activeLocation) chip(`Within ${within} ${unit}`, "within");
  if (params.category)
    chip(categoryTrail(categoryPath) || params.category, "category");
  if (params.format)
    chip(
      FORMATS.find((f) => f.value === params.format)?.label ?? params.format,
      "format",
    );
  if (params.language)
    chip(
      LANGUAGES.find(([c]) => c === params.language)?.[1] ?? params.language,
      "language",
    );
  if (params.author) chip(`Author: ${params.author}`, "author");
  if (params.publisher) chip(`Publisher: ${params.publisher}`, "publisher");
  if (params.year) chip(`Year ${params.year}`, "year");
  if (delivery)
    chip(DELIVERY.find((d) => d.value === delivery)!.label, "delivery");
  for (const [key, , label] of TOGGLES)
    if (params[key] === "1") chip(label, key);
  if (params.city) chip(`City: ${params.city}`, "city");
  if (params.state) chip(`State: ${params.state}`, "state");
  if (params.country) chip(`Country: ${params.country}`, "country");
  const filterCount = chips.length - (q ? 1 : 0);

  const bookOpen = !!(
    params.format ||
    params.language ||
    params.author ||
    params.publisher ||
    params.year
  );
  const placeOpen = !!(
    within ||
    params.city ||
    params.state ||
    params.country ||
    delivery
  );
  const extrasOpen = TOGGLES.some(([key]) => params[key] === "1");

  const scope = activeLocation
    ? within
      ? `within ${within} ${unit} of ${shortLocationLabel(activeLocation)}`
      : `from everywhere · distances from ${shortLocationLabel(activeLocation)}`
    : "from everywhere";

  return (
    <div style={{ padding: `20px 0 40px` }}>
      <Container>
        <PageHeader
          eyebrow="Browse"
          title={q ? `Results for “${q}”` : "All books"}
          subtitle={`${resultCount} book${resultCount !== 1 ? "s" : ""} ${scope}${viewerId ? " · not showing your own" : ""}`}
        />

        <div
          className="op-split"
          style={
            {
              "--op-side": "clamp(230px, 24vw, 290px)",
              "--op-split-gap": "20px",
            } as React.CSSProperties
          }
        >
          {/* Filters */}
          <aside
            className="op-split-sticky op-filters"
            style={
              {
                background: colors.surface,
                border: `1px solid ${colors.border}`,
                borderRadius: radius.xl,
                padding: "clamp(14px, 2vw, 20px)",
                position: "sticky",
                top: layout.headerHeight + 12,
                "--op-filters-top": `${layout.headerHeight + 12}px`,
              } as React.CSSProperties
            }
          >
            {/* Collapsed behind a toggle on small screens; CSS-only so it works without JS. */}
            <input
              type="checkbox"
              id="op-filters-toggle"
              className="op-filters-toggle"
            />
            <label htmlFor="op-filters-toggle" className="op-filters-label">
              Filters{filterCount > 0 ? ` (${filterCount})` : ""}
              <span aria-hidden>▾</span>
            </label>
            <form
              method="GET"
              action="/search"
              style={{ display: "flex", flexDirection: "column", gap: 16 }}
            >
              <input
                type="hidden"
                name="sort"
                value={sort === "relevance" ? "" : sort}
              />

              <FilterBlock title="Search">
                <input
                  type="search"
                  name="q"
                  defaultValue={q}
                  placeholder="Title, author, ISBN..."
                  style={filterInputStyle}
                />
              </FilterBlock>

              <FilterBlock title="Category">
                <CategoryPicker
                  key={params.category ?? ""}
                  mode="filter"
                  name="category"
                  value={params.category ?? null}
                />
              </FilterBlock>

              <FilterBlock title="Listing type">
                <div
                  style={{ display: "flex", flexDirection: "column", gap: 8 }}
                >
                  <RadioLabel
                    name="listing_mode"
                    value=""
                    label="All types"
                    defaultChecked={!listingMode}
                  />
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

              <FilterBlock title={`Price (${currency})`}>
                <div style={{ display: "flex", gap: 8 }}>
                  <input
                    type="number"
                    name="min_price"
                    defaultValue={minPrice}
                    placeholder="Min"
                    min="0"
                    inputMode="decimal"
                    aria-label="Minimum price"
                    style={filterInputStyle}
                  />
                  <input
                    type="number"
                    name="max_price"
                    defaultValue={maxPrice}
                    placeholder="Max"
                    min="0"
                    inputMode="decimal"
                    aria-label="Maximum price"
                    style={filterInputStyle}
                  />
                </div>
                <div style={{ marginTop: 8 }}>
                  <CheckLabel
                    name="free"
                    label="Free books only"
                    defaultChecked={freeOnly}
                  />
                </div>
              </FilterBlock>

              <FilterBlock title="Condition">
                <select
                  name="condition"
                  defaultValue={condition ?? ""}
                  style={filterSelectStyle}
                >
                  <option value="">Any condition</option>
                  {CONDITIONS.map((c) => (
                    <option key={c.value} value={c.value}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </FilterBlock>

              <FilterGroup title="Distance & place" open={placeOpen}>
                <Field label="Distance">
                  <select
                    name="within"
                    defaultValue={within ?? ""}
                    disabled={!activeLocation}
                    style={filterSelectStyle}
                  >
                    <option value="">Anywhere</option>
                    {WITHIN.map((w) => (
                      <option key={w} value={w}>
                        Within {w} {unit}
                      </option>
                    ))}
                  </select>
                  {!activeLocation && (
                    <p style={hintStyle}>
                      Set your location at the top to filter by distance.
                    </p>
                  )}
                </Field>
                <Field label="Delivery">
                  <select
                    name="delivery"
                    defaultValue={delivery ?? ""}
                    style={filterSelectStyle}
                  >
                    <option value="">Any</option>
                    {DELIVERY.map((d) => (
                      <option key={d.value} value={d.value}>
                        {d.label}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="City">
                  <input
                    name="city"
                    defaultValue={params.city}
                    placeholder="e.g. Hyderabad"
                    style={filterInputStyle}
                  />
                </Field>
                <Field label="State">
                  <input
                    name="state"
                    defaultValue={params.state}
                    placeholder="e.g. Telangana"
                    style={filterInputStyle}
                  />
                </Field>
                <Field label="Country">
                  <input
                    name="country"
                    defaultValue={params.country}
                    placeholder="e.g. IN"
                    style={filterInputStyle}
                  />
                </Field>
              </FilterGroup>

              <FilterGroup title="Book details" open={bookOpen}>
                <Field label="Format">
                  <select
                    name="format"
                    defaultValue={params.format ?? ""}
                    style={filterSelectStyle}
                  >
                    <option value="">Any format</option>
                    {FORMATS.map((f) => (
                      <option key={f.value} value={f.value}>
                        {f.label}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Language">
                  <select
                    name="language"
                    defaultValue={params.language ?? ""}
                    style={filterSelectStyle}
                  >
                    <option value="">Any language</option>
                    {LANGUAGES.map(([code, name]) => (
                      <option key={code} value={code}>
                        {name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Author">
                  <input
                    name="author"
                    defaultValue={params.author}
                    placeholder="e.g. Premchand"
                    style={filterInputStyle}
                  />
                </Field>
                <Field label="Publisher">
                  <input
                    name="publisher"
                    defaultValue={params.publisher}
                    placeholder="e.g. Penguin"
                    style={filterInputStyle}
                  />
                </Field>
                <Field label="Published in">
                  <input
                    type="number"
                    name="year"
                    defaultValue={params.year}
                    placeholder="Year, e.g. 2019"
                    min="1450"
                    max="2200"
                    inputMode="numeric"
                    style={filterInputStyle}
                  />
                </Field>
              </FilterGroup>

              <FilterGroup title="More options" open={extrasOpen}>
                <div
                  style={{ display: "flex", flexDirection: "column", gap: 8 }}
                >
                  {TOGGLES.map(([key, , label]) => (
                    <CheckLabel
                      key={key}
                      name={key}
                      label={label}
                      defaultChecked={params[key] === "1"}
                    />
                  ))}
                </div>
              </FilterGroup>

              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <button type="submit" style={applyBtn}>
                  Show results
                </button>
                <Link href="/search" style={clearBtn}>
                  Clear all
                </Link>
              </div>
            </form>
          </aside>

          {/* Results */}
          <div style={{ minWidth: 0 }}>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 10,
                marginBottom: 14,
              }}
            >
              <span style={{ fontSize: font.size.sm, color: colors.textMuted }}>
                {resultCount} result{resultCount !== 1 ? "s" : ""}
              </span>
              <SortSelect value={sort} options={sortOptions} />
            </div>

            {chips.length > 0 && (
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 8,
                  marginBottom: 16,
                }}
              >
                {chips.map((c) => (
                  <Link
                    key={c.label}
                    href={c.href}
                    aria-label={`Remove filter ${c.label}`}
                    style={chipStyle}
                  >
                    <span
                      style={{
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {c.label}
                    </span>
                    <span aria-hidden style={{ fontWeight: font.weight.bold }}>
                      ×
                    </span>
                  </Link>
                ))}
                {chips.length > 1 && (
                  <Link
                    href="/search"
                    style={{
                      ...chipStyle,
                      background: "transparent",
                      borderColor: "transparent",
                      color: colors.primary,
                    }}
                  >
                    Clear all
                  </Link>
                )}
              </div>
            )}

            {!searchResult.ok ? (
              <Section>
                <div
                  style={{
                    padding: "24px",
                    textAlign: "center",
                    color: colors.dangerText,
                  }}
                >
                  <p
                    style={{
                      margin: "0 0 6px",
                      fontWeight: font.weight.semibold,
                    }}
                  >
                    Could not load results
                  </p>
                  <p style={{ margin: 0, fontSize: font.size.sm }}>
                    {searchResult.error}
                  </p>
                </div>
              </Section>
            ) : items.length === 0 ? (
              <EmptyState
                icon={<Icon.search size={24} color={colors.primary} />}
                title="No books found"
                description={
                  chips.length
                    ? "Try removing a filter or two."
                    : "No one has listed a book yet. Be the first!"
                }
                action={
                  chips.length ? (
                    <LinkButton href="/search" variant="secondary">
                      Clear all filters
                    </LinkButton>
                  ) : (
                    <LinkButton href="/listings/create">List a Book</LinkButton>
                  )
                }
              />
            ) : (
              <div className="op-results-grid">
                {items.map((l) => (
                  <BookCard
                    key={l.id}
                    book={toBookCard(l, activeLocation?.country_code)}
                  />
                ))}
              </div>
            )}

            {(params.cursor || nextCursor) && (
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  justifyContent: "center",
                  gap: 12,
                  marginTop: 24,
                }}
              >
                {params.cursor && (
                  <LinkButton
                    href={buildUrl({ cursor: undefined })}
                    variant="secondary"
                  >
                    ← First page
                  </LinkButton>
                )}
                {nextCursor && (
                  <LinkButton href={buildUrl({ cursor: nextCursor })}>
                    Next page →
                  </LinkButton>
                )}
              </div>
            )}
          </div>
        </div>
      </Container>
    </div>
  );
}

function FilterBlock({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h3 style={blockTitleStyle}>{title}</h3>
      {children}
    </div>
  );
}

/** A collapsible group of less-used filters; starts open when one of them is in use. */
function FilterGroup({
  title,
  open,
  children,
}: {
  title: string;
  open: boolean;
  children: React.ReactNode;
}) {
  return (
    <details open={open} className="op-filter-group">
      <summary
        style={{
          ...blockTitleStyle,
          margin: 0,
          cursor: "pointer",
          listStyle: "none",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          minHeight: 32,
        }}
      >
        {title}
        <span aria-hidden className="op-filter-group-caret">
          ▾
        </span>
      </summary>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 12,
          paddingTop: 10,
        }}
      >
        {children}
      </div>
    </details>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 6,
        fontSize: font.size.sm,
        color: colors.textMuted,
      }}
    >
      {label}
      {children}
    </label>
  );
}

function RadioLabel({
  name,
  value,
  label,
  defaultChecked,
}: {
  name: string;
  value: string;
  label: string;
  defaultChecked?: boolean;
}) {
  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        minHeight: 28,
        fontSize: font.size.base,
        color: colors.textMuted,
        cursor: "pointer",
      }}
    >
      <input
        type="radio"
        name={name}
        value={value}
        defaultChecked={defaultChecked}
        style={{ accentColor: colors.primary, width: 16, height: 16 }}
      />
      {label}
    </label>
  );
}

function CheckLabel({
  name,
  label,
  defaultChecked,
}: {
  name: string;
  label: string;
  defaultChecked?: boolean;
}) {
  return (
    <label
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        minHeight: 28,
        fontSize: font.size.base,
        color: colors.textMuted,
        cursor: "pointer",
      }}
    >
      <input
        type="checkbox"
        name={name}
        value="1"
        defaultChecked={defaultChecked}
        style={{ accentColor: colors.primary, width: 16, height: 16 }}
      />
      {label}
    </label>
  );
}

const blockTitleStyle: React.CSSProperties = {
  margin: "0 0 8px",
  fontSize: font.size.sm,
  fontWeight: font.weight.bold,
  color: colors.textMuted,
  textTransform: "uppercase",
  letterSpacing: "0.06em",
};

const hintStyle: React.CSSProperties = {
  margin: "2px 0 0",
  fontSize: font.size.xs,
  color: colors.textSubtle,
};

const filterInputStyle: React.CSSProperties = {
  width: "100%",
  minWidth: 0,
  boxSizing: "border-box",
  height: 40,
  padding: "0 12px",
  border: `1px solid ${colors.borderStrong}`,
  borderRadius: radius.md,
  background: colors.surface,
  // 16px keeps iOS Safari from zooming into the field on focus.
  fontSize: 16,
  color: colors.text,
  outline: "none",
};

const filterSelectStyle: React.CSSProperties = { ...filterInputStyle };

const chipStyle: React.CSSProperties = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  maxWidth: "100%",
  minHeight: 32,
  padding: "4px 12px",
  borderRadius: 999,
  border: `1px solid ${colors.border}`,
  background: colors.surface,
  color: colors.text,
  fontSize: font.size.sm,
  textDecoration: "none",
};

const applyBtn: React.CSSProperties = {
  height: 44,
  border: "none",
  background: colors.primary,
  color: "#fff",
  fontWeight: font.weight.semibold,
  fontSize: font.size.base,
  borderRadius: radius.lg,
  cursor: "pointer",
};

const clearBtn: React.CSSProperties = {
  height: 44,
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
