import type {
  AuthResponse,
  AuthorListResponse,
  BookClubCreateRequest,
  BookClubListResponse,
  BookClubResponse,
  BookCreateRequest,
  BookListResponse,
  BookNominationCreateRequest,
  BookNominationResponse,
  BookResponse,
  BookUpdateRequest,
  BookVoteRequest,
  BookVoteResponse,
  BuddyReadCreateRequest,
  BuddyReadProgressRequest,
  BuddyReadResponse,
  CategoryTreeResponse,
  ChatRequestActionRequest,
  ChatRequestCreateRequest,
  ChatRequestResponse,
  ClubBookCreateRequest,
  ClubBookListResponse,
  ClubBookResponse,
  CommunityApproveMemberRequest,
  CommunityCreateRequest,
  CommunityFeedResponse,
  CommunityJoinRequest,
  CommunityListResponse,
  CommunityMarketplaceResponse,
  CommunityMemberResponse,
  CommunityPostCreateRequest,
  CommunityPostResponse,
  CommunityReportCreateRequest,
  CommunityReportResponse,
  CommunityResponse,
  ConversationEvidenceResponse,
  ConversationListResponse,
  CounterOfferRequest,
  EmptyActionRequest,
  ExampleResponse,
  EventCheckinRequest,
  EventCheckinResponse,
  EventCreateRequest,
  EventListResponse,
  EventRSVPRequest,
  EventRSVPResponse,
  EventResponse,
  EventUpdateRequest,
  FollowCreateRequest,
  FollowResponse,
  HealthResponse,
  ListingFavoriteResponse,
  ListingCreateRequest,
  ListingResponse,
  ListingSearchParams,
  ListingSearchResponse,
  ListingUpdateRequest,
  LoginRequest,
  MediaAssetResponse,
  MediaUploadUrlRequest,
  MediaUploadUrlResponse,
  MessageCreateRequest,
  MessageListResponse,
  MessageReportRequest,
  MessageReportResponse,
  MessageResponse,
  ModerationActionRequest,
  ModerationCaseListResponse,
  ModerationCaseResponse,
  ModerationListingResponse,
  ModerationRuleConfigResponse,
  ModerationUserResponse,
  NotificationListResponse,
  NotificationPreferenceResponse,
  NotificationPreferenceUpdateRequest,
  NotificationResponse,
  OfferCreateRequest,
  OfferResponse,
  PickupConfirmRequest,
  PickupCreateRequest,
  PickupResponse,
  PostCommentCreateRequest,
  PostCommentResponse,
  PostReactionRequest,
  PostReactionResponse,
  ProblemDetail,
  PublisherListResponse,
  ReadalongCreateRequest,
  ReadalongResponse,
  ReadingGoalCreateRequest,
  ReadingGoalListResponse,
  ReadingGoalResponse,
  ReadingMilestoneCreateRequest,
  ReadingMilestoneListResponse,
  ReadingMilestoneResponse,
  ReadingNoteCreateRequest,
  ReadingNoteListResponse,
  ReadingNoteResponse,
  ReadingProgressListResponse,
  ReadingProgressResponse,
  ReadingProgressUpdateRequest,
  ReadingShelfCreateRequest,
  ReadingShelfItemCreateRequest,
  ReadingShelfItemResponse,
  ReadingShelfListResponse,
  ReadingShelfResponse,
  ReadingStatisticListResponse,
  ReadingStatisticRecomputeRequest,
  ReadingStatisticResponse,
  RegisterRequest,
  ReportAppealRequest,
  ReportCreateRequest,
  ReportResponse,
  ReviewCreateRequest,
  ReviewResponse,
  ResolveIsbnResponse,
  SavedSearchCreateRequest,
  SavedSearchListResponse,
  SavedSearchResponse,
  SearchSuggestionResponse,
  SelectClubBookRequest,
  TransactionCompleteRequest,
  TransactionResponse,
  UserPrivateResponse,
  UserPublicResponse,
  WishlistItemResponse,
} from "@oldpages/shared-types";
import {
  authorListResponseSchema,
  authResponseSchema,
  bookClubListResponseSchema,
  bookClubResponseSchema,
  bookListResponseSchema,
  bookNominationResponseSchema,
  bookResponseSchema,
  bookVoteResponseSchema,
  buddyReadResponseSchema,
  categoryTreeResponseSchema,
  chatRequestResponseSchema,
  clubBookListResponseSchema,
  clubBookResponseSchema,
  communityFeedResponseSchema,
  communityListResponseSchema,
  communityMarketplaceResponseSchema,
  communityMemberResponseSchema,
  communityPostResponseSchema,
  communityReportResponseSchema,
  communityResponseSchema,
  conversationEvidenceResponseSchema,
  conversationListResponseSchema,
  eventCheckinResponseSchema,
  eventListResponseSchema,
  eventResponseSchema,
  eventRSVPResponseSchema,
  exampleResponseSchema,
  healthResponseSchema,
  followResponseSchema,
  listingFavoriteResponseSchema,
  listingResponseSchema,
  listingSearchResponseSchema,
  mediaAssetResponseSchema,
  mediaUploadUrlResponseSchema,
  messageListResponseSchema,
  messageReportResponseSchema,
  messageResponseSchema,
  moderationCaseListResponseSchema,
  moderationCaseResponseSchema,
  moderationListingResponseSchema,
  moderationRuleConfigResponseSchema,
  moderationUserResponseSchema,
  notificationListResponseSchema,
  notificationPreferenceResponseSchema,
  notificationResponseSchema,
  offerResponseSchema,
  pickupResponseSchema,
  postCommentResponseSchema,
  postReactionResponseSchema,
  publisherListResponseSchema,
  readalongResponseSchema,
  readingGoalListResponseSchema,
  readingGoalResponseSchema,
  readingMilestoneListResponseSchema,
  readingMilestoneResponseSchema,
  readingNoteListResponseSchema,
  readingNoteResponseSchema,
  readingProgressListResponseSchema,
  readingProgressResponseSchema,
  readingShelfItemResponseSchema,
  readingShelfListResponseSchema,
  readingShelfResponseSchema,
  readingStatisticListResponseSchema,
  readingStatisticResponseSchema,
  reportResponseSchema,
  reviewResponseSchema,
  resolveIsbnResponseSchema,
  savedSearchListResponseSchema,
  savedSearchResponseSchema,
  searchSuggestionResponseSchema,
  transactionResponseSchema,
  userPrivateResponseSchema,
  wishlistItemResponseSchema,
} from "@oldpages/validation";

