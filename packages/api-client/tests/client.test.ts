import { describe, expect, it, vi } from "vitest";

import { OldPagesApiClient } from "../src/index";

describe("OldPagesApiClient", () => {
  it("parses live health responses", async () => {
    const fetcher = vi.fn(async () =>
      Response.json({
        components: {},
        environment: "test",
        service: "oldpages-api",
        status: "ok",
        version: "0.0.0",
      }),
    );
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await expect(client.getLiveHealth()).resolves.toMatchObject({
      service: "oldpages-api",
      status: "ok",
    });
    expect(fetcher).toHaveBeenCalledOnce();
  });

  it("sends register payloads to the auth API", async () => {
    const requestedUrls: string[] = [];
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      requestedUrls.push(input.toString());
      return Promise.resolve(
        Response.json({
          tokens: {
            access_token: "access",
            expires_in_seconds: 900,
            refresh_token: "refresh",
            token_type: "bearer",
          },
          user: {
            email: "reader@example.com",
            email_verified: false,
            id: "01JTESTUSER0000000000000",
            status: "active",
          },
        }),
      );
    });
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await expect(
      client.register({
        display_name: "Reader",
        email: "reader@example.com",
        password: "correct horse battery staple",
        privacy_accepted: true,
        terms_accepted: true,
        username: "reader",
      }),
    ).resolves.toMatchObject({ user: { email: "reader@example.com" } });
    expect(requestedUrls[0]).toBe("http://localhost:8000/api/v1/auth/register");
  });

  it("serializes catalog list filters", async () => {
    const requestedUrls: string[] = [];
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      requestedUrls.push(input.toString());
      return Promise.resolve(
        Response.json({
          items: [sampleBook()],
          next_cursor: null,
        }),
      );
    });
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await expect(
      client.listBooks({ isbn: "9780143039433", limit: 10, query: "Godaan" }),
    ).resolves.toMatchObject({ items: [{ title: "Godaan" }] });
    expect(requestedUrls[0]).toBe(
      "http://localhost:8000/api/v1/books?isbn=9780143039433&limit=10&query=Godaan",
    );
  });

  it("sends authenticated catalog create payloads", async () => {
    const requestInits: (RequestInit | undefined)[] = [];
    const requestedUrls: string[] = [];
    const fetcher = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        requestedUrls.push(input.toString());
        requestInits.push(init);
        return Promise.resolve(Response.json(sampleBook()));
      },
    );
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await expect(
      client.createBook(
        {
          authors: [{ name: "Munshi Premchand" }],
          isbn_13: "9780143039433",
          title: "Godaan",
        },
        "access-token",
      ),
    ).resolves.toMatchObject({ isbn_13: "9780143039433" });

    const init = requestInits[0];
    if (!init) {
      throw new Error("Expected request init options.");
    }
    expect(requestedUrls[0]).toBe("http://localhost:8000/api/v1/books");
    expect(init.method).toBe("POST");
    expect(init.headers).toMatchObject({
      Authorization: "Bearer access-token",
      "Content-Type": "application/json",
    });
  });

  it("requests listing media upload URLs", async () => {
    const requestedUrls: string[] = [];
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      requestedUrls.push(input.toString());
      return Promise.resolve(
        Response.json({
          expires_at: "2026-06-23T00:15:00Z",
          headers: { "Content-Type": "image/jpeg" },
          id: "01JMEDIA000000000000000",
          storage_key: "media/user/media/listing.jpg",
          upload_url:
            "http://localhost:9000/oldpages-media/media/user/media/listing.jpg",
        }),
      );
    });
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await expect(
      client.requestMediaUploadUrl(
        {
          byte_size: 512000,
          content_type: "image/jpeg",
          filename: "listing.jpg",
        },
        "access-token",
      ),
    ).resolves.toMatchObject({ id: "01JMEDIA000000000000000" });
    expect(requestedUrls[0]).toBe(
      "http://localhost:8000/api/v1/media/upload-url",
    );
  });

  it("sends authenticated listing create payloads", async () => {
    const requestedUrls: string[] = [];
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      requestedUrls.push(input.toString());
      return Promise.resolve(Response.json(sampleListing()));
    });
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await expect(
      client.createListing(
        {
          book_id: "01JBOOK00000000000000000",
          condition: { condition: "good" },
          listing_modes: ["sell"],
          location: {
            city: "Pune",
            country: "IN",
            public_area: "Deccan, Pune",
          },
          price_amount_cents: 45000,
        },
        "access-token",
      ),
    ).resolves.toMatchObject({ status: "draft", title: "Godaan" });
    expect(requestedUrls[0]).toBe("http://localhost:8000/api/v1/listings");
  });

  it("serializes listing search filters", async () => {
    const requestedUrls: string[] = [];
    const fetcher = vi.fn(async (input: RequestInfo | URL) => {
      requestedUrls.push(input.toString());
      return Promise.resolve(Response.json(sampleListingSearch()));
    });
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await expect(
      client.searchListings({
        city: "Pune",
        latitude: 18.52,
        limit: 10,
        listing_mode: "sell",
        longitude: 73.85,
        q: "Godaan",
        sort: "nearest",
      }),
    ).resolves.toMatchObject({ items: [{ title: "Godaan" }] });
    expect(requestedUrls[0]).toBe(
      "http://localhost:8000/api/v1/search/listings?city=Pune&latitude=18.52&limit=10&listing_mode=sell&longitude=73.85&q=Godaan&sort=nearest",
    );
  });

  it("sends authenticated discovery mutations", async () => {
    const requestedUrls: string[] = [];
    const requestInits: (RequestInit | undefined)[] = [];
    const fetcher = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        requestedUrls.push(input.toString());
        requestInits.push(init);
        if (input.toString().endsWith("/saved-searches")) {
          return Promise.resolve(Response.json(sampleSavedSearch()));
        }
        if (input.toString().includes("/wishlists/")) {
          return Promise.resolve(Response.json(sampleWishlistItem()));
        }
        if (input.toString().includes("/favorite")) {
          return Promise.resolve(Response.json(sampleFavorite()));
        }
        return Promise.resolve(Response.json(sampleFollow()));
      },
    );
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await client.createSavedSearch(
      { filters: { city: "Pune" }, name: "Pune", query: "Godaan" },
      "access-token",
    );
    await client.addWishlistItem("01JBOOK00000000000000000", "access-token");
    await client.favoriteListing("01JLISTING00000000000000", "access-token");
    await client.createFollow(
      { target_id: "01JSELLER000000000000000", target_type: "seller" },
      "access-token",
    );

    expect(requestedUrls).toEqual([
      "http://localhost:8000/api/v1/saved-searches",
      "http://localhost:8000/api/v1/wishlists/01JBOOK00000000000000000",
      "http://localhost:8000/api/v1/listings/01JLISTING00000000000000/favorite",
      "http://localhost:8000/api/v1/follows",
    ]);
    for (const init of requestInits) {
      expect(init?.headers).toMatchObject({
        Authorization: "Bearer access-token",
      });
    }
  });

  it("sends authenticated chat and notification requests", async () => {
    const requestedUrls: string[] = [];
    const requestInits: (RequestInit | undefined)[] = [];
    const fetcher = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = input.toString();
        requestedUrls.push(url);
        requestInits.push(init);
        if (url.endsWith("/chat-requests")) {
          return Promise.resolve(Response.json(sampleChatRequest("pending")));
        }
        if (url.endsWith("/accept")) {
          return Promise.resolve(Response.json(sampleChatRequest("accepted")));
        }
        if (url.includes("/conversations/") && url.endsWith("/messages")) {
          return Promise.resolve(Response.json(sampleMessage()));
        }
        if (url.includes("/conversations?")) {
          return Promise.resolve(Response.json(sampleConversations()));
        }
        if (url.includes("/notifications?")) {
          return Promise.resolve(Response.json(sampleNotifications()));
        }
        if (url.endsWith("/read")) {
          return Promise.resolve(Response.json(sampleNotification("read")));
        }
        return Promise.resolve(Response.json(sampleNotificationPreferences()));
      },
    );
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await client.createChatRequest(
      { listing_id: "01JLISTING00000000000000", message: "Available?" },
      "access-token",
    );
    await client.acceptChatRequest(
      "01JCHATREQ0000000000000",
      { message: "Yes." },
      "access-token",
    );
    await client.listConversations("access-token", { limit: 10 });
    await client.sendConversationMessage(
      "01JCONVO000000000000000",
      { body: "Great.", client_message_id: "client-1" },
      "access-token",
    );
    await client.listNotifications("access-token", { limit: 20 });
    await client.markNotificationRead(
      "01JNOTIFY00000000000000",
      "access-token",
    );
    await client.updateNotificationPreferences(
      { email_enabled: false },
      "access-token",
    );

    expect(requestedUrls).toEqual([
      "http://localhost:8000/api/v1/chat-requests",
      "http://localhost:8000/api/v1/chat-requests/01JCHATREQ0000000000000/accept",
      "http://localhost:8000/api/v1/conversations?limit=10",
      "http://localhost:8000/api/v1/conversations/01JCONVO000000000000000/messages",
      "http://localhost:8000/api/v1/notifications?limit=20",
      "http://localhost:8000/api/v1/notifications/01JNOTIFY00000000000000/read",
      "http://localhost:8000/api/v1/notification-preferences",
    ]);
    for (const init of requestInits) {
      expect(init?.headers).toMatchObject({
        Authorization: "Bearer access-token",
      });
    }
  });

  it("sends authenticated commerce requests", async () => {
    const requestedUrls: string[] = [];
    const requestInits: (RequestInit | undefined)[] = [];
    const fetcher = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = input.toString();
        requestedUrls.push(url);
        requestInits.push(init);
        if (url.endsWith("/pickups")) {
          return Promise.resolve(Response.json(samplePickup("proposed")));
        }
        if (url.endsWith("/confirm")) {
          return Promise.resolve(Response.json(samplePickup("confirmed")));
        }
        if (url.includes("/transactions/")) {
          return Promise.resolve(Response.json(sampleTransaction("completed")));
        }
        if (url.endsWith("/reviews")) {
          return Promise.resolve(Response.json(sampleReview()));
        }
        if (url.endsWith("/counter")) {
          return Promise.resolve(
            Response.json(sampleOffer("pending", "counter")),
          );
        }
        if (url.endsWith("/accept")) {
          return Promise.resolve(
            Response.json(sampleOffer("accepted", "price")),
          );
        }
        return Promise.resolve(Response.json(sampleOffer("pending", "price")));
      },
    );
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await client.createOffer(
      {
        amount_cents: 40000,
        listing_id: "01JLISTING00000000000000",
      },
      "access-token",
    );
    await client.counterOffer(
      "01JOFFER000000000000000",
      { amount_cents: 42000 },
      "access-token",
    );
    await client.acceptOffer("01JOFFER000000000000000", {}, "access-token");
    await client.createPickup(
      {
        public_location_label: "Library gate",
        transaction_id: "01JTX00000000000000000",
      },
      "access-token",
    );
    await client.confirmPickup("01JPICKUP0000000000000", {}, "access-token");
    await client.completeTransaction(
      "01JTX00000000000000000",
      { handover_code: "ABC123" },
      "access-token",
    );
    await client.createReview(
      {
        dimensions: [{ dimension: "communication", rating: 5 }],
        rating: 5,
        transaction_id: "01JTX00000000000000000",
      },
      "access-token",
    );

    expect(requestedUrls).toEqual([
      "http://localhost:8000/api/v1/offers",
      "http://localhost:8000/api/v1/offers/01JOFFER000000000000000/counter",
      "http://localhost:8000/api/v1/offers/01JOFFER000000000000000/accept",
      "http://localhost:8000/api/v1/pickups",
      "http://localhost:8000/api/v1/pickups/01JPICKUP0000000000000/confirm",
      "http://localhost:8000/api/v1/transactions/01JTX00000000000000000/complete",
      "http://localhost:8000/api/v1/reviews",
    ]);
    for (const init of requestInits) {
      expect(init?.headers).toMatchObject({
        Authorization: "Bearer access-token",
      });
    }
  });

  it("sends authenticated trust and moderation requests", async () => {
    const requestedUrls: string[] = [];
    const requestInits: (RequestInit | undefined)[] = [];
    const fetcher = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = input.toString();
        requestedUrls.push(url);
        requestInits.push(init);
        if (url.endsWith("/reports")) {
          return Promise.resolve(Response.json(sampleReport("open")));
        }
        if (url.endsWith("/appeal")) {
          return Promise.resolve(Response.json(sampleReport("appealed")));
        }
        if (url.includes("/conversation-evidence")) {
          return Promise.resolve(Response.json(sampleConversationEvidence()));
        }
        if (url.includes("/admin/moderation/users/")) {
          return Promise.resolve(Response.json(sampleModerationUser()));
        }
        if (url.includes("/admin/moderation/listings/")) {
          return Promise.resolve(Response.json(sampleModerationListing()));
        }
        if (url.endsWith("/rules")) {
          return Promise.resolve(Response.json(sampleModerationRules()));
        }
        if (url.endsWith("/actions")) {
          return Promise.resolve(
            Response.json(sampleModerationCase("actioned")),
          );
        }
        if (url.includes("/cases?")) {
          return Promise.resolve(
            Response.json({
              items: [sampleModerationCase("open")],
              next_cursor: null,
            }),
          );
        }
        return Promise.resolve(Response.json(sampleModerationCase("open")));
      },
    );
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await client.createReport(
      {
        reason: "scam",
        target_id: "01JUSER0000000000000000",
        target_type: "user",
      },
      "access-token",
    );
    await client.appealReport(
      "01JREPORT0000000000000",
      { statement: "Please review again." },
      "access-token",
    );
    await client.listModerationCases("access-token", {
      limit: 10,
      status: "open",
    });
    await client.getModerationCase("01JCASE000000000000000", "access-token");
    await client.takeModerationAction(
      "01JCASE000000000000000",
      { action_type: "suspend", reason: "Confirmed scam." },
      "access-token",
    );
    await client.getConversationEvidence(
      "01JCASE000000000000000",
      "access-token",
    );
    await client.getModerationUser("01JUSER0000000000000000", "access-token");
    await client.getModerationListing(
      "01JLISTING00000000000000",
      "access-token",
    );
    await client.getModerationRules("access-token");

    expect(requestedUrls).toEqual([
      "http://localhost:8000/api/v1/reports",
      "http://localhost:8000/api/v1/reports/01JREPORT0000000000000/appeal",
      "http://localhost:8000/api/v1/admin/moderation/cases?limit=10&status=open",
      "http://localhost:8000/api/v1/admin/moderation/cases/01JCASE000000000000000",
      "http://localhost:8000/api/v1/admin/moderation/cases/01JCASE000000000000000/actions",
      "http://localhost:8000/api/v1/admin/moderation/cases/01JCASE000000000000000/conversation-evidence",
      "http://localhost:8000/api/v1/admin/moderation/users/01JUSER0000000000000000",
      "http://localhost:8000/api/v1/admin/moderation/listings/01JLISTING00000000000000",
      "http://localhost:8000/api/v1/admin/moderation/rules",
    ]);
    for (const init of requestInits) {
      expect(init?.headers).toMatchObject({
        Authorization: "Bearer access-token",
      });
    }
  });

  it("sends authenticated community requests", async () => {
    const requestedUrls: string[] = [];
    const requestInits: (RequestInit | undefined)[] = [];
    const fetcher = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = input.toString();
        requestedUrls.push(url);
        requestInits.push(init);
        if (url.endsWith("/join") || url.endsWith("/approve-member")) {
          return Promise.resolve(
            Response.json(sampleCommunityMember("active")),
          );
        }
        if (url.endsWith("/posts")) {
          return Promise.resolve(Response.json(sampleCommunityPost()));
        }
        if (url.endsWith("/comments")) {
          return Promise.resolve(Response.json(samplePostComment()));
        }
        if (url.endsWith("/reactions")) {
          return Promise.resolve(Response.json(samplePostReaction()));
        }
        if (url.includes("/feed?")) {
          return Promise.resolve(
            Response.json({
              items: [sampleCommunityPost()],
              next_cursor: null,
            }),
          );
        }
        if (url.includes("/marketplace?")) {
          return Promise.resolve(
            Response.json({
              community_id: "01JCOMMUNITY000000000000",
              items: [sampleListing()],
              next_cursor: null,
            }),
          );
        }
        if (url.endsWith("/reports")) {
          return Promise.resolve(Response.json(sampleCommunityReport()));
        }
        if (url.includes("/communities?")) {
          return Promise.resolve(
            Response.json({
              items: [sampleCommunitySummary()],
              next_cursor: null,
            }),
          );
        }
        return Promise.resolve(Response.json(sampleCommunity()));
      },
    );
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await client.createCommunity(
      { city: "Pune", name: "Pune Readers", slug: "pune-readers" },
      "access-token",
    );
    await client.listCommunities({ city: "Pune", limit: 10 }, "access-token");
    await client.getCommunity("01JCOMMUNITY000000000000", "access-token");
    await client.joinCommunity(
      "01JCOMMUNITY000000000000",
      { answers: { reason: "local reader" } },
      "access-token",
    );
    await client.approveCommunityMember(
      "01JCOMMUNITY000000000000",
      { user_id: "01JUSER0000000000000000" },
      "access-token",
    );
    await client.createCommunityPost(
      "01JCOMMUNITY000000000000",
      { body: "Hello", title: "First post" },
      "access-token",
    );
    await client.getCommunityFeed(
      "01JCOMMUNITY000000000000",
      { limit: 20 },
      "access-token",
    );
    await client.getCommunityMarketplace(
      "01JCOMMUNITY000000000000",
      { limit: 20 },
      "access-token",
    );
    await client.createCommunityReport(
      "01JCOMMUNITY000000000000",
      {
        reason: "spam",
        target_type: "post",
        target_id: "01JPOST0000000000000000",
      },
      "access-token",
    );
    await client.createPostComment(
      "01JPOST0000000000000000",
      { body: "Welcome." },
      "access-token",
    );
    await client.setPostReaction(
      "01JPOST0000000000000000",
      { reaction_type: "love" },
      "access-token",
    );

    expect(requestedUrls).toEqual([
      "http://localhost:8000/api/v1/communities",
      "http://localhost:8000/api/v1/communities?city=Pune&limit=10",
      "http://localhost:8000/api/v1/communities/01JCOMMUNITY000000000000",
      "http://localhost:8000/api/v1/communities/01JCOMMUNITY000000000000/join",
      "http://localhost:8000/api/v1/communities/01JCOMMUNITY000000000000/approve-member",
      "http://localhost:8000/api/v1/communities/01JCOMMUNITY000000000000/posts",
      "http://localhost:8000/api/v1/communities/01JCOMMUNITY000000000000/feed?limit=20",
      "http://localhost:8000/api/v1/communities/01JCOMMUNITY000000000000/marketplace?limit=20",
      "http://localhost:8000/api/v1/communities/01JCOMMUNITY000000000000/reports",
      "http://localhost:8000/api/v1/posts/01JPOST0000000000000000/comments",
      "http://localhost:8000/api/v1/posts/01JPOST0000000000000000/reactions",
    ]);
    for (const init of requestInits) {
      expect(init?.headers).toMatchObject({
        Authorization: "Bearer access-token",
      });
    }
  });

  it("sends authenticated club and event requests", async () => {
    const requestedUrls: string[] = [];
    const requestInits: (RequestInit | undefined)[] = [];
    const fetcher = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = input.toString();
        requestedUrls.push(url);
        requestInits.push(init);
        if (url.endsWith("/calendar.ics")) {
          return Promise.resolve(
            new Response("BEGIN:VCALENDAR\r\nEND:VCALENDAR\r\n", {
              headers: { "Content-Type": "text/calendar" },
            }),
          );
        }
        if (url.includes("/milestones?")) {
          return Promise.resolve(
            Response.json({ items: [sampleReadingMilestone()] }),
          );
        }
        if (url.endsWith("/milestones")) {
          return Promise.resolve(Response.json(sampleReadingMilestone()));
        }
        if (url.endsWith("/select-book")) {
          return Promise.resolve(Response.json(sampleClubBook()));
        }
        if (url.endsWith("/books")) {
          if (init?.method === "POST") {
            return Promise.resolve(Response.json(sampleClubBook()));
          }
          return Promise.resolve(Response.json({ items: [sampleClubBook()] }));
        }
        if (url.endsWith("/nominations")) {
          return Promise.resolve(Response.json(sampleBookNomination()));
        }
        if (url.endsWith("/votes")) {
          return Promise.resolve(Response.json(sampleBookVote()));
        }
        if (url.includes("/buddy-reads")) {
          return Promise.resolve(Response.json(sampleBuddyRead()));
        }
        if (url.endsWith("/readalongs")) {
          return Promise.resolve(Response.json(sampleReadalong()));
        }
        if (url.endsWith("/rsvps") || url.endsWith("/rsvps/cancel")) {
          return Promise.resolve(Response.json(sampleEventRsvp()));
        }
        if (url.endsWith("/checkins")) {
          return Promise.resolve(Response.json(sampleEventCheckin()));
        }
        if (url.includes("/events?")) {
          return Promise.resolve(Response.json({ items: [sampleEvent()] }));
        }
        if (url.endsWith("/events")) {
          return Promise.resolve(Response.json(sampleEvent()));
        }
        if (url.includes("/events/")) {
          return Promise.resolve(Response.json(sampleEvent()));
        }
        if (url.includes("/clubs?")) {
          return Promise.resolve(Response.json({ items: [sampleClub()] }));
        }
        return Promise.resolve(Response.json(sampleClub()));
      },
    );
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await client.createClub(
      { name: "Pune Readers", slug: "pune-readers" },
      "access-token",
    );
    await client.listClubs({ limit: 10 }, "access-token");
    await client.getClub("01JCLUB0000000000000000", "access-token");
    await client.addClubBook(
      "01JCLUB0000000000000000",
      { book_id: "01JBOOK00000000000000000" },
      "access-token",
    );
    await client.listClubBooks("01JCLUB0000000000000000", "access-token");
    await client.createBookNomination(
      "01JCLUB0000000000000000",
      { book_id: "01JBOOK00000000000000000" },
      "access-token",
    );
    await client.castBookVote(
      "01JCLUB0000000000000000",
      { nomination_id: "01JNOM00000000000000000", rank: 1 },
      "access-token",
    );
    await client.selectClubBook(
      "01JCLUB0000000000000000",
      { cycle_key: "default" },
      "access-token",
    );
    await client.createReadingMilestone(
      "01JCLUBBOOK000000000000",
      { position_type: "page", position_value: 100, title: "Week 1" },
      "access-token",
    );
    await client.listReadingMilestones(
      "01JCLUBBOOK000000000000",
      { progress_type: "page", progress_value: 50 },
      "access-token",
    );
    await client.createBuddyRead(
      { book_id: "01JBOOK00000000000000000", title: "Buddy Sprint" },
      "access-token",
    );
    await client.joinBuddyRead("01JBUDDY00000000000000", "access-token");
    await client.updateBuddyReadProgress(
      "01JBUDDY00000000000000",
      { position_value: 50 },
      "access-token",
    );
    await client.createReadalong(
      { book_id: "01JBOOK00000000000000000", title: "July Readalong" },
      "access-token",
    );
    await client.createEvent(
      {
        ends_at: "2026-07-01T20:00:00+05:30",
        event_type: "book_exchange",
        starts_at: "2026-07-01T19:00:00+05:30",
        timezone: "Asia/Kolkata",
        title: "Book Exchange Evening",
      },
      "access-token",
    );
    await client.listEvents({ limit: 20 }, "access-token");
    await client.getEvent("01JEVENT00000000000000", "access-token");
    await client.updateEvent(
      "01JEVENT00000000000000",
      { capacity: 20 },
      "access-token",
    );
    await client.createEventRsvp(
      "01JEVENT00000000000000",
      { guest_count: 1 },
      "access-token",
    );
    await client.cancelEventRsvp("01JEVENT00000000000000", "access-token");
    await client.createEventCheckin(
      "01JEVENT00000000000000",
      { checkin_code: "CHECKIN", user_id: "01JUSER0000000000000000" },
      "access-token",
    );
    await expect(
      client.getEventCalendar("01JEVENT00000000000000", "access-token"),
    ).resolves.toContain("VCALENDAR");

    expect(requestedUrls).toEqual([
      "http://localhost:8000/api/v1/clubs",
      "http://localhost:8000/api/v1/clubs?limit=10",
      "http://localhost:8000/api/v1/clubs/01JCLUB0000000000000000",
      "http://localhost:8000/api/v1/clubs/01JCLUB0000000000000000/books",
      "http://localhost:8000/api/v1/clubs/01JCLUB0000000000000000/books",
      "http://localhost:8000/api/v1/clubs/01JCLUB0000000000000000/nominations",
      "http://localhost:8000/api/v1/clubs/01JCLUB0000000000000000/votes",
      "http://localhost:8000/api/v1/clubs/01JCLUB0000000000000000/select-book",
      "http://localhost:8000/api/v1/club-books/01JCLUBBOOK000000000000/milestones",
      "http://localhost:8000/api/v1/club-books/01JCLUBBOOK000000000000/milestones?progress_type=page&progress_value=50",
      "http://localhost:8000/api/v1/buddy-reads",
      "http://localhost:8000/api/v1/buddy-reads/01JBUDDY00000000000000/join",
      "http://localhost:8000/api/v1/buddy-reads/01JBUDDY00000000000000/progress",
      "http://localhost:8000/api/v1/readalongs",
      "http://localhost:8000/api/v1/events",
      "http://localhost:8000/api/v1/events?limit=20",
      "http://localhost:8000/api/v1/events/01JEVENT00000000000000",
      "http://localhost:8000/api/v1/events/01JEVENT00000000000000",
      "http://localhost:8000/api/v1/events/01JEVENT00000000000000/rsvps",
      "http://localhost:8000/api/v1/events/01JEVENT00000000000000/rsvps/cancel",
      "http://localhost:8000/api/v1/events/01JEVENT00000000000000/checkins",
      "http://localhost:8000/api/v1/events/01JEVENT00000000000000/calendar.ics",
    ]);
    for (const init of requestInits) {
      expect(init?.headers).toMatchObject({
        Authorization: "Bearer access-token",
      });
    }
  });

  it("sends authenticated reading tracker requests", async () => {
    const requestedUrls: string[] = [];
    const requestInits: (RequestInit | undefined)[] = [];
    const fetcher = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = input.toString();
        requestedUrls.push(url);
        requestInits.push(init);
        if (url.endsWith("/statistics/recompute")) {
          return Promise.resolve(Response.json(sampleReadingStatistic()));
        }
        if (url.endsWith("/statistics")) {
          return Promise.resolve(
            Response.json({ items: [sampleReadingStatistic()] }),
          );
        }
        if (url.endsWith("/goals")) {
          if (init?.method === "POST") {
            return Promise.resolve(Response.json(sampleReadingGoal()));
          }
          return Promise.resolve(
            Response.json({ items: [sampleReadingGoal()] }),
          );
        }
        if (url.includes("/reading-notes")) {
          return Promise.resolve(
            Response.json({ items: [sampleReadingNote()] }),
          );
        }
        if (url.endsWith("/notes") || url.includes("/notes?")) {
          if (init?.method === "POST") {
            return Promise.resolve(Response.json(sampleReadingNote()));
          }
          return Promise.resolve(
            Response.json({ items: [sampleReadingNote()] }),
          );
        }
        if (url.endsWith("/progress")) {
          return Promise.resolve(
            Response.json({ items: [sampleReadingProgress()] }),
          );
        }
        if (url.includes("/progress/")) {
          return Promise.resolve(Response.json(sampleReadingProgress()));
        }
        if (url.endsWith("/items")) {
          return Promise.resolve(Response.json(sampleReadingShelfItem()));
        }
        if (url.includes("/items/")) {
          return Promise.resolve(new Response(null, { status: 204 }));
        }
        if (url.endsWith("/shelves")) {
          if (init?.method === "POST") {
            return Promise.resolve(Response.json(sampleReadingShelf()));
          }
          return Promise.resolve(
            Response.json({ items: [sampleReadingShelf()] }),
          );
        }
        return Promise.resolve(
          Response.json({ items: [sampleReadingShelf()] }),
        );
      },
    );
    const client = new OldPagesApiClient({
      baseUrl: "http://localhost:8000",
      fetcher: fetcher as unknown as typeof fetch,
    });

    await client.createReadingShelf(
      { name: "Research", slug: "research", visibility: "private" },
      "access-token",
    );
    await client.listMyReadingShelves("access-token");
    await client.listUserReadingShelves(
      "01JUSER0000000000000000",
      "access-token",
    );
    await client.addReadingShelfItem(
      "01JSHELF000000000000000",
      { book_id: "01JBOOK00000000000000000", sort_order: 1 },
      "access-token",
    );
    await client.removeReadingShelfItem(
      "01JSHELF000000000000000",
      "01JBOOK00000000000000000",
      "access-token",
    );
    await client.updateReadingProgress(
      "01JBOOK00000000000000000",
      {
        current_page: 160,
        progressed_on: "2026-07-01",
        reading_minutes: 45,
        status: "currently_reading",
      },
      "access-token",
    );
    await client.listReadingProgress("access-token");
    await client.createReadingNote(
      {
        body: "A useful note.",
        book_id: "01JBOOK00000000000000000",
        client_note_id: "note-1",
      },
      "access-token",
    );
    await client.listReadingNotes("access-token", {
      book_id: "01JBOOK00000000000000000",
    });
    await client.listUserReadingNotes("01JUSER0000000000000000", {
      book_id: "01JBOOK00000000000000000",
    });
    await client.createReadingGoal(
      {
        goal_type: "books_per_year",
        period_end: "2026-12-31",
        period_start: "2026-01-01",
        target_value: 24,
        timezone: "Asia/Kolkata",
      },
      "access-token",
    );
    await client.listReadingGoals("access-token");
    await client.recomputeReadingStatistics(
      {
        period_start: "2026-01-01",
        period_type: "year",
        timezone: "Asia/Kolkata",
      },
      "access-token",
    );
    await client.listReadingStatistics("access-token");

    expect(requestedUrls).toEqual([
      "http://localhost:8000/api/v1/reading/shelves",
      "http://localhost:8000/api/v1/reading/shelves",
      "http://localhost:8000/api/v1/users/01JUSER0000000000000000/shelves",
      "http://localhost:8000/api/v1/reading/shelves/01JSHELF000000000000000/items",
      "http://localhost:8000/api/v1/reading/shelves/01JSHELF000000000000000/items/01JBOOK00000000000000000",
      "http://localhost:8000/api/v1/reading/progress/01JBOOK00000000000000000",
      "http://localhost:8000/api/v1/reading/progress",
      "http://localhost:8000/api/v1/reading/notes",
      "http://localhost:8000/api/v1/reading/notes?book_id=01JBOOK00000000000000000",
      "http://localhost:8000/api/v1/users/01JUSER0000000000000000/reading-notes?book_id=01JBOOK00000000000000000",
      "http://localhost:8000/api/v1/reading/goals",
      "http://localhost:8000/api/v1/reading/goals",
      "http://localhost:8000/api/v1/reading/statistics/recompute",
      "http://localhost:8000/api/v1/reading/statistics",
    ]);
    for (const [index, init] of requestInits.entries()) {
      if (index === 9) {
        expect(init?.headers).not.toMatchObject({
          Authorization: "Bearer access-token",
        });
        continue;
      }
      expect(init?.headers).toMatchObject({
        Authorization: "Bearer access-token",
      });
    }
  });
});

