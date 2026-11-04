export type ComponentStatus = {
  status: "ok" | "error";
  detail?: string | null;
};

export type HealthResponse = {
  components: Record<string, ComponentStatus>;
  environment: string;
  service: string;
  status: "ok" | "degraded";
  version: string;
};

export type ExampleResponse = {
  message: string;
  request_id: string;
  service: string;
  version: string;
};

export type ProblemDetail = {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
  request_id?: string | null;
};

export type TokenPair = {
  access_token: string;
  expires_in_seconds: number;
  refresh_token: string;
  token_type: "bearer";
};

export type AuthUser = {
  email: string;
  email_verified: boolean;
  id: string;
  status: string;
};

export type DevelopmentToken = {
  delivery: "development" | "out_of_band";
  token?: string | null;
};

export type AuthResponse = {
  tokens: TokenPair;
  user: AuthUser;
  email_verification?: DevelopmentToken | null;
};

export type RegisterRequest = {
  display_name: string;
  email: string;
  password: string;
  privacy_accepted: boolean;
  terms_accepted: boolean;
  username?: string | null;
};

export type LoginRequest = {
  device_fingerprint?: string | null;
  device_name?: string | null;
  device_type?: string | null;
  email: string;
  password: string;
};

export type UserPrivateResponse = {
  bio: string | null;
  course_department: string | null;
  display_name: string;
  email: string;
  email_verified: boolean;
  favorite_authors: string[];
  favorite_books: string[];
  favorite_genres: string[];
  id: string;
  institution: string | null;
  languages: string[];
  mobile_verified: boolean;
  preferences: Record<string, string | boolean>;
  privacy: Record<string, string | boolean>;
  profile_image_url: string | null;
  reading_interests: string[];
  status: string;
  username: string | null;
};

export type UserPublicResponse = {
  approximate_location: string | null;
  bio: string | null;
  display_name: string;
  id: string;
  institution: string | null;
  privacy_level: string;
  profile_image_url: string | null;
  username: string | null;
  verification_badges: string[];
};

export type SessionResponse = {
  created_at: string;
  current: boolean;
  id: string;
  last_used_at: string;
  revoked_at?: string | null;
  user_agent?: string | null;
};

export type BookFormat =
  | "paperback"
  | "hardcover"
  | "ebook"
  | "audiobook"
  | "spiral_bound"
  | "loose_leaf"
  | "unknown";

export type IdentifierType =
  | "isbn10"
  | "isbn13"
  | "open_library"
  | "google_books"
  | "other";

export type MetadataStatus = "needs_review" | "verified";

export type AuthorRole =
  | "author"
  | "editor"
  | "translator"
  | "illustrator"
  | "contributor";

export type AuthorInput = {
  name: string;
  role?: AuthorRole;
};

export type PublisherInput = {
  name: string;
  website_url?: string | null;
};

export type BookIdentifierInput = {
  identifier_type: IdentifierType;
  identifier_value: string;
  source?: string;
};

export type AcademicMetadata = {
  school_board?: string | null;
  grade?: string | null;
  subject?: string | null;
  college?: string | null;
  university?: string | null;
  degree?: string | null;
  department?: string | null;
  course?: string | null;
  semester?: string | null;
  professor?: string | null;
  exam?: string | null;
  exam_year?: number | null;
  syllabus_version?: string | null;
};

export type BookCreateRequest = {
  academic_metadata?: AcademicMetadata | null;
  authors: AuthorInput[];
  category_ids?: string[];
  cover_image_url?: string | null;
  description?: string | null;
  edition?: string | null;
  format?: BookFormat;
  genres?: string[];
  identifiers?: BookIdentifierInput[];
  isbn_10?: string | null;
  isbn_13?: string | null;
  language?: string;
  page_count?: number | null;
  publication_year?: number | null;
  publisher?: PublisherInput | null;
  subjects?: string[];
  subtitle?: string | null;
  title: string;
};

export type BookUpdateRequest = Partial<BookCreateRequest> & {
  metadata_status?: MetadataStatus | null;
};

export type AuthorSummary = {
  id: string;
  name: string;
  role: AuthorRole;
};

export type PublisherSummary = {
  id: string;
  name: string;
  website_url?: string | null;
};

export type CategorySummary = {
  id: string;
  name: string;
  parent_id?: string | null;
  slug: string;
};

export type BookIdentifierResponse = {
  identifier_type: IdentifierType;
  identifier_value: string;
  source: string;
};

export type BookResponse = {
  academic_metadata?: AcademicMetadata | null;
  authors: AuthorSummary[];
  categories: CategorySummary[];
  cover_image_url?: string | null;
  created_at: string;
  description?: string | null;
  edition?: string | null;
  format: BookFormat;
  genres: string[];
  id: string;
  identifiers: BookIdentifierResponse[];
  isbn_10?: string | null;
  isbn_13?: string | null;
  language: string;
  metadata_status: MetadataStatus;
  page_count?: number | null;
  publication_year?: number | null;
  publisher?: PublisherSummary | null;
  subjects: string[];
  subtitle?: string | null;
  title: string;
  updated_at: string;
  work_id: string;
};

export type BookListResponse = {
  items: BookResponse[];
  next_cursor?: string | null;
};

export type ResolveIsbnResponse = {
  book?: BookResponse | null;
  isbn: string;
  provider: string;
  status: "found" | "not_found";
};

export type CategoryNode = CategorySummary & {
  children: CategoryNode[];
};

