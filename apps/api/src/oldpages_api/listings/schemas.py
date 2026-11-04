from __future__ import annotations

from datetime import datetime
from typing import Literal

ListingScope = Literal["personal", "business", "institution"]
ListingVisibility = Literal["public", "private", "business_only", "institution_only"]

VISIBILITY_BY_SCOPE: dict[str, list[str]] = {
    "personal":    ["public", "private"],
    "business":    ["public", "business_only"],
    "institution": ["public", "institution_only"],
}

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ListingMode = Literal[
    "sell",
    "exchange",
    "donate",
    "lend",
    "rent",
    "request",
]
ListingStatus = Literal[
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
]
ConditionGrade = Literal[
    "new_sealed",
    "like_new",
    "excellent",
    "very_good",
    "good",
    "acceptable",
    "poor",
    "reference_only",
]
DeliveryMethod = Literal["pickup", "shipping"]
MediaStatus = Literal["pending_upload", "uploaded", "processing", "approved", "rejected"]

PRICE_REQUIRED_MODES = {"sell", "rent"}
PRICELESS_MODES = {"donate", "request"}


class ListingConditionInput(BaseModel):
    condition: ConditionGrade
    damage_details: str | None = Field(default=None, max_length=4000)
    highlighting_percent: int | None = Field(default=None, ge=0, le=100)
    handwritten_notes: bool = False
    name_written_inside: bool = False
    torn_pages: bool = False
    missing_pages: bool = False
    loose_binding: bool = False
    water_damage: bool = False
    stains: bool = False
    odor_or_smoke_exposure: bool = False
    library_markings: bool = False
    stickers: bool = False
    dust_jacket_present: bool | None = None
    supplemental_media_present: bool | None = None
    access_code_status: str | None = Field(default=None, max_length=80)
    answer_key_present: bool | None = None
    workbook_completion_percent: int | None = Field(default=None, ge=0, le=100)
    signed_by_author: bool = False
    first_edition: bool = False
    collectible_notes: str | None = Field(default=None, max_length=4000)


class ListingLocationInput(BaseModel):
    country: str = Field(min_length=2, max_length=80)
    state: str | None = Field(default=None, max_length=120)
    city: str = Field(min_length=1, max_length=120)
    neighborhood: str | None = Field(default=None, max_length=120)
    public_area: str = Field(min_length=1, max_length=180)
    campus_pickup: bool = False
    exact_latitude: str | None = Field(default=None, max_length=40)
    exact_longitude: str | None = Field(default=None, max_length=40)
    pickup_notes_private: str | None = Field(default=None, max_length=4000)


class ListingDeliveryMethodInput(BaseModel):
    method: DeliveryMethod
    enabled: bool = True
    price_amount_cents: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=500)


class ListingImageInput(BaseModel):
    media_id: str = Field(min_length=1, max_length=26)
    alt_text: str | None = Field(default=None, max_length=280)
    is_primary: bool = False


class ListingCreateRequest(BaseModel):
    book_id: str | None = Field(default=None, max_length=26)
    isbn: str | None = Field(default=None, max_length=32)
    book_title: str | None = Field(default=None, max_length=500)
    book_author: str | None = Field(default=None, max_length=240)
    listing_modes: list[ListingMode] = Field(min_length=1, max_length=4)
    description: str | None = Field(default=None, max_length=8000)
    price_amount_cents: int | None = Field(default=None, ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    negotiable: bool = True
    return_policy: str | None = Field(default=None, max_length=500)
    scope: ListingScope = "personal"
    visibility: ListingVisibility = "public"
    business_profile_id: str | None = Field(default=None, max_length=26)
    institution_id: str | None = Field(default=None, max_length=26)
    open_to_exchange: bool = False
    exchange_preferences: str | None = Field(default=None, max_length=500)
    lending_duration_days: int | None = Field(default=None, ge=1, le=365)
    rental_fee_per_day_cents: int | None = Field(default=None, ge=0)
    rental_deposit_amount_cents: int | None = Field(default=None, ge=0)
    quantity: int = Field(default=1, ge=1)
    condition: ListingConditionInput
    location: ListingLocationInput
    delivery_methods: list[ListingDeliveryMethodInput] = Field(default_factory=list, max_length=2)
    images: list[ListingImageInput] = Field(default_factory=list, max_length=12)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("listing_modes")
    @classmethod
    def dedupe_modes(cls, value: list[ListingMode]) -> list[ListingMode]:
        deduped: list[ListingMode] = []
        for item in value:
            if item not in deduped:
                deduped.append(item)
        return deduped

    @model_validator(mode="after")
    def validate_business_rules(self) -> ListingCreateRequest:
        if not self.book_id and not self.isbn and not self.book_title:
            raise ValueError("Either book_id, isbn, or book_title is required.")
        validate_price_rules(self.listing_modes, self.price_amount_cents)
        allowed = VISIBILITY_BY_SCOPE.get(self.scope, [])
        if self.visibility not in allowed:
            raise ValueError(
                f"Visibility '{self.visibility}' is not valid for scope '{self.scope}'. "
                f"Allowed: {allowed}"
            )
        if self.scope == "business" and not self.business_profile_id:
            raise ValueError("business_profile_id is required when scope is 'business'.")
        if self.scope == "institution" and not self.institution_id:
            raise ValueError("institution_id is required when scope is 'institution'.")
        return self


class ListingUpdateRequest(BaseModel):
    listing_modes: list[ListingMode] | None = Field(default=None, min_length=1, max_length=4)
    description: str | None = Field(default=None, max_length=8000)
    price_amount_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    negotiable: bool | None = None
    return_policy: str | None = Field(default=None, max_length=500)
    open_to_exchange: bool | None = None
    exchange_preferences: str | None = Field(default=None, max_length=500)
    lending_duration_days: int | None = Field(default=None, ge=1, le=365)
    rental_fee_per_day_cents: int | None = Field(default=None, ge=0)
    rental_deposit_amount_cents: int | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, ge=1)
    condition: ListingConditionInput | None = None
    location: ListingLocationInput | None = None
    delivery_methods: list[ListingDeliveryMethodInput] | None = Field(default=None, max_length=2)
    images: list[ListingImageInput] | None = Field(default=None, max_length=12)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator("listing_modes")
    @classmethod
    def dedupe_modes(cls, value: list[ListingMode] | None) -> list[ListingMode] | None:
        if value is None:
            return None
        return ListingCreateRequest.dedupe_modes(value)


