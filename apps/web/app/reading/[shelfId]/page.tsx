"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../../contexts/AuthContext";
import { apiClient } from "../../../lib/api";
import { getAccessToken } from "../../../lib/auth";
import {
  Button,
  Container,
  EmptyState,
  Icon,
  IconButton,
  Input,
  LinkButton,
  Modal,
  Select,
  Spinner,
  colors,
  font,
  radius,
  useToast,
} from "../../../components/ui";
import type { ReadingShelfResponse, ReadingShelfItemResponse } from "@oldpages/shared-types";

type SortOrder = "date_added" | "title" | "author";

function sortItems(items: ReadingShelfItemResponse[], order: SortOrder): ReadingShelfItemResponse[] {
  return [...items].sort((a, b) => {
    if (order === "title") return a.book.title.localeCompare(b.book.title);
    if (order === "author") return (a.book.authors[0] ?? "").localeCompare(b.book.authors[0] ?? "");
    return new Date(b.added_at).getTime() - new Date(a.added_at).getTime();
  });
}

export default function ShelfDetailPage() {
  const params = useParams<{ shelfId: string }>();
  const shelfId = params.shelfId;
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [shelf, setShelf] = useState<ReadingShelfResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>("date_added");

  const [progressItem, setProgressItem] = useState<ReadingShelfItemResponse | null>(null);
  const [progressPage, setProgressPage] = useState("");
  const [progressSaving, setProgressSaving] = useState(false);

  const [removingId, setRemovingId] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    apiClient
      .listMyReadingShelves(token)
      .then((res) => {
        const found = res.items.find((s) => s.id === shelfId || s.slug === shelfId);
        setShelf(found ?? null);
        if (!found) setError("Shelf not found.");
      })
      .catch((err) => setError(err.message ?? "Failed to load shelf"))
      .finally(() => setLoading(false));
  }, [isAuthenticated, shelfId]);

  const handleRemove = async (item: ReadingShelfItemResponse) => {
    const token = getAccessToken();
    if (!token || !shelf) return;
    setRemovingId(item.id);
    try {
      await apiClient.removeReadingShelfItem(shelf.id, item.book.id, token);
      setShelf((prev) => (prev ? { ...prev, items: prev.items.filter((i) => i.id !== item.id) } : prev));
      toast("Removed from shelf", "success");
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : "Failed to remove book", "error");
    } finally {
      setRemovingId(null);
    }
  };

  const handleProgressSave = async () => {
    if (!progressItem) return;
    const token = getAccessToken();
    if (!token) return;
    setProgressSaving(true);
    try {
      await apiClient.updateReadingProgress(
        progressItem.book.id,
        { status: "currently_reading", current_page: Number(progressPage) || undefined },
        token,
      );
      setProgressItem(null);
      setProgressPage("");
      toast("Progress updated", "success");
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : "Failed to update progress", "error");
    } finally {
      setProgressSaving(false);
    }
  };

  if (isLoading || loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "24px 0" }}>
        <Container>
          <LinkButton href="/reading" variant="ghost" size="sm" style={{ marginBottom: 12 }}>
            ← Back to Reading
          </LinkButton>
          <div style={{ background: colors.dangerSoft, border: `1px solid #fecaca`, color: colors.dangerText, borderRadius: radius.lg, padding: "14px 18px" }}>
            {error}
          </div>
        </Container>
      </div>
    );
  }

  if (!shelf) return null;

  const sortedItems = sortItems(shelf.items, sortOrder);

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container>
        <LinkButton href="/reading" variant="ghost" size="sm" style={{ marginBottom: 12 }}>
          ← Back to Reading
        </LinkButton>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: font.size["2xl"], fontWeight: font.weight.bold, color: colors.text }}>
              {shelf.name}
            </h1>
            <p style={{ margin: "4px 0 0", color: colors.textSubtle, fontSize: font.size.base }}>
              {shelf.items.length} {shelf.items.length === 1 ? "book" : "books"}
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <label style={{ color: colors.textSubtle, fontSize: font.size.sm }}>Sort by:</label>
            <Select
              containerStyle={{ width: 160 }}
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as SortOrder)}
              options={[
                { value: "date_added", label: "Date Added" },
                { value: "title", label: "Title" },
                { value: "author", label: "Author" },
              ]}
            />
          </div>
        </div>

        {sortedItems.length === 0 ? (
          <EmptyState
            icon={<Icon.book size={26} color={colors.primary} />}
            title="No books on this shelf yet"
            action={<LinkButton href="/search">Browse Books</LinkButton>}
          />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 14 }}>
            {sortedItems.map((item) => (
              <div
                key={item.id}
                style={{
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: radius.xl,
                  padding: 14,
                  display: "flex",
                  flexDirection: "column",
                  gap: 10,
                }}
              >
                <div
                  style={{
                    width: "100%",
                    aspectRatio: "3/4",
                    background: colors.surfaceMuted,
                    borderRadius: radius.md,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Icon.book size={32} color={colors.textFaint} />
                </div>
                <div>
                  <p style={{ margin: 0, fontWeight: font.weight.semibold, fontSize: font.size.base, color: colors.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {item.book.title}
                  </p>
                  <p style={{ margin: "3px 0 0", color: colors.textSubtle, fontSize: font.size.sm }}>
                    {item.book.authors.join(", ")}
                  </p>
                </div>
                {item.book.page_count && (
                  <div>
                    <div style={{ height: 4, background: colors.divider, borderRadius: radius.pill }}>
                      <div style={{ height: "100%", width: "0%", background: colors.primary, borderRadius: radius.pill }} />
                    </div>
                    <p style={{ margin: "4px 0 0", color: colors.textFaint, fontSize: font.size.xs }}>
                      {item.book.page_count} pages
                    </p>
                  </div>
                )}
                {item.note && (
                  <p style={{ margin: 0, color: colors.textFaint, fontSize: font.size.xs, fontStyle: "italic" }}>
                    &ldquo;{item.note}&rdquo;
                  </p>
                )}
                <div style={{ display: "flex", gap: 8, marginTop: "auto" }}>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => { setProgressItem(item); setProgressPage(""); }}
                    style={{ flex: 1 }}
                  >
                    Update Progress
                  </Button>
                  <IconButton
                    ariaLabel="Remove from shelf"
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

        <Modal
          isOpen={!!progressItem}
          onClose={() => setProgressItem(null)}
          title="Update Reading Progress"
          footer={
            <>
              <Button variant="secondary" onClick={() => setProgressItem(null)} disabled={progressSaving}>Cancel</Button>
              <Button variant="primary" loading={progressSaving} disabled={!progressPage} onClick={handleProgressSave}>
                Save Progress
              </Button>
            </>
          }
        >
          {progressItem && (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <p style={{ margin: 0, fontWeight: font.weight.semibold, color: colors.text }}>{progressItem.book.title}</p>
              <Input
                label="Current page"
                type="number"
                value={progressPage}
                onChange={(e) => setProgressPage(e.target.value)}
                placeholder={progressItem.book.page_count ? `Max: ${progressItem.book.page_count}` : "Page number"}
                min={0}
                max={progressItem.book.page_count ?? undefined}
              />
            </div>
          )}
        </Modal>
      </Container>
    </div>
  );
}
