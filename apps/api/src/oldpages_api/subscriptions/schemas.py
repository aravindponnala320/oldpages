from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

BillingInterval = Literal["monthly", "yearly"]
SubscriptionStatus = Literal["trialing", "active", "past_due", "cancelled", "expired"]
SubscriptionProvider = Literal["local", "razorpay", "stripe"]
PromotionType = Literal[
    "featured", "search_boost", "homepage", "category_spotlight", "urgent_badge"
]
PromotionStatus = Literal["active", "expired", "cancelled"]
DiscountType = Literal["percent", "fixed"]


class SubscriptionPlanResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    price_cents: int
    billing_interval: BillingInterval
    features_json: list[Any]
    listing_limit: int | None = None
    saved_search_limit: int | None = None
    community_limit: int | None = None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class SubscribeRequest(BaseModel):
    plan_id: str = Field(min_length=1, max_length=26)


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan: SubscriptionPlanResponse
    status: SubscriptionStatus
    provider: SubscriptionProvider
    provider_subscription_id: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancelled_at: datetime | None = None
    trial_end_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SubscriptionEntitlementsResponse(BaseModel):
    active: bool
    status: SubscriptionStatus | None = None
    subscription_id: str | None = None
    plan_id: str | None = None
    plan_slug: str | None = None
    features: list[Any]
    limits: dict[str, int | None]
    current_period_end: datetime | None = None


class PromotionCreateRequest(BaseModel):
    listing_id: str = Field(min_length=1, max_length=26)
    type: PromotionType
    starts_at: datetime
    ends_at: datetime
    amount_cents: int = Field(ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class PromotionResponse(BaseModel):
    id: str
    listing_id: str
    promotion_order_id: str | None = None
    seller_user_id: str
    type: PromotionType
    status: PromotionStatus
    amount_cents: int
    currency: str
    is_paid: bool
    starts_at: datetime
    ends_at: datetime
    created_at: datetime
    updated_at: datetime


class CouponCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    discount_type: DiscountType
    discount_value: int = Field(ge=1)
    min_order_cents: int | None = Field(default=None, ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    valid_from: datetime
    valid_until: datetime | None = None

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.strip().upper()


class CouponResponse(BaseModel):
    id: str
    code: str
    discount_type: DiscountType
    discount_value: int
    min_order_cents: int | None = None
    max_uses: int | None = None
    used_count: int
    valid_from: datetime
    valid_until: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CouponValidateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    order_amount_cents: int = Field(ge=0)

    @field_validator("code")
    @classmethod
    def uppercase_code(cls, value: str) -> str:
        return value.strip().upper()


class CouponValidateResponse(BaseModel):
    valid: bool
    discount_cents: int
    message: str