export type CategoryTreeResponse = {
  items: CategoryNode[];
};

export type AuthorListResponse = {
  items: AuthorSummary[];
  next_cursor?: string | null;
};

export type PublisherListResponse = {
  items: PublisherSummary[];
  next_cursor?: string | null;
};

export type ListingMode =
  | "sell"
  | "exchange"
  | "sell_exchange"
  | "donate"
  | "lend"
  | "rent"
  | "request"
  | "giveaway"
  | "bulk_sale";

export type ListingStatus =
  | "draft"
  | "pending_moderation"
  | "active"
  | "paused"
  | "reserved"
  | "completed"
  | "expired"
  | "suspended"
  | "rejected"
  | "deleted";

export type ConditionGrade =
  | "new_sealed"
  | "like_new"
  | "excellent"
  | "very_good"
  | "good"
  | "acceptable"
  | "poor"
  | "reference_only";

export type DeliveryMethod = "pickup" | "shipping";
export type MediaStatus =
  | "pending_upload"
  | "uploaded"
  | "processing"
  | "approved"
  | "rejected";

export type ListingCondition = {
  access_code_status?: string | null;
  answer_key_present?: boolean | null;
  collectible_notes?: string | null;
  condition: ConditionGrade;
  damage_details?: string | null;
  dust_jacket_present?: boolean | null;
  first_edition?: boolean;
  handwritten_notes?: boolean;
  highlighting_percent?: number | null;
  library_markings?: boolean;
  loose_binding?: boolean;
  missing_pages?: boolean;
  name_written_inside?: boolean;
  odor_or_smoke_exposure?: boolean;
  signed_by_author?: boolean;
  stains?: boolean;
  stickers?: boolean;
  supplemental_media_present?: boolean | null;
  torn_pages?: boolean;
  water_damage?: boolean;
  workbook_completion_percent?: number | null;
};

export type ListingLocationInput = {
  campus_pickup?: boolean;
  city: string;
  country: string;
  exact_latitude?: string | null;
  exact_longitude?: string | null;
  neighborhood?: string | null;
  pickup_notes_private?: string | null;
  public_area: string;
  state?: string | null;
};

export type ListingLocationPublicResponse = Omit<
  ListingLocationInput,
  "exact_latitude" | "exact_longitude" | "pickup_notes_private"
>;

export type ListingDeliveryMethod = {
  enabled?: boolean;
  method: DeliveryMethod;
  notes?: string | null;
  price_amount_cents?: number | null;
};

export type ListingImageInput = {
  alt_text?: string | null;
  is_primary?: boolean;
  media_id: string;
};

export type ListingCreateRequest = {
  book_id?: string | null;
  condition: ListingCondition;
  currency?: string;
  delivery_methods?: ListingDeliveryMethod[];
  description?: string | null;
  exchange_preferences?: string | null;
  images?: ListingImageInput[];
  isbn?: string | null;
  lending_duration_days?: number | null;
  listing_modes: ListingMode[];
  location: ListingLocationInput;
  negotiable?: boolean;
  price_amount_cents?: number | null;
  quantity?: number;
  rental_deposit_amount_cents?: number | null;
  return_policy?: string | null;
};

export type ListingUpdateRequest = Partial<
  Omit<ListingCreateRequest, "book_id" | "isbn">
>;

export type MediaUploadUrlRequest = {
  byte_size: number;
  checksum_sha256?: string | null;
  content_type: "image/jpeg" | "image/png" | "image/webp";
  filename: string;
};

export type MediaUploadUrlResponse = {
  expires_at: string;
  headers: Record<string, string>;
  id: string;
  storage_key: string;
  upload_url: string;
};

export type MediaAssetResponse = {
  byte_size: number;
  content_type: string;
  created_at: string;
  id: string;
  original_filename: string;
  public_url?: string | null;
  status: MediaStatus;
};

export type ListingImageResponse = {
  alt_text?: string | null;
  id: string;
  is_primary: boolean;
  media: MediaAssetResponse;
  public_url?: string | null;
  sort_order: number;
};

export type ListingInventoryResponse = {
  quantity_available: number;
  quantity_total: number;
};

export type ListingPriceHistoryResponse = {
  changed_at: string;
  currency: string;
  id: string;
  new_amount_cents?: number | null;
  old_amount_cents?: number | null;
  reason: string;
};

export type ListingResponse = {
  book: { id: string; title: string };
  condition?: ListingCondition | null;
  created_at: string;
  currency: string;
  delivery_methods: ListingDeliveryMethod[];
  description?: string | null;
  exchange_preferences?: string | null;
  id: string;
  images: ListingImageResponse[];
  inventory?: ListingInventoryResponse | null;
  lending_duration_days?: number | null;
  listing_modes: ListingMode[];
  location?: ListingLocationPublicResponse | null;
  negotiable: boolean;
  price_amount_cents?: number | null;
  price_history: ListingPriceHistoryResponse[];
  quality_score: number;
  rental_deposit_amount_cents?: number | null;
  return_policy?: string | null;
  seller: { id: string };
  status: ListingStatus;
  title: string;
  updated_at: string;
};

export type SearchSort =
  | "relevance"
  | "nearest"
  | "newest"
  | "lowest_price"
  | "highest_price"
  | "best_condition"
  | "most_saved";

export type SearchSuggestionType =
  | "title"
  | "author"
  | "isbn"
  | "category"
  | "location";

export type FollowTargetType =
  | "user"
  | "seller"
  | "author"
  | "genre"
  | "community"
  | "college";