function sampleBook() {
  return {
    academic_metadata: null,
    authors: [
      {
        id: "01JAUTHOR000000000000000",
        name: "Munshi Premchand",
        role: "author",
      },
    ],
    categories: [],
    cover_image_url: null,
    created_at: "2026-06-23T00:00:00Z",
    description: "A canonical Hindi novel.",
    edition: "Paperback",
    format: "paperback",
    genres: ["Literary Fiction"],
    id: "01JBOOK00000000000000000",
    identifiers: [
      {
        identifier_type: "isbn13",
        identifier_value: "9780143039433",
        source: "manual",
      },
    ],
    isbn_10: null,
    isbn_13: "9780143039433",
    language: "hi",
    metadata_status: "needs_review",
    page_count: 320,
    publication_year: 2019,
    publisher: { id: "01JPUB00000000000000000", name: "Penguin Classics" },
    subjects: ["Indian literature"],
    subtitle: null,
    title: "Godaan",
    updated_at: "2026-06-23T00:00:00Z",
    work_id: "01JWORK0000000000000000",
  };
}

function sampleListing() {
  return {
    book: { id: "01JBOOK00000000000000000", title: "Godaan" },
    condition: {
      condition: "good",
      damage_details: "Light shelf wear.",
      first_edition: false,
      handwritten_notes: false,
      library_markings: false,
      loose_binding: false,
      missing_pages: false,
      name_written_inside: false,
      odor_or_smoke_exposure: false,
      signed_by_author: false,
      stains: false,
      stickers: false,
      torn_pages: false,
      water_damage: false,
    },
    created_at: "2026-06-23T00:00:00Z",
    currency: "INR",
    delivery_methods: [{ enabled: true, method: "pickup" }],
    description: "A clean used copy.",
    exchange_preferences: null,
    id: "01JLISTING00000000000000",
    images: [],
    inventory: { quantity_available: 1, quantity_total: 1 },
    lending_duration_days: null,
    listing_modes: ["sell"],
    location: {
      campus_pickup: true,
      city: "Pune",
      country: "IN",
      neighborhood: "Deccan",
      public_area: "Deccan, Pune",
      state: "Maharashtra",
    },
    negotiable: true,
    price_amount_cents: 45000,
    price_history: [],
    quality_score: 70,
    rental_deposit_amount_cents: null,
    return_policy: null,
    seller: { id: "01JSELLER000000000000000" },
    status: "draft",
    title: "Godaan",
    updated_at: "2026-06-23T00:00:00Z",
  };
}

