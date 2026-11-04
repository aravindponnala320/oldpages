import { z } from "zod";

export const componentStatusSchema = z.object({
  detail: z.string().nullable().optional(),
  status: z.enum(["ok", "error"]),
});

export const healthResponseSchema = z.object({
  components: z.record(componentStatusSchema),
  environment: z.string(),
  service: z.string(),
  status: z.enum(["ok", "degraded"]),
  version: z.string(),
});

export const exampleResponseSchema = z.object({
  message: z.string(),
  request_id: z.string(),
  service: z.string(),
  version: z.string(),
});

export const tokenPairSchema = z.object({
  access_token: z.string(),
  expires_in_seconds: z.number(),
  refresh_token: z.string(),
  token_type: z.literal("bearer"),
});

export const developmentTokenSchema = z.object({
  delivery: z.enum(["development", "out_of_band"]),
  token: z.string().nullable().optional(),
});

export const authResponseSchema = z.object({
  email_verification: developmentTokenSchema.nullable().optional(),
  tokens: tokenPairSchema,
  user: z.object({
    email: z.string(),
    email_verified: z.boolean(),
    id: z.string(),
    status: z.string(),
  }),
});

export const userPrivateResponseSchema = z.object({
  bio: z.string().nullable(),
  course_department: z.string().nullable(),
  display_name: z.string(),
  email: z.string(),
  email_verified: z.boolean(),
  favorite_authors: z.array(z.string()),
  favorite_books: z.array(z.string()),
  favorite_genres: z.array(z.string()),
  id: z.string(),
  institution: z.string().nullable(),
  languages: z.array(z.string()),
  mobile_verified: z.boolean(),
  preferences: z.record(z.union([z.string(), z.boolean()])),
  privacy: z.record(z.union([z.string(), z.boolean()])),
  profile_image_url: z.string().nullable(),
  reading_interests: z.array(z.string()),
  status: z.string(),
  username: z.string().nullable(),
});

export const bookFormatSchema = z.enum([
  "paperback",
  "hardcover",
  "ebook",
  "audiobook",
  "spiral_bound",
  "loose_leaf",
  "unknown",
]);

export const identifierTypeSchema = z.enum([
  "isbn10",
  "isbn13",
  "open_library",
  "google_books",
  "other",
]);

export const metadataStatusSchema = z.enum(["needs_review", "verified"]);

export const authorRoleSchema = z.enum([
  "author",
  "editor",
  "translator",
  "illustrator",
  "contributor",
]);

export const authorSummarySchema = z.object({
  id: z.string(),
  name: z.string(),
  role: authorRoleSchema,
});

export const publisherSummarySchema = z.object({
  id: z.string(),
  name: z.string(),
  website_url: z.string().nullable().optional(),
});

export const categorySummarySchema = z.object({
  id: z.string(),
  name: z.string(),
  parent_id: z.string().nullable().optional(),
  slug: z.string(),
});

export const bookIdentifierResponseSchema = z.object({
  identifier_type: identifierTypeSchema,
  identifier_value: z.string(),
  source: z.string(),
});

export const academicMetadataSchema = z.object({
  school_board: z.string().nullable().optional(),
  grade: z.string().nullable().optional(),
  subject: z.string().nullable().optional(),
  college: z.string().nullable().optional(),
  university: z.string().nullable().optional(),
  degree: z.string().nullable().optional(),
  department: z.string().nullable().optional(),
  course: z.string().nullable().optional(),
  semester: z.string().nullable().optional(),
  professor: z.string().nullable().optional(),
  exam: z.string().nullable().optional(),
  exam_year: z.number().nullable().optional(),
  syllabus_version: z.string().nullable().optional(),
});

export const bookResponseSchema = z.object({
  academic_metadata: academicMetadataSchema.nullable().optional(),
  authors: z.array(authorSummarySchema),
  categories: z.array(categorySummarySchema),
  cover_image_url: z.string().nullable().optional(),
  created_at: z.string(),
  description: z.string().nullable().optional(),
  edition: z.string().nullable().optional(),
  format: bookFormatSchema,
  genres: z.array(z.string()),
  id: z.string(),
  identifiers: z.array(bookIdentifierResponseSchema),
  isbn_10: z.string().nullable().optional(),
  isbn_13: z.string().nullable().optional(),
  language: z.string(),
  metadata_status: metadataStatusSchema,
  page_count: z.number().nullable().optional(),
  publication_year: z.number().nullable().optional(),
  publisher: publisherSummarySchema.nullable().optional(),
  subjects: z.array(z.string()),
  subtitle: z.string().nullable().optional(),
  title: z.string(),
  updated_at: z.string(),
  work_id: z.string(),
});

export const bookListResponseSchema = z.object({
  items: z.array(bookResponseSchema),
  next_cursor: z.string().nullable().optional(),
});

export const resolveIsbnResponseSchema = z.object({
  book: bookResponseSchema.nullable().optional(),
  isbn: z.string(),
  provider: z.string(),
  status: z.enum(["found", "not_found"]),
});

export const categoryNodeSchema: z.ZodTypeAny = z.lazy(() =>
  categorySummarySchema.extend({
    children: z.array(categoryNodeSchema),
  }),
);

export const categoryTreeResponseSchema = z.object({
  items: z.array(categoryNodeSchema),
});

export const authorListResponseSchema = z.object({
  items: z.array(authorSummarySchema),
  next_cursor: z.string().nullable().optional(),
});

export const publisherListResponseSchema = z.object({
  items: z.array(publisherSummarySchema),
  next_cursor: z.string().nullable().optional(),
});

export const listingModeSchema = z.enum([
  "sell",
  "exchange",
  "sell_exchange",
  "donate",
  "lend",
  "rent",
  "request",
  "giveaway",
  "bulk_sale",
]);

export const listingStatusSchema = z.enum([
  "draft",
  "pending_moderation",
  "active",
  "paused",
  "reserved",
  "completed",
  "expired",
  "suspended",
  "rejected",
  "deleted",
]);