export type ListingSearchParams = {
  actual_photos?: boolean | null;
  author?: string | null;
  campus_pickup?: boolean | null;
  category?: string | null;
  city?: string | null;
  condition?: ConditionGrade | null;
  country?: string | null;
  cursor?: string | null;
  delivery_method?: DeliveryMethod | null;
  distance_km?: number | null;
  first_edition?: boolean | null;
  format?: string | null;
  free_only?: boolean | null;
  isbn?: string | null;
  language?: string | null;
  latitude?: number | null;
  limit?: number | null;
  listing_mode?: ListingMode | null;
  longitude?: number | null;
  max_price_amount_cents?: number | null;
  min_price_amount_cents?: number | null;
  negotiable?: boolean | null;
  publication_year?: number | null;
  publisher?: string | null;
  q?: string | null;
  signed_copy?: boolean | null;
  sort?: SearchSort | null;
  state?: string | null;
};

export type SearchListingBookSummary = {
  authors: string[];
  categories: string[];
  id: string;
  isbn_10?: string | null;
  isbn_13?: string | null;
  title: string;
};

export type ListingSearchResult = {
  book: SearchListingBookSummary;
  condition?: ConditionGrade | null;
  created_at: string;
  currency: string;
  delivery_methods: DeliveryMethod[];
  distance_km?: number | null;
  favorite_count: number;
  id: string;
  image_url?: string | null;
  listing_modes: ListingMode[];
  location?: ListingLocationPublicResponse | null;
  negotiable: boolean;
  price_amount_cents?: number | null;
  quality_score: number;
  seller: { id: string };
  title: string;
};

export type ListingSearchResponse = {
  items: ListingSearchResult[];
  next_cursor?: string | null;
  result_count: number;
};

export type SearchSuggestion = {
  text: string;
  type: SearchSuggestionType;
};

export type SearchSuggestionResponse = {
  items: SearchSuggestion[];
};

export type SavedSearchCreateRequest = {
  filters?: Record<string, unknown>;
  name: string;
  notifications_enabled?: boolean;
  query?: string | null;
  sort?: SearchSort;
};

export type SavedSearchResponse = {
  created_at: string;
  filters: Record<string, unknown>;
  id: string;
  last_matched_at?: string | null;
  last_result_count: number;
  name: string;
  notifications_enabled: boolean;
  query?: string | null;
  sort: SearchSort;
};

export type SavedSearchListResponse = {
  items: SavedSearchResponse[];
};

export type WishlistItemResponse = {
  book: SearchListingBookSummary;
  created_at: string;
  id: string;
};

export type ListingFavoriteResponse = {
  created_at: string;
  id: string;
  listing_id: string;
};

export type FollowCreateRequest = {
  target_id: string;
  target_label?: string | null;
  target_type: FollowTargetType;
};

export type FollowResponse = {
  created_at: string;
  id: string;
  target_id: string;
  target_label?: string | null;
  target_type: FollowTargetType;
};

export type ChatRequestStatus = "pending" | "accepted" | "declined" | "blocked";
export type ConversationStatus = "active" | "blocked" | "closed";
export type ConversationMemberRole = "requester" | "recipient";
export type ConversationMemberStatus =
  | "active"
  | "muted"
  | "archived"
  | "blocked";
export type MessageType = "text" | "image" | "listing" | "system";
export type MessageAttachmentType = "image";

export type ChatUserSummary = {
  id: string;
};

export type ChatRequestCreateRequest = {
  listing_id: string;
  message?: string | null;
};

export type ChatRequestActionRequest = {
  message?: string | null;
};

export type ChatRequestResponse = {
  conversation_id?: string | null;
  created_at: string;
  id: string;
  initial_message?: string | null;
  listing_id: string;
  recipient: ChatUserSummary;
  requester: ChatUserSummary;
  responded_at?: string | null;
  response_message?: string | null;
  status: ChatRequestStatus;
};

export type ConversationMemberResponse = {
  role: ConversationMemberRole;
  status: ConversationMemberStatus;
  user: ChatUserSummary;
};

export type ConversationResponse = {
  created_at: string;
  id: string;
  last_message_at?: string | null;
  listing_id?: string | null;
  members: ConversationMemberResponse[];
  status: ConversationStatus;
  unread_count: number;
};

export type ConversationListResponse = {
  items: ConversationResponse[];
  next_cursor?: string | null;
};

export type MessageAttachmentInput = {
  attachment_type?: MessageAttachmentType;
  media_id: string;
  metadata?: Record<string, unknown>;
};

export type MessageCreateRequest = {
  attachments?: MessageAttachmentInput[];
  body?: string | null;
  client_message_id: string;
  listing_id?: string | null;
  message_type?: MessageType;
  metadata?: Record<string, unknown>;
};

export type MessageAttachmentResponse = {
  attachment_type: MessageAttachmentType;
  id: string;
  media_id: string;
  metadata: Record<string, unknown>;
  public_url?: string | null;
  sort_order: number;
};

export type MessageResponse = {
  attachments: MessageAttachmentResponse[];
  body?: string | null;
  client_message_id?: string | null;
  conversation_id: string;
  created_at: string;
  id: string;
  listing_id?: string | null;
  message_type: MessageType;
  metadata: Record<string, unknown>;
  read_by_user_ids: string[];
  sender: ChatUserSummary;
};

export type MessageListResponse = {
  items: MessageResponse[];
  next_cursor?: string | null;
};