export type ApiClientOptions = {
  baseUrl: string;
  fetcher?: typeof fetch;
};

export type LocationPayload = {
  latitude: number;
  longitude: number;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  country_code?: string | null;
  postal_code?: string | null;
  display_name?: string | null;
  radius_km?: number | null;
};

export type LocationSource =
  | "browser"
  | "ip"
  | "manual"
  | "home"
  | "default"
  | "unknown";

export type DetectLocationResponse = {
  location: LocationPayload | null;
  source: LocationSource;
};

export type ActiveLocationResponse = {
  active: LocationPayload | null;
  home: LocationPayload | null;
  source: LocationSource;
};

export type GeoSearchItem = {
  display_name: string;
  latitude: number;
  longitude: number;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  country_code?: string | null;
  postal_code?: string | null;
  type?: string | null;
};

export type GeoSearchResponse = { items: GeoSearchItem[] };

export type SetActiveLocationRequest = {
  location: LocationPayload;
  persist_as_home?: boolean;
};

export function encodeLocationHeader(location: LocationPayload): string {
  const compact: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(location)) {
    if (v !== undefined && v !== null) compact[k] = v;
  }
  const json = JSON.stringify(compact);
  if (typeof btoa !== "undefined") {
    return btoa(unescape(encodeURIComponent(json)))
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");
  }
  return Buffer.from(json, "utf-8").toString("base64url");
}

export class ApiClientError extends Error {
  readonly problem?: ProblemDetail;
  readonly status: number;

  constructor(message: string, status: number, problem?: ProblemDetail) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.problem = problem;
  }
}

export class OldPagesApiClient {
  private readonly baseUrl: URL;
  private readonly fetcher: typeof fetch;

  constructor(options: ApiClientOptions) {
    this.baseUrl = new URL(options.baseUrl);
    this.fetcher = options.fetcher ?? fetch;
  }

  async getLiveHealth(): Promise<HealthResponse> {
    const payload = await this.request<unknown>("/health/live");
    return healthResponseSchema.parse(payload);
  }

  async getReadiness(): Promise<HealthResponse> {
    const payload = await this.request<unknown>("/health/ready");
    return healthResponseSchema.parse(payload);
  }

  async getFoundationExample(): Promise<ExampleResponse> {
    const payload = await this.request<unknown>("/api/v1/foundation/example");
    return exampleResponseSchema.parse(payload);
  }

  async register(payload: RegisterRequest): Promise<AuthResponse> {
    const response = await this.request<unknown>("/api/v1/auth/register", {
      body: JSON.stringify(payload),
      method: "POST",
    });
    return authResponseSchema.parse(response);
  }

  async login(payload: LoginRequest): Promise<AuthResponse> {
    const response = await this.request<unknown>("/api/v1/auth/login", {
      body: JSON.stringify(payload),
      method: "POST",
    });
    return authResponseSchema.parse(response);
  }

  async refresh(refreshToken: string): Promise<AuthResponse> {
    const response = await this.request<unknown>("/api/v1/auth/refresh", {
      body: JSON.stringify({ refresh_token: refreshToken }),
      method: "POST",
    });
    return authResponseSchema.parse(response);
  }

  async getMe(accessToken: string): Promise<UserPrivateResponse> {
    const response = await this.request<unknown>("/api/v1/users/me", {
      accessToken,
    });
    return userPrivateResponseSchema.parse(response);
  }