export const conditionGradeSchema = z.enum([
  "new_sealed",
  "like_new",
  "excellent",
  "very_good",
  "good",
  "acceptable",
  "poor",
  "reference_only",
]);

export const deliveryMethodSchema = z.enum(["pickup", "shipping"]);
export const mediaStatusSchema = z.enum([
  "pending_upload",
  "uploaded",
  "processing",
  "approved",
  "rejected",
]);

export const listingConditionSchema = z.object({
  access_code_status: z.string().nullable().optional(),
  answer_key_present: z.boolean().nullable().optional(),
  collectible_notes: z.string().nullable().optional(),
  condition: conditionGradeSchema,
  damage_details: z.string().nullable().optional(),
  dust_jacket_present: z.boolean().nullable().optional(),
  first_edition: z.boolean().optional(),
  handwritten_notes: z.boolean().optional(),
  highlighting_percent: z.number().nullable().optional(),
  library_markings: z.boolean().optional(),
  loose_binding: z.boolean().optional(),
  missing_pages: z.boolean().optional(),
  name_written_inside: z.boolean().optional(),
  odor_or_smoke_exposure: z.boolean().optional(),
  signed_by_author: z.boolean().optional(),
  stains: z.boolean().optional(),
  stickers: z.boolean().optional(),
  supplemental_media_present: z.boolean().nullable().optional(),
  torn_pages: z.boolean().optional(),
  water_damage: z.boolean().optional(),
  workbook_completion_percent: z.number().nullable().optional(),
});

export const listingLocationPublicSchema = z.object({
  campus_pickup: z.boolean().optional(),
  city: z.string(),
  country: z.string(),
  neighborhood: z.string().nullable().optional(),
  public_area: z.string(),
  state: z.string().nullable().optional(),
});

export const listingDeliveryMethodSchema = z.object({
  enabled: z.boolean().optional(),
  method: deliveryMethodSchema,
  notes: z.string().nullable().optional(),
  price_amount_cents: z.number().nullable().optional(),
});

export const mediaAssetResponseSchema = z.object({
  byte_size: z.number(),
  content_type: z.string(),
  created_at: z.string(),
  id: z.string(),
  original_filename: z.string(),
  public_url: z.string().nullable().optional(),
  status: mediaStatusSchema,
});

export const listingImageResponseSchema = z.object({
  alt_text: z.string().nullable().optional(),
  id: z.string(),
  is_primary: z.boolean(),
  media: mediaAssetResponseSchema,
  public_url: z.string().nullable().optional(),
  sort_order: z.number(),
});

export const listingResponseSchema = z.object({
  book: z.object({ id: z.string(), title: z.string() }),
  condition: listingConditionSchema.nullable().optional(),
  created_at: z.string(),
  currency: z.string(),
  delivery_methods: z.array(listingDeliveryMethodSchema),
  description: z.string().nullable().optional(),
  exchange_preferences: z.string().nullable().optional(),
  id: z.string(),
  images: z.array(listingImageResponseSchema),
  inventory: z
    .object({ quantity_available: z.number(), quantity_total: z.number() })
    .nullable()
    .optional(),
  lending_duration_days: z.number().nullable().optional(),
  listing_modes: z.array(listingModeSchema),
  location: listingLocationPublicSchema.nullable().optional(),
  negotiable: z.boolean(),
  price_amount_cents: z.number().nullable().optional(),
  price_history: z.array(
    z.object({
      changed_at: z.string(),
      currency: z.string(),
      id: z.string(),
      new_amount_cents: z.number().nullable().optional(),
      old_amount_cents: z.number().nullable().optional(),
      reason: z.string(),
    }),
  ),
  quality_score: z.number(),
  rental_deposit_amount_cents: z.number().nullable().optional(),
  return_policy: z.string().nullable().optional(),
  seller: z.object({ id: z.string() }),
  status: listingStatusSchema,
  title: z.string(),
  updated_at: z.string(),
});

export const searchSortSchema = z.enum([
  "relevance",
  "nearest",
  "newest",
  "lowest_price",
  "highest_price",
  "best_condition",
  "most_saved",
]);

export const searchSuggestionTypeSchema = z.enum([
  "title",
  "author",
  "isbn",
  "category",
  "location",
]);

export const followTargetTypeSchema = z.enum([
  "user",
  "seller",
  "author",
  "genre",
  "community",
  "college",
]);

export const searchListingBookSummarySchema = z.object({
  authors: z.array(z.string()),
  categories: z.array(z.string()),
  id: z.string(),
  isbn_10: z.string().nullable().optional(),
  isbn_13: z.string().nullable().optional(),
  title: z.string(),
});

export const listingSearchResultSchema = z.object({
  book: searchListingBookSummarySchema,
  condition: conditionGradeSchema.nullable().optional(),
  created_at: z.string(),
  currency: z.string(),
  delivery_methods: z.array(deliveryMethodSchema),
  distance_km: z.number().nullable().optional(),
  favorite_count: z.number(),
  id: z.string(),
  image_url: z.string().nullable().optional(),
  listing_modes: z.array(listingModeSchema),
  location: listingLocationPublicSchema.nullable().optional(),
  negotiable: z.boolean(),
  price_amount_cents: z.number().nullable().optional(),
  quality_score: z.number(),
  seller: z.object({ id: z.string() }),
  title: z.string(),
});

export const listingSearchResponseSchema = z.object({
  items: z.array(listingSearchResultSchema),
  next_cursor: z.string().nullable().optional(),
  result_count: z.number(),
});

export const searchSuggestionSchema = z.object({
  text: z.string(),
  type: searchSuggestionTypeSchema,
});

export const searchSuggestionResponseSchema = z.object({
  items: z.array(searchSuggestionSchema),
});

export const savedSearchResponseSchema = z.object({
  created_at: z.string(),
  filters: z.record(z.unknown()),
  id: z.string(),
  last_matched_at: z.string().nullable().optional(),
  last_result_count: z.number(),
  name: z.string(),
  notifications_enabled: z.boolean(),
  query: z.string().nullable().optional(),
  sort: searchSortSchema,
});

