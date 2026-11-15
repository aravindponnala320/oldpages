"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { ListingResponse } from "@oldpages/shared-types";
import { apiClient } from "../../../lib/api";
import { getAccessToken } from "../../../lib/auth";
import {
  Container,
  EmptyState,
  Icon,
  LinkButton,
  colors,
  font,
  radius,
} from "../../../components/ui";

const STATUS_NOTE: Record<string, string> = {
  draft: "This is a draft. Publish it so buyers can find it.",
  paused: "This listing is paused, so buyers can't see it.",
  expired: "This listing has expired.",
  pending_moderation: "This listing is being reviewed.",
  suspended: "This listing was suspended by moderators.",
  rejected: "This listing was not approved.",
};

/** Shown when a listing isn't public: its seller (signed in here) still gets to see it. */
export function OwnListingFallback({ listingId }: { listingId: string }) {
  const [state, setState] = useState<"loading" | "missing" | ListingResponse>(
    "loading",
  );

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      setState("missing");
      return;
    }
    apiClient
      .getListing(listingId, token)
      .then(setState)
      .catch(() => setState("missing"));
  }, [listingId]);

  if (state === "loading") return null;

  if (state === "missing") {
    return (
      <Container>
        <div style={{ padding: "48px 0" }}>
          <EmptyState
            icon={<Icon.search size={24} color={colors.primary} />}
            title="Listing not found"
            description="It may have been sold, removed, or made private by the seller."
            action={<LinkButton href="/search">Browse books</LinkButton>}
          />
        </div>
      </Container>
    );
  }

  const note =
    STATUS_NOTE[state.status] ??
    (state.visibility === "private"
      ? "This listing is private: only you can see it."
      : "Only you and your team can see this listing.");
  return (
    <Container>
      <div
        style={{
          maxWidth: 560,
          margin: "32px auto",
          padding: 24,
          background: colors.surface,
          border: `1px solid ${colors.border}`,
          borderRadius: radius.xl,
        }}
      >
        <p
          style={{
            margin: "0 0 6px",
            fontSize: font.size.sm,
            fontWeight: font.weight.semibold,
            color: colors.primary,
          }}
        >
          Only visible to you
        </p>
        <h1
          style={{
            margin: "0 0 8px",
            fontSize: font.size["2xl"],
            color: colors.text,
          }}
        >
          {state.title}
        </h1>
        <p
          style={{
            margin: "0 0 20px",
            color: colors.textMuted,
            lineHeight: 1.5,
          }}
        >
          {note}
        </p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <LinkButton href={`/listings/${state.id}/edit`}>
            Edit listing
          </LinkButton>
          <Link
            href="/my-listings"
            style={{
              alignSelf: "center",
              color: colors.primary,
              textDecoration: "none",
              fontWeight: font.weight.medium,
            }}
          >
            My Ads
          </Link>
        </div>
      </div>
    </Container>
  );
}
