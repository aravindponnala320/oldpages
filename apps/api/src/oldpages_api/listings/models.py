from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oldpages_api.business.models import BusinessProfile
from oldpages_api.catalog.models import BookEdition
from oldpages_api.identity.models import User
from oldpages_api.institutions.models import Institution
from oldpages_api.shared.db.base import Base, PublicIdMixin, TimestampMixin


class Listing(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "listings"
    __table_args__ = (
        CheckConstraint(
            "status in "
            "('draft', 'pending_moderation', 'active', 'paused', 'reserved', 'completed', "
            "'expired', 'suspended', 'rejected', 'deleted')",
            name="status",
        ),
        CheckConstraint(
            "price_amount_cents is null or price_amount_cents >= 0", name="price_non_negative"
        ),
        CheckConstraint("quality_score >= 0 and quality_score <= 100", name="quality_score_range"),
        Index("ix_listings_seller_user_id", "seller_user_id"),
        Index("ix_listings_book_edition_id", "book_edition_id"),
        Index("ix_listings_status", "status"),
        Index("ix_listings_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seller_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    book_edition_id: Mapped[int] = mapped_column(
        ForeignKey("book_editions.id", ondelete="RESTRICT")
    )
    title_snapshot: Mapped[str] = mapped_column(String(500), nullable=False)
    listing_modes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    scope: Mapped[str] = mapped_column(String(24), nullable=False, default="personal")
    visibility: Mapped[str] = mapped_column(String(32), nullable=False, default="public")
    business_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("business_profiles.id", ondelete="SET NULL"), nullable=True
    )
    institution_id: Mapped[int | None] = mapped_column(
        ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    negotiable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    return_policy: Mapped[str | None] = mapped_column(String(500), nullable=True)
    exchange_preferences: Mapped[str | None] = mapped_column(String(500), nullable=True)
    open_to_exchange: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lending_duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rental_fee_per_day_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rental_deposit_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    book_edition: Mapped[BookEdition] = relationship()
    condition: Mapped[ListingCondition | None] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
        uselist=False,
    )
    delivery_methods: Mapped[list[ListingDeliveryMethod]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    images: Mapped[list[ListingImage]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    inventory: Mapped[ListingInventory | None] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
        uselist=False,
    )
    location: Mapped[ListingLocation | None] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
        uselist=False,
    )
    price_history: Mapped[list[ListingPriceHistory]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    seller: Mapped[User] = relationship()


class ListingCondition(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "listing_conditions"
    __table_args__ = (
        CheckConstraint(
            "condition in "
            "('new_sealed', 'like_new', 'excellent', 'very_good', 'good', 'acceptable', "
            "'poor', 'reference_only')",
            name="condition",
        ),
        CheckConstraint(
            "highlighting_percent is null or "
            "(highlighting_percent >= 0 and highlighting_percent <= 100)",
            name="highlighting_percent_range",
        ),
        CheckConstraint(
            "workbook_completion_percent is null or "
            "(workbook_completion_percent >= 0 and workbook_completion_percent <= 100)",
            name="workbook_completion_percent_range",
        ),
        UniqueConstraint("listing_id", name="uq_listing_conditions_listing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    condition: Mapped[str] = mapped_column(String(32), nullable=False)
    damage_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    highlighting_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    handwritten_notes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    name_written_inside: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    torn_pages: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    missing_pages: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    loose_binding: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    water_damage: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stains: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    odor_or_smoke_exposure: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    library_markings: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stickers: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dust_jacket_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    supplemental_media_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    access_code_status: Mapped[str | None] = mapped_column(String(80), nullable=True)
    answer_key_present: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    workbook_completion_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    signed_by_author: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    first_edition: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    collectible_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    listing: Mapped[Listing] = relationship(back_populates="condition")


class ListingLocation(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "listing_locations"
    __table_args__ = (
        CheckConstraint(
            "public_latitude is null or (public_latitude >= -90 and public_latitude <= 90)",
            name="public_latitude_range",
        ),
        CheckConstraint(
            "public_longitude is null or (public_longitude >= -180 and public_longitude <= 180)",
            name="public_longitude_range",
        ),
        UniqueConstraint("listing_id", name="uq_listing_locations_listing_id"),
        Index("ix_listing_locations_city", "city"),
        Index("ix_listing_locations_state", "state"),
        Index("ix_listing_locations_country", "country"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    neighborhood: Mapped[str | None] = mapped_column(String(120), nullable=True)
    public_area: Mapped[str] = mapped_column(String(180), nullable=False)
    campus_pickup: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    exact_latitude: Mapped[str | None] = mapped_column(String(40), nullable=True)
    exact_longitude: Mapped[str | None] = mapped_column(String(40), nullable=True)
    public_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    public_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    pickup_notes_private: Mapped[str | None] = mapped_column(Text, nullable=True)

    listing: Mapped[Listing] = relationship(back_populates="location")


class ListingDeliveryMethod(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "listing_delivery_methods"
    __table_args__ = (
        CheckConstraint("method in ('pickup', 'shipping')", name="method"),
        CheckConstraint(
            "price_amount_cents is null or price_amount_cents >= 0",
            name="price_non_negative",
        ),
        UniqueConstraint("listing_id", "method", name="uq_listing_delivery_methods_method"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    method: Mapped[str] = mapped_column(String(24), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    price_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    listing: Mapped[Listing] = relationship(back_populates="delivery_methods")


class ListingPriceHistory(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "listing_price_history"
    __table_args__ = (
        CheckConstraint(
            "old_amount_cents is null or old_amount_cents >= 0",
            name="old_price_non_negative",
        ),
        CheckConstraint(
            "new_amount_cents is null or new_amount_cents >= 0",
            name="new_price_non_negative",
        ),
        Index("ix_listing_price_history_listing_id", "listing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    changed_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    old_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_amount_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    reason: Mapped[str] = mapped_column(String(120), nullable=False, default="manual_update")

    listing: Mapped[Listing] = relationship(back_populates="price_history")


class ListingInventory(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "listing_inventory"
    __table_args__ = (
        CheckConstraint("quantity_total > 0", name="quantity_total_positive"),
        CheckConstraint("quantity_available >= 0", name="quantity_available_non_negative"),
        CheckConstraint(
            "quantity_available <= quantity_total", name="quantity_available_lte_total"
        ),
        UniqueConstraint("listing_id", name="uq_listing_inventory_listing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    quantity_total: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    listing: Mapped[Listing] = relationship(back_populates="inventory")


class MediaAsset(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "media_assets"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending_upload', 'uploaded', 'processing', 'approved', 'rejected')",
            name="status",
        ),
        CheckConstraint("byte_size > 0", name="byte_size_positive"),
        UniqueConstraint("storage_key", name="uq_media_assets_storage_key"),
        Index("ix_media_assets_user_id", "user_id"),
        Index("ix_media_assets_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending_upload")
    upload_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    public_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    user: Mapped[User] = relationship()


class ListingImage(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "listing_images"
    __table_args__ = (
        UniqueConstraint("media_asset_id", name="uq_listing_images_media_asset_id"),
        Index("ix_listing_images_listing_id", "listing_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    media_asset_id: Mapped[int] = mapped_column(ForeignKey("media_assets.id", ondelete="RESTRICT"))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alt_text: Mapped[str | None] = mapped_column(String(280), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    listing: Mapped[Listing] = relationship(back_populates="images")
    media_asset: Mapped[MediaAsset] = relationship()