export const savedSearchListResponseSchema = z.object({
  items: z.array(savedSearchResponseSchema),
});

export const wishlistItemResponseSchema = z.object({
  book: searchListingBookSummarySchema,
  created_at: z.string(),
  id: z.string(),
});

export const listingFavoriteResponseSchema = z.object({
  created_at: z.string(),
  id: z.string(),
  listing_id: z.string(),
});

export const followResponseSchema = z.object({
  created_at: z.string(),
  id: z.string(),
  target_id: z.string(),
  target_label: z.string().nullable().optional(),
  target_type: followTargetTypeSchema,
});

export const mediaUploadUrlResponseSchema = z.object({
  expires_at: z.string(),
  headers: z.record(z.string()),
  id: z.string(),
  storage_key: z.string(),
  upload_url: z.string(),
});

export const chatRequestStatusSchema = z.enum([
  "pending",
  "accepted",
  "declined",
  "blocked",
]);
export const conversationStatusSchema = z.enum(["active", "blocked", "closed"]);
export const conversationMemberRoleSchema = z.enum(["requester", "recipient"]);
export const conversationMemberStatusSchema = z.enum([
  "active",
  "muted",
  "archived",
  "blocked",
]);
export const messageTypeSchema = z.enum(["text", "image", "listing", "system"]);
export const messageAttachmentTypeSchema = z.enum(["image"]);

export const chatUserSummarySchema = z.object({
  id: z.string(),
});

export const chatRequestResponseSchema = z.object({
  conversation_id: z.string().nullable().optional(),
  created_at: z.string(),
  id: z.string(),
  initial_message: z.string().nullable().optional(),
  listing_id: z.string(),
  recipient: chatUserSummarySchema,
  requester: chatUserSummarySchema,
  responded_at: z.string().nullable().optional(),
  response_message: z.string().nullable().optional(),
  status: chatRequestStatusSchema,
});

export const conversationMemberResponseSchema = z.object({
  role: conversationMemberRoleSchema,
  status: conversationMemberStatusSchema,
  user: chatUserSummarySchema,
});

export const conversationResponseSchema = z.object({
  created_at: z.string(),
  id: z.string(),
  last_message_at: z.string().nullable().optional(),
  listing_id: z.string().nullable().optional(),
  members: z.array(conversationMemberResponseSchema),
  status: conversationStatusSchema,
  unread_count: z.number(),
});

export const conversationListResponseSchema = z.object({
  items: z.array(conversationResponseSchema),
  next_cursor: z.string().nullable().optional(),
});

export const messageAttachmentResponseSchema = z.object({
  attachment_type: messageAttachmentTypeSchema,
  id: z.string(),
  media_id: z.string(),
  metadata: z.record(z.unknown()),
  public_url: z.string().nullable().optional(),
  sort_order: z.number(),
});

export const messageResponseSchema = z.object({
  attachments: z.array(messageAttachmentResponseSchema),
  body: z.string().nullable().optional(),
  client_message_id: z.string().nullable().optional(),
  conversation_id: z.string(),
  created_at: z.string(),
  id: z.string(),
  listing_id: z.string().nullable().optional(),
  message_type: messageTypeSchema,
  metadata: z.record(z.unknown()),
  read_by_user_ids: z.array(z.string()),
  sender: chatUserSummarySchema,
});

export const messageListResponseSchema = z.object({
  items: z.array(messageResponseSchema),
  next_cursor: z.string().nullable().optional(),
});

export const messageReportResponseSchema = z.object({
  created_at: z.string(),
  id: z.string(),
  message_id: z.string(),
  reason: z.string(),
  status: z.string(),
});

export const notificationTypeSchema = z.enum([
  "chat_request",
  "chat_accepted",
  "chat_declined",
  "message",
  "saved_search_match",
  "system",
]);
export const notificationStatusSchema = z.enum(["unread", "read", "archived"]);
export const notificationChannelSchema = z.enum(["in_app", "email", "push"]);
export const notificationDeliveryStatusSchema = z.enum([
  "pending",
  "sent",
  "failed",
  "suppressed",
]);

export const notificationDeliveryResponseSchema = z.object({
  channel: notificationChannelSchema,
  id: z.string(),
  status: notificationDeliveryStatusSchema,
});

export const notificationResponseSchema = z.object({
  body: z.string(),
  created_at: z.string(),
  data: z.record(z.unknown()),
  deliveries: z.array(notificationDeliveryResponseSchema),
  id: z.string(),
  read_at: z.string().nullable().optional(),
  related_entity_id: z.string().nullable().optional(),
  related_entity_type: z.string().nullable().optional(),
  status: notificationStatusSchema,
  title: z.string(),
  type: notificationTypeSchema,
});

export const notificationListResponseSchema = z.object({
  items: z.array(notificationResponseSchema),
  next_cursor: z.string().nullable().optional(),
});

export const notificationPreferenceResponseSchema = z.object({
  chat_requests_enabled: z.boolean(),
  email_enabled: z.boolean(),
  id: z.string(),
  in_app_enabled: z.boolean(),
  marketing_enabled: z.boolean(),
  messages_enabled: z.boolean(),
  push_enabled: z.boolean(),
  quiet_hours_end: z.string().nullable().optional(),
  quiet_hours_start: z.string().nullable().optional(),
});

export const offerTypeSchema = z.enum([
  "price",
  "counter",
  "exchange",
  "bundle",
]);
export const offerStatusSchema = z.enum([
  "pending",
  "countered",
  "accepted",
  "rejected",
  "withdrawn",
  "expired",
]);
export const fulfillmentMethodSchema = z.enum(["pickup", "shipping"]);
export const transactionStatusSchema = z.enum([
  "reserved",
  "ready_for_pickup",
  "completed",
  "cancelled",
  "disputed",
]);
export const pickupStatusSchema = z.enum([
  "proposed",
  "confirmed",
  "completed",
  "cancelled",
]);
export const reviewTypeSchema = z.enum([
  "buyer_reviews_seller",
  "seller_reviews_buyer",
]);

export const commerceUserSummarySchema = z.object({
  id: z.string(),
});