export type MessageReportRequest = {
  details?: string | null;
  reason:
    | "spam"
    | "scam"
    | "harassment"
    | "unsafe_content"
    | "personal_information"
    | "other";
};

export type MessageReportResponse = {
  created_at: string;
  id: string;
  message_id: string;
  reason: string;
  status: string;
};

export type NotificationType =
  | "chat_request"
  | "chat_accepted"
  | "chat_declined"
  | "message"
  | "saved_search_match"
  | "system";
export type NotificationStatus = "unread" | "read" | "archived";
export type NotificationChannel = "in_app" | "email" | "push";
export type NotificationDeliveryStatus =
  | "pending"
  | "sent"
  | "failed"
  | "suppressed";

export type NotificationDeliveryResponse = {
  channel: NotificationChannel;
  id: string;
  status: NotificationDeliveryStatus;
};

export type NotificationResponse = {
  body: string;
  created_at: string;
  data: Record<string, unknown>;
  deliveries: NotificationDeliveryResponse[];
  id: string;
  read_at?: string | null;
  related_entity_id?: string | null;
  related_entity_type?: string | null;
  status: NotificationStatus;
  title: string;
  type: NotificationType;
};

export type NotificationListResponse = {
  items: NotificationResponse[];
  next_cursor?: string | null;
};

export type NotificationPreferenceResponse = {
  chat_requests_enabled: boolean;
  email_enabled: boolean;
  id: string;
  in_app_enabled: boolean;
  marketing_enabled: boolean;
  messages_enabled: boolean;
  push_enabled: boolean;
  quiet_hours_end?: string | null;
  quiet_hours_start?: string | null;
};

export type NotificationPreferenceUpdateRequest = Partial<
  Omit<NotificationPreferenceResponse, "id">
>;

export type OfferType = "price" | "counter" | "exchange" | "bundle";
export type OfferStatus =
  | "pending"
  | "countered"
  | "accepted"
  | "rejected"
  | "withdrawn"
  | "expired";
export type FulfillmentMethod = "pickup" | "shipping";
export type TransactionStatus =
  | "reserved"
  | "ready_for_pickup"
  | "completed"
  | "cancelled"
  | "disputed";
export type PickupStatus = "proposed" | "confirmed" | "completed" | "cancelled";
export type ReviewType = "buyer_reviews_seller" | "seller_reviews_buyer";

export type CommerceUserSummary = {
  id: string;
};

export type ExchangeOfferItemInput = {
  cash_adjustment_cents?: number | null;
  condition_note?: string | null;
  offered_listing_id?: string | null;
  title: string;
};

export type OfferCreateRequest = {
  amount_cents?: number | null;
  bundle_listing_ids?: string[];
  currency?: string;
  exchange_items?: ExchangeOfferItemInput[];
  expires_at?: string | null;
  fulfillment_method?: FulfillmentMethod;
  listing_id: string;
  message?: string | null;
  offer_type?: OfferType;
  quantity?: number;
};

export type CounterOfferRequest = {
  amount_cents: number;
  currency?: string;
  expires_at?: string | null;
  fulfillment_method?: FulfillmentMethod | null;
  message?: string | null;
  quantity?: number | null;
};

export type EmptyActionRequest = {
  message?: string | null;
};

export type ExchangeOfferItemResponse = {
  cash_adjustment_cents?: number | null;
  condition_note?: string | null;
  id: string;
  offered_listing_id?: string | null;
  title: string;
};

export type OfferResponse = {
  amount_cents?: number | null;
  bundle_listing_ids: string[];
  buyer: CommerceUserSummary;
  created_at: string;
  currency: string;
  exchange_items: ExchangeOfferItemResponse[];
  expires_at: string;
  fulfillment_method: FulfillmentMethod;
  id: string;
  listing_id: string;
  message?: string | null;
  offer_type: OfferType;
  parent_offer_id?: string | null;
  proposer: CommerceUserSummary;
  quantity: number;
  responded_at?: string | null;
  seller: CommerceUserSummary;
  status: OfferStatus;
  transaction_id?: string | null;
};

export type PickupCreateRequest = {
  exact_address?: string | null;
  exact_latitude?: string | null;
  exact_longitude?: string | null;
  pickup_notes_private?: string | null;
  proposed_end_at?: string | null;
  proposed_start_at?: string | null;
  public_location_label?: string | null;
  transaction_id: string;
};

export type PickupConfirmRequest = {
  message?: string | null;
};

export type PickupResponse = {
  confirmed_at?: string | null;
  confirmed_by_user_id?: string | null;
  exact_address?: string | null;
  exact_latitude?: string | null;
  exact_longitude?: string | null;
  handover_code?: string | null;
  id: string;
  pickup_notes_private?: string | null;
  proposed_by_user_id: string;
  proposed_end_at?: string | null;
  proposed_start_at?: string | null;
  public_location_label: string;
  status: PickupStatus;
  transaction_id: string;
};

export type TransactionResponse = {
  amount_cents?: number | null;
  buyer: CommerceUserSummary;
  completed_at?: string | null;
  created_at: string;
  currency: string;
  fulfillment_method: FulfillmentMethod;
  id: string;
  listing_id: string;
  offer_id: string;
  pickup?: PickupResponse | null;
  quantity: number;
  seller: CommerceUserSummary;
  status: TransactionStatus;
};

export type TransactionCompleteRequest = {
  handover_code?: string | null;
};

export type ReviewDimensionInput = {
  dimension: string;
  rating: number;
};

