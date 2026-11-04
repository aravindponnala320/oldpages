import { notFound } from "next/navigation";
import Link from "next/link";
import { apiClient } from "../../../lib/api";
import type { ListingSearchResult } from "@oldpages/shared-types";
import {
  Badge,
  BookCard,
  BookCover,
  Container,
  EmptyState,
  Icon,
  LinkButton,
  Section,
  colors,
  font,
  formatPrice,
  radius,
  type BookCardData,
} from "../../../components/ui";

interface BookPageProps {
  params: Promise<{ id: string }>;
}

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

export default async function BookPage({ params }: BookPageProps) {
  const { id } = await params;

  let book;
  try {
    book = await apiClient.getBook(id);
  } catch {
    notFound();
  }

  let listings = { items: [] as ListingSearchResult[], result_count: 0 };
  try {
    const res = await apiClient.searchListings({ q: book.title, limit: 20 });
    listings = { items: res.items, result_count: res.result_count };
  } catch { /* ignore */ }

  const authorsText = book.authors.map((a) => a.name).join(", ");

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
          <Link href="/search" style={{ color: colors.textSubtle, textDecoration: "none" }}>Books</Link>
          <span>/</span>
          <span style={{ color: colors.text }}>{book.title}</span>
        </nav>

        <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 32, alignItems: "flex-start" }}>
          <div>
            <BookCover
              imageUrl={book.cover_image_url}
              title={book.title}
              seed={book.id}
              author={book.authors?.[0]?.name}
              aspectRatio="2/3"
            />
          </div>

          <div>
            <h1
              style={{
                margin: "0 0 6px",
                fontSize: font.size["3xl"],
                fontWeight: font.weight.heavy,
                color: colors.text,
                lineHeight: 1.2,
                letterSpacing: "-0.02em",
              }}
            >
              {book.title}
            </h1>
            {book.subtitle && (
              <p style={{ margin: "0 0 12px", fontSize: font.size.lg, color: colors.textSubtle }}>{book.subtitle}</p>
            )}
            {authorsText && (
              <p style={{ margin: "0 0 16px", fontSize: font.size.base, color: colors.textMuted }}>
                by <span style={{ fontWeight: font.weight.semibold }}>{authorsText}</span>
              </p>
            )}

            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
              {book.publication_year && <Badge label={String(book.publication_year)} />}
              {book.format && book.format !== "unknown" && (
                <Badge label={book.format.replace("_", " ")} />
              )}
              {book.language && book.language !== "en" && <Badge label={book.language.toUpperCase()} />}
              {book.page_count && <Badge label={`${book.page_count} pages`} />}
            </div>

            {book.genres.length > 0 && (
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 16 }}>
                {book.genres.map((g) => <Badge key={g} variant="info" label={g} />)}
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 20 }}>
              {book.publisher && <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textFaint }}>Publisher: {book.publisher.name}</p>}
              {book.isbn_13 && <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textFaint }}>ISBN-13: {book.isbn_13}</p>}
              {book.isbn_10 && !book.isbn_13 && <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textFaint }}>ISBN-10: {book.isbn_10}</p>}
            </div>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <LinkButton href={`/search?q=${encodeURIComponent(book.title)}`}>
                Find Listings ({listings.result_count})
              </LinkButton>
              <LinkButton href="/listings/create" variant="secondary">
                List Your Copy
              </LinkButton>
            </div>
          </div>
        </div>

        {book.description && (
          <div style={{ marginTop: 24 }}>
            <Section title="About this book">
              <p style={{ margin: 0, lineHeight: font.lineHeight.relaxed, color: colors.textMuted, fontSize: font.size.base }}>
                {book.description}
              </p>
            </Section>
          </div>
        )}

        {book.academic_metadata && (
          <div style={{ marginTop: 16 }}>
            <Section title="Academic info">
              <dl style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "6px 24px", margin: 0 }}>
                {book.academic_metadata.subject && (<><dt style={dt}>Subject</dt><dd style={dd}>{book.academic_metadata.subject}</dd></>)}
                {book.academic_metadata.department && (<><dt style={dt}>Department</dt><dd style={dd}>{book.academic_metadata.department}</dd></>)}
                {book.academic_metadata.university && (<><dt style={dt}>University</dt><dd style={dd}>{book.academic_metadata.university}</dd></>)}
                {book.academic_metadata.course && (<><dt style={dt}>Course</dt><dd style={dd}>{book.academic_metadata.course}</dd></>)}
              </dl>
            </Section>
          </div>
        )}

        <div style={{ marginTop: 24 }}>
          <Section
            title="Available copies"
            actions={
              listings.result_count > 0 ? (
                <span style={{ color: colors.textSubtle, fontSize: font.size.sm }}>
                  {listings.result_count} listing{listings.result_count !== 1 ? "s" : ""}
                </span>
              ) : undefined
            }
          >
            {listings.items.length === 0 ? (
              <EmptyState
                icon={<Icon.book size={26} color={colors.primary} />}
                title="No listings yet"
                description="Be the first to list a copy of this book."
                action={<LinkButton href="/listings/create">List Your Copy</LinkButton>}
              />
            ) : (
              <>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 16 }}>
                  {listings.items.map((l) => <BookCard key={l.id} book={toBookCard(l)} />)}
                </div>
                {listings.result_count > listings.items.length && (
                  <div style={{ textAlign: "center", marginTop: 20 }}>
                    <LinkButton href={`/search?q=${encodeURIComponent(book.title)}`} variant="secondary">
                      View all {listings.result_count} listings
                    </LinkButton>
                  </div>
                )}
              </>
            )}
          </Section>
        </div>
      </Container>
    </div>
  );
}

const dt: React.CSSProperties = { color: colors.textSubtle, fontSize: font.size.sm, fontWeight: font.weight.semibold };
const dd: React.CSSProperties = { margin: 0, fontSize: font.size.base, color: colors.text };
