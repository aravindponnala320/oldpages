from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oldpages_api.identity.models import User
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class Cart(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "carts"
    __table_args__ = (
        CheckConstraint(
            "status in ('active', 'checked_out', 'abandoned')",
            name="status",
        ),
        Index("ix_carts_buyer_user_id", "buyer_user_id"),
        Index("ix_carts_seller_user_id", "seller_user_id"),
        Index("ix_carts_buyer_seller_status", "buyer_user_id", "seller_user_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    buyer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")

    buyer: Mapped[User] = relationship(foreign_keys=[buyer_user_id])
    items: Mapped[list[CartItem]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list[Order]] = relationship(back_populates="cart")
    seller: Mapped[User] = relationship(foreign_keys=[seller_user_id])


class CartItem(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("price_snapshot_cents >= 0", name="price_non_negative"),
        Index("ix_cart_items_cart_id", "cart_id"),
        Index("ix_cart_items_listing_id", "listing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="RESTRICT"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    price_snapshot_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")

    cart: Mapped[Cart] = relationship(back_populates="items")


class Order(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "status in ('created', 'awaiting_payment', 'paid', 'accepted', 'preparing',"
            " 'ready_for_pickup', 'shipped', 'delivered', 'completed', 'cancelled',"
            " 'refunded', 'disputed')",
            name="status",
        ),
        CheckConstraint(
            "fulfillment_method in ('pickup', 'shipping')",
            name="fulfillment_method",
        ),
        CheckConstraint("subtotal_cents >= 0", name="subtotal_non_negative"),
        CheckConstraint("platform_fee_cents >= 0", name="platform_fee_non_negative"),
        CheckConstraint("total_cents >= 0", name="total_non_negative"),
        Index("ix_orders_buyer_status", "buyer_user_id", "status"),
        Index("ix_orders_seller_status", "seller_user_id", "status"),
        Index("ix_orders_cart_id", "cart_id"),
        Index("ix_orders_offer_id", "offer_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    buyer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    cart_id: Mapped[int | None] = mapped_column(
        ForeignKey("carts.id", ondelete="SET NULL"),
        nullable=True,
    )
    offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("offers.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="created")
    fulfillment_method: Mapped[str] = mapped_column(String(24), nullable=False, default="pickup")
    subtotal_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    platform_fee_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    buyer: Mapped[User] = relationship(foreign_keys=[buyer_user_id])
    cart: Mapped[Cart | None] = relationship(back_populates="orders")
    disputes: Mapped[list[Dispute]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    payments: Mapped[list[Payment]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    payouts: Mapped[list[Payout]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    refunds: Mapped[list[Refund]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    seller: Mapped[User] = relationship(foreign_keys=[seller_user_id])
    shipments: Mapped[list[Shipment]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price_cents >= 0", name="unit_price_non_negative"),
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_listing_id", "listing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="RESTRICT"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    title_snapshot: Mapped[str] = mapped_column(String(500), nullable=False)
    condition_snapshot: Mapped[str] = mapped_column(String(80), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")


class Payment(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "provider in ('local', 'razorpay', 'stripe')",
            name="provider",
        ),
        CheckConstraint(
            "status in ('pending', 'authorized', 'captured', 'failed', 'refunded', 'disputed')",
            name="status",
        ),
        CheckConstraint("amount_cents >= 0", name="amount_non_negative"),
        Index("ix_payments_order_id", "order_id"),
        Index("ix_payments_provider_status", "provider", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(24), nullable=False, default="local")
    provider_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped[Order] = relationship(back_populates="payments")
    refunds: Mapped[list[Refund]] = relationship(
        back_populates="payment",
        cascade="all, delete-orphan",
    )


class Payout(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "payouts"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'processing', 'paid', 'failed')",
            name="status",
        ),
        CheckConstraint("amount_cents >= 0", name="amount_non_negative"),
        Index("ix_payouts_order_id", "order_id"),
        Index("ix_payouts_seller_user_id", "seller_user_id"),
        Index("ix_payouts_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    provider: Mapped[str] = mapped_column(String(24), nullable=False, default="local")
    provider_payout_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    initiated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped[Order] = relationship(back_populates="payouts")
    seller: Mapped[User] = relationship(foreign_keys=[seller_user_id])


class Refund(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "refunds"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'processing', 'succeeded', 'failed')",
            name="status",
        ),
        CheckConstraint("amount_cents >= 0", name="amount_non_negative"),
        Index("ix_refunds_payment_id", "payment_id"),
        Index("ix_refunds_order_id", "order_id"),
        Index("ix_refunds_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id", ondelete="CASCADE"))
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    provider_refund_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    initiated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    succeeded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped[Order] = relationship(back_populates="refunds")
    payment: Mapped[Payment] = relationship(back_populates="refunds")


class Shipment(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "shipments"
    __table_args__ = (
        CheckConstraint(
            "provider in ('local', 'shiprocket', 'delhivery')",
            name="provider",
        ),
        CheckConstraint(
            "status in ('pending', 'label_generated', 'picked_up', 'in_transit',"
            " 'delivered', 'failed', 'returned')",
            name="status",
        ),
        Index("ix_shipments_order_id", "order_id"),
        Index("ix_shipments_status", "status"),
        Index("ix_shipments_tracking_number", "tracking_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(24), nullable=False, default="local")
    provider_shipment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    carrier: Mapped[str | None] = mapped_column(String(80), nullable=True)
    estimated_delivery_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    from_address_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    to_address_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    weight_grams: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    order: Mapped[Order] = relationship(back_populates="shipments")


class Dispute(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "disputes"
    __table_args__ = (
        CheckConstraint(
            "reason in ('item_not_received', 'item_not_as_described', 'wrong_item',"
            " 'damaged', 'other')",
            name="reason",
        ),
        CheckConstraint(
            "status in ('opened', 'under_review', 'resolved_buyer', 'resolved_seller', 'closed')",
            name="status",
        ),
        Index("ix_disputes_order_id", "order_id"),
        Index("ix_disputes_opened_by_user_id", "opened_by_user_id"),
        Index("ix_disputes_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    opened_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="opened")
    resolved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    opened_by: Mapped[User] = relationship(foreign_keys=[opened_by_user_id])
    order: Mapped[Order] = relationship(back_populates="disputes")
    resolved_by: Mapped[User | None] = relationship(foreign_keys=[resolved_by_user_id])


class WebhookEvent(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_webhook_events_provider_event"),
        Index("ix_webhook_events_provider_event_type", "provider", "event_type"),
        Index("ix_webhook_events_processed", "processed"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class IdempotencyKey(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint("key", name="uq_idempotency_keys_key"),
        Index("ix_idempotency_keys_user_id", "user_id"),
        Index("ix_idempotency_keys_expires_at", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    response_status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


__all__ = [
    "Cart",
    "CartItem",
    "Dispute",
    "IdempotencyKey",
    "Order",
    "OrderItem",
    "Payment",
    "Payout",
    "Refund",
    "Shipment",
    "WebhookEvent",
]