export type ReviewCreateRequest = {
  comment?: string | null;
  dimensions?: ReviewDimensionInput[];
  rating: number;
  transaction_id: string;
};

export type ReviewDimensionResponse = {
  dimension: string;
  id: string;
  rating: number;
};

export type ReviewResponse = {
  comment?: string | null;
  created_at: string;
  dimensions: ReviewDimensionResponse[];
  id: string;
  rating: number;
  review_type: ReviewType;
  reviewee: CommerceUserSummary;
  reviewer: CommerceUserSummary;
  status: string;
  transaction_id: string;
};

export type ReportTargetType =
  | "user"
  | "listing"
  | "message"
  | "review"
  | "copyright";
export type ReportSeverity = "low" | "medium" | "high" | "critical";
export type ReportStatus =
  | "open"
  | "in_review"
  | "resolved"
  | "dismissed"
  | "appealed";
export type ReportReason =
  | "fake_listing"
  | "misleading_condition"
  | "piracy"
  | "counterfeit"
  | "scam"
  | "harassment"
  | "hate_speech"
  | "sexual_content"
  | "child_safety"
  | "spam"
  | "fake_review"
  | "payment_fraud"
  | "stolen_image"
  | "copyright_infringement"
  | "personal_information"
  | "dangerous_meetup"
  | "other";
export type ModerationCaseStatus =
  | "open"
  | "in_review"
  | "actioned"
  | "closed"
  | "appealed";
export type ModerationActionType =
  | "warn"
  | "remove_content"
  | "suspend"
  | "ban"
  | "dismiss"
  | "restore"
  | "appeal_submitted"
  | "note";

export type CopyrightClaimInput = {
  claimant_email: string;
  claimant_statement: string;
  work_title: string;
};

export type ReportCreateRequest = {
  copyright_claim?: CopyrightClaimInput | null;
  description?: string | null;
  device_fingerprint?: string | null;
  evidence?: Record<string, unknown>;
  reason: ReportReason;
  target_id?: string | null;
  target_type: ReportTargetType;
};

export type ReportAppealRequest = {
  statement: string;
};

export type ModerationActionRequest = {
  action_type: Exclude<ModerationActionType, "appeal_submitted">;
  duration_until?: string | null;
  metadata?: Record<string, unknown>;
  reason?: string | null;
};

export type TrustUserSummary = {
  id: string;
};

export type ReportResponse = {
  case_id?: string | null;
  created_at: string;
  description?: string | null;
  evidence: Record<string, unknown>;
  id: string;
  reason: string;
  reporter: TrustUserSummary;
  severity: ReportSeverity;
  status: ReportStatus;
  target: {
    id?: string | null;
    type: ReportTargetType;
  };
};

export type ModerationActionResponse = {
  action_type: ModerationActionType;
  actor_user_id?: string | null;
  created_at: string;
  duration_until?: string | null;
  evidence_snapshot: Record<string, unknown>;
  id: string;
  metadata: Record<string, unknown>;
  moderator_user_id?: string | null;
  reason?: string | null;
};

export type ModerationCaseResponse = {
  actions: ModerationActionResponse[];
  assigned_moderator_user_id?: string | null;
  created_at: string;
  evidence_snapshot: Record<string, unknown>;
  id: string;
  priority_score: number;
  report: ReportResponse;
  severity: ReportSeverity;
  status: ModerationCaseStatus;
  summary: string;
};

export type ModerationCaseListResponse = {
  items: ModerationCaseResponse[];
  next_cursor?: string | null;
};

export type ConversationEvidenceMessage = {
  body?: string | null;
  created_at: string;
  id: string;
  message_type: string;
  sender_user_id: string;
};

export type ConversationEvidenceResponse = {
  case_id: string;
  conversation_id: string;
  messages: ConversationEvidenceMessage[];
  report_id: string;
};

export type ModerationUserResponse = {
  email: string;
  id: string;
  report_count: number;
  status: string;
};

export type ModerationListingResponse = {
  id: string;
  report_count: number;
  seller_user_id: string;
  status: string;
  title: string;
};

export type ModerationRuleConfigResponse = {
  action_types: string[];
  moderator_roles: string[];
  severity_by_reason: Record<ReportReason, ReportSeverity>;
};

export type CommunityVisibility =
  | "public"
  | "private"
  | "secret"
  | "institution_verified";
export type CommunityMembershipPolicy =
  | "open"
  | "request"
  | "approval"
  | "institution_verified";
export type CommunityType =
  | "college"
  | "university"
  | "school"
  | "area"
  | "city"
  | "apartment"
  | "workplace"
  | "language"
  | "genre"
  | "author"
  | "series"
  | "book"
  | "exam"
  | "course"
  | "profession"
  | "age_group"
  | "reading_goal"
  | "library"
  | "bookstore"
  | "publisher"
  | "social_cause"
  | "local"
  | "general";
export type CommunityMemberStatus =
  | "pending"
  | "active"
  | "rejected"
  | "banned"
  | "muted";
export type CommunityChannelType =
  | "general"
  | "announcements"
  | "marketplace"
  | "questions"
  | "resources";
export type CommunityChannelVisibility = "public" | "members" | "moderators";
export type CommunityPostType =
  | "text"
  | "review"
  | "photo"
  | "video"
  | "poll"
  | "question"
  | "recommendation"
  | "quote"
  | "reading_update"
  | "listing"
  | "exchange_request"
  | "donation_request"
  | "event"
  | "challenge"
  | "resource"
  | "announcement";