function sampleCommunitySummary() {
  return {
    book_id: null,
    city: "Pune",
    community_type: "city",
    country: "IN",
    description: "Local reading group.",
    genre: null,
    id: "01JCOMMUNITY000000000000",
    institution: null,
    member_count: 2,
    name: "Pune Readers",
    slug: "pune-readers",
    state: "Maharashtra",
    visibility: "public",
    viewer_membership_status: "active",
  };
}

function sampleCommunity() {
  return {
    ...sampleCommunitySummary(),
    channels: [
      {
        channel_type: "general",
        id: "01JCHANNEL00000000000000",
        name: "General",
        slug: "general",
        visibility: "members",
      },
    ],
    membership_policy: "open",
    owner: { id: "01JOWNER000000000000000" },
    rules: [
      {
        body: "Keep posts relevant.",
        enabled: true,
        id: "01JRULE0000000000000000",
        sort_order: 0,
        title: "Be useful",
      },
    ],
  };
}

function sampleCommunityMember(status: "active" | "pending") {
  return {
    joined_at: status === "active" ? "2026-06-24T00:00:00Z" : null,
    role: "member",
    status,
    user: { id: "01JUSER0000000000000000" },
  };
}

function sampleCommunityPost() {
  return {
    author: { id: "01JUSER0000000000000000" },
    body: "Hello",
    channel_id: "01JCHANNEL00000000000000",
    comment_count: 1,
    community_id: "01JCOMMUNITY000000000000",
    created_at: "2026-06-24T00:00:00Z",
    id: "01JPOST0000000000000000",
    is_announcement: false,
    is_pinned: false,
    listing_id: null,
    poll: {},
    post_type: "text",
    reaction_counts: { love: 1 },
    status: "published",
    title: "First post",
    viewer_reaction: "love",
  };
}