export const exchangeOfferItemResponseSchema = z.object({
  cash_adjustment_cents: z.number().nullable().optional(),
  condition_note: z.string().nullable().optional(),
  id: z.string(),
  offered_listing_id: z.string().nullable().optional(),
  title: z.string(),
});

export const offerResponseSchema = z.object({
  amount_cents: z.number().nullable().optional(),
  bundle_listing_ids: z.array(z.string()),
  buyer: commerceUserSummarySchema,
  created_at: z.string(),
  currency: z.string(),
  exchange_items: z.array(exchangeOfferItemResponseSchema),
  expires_at: z.string(),
  fulfillment_method: fulfillmentMethodSchema,
  id: z.string(),
  listing_id: z.string(),
  message: z.string().nullable().optional(),
  offer_type: offerTypeSchema,
  parent_offer_id: z.string().nullable().optional(),
  proposer: commerceUserSummarySchema,
  quantity: z.number(),
  responded_at: z.string().nullable().optional(),
  seller: commerceUserSummarySchema,
  status: offerStatusSchema,
  transaction_id: z.string().nullable().optional(),
});

export const pickupResponseSchema = z.object({
  confirmed_at: z.string().nullable().optional(),
  confirmed_by_user_id: z.string().nullable().optional(),
  exact_address: z.string().nullable().optional(),
  exact_latitude: z.string().nullable().optional(),
  exact_longitude: z.string().nullable().optional(),
  handover_code: z.string().nullable().optional(),
  id: z.string(),
  pickup_notes_private: z.string().nullable().optional(),
  proposed_by_user_id: z.string(),
  proposed_end_at: z.string().nullable().optional(),
  proposed_start_at: z.string().nullable().optional(),
  public_location_label: z.string(),
  status: pickupStatusSchema,
  transaction_id: z.string(),
});

export const transactionResponseSchema = z.object({
  amount_cents: z.number().nullable().optional(),
  buyer: commerceUserSummarySchema,
  completed_at: z.string().nullable().optional(),
  created_at: z.string(),
  currency: z.string(),
  fulfillment_method: fulfillmentMethodSchema,
  id: z.string(),
  listing_id: z.string(),
  offer_id: z.string(),
  pickup: pickupResponseSchema.nullable().optional(),
  quantity: z.number(),
  seller: commerceUserSummarySchema,
  status: transactionStatusSchema,
});

export const reviewDimensionResponseSchema = z.object({
  dimension: z.string(),
  id: z.string(),
  rating: z.number(),
});

export const reviewResponseSchema = z.object({
  comment: z.string().nullable().optional(),
  created_at: z.string(),
  dimensions: z.array(reviewDimensionResponseSchema),
  id: z.string(),
  rating: z.number(),
  review_type: reviewTypeSchema,
  reviewee: commerceUserSummarySchema,
  reviewer: commerceUserSummarySchema,
  status: z.string(),
  transaction_id: z.string(),
});

export const reportTargetTypeSchema = z.enum([
  "user",
  "listing",
  "message",
  "review",
  "copyright",
]);
export const reportSeveritySchema = z.enum([
  "low",
  "medium",
  "high",
  "critical",
]);
export const reportStatusSchema = z.enum([
  "open",
  "in_review",
  "resolved",
  "dismissed",
  "appealed",
]);
export const reportReasonSchema = z.enum([
  "fake_listing",
  "misleading_condition",
  "piracy",
  "counterfeit",
  "scam",
  "harassment",
  "hate_speech",
  "sexual_content",
  "child_safety",
  "spam",
  "fake_review",
  "payment_fraud",
  "stolen_image",
  "copyright_infringement",
  "personal_information",
  "dangerous_meetup",
  "other",
]);
export const moderationCaseStatusSchema = z.enum([
  "open",
  "in_review",
  "actioned",
  "closed",
  "appealed",
]);
export const moderationActionTypeSchema = z.enum([
  "warn",
  "remove_content",
  "suspend",
  "ban",
  "dismiss",
  "restore",
  "appeal_submitted",
  "note",
]);

export const trustUserSummarySchema = z.object({
  id: z.string(),
});

export const reportResponseSchema = z.object({
  case_id: z.string().nullable().optional(),
  created_at: z.string(),
  description: z.string().nullable().optional(),
  evidence: z.record(z.unknown()),
  id: z.string(),
  reason: z.string(),
  reporter: trustUserSummarySchema,
  severity: reportSeveritySchema,
  status: reportStatusSchema,
  target: z.object({
    id: z.string().nullable().optional(),
    type: reportTargetTypeSchema,
  }),
});

export const moderationActionResponseSchema = z.object({
  action_type: moderationActionTypeSchema,
  actor_user_id: z.string().nullable().optional(),
  created_at: z.string(),
  duration_until: z.string().nullable().optional(),
  evidence_snapshot: z.record(z.unknown()),
  id: z.string(),
  metadata: z.record(z.unknown()),
  moderator_user_id: z.string().nullable().optional(),
  reason: z.string().nullable().optional(),
});

export const moderationCaseResponseSchema = z.object({
  actions: z.array(moderationActionResponseSchema),
  assigned_moderator_user_id: z.string().nullable().optional(),
  created_at: z.string(),
  evidence_snapshot: z.record(z.unknown()),
  id: z.string(),
  priority_score: z.number(),
  report: reportResponseSchema,
  severity: reportSeveritySchema,
  status: moderationCaseStatusSchema,
  summary: z.string(),
});

export const moderationCaseListResponseSchema = z.object({
  items: z.array(moderationCaseResponseSchema),
  next_cursor: z.string().nullable().optional(),
});

export const conversationEvidenceMessageSchema = z.object({
  body: z.string().nullable().optional(),
  created_at: z.string(),
  id: z.string(),
  message_type: z.string(),
  sender_user_id: z.string(),
});

export const conversationEvidenceResponseSchema = z.object({
  case_id: z.string(),
  conversation_id: z.string(),
  messages: z.array(conversationEvidenceMessageSchema),
  report_id: z.string(),
});

