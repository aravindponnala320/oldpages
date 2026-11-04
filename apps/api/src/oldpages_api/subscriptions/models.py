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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oldpages_api.identity.models import User
from oldpages_api.listings.models import Listing
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class SubscriptionPlan(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "subscription_plans"
    __table_args__ = (
        CheckConstraint(
            "billing_interval in ('monthly', 'yearly')",
            name="billing_interval",
        ),
        CheckConstraint("price_cents >= 0", name="price_cents_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(140), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    billing_interval: Mapped[str] = mapped_column(String(24), nullable=False, default="monthly")
    features_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    listing_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    saved_search_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    community_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    subscriptions: Mapped[list[Subscription]] = relationship(back_populates="plan")


class Subscription(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint(
            "status in ('trialing', 'active', 'past_due', 'cancelled', 'expired')",
            name="status",
        ),
        CheckConstraint(
            "provider in ('local', 'razorpay', 'stripe')",
            name="provider",
        ),
        Index("ix_subscriptions_user_id", "user_id"),
        Index("ix_subscriptions_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    plan_id: Mapped[int] = mapped_column(ForeignKey("subscription_plans.id", ondelete="RESTRICT"))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    provider: Mapped[str] = mapped_column(String(24), nullable=False, default="local")
    provider_subscription_id: Mapped[str | None] = mapped_column(String(240), nullable=True)
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    plan: Mapped[SubscriptionPlan] = relationship(back_populates="subscriptions")


class Promotion(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "promotions"
    __table_args__ = (
        CheckConstraint(
            "type in ("
            "'featured', 'search_boost', 'homepage', 'category_spotlight', 'urgent_badge'"
            ")",
            name="type",
        ),
        CheckConstraint(
            "status in ('active', 'expired', 'cancelled')",
            name="status",
        ),
        CheckConstraint("amount_cents >= 0", name="amount_cents_non_negative"),
        Index("ix_promotions_listing_id", "listing_id"),
        Index("ix_promotions_seller_user_id", "seller_user_id"),
        Index("ix_promotions_status", "status"),
        Index("ix_promotions_ends_at", "ends_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    listing: Mapped[Listing] = relationship(foreign_keys=[listing_id])
    orders: Mapped[list[PromotionOrder]] = relationship(
        back_populates="promotion",
        cascade="all, delete-orphan",
    )
    seller: Mapped[User] = relationship(foreign_keys=[seller_user_id])


class PromotionOrder(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "promotion_orders"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'paid', 'cancelled', 'refunded')",
            name="status",
        ),
        CheckConstraint(
            "provider in ('local', 'razorpay', 'stripe')",
            name="provider",
        ),
        CheckConstraint("amount_cents >= 0", name="amount_cents_non_negative"),
        Index("ix_promotion_orders_promotion_id", "promotion_id"),
        Index("ix_promotion_orders_seller_user_id", "seller_user_id"),
        Index("ix_promotion_orders_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    promotion_id: Mapped[int] = mapped_column(ForeignKey("promotions.id", ondelete="CASCADE"))
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    provider: Mapped[str] = mapped_column(String(24), nullable=False, default="local")
    provider_order_id: Mapped[str | None] = mapped_column(String(240), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    promotion: Mapped[Promotion] = relationship(back_populates="orders")
    seller: Mapped[User] = relationship(foreign_keys=[seller_user_id])


class Coupon(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "coupons"
    __table_args__ = (
        CheckConstraint(
            "discount_type in ('percent', 'fixed')",
            name="discount_type",
        ),
        CheckConstraint("discount_value > 0", name="discount_value_positive"),
        CheckConstraint(
            "min_order_cents is null or min_order_cents >= 0",
            name="min_order_cents_non_negative",
        ),
        CheckConstraint(
            "max_uses is null or max_uses > 0",
            name="max_uses_positive",
        ),
        CheckConstraint("used_count >= 0", name="used_count_non_negative"),
        Index("ix_coupons_code", "code"),
        Index("ix_coupons_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    discount_type: Mapped[str] = mapped_column(String(24), nullable=False)
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)
    min_order_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


__all__ = [
    "Coupon",
    "Promotion",
    "PromotionOrder",
    "Subscription",
    "SubscriptionPlan",
]
