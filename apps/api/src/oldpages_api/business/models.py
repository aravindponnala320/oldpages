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


class BusinessProfile(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "business_profiles"
    __table_args__ = (
        CheckConstraint(
            "type in ('individual', 'shop', 'publisher', 'library', 'institution')",
            name="type",
        ),
        CheckConstraint(
            "status in ('pending', 'active', 'suspended', 'rejected')",
            name="status",
        ),
        Index("ix_business_profiles_owner_user_id", "owner_user_id"),
        Index("ix_business_profiles_slug", "slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    slug: Mapped[str] = mapped_column(String(260), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False, default="individual")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    listing_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    owner: Mapped[User] = relationship(foreign_keys=[owner_user_id])
    locations: Mapped[list[BusinessLocation]] = relationship(
        back_populates="business_profile",
        cascade="all, delete-orphan",
    )
    staff_accounts: Mapped[list[StaffAccount]] = relationship(
        back_populates="business_profile",
        cascade="all, delete-orphan",
    )
    inventory_imports: Mapped[list[InventoryImport]] = relationship(
        back_populates="business_profile",
        cascade="all, delete-orphan",
    )


class BusinessLocation(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "business_locations"
    __table_args__ = (Index("ix_business_locations_business_profile_id", "business_profile_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_profile_id: Mapped[int] = mapped_column(
        ForeignKey("business_profiles.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(4), nullable=False, default="IN")
    pincode: Mapped[str | None] = mapped_column(String(12), nullable=True)
    latitude: Mapped[str | None] = mapped_column(String(40), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    business_profile: Mapped[BusinessProfile] = relationship(back_populates="locations")


class StaffAccount(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "staff_accounts"
    __table_args__ = (
        CheckConstraint(
            "role in ('owner', 'manager', 'staff')",
            name="role",
        ),
        CheckConstraint(
            "status in ('active', 'suspended')",
            name="status",
        ),
        UniqueConstraint("business_profile_id", "user_id", name="uq_staff_accounts_profile_user"),
        Index("ix_staff_accounts_business_profile_id", "business_profile_id"),
        Index("ix_staff_accounts_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_profile_id: Mapped[int] = mapped_column(
        ForeignKey("business_profiles.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(24), nullable=False, default="staff")
    permissions_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    business_profile: Mapped[BusinessProfile] = relationship(back_populates="staff_accounts")
    user: Mapped[User] = relationship(foreign_keys=[user_id])


class InventoryImport(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "inventory_imports"
    __table_args__ = (
        CheckConstraint(
            "status in ('pending', 'processing', 'completed', 'failed')",
            name="status",
        ),
        UniqueConstraint(
            "business_profile_id",
            "payload_hash",
            name="uq_inventory_imports_profile_payload_hash",
        ),
        Index("ix_inventory_imports_business_profile_id", "business_profile_id"),
        Index("ix_inventory_imports_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_profile_id: Mapped[int] = mapped_column(
        ForeignKey("business_profiles.id", ondelete="CASCADE")
    )
    imported_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_rows_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    error_report_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    business_profile: Mapped[BusinessProfile] = relationship(back_populates="inventory_imports")
    imported_by: Mapped[User] = relationship(foreign_keys=[imported_by_user_id])


__all__ = [
    "BusinessLocation",
    "BusinessProfile",
    "InventoryImport",
    "StaffAccount",
]
