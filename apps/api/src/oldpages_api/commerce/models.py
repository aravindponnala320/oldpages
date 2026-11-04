from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
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
from oldpages_api.listings.models import Listing
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class Offer(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint(
            "offer_type in ('price', 'counter', 'exchange', 'bundle')",
            name="offer_type",
        ),
        CheckConstraint(
            "status in ('pending', 'countered', 'accepted', 'rejected', 'withdrawn', 'expired')",
            name="status",
        ),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint(
            "amount_cents is null or amount_cents >= 0",
            name="amount_non_negative",
        ),
        CheckConstraint(
            "fulfillment_method in ('pickup', 'shipping')",
            name="fulfillment_method",
        ),
        Index("ix_offers_listing_status", "listing_id", "status"),
        Index("ix_offers_buyer_user_id", "buyer_user_id"),
        Index("ix_offers_seller_user_id", "seller_user_id"),
        Index("ix_offers_expires_at", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    buyer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    proposer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    parent_offer_id: Mapped[int | None] = mapped_column(
        ForeignKey("offers.id", ondelete="SET NULL"),
        nullable=True,
    )
    offer_type: Mapped[str] = mapped_column(String(24), nullable=False, default="price")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    fulfillment_method: Mapped[str] = mapped_column(String(24), nullable=False, default="pickup")
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    bundle_listing_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    buyer: Mapped[User] = relationship(foreign_keys=[buyer_user_id])
    children: Mapped[list[Offer]] = relationship(back_populates="parent")
    exchange_items: Mapped[list[ExchangeOfferItem]] = relationship(
        back_populates="offer",
        cascade="all, delete-orphan",
    )
    listing: Mapped[Listing] = relationship()
    parent: Mapped[Offer | None] = relationship(
        back_populates="children",
        remote_side=[id],
    )
    proposer: Mapped[User] = relationship(foreign_keys=[proposer_user_id])
    seller: Mapped[User] = relationship(foreign_keys=[seller_user_id])
    transaction: Mapped[Transaction | None] = relationship(
        back_populates="offer",
        uselist=False,
    )


class ExchangeOfferItem(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "exchange_offer_items"
    __table_args__ = (
        CheckConstraint(
            "cash_adjustment_cents is null or cash_adjustment_cents >= 0",
            name="cash_adjustment_non_negative",
        ),
        Index("ix_exchange_offer_items_offer_id", "offer_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"))
    offered_listing_id: Mapped[int | None] = mapped_column(
        ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    condition_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cash_adjustment_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)

    offer: Mapped[Offer] = relationship(back_populates="exchange_items")
    offered_listing: Mapped[Listing | None] = relationship()


class Transaction(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "status in ('reserved', 'ready_for_pickup', 'completed', 'cancelled', 'disputed')",
            name="status",
        ),
        CheckConstraint(
            "fulfillment_method in ('pickup', 'shipping')",
            name="fulfillment_method",
        ),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint(
            "amount_cents is null or amount_cents >= 0",
            name="amount_non_negative",
        ),
        UniqueConstraint("offer_id", name="uq_transactions_offer_id"),
        Index("ix_transactions_buyer_status", "buyer_user_id", "status"),
        Index("ix_transactions_seller_status", "seller_user_id", "status"),
        Index("ix_transactions_listing_id", "listing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="RESTRICT"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="RESTRICT"))
    buyer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="reserved")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    fulfillment_method: Mapped[str] = mapped_column(String(24), nullable=False, default="pickup")
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cancelled_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    buyer_marked_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seller_marked_delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    buyer: Mapped[User] = relationship(foreign_keys=[buyer_user_id])
    listing: Mapped[Listing] = relationship()
    offer: Mapped[Offer] = relationship(back_populates="transaction")
    pickup_sessions: Mapped[list[PickupSession]] = relationship(
        back_populates="transaction",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[list[Review]] = relationship(
        back_populates="transaction",
        cascade="all, delete-orphan",
    )
    seller: Mapped[User] = relationship(foreign_keys=[seller_user_id])


class PickupSession(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "pickup_sessions"
    __table_args__ = (
        CheckConstraint(
            "status in ('proposed', 'confirmed', 'completed', 'cancelled')",
            name="status",
        ),
        UniqueConstraint("transaction_id", name="uq_pickup_sessions_transaction_id"),
        Index("ix_pickup_sessions_status", "status"),
        Index("ix_pickup_sessions_proposed_start_at", "proposed_start_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"))
    proposed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    confirmed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="proposed")
    proposed_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    proposed_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    public_location_label: Mapped[str] = mapped_column(String(240), nullable=False)
    exact_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    exact_latitude: Mapped[str | None] = mapped_column(String(40), nullable=True)
    exact_longitude: Mapped[str | None] = mapped_column(String(40), nullable=True)
    pickup_notes_private: Mapped[str | None] = mapped_column(Text, nullable=True)
    handover_code: Mapped[str] = mapped_column(String(12), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    confirmed_by: Mapped[User | None] = relationship(foreign_keys=[confirmed_by_user_id])
    proposed_by: Mapped[User] = relationship(foreign_keys=[proposed_by_user_id])
    transaction: Mapped[Transaction] = relationship(back_populates="pickup_sessions")


class Review(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 and rating <= 5", name="rating_range"),
        CheckConstraint(
            "review_type in ('buyer_reviews_seller', 'seller_reviews_buyer')",
            name="review_type",
        ),
        CheckConstraint(
            "status in ('published', 'hidden', 'removed')",
            name="status",
        ),
        UniqueConstraint("transaction_id", "reviewer_user_id", name="uq_reviews_once_per_side"),
        Index("ix_reviews_reviewee_user_id", "reviewee_user_id"),
        Index("ix_reviews_transaction_id", "transaction_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"))
    reviewer_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reviewee_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    review_type: Mapped[str] = mapped_column(String(40), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="published")

    dimensions: Mapped[list[ReviewDimension]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
    )
    reviewee: Mapped[User] = relationship(foreign_keys=[reviewee_user_id])
    reviewer: Mapped[User] = relationship(foreign_keys=[reviewer_user_id])
    transaction: Mapped[Transaction] = relationship(back_populates="reviews")


class ReviewDimension(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "review_dimensions"
    __table_args__ = (
        CheckConstraint("rating >= 1 and rating <= 5", name="rating_range"),
        UniqueConstraint("review_id", "dimension", name="uq_review_dimensions_dimension"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"))
    dimension: Mapped[str] = mapped_column(String(80), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)

    review: Mapped[Review] = relationship(back_populates="dimensions")


__all__ = [
    "ExchangeOfferItem",
    "Offer",
    "PickupSession",
    "Review",
    "ReviewDimension",
    "Transaction",
]