function samplePostComment() {
  return {
    author: { id: "01JUSER0000000000000000" },
    body: "Welcome.",
    created_at: "2026-06-24T00:00:00Z",
    id: "01JCOMMENT00000000000000",
    parent_comment_id: null,
    post_id: "01JPOST0000000000000000",
    status: "published",
  };
}

function samplePostReaction() {
  return {
    id: "01JREACTION000000000000",
    post_id: "01JPOST0000000000000000",
    reaction_type: "love",
    user_id: "01JUSER0000000000000000",
  };
}

function sampleCommunityReport() {
  return {
    community_id: "01JCOMMUNITY000000000000",
    created_at: "2026-06-24T00:00:00Z",
    id: "01JCOMMREPORT00000000000",
    reason: "spam",
    status: "open",
    target_id: "01JPOST0000000000000000",
    target_type: "post",
  };
}

function sampleClub() {
  return {
    community_id: "01JCOMMUNITY000000000000",
    current_book: null,
    description: "A city club.",
    id: "01JCLUB0000000000000000",
    member_context: "owner",
    name: "Pune Readers",
    next_book: { id: "01JBOOK00000000000000000", title: "Godaan" },
    owner: { id: "01JOWNER000000000000000" },
    slug: "pune-readers",
    status: "active",
    timezone: "Asia/Kolkata",
    visibility: "public",
  };
}

