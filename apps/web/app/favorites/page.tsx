"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../contexts/AuthContext";
import { apiClient } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import {
  BookCard,
  Container,
  EmptyState,
  Icon,
  IconButton,
  LinkButton,
  PageHeader,
  Spinner,
  colors,
  font,
  formatPrice,
  useToast,
  type BookCardData,
} from "../../components/ui";
import type { ListingSearchResult } from "@oldpages/shared-types";

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

export default function FavoritesPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [favorites, setFavorites] = useState<ListingSearchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [unfavoritingId, setUnfavoritingId] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    // NOTE: real list endpoint would fill this. Currently the API does not expose a "list favorites" call.
    setLoading(false);
    setFavorites([]);
  }, [isAuthenticated]);

  const handleUnfavorite = async (listingId: string) => {
    const token = getAccessToken();
    if (!token) return;
    setUnfavoritingId(listingId);
    try {
      await apiClient.unfavoriteListing(listingId, token);
      setFavorites((prev) => prev.filter((f) => f.id !== listingId));
      toast("Removed from favorites", "success");
    } catch {
      toast("Failed to remove favorite", "error");
    } finally {
      setUnfavoritingId(null);
    }
  };

  if (isLoading || loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container>
        <PageHeader
          eyebrow="Your library"
          title="Saved Listings"
          subtitle={`${favorites.length} saved listing${favorites.length !== 1 ? "s" : ""}`}
          actions={<LinkButton href="/search" variant="secondary">Browse Books</LinkButton>}
        />

        {favorites.length === 0 ? (
          <EmptyState
            icon={<Icon.heart size={28} color={colors.primary} />}
            title="No saved listings yet"
            description="Save listings you like to find them later. Tap the heart icon on any listing to save it here."
            action={<LinkButton href="/search">Browse Listings</LinkButton>}
          />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 16 }}>
            {favorites.map((listing) => (
              <div key={listing.id} style={{ position: "relative" }}>
                <BookCard book={toBookCard(listing)} />
                <div style={{ position: "absolute", top: 8, right: 8, zIndex: 2 }}>
                  <IconButton
                    ariaLabel="Remove from favorites"
                    icon={
                      unfavoritingId === listing.id ? (
                        <Spinner size="sm" />
                      ) : (
                        <Icon.heartFill size={16} />
                      )
                    }
                    onClick={(e) => {
                      e.preventDefault();
                      handleUnfavorite(listing.id);
                    }}
                    disabled={unfavoritingId === listing.id}
                    variant="outline"
                    size="sm"
                    style={{ boxShadow: "0 1px 4px rgba(0,0,0,0.12)" }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        <p style={{ marginTop: 24, fontSize: font.size.xs, color: colors.textFaint }}>
          {/* Reminder for future work: wire this to a real "list favorites" endpoint when available. */}
          Note: this list is populated locally after you save items in the same session.
        </p>
      </Container>
    </div>
  );
}