export const moderationUserResponseSchema = z.object({
  email: z.string(),
  id: z.string(),
  report_count: z.number(),
  status: z.string(),
});

export const moderationListingResponseSchema = z.object({
  id: z.string(),
  report_count: z.number(),
  seller_user_id: z.string(),
  status: z.string(),
  title: z.string(),
});

export const moderationRuleConfigResponseSchema = z.object({
  action_types: z.array(z.string()),
  moderator_roles: z.array(z.string()),
  severity_by_reason: z.record(reportReasonSchema, reportSeveritySchema),
});

export const communityVisibilitySchema = z.enum([
  "public",
  "private",
  "secret",
  "institution_verified",
]);
export const communityMembershipPolicySchema = z.enum([
  "open",
  "request",
  "approval",
  "institution_verified",
]);
export const communityTypeSchema = z.enum([
  "college",
  "university",
  "school",
  "area",
  "city",
  "apartment",
  "workplace",
  "language",
  "genre",
  "author",
  "series",
  "book",
  "exam",
  "course",
  "profession",
  "age_group",
  "reading_goal",
  "library",
  "bookstore",
  "publisher",
  "social_cause",
  "local",
  "general",
]);
export const communityMemberStatusSchema = z.enum([
  "pending",
  "active",
  "rejected",
  "banned",
  "muted",
]);
export const communityChannelTypeSchema = z.enum([
  "general",
  "announcements",
  "marketplace",
  "questions",
  "resources",
]);
export const communityChannelVisibilitySchema = z.enum([
  "public",
  "members",
  "moderators",
]);
export const communityPostTypeSchema = z.enum([
  "text",
  "review",
  "photo",
  "video",
  "poll",
  "question",
  "recommendation",
  "quote",
  "reading_update",
  "listing",
  "exchange_request",
  "donation_request",
  "event",
  "challenge",
  "resource",
  "announcement",
]);
export const communityPostStatusSchema = z.enum([
  "published",
  "pending_review",
  "hidden",
  "deleted",
]);
export const postReactionTypeSchema = z.enum([
  "like",
  "love",
  "insightful",
  "upvote",
  "celebrate",
]);
export const communityReportTargetTypeSchema = z.enum([
  "community",
  "post",
  "comment",
  "member",
]);
export const communityReportStatusSchema = z.enum([
  "open",
  "resolved",
  "dismissed",
]);

export const communityRuleInputSchema = z.object({
  body: z.string(),
  title: z.string(),
});

export const communityChannelInputSchema = z.object({
  channel_type: communityChannelTypeSchema.optional(),
  name: z.string(),
  slug: z.string().nullable().optional(),
  visibility: communityChannelVisibilitySchema.optional(),
});

export const communityCreateRequestSchema = z.object({
  book_id: z.string().nullable().optional(),
  channels: z.array(communityChannelInputSchema).optional(),
  city: z.string().nullable().optional(),
  community_type: communityTypeSchema.optional(),
  country: z.string().nullable().optional(),
  cover_image_url: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  genre: z.string().nullable().optional(),
  institution: z.string().nullable().optional(),
  language: z.string().nullable().optional(),
  membership_policy: communityMembershipPolicySchema.nullable().optional(),
  name: z.string(),
  rules: z.array(communityRuleInputSchema).optional(),
  settings: z.record(z.unknown()).optional(),
  slug: z.string().nullable().optional(),
  state: z.string().nullable().optional(),
  visibility: communityVisibilitySchema.optional(),
});

export const communityUserSummarySchema = z.object({
  id: z.string(),
});

export const communityRoleResponseSchema = z.object({
  id: z.string(),
  is_default: z.boolean(),
  name: z.string(),
  permissions: z.array(z.string()),
});

export const communityMemberResponseSchema = z.object({
  joined_at: z.string().nullable().optional(),
  role: z.string(),
  status: communityMemberStatusSchema,
  user: communityUserSummarySchema,
});

export const communityRuleResponseSchema = z.object({
  body: z.string(),
  enabled: z.boolean(),
  id: z.string(),
  sort_order: z.number(),
  title: z.string(),
});

export const communityChannelResponseSchema = z.object({
  channel_type: communityChannelTypeSchema,
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  visibility: communityChannelVisibilitySchema,
});

export const communitySummaryResponseSchema = z.object({
  book_id: z.string().nullable().optional(),
  city: z.string().nullable().optional(),
  community_type: communityTypeSchema,
  country: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  genre: z.string().nullable().optional(),
  id: z.string(),
  institution: z.string().nullable().optional(),
  member_count: z.number(),
  name: z.string(),
  slug: z.string(),
  state: z.string().nullable().optional(),
  visibility: communityVisibilitySchema,
  viewer_membership_status: communityMemberStatusSchema.nullable().optional(),
});

export const communityResponseSchema = communitySummaryResponseSchema.extend({
  channels: z.array(communityChannelResponseSchema),
  membership_policy: communityMembershipPolicySchema,
  owner: communityUserSummarySchema,
  rules: z.array(communityRuleResponseSchema),
});

export const communityListResponseSchema = z.object({
  items: z.array(communitySummaryResponseSchema),
  next_cursor: z.string().nullable().optional(),
});

export const communityPostResponseSchema = z.object({
  author: communityUserSummarySchema,
  body: z.string().nullable().optional(),
  channel_id: z.string().nullable().optional(),
  comment_count: z.number(),
  community_id: z.string(),
  created_at: z.string(),
  id: z.string(),
  is_announcement: z.boolean(),
  is_pinned: z.boolean(),
  listing_id: z.string().nullable().optional(),
  poll: z.record(z.unknown()),
  post_type: communityPostTypeSchema,
  reaction_counts: z.record(z.number()),
  status: communityPostStatusSchema,
  title: z.string().nullable().optional(),
  viewer_reaction: postReactionTypeSchema.nullable().optional(),
});

export const communityFeedResponseSchema = z.object({
  items: z.array(communityPostResponseSchema),
  next_cursor: z.string().nullable().optional(),
});