function sampleClubBook() {
  return {
    available_listings: [sampleListing()],
    book: { id: "01JBOOK00000000000000000", title: "Godaan" },
    discussion_guide: null,
    end_date: null,
    id: "01JCLUBBOOK000000000000",
    selected_at: "2026-06-25T00:00:00Z",
    sequence: 1,
    start_date: null,
    status: "next",
  };
}

function sampleBookNomination() {
  return {
    book: { id: "01JBOOK00000000000000000", title: "Godaan" },
    cycle_key: "default",
    id: "01JNOM00000000000000000",
    note: null,
    nominator: { id: "01JOWNER000000000000000" },
    status: "active",
    vote_count: 1,
  };
}

function sampleBookVote() {
  return {
    cycle_key: "default",
    id: "01JVOTE0000000000000000",
    nomination_id: "01JNOM00000000000000000",
    rank: 1,
    voter: { id: "01JUSER0000000000000000" },
  };
}

function sampleReadingMilestone() {
  return {
    discussion_prompt: null,
    ends_at: null,
    id: "01JMILESTONE000000000000",
    position_type: "page",
    position_value: 100,
    spoiler_locked: true,
    starts_at: null,
    title: "Week 1",
  };
}

function sampleBuddyRead() {
  return {
    book: { id: "01JBOOK00000000000000000", title: "Godaan" },
    deadline_at: null,
    id: "01JBUDDY00000000000000",
    max_participants: 4,
    participant_user_ids: ["01JOWNER000000000000000"],
    progress: {},
    status: "active",
    title: "Buddy Sprint",
    visibility: "private",
  };
}

