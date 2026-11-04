"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../contexts/AuthContext";
import { apiClient } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import {
  Badge,
  Button,
  Container,
  EmptyState,
  Icon,
  IconButton,
  Input,
  LinkButton,
  PageHeader,
  Section,
  Spinner,
  colors,
  font,
  radius,
  useToast,
} from "../../components/ui";
import type { WishlistItemResponse, BookResponse } from "@oldpages/shared-types";

export default function WishlistsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [wishlistItems, setWishlistItems] = useState<WishlistItemResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<BookResponse[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [addingId, setAddingId] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    setLoading(false);
    setWishlistItems([]);
  }, [isAuthenticated]);

  useEffect(() => {
    if (!searchQuery.trim()) { setSearchResults([]); setShowDropdown(false); return; }
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const res = await apiClient.listBooks({ query: searchQuery, limit: 8 });
        setSearchResults(res.items);
        setShowDropdown(true);
      } catch {
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 400);
    return () => { if (searchTimeout.current) clearTimeout(searchTimeout.current); };
  }, [searchQuery]);

  const handleAdd = async (book: BookResponse) => {
    const token = getAccessToken();
    if (!token) return;
    setAddingId(book.id);
    try {
      const item = await apiClient.addWishlistItem(book.id, token);
      setWishlistItems((prev) => [item, ...prev]);
      setSearchQuery("");
      setSearchResults([]);
      setShowDropdown(false);
      toast("Added to wishlist", "success");
    } catch {
      toast("Failed to add to wishlist", "error");
    } finally {
      setAddingId(null);
    }
  };

  const handleRemove = async (item: WishlistItemResponse) => {
    const token = getAccessToken();
    if (!token) return;
    setRemovingId(item.id);
    try {
      await apiClient.deleteWishlistItem(item.book.id, token);
      setWishlistItems((prev) => prev.filter((w) => w.id !== item.id));
      toast("Removed from wishlist", "success");
    } catch {
      toast("Failed to remove from wishlist", "error");
    } finally {
      setRemovingId(null);
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
          title="My Wishlist"
          subtitle={`${wishlistItems.length} book${wishlistItems.length !== 1 ? "s" : ""} · You'll be notified when copies become available`}
        />

        <div style={{ marginBottom: 20 }}>
          <Section title="Add a book">
            <div style={{ position: "relative" }}>
              <Input
                prefix={<Icon.search size={16} color={colors.textFaint} />}
                suffix={searchLoading ? <Spinner size="sm" /> : undefined}
                placeholder="Search by title, author, or ISBN..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />

              {showDropdown && searchResults.length > 0 && (
                <div
                  style={{
                    position: "absolute",
                    top: "calc(100% + 6px)",
                    left: 0,
                    right: 0,
                    zIndex: 20,
                    background: colors.surface,
                    border: `1px solid ${colors.borderStrong}`,
                    borderRadius: radius.lg,
                    boxShadow: "0 8px 24px rgba(15,23,42,0.12)",
                    maxHeight: 340,
                    overflowY: "auto",
                  }}
                >
                  {searchResults.map((book) => {
                    const already = wishlistItems.some((w) => w.book.id === book.id);
                    return (
                      <div
                        key={book.id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 12,
                          padding: "10px 14px",
                          borderBottom: `1px solid ${colors.divider}`,
                        }}
                      >
                        {book.cover_image_url && (
                          <img
                            src={book.cover_image_url}
                            alt={book.title}
                            style={{ width: 40, height: 52, objectFit: "cover", borderRadius: 4, flexShrink: 0 }}
                          />
                        )}
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <p style={{ margin: 0, fontWeight: font.weight.semibold, fontSize: font.size.base, color: colors.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {book.title}
                          </p>
                          <p style={{ margin: 0, fontSize: font.size.sm, color: colors.textSubtle }}>
                            {book.authors.map((a) => a.name).join(", ")}
                            {book.publication_year && ` · ${book.publication_year}`}
                          </p>
                        </div>
                        <Button
                          size="sm"
                          variant={already ? "secondary" : "primary"}
                          disabled={addingId === book.id || already}
                          loading={addingId === book.id}
                          onClick={() => !already && handleAdd(book)}
                        >
                          {already ? "Added" : "Add"}
                        </Button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </Section>
        </div>

        {wishlistItems.length === 0 ? (
          <EmptyState
            icon={<Icon.clipboard size={26} color={colors.primary} />}
            title="Your wishlist is empty"
            description="Add books you want to read or buy. You'll be notified when copies become available from sellers near you."
            action={<LinkButton href="/search">Explore Book Catalog</LinkButton>}
          />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {wishlistItems.map((item) => (
              <div
                key={item.id}
                style={{
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: radius.xl,
                  padding: 14,
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                }}
              >
                <div style={{ width: 48, height: 64, background: colors.surfaceMuted, borderRadius: radius.md, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <Icon.book size={22} color={colors.textFaint} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ margin: 0, fontWeight: font.weight.semibold, fontSize: font.size.md, color: colors.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {item.book.title}
                  </p>
                  <p style={{ margin: "3px 0 6px", fontSize: font.size.sm, color: colors.textSubtle }}>
                    {item.book.authors.join(", ")}
                  </p>
                  <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                    {item.book.categories?.slice(0, 2).map((c) => <Badge key={c} label={c} />)}
                  </div>
                  <p style={{ margin: "6px 0 0", fontSize: font.size.xs, color: colors.textFaint }}>
                    Added {new Date(item.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                  <LinkButton href={`/search?q=${encodeURIComponent(item.book.title)}`} variant="secondary" size="sm">
                    Find Copies
                  </LinkButton>
                  <IconButton
                    ariaLabel="Remove from wishlist"
                    icon={removingId === item.id ? <Spinner size="sm" /> : <Icon.trash size={16} />}
                    onClick={() => handleRemove(item)}
                    disabled={removingId === item.id}
                    variant="ghost"
                    size="sm"
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </Container>
    </div>
  );
}
