"use client";

import { useEffect, useState } from "react";
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
  Input,
  Modal,
  PageHeader,
  Spinner,
  Tabs,
  Textarea,
  colors,
  font,
  formatPrice,
  radius,
  useToast,
} from "../../components/ui";
import type { OfferResponse, OfferStatus } from "@oldpages/shared-types";

type Tab = "received" | "sent";

/**
 * There is no `listOffers` endpoint yet in the API — offers are surfaced per
 * conversation. Until an aggregate endpoint ships, this returns [] so the page
 * shows a proper empty state instead of dummy rows.
 */
async function fetchOffers(_token: string): Promise<OfferResponse[]> { return []; }

function statusVariant(status: OfferStatus): "warning" | "success" | "danger" | "default" {
  if (status === "pending" || status === "countered") return "warning";
  if (status === "accepted") return "success";
  if (status === "rejected") return "danger";
  return "default";
}

function statusLabel(status: OfferStatus): string {
  const map: Record<OfferStatus, string> = {
    pending: "Pending", countered: "Countered", accepted: "Accepted",
    rejected: "Declined", withdrawn: "Withdrawn", expired: "Expired",
  };
  return map[status] ?? status;
}

export default function OffersPage() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();
  const { toast } = useToast();

  const [offers, setOffers] = useState<OfferResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("received");
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const [counterModal, setCounterModal] = useState<{ offerId: string; current?: number; currency: string } | null>(null);
  const [counterAmount, setCounterAmount] = useState("");
  const [counterMsg, setCounterMsg] = useState("");
  const [counterLoading, setCounterLoading] = useState(false);
  const [acceptModal, setAcceptModal] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/");
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (!isAuthenticated) return;
    const token = getAccessToken();
    if (!token) return;
    setLoading(true);
    fetchOffers(token)
      .then(setOffers)
      .catch(() => toast("Failed to load offers", "error"))
      .finally(() => setLoading(false));
  }, [isAuthenticated, toast]);

  const received = offers.filter((o) => o.seller.id === user?.id);
  const sent = offers.filter((o) => o.buyer.id === user?.id);
  const displayed = tab === "received" ? received : sent;

  const handleAccept = async (offerId: string) => {
    const token = getAccessToken();
    if (!token) return;
    setActionLoading(offerId);
    try {
      const result = await apiClient.acceptOffer(offerId, {}, token);
      setOffers((prev) => prev.map((o) => (o.id === offerId ? result : o)));
      setAcceptModal(null);
      toast("Offer accepted", "success");
    } catch {
      toast("Failed to accept offer", "error");
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (offerId: string) => {
    const token = getAccessToken();
    if (!token) return;
    setActionLoading(offerId);
    try {
      const result = await apiClient.rejectOffer(offerId, {}, token);
      setOffers((prev) => prev.map((o) => (o.id === offerId ? result : o)));
      toast("Offer declined", "info");
    } catch {
      toast("Failed to decline offer", "error");
    } finally {
      setActionLoading(null);
    }
  };

  const handleWithdraw = async (offerId: string) => {
    const token = getAccessToken();
    if (!token) return;
    setActionLoading(offerId);
    try {
      const result = await apiClient.withdrawOffer(offerId, {}, token);
      setOffers((prev) => prev.map((o) => (o.id === offerId ? result : o)));
      toast("Offer withdrawn", "info");
    } catch {
      toast("Failed to withdraw offer", "error");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCounter = async () => {
    if (!counterModal) return;
    const token = getAccessToken();
    if (!token) return;
    const amountCents = Math.round(parseFloat(counterAmount) * 100);
    if (!amountCents || isNaN(amountCents)) return;
    setCounterLoading(true);
    try {
      const result = await apiClient.counterOffer(
        counterModal.offerId,
        { amount_cents: amountCents, currency: counterModal.currency, message: counterMsg || null },
        token,
      );
      setOffers((prev) => prev.map((o) => (o.id === counterModal.offerId ? result : o)));
      setCounterModal(null);
      setCounterAmount("");
      setCounterMsg("");
      toast("Counter offer sent", "success");
    } catch {
      toast("Failed to send counter", "error");
    } finally {
      setCounterLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
        <Spinner size="lg" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  return (
    <div style={{ padding: "24px 0 40px" }}>
      <Container>
        <PageHeader
          eyebrow="Trade"
          title="Offers"
          subtitle="Manage your incoming and outgoing price offers."
        />

        <div style={{ marginBottom: 20 }}>
          <Tabs
            tabs={[
              { key: "received", label: "Received", count: received.length },
              { key: "sent",     label: "Sent",     count: sent.length },
            ]}
            value={tab}
            onChange={(k) => setTab(k as Tab)}
          />
        </div>

        {loading && (
          <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
            <Spinner size="md" />
          </div>
        )}

        {!loading && displayed.length === 0 && (
          <EmptyState
            icon={<Icon.chat size={26} color={colors.primary} />}
            title={`No ${tab} offers`}
            description={
              tab === "sent"
                ? "Make an offer on a listing to get started."
                : "Offers from buyers will appear here."
            }
          />
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {displayed.map((offer) => {
            const isActing = actionLoading === offer.id;
            const isPending = offer.status === "pending";
            const isAccepted = offer.status === "accepted";
            const counterpartyId = tab === "received" ? offer.buyer.id : offer.seller.id;
            return (
              <div
                key={offer.id}
                style={{
                  background: colors.surface,
                  border: `1px solid ${colors.border}`,
                  borderRadius: radius.xl,
                  padding: 18,
                }}
              >
                <div style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
                  <div style={{ width: 48, height: 64, background: colors.surfaceMuted, borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                    <Icon.book size={22} color={colors.textFaint} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6, flexWrap: "wrap" }}>
                      <span style={{ fontWeight: font.weight.semibold, fontSize: font.size.base, color: colors.text }}>
                        Listing {offer.listing_id.slice(0, 8)}…
                      </span>
                      <Badge variant={statusVariant(offer.status)} label={statusLabel(offer.status)} />
                    </div>
                    <p style={{ margin: 0, fontSize: font.size["2xl"], fontWeight: font.weight.heavy, color: colors.text, letterSpacing: "-0.02em" }}>
                      {formatPrice(offer.amount_cents, offer.currency)}
                    </p>
                    <p style={{ margin: "4px 0 0", fontSize: font.size.xs, color: colors.textFaint }}>
                      {tab === "received" ? "From" : "To"}: User {counterpartyId.slice(0, 6)} · {new Date(offer.created_at).toLocaleDateString()}
                    </p>
                    {offer.message && (
                      <p style={{ margin: "8px 0 0", fontSize: font.size.base, color: colors.textSubtle, fontStyle: "italic" }}>
                        &ldquo;{offer.message}&rdquo;
                      </p>
                    )}
                  </div>
                </div>

                <div style={{ display: "flex", gap: 8, marginTop: 14, flexWrap: "wrap" }}>
                  {tab === "received" && isPending && (
                    <>
                      <Button variant="primary" size="sm" loading={isActing} onClick={() => setAcceptModal(offer.id)}>Accept</Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setCounterModal({ offerId: offer.id, current: offer.amount_cents ?? undefined, currency: offer.currency })}
                      >
                        Counter
                      </Button>
                      <Button variant="danger" size="sm" loading={isActing} onClick={() => handleReject(offer.id)}>Decline</Button>
                    </>
                  )}
                  {tab === "sent" && isPending && (
                    <Button variant="danger" size="sm" loading={isActing} onClick={() => handleWithdraw(offer.id)}>Withdraw</Button>
                  )}
                  {isAccepted && offer.transaction_id && (
                    <Button variant="primary" size="sm" onClick={() => router.push(`/orders/${offer.transaction_id}`)}>
                      View Order
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <Modal
          isOpen={!!counterModal}
          onClose={() => { setCounterModal(null); setCounterAmount(""); setCounterMsg(""); }}
          title="Counter Offer"
          footer={
            <>
              <Button variant="secondary" onClick={() => setCounterModal(null)}>Cancel</Button>
              <Button variant="primary" loading={counterLoading} onClick={handleCounter}>Send Counter</Button>
            </>
          }
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {counterModal?.current && (
              <div style={{ background: colors.surfaceMuted, borderRadius: radius.lg, padding: 12 }}>
                <p style={{ margin: "0 0 4px", fontSize: font.size.xs, fontWeight: font.weight.bold, color: colors.textFaint, textTransform: "uppercase" }}>
                  Their offer
                </p>
                <p style={{ margin: 0, fontWeight: font.weight.bold, color: colors.text, fontSize: font.size.lg }}>
                  {formatPrice(counterModal.current, counterModal.currency)}
                </p>
              </div>
            )}
            <Input
              label={`Your counter amount (${counterModal?.currency ?? "INR"})`}
              type="number"
              placeholder="e.g. 250"
              value={counterAmount}
              onChange={(e) => setCounterAmount(e.target.value)}
            />
            <Textarea
              label="Message (optional)"
              rows={3}
              placeholder="Add a note..."
              value={counterMsg}
              onChange={(e) => setCounterMsg(e.target.value)}
            />
          </div>
        </Modal>

        <Modal
          isOpen={!!acceptModal}
          onClose={() => setAcceptModal(null)}
          title="Accept Offer"
          footer={
            <>
              <Button variant="secondary" onClick={() => setAcceptModal(null)}>Cancel</Button>
              <Button variant="primary" loading={actionLoading === acceptModal} onClick={() => acceptModal && handleAccept(acceptModal)}>
                Yes, Accept
              </Button>
            </>
          }
        >
          <p style={{ margin: 0, lineHeight: 1.6, color: colors.text }}>
            Are you sure you want to accept this offer? This will create an order that you need to fulfill.
          </p>
        </Modal>
      </Container>
    </div>
  );
}