class MediaUploadUrlRequest(BaseModel):
    byte_size: int = Field(gt=0, le=15 * 1024 * 1024)
    checksum_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    filename: str = Field(min_length=1, max_length=255)


class MediaUploadUrlResponse(BaseModel):
    expires_at: datetime
    headers: dict[str, str]
    id: str
    storage_key: str
    upload_url: str


class CompleteMediaUploadRequest(BaseModel):
    byte_size: int | None = Field(default=None, gt=0, le=15 * 1024 * 1024)
    checksum_sha256: str | None = Field(default=None, min_length=64, max_length=64)


class MediaAssetResponse(BaseModel):
    byte_size: int
    content_type: str
    created_at: datetime
    id: str
    original_filename: str
    public_url: str | None = None
    status: MediaStatus


class ListingConditionResponse(ListingConditionInput):
    pass


class ListingLocationPublicResponse(BaseModel):
    campus_pickup: bool
    city: str
    country: str
    neighborhood: str | None = None
    public_area: str
    state: str | None = None


class ListingDeliveryMethodResponse(BaseModel):
    enabled: bool
    method: DeliveryMethod
    notes: str | None = None
    price_amount_cents: int | None = None


class ListingImageResponse(BaseModel):
    alt_text: str | None = None
    id: str
    is_primary: bool
    media: MediaAssetResponse
    public_url: str | None = None
    sort_order: int


class ListingInventoryResponse(BaseModel):
    quantity_available: int
    quantity_total: int


class ListingPriceHistoryResponse(BaseModel):
    changed_at: datetime
    currency: str
    id: str
    new_amount_cents: int | None
    old_amount_cents: int | None
    reason: str


class ListingBookSummary(BaseModel):
    id: str
    title: str


class ListingSellerSummary(BaseModel):
    id: str


class ListingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    book: ListingBookSummary
    condition: ListingConditionResponse | None
    created_at: datetime
    currency: str
    delivery_methods: list[ListingDeliveryMethodResponse]
    description: str | None = None
    exchange_preferences: str | None = None
    open_to_exchange: bool = False
    scope: ListingScope = "personal"
    visibility: ListingVisibility = "public"
    business_profile_id: str | None = None
    institution_id: str | None = None
    id: str
    images: list[ListingImageResponse]
    inventory: ListingInventoryResponse | None
    lending_duration_days: int | None = None
    rental_fee_per_day_cents: int | None = None
    listing_modes: list[ListingMode]
    location: ListingLocationPublicResponse | None
    negotiable: bool
    price_amount_cents: int | None = None
    price_history: list[ListingPriceHistoryResponse]
    quality_score: int
    rental_deposit_amount_cents: int | None = None
    return_policy: str | None = None
    seller: ListingSellerSummary
    status: ListingStatus
    title: str
    updated_at: datetime


def validate_price_rules(modes: list[ListingMode], price_amount_cents: int | None) -> None:
    mode_set = set(modes)
    if mode_set & PRICE_REQUIRED_MODES and price_amount_cents is None:
        raise ValueError("Price is required for sell, sell-exchange, rent, and bulk-sale listings.")
    if mode_set <= PRICELESS_MODES and price_amount_cents not in {None, 0}:
        raise ValueError("Donate, giveaway, and request listings cannot have a sale price.")