function sampleReadalong() {
  return {
    book: { id: "01JBOOK00000000000000000", title: "Godaan" },
    chapter_schedule: [{ chapter: 1 }],
    community_id: null,
    description: null,
    ends_at: null,
    host: { id: "01JOWNER000000000000000" },
    id: "01JREADALONG0000000000",
    starts_at: null,
    status: "scheduled",
    timezone: "Asia/Kolkata",
    title: "July Readalong",
    visibility: "public",
  };
}

function sampleEvent() {
  return {
    capacity: 20,
    checkin_code: "CHECKIN",
    club_id: "01JCLUB0000000000000000",
    community_id: null,
    description: null,
    ends_at: "2026-07-01T20:00:00+05:30",
    event_type: "book_exchange",
    id: "01JEVENT00000000000000",
    location_name: "Community library",
    online_url: null,
    organizer: { id: "01JOWNER000000000000000" },
    rsvp_count: 1,
    starts_at: "2026-07-01T19:00:00+05:30",
    status: "scheduled",
    timezone: "Asia/Kolkata",
    title: "Book Exchange Evening",
    visibility: "public",
    waitlist_count: 0,
  };
}

function sampleEventRsvp() {
  return {
    event_id: "01JEVENT00000000000000",
    guest_count: 1,
    id: "01JRSVP000000000000000",
    status: "going",
    user: { id: "01JUSER0000000000000000" },
    waitlist_position: null,
  };
}

