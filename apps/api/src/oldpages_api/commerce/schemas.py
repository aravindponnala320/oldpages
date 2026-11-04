from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

OfferType = Literal["price", "counter", "exchange", "bundle"]
OfferStatus = Literal["pending", "countered", "accepted", "rejected", "withdrawn", "expired"]
FulfillmentMethod = Literal["pickup", "shipping"]
TransactionStatus = Literal["reserved", "ready_for_pickup", "completed", "cancelled", "disputed"]
PickupStatus = Literal["proposed", "confirmed", "completed", "cancelled"]
ReviewType = Literal["buyer_reviews_seller", "seller_reviews_buyer"]


class CommerceUserSummary(BaseModel):
    id: str
    display_name: str | None = None


class ExchangeOfferItemInput(BaseModel):
    cash_adjustment_cents: int | None = Field(default=None, ge=0)
    condition_note: str | None = Field(default=None, max_length=500)
    offered_listing_id: str | None = Field(default=None, max_length=26)
    title: str = Field(min_length=1, max_length=500)

    @field_validator("condition_note", "title")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.strip()


class OfferCreateRequest(BaseModel):
    amount_cents: int | None = Field(default=None, ge=0)
    bundle_listing_ids: list[str] = Field(default_factory=list, max_length=12)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    exchange_items: list[ExchangeOfferItemInput] = Field(default_factory=list, max_length=12)
    expires_at: datetime | None = None
    fulfillment_method: FulfillmentMethod = "pickup"
    listing_id: str = Field(min_length=1, max_length=26)
    message: str | None = Field(default=None, max_length=2000)
    offer_type: OfferType = "price"
    quantity: int = Field(default=1, ge=1, le=100)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_offer_content(self) -> OfferCreateRequest:
        if self.offer_type in {"price", "bundle"} and self.amount_cents is None:
            raise ValueError("Price and bundle offers require amount_cents.")
        if self.offer_type == "exchange" and not self.exchange_items:
            raise ValueError("Exchange offers require at least one exchange item.")
        if self.offer_type == "bundle" and not self.bundle_listing_ids:
            raise ValueError("Bundle offers require at least one bundled listing ID.")
        return self


class CounterOfferRequest(BaseModel):
    amount_cents: int = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    expires_at: datetime | None = None
    fulfillment_method: FulfillmentMethod | None = None
    message: str | None = Field(default=None, max_length=2000)
    quantity: int | None = Field(default=None, ge=1, le=100)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class EmptyActionRequest(BaseModel):
    message: str | None = Field(default=None, max_length=1000)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class ExchangeOfferItemResponse(BaseModel):
    cash_adjustment_cents: int | None = None
    condition_note: str | None = None
    id: str
    offered_listing_id: str | None = None
    title: str


class OfferResponse(BaseModel):
    amount_cents: int | None = None
    bundle_listing_ids: list[str]
    buyer: CommerceUserSummary
    created_at: datetime
    currency: str
    exchange_items: list[ExchangeOfferItemResponse]
    expires_at: datetime
    fulfillment_method: FulfillmentMethod
    id: str
    listing_id: str
    listing_title: str | None = None
    listing_price_cents: int | None = None
    message: str | None = None
    offer_type: OfferType
    parent_offer_id: str | None = None
    proposer: CommerceUserSummary
    quantity: int
    responded_at: datetime | None = None
    seller: CommerceUserSummary
    status: OfferStatus
    transaction_id: str | None = None


class PickupCreateRequest(BaseModel):
    exact_address: str | None = Field(default=None, max_length=500)
    exact_latitude: str | None = Field(default=None, max_length=40)
    exact_longitude: str | None = Field(default=None, max_length=40)
    pickup_notes_private: str | None = Field(default=None, max_length=2000)
    proposed_end_at: datetime | None = None
    proposed_start_at: datetime | None = None
    public_location_label: str | None = Field(default=None, max_length=240)
    transaction_id: str = Field(min_length=1, max_length=26)

    @field_validator(
        "exact_address",
        "exact_latitude",
        "exact_longitude",
        "pickup_notes_private",
        "public_location_label",
    )
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class PickupConfirmRequest(BaseModel):
    message: str | None = Field(default=None, max_length=1000)


class PickupResponse(BaseModel):
    confirmed_at: datetime | None = None
    confirmed_by_user_id: str | None = None
    exact_address: str | None = None
    exact_latitude: str | None = None
    exact_longitude: str | None = None
    handover_code: str | None = None
    id: str
    pickup_notes_private: str | None = None
    proposed_by_user_id: str
    proposed_end_at: datetime | None = None
    proposed_start_at: datetime | None = None
    public_location_label: str
    status: PickupStatus
    transaction_id: str


class TransactionResponse(BaseModel):
    amount_cents: int | None = None
    buyer: CommerceUserSummary
    completed_at: datetime | None = None
    created_at: datetime
    currency: str
    fulfillment_method: FulfillmentMethod
    id: str
    listing_id: str
    offer_id: str
    pickup: PickupResponse | None = None
    quantity: int
    seller: CommerceUserSummary
    status: TransactionStatus
    cancellation_reason: str | None = None
    cancelled_at: datetime | None = None
    cancelled_by_user_id: str | None = None
    buyer_marked_received_at: datetime | None = None
    seller_marked_delivered_at: datetime | None = None


class TransactionCompleteRequest(BaseModel):
    handover_code: str | None = Field(default=None, min_length=4, max_length=12)


class TransactionCancelRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str | None) -> str | None:
        if value is None:
            return value
        s = value.strip()
        return s or None


class ReviewDimensionInput(BaseModel):
    dimension: str = Field(min_length=1, max_length=80)
    rating: int = Field(ge=1, le=5)

    @field_validator("dimension")
    @classmethod
    def normalize_dimension(cls, value: str) -> str:
        return value.strip().lower().replace(" ", "_")


class ReviewCreateRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=4000)
    dimensions: list[ReviewDimensionInput] = Field(default_factory=list, max_length=10)
    rating: int = Field(ge=1, le=5)
    transaction_id: str = Field(min_length=1, max_length=26)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class ReviewDimensionResponse(BaseModel):
    dimension: str
    id: str
    rating: int


class ReviewResponse(BaseModel):
    comment: str | None = None
    created_at: datetime
    dimensions: list[ReviewDimensionResponse]
    id: str
    rating: int
    review_type: ReviewType
    reviewee: CommerceUserSummary
    reviewer: CommerceUserSummary
    status: str
    transaction_id: str
