from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
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


class Institution(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "institutions"
    __table_args__ = (
        CheckConstraint(
            "type in ('school', 'college', 'university', 'library', 'ngo', 'coaching', "
            "'publisher', 'bookstore', 'other')",
            name="type",
        ),
        CheckConstraint(
            "status in ('pending', 'active', 'suspended', 'rejected')",
            name="status",
        ),
        CheckConstraint("member_count >= 0", name="member_count_non_negative"),
        Index("ix_institutions_slug", "slug"),
        Index("ix_institutions_type_status", "type", "status"),
        Index("ix_institutions_owner_user_id", "owner_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    slug: Mapped[str] = mapped_column(String(260), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    country: Mapped[str] = mapped_column(String(4), nullable=False, default="IN")
    latitude: Mapped[str | None] = mapped_column(String(40), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    rejected_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    domains: Mapped[list[InstitutionDomain]] = relationship(
        back_populates="institution",
        cascade="all, delete-orphan",
    )
    members: Mapped[list[InstitutionMember]] = relationship(
        back_populates="institution",
        cascade="all, delete-orphan",
    )
    owner: Mapped[User | None] = relationship(foreign_keys=[owner_user_id])


class InstitutionDomain(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "institution_domains"
    __table_args__ = (Index("ix_institution_domains_institution_id", "institution_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    institution_id: Mapped[int] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(String(253), nullable=False, unique=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    institution: Mapped[Institution] = relationship(back_populates="domains")


class InstitutionMember(TimestampMixin, PublicIdMixin, Base):
    __tablename__ = "institution_members"
    __table_args__ = (
        CheckConstraint(
            "role in ('admin', 'staff', 'student', 'alumni', 'member')",
            name="role",
        ),
        CheckConstraint(
            "status in ('pending', 'active', 'suspended')",
            name="status",
        ),
        UniqueConstraint("institution_id", "user_id", name="uq_institution_members_inst_user"),
        Index("ix_institution_members_institution_id", "institution_id"),
        Index("ix_institution_members_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    institution_id: Mapped[int] = mapped_column(
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(24), nullable=False, default="member")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    institution: Mapped[Institution] = relationship(back_populates="members")
    user: Mapped[User] = relationship(foreign_keys=[user_id])


__all__ = [
    "Institution",
    "InstitutionDomain",
    "InstitutionMember",
]