function sampleEventCheckin() {
  return {
    checked_in_at: "2026-07-01T19:05:00+05:30",
    checked_in_by_user_id: "01JOWNER000000000000000",
    event_id: "01JEVENT00000000000000",
    id: "01JCHECKIN000000000000",
    user_id: "01JUSER0000000000000000",
  };
}

function sampleReadingBook() {
  return {
    authors: ["Munshi Premchand"],
    genres: ["Literary Fiction"],
    id: "01JBOOK00000000000000000",
    page_count: 320,
    title: "Godaan",
  };
}

function sampleReadingShelfItem() {
  return {
    added_at: "2026-07-01T00:00:00Z",
    book: sampleReadingBook(),
    id: "01JSHELFITEM00000000000",
    note: null,
    sort_order: 1,
  };
}

function sampleReadingShelf() {
  return {
    id: "01JSHELF000000000000000",
    is_system: false,
    items: [sampleReadingShelfItem()],
    name: "Research",
    shelf_type: "custom",
    slug: "research",
    sort_order: 0,
    visibility: "private",
  };
}

function sampleReadingProgress() {
  return {
    book: sampleReadingBook(),
    current_page: 160,
    daily_minutes: { "2026-07-01": 45 },
    finished_on: null,
    id: "01JPROGRESS000000000000",
    last_progress_at: "2026-07-01T00:00:00Z",
    percent_complete: 50,
    rating: null,
    reread_count: 0,
    review_text: null,
    started_on: "2026-07-01",
    status: "currently_reading",
    total_reading_minutes: 45,
  };
}

function sampleReadingNote() {
  return {
    body: "A useful note.",
    book: sampleReadingBook(),
    created_at: "2026-07-01T00:00:00Z",
    id: "01JREADNOTE000000000000",
    note_type: "note",
    page_number: 160,
    percent_complete: 50,
    visibility: "private",
  };
}

function sampleReadingGoal() {
  return {
    community_id: null,
    current_value: 0,
    goal_type: "books_per_year",
    id: "01JREADGOAL000000000000",
    period_end: "2026-12-31",
    period_start: "2026-01-01",
    scope: "personal",
    status: "active",
    target_metadata: {},
    target_value: 24,
    timezone: "Asia/Kolkata",
  };
}

function sampleReadingStatistic() {
  return {
    authors: { "Munshi Premchand": 1 },
    books_completed: 1,
    computed_at: "2026-07-02T00:00:00Z",
    genres: { "Literary Fiction": 1 },
    id: "01JREADSTAT000000000000",
    minutes_read: 60,
    monthly_progress: { "2026-07": { books_completed: 1 } },
    pages_read: 320,
    period_end: "2026-12-31",
    period_start: "2026-01-01",
    period_type: "year",
    reading_streak_days: 2,
    timezone: "Asia/Kolkata",
    year_summary: { books_completed: 1 },
  };
}

function sampleListingSearch() {
  return {
    items: [
      {
        book: sampleSearchBook(),
        condition: "good",
        created_at: "2026-06-23T00:00:00Z",
        currency: "INR",
        delivery_methods: ["pickup"],
        distance_km: 0.6,
        favorite_count: 1,
        id: "01JLISTING00000000000000",
        image_url: null,
        listing_modes: ["sell"],
        location: {
          campus_pickup: true,
          city: "Pune",
          country: "IN",
          neighborhood: "Deccan",
          public_area: "Deccan, Pune",
          state: "Maharashtra",
        },
        negotiable: true,
        price_amount_cents: 45000,
        quality_score: 70,
        seller: { id: "01JSELLER000000000000000" },
        title: "Godaan",
      },
    ],
    next_cursor: null,
    result_count: 1,
  };
}

function sampleSearchBook() {
  return {
    authors: ["Munshi Premchand"],
    categories: ["Fiction"],
    id: "01JBOOK00000000000000000",
    isbn_13: "9780143039433",
    title: "Godaan",
  };
}

function sampleSavedSearch() {
  return {
    created_at: "2026-06-23T00:00:00Z",
    filters: { city: "Pune" },
    id: "01JSAVED000000000000000",
    last_matched_at: "2026-06-23T00:00:00Z",
    last_result_count: 1,
    name: "Pune",
    notifications_enabled: true,
    query: "Godaan",
    sort: "relevance",
  };
}

function sampleWishlistItem() {
  return {
    book: sampleSearchBook(),
    created_at: "2026-06-23T00:00:00Z",
    id: "01JWISH0000000000000000",
  };
}

function sampleFavorite() {
  return {
    created_at: "2026-06-23T00:00:00Z",
    id: "01JFAV00000000000000000",
    listing_id: "01JLISTING00000000000000",
  };
}

function sampleFollow() {
  return {
    created_at: "2026-06-23T00:00:00Z",
    id: "01JFOLLOW0000000000000",
    target_id: "01JSELLER000000000000000",
    target_label: null,
    target_type: "seller",
  };
}

function sampleChatRequest(status: "accepted" | "pending") {
  return {
    conversation_id: status === "accepted" ? "01JCONVO000000000000000" : null,
    created_at: "2026-06-23T00:00:00Z",
    id: "01JCHATREQ0000000000000",
    initial_message: "Available?",
    listing_id: "01JLISTING00000000000000",
    recipient: { id: "01JSELLER000000000000000" },
    requester: { id: "01JBUYER0000000000000000" },
    responded_at: status === "accepted" ? "2026-06-23T00:01:00Z" : null,
    response_message: status === "accepted" ? "Yes." : null,
    status,
  };
}

function sampleConversations() {
  return {
    items: [
      {
        created_at: "2026-06-23T00:01:00Z",
        id: "01JCONVO000000000000000",
        last_message_at: "2026-06-23T00:02:00Z",
        listing_id: "01JLISTING00000000000000",
        members: [
          {
            role: "requester",
            status: "active",
            user: { id: "01JBUYER0000000000000000" },
          },
          {
            role: "recipient",
            status: "active",
            user: { id: "01JSELLER000000000000000" },
          },
        ],
        status: "active",
        unread_count: 1,
      },
    ],
    next_cursor: null,
  };
}

function sampleMessage() {
  return {
    attachments: [],
    body: "Great.",
    client_message_id: "client-1",
    conversation_id: "01JCONVO000000000000000",
    created_at: "2026-06-23T00:02:00Z",
    id: "01JMSG00000000000000000",
    listing_id: null,
    message_type: "text",
    metadata: {},
    read_by_user_ids: ["01JBUYER0000000000000000"],
    sender: { id: "01JBUYER0000000000000000" },
  };
}

