"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../contexts/AuthContext";
import { apiClient } from "../../lib/api";
import { getAccessToken } from "../../lib/auth";
import {
  Badge,
  BookCover,
  Button,
  Container,
  EmptyState,
  Icon,
  LinkButton,
  Modal,
  PageHeader,
  Spinner,
  Tabs,
  colors,
  font,
  formatPrice,
  radius,
  useToast,
} from "../../components/ui";
import type { ListingResponse, ListingStatus } from "@oldpages/shared-types";

const STATUS_TABS: { key: ListingStatus | "all"; label: string }[] = [
  { key: "all",       label: "All" },
  { key: "active",    label: "Active" },
  { key: "draft",     label: "Drafts" },
  { key: "paused",    label: "Paused" },
  { key: "completed", label: "Completed" },
];

const STATUS_VARIANT: Record<ListingStatus, "success" | "warning" | "danger" | "info" | "default"> = {
  active: "success", draft: "default", paused: "warning", completed: "info",
  expired: "warning", reserved: "info", pending_moderation: "warning",
  suspended: "danger", rejected: "danger", deleted: "danger",
};

export default function MyListingsPage() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [listings, setListings] = useState<ListingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ListingStatus | "all">("all");
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ListingResponse | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated || !user) return;
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    fetch(`${API_BASE}/api/v1/listings/mine?limit=100`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("Failed to load"))))
      .then((data: ListingResponse[]) => setListings(data))
      .catch((err) => setError(err.message ?? "Failed to load listings"))
      .finally(() => setLoading(false));
  }, [isAuthenticated, user]);

  const run = async (
    listing: ListingResponse,
    fn: (id: string, token: string) => Promise<ListingResponse>,
    successMsg: string,
    errorMsg: string,
  ) => {
    const token = getAccessToken();
    if (!token) return;
    setActionLoading(listing.id);
    try {
      const updated = await fn(listing.id, token);
      setListings((prev) => prev.map((l) => (l.id === listing.id ? updated : l)));
      toast(successMsg, "success");
    } catch {
      toast(errorMsg, "error");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    const token = getAccessToken();
    if (!token) return;
    setActionLoading(deleteTarget.id);
    try {
      await apiClient.deleteListing(deleteTarget.id, token);
      setListings((prev) => prev.filter((l) => l.id !== deleteTarget.id));
      setDeleteTarget(null);
      toast("Listing deleted", "success");
    } catch {
      toast("Failed to delete listing", "error");
    } finally {
      setActionLoading(null);
    }
  };

  const filtered = activeTab === "all" ? listings : listings.filter((l) => l.status === activeTab);

  if (isLoading || loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }

  const tabsWithCounts = STATUS_TABS.map((t) => ({
    key: t.key,
    label: t.label,
    count: t.key === "all" ? listings.length : listings.filter((l) => l.status === t.key).length,
  }));

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container>
        <PageHeader
          eyebrow="Seller"
          title="My Listings"
          subtitle={`${listings.length} listing${listings.length !== 1 ? "s" : ""}`}
          actions={<LinkButton href="/listings/create" leftIcon={<Icon.plus size={16} />}>Create New Listing</LinkButton>}
        />

        {error && (
          <div
            role="alert"
            style={{
              background: colors.dangerSoft,
              border: `1px solid #fecaca`,
              color: colors.dangerText,
              borderRadius: radius.lg,
              padding: "10px 14px",
              marginBottom: 16,
            }}
          >
            {error}
          </div>
        )}

        <div style={{ marginBottom: 20 }}>
          <Tabs
            tabs={tabsWithCounts}
            value={activeTab}
            onChange={(k) => setActiveTab(k as ListingStatus | "all")}
          />
        </div>

        {filtered.length === 0 ? (
          <EmptyState
            icon={<Icon.book size={28} color={colors.primary} />}
            title={activeTab === "all" ? "No listings yet" : `No ${activeTab} listings`}
            description={
              activeTab === "all"
                ? "Start listing your books to sell, exchange, or donate them."
                : `You don't have any ${activeTab} listings.`
            }
            action={<LinkButton href="/listings/create">Create Your First Listing</LinkButton>}
          />
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {filtered.map((listing) => (
              <div
                key={listing.id}
                style={{
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: radius.xl,
                  padding: 16,
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                  flexWrap: "wrap",
                }}
              >
                <div style={{ width: 56, height: 72, flexShrink: 0, overflow: "hidden", borderRadius: radius.md }}>
                  <BookCover
                    imageUrl={listing.images[0]?.public_url}
                    title={listing.title}
                    seed={listing.id}
                    aspectRatio="7/9"
                  />
                </div>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <Link
                    href={`/listings/${listing.id}`}
                    style={{ textDecoration: "none", color: colors.text, fontSize: font.size.md, fontWeight: font.weight.semibold, display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
                  >
                    {listing.title}
                  </Link>
                  <div style={{ display: "flex", gap: 8, marginTop: 6, alignItems: "center", flexWrap: "wrap" }}>
                    <Badge
                      variant={STATUS_VARIANT[listing.status] ?? "default"}
                      label={listing.status.replace(/_/g, " ")}
                    />
                    <span style={{ color: colors.textMuted, fontSize: font.size.sm, fontWeight: font.weight.semibold }}>
                      {formatPrice(listing.price_amount_cents, listing.currency)}
                    </span>
                    {listing.condition?.condition && (
                      <span style={{ color: colors.textFaint, fontSize: font.size.xs }}>
                        {listing.condition.condition.replace(/_/g, " ")}
                      </span>
                    )}
                  </div>
                  <p style={{ margin: "4px 0 0", color: colors.textFaint, fontSize: font.size.xs }}>
                    Listed {new Date(listing.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div style={{ display: "flex", gap: 8, flexShrink: 0, flexWrap: "wrap" }}>
                  <LinkButton href={`/listings/${listing.id}/edit`} variant="secondary" size="sm">Edit</LinkButton>
                  {listing.status === "active" && (
                    <Button variant="secondary" size="sm" loading={actionLoading === listing.id}
                      onClick={() => run(listing, apiClient.pauseListing.bind(apiClient), "Listing paused", "Failed to pause listing")}>
                      Pause
                    </Button>
                  )}
                  {listing.status === "paused" && (
                    <Button variant="secondary" size="sm" loading={actionLoading === listing.id}
                      onClick={() => run(listing, apiClient.relistListing.bind(apiClient), "Listing resumed", "Failed to resume listing")}>
                      Resume
                    </Button>
                  )}
                  {listing.status === "draft" && (
                    <Button variant="primary" size="sm" loading={actionLoading === listing.id}
                      onClick={() => run(listing, apiClient.publishListing.bind(apiClient), "Listing published", "Failed to publish listing")}>
                      Publish
                    </Button>
                  )}
                  <Button variant="danger" size="sm" disabled={actionLoading === listing.id} onClick={() => setDeleteTarget(listing)}>
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

        <Modal
          isOpen={!!deleteTarget}
          onClose={() => setDeleteTarget(null)}
          title="Delete Listing"
          footer={
            <>
              <Button variant="secondary" onClick={() => setDeleteTarget(null)}>Cancel</Button>
              <Button variant="danger" loading={actionLoading === deleteTarget?.id} onClick={handleDelete}>
                Delete Listing
              </Button>
            </>
          }
        >
          {deleteTarget && (
            <p style={{ margin: 0, lineHeight: 1.6, color: colors.text }}>
              Are you sure you want to delete <strong>&ldquo;{deleteTarget.title}&rdquo;</strong>? This action cannot be undone.
            </p>
          )}
        </Modal>
      </Container>
    </div>
  );
}