export const postCommentResponseSchema = z.object({
  author: communityUserSummarySchema,
  body: z.string(),
  created_at: z.string(),
  id: z.string(),
  parent_comment_id: z.string().nullable().optional(),
  post_id: z.string(),
  status: z.string(),
});

export const postReactionResponseSchema = z.object({
  id: z.string(),
  post_id: z.string(),
  reaction_type: postReactionTypeSchema,
  user_id: z.string(),
});

export const communityMarketplaceResponseSchema = z.object({
  community_id: z.string(),
  items: z.array(listingResponseSchema),
  next_cursor: z.string().nullable().optional(),
});

export const communityReportResponseSchema = z.object({
  community_id: z.string(),
  created_at: z.string(),
  id: z.string(),
  reason: z.string(),
  status: communityReportStatusSchema,
  target_id: z.string().nullable().optional(),
  target_type: communityReportTargetTypeSchema,
});

export const clubVisibilitySchema = z.enum(["public", "private"]);
export const bookClubStatusSchema = z.enum(["active", "archived", "suspended"]);
export const clubBookStatusSchema = z.enum(["current", "next", "past"]);
export const bookNominationStatusSchema = z.enum([
  "active",
  "selected",
  "withdrawn",
]);
export const milestonePositionTypeSchema = z.enum([
  "chapter",
  "page",
  "percent",
  "whole_book",
]);
export const buddyReadStatusSchema = z.enum([
  "active",
  "completed",
  "cancelled",
]);
export const readalongStatusSchema = z.enum([
  "scheduled",
  "active",
  "completed",
  "cancelled",
]);
export const eventTypeSchema = z.enum([
  "book_club_meeting",
  "book_exchange",
  "used_book_fair",
  "donation_drive",
  "author_meetup",
  "signing",
  "reading_session",
  "silent_reading",
  "childrens_story_session",
  "library_event",
  "college_textbook_sale",
  "writing_workshop",
  "poetry_reading",
  "online_discussion",
  "author_interview",
]);
export const eventStatusSchema = z.enum([
  "scheduled",
  "cancelled",
  "completed",
]);
export const eventRSVPStatusSchema = z.enum([
  "going",
  "cancelled",
  "waitlisted",
]);

export const clubUserSummarySchema = z.object({
  id: z.string(),
});

export const clubBookSummarySchema = z.object({
  id: z.string(),
  title: z.string(),
});

export const bookClubCreateRequestSchema = z.object({
  community_id: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  name: z.string(),
  settings: z.record(z.unknown()).optional(),
  slug: z.string().nullable().optional(),
  timezone: z.string().optional(),
  visibility: clubVisibilitySchema.optional(),
});

export const clubBookCreateRequestSchema = z.object({
  book_id: z.string(),
  discussion_guide: z.string().nullable().optional(),
  end_date: z.string().nullable().optional(),
  start_date: z.string().nullable().optional(),
  status: clubBookStatusSchema.optional(),
});

export const bookNominationCreateRequestSchema = z.object({
  book_id: z.string(),
  cycle_key: z.string().optional(),
  note: z.string().nullable().optional(),
});

export const bookVoteRequestSchema = z.object({
  cycle_key: z.string().optional(),
  nomination_id: z.string(),
  rank: z.number(),
});

export const selectClubBookRequestSchema = z.object({
  cycle_key: z.string().optional(),
  end_date: z.string().nullable().optional(),
  start_date: z.string().nullable().optional(),
  status: clubBookStatusSchema.optional(),
});

export const readingMilestoneCreateRequestSchema = z.object({
  discussion_prompt: z.string().nullable().optional(),
  ends_at: z.string().nullable().optional(),
  position_type: milestonePositionTypeSchema,
  position_value: z.number(),
  starts_at: z.string().nullable().optional(),
  title: z.string(),
});

export const buddyReadCreateRequestSchema = z.object({
  book_id: z.string(),
  deadline_at: z.string().nullable().optional(),
  max_participants: z.number().optional(),
  title: z.string(),
  visibility: clubVisibilitySchema.optional(),
});

export const buddyReadProgressRequestSchema = z.object({
  position_type: milestonePositionTypeSchema.optional(),
  position_value: z.number(),
});

export const readalongCreateRequestSchema = z.object({
  book_id: z.string(),
  chapter_schedule: z.array(z.record(z.unknown())).optional(),
  community_id: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  ends_at: z.string().nullable().optional(),
  starts_at: z.string().nullable().optional(),
  timezone: z.string().optional(),
  title: z.string(),
  visibility: clubVisibilitySchema.optional(),
});

export const eventCreateRequestSchema = z.object({
  address: z.string().nullable().optional(),
  capacity: z.number().nullable().optional(),
  club_id: z.string().nullable().optional(),
  community_id: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  ends_at: z.string(),
  event_type: eventTypeSchema,
  location_name: z.string().nullable().optional(),
  metadata: z.record(z.unknown()).optional(),
  online_url: z.string().nullable().optional(),
  starts_at: z.string(),
  timezone: z.string(),
  title: z.string(),
  visibility: clubVisibilitySchema.optional(),
});

export const eventUpdateRequestSchema = z.object({
  capacity: z.number().nullable().optional(),
  description: z.string().nullable().optional(),
  ends_at: z.string().nullable().optional(),
  location_name: z.string().nullable().optional(),
  online_url: z.string().nullable().optional(),
  starts_at: z.string().nullable().optional(),
  status: eventStatusSchema.nullable().optional(),
  timezone: z.string().nullable().optional(),
  title: z.string().nullable().optional(),
});

export const eventRSVPRequestSchema = z.object({
  guest_count: z.number().optional(),
  note: z.string().nullable().optional(),
});

export const eventCheckinRequestSchema = z.object({
  checkin_code: z.string(),
  user_id: z.string(),
});

export const bookClubResponseSchema = z.object({
  community_id: z.string().nullable().optional(),
  current_book: clubBookSummarySchema.nullable().optional(),
  description: z.string().nullable().optional(),
  id: z.string(),
  member_context: z.string().nullable().optional(),
  name: z.string(),
  next_book: clubBookSummarySchema.nullable().optional(),
  owner: clubUserSummarySchema,
  slug: z.string(),
  status: bookClubStatusSchema,
  timezone: z.string(),
  visibility: clubVisibilitySchema,
});