function sampleNotification(status: "read" | "unread" = "unread") {
  return {
    body: "New message.",
    created_at: "2026-06-23T00:02:00Z",
    data: { conversation_id: "01JCONVO000000000000000" },
    deliveries: [
      {
        channel: "in_app",
        id: "01JDELIVERY000000000000",
        status: "pending",
      },
    ],
    id: "01JNOTIFY00000000000000",
    read_at: status === "read" ? "2026-06-23T00:03:00Z" : null,
    related_entity_id: "01JMSG00000000000000000",
    related_entity_type: "message",
    status,
    title: "New message",
    type: "message",
  };
}

function sampleNotifications() {
  return {
    items: [sampleNotification()],
    next_cursor: null,
  };
}

function sampleNotificationPreferences() {
  return {
    chat_requests_enabled: true,
    email_enabled: false,
    id: "01JPREF000000000000000",
    in_app_enabled: true,
    marketing_enabled: false,
    messages_enabled: true,
    push_enabled: true,
    quiet_hours_end: null,
    quiet_hours_start: null,
  };
}

function sampleOffer(
  status: "accepted" | "pending",
  offerType: "counter" | "price",
) {
  return {
    amount_cents: 40000,
    bundle_listing_ids: [],
    buyer: { id: "01JBUYER0000000000000000" },
    created_at: "2026-06-23T00:00:00Z",
    currency: "INR",
    exchange_items: [],
    expires_at: "2026-06-25T00:00:00Z",
    fulfillment_method: "pickup",
    id: "01JOFFER000000000000000",
    listing_id: "01JLISTING00000000000000",
    message: null,
    offer_type: offerType,
    parent_offer_id: offerType === "counter" ? "01JPARENTOFFER000000000" : null,
    proposer: { id: "01JBUYER0000000000000000" },
    quantity: 1,
    responded_at: status === "accepted" ? "2026-06-23T00:01:00Z" : null,
    seller: { id: "01JSELLER000000000000000" },
    status,
    transaction_id: status === "accepted" ? "01JTX00000000000000000" : null,
  };
}

function samplePickup(status: "confirmed" | "proposed") {
  return {
    confirmed_at: status === "confirmed" ? "2026-06-23T00:02:00Z" : null,
    confirmed_by_user_id:
      status === "confirmed" ? "01JSELLER000000000000000" : null,
    exact_address: "Library gate",
    exact_latitude: "18.520430",
    exact_longitude: "73.856744",
    handover_code: "ABC123",
    id: "01JPICKUP0000000000000",
    pickup_notes_private: "Meet near the front desk.",
    proposed_by_user_id: "01JBUYER0000000000000000",
    proposed_end_at: null,
    proposed_start_at: null,
    public_location_label: "Library gate",
    status,
    transaction_id: "01JTX00000000000000000",
  };
}

function sampleTransaction(status: "completed" | "reserved") {
  return {
    amount_cents: 40000,
    buyer: { id: "01JBUYER0000000000000000" },
    completed_at: status === "completed" ? "2026-06-23T00:05:00Z" : null,
    created_at: "2026-06-23T00:01:00Z",
    currency: "INR",
    fulfillment_method: "pickup",
    id: "01JTX00000000000000000",
    listing_id: "01JLISTING00000000000000",
    offer_id: "01JOFFER000000000000000",
    pickup: samplePickup("confirmed"),
    quantity: 1,
    seller: { id: "01JSELLER000000000000000" },
    status,
  };
}

function sampleReview() {
  return {
    comment: null,
    created_at: "2026-06-23T00:06:00Z",
    dimensions: [
      {
        dimension: "communication",
        id: "01JREVDIM0000000000000",
        rating: 5,
      },
    ],
    id: "01JREVIEW0000000000000",
    rating: 5,
    review_type: "buyer_reviews_seller",
    reviewee: { id: "01JSELLER000000000000000" },
    reviewer: { id: "01JBUYER0000000000000000" },
    status: "published",
    transaction_id: "01JTX00000000000000000",
  };
}

function sampleReport(status: "appealed" | "open") {
  return {
    case_id: "01JCASE000000000000000",
    created_at: "2026-06-24T00:00:00Z",
    description: "Trust report.",
    evidence: {},
    id: "01JREPORT0000000000000",
    reason: "scam",
    reporter: { id: "01JREPORTER000000000000" },
    severity: "high",
    status,
    target: { id: "01JUSER0000000000000000", type: "user" },
  };
}

function sampleModerationCase(status: "actioned" | "open") {
  return {
    actions:
      status === "actioned"
        ? [
            {
              action_type: "suspend",
              actor_user_id: "01JMOD0000000000000000",
              created_at: "2026-06-24T00:01:00Z",
              duration_until: null,
              evidence_snapshot: {},
              id: "01JACTION0000000000000",
              metadata: {},
              moderator_user_id: "01JMOD0000000000000000",
              reason: "Confirmed scam.",
            },
          ]
        : [],
    assigned_moderator_user_id:
      status === "actioned" ? "01JMOD0000000000000000" : null,
    created_at: "2026-06-24T00:00:00Z",
    evidence_snapshot: {},
    id: "01JCASE000000000000000",
    priority_score: 80,
    report: sampleReport("open"),
    severity: "high",
    status,
    summary: "scam report on user 01JUSER0000000000000000",
  };
}

function sampleConversationEvidence() {
  return {
    case_id: "01JCASE000000000000000",
    conversation_id: "01JCONVO000000000000000",
    messages: [
      {
        body: "Suspicious message.",
        created_at: "2026-06-24T00:00:00Z",
        id: "01JMSG0000000000000000",
        message_type: "text",
        sender_user_id: "01JUSER0000000000000000",
      },
    ],
    report_id: "01JREPORT0000000000000",
  };
}

function sampleModerationUser() {
  return {
    email: "reader@example.com",
    id: "01JUSER0000000000000000",
    report_count: 1,
    status: "active",
  };
}

function sampleModerationListing() {
  return {
    id: "01JLISTING00000000000000",
    report_count: 1,
    seller_user_id: "01JSELLER000000000000000",
    status: "active",
    title: "Godaan",
  };
}

function sampleModerationRules() {
  return {
    action_types: [
      "warn",
      "remove_content",
      "suspend",
      "ban",
      "dismiss",
      "restore",
      "note",
    ],
    moderator_roles: ["admin", "moderator", "trust_moderator"],
    severity_by_reason: {
      child_safety: "critical",
      copyright_infringement: "high",
      counterfeit: "medium",
      dangerous_meetup: "high",
      fake_listing: "medium",
      fake_review: "medium",
      harassment: "medium",
      hate_speech: "high",
      misleading_condition: "medium",
      other: "low",
      payment_fraud: "critical",
      personal_information: "high",
      piracy: "medium",
      scam: "high",
      sexual_content: "high",
      spam: "low",
      stolen_image: "medium",
    },
  };
}
