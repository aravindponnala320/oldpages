from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

CartStatus = Literal["active", "checked_out", "abandoned"]
OrderStatus = Literal[
    "created",
    "awaiting_payment",
    "paid",
    "accepted",
    "preparing",
    "ready_for_pickup",
    "shipped",
    "delivered",
    "completed",
    "cancelled",
    "refunded",
    "disputed",
]
FulfillmentMethod = Literal["pickup", "shipping"]
PaymentProvider = Literal["local", "razorpay", "stripe"]
PaymentStatus = Literal["pending", "authorized", "captured", "failed", "refunded", "disputed"]
PayoutStatus = Literal["pending", "processing", "paid", "failed"]
RefundStatus = Literal["pending", "processing", "succeeded", "failed"]
ShipmentProvider = Literal["local", "shiprocket", "delhivery"]
ShipmentStatus = Literal[
    "pending",
    "label_generated",
    "picked_up",
    "in_transit",
    "delivered",
    "failed",
    "returned",
]
DisputeReason = Literal[
    "item_not_received",
    "item_not_as_described",
    "wrong_item",
    "damaged",
    "other",
]
DisputeStatus = Literal["opened", "under_review", "resolved_buyer", "resolved_seller", "closed"]


class PaymentsUserSummary(BaseModel):
    id: str


# --- Cart Schemas ---


class CartCreateRequest(BaseModel):
    seller_id: str = Field(min_length=1, max_length=26)
    currency: str = Field(default="INR", min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class CartItemAddRequest(BaseModel):
    listing_id: str = Field(min_length=1, max_length=26)
    quantity: int = Field(default=1, ge=1, le=100)


class CartCheckoutRequest(BaseModel):
    fulfillment_method: FulfillmentMethod = "pickup"
    idempotency_key: str | None = Field(default=None, max_length=128)


class CartItemResponse(BaseModel):
    cart_id: str
    created_at: datetime
    currency: str
    id: str
    listing_id: str
    price_snapshot_cents: int
    quantity: int


class CartResponse(BaseModel):
    buyer: PaymentsUserSummary
    created_at: datetime
    currency: str
    id: str
    items: list[CartItemResponse]
    seller: PaymentsUserSummary
    status: CartStatus


# --- Order Schemas ---


class OrderItemResponse(BaseModel):
    condition_snapshot: str
    currency: str
    id: str
    listing_id: str
    order_id: str
    quantity: int
    title_snapshot: str
    unit_price_cents: int


class OrderResponse(BaseModel):
    buyer: PaymentsUserSummary
    cart_id: str | None = None
    created_at: datetime
    currency: str
    fulfillment_method: FulfillmentMethod
    id: str
    idempotency_key: str | None = None
    items: list[OrderItemResponse]
    offer_id: str | None = None
    platform_fee_cents: int
    seller: PaymentsUserSummary
    status: OrderStatus
    subtotal_cents: int
    total_cents: int


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int


class OrderCancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()


# --- Payment Schemas ---


class PaymentInitiateRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=128)
    provider: PaymentProvider = "local"
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaymentResponse(BaseModel):
    amount_cents: int
    captured_at: datetime | None = None
    created_at: datetime
    currency: str
    failed_at: datetime | None = None
    id: str
    idempotency_key: str
    order_id: str
    provider: PaymentProvider
    provider_payment_id: str | None = None
    refunded_at: datetime | None = None
    status: PaymentStatus


class PaymentInitiateResponse(BaseModel):
    payment: PaymentResponse
    provider_data: dict[str, Any]


# --- Payout Schemas ---


class PayoutResponse(BaseModel):
    amount_cents: int
    created_at: datetime
    currency: str
    id: str
    initiated_at: datetime | None = None
    order_id: str
    paid_at: datetime | None = None
    provider: str
    provider_payout_id: str | None = None
    seller: PaymentsUserSummary
    status: PayoutStatus


# --- Refund Schemas ---


class RefundInitiateRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    amount_cents: int | None = Field(default=None, ge=1)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        return value.strip()


class RefundResponse(BaseModel):
    amount_cents: int
    created_at: datetime
    currency: str
    id: str
    initiated_at: datetime | None = None
    order_id: str
    payment_id: str
    provider_refund_id: str | None = None
    reason: str
    status: RefundStatus
    succeeded_at: datetime | None = None


# --- Shipment Schemas ---


class AddressInput(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    phone: str = Field(min_length=1, max_length=24)
    address_line1: str = Field(min_length=1, max_length=500)
    address_line2: str | None = Field(default=None, max_length=500)
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=120)
    pincode: str = Field(min_length=1, max_length=12)
    country: str = Field(default="IN", min_length=2, max_length=3)


class ShipmentCreateRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=26)
    provider: ShipmentProvider = "local"
    from_address: AddressInput
    to_address: AddressInput
    weight_grams: int | None = Field(default=None, ge=1)


class ShipmentStatusUpdateRequest(BaseModel):
    status: ShipmentStatus
    tracking_number: str | None = Field(default=None, max_length=128)
    carrier: str | None = Field(default=None, max_length=80)
    estimated_delivery_at: datetime | None = None


class ShipmentResponse(BaseModel):
    carrier: str | None = None
    created_at: datetime
    delivered_at: datetime | None = None
    estimated_delivery_at: datetime | None = None
    from_address: dict[str, Any]
    id: str
    order_id: str
    provider: ShipmentProvider
    provider_shipment_id: str | None = None
    status: ShipmentStatus
    to_address: dict[str, Any]
    tracking_number: str | None = None
    weight_grams: int | None = None


# --- Dispute Schemas ---


class DisputeOpenRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=26)
    reason: DisputeReason
    description: str = Field(min_length=1, max_length=4000)

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str) -> str:
        return value.strip()


class DisputeEvidenceRequest(BaseModel):
    evidence: dict[str, Any] = Field(default_factory=dict)
    note: str | None = Field(default=None, max_length=2000)


class DisputeResolveRequest(BaseModel):
    resolution: Literal["resolved_buyer", "resolved_seller", "closed"]
    resolution_note: str | None = Field(default=None, max_length=2000)

    @field_validator("resolution_note")
    @classmethod
    def strip_note(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        return stripped or None


class DisputeResponse(BaseModel):
    created_at: datetime
    description: str
    evidence: dict[str, Any]
    id: str
    opened_by: PaymentsUserSummary
    order_id: str
    reason: DisputeReason
    resolution_note: str | None = None
    resolved_at: datetime | None = None
    resolved_by: PaymentsUserSummary | None = None
    status: DisputeStatus