export type CommunityPostStatus =
  | "published"
  | "pending_review"
  | "hidden"
  | "deleted";
export type PostReactionType =
  | "like"
  | "love"
  | "insightful"
  | "upvote"
  | "celebrate";
export type CommunityReportTargetType =
  | "community"
  | "post"
  | "comment"
  | "member";
export type CommunityReportStatus = "open" | "resolved" | "dismissed";

export type CommunityRuleInput = {
  body: string;
  title: string;
};

export type CommunityChannelInput = {
  channel_type?: CommunityChannelType;
  name: string;
  slug?: string | null;
  visibility?: CommunityChannelVisibility;
};

export type CommunityCreateRequest = {
  book_id?: string | null;
  channels?: CommunityChannelInput[];
  city?: string | null;
  community_type?: CommunityType;
  country?: string | null;
  cover_image_url?: string | null;
  description?: string | null;
  genre?: string | null;
  institution?: string | null;
  language?: string | null;
  membership_policy?: CommunityMembershipPolicy | null;
  name: string;
  rules?: CommunityRuleInput[];
  settings?: Record<string, unknown>;
  slug?: string | null;
  state?: string | null;
  visibility?: CommunityVisibility;
};

export type CommunityJoinRequest = {
  answers?: Record<string, unknown>;
};

export type CommunityApproveMemberRequest = {
  role?: "member" | "moderator";
  user_id: string;
};

export type CommunityPostCreateRequest = {
  body?: string | null;
  channel_id?: string | null;
  is_announcement?: boolean;
  is_pinned?: boolean;
  listing_id?: string | null;
  poll_options?: string[];
  post_type?: CommunityPostType;
  title?: string | null;
};

export type PostCommentCreateRequest = {
  body: string;
  parent_comment_id?: string | null;
};

export type PostReactionRequest = {
  reaction_type?: PostReactionType;
};

export type CommunityReportCreateRequest = {
  details?: string | null;
  reason: string;
  target_id?: string | null;
  target_type: CommunityReportTargetType;
};

export type CommunityUserSummary = {
  id: string;
};

export type CommunityRoleResponse = {
  id: string;
  is_default: boolean;
  name: string;
  permissions: string[];
};

export type CommunityMemberResponse = {
  joined_at?: string | null;
  role: string;
  status: CommunityMemberStatus;
  user: CommunityUserSummary;
};

export type CommunityRuleResponse = {
  body: string;
  enabled: boolean;
  id: string;
  sort_order: number;
  title: string;
};

export type CommunityChannelResponse = {
  channel_type: CommunityChannelType;
  id: string;
  name: string;
  slug: string;
  visibility: CommunityChannelVisibility;
};

export type CommunitySummaryResponse = {
  book_id?: string | null;
  city?: string | null;
  community_type: CommunityType;
  country?: string | null;
  description?: string | null;
  genre?: string | null;
  id: string;
  institution?: string | null;
  member_count: number;
  name: string;
  slug: string;
  state?: string | null;
  visibility: CommunityVisibility;
  viewer_membership_status?: CommunityMemberStatus | null;
};

export type CommunityResponse = CommunitySummaryResponse & {
  channels: CommunityChannelResponse[];
  membership_policy: CommunityMembershipPolicy;
  owner: CommunityUserSummary;
  rules: CommunityRuleResponse[];
};

export type CommunityListResponse = {
  items: CommunitySummaryResponse[];
  next_cursor?: string | null;
};

export type CommunityPostResponse = {
  author: CommunityUserSummary;
  body?: string | null;
  channel_id?: string | null;
  comment_count: number;
  community_id: string;
  created_at: string;
  id: string;
  is_announcement: boolean;
  is_pinned: boolean;
  listing_id?: string | null;
  poll: Record<string, unknown>;
  post_type: CommunityPostType;
  reaction_counts: Record<string, number>;
  status: CommunityPostStatus;
  title?: string | null;
  viewer_reaction?: PostReactionType | null;
};

export type CommunityFeedResponse = {
  items: CommunityPostResponse[];
  next_cursor?: string | null;
};

export type PostCommentResponse = {
  author: CommunityUserSummary;
  body: string;
  created_at: string;
  id: string;
  parent_comment_id?: string | null;
  post_id: string;
  status: string;
};

export type PostReactionResponse = {
  id: string;
  post_id: string;
  reaction_type: PostReactionType;
  user_id: string;
};

export type CommunityMarketplaceResponse = {
  community_id: string;
  items: ListingResponse[];
  next_cursor?: string | null;
};

export type CommunityReportResponse = {
  community_id: string;
  created_at: string;
  id: string;
  reason: string;
  status: CommunityReportStatus;
  target_id?: string | null;
  target_type: CommunityReportTargetType;
};

export type ClubVisibility = "public" | "private";
export type BookClubStatus = "active" | "archived" | "suspended";
export type ClubBookStatus = "current" | "next" | "past";
export type BookNominationStatus = "active" | "selected" | "withdrawn";
export type MilestonePositionType =
  | "chapter"
  | "page"
  | "percent"
  | "whole_book";
export type BuddyReadStatus = "active" | "completed" | "cancelled";
export type ReadalongStatus =
  | "scheduled"
  | "active"
  | "completed"
  | "cancelled";
export type EventType =
  | "book_club_meeting"
  | "book_exchange"
  | "used_book_fair"
  | "donation_drive"
  | "author_meetup"
  | "signing"
  | "reading_session"
  | "silent_reading"
  | "childrens_story_session"
  | "library_event"
  | "college_textbook_sale"
  | "writing_workshop"
  | "poetry_reading"
  | "online_discussion"
  | "author_interview";