  async listBooks(
    params: {
      author?: string | null;
      category?: string | null;
      cursor?: string | null;
      isbn?: string | null;
      language?: string | null;
      limit?: number | null;
      publisher?: string | null;
      query?: string | null;
    } = {},
  ): Promise<BookListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/books${queryString(params)}`,
    );
    return bookListResponseSchema.parse(response) as BookListResponse;
  }

  async getBook(bookId: string): Promise<BookResponse> {
    const response = await this.request<unknown>(
      `/api/v1/books/${encodeURIComponent(bookId)}`,
    );
    return bookResponseSchema.parse(response);
  }

  async createBook(
    payload: BookCreateRequest,
    accessToken: string,
  ): Promise<BookResponse> {
    const response = await this.request<unknown>("/api/v1/books", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return bookResponseSchema.parse(response);
  }

  async updateBook(
    bookId: string,
    payload: BookUpdateRequest,
    accessToken: string,
  ): Promise<BookResponse> {
    const response = await this.request<unknown>(
      `/api/v1/books/${encodeURIComponent(bookId)}`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "PATCH",
      },
    );
    return bookResponseSchema.parse(response);
  }

  async resolveIsbn(isbn: string): Promise<ResolveIsbnResponse> {
    const response = await this.request<unknown>("/api/v1/books/resolve-isbn", {
      body: JSON.stringify({ isbn }),
      method: "POST",
    });
    return resolveIsbnResponseSchema.parse(response) as ResolveIsbnResponse;
  }

  async listCategories(): Promise<CategoryTreeResponse> {
    const response = await this.request<unknown>("/api/v1/categories");
    return categoryTreeResponseSchema.parse(response) as CategoryTreeResponse;
  }

  async listAuthors(
    params: {
      cursor?: string | null;
      limit?: number | null;
      query?: string | null;
    } = {},
  ): Promise<AuthorListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/authors${queryString(params)}`,
    );
    return authorListResponseSchema.parse(response);
  }

  async listPublishers(
    params: {
      cursor?: string | null;
      limit?: number | null;
      query?: string | null;
    } = {},
  ): Promise<PublisherListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/publishers${queryString(params)}`,
    );
    return publisherListResponseSchema.parse(response);
  }

  async requestMediaUploadUrl(
    payload: MediaUploadUrlRequest,
    accessToken: string,
  ): Promise<MediaUploadUrlResponse> {
    const response = await this.request<unknown>("/api/v1/media/upload-url", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return mediaUploadUrlResponseSchema.parse(
      response,
    ) as MediaUploadUrlResponse;
  }

  async completeMediaUpload(
    mediaId: string,
    payload: { byte_size?: number | null; checksum_sha256?: string | null },
    accessToken: string,
  ): Promise<MediaAssetResponse> {
    const response = await this.request<unknown>(
      `/api/v1/media/${encodeURIComponent(mediaId)}/complete`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return mediaAssetResponseSchema.parse(response) as MediaAssetResponse;
  }

  async createListing(
    payload: ListingCreateRequest,
    accessToken: string,
  ): Promise<ListingResponse> {
    const response = await this.request<unknown>("/api/v1/listings", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return listingResponseSchema.parse(response) as ListingResponse;
  }

  async getListing(listingId: string): Promise<ListingResponse> {
    const response = await this.request<unknown>(
      `/api/v1/listings/${encodeURIComponent(listingId)}`,
    );
    return listingResponseSchema.parse(response) as ListingResponse;
  }

  async updateListing(
    listingId: string,
    payload: ListingUpdateRequest,
    accessToken: string,
  ): Promise<ListingResponse> {
    const response = await this.request<unknown>(
      `/api/v1/listings/${encodeURIComponent(listingId)}`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "PATCH",
      },
    );
    return listingResponseSchema.parse(response) as ListingResponse;
  }

  async publishListing(
    listingId: string,
    accessToken: string,
  ): Promise<ListingResponse> {
    return this.postListingTransition(listingId, "publish", accessToken);
  }

  async pauseListing(
    listingId: string,
    accessToken: string,
  ): Promise<ListingResponse> {
    return this.postListingTransition(listingId, "pause", accessToken);
  }

  async relistListing(
    listingId: string,
    accessToken: string,
  ): Promise<ListingResponse> {
    return this.postListingTransition(listingId, "relist", accessToken);
  }

  async deleteListing(listingId: string, accessToken: string): Promise<void> {
    await this.request<unknown>(
      `/api/v1/listings/${encodeURIComponent(listingId)}`,
      {
        accessToken,
        method: "DELETE",
      },
    );
  }

  async searchListings(
    params: ListingSearchParams = {},
    accessToken?: string,
    headers?: Record<string, string>,
  ): Promise<ListingSearchResponse> {
    const response = await this.request<unknown>(
      `/api/v1/search/listings${queryString(params)}`,
      { accessToken, headers },
    );
    return listingSearchResponseSchema.parse(response) as ListingSearchResponse;
  }

  async getSearchSuggestions(
    q: string,
    params: { limit?: number | null } = {},
  ): Promise<SearchSuggestionResponse> {
    const response = await this.request<unknown>(
      `/api/v1/search/suggestions${queryString({ q, ...params })}`,
    );
    return searchSuggestionResponseSchema.parse(
      response,
    ) as SearchSuggestionResponse;
  }

  async createSavedSearch(
    payload: SavedSearchCreateRequest,
    accessToken: string,
  ): Promise<SavedSearchResponse> {
    const response = await this.request<unknown>("/api/v1/saved-searches", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return savedSearchResponseSchema.parse(response) as SavedSearchResponse;
  }

  async listSavedSearches(
    accessToken: string,
  ): Promise<SavedSearchListResponse> {
    const response = await this.request<unknown>("/api/v1/saved-searches", {
      accessToken,
    });
    return savedSearchListResponseSchema.parse(
      response,
    ) as SavedSearchListResponse;
  }

  async addWishlistItem(
    bookId: string,
    accessToken: string,
  ): Promise<WishlistItemResponse> {
    const response = await this.request<unknown>(
      `/api/v1/wishlists/${encodeURIComponent(bookId)}`,
      {
        accessToken,
        method: "POST",
      },
    );
    return wishlistItemResponseSchema.parse(response) as WishlistItemResponse;
  }

  async deleteWishlistItem(bookId: string, accessToken: string): Promise<void> {
    await this.request<unknown>(
      `/api/v1/wishlists/${encodeURIComponent(bookId)}`,
      {
        accessToken,
        method: "DELETE",
      },
    );
  }

  async favoriteListing(
    listingId: string,
    accessToken: string,
  ): Promise<ListingFavoriteResponse> {
    const response = await this.request<unknown>(
      `/api/v1/listings/${encodeURIComponent(listingId)}/favorite`,
      {
        accessToken,
        method: "POST",
      },
    );
    return listingFavoriteResponseSchema.parse(
      response,
    ) as ListingFavoriteResponse;
  }

  async unfavoriteListing(
    listingId: string,
    accessToken: string,
  ): Promise<void> {
    await this.request<unknown>(
      `/api/v1/listings/${encodeURIComponent(listingId)}/favorite`,
      {
        accessToken,
        method: "DELETE",
      },
    );
  }

  async createFollow(
    payload: FollowCreateRequest,
    accessToken: string,
  ): Promise<FollowResponse> {
    const response = await this.request<unknown>("/api/v1/follows", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return followResponseSchema.parse(response) as FollowResponse;
  }

  async deleteFollow(followId: string, accessToken: string): Promise<void> {
    await this.request<unknown>(
      `/api/v1/follows/${encodeURIComponent(followId)}`,
      {
        accessToken,
        method: "DELETE",
      },
    );
  }

  async createChatRequest(
    payload: ChatRequestCreateRequest,
    accessToken: string,
  ): Promise<ChatRequestResponse> {
    const response = await this.request<unknown>("/api/v1/chat-requests", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return chatRequestResponseSchema.parse(response) as ChatRequestResponse;
  }

  async acceptChatRequest(
    requestId: string,
    payload: ChatRequestActionRequest,
    accessToken: string,
  ): Promise<ChatRequestResponse> {
    return this.postChatRequestAction(
      requestId,
      "accept",
      payload,
      accessToken,
    );
  }

  async declineChatRequest(
    requestId: string,
    payload: ChatRequestActionRequest,
    accessToken: string,
  ): Promise<ChatRequestResponse> {
    return this.postChatRequestAction(
      requestId,
      "decline",
      payload,
      accessToken,
    );
  }

  async blockChatRequest(
    requestId: string,
    payload: ChatRequestActionRequest,
    accessToken: string,
  ): Promise<ChatRequestResponse> {
    return this.postChatRequestAction(requestId, "block", payload, accessToken);
  }

  async listConversations(
    accessToken: string,
    params: { cursor?: string | null; limit?: number | null } = {},
  ): Promise<ConversationListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/conversations${queryString(params)}`,
      { accessToken },
    );
    return conversationListResponseSchema.parse(
      response,
    ) as ConversationListResponse;
  }

  async listConversationMessages(
    conversationId: string,
    accessToken: string,
    params: { cursor?: string | null; limit?: number | null } = {},
  ): Promise<MessageListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/conversations/${encodeURIComponent(conversationId)}/messages${queryString(params)}`,
      { accessToken },
    );
    return messageListResponseSchema.parse(response) as MessageListResponse;
  }

  async sendConversationMessage(
    conversationId: string,
    payload: MessageCreateRequest,
    accessToken: string,
  ): Promise<MessageResponse> {
    const response = await this.request<unknown>(
      `/api/v1/conversations/${encodeURIComponent(conversationId)}/messages`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return messageResponseSchema.parse(response) as MessageResponse;
  }

  async reportMessage(
    messageId: string,
    payload: MessageReportRequest,
    accessToken: string,
  ): Promise<MessageReportResponse> {
    const response = await this.request<unknown>(
      `/api/v1/conversations/messages/${encodeURIComponent(messageId)}/report`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return messageReportResponseSchema.parse(response) as MessageReportResponse;
  }

  async listNotifications(
    accessToken: string,
    params: { cursor?: string | null; limit?: number | null } = {},
  ): Promise<NotificationListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/notifications${queryString(params)}`,
      { accessToken },
    );
    return notificationListResponseSchema.parse(
      response,
    ) as NotificationListResponse;
  }

  async markNotificationRead(
    notificationId: string,
    accessToken: string,
  ): Promise<NotificationResponse> {
    const response = await this.request<unknown>(
      `/api/v1/notifications/${encodeURIComponent(notificationId)}/read`,
      {
        accessToken,
        method: "POST",
      },
    );
    return notificationResponseSchema.parse(response) as NotificationResponse;
  }

  async getNotificationPreferences(
    accessToken: string,
  ): Promise<NotificationPreferenceResponse> {
    const response = await this.request<unknown>(
      "/api/v1/notification-preferences",
      { accessToken },
    );
    return notificationPreferenceResponseSchema.parse(
      response,
    ) as NotificationPreferenceResponse;
  }

  async updateNotificationPreferences(
    payload: NotificationPreferenceUpdateRequest,
    accessToken: string,
  ): Promise<NotificationPreferenceResponse> {
    const response = await this.request<unknown>(
      "/api/v1/notification-preferences",
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "PATCH",
      },
    );
    return notificationPreferenceResponseSchema.parse(
      response,
    ) as NotificationPreferenceResponse;
  }

  async createOffer(
    payload: OfferCreateRequest,
    accessToken: string,
  ): Promise<OfferResponse> {
    const response = await this.request<unknown>("/api/v1/offers", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return offerResponseSchema.parse(response) as OfferResponse;
  }

  async counterOffer(
    offerId: string,
    payload: CounterOfferRequest,
    accessToken: string,
  ): Promise<OfferResponse> {
    const response = await this.request<unknown>(
      `/api/v1/offers/${encodeURIComponent(offerId)}/counter`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return offerResponseSchema.parse(response) as OfferResponse;
  }

  async acceptOffer(
    offerId: string,
    payload: EmptyActionRequest,
    accessToken: string,
  ): Promise<OfferResponse> {
    return this.postOfferAction(offerId, "accept", payload, accessToken);
  }

  async rejectOffer(
    offerId: string,
    payload: EmptyActionRequest,
    accessToken: string,
  ): Promise<OfferResponse> {
    return this.postOfferAction(offerId, "reject", payload, accessToken);
  }

  async withdrawOffer(
    offerId: string,
    payload: EmptyActionRequest,
    accessToken: string,
  ): Promise<OfferResponse> {
    return this.postOfferAction(offerId, "withdraw", payload, accessToken);
  }

  async createPickup(
    payload: PickupCreateRequest,
    accessToken: string,
  ): Promise<PickupResponse> {
    const response = await this.request<unknown>("/api/v1/pickups", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return pickupResponseSchema.parse(response) as PickupResponse;
  }

  async confirmPickup(
    pickupId: string,
    payload: PickupConfirmRequest,
    accessToken: string,
  ): Promise<PickupResponse> {
    const response = await this.request<unknown>(
      `/api/v1/pickups/${encodeURIComponent(pickupId)}/confirm`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return pickupResponseSchema.parse(response) as PickupResponse;
  }

  async completeTransaction(
    transactionId: string,
    payload: TransactionCompleteRequest,
    accessToken: string,
  ): Promise<TransactionResponse> {
    const response = await this.request<unknown>(
      `/api/v1/transactions/${encodeURIComponent(transactionId)}/complete`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return transactionResponseSchema.parse(response) as TransactionResponse;
  }

  async createReview(
    payload: ReviewCreateRequest,
    accessToken: string,
  ): Promise<ReviewResponse> {
    const response = await this.request<unknown>("/api/v1/reviews", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return reviewResponseSchema.parse(response) as ReviewResponse;
  }

  async createReport(
    payload: ReportCreateRequest,
    accessToken: string,
  ): Promise<ReportResponse> {
    const response = await this.request<unknown>("/api/v1/reports", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return reportResponseSchema.parse(response) as ReportResponse;
  }

  async appealReport(
    reportId: string,
    payload: ReportAppealRequest,
    accessToken: string,
  ): Promise<ReportResponse> {
    const response = await this.request<unknown>(
      `/api/v1/reports/${encodeURIComponent(reportId)}/appeal`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return reportResponseSchema.parse(response) as ReportResponse;
  }

  async listModerationCases(
    accessToken: string,
    params: {
      cursor?: string | null;
      limit?: number | null;
      status?: string | null;
    } = {},
  ): Promise<ModerationCaseListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/admin/moderation/cases${queryString(params)}`,
      { accessToken },
    );
    return moderationCaseListResponseSchema.parse(
      response,
    ) as ModerationCaseListResponse;
  }

  async getModerationCase(
    caseId: string,
    accessToken: string,
  ): Promise<ModerationCaseResponse> {
    const response = await this.request<unknown>(
      `/api/v1/admin/moderation/cases/${encodeURIComponent(caseId)}`,
      { accessToken },
    );
    return moderationCaseResponseSchema.parse(
      response,
    ) as ModerationCaseResponse;
  }

  async takeModerationAction(
    caseId: string,
    payload: ModerationActionRequest,
    accessToken: string,
  ): Promise<ModerationCaseResponse> {
    const response = await this.request<unknown>(
      `/api/v1/admin/moderation/cases/${encodeURIComponent(caseId)}/actions`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return moderationCaseResponseSchema.parse(
      response,
    ) as ModerationCaseResponse;
  }

  async getConversationEvidence(
    caseId: string,
    accessToken: string,
  ): Promise<ConversationEvidenceResponse> {
    const response = await this.request<unknown>(
      `/api/v1/admin/moderation/cases/${encodeURIComponent(caseId)}/conversation-evidence`,
      { accessToken },
    );
    return conversationEvidenceResponseSchema.parse(
      response,
    ) as ConversationEvidenceResponse;
  }

  async getModerationUser(
    userId: string,
    accessToken: string,
  ): Promise<ModerationUserResponse> {
    const response = await this.request<unknown>(
      `/api/v1/admin/moderation/users/${encodeURIComponent(userId)}`,
      { accessToken },
    );
    return moderationUserResponseSchema.parse(
      response,
    ) as ModerationUserResponse;
  }

  async getModerationListing(
    listingId: string,
    accessToken: string,
  ): Promise<ModerationListingResponse> {
    const response = await this.request<unknown>(
      `/api/v1/admin/moderation/listings/${encodeURIComponent(listingId)}`,
      { accessToken },
    );
    return moderationListingResponseSchema.parse(
      response,
    ) as ModerationListingResponse;
  }

  async getModerationRules(
    accessToken: string,
  ): Promise<ModerationRuleConfigResponse> {
    const response = await this.request<unknown>(
      "/api/v1/admin/moderation/rules",
      { accessToken },
    );
    return moderationRuleConfigResponseSchema.parse(
      response,
    ) as ModerationRuleConfigResponse;
  }

  async createCommunity(
    payload: CommunityCreateRequest,
    accessToken: string,
  ): Promise<CommunityResponse> {
    const response = await this.request<unknown>("/api/v1/communities", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return communityResponseSchema.parse(response) as CommunityResponse;
  }

  async listCommunities(
    params: {
      book_id?: string | null;
      city?: string | null;
      country?: string | null;
      cursor?: string | null;
      genre?: string | null;
      institution?: string | null;
      limit?: number | null;
    } = {},
    accessToken?: string,
  ): Promise<CommunityListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/communities${queryString(params)}`,
      { accessToken },
    );
    return communityListResponseSchema.parse(response) as CommunityListResponse;
  }

  async getCommunity(
    communityId: string,
    accessToken?: string,
  ): Promise<CommunityResponse> {
    const response = await this.request<unknown>(
      `/api/v1/communities/${encodeURIComponent(communityId)}`,
      { accessToken },
    );
    return communityResponseSchema.parse(response) as CommunityResponse;
  }

  async joinCommunity(
    communityId: string,
    payload: CommunityJoinRequest,
    accessToken: string,
  ): Promise<CommunityMemberResponse> {
    const response = await this.request<unknown>(
      `/api/v1/communities/${encodeURIComponent(communityId)}/join`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return communityMemberResponseSchema.parse(
      response,
    ) as CommunityMemberResponse;
  }

  async approveCommunityMember(
    communityId: string,
    payload: CommunityApproveMemberRequest,
    accessToken: string,
  ): Promise<CommunityMemberResponse> {
    const response = await this.request<unknown>(
      `/api/v1/communities/${encodeURIComponent(communityId)}/approve-member`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return communityMemberResponseSchema.parse(
      response,
    ) as CommunityMemberResponse;
  }

  async createCommunityPost(
    communityId: string,
    payload: CommunityPostCreateRequest,
    accessToken: string,
  ): Promise<CommunityPostResponse> {
    const response = await this.request<unknown>(
      `/api/v1/communities/${encodeURIComponent(communityId)}/posts`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return communityPostResponseSchema.parse(response) as CommunityPostResponse;
  }

  async getCommunityFeed(
    communityId: string,
    params: { cursor?: string | null; limit?: number | null } = {},
    accessToken?: string,
  ): Promise<CommunityFeedResponse> {
    const response = await this.request<unknown>(
      `/api/v1/communities/${encodeURIComponent(communityId)}/feed${queryString(params)}`,
      { accessToken },
    );
    return communityFeedResponseSchema.parse(response) as CommunityFeedResponse;
  }

  async getCommunityMarketplace(
    communityId: string,
    params: { cursor?: string | null; limit?: number | null } = {},
    accessToken?: string,
  ): Promise<CommunityMarketplaceResponse> {
    const response = await this.request<unknown>(
      `/api/v1/communities/${encodeURIComponent(communityId)}/marketplace${queryString(params)}`,
      { accessToken },
    );
    return communityMarketplaceResponseSchema.parse(
      response,
    ) as CommunityMarketplaceResponse;
  }

  async createCommunityReport(
    communityId: string,
    payload: CommunityReportCreateRequest,
    accessToken: string,
  ): Promise<CommunityReportResponse> {
    const response = await this.request<unknown>(
      `/api/v1/communities/${encodeURIComponent(communityId)}/reports`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return communityReportResponseSchema.parse(
      response,
    ) as CommunityReportResponse;
  }

  async createClub(
    payload: BookClubCreateRequest,
    accessToken: string,
  ): Promise<BookClubResponse> {
    const response = await this.request<unknown>("/api/v1/clubs", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return bookClubResponseSchema.parse(response) as BookClubResponse;
  }

  async listClubs(
    params: {
      community_id?: string | null;
      cursor?: string | null;
      limit?: number | null;
    } = {},
    accessToken?: string,
  ): Promise<BookClubListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/clubs${queryString(params)}`,
      { accessToken },
    );
    return bookClubListResponseSchema.parse(response) as BookClubListResponse;
  }

  async getClub(
    clubId: string,
    accessToken?: string,
  ): Promise<BookClubResponse> {
    const response = await this.request<unknown>(
      `/api/v1/clubs/${encodeURIComponent(clubId)}`,
      { accessToken },
    );
    return bookClubResponseSchema.parse(response) as BookClubResponse;
  }

  async addClubBook(
    clubId: string,
    payload: ClubBookCreateRequest,
    accessToken: string,
  ): Promise<ClubBookResponse> {
    const response = await this.request<unknown>(
      `/api/v1/clubs/${encodeURIComponent(clubId)}/books`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return clubBookResponseSchema.parse(response) as ClubBookResponse;
  }

  async listClubBooks(
    clubId: string,
    accessToken?: string,
  ): Promise<ClubBookListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/clubs/${encodeURIComponent(clubId)}/books`,
      { accessToken },
    );
    return clubBookListResponseSchema.parse(response) as ClubBookListResponse;
  }

  async createBookNomination(
    clubId: string,
    payload: BookNominationCreateRequest,
    accessToken: string,
  ): Promise<BookNominationResponse> {
    const response = await this.request<unknown>(
      `/api/v1/clubs/${encodeURIComponent(clubId)}/nominations`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return bookNominationResponseSchema.parse(
      response,
    ) as BookNominationResponse;
  }

  async castBookVote(
    clubId: string,
    payload: BookVoteRequest,
    accessToken: string,
  ): Promise<BookVoteResponse> {
    const response = await this.request<unknown>(
      `/api/v1/clubs/${encodeURIComponent(clubId)}/votes`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return bookVoteResponseSchema.parse(response) as BookVoteResponse;
  }

  async selectClubBook(
    clubId: string,
    payload: SelectClubBookRequest,
    accessToken: string,
  ): Promise<ClubBookResponse> {
    const response = await this.request<unknown>(
      `/api/v1/clubs/${encodeURIComponent(clubId)}/select-book`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return clubBookResponseSchema.parse(response) as ClubBookResponse;
  }

  async createReadingMilestone(
    clubBookId: string,
    payload: ReadingMilestoneCreateRequest,
    accessToken: string,
  ): Promise<ReadingMilestoneResponse> {
    const response = await this.request<unknown>(
      `/api/v1/club-books/${encodeURIComponent(clubBookId)}/milestones`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return readingMilestoneResponseSchema.parse(
      response,
    ) as ReadingMilestoneResponse;
  }

  async listReadingMilestones(
    clubBookId: string,
    params: {
      finished?: boolean | null;
      progress_type?: string | null;
      progress_value?: number | null;
    } = {},
    accessToken?: string,
  ): Promise<ReadingMilestoneListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/club-books/${encodeURIComponent(clubBookId)}/milestones${queryString(params)}`,
      { accessToken },
    );
    return readingMilestoneListResponseSchema.parse(
      response,
    ) as ReadingMilestoneListResponse;
  }

  async createBuddyRead(
    payload: BuddyReadCreateRequest,
    accessToken: string,
  ): Promise<BuddyReadResponse> {
    const response = await this.request<unknown>("/api/v1/buddy-reads", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return buddyReadResponseSchema.parse(response) as BuddyReadResponse;
  }

  async joinBuddyRead(
    buddyReadId: string,
    accessToken: string,
  ): Promise<BuddyReadResponse> {
    const response = await this.request<unknown>(
      `/api/v1/buddy-reads/${encodeURIComponent(buddyReadId)}/join`,
      {
        accessToken,
        method: "POST",
      },
    );
    return buddyReadResponseSchema.parse(response) as BuddyReadResponse;
  }

  async updateBuddyReadProgress(
    buddyReadId: string,
    payload: BuddyReadProgressRequest,
    accessToken: string,
  ): Promise<BuddyReadResponse> {
    const response = await this.request<unknown>(
      `/api/v1/buddy-reads/${encodeURIComponent(buddyReadId)}/progress`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return buddyReadResponseSchema.parse(response) as BuddyReadResponse;
  }

  async createReadalong(
    payload: ReadalongCreateRequest,
    accessToken: string,
  ): Promise<ReadalongResponse> {
    const response = await this.request<unknown>("/api/v1/readalongs", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return readalongResponseSchema.parse(response) as ReadalongResponse;
  }

  async createEvent(
    payload: EventCreateRequest,
    accessToken: string,
  ): Promise<EventResponse> {
    const response = await this.request<unknown>("/api/v1/events", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return eventResponseSchema.parse(response) as EventResponse;
  }

  async listEvents(
    params: {
      club_id?: string | null;
      community_id?: string | null;
      cursor?: string | null;
      limit?: number | null;
    } = {},
    accessToken?: string,
  ): Promise<EventListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/events${queryString(params)}`,
      { accessToken },
    );
    return eventListResponseSchema.parse(response) as EventListResponse;
  }

  async getEvent(
    eventId: string,
    accessToken?: string,
  ): Promise<EventResponse> {
    const response = await this.request<unknown>(
      `/api/v1/events/${encodeURIComponent(eventId)}`,
      { accessToken },
    );
    return eventResponseSchema.parse(response) as EventResponse;
  }

  async updateEvent(
    eventId: string,
    payload: EventUpdateRequest,
    accessToken: string,
  ): Promise<EventResponse> {
    const response = await this.request<unknown>(
      `/api/v1/events/${encodeURIComponent(eventId)}`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "PATCH",
      },
    );
    return eventResponseSchema.parse(response) as EventResponse;
  }

  async createEventRsvp(
    eventId: string,
    payload: EventRSVPRequest,
    accessToken: string,
  ): Promise<EventRSVPResponse> {
    const response = await this.request<unknown>(
      `/api/v1/events/${encodeURIComponent(eventId)}/rsvps`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return eventRSVPResponseSchema.parse(response) as EventRSVPResponse;
  }

  async cancelEventRsvp(
    eventId: string,
    accessToken: string,
  ): Promise<EventRSVPResponse> {
    const response = await this.request<unknown>(
      `/api/v1/events/${encodeURIComponent(eventId)}/rsvps/cancel`,
      {
        accessToken,
        method: "POST",
      },
    );
    return eventRSVPResponseSchema.parse(response) as EventRSVPResponse;
  }

  async createEventCheckin(
    eventId: string,
    payload: EventCheckinRequest,
    accessToken: string,
  ): Promise<EventCheckinResponse> {
    const response = await this.request<unknown>(
      `/api/v1/events/${encodeURIComponent(eventId)}/checkins`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return eventCheckinResponseSchema.parse(response) as EventCheckinResponse;
  }

  async getEventCalendar(
    eventId: string,
    accessToken?: string,
  ): Promise<string> {
    return await this.requestText(
      `/api/v1/events/${encodeURIComponent(eventId)}/calendar.ics`,
      { accessToken },
    );
  }

  async createReadingShelf(
    payload: ReadingShelfCreateRequest,
    accessToken: string,
  ): Promise<ReadingShelfResponse> {
    const response = await this.request<unknown>("/api/v1/reading/shelves", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return readingShelfResponseSchema.parse(response) as ReadingShelfResponse;
  }

  async listMyReadingShelves(
    accessToken: string,
  ): Promise<ReadingShelfListResponse> {
    const response = await this.request<unknown>("/api/v1/reading/shelves", {
      accessToken,
    });
    return readingShelfListResponseSchema.parse(
      response,
    ) as ReadingShelfListResponse;
  }

  async listUserReadingShelves(
    userId: string,
    accessToken?: string,
  ): Promise<ReadingShelfListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/users/${encodeURIComponent(userId)}/shelves`,
      { accessToken },
    );
    return readingShelfListResponseSchema.parse(
      response,
    ) as ReadingShelfListResponse;
  }

  async addReadingShelfItem(
    shelfId: string,
    payload: ReadingShelfItemCreateRequest,
    accessToken: string,
  ): Promise<ReadingShelfItemResponse> {
    const response = await this.request<unknown>(
      `/api/v1/reading/shelves/${encodeURIComponent(shelfId)}/items`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return readingShelfItemResponseSchema.parse(
      response,
    ) as ReadingShelfItemResponse;
  }

  async removeReadingShelfItem(
    shelfId: string,
    bookId: string,
    accessToken: string,
  ): Promise<void> {
    await this.request<void>(
      `/api/v1/reading/shelves/${encodeURIComponent(shelfId)}/items/${encodeURIComponent(bookId)}`,
      {
        accessToken,
        method: "DELETE",
      },
    );
  }

  async updateReadingProgress(
    bookId: string,
    payload: ReadingProgressUpdateRequest,
    accessToken: string,
  ): Promise<ReadingProgressResponse> {
    const response = await this.request<unknown>(
      `/api/v1/reading/progress/${encodeURIComponent(bookId)}`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "PUT",
      },
    );
    return readingProgressResponseSchema.parse(
      response,
    ) as ReadingProgressResponse;
  }

  async listReadingProgress(
    accessToken: string,
  ): Promise<ReadingProgressListResponse> {
    const response = await this.request<unknown>("/api/v1/reading/progress", {
      accessToken,
    });
    return readingProgressListResponseSchema.parse(
      response,
    ) as ReadingProgressListResponse;
  }

  async createReadingNote(
    payload: ReadingNoteCreateRequest,
    accessToken: string,
  ): Promise<ReadingNoteResponse> {
    const response = await this.request<unknown>("/api/v1/reading/notes", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return readingNoteResponseSchema.parse(response) as ReadingNoteResponse;
  }

  async listReadingNotes(
    accessToken: string,
    params: { book_id?: string | null } = {},
  ): Promise<ReadingNoteListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/reading/notes${queryString(params)}`,
      { accessToken },
    );
    return readingNoteListResponseSchema.parse(
      response,
    ) as ReadingNoteListResponse;
  }

  async listUserReadingNotes(
    userId: string,
    params: { book_id?: string | null } = {},
  ): Promise<ReadingNoteListResponse> {
    const response = await this.request<unknown>(
      `/api/v1/users/${encodeURIComponent(userId)}/reading-notes${queryString(params)}`,
    );
    return readingNoteListResponseSchema.parse(
      response,
    ) as ReadingNoteListResponse;
  }

  async createReadingGoal(
    payload: ReadingGoalCreateRequest,
    accessToken: string,
  ): Promise<ReadingGoalResponse> {
    const response = await this.request<unknown>("/api/v1/reading/goals", {
      accessToken,
      body: JSON.stringify(payload),
      method: "POST",
    });
    return readingGoalResponseSchema.parse(response) as ReadingGoalResponse;
  }

  async listReadingGoals(
    accessToken: string,
  ): Promise<ReadingGoalListResponse> {
    const response = await this.request<unknown>("/api/v1/reading/goals", {
      accessToken,
    });
    return readingGoalListResponseSchema.parse(
      response,
    ) as ReadingGoalListResponse;
  }

  async recomputeReadingStatistics(
    payload: ReadingStatisticRecomputeRequest,
    accessToken: string,
  ): Promise<ReadingStatisticResponse> {
    const response = await this.request<unknown>(
      "/api/v1/reading/statistics/recompute",
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return readingStatisticResponseSchema.parse(
      response,
    ) as ReadingStatisticResponse;
  }

  async listReadingStatistics(
    accessToken: string,
  ): Promise<ReadingStatisticListResponse> {
    const response = await this.request<unknown>("/api/v1/reading/statistics", {
      accessToken,
    });
    return readingStatisticListResponseSchema.parse(
      response,
    ) as ReadingStatisticListResponse;
  }

  async createPostComment(
    postId: string,
    payload: PostCommentCreateRequest,
    accessToken: string,
  ): Promise<PostCommentResponse> {
    const response = await this.request<unknown>(
      `/api/v1/posts/${encodeURIComponent(postId)}/comments`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return postCommentResponseSchema.parse(response) as PostCommentResponse;
  }

  async setPostReaction(
    postId: string,
    payload: PostReactionRequest,
    accessToken: string,
  ): Promise<PostReactionResponse> {
    const response = await this.request<unknown>(
      `/api/v1/posts/${encodeURIComponent(postId)}/reactions`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return postReactionResponseSchema.parse(response) as PostReactionResponse;
  }

  async listTransactions(
    accessToken: string,
    params: { role?: "buyer" | "seller"; status?: string; limit?: number; cursor?: string } = {},
  ): Promise<{ items: TransactionResponse[]; next_cursor: string | null }> {
    const response = await this.request<unknown>(
      `/api/v1/orders${queryString({ ...params })}`,
      { accessToken },
    );
    return response as { items: TransactionResponse[]; next_cursor: string | null };
  }

  async getTransaction(
    transactionId: string,
    accessToken: string,
  ): Promise<TransactionResponse> {
    const response = await this.request<unknown>(
      `/api/v1/orders/${encodeURIComponent(transactionId)}`,
      { accessToken },
    );
    return response as TransactionResponse;
  }

  async getUser(
    userId: string,
    accessToken?: string,
  ): Promise<UserPublicResponse> {
    const response = await this.request<unknown>(
      `/api/v1/users/${encodeURIComponent(userId)}`,
      { accessToken },
    );
    return response as UserPublicResponse;
  }

  async detectLocation(): Promise<DetectLocationResponse> {
    return (await this.request<unknown>("/api/v1/geo/detect")) as DetectLocationResponse;
  }

  async searchPlaces(
    q: string,
    params: { limit?: number | null; cc?: string | null } = {},
  ): Promise<GeoSearchResponse> {
    return (await this.request<unknown>(
      `/api/v1/geo/search${queryString({ q, ...params })}`,
    )) as GeoSearchResponse;
  }

  async reverseGeocode(
    latitude: number,
    longitude: number,
  ): Promise<LocationPayload | null> {
    return (await this.request<unknown>(
      `/api/v1/geo/reverse${queryString({ latitude, longitude })}`,
    )) as LocationPayload | null;
  }

  async lookupPincode(
    pincode: string,
    countryCode: string = "IN",
  ): Promise<LocationPayload | null> {
    return (await this.request<unknown>(
      `/api/v1/geo/pincode/${encodeURIComponent(pincode)}${queryString({ cc: countryCode })}`,
    )) as LocationPayload | null;
  }

  async getMyLocation(
    accessToken?: string,
    location?: LocationPayload | null,
  ): Promise<ActiveLocationResponse> {
    return (await this.request<unknown>("/api/v1/me/location", {
      accessToken,
      headers: location ? { "X-User-Location": encodeLocationHeader(location) } : undefined,
    })) as ActiveLocationResponse;
  }

  async setActiveLocation(
    payload: SetActiveLocationRequest,
    accessToken?: string,
  ): Promise<ActiveLocationResponse> {
    return (await this.request<unknown>("/api/v1/me/location/active", {
      accessToken,
      body: JSON.stringify(payload),
      method: "PUT",
    })) as ActiveLocationResponse;
  }

  async setHomeLocation(
    payload: LocationPayload,
    accessToken: string,
  ): Promise<LocationPayload> {
    return (await this.request<unknown>("/api/v1/me/location/home", {
      accessToken,
      body: JSON.stringify(payload),
      method: "PUT",
    })) as LocationPayload;
  }

  async clearActiveLocation(accessToken?: string): Promise<void> {
    await this.request<void>("/api/v1/me/location/active", {
      accessToken,
      method: "DELETE",
    });
  }

  private async postListingTransition(
    listingId: string,
    transition: "pause" | "publish" | "relist",
    accessToken: string,
  ): Promise<ListingResponse> {
    const response = await this.request<unknown>(
      `/api/v1/listings/${encodeURIComponent(listingId)}/${transition}`,
      {
        accessToken,
        method: "POST",
      },
    );
    return listingResponseSchema.parse(response) as ListingResponse;
  }

  private async postChatRequestAction(
    requestId: string,
    action: "accept" | "block" | "decline",
    payload: ChatRequestActionRequest,
    accessToken: string,
  ): Promise<ChatRequestResponse> {
    const response = await this.request<unknown>(
      `/api/v1/chat-requests/${encodeURIComponent(requestId)}/${action}`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return chatRequestResponseSchema.parse(response) as ChatRequestResponse;
  }

  private async postOfferAction(
    offerId: string,
    action: "accept" | "reject" | "withdraw",
    payload: EmptyActionRequest,
    accessToken: string,
  ): Promise<OfferResponse> {
    const response = await this.request<unknown>(
      `/api/v1/offers/${encodeURIComponent(offerId)}/${action}`,
      {
        accessToken,
        body: JSON.stringify(payload),
        method: "POST",
      },
    );
    return offerResponseSchema.parse(response) as OfferResponse;
  }

  private async request<T>(
    path: string,
    options: {
      accessToken?: string;
      body?: BodyInit;
      method?: string;
      headers?: Record<string, string>;
    } = {},
  ): Promise<T> {
    const response = await this.fetcher(new URL(path, this.baseUrl), {
      headers: {
        Accept: "application/json",
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(options.accessToken
          ? { Authorization: `Bearer ${options.accessToken}` }
          : {}),
        ...(options.headers ?? {}),
      },
      credentials: "include",
      method: options.method ?? "GET",
      ...(options.body ? { body: options.body } : {}),
    });
    const payload =
      response.status === 204
        ? (undefined as T)
        : ((await response.json()) as T);

    if (!response.ok) {
      const problem = payload as ProblemDetail;
      throw new ApiClientError(
        problem.detail ?? response.statusText,
        response.status,
        problem,
      );
    }

    return payload;
  }

  private async requestText(
    path: string,
    options: { accessToken?: string; method?: string } = {},
  ): Promise<string> {
    const response = await this.fetcher(new URL(path, this.baseUrl), {
      headers: {
        Accept: "text/calendar",
        ...(options.accessToken
          ? { Authorization: `Bearer ${options.accessToken}` }
          : {}),
      },
      method: options.method ?? "GET",
    });
    const body = await response.text();

    if (!response.ok) {
      throw new ApiClientError(body || response.statusText, response.status);
    }

    return body;
  }
}

function queryString(
  params: Record<string, boolean | number | string | null | undefined>,
): string {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  }
  const serialized = searchParams.toString();
  return serialized ? `?${serialized}` : "";
}