export const bookClubListResponseSchema = z.object({
  items: z.array(bookClubResponseSchema),
  next_cursor: z.string().nullable().optional(),
});

export const clubBookResponseSchema = z.object({
  available_listings: z.array(listingResponseSchema),
  book: clubBookSummarySchema,
  discussion_guide: z.string().nullable().optional(),
  end_date: z.string().nullable().optional(),
  id: z.string(),
  selected_at: z.string().nullable().optional(),
  sequence: z.number(),
  start_date: z.string().nullable().optional(),
  status: clubBookStatusSchema,
});

export const clubBookListResponseSchema = z.object({
  items: z.array(clubBookResponseSchema),
});

export const bookNominationResponseSchema = z.object({
  book: clubBookSummarySchema,
  cycle_key: z.string(),
  id: z.string(),
  note: z.string().nullable().optional(),
  nominator: clubUserSummarySchema,
  status: bookNominationStatusSchema,
  vote_count: z.number(),
});

export const bookVoteResponseSchema = z.object({
  cycle_key: z.string(),
  id: z.string(),
  nomination_id: z.string(),
  rank: z.number(),
  voter: clubUserSummarySchema,
});

export const readingMilestoneResponseSchema = z.object({
  discussion_prompt: z.string().nullable().optional(),
  ends_at: z.string().nullable().optional(),
  id: z.string(),
  position_type: milestonePositionTypeSchema,
  position_value: z.number(),
  spoiler_locked: z.boolean(),
  starts_at: z.string().nullable().optional(),
  title: z.string(),
});

export const readingMilestoneListResponseSchema = z.object({
  items: z.array(readingMilestoneResponseSchema),
});

export const buddyReadResponseSchema = z.object({
  book: clubBookSummarySchema,
  deadline_at: z.string().nullable().optional(),
  id: z.string(),
  max_participants: z.number(),
  participant_user_ids: z.array(z.string()),
  progress: z.record(z.unknown()),
  status: buddyReadStatusSchema,
  title: z.string(),
  visibility: clubVisibilitySchema,
});

export const readalongResponseSchema = z.object({
  book: clubBookSummarySchema,
  chapter_schedule: z.array(z.record(z.unknown())),
  community_id: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  ends_at: z.string().nullable().optional(),
  host: clubUserSummarySchema,
  id: z.string(),
  starts_at: z.string().nullable().optional(),
  status: readalongStatusSchema,
  timezone: z.string(),
  title: z.string(),
  visibility: clubVisibilitySchema,
});

export const eventResponseSchema = z.object({
  capacity: z.number().nullable().optional(),
  checkin_code: z.string().nullable().optional(),
  club_id: z.string().nullable().optional(),
  community_id: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  ends_at: z.string(),
  event_type: eventTypeSchema,
  id: z.string(),
  location_name: z.string().nullable().optional(),
  online_url: z.string().nullable().optional(),
  organizer: clubUserSummarySchema,
  rsvp_count: z.number(),
  starts_at: z.string(),
  status: eventStatusSchema,
  timezone: z.string(),
  title: z.string(),
  visibility: clubVisibilitySchema,
  waitlist_count: z.number(),
});

export const eventListResponseSchema = z.object({
  items: z.array(eventResponseSchema),
  next_cursor: z.string().nullable().optional(),
});

export const eventRSVPResponseSchema = z.object({
  event_id: z.string(),
  guest_count: z.number(),
  id: z.string(),
  status: eventRSVPStatusSchema,
  user: clubUserSummarySchema,
  waitlist_position: z.number().nullable().optional(),
});

export const eventCheckinResponseSchema = z.object({
  checked_in_at: z.string(),
  checked_in_by_user_id: z.string(),
  event_id: z.string(),
  id: z.string(),
  user_id: z.string(),
});

export const readingShelfTypeSchema = z.enum([
  "want_to_read",
  "currently_reading",
  "finished",
  "did_not_finish",
  "owned",
  "previously_owned",
  "available_for_exchange",
  "available_for_lending",
  "favorites",
  "academic_books",
  "rare_collection",
  "custom",
]);
export const readingShelfVisibilitySchema = z.enum(["public", "private"]);
export const readingStatusSchema = z.enum([
  "want_to_read",
  "currently_reading",
  "finished",
  "did_not_finish",
]);
export const readingNoteTypeSchema = z.enum(["note", "highlight", "quote"]);
export const readingNoteVisibilitySchema = z.enum(["private", "public"]);
export const readingGoalTypeSchema = z.enum([
  "books_per_year",
  "pages_per_month",
  "minutes_per_day",
  "genre",
  "author",
  "language",
  "community_challenge",
  "institution_challenge",
]);
export const readingGoalScopeSchema = z.enum([
  "personal",
  "community",
  "institution",
]);
export const readingGoalStatusSchema = z.enum([
  "active",
  "completed",
  "cancelled",
]);
export const readingStatisticPeriodSchema = z.enum([
  "month",
  "year",
  "all_time",
]);

export const readingBookSummarySchema = z.object({
  authors: z.array(z.string()),
  genres: z.array(z.string()),
  id: z.string(),
  page_count: z.number().nullable().optional(),
  title: z.string(),
});

export const readingShelfCreateRequestSchema = z.object({
  name: z.string(),
  slug: z.string().nullable().optional(),
  visibility: readingShelfVisibilitySchema.optional(),
});

export const readingShelfItemCreateRequestSchema = z.object({
  book_id: z.string(),
  note: z.string().nullable().optional(),
  sort_order: z.number().optional(),
});

export const readingShelfItemResponseSchema = z.object({
  added_at: z.string(),
  book: readingBookSummarySchema,
  id: z.string(),
  note: z.string().nullable().optional(),
  sort_order: z.number(),
});