export type EventStatus = "scheduled" | "cancelled" | "completed";
export type EventRSVPStatus = "going" | "cancelled" | "waitlisted";

export type ClubUserSummary = {
  id: string;
};

export type ClubBookSummary = {
  id: string;
  title: string;
};

export type BookClubCreateRequest = {
  community_id?: string | null;
  description?: string | null;
  name: string;
  settings?: Record<string, unknown>;
  slug?: string | null;
  timezone?: string;
  visibility?: ClubVisibility;
};

export type ClubBookCreateRequest = {
  book_id: string;
  discussion_guide?: string | null;
  end_date?: string | null;
  start_date?: string | null;
  status?: ClubBookStatus;
};

export type BookNominationCreateRequest = {
  book_id: string;
  cycle_key?: string;
  note?: string | null;
};

export type BookVoteRequest = {
  cycle_key?: string;
  nomination_id: string;
  rank: number;
};

export type SelectClubBookRequest = {
  cycle_key?: string;
  end_date?: string | null;
  start_date?: string | null;
  status?: ClubBookStatus;
};

export type ReadingMilestoneCreateRequest = {
  discussion_prompt?: string | null;
  ends_at?: string | null;
  position_type: MilestonePositionType;
  position_value: number;
  starts_at?: string | null;
  title: string;
};

export type BuddyReadCreateRequest = {
  book_id: string;
  deadline_at?: string | null;
  max_participants?: number;
  title: string;
  visibility?: ClubVisibility;
};

export type BuddyReadProgressRequest = {
  position_type?: MilestonePositionType;
  position_value: number;
};

export type ReadalongCreateRequest = {
  book_id: string;
  chapter_schedule?: Record<string, unknown>[];
  community_id?: string | null;
  description?: string | null;
  ends_at?: string | null;
  starts_at?: string | null;
  timezone?: string;
  title: string;
  visibility?: ClubVisibility;
};

export type EventCreateRequest = {
  address?: string | null;
  capacity?: number | null;
  club_id?: string | null;
  community_id?: string | null;
  description?: string | null;
  ends_at: string;
  event_type: EventType;
  location_name?: string | null;
  metadata?: Record<string, unknown>;
  online_url?: string | null;
  starts_at: string;
  timezone: string;
  title: string;
  visibility?: ClubVisibility;
};

export type EventUpdateRequest = {
  capacity?: number | null;
  description?: string | null;
  ends_at?: string | null;
  location_name?: string | null;
  online_url?: string | null;
  starts_at?: string | null;
  status?: EventStatus | null;
  timezone?: string | null;
  title?: string | null;
};

export type EventRSVPRequest = {
  guest_count?: number;
  note?: string | null;
};

export type EventCheckinRequest = {
  checkin_code: string;
  user_id: string;
};

export type BookClubResponse = {
  community_id?: string | null;
  current_book?: ClubBookSummary | null;
  description?: string | null;
  id: string;
  member_context?: string | null;
  name: string;
  next_book?: ClubBookSummary | null;
  owner: ClubUserSummary;
  slug: string;
  status: BookClubStatus;
  timezone: string;
  visibility: ClubVisibility;
};

export type BookClubListResponse = {
  items: BookClubResponse[];
  next_cursor?: string | null;
};

export type ClubBookResponse = {
  available_listings: ListingResponse[];
  book: ClubBookSummary;
  discussion_guide?: string | null;
  end_date?: string | null;
  id: string;
  selected_at?: string | null;
  sequence: number;
  start_date?: string | null;
  status: ClubBookStatus;
};

export type ClubBookListResponse = {
  items: ClubBookResponse[];
};

export type BookNominationResponse = {
  book: ClubBookSummary;
  cycle_key: string;
  id: string;
  note?: string | null;
  nominator: ClubUserSummary;
  status: BookNominationStatus;
  vote_count: number;
};

export type BookVoteResponse = {
  cycle_key: string;
  id: string;
  nomination_id: string;
  rank: number;
  voter: ClubUserSummary;
};

export type ReadingMilestoneResponse = {
  discussion_prompt?: string | null;
  ends_at?: string | null;
  id: string;
  position_type: MilestonePositionType;
  position_value: number;
  spoiler_locked: boolean;
  starts_at?: string | null;
  title: string;
};

export type ReadingMilestoneListResponse = {
  items: ReadingMilestoneResponse[];
};

export type BuddyReadResponse = {
  book: ClubBookSummary;
  deadline_at?: string | null;
  id: string;
  max_participants: number;
  participant_user_ids: string[];
  progress: Record<string, unknown>;
  status: BuddyReadStatus;
  title: string;
  visibility: ClubVisibility;
};

export type ReadalongResponse = {
  book: ClubBookSummary;
  chapter_schedule: Record<string, unknown>[];
  community_id?: string | null;
  description?: string | null;
  ends_at?: string | null;
  host: ClubUserSummary;
  id: string;
  starts_at?: string | null;
  status: ReadalongStatus;
  timezone: string;
  title: string;
  visibility: ClubVisibility;
};

export type EventResponse = {
  capacity?: number | null;
  checkin_code?: string | null;
  club_id?: string | null;
  community_id?: string | null;
  description?: string | null;
  ends_at: string;
  event_type: EventType;
  id: string;
  location_name?: string | null;
  online_url?: string | null;
  organizer: ClubUserSummary;
  rsvp_count: number;
  starts_at: string;
  status: EventStatus;
  timezone: string;
  title: string;
  visibility: ClubVisibility;
  waitlist_count: number;
};

export type EventListResponse = {
  items: EventResponse[];
  next_cursor?: string | null;
};

export type EventRSVPResponse = {
  event_id: string;
  guest_count: number;
  id: string;
  status: EventRSVPStatus;
  user: ClubUserSummary;
  waitlist_position?: number | null;
};

export type EventCheckinResponse = {
  checked_in_at: string;
  checked_in_by_user_id: string;
  event_id: string;
  id: string;
  user_id: string;
};

export type ReadingShelfType =
  | "want_to_read"
  | "currently_reading"
  | "finished"
  | "did_not_finish"
  | "owned"
  | "previously_owned"
  | "available_for_exchange"
  | "available_for_lending"
  | "favorites"
  | "academic_books"
  | "rare_collection"
  | "custom";

export type ReadingShelfVisibility = "public" | "private";
export type ReadingStatus =
  | "want_to_read"
  | "currently_reading"
  | "finished"
  | "did_not_finish";
export type ReadingNoteType = "note" | "highlight" | "quote";
export type ReadingNoteVisibility = "private" | "public";
export type ReadingGoalType =
  | "books_per_year"
  | "pages_per_month"
  | "minutes_per_day"
  | "genre"
  | "author"
  | "language"
  | "community_challenge"
  | "institution_challenge";
export type ReadingGoalScope = "personal" | "community" | "institution";
export type ReadingGoalStatus = "active" | "completed" | "cancelled";
export type ReadingStatisticPeriod = "month" | "year" | "all_time";

export type ReadingBookSummary = {
  authors: string[];
  genres: string[];
  id: string;
  page_count?: number | null;
  title: string;
};

export type ReadingShelfCreateRequest = {
  name: string;
  slug?: string | null;
  visibility?: ReadingShelfVisibility;
};

export type ReadingShelfItemCreateRequest = {
  book_id: string;
  note?: string | null;
  sort_order?: number;
};

export type ReadingShelfItemResponse = {
  added_at: string;
  book: ReadingBookSummary;
  id: string;
  note?: string | null;
  sort_order: number;
};

export type ReadingShelfResponse = {
  id: string;
  is_system: boolean;
  items: ReadingShelfItemResponse[];
  name: string;
  shelf_type: ReadingShelfType;
  slug: string;
  sort_order: number;
  visibility: ReadingShelfVisibility;
};

export type ReadingShelfListResponse = {
  items: ReadingShelfResponse[];
};

export type ReadingProgressUpdateRequest = {
  current_page?: number | null;
  finished_on?: string | null;
  percent_complete?: number | null;
  progressed_on?: string | null;
  rating?: number | null;
  reading_minutes?: number | null;
  reread_count?: number | null;
  review_text?: string | null;
  started_on?: string | null;
  status: ReadingStatus;
};

export type ReadingProgressResponse = {
  book: ReadingBookSummary;
  current_page?: number | null;
  daily_minutes: Record<string, number>;
  finished_on?: string | null;
  id: string;
  last_progress_at?: string | null;
  percent_complete?: number | null;
  rating?: number | null;
  reread_count: number;
  review_text?: string | null;
  started_on?: string | null;
  status: ReadingStatus;
  total_reading_minutes: number;
};

export type ReadingProgressListResponse = {
  items: ReadingProgressResponse[];
};

export type ReadingNoteCreateRequest = {
  body: string;
  book_id: string;
  client_note_id?: string | null;
  note_type?: ReadingNoteType;
  page_number?: number | null;
  percent_complete?: number | null;
  visibility?: ReadingNoteVisibility;
};

export type ReadingNoteResponse = {
  body: string;
  book: ReadingBookSummary;
  created_at: string;
  id: string;
  note_type: ReadingNoteType;
  page_number?: number | null;
  percent_complete?: number | null;
  visibility: ReadingNoteVisibility;
};

export type ReadingNoteListResponse = {
  items: ReadingNoteResponse[];
};

export type ReadingGoalCreateRequest = {
  community_id?: string | null;
  goal_type: ReadingGoalType;
  period_end: string;
  period_start: string;
  scope?: ReadingGoalScope;
  target_metadata?: Record<string, unknown>;
  target_value: number;
  timezone?: string;
};

export type ReadingGoalResponse = {
  community_id?: string | null;
  current_value: number;
  goal_type: ReadingGoalType;
  id: string;
  period_end: string;
  period_start: string;
  scope: ReadingGoalScope;
  status: ReadingGoalStatus;
  target_metadata: Record<string, unknown>;
  target_value: number;
  timezone: string;
};

export type ReadingGoalListResponse = {
  items: ReadingGoalResponse[];
};

export type ReadingStatisticRecomputeRequest = {
  period_start?: string | null;
  period_type?: ReadingStatisticPeriod;
  timezone?: string;
};

export type ReadingStatisticResponse = {
  authors: Record<string, number>;
  books_completed: number;
  computed_at: string;
  genres: Record<string, number>;
  id: string;
  minutes_read: number;
  monthly_progress: Record<string, unknown>;
  pages_read: number;
  period_end: string;
  period_start: string;
  period_type: ReadingStatisticPeriod;
  reading_streak_days: number;
  timezone: string;
  year_summary: Record<string, unknown>;
};

export type ReadingStatisticListResponse = {
  items: ReadingStatisticResponse[];
};