export const readingShelfResponseSchema = z.object({
  id: z.string(),
  is_system: z.boolean(),
  items: z.array(readingShelfItemResponseSchema),
  name: z.string(),
  shelf_type: readingShelfTypeSchema,
  slug: z.string(),
  sort_order: z.number(),
  visibility: readingShelfVisibilitySchema,
});

export const readingShelfListResponseSchema = z.object({
  items: z.array(readingShelfResponseSchema),
});

export const readingProgressUpdateRequestSchema = z.object({
  current_page: z.number().nullable().optional(),
  finished_on: z.string().nullable().optional(),
  percent_complete: z.number().nullable().optional(),
  progressed_on: z.string().nullable().optional(),
  rating: z.number().nullable().optional(),
  reading_minutes: z.number().nullable().optional(),
  reread_count: z.number().nullable().optional(),
  review_text: z.string().nullable().optional(),
  started_on: z.string().nullable().optional(),
  status: readingStatusSchema,
});

export const readingProgressResponseSchema = z.object({
  book: readingBookSummarySchema,
  current_page: z.number().nullable().optional(),
  daily_minutes: z.record(z.number()),
  finished_on: z.string().nullable().optional(),
  id: z.string(),
  last_progress_at: z.string().nullable().optional(),
  percent_complete: z.number().nullable().optional(),
  rating: z.number().nullable().optional(),
  reread_count: z.number(),
  review_text: z.string().nullable().optional(),
  started_on: z.string().nullable().optional(),
  status: readingStatusSchema,
  total_reading_minutes: z.number(),
});

export const readingProgressListResponseSchema = z.object({
  items: z.array(readingProgressResponseSchema),
});

export const readingNoteCreateRequestSchema = z.object({
  body: z.string(),
  book_id: z.string(),
  client_note_id: z.string().nullable().optional(),
  note_type: readingNoteTypeSchema.optional(),
  page_number: z.number().nullable().optional(),
  percent_complete: z.number().nullable().optional(),
  visibility: readingNoteVisibilitySchema.optional(),
});

export const readingNoteResponseSchema = z.object({
  body: z.string(),
  book: readingBookSummarySchema,
  created_at: z.string(),
  id: z.string(),
  note_type: readingNoteTypeSchema,
  page_number: z.number().nullable().optional(),
  percent_complete: z.number().nullable().optional(),
  visibility: readingNoteVisibilitySchema,
});

export const readingNoteListResponseSchema = z.object({
  items: z.array(readingNoteResponseSchema),
});

export const readingGoalCreateRequestSchema = z.object({
  community_id: z.string().nullable().optional(),
  goal_type: readingGoalTypeSchema,
  period_end: z.string(),
  period_start: z.string(),
  scope: readingGoalScopeSchema.optional(),
  target_metadata: z.record(z.unknown()).optional(),
  target_value: z.number(),
  timezone: z.string().optional(),
});

export const readingGoalResponseSchema = z.object({
  community_id: z.string().nullable().optional(),
  current_value: z.number(),
  goal_type: readingGoalTypeSchema,
  id: z.string(),
  period_end: z.string(),
  period_start: z.string(),
  scope: readingGoalScopeSchema,
  status: readingGoalStatusSchema,
  target_metadata: z.record(z.unknown()),
  target_value: z.number(),
  timezone: z.string(),
});

export const readingGoalListResponseSchema = z.object({
  items: z.array(readingGoalResponseSchema),
});

export const readingStatisticRecomputeRequestSchema = z.object({
  period_start: z.string().nullable().optional(),
  period_type: readingStatisticPeriodSchema.optional(),
  timezone: z.string().optional(),
});

export const readingStatisticResponseSchema = z.object({
  authors: z.record(z.number()),
  books_completed: z.number(),
  computed_at: z.string(),
  genres: z.record(z.number()),
  id: z.string(),
  minutes_read: z.number(),
  monthly_progress: z.record(z.unknown()),
  pages_read: z.number(),
  period_end: z.string(),
  period_start: z.string(),
  period_type: readingStatisticPeriodSchema,
  reading_streak_days: z.number(),
  timezone: z.string(),
  year_summary: z.record(z.unknown()),
});

export const readingStatisticListResponseSchema = z.object({
  items: z.array(readingStatisticResponseSchema),
});

export type HealthResponseInput = z.infer<typeof healthResponseSchema>;
export type ExampleResponseInput = z.infer<typeof exampleResponseSchema>;
export type AuthResponseInput = z.infer<typeof authResponseSchema>;
export type UserPrivateResponseInput = z.infer<
  typeof userPrivateResponseSchema
>;
export type BookResponseInput = z.infer<typeof bookResponseSchema>;
export type BookListResponseInput = z.infer<typeof bookListResponseSchema>;
export type CategoryTreeResponseInput = z.infer<
  typeof categoryTreeResponseSchema
>;
export type ListingResponseInput = z.infer<typeof listingResponseSchema>;
export type MediaAssetResponseInput = z.infer<typeof mediaAssetResponseSchema>;
export type ListingSearchResponseInput = z.infer<
  typeof listingSearchResponseSchema
>;
export type SearchSuggestionResponseInput = z.infer<
  typeof searchSuggestionResponseSchema
>;
export type SavedSearchResponseInput = z.infer<
  typeof savedSearchResponseSchema
>;
export type CommunityResponseInput = z.infer<typeof communityResponseSchema>;
export type CommunityListResponseInput = z.infer<
  typeof communityListResponseSchema
>;
export type CommunityPostResponseInput = z.infer<
  typeof communityPostResponseSchema
>;
export type BookClubResponseInput = z.infer<typeof bookClubResponseSchema>;
export type EventResponseInput = z.infer<typeof eventResponseSchema>;
export type ReadingShelfResponseInput = z.infer<
  typeof readingShelfResponseSchema
>;
export type ReadingProgressResponseInput = z.infer<
  typeof readingProgressResponseSchema
>;
export type ReadingNoteResponseInput = z.infer<
  typeof readingNoteResponseSchema
>;
export type ReadingGoalResponseInput = z.infer<
  typeof readingGoalResponseSchema
>;
export type ReadingStatisticResponseInput = z.infer<
  typeof readingStatisticResponseSchema
>;
